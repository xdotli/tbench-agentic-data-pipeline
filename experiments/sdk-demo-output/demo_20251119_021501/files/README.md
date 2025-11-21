# Kafka Inventory Consumer - Race Condition Debug Challenge

## Overview

This is a Go-based microservice that consumes inventory change events from Apache Kafka and updates a PostgreSQL database. The service has critical race conditions that lead to:

- **Lost Updates**: Concurrent requests overwrite each other's changes
- **Inconsistent Inventory**: Final inventory counts don't match expected values
- **Overselling**: Products can be sold with negative or insufficient stock
- **Duplicate Processing**: Kafka messages may be processed multiple times

## Problem Description

### Current Issues

1. **No Per-Product Locking**: A global mutex protects the entire inventory map, causing all products to serialize through a single lock
2. **Read-Modify-Write Race Condition**: The sequence of reading stock, modifying it, and writing it back is not atomic
3. **Improper Transaction Isolation**: Using default transaction isolation level instead of SERIALIZABLE
4. **Unsafe Kafka Offset Management**: Offsets are committed before database writes complete
5. **No Idempotency Tracking**: Duplicate messages are not deduplicated properly

### Example Race Condition

```
Thread A: READ stock=100 → COMPUTE 100+10=110 → WRITE 110
Thread B: READ stock=100 → COMPUTE 100-5=95  → WRITE 95
Expected: 105
Actual: 95 (Thread A's update is lost!)
```

## Architecture

### Components

- **Go Service**: Consumes from Kafka, processes inventory updates
- **Apache Kafka**: Message queue with multiple partitions (simulating concurrent producers)
- **PostgreSQL**: Persistent inventory data store

### Data Flow

```
Kafka (inventory-events topic)
    ↓
Go Consumer (multiple workers reading from partitions)
    ↓
PostgreSQL Database
    ↓
Inventory Table (products)
```

## Running the Service

### Prerequisites

- Docker and Docker Compose
- Go 1.21+
- PostgreSQL 15+
- Apache Kafka 3.6+

### Start Infrastructure

```bash
docker-compose up -d
```

This starts:
- Zookeeper (port 2181)
- Kafka (ports 9092, 29092)
- PostgreSQL (port 5432)

### Verify Components

```bash
# Check Kafka is ready
docker-compose exec kafka kafka-broker-api-versions.sh --bootstrap-server localhost:9092

# Check PostgreSQL is ready
docker-compose exec postgres psql -U postgres -d inventory_test -c "SELECT 1"
```

### Build and Run Consumer

```bash
# Build Go binary
go build -o inventory-consumer main.go

# Run with race detector (will show race conditions!)
go run -race main.go

# Or compile and run
go build -o inventory-consumer main.go
./inventory-consumer
```

## Testing

### Run Test Suite

```bash
# Run all tests
pytest tests.py -v

# Run specific test category
pytest tests.py::TestRaceConditionDetection -v

# Run with verbose output and stop on first failure
pytest tests.py -v -x
```

### Key Tests

1. **TestConcurrentUpdatesConsistency**: Detects lost updates in concurrent operations
2. **TestConcurrentPartitionSimulation**: Simulates multiple Kafka partitions writing concurrently
3. **TestDuplicateEventNotDoubleProcessed**: Verifies idempotent processing
4. **TestHighConcurrentLoadNoCorruption**: Stress test with 10 workers × 50 ops

### Expected Test Results

**BEFORE FIX**: Most concurrency tests will FAIL
- Lost updates detected
- Data corruption under load
- Duplicate processing

**AFTER FIX**: All tests should PASS
- No lost updates
- Consistent data under concurrent load
- Proper idempotency

## Fix Implementation Guide

### Step 1: Replace Global Lock with Per-Product Locking

```go
// BEFORE: Global lock blocks all products
inventoryLock sync.Mutex

// AFTER: Per-product locks
type InventoryManager struct {
    locks sync.Map // map[string]*sync.Mutex
}

func (im *InventoryManager) getLock(productID string) *sync.Mutex {
    val, _ := im.locks.LoadOrStore(productID, &sync.Mutex{})
    return val.(*sync.Mutex)
}
```

### Step 2: Use Atomic Database Updates

```go
// BEFORE: Multiple SQL statements (RACE!)
UPDATE products SET current_stock = ? WHERE sku = ?

// AFTER: Atomic operation with version checking
UPDATE products
SET current_stock = current_stock + ?, version = version + 1
WHERE sku = ? AND version = ?
RETURNING current_stock
```

### Step 3: Use SERIALIZABLE Isolation Level

```go
// BEFORE: Default isolation level
tx, err := db.BeginTx(ctx, nil)

// AFTER: SERIALIZABLE prevents concurrent conflicts
tx, err := db.BeginTx(ctx, &sql.TxOptions{
    Isolation: sql.LevelSerializable,
})
```

### Step 4: Implement Idempotent Processing

```go
// Check and mark processed atomically in same transaction
cursor.execute("""
    BEGIN;
    SELECT FOR UPDATE FROM processed_events WHERE event_id = ?;
    IF NOT FOUND THEN
        INSERT INTO processed_events (event_id, product_id) VALUES (?, ?);
        UPDATE products SET current_stock = current_stock + ? WHERE sku = ?;
    END IF;
    COMMIT;
""")
```

### Step 5: Use Row-Level Locks (SELECT FOR UPDATE)

```go
// Lock the row while updating
cursor.execute(
    "SELECT current_stock FROM products WHERE sku = ? FOR UPDATE"
)
```

## Performance Considerations

### Locking Strategy Trade-offs

| Approach | Pros | Cons |
|----------|------|------|
| Global Mutex | Simple, prevents all races | Serializes all products, poor throughput |
| Per-Product Mutex | Good throughput, fair | More complex, risk of deadlock |
| RWMutex | Read-heavy workloads | Slower for write-heavy workloads |
| Database Locks | ACID guarantees | Network latency, deadlock risk |
| Optimistic Locking | Non-blocking reads | Retry logic overhead |

### Recommended Approach

Combine:
1. **Per-product RWMutex** in application layer (fast path)
2. **Database-level SERIALIZABLE** transactions (safety)
3. **Version numbers** for optimistic conflicts
4. **SELECT FOR UPDATE** for critical sections

Expected performance: <5% overhead vs buggy version (no serialization)

## Monitoring and Debugging

### Check for Race Conditions

```bash
# Run with Go race detector
go run -race main.go

# Look for "WARNING: DATA RACE" in output
```

### Check Database Consistency

```bash
# View all products and their stock
psql -U postgres -d inventory_test -c "SELECT sku, current_stock, version FROM products"

# Check processed events deduplication
psql -U postgres -d inventory_test -c "SELECT COUNT(*) as total, COUNT(DISTINCT event_id) as unique FROM processed_events"
```

### Monitor Consumer Lag

```bash
docker-compose exec kafka kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --group inventory-consumer-group \
  --describe
```

## Common Pitfalls

### ❌ Mistake 1: Using Mutex But Not All Paths

```go
// BUG: Only locked in one code path!
if someCondition {
    lock.Lock()
    defer lock.Unlock()
    // do work
}
// Can still race here!
```

### ❌ Mistake 2: Holding Locks Across Async Operations

```go
// BUG: Lock held while waiting for I/O
lock.Lock()
result := expensiveIO()
lock.Unlock()
// Can deadlock or cause starvation
```

### ❌ Mistake 3: Nested Locks (Deadlock Risk)

```go
// BUG: Nested locking can deadlock
func processMultiple(ids []string) {
    for _, id := range ids {
        lock.Lock()
        for _, other := range ids {
            lock.Lock() // DEADLOCK!
            lock.Unlock()
        }
        lock.Unlock()
    }
}
```

### ✅ Solution: Consistent Lock Ordering

```go
// GOOD: Always acquire in sorted order
sort.Strings(ids)
for _, id := range ids {
    locks[id].Lock()
    defer locks[id].Unlock()
}
```

## Files Overview

```
/files/
├── main.go                 # Broken Kafka consumer with race conditions
├── go.mod                  # Go module dependencies
├── kafka_producer_test.go  # Test event producer
├── docker-compose.yml      # Infrastructure setup
└── README.md              # This file

/tests.py                   # Comprehensive pytest test suite
/weights.json              # Test importance weights
/prompt.md                 # Task description
/dockerfile               # Ubuntu container with Go, Kafka, PostgreSQL
```

## Solution Verification Checklist

- [ ] All pytest tests pass
- [ ] `go run -race` shows no data races
- [ ] Inventory remains consistent under concurrent load
- [ ] Duplicate Kafka messages are not double-processed
- [ ] No deadlocks observed in stress tests
- [ ] Offset commits happen after database writes
- [ ] Performance degradation < 5% vs buggy version

## Additional Resources

- [Go Data Race Detector](https://go.dev/blog/race-detector)
- [PostgreSQL Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html)
- [Kafka Exactly-Once Semantics](https://kafka.apache.org/documentation/#semantics)
- [Designing Data-Intensive Applications, Chapter 7 (Transactions)](https://dataintensive.net/)

## Support

For issues or questions:
1. Check that all infrastructure is running: `docker-compose ps`
2. Review error logs: `docker-compose logs [service_name]`
3. Verify database connectivity: `psql` connection test
4. Run individual tests for isolation: `pytest tests.py::TestRaceConditionDetection::test_concurrent_updates_consistency -v`
