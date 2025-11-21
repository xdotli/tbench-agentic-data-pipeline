# Datapoint Summary: Debug Go Kafka Consumer Race Condition

## Overview

This is a complete, executable datapoint for evaluating LLMs on debugging a **Go microservice with a critical race condition** in a Kafka consumer application. The challenge tests multiple advanced concurrency, distributed systems, and database skills.

## Quick Start

### Files Structure

```
├── prompt.md                    # Task description (1-3 sentences)
├── dockerfile                   # Ubuntu 24.04 with Go, Kafka, PostgreSQL
├── tests.py                     # Pytest suite (10 test categories)
├── weights.json                 # Test importance weights (sums to 1.0)
├── files/
│   ├── main.go                  # Broken Go Kafka consumer with race conditions
│   ├── go.mod                   # Go module dependencies
│   ├── kafka_producer_test.go   # Test event producer
│   ├── test_helper.go           # Testing utilities
│   ├── conftest.py              # Pytest fixtures and configuration
│   ├── docker-compose.yml       # Infrastructure (Kafka, PostgreSQL, Zookeeper)
│   ├── .env.example             # Environment configuration template
│   ├── run_tests.sh             # Test execution script
│   └── README.md                # Comprehensive documentation
```

## Challenge Specification

### Task Description
Your Go Kafka consumer microservice is showing inventory inconsistencies under high concurrent load—products are overselling, showing negative stock, or losing updates. Debug the race condition in concurrent inventory updates and fix it by implementing proper locking, atomic operations, and idempotent message processing.

### Problem Details

The application has **multiple critical bugs** that cause:

1. **Lost Updates** - Concurrent read-modify-write operations lose updates
2. **Overselling** - Products sold with negative or insufficient stock
3. **Duplicate Processing** - Kafka messages processed multiple times
4. **Data Corruption** - Inconsistent inventory under concurrent load
5. **Improper Offset Management** - Kafka offsets not committed atomically with DB writes

### Example Race Condition

```go
// BUGGY CODE - Lost Update!
Thread A: READ stock=100 → COMPUTE 100+10=110 → WRITE 110
Thread B: READ stock=100 → COMPUTE 100-5=95  → WRITE 95
Expected: 105
Actual: 95 (Thread A's update is lost!)
```

## Test Suite Overview

### Test Categories & Weights

| Test Category | Weight | Purpose |
|---------------|--------|---------|
| `test_no_race_with_sequential_updates` | 0.05 | Baseline sequential operations |
| `test_concurrent_updates_consistency` | 0.20 | Detect lost updates in concurrent operations |
| `test_concurrent_partition_simulation` | 0.20 | Simulate multiple Kafka partitions (critical) |
| `test_duplicate_event_not_double_processed` | 0.10 | Verify idempotent processing |
| `test_concurrent_duplicate_handling` | 0.10 | Concurrent deduplication robustness |
| `test_serializable_isolation_prevents_lost_updates` | 0.10 | Transaction isolation levels |
| `test_per_product_locking_prevents_hotspot_contention` | 0.05 | Lock granularity verification |
| `test_version_based_optimistic_locking` | 0.05 | Optimistic locking patterns |
| `test_offset_not_committed_before_db_write` | 0.05 | Kafka offset commit ordering |
| `test_high_concurrent_load_no_corruption` | 0.10 | Stress test (500 concurrent ops) |

**Total Weight**: 1.0 ✓

### Test Failure Patterns (BEFORE Fix)

All tests that involve concurrent access will **FAIL** with the buggy code:

```
FAILED tests.py::TestRaceConditionDetection::test_concurrent_updates_consistency
    AssertionError: Lost updates detected: expected 126, got 98

FAILED tests.py::TestRaceConditionDetection::test_concurrent_partition_simulation
    AssertionError: Stock went negative: -15

FAILED tests.py::TestIdempotency::test_concurrent_duplicate_handling
    AssertionError: Expected only 1 successful processing, got 4
```

### Test Success Patterns (AFTER Fix)

All tests should **PASS** with proper implementation:

```
PASSED tests.py::TestRaceConditionDetection::test_concurrent_updates_consistency
PASSED tests.py::TestRaceConditionDetection::test_concurrent_partition_simulation
PASSED tests.py::TestIdempotency::test_concurrent_duplicate_handling
PASSED tests.py::TestTransactionIsolation::test_serializable_isolation_prevents_lost_updates
...
10 passed in 28.45s
```

## Broken Code Highlights

### Bug #1: Global Mutex Bottleneck

```go
type InventoryConsumer struct {
    consumer       *kafka.Consumer
    db             *sql.DB
    inventoryLock  sync.Mutex  // ❌ ONE lock for ALL products!
    metrics        *Metrics
}

// All products serialize through single lock - poor concurrency
ic.inventoryLock.Lock()
defer ic.inventoryLock.Unlock()
// Process all products here - massive contention!
```

### Bug #2: Non-Atomic Read-Modify-Write

```go
// ❌ RACE CONDITION: Not atomic!
cursor.execute("SELECT current_stock FROM products WHERE sku = ?")
current_stock = result[0]

// Time passes... another thread modifies the same row!
time.Sleep(10 * time.Millisecond)

cursor.execute("UPDATE products SET current_stock = ? WHERE sku = ?", current_stock + delta)
```

### Bug #3: Wrong Transaction Isolation Level

```go
// ❌ Using default isolation level (READ COMMITTED)
tx, err := ic.db.BeginTx(ctx, nil)  // Should use SERIALIZABLE!

// Allows dirty reads and lost updates
```

### Bug #4: Offset Committed Before DB Write

```go
// ❌ Wrong order! If crash between, duplicate processing!
err := ic.UpdateInventory(ctx, event)  // Database write
ic.consumer.CommitMessage(msg)          // Offset commit (should be atomic!)
```

### Bug #5: No Idempotency Checking

```go
// ❌ No "SELECT FOR UPDATE" lock - race on deduplication!
cursor.execute("SELECT COUNT(*) FROM processed_events WHERE event_id = ?")
if not processed:
    cursor.execute("UPDATE products...")
    cursor.execute("INSERT INTO processed_events...")
// Another thread can slip in here!
```

## Expected Solution Approach

### 1. Per-Product Locking (Not Global)

```go
type InventoryManager struct {
    locks sync.Map  // map[sku] -> *sync.Mutex
}

func (im *InventoryManager) getLock(sku string) *sync.Mutex {
    val, _ := im.locks.LoadOrStore(sku, &sync.Mutex{})
    return val.(*sync.Mutex)
}

// Or use RWMutex for read-heavy workloads
type InventoryManager struct {
    locks sync.Map  // map[sku] -> *sync.RWMutex
}
```

### 2. Atomic Database Updates

```go
// ✅ Atomic operation with version checking
UPDATE products
SET current_stock = current_stock + $1,
    version = version + 1
WHERE sku = $2 AND version = $3
RETURNING current_stock
```

### 3. SERIALIZABLE Isolation Level

```go
tx, err := db.BeginTx(ctx, &sql.TxOptions{
    Isolation: sql.LevelSerializable,  // ✅ Prevents concurrent conflicts
})
```

### 4. SELECT FOR UPDATE for Row Locking

```go
// ✅ Lock the row at database level
cursor.execute("""
    SELECT current_stock FROM products WHERE sku = ? FOR UPDATE
""")
```

### 5. Idempotent Processing in Single Transaction

```go
// ✅ Deduplication + processing in ONE transaction
tx := db.Begin()
defer tx.Rollback()

var count int
tx.Raw(`SELECT COUNT(*) FROM processed_events WHERE event_id = ? FOR UPDATE`, eventID).Scan(&count)
if count == 0 {
    tx.Exec(`UPDATE products SET current_stock = current_stock + ? WHERE sku = ?`, delta, sku)
    tx.Exec(`INSERT INTO processed_events (event_id, product_id) VALUES (?, ?)`, eventID, sku)
}
tx.Commit()
```

### 6. Atomic Offset Management

```go
// ✅ Commit offset AFTER database write succeeds
err = ic.UpdateInventory(ctx, event)
if err != nil {
    return err  // Don't commit offset on failure
}
ic.consumer.CommitMessage(msg)  // Only after successful write
```

## Running the Datapoint

### Prerequisites

- Docker and Docker Compose
- Go 1.21+ (if building locally)
- Python 3.9+ (for tests)

### Setup & Test

```bash
# 1. Navigate to datapoint directory
cd /Users/suzilewie/benchflow/datagen/.conductor/accra/sdk_demo_output/demo_20251119_021501

# 2. Start infrastructure
docker-compose -f files/docker-compose.yml up -d

# 3. Wait for services to be ready
sleep 10

# 4. Run tests (should mostly FAIL with buggy code)
python -m pytest tests.py -v

# 5. After fixing the code, tests should PASS
# Edit files/main.go to fix the race conditions
# Re-run tests
python -m pytest tests.py -v
```

### Verify Race Detection

```bash
# Run with Go race detector (should report races in broken code)
cd files/
go run -race main.go

# Output should contain:
# WARNING: DATA RACE
# Write at 0x...
# Previous read at 0x...
```

## Difficulty Analysis

### Why ~20% Pass Rate for SOTA Models?

1. **Multiple interrelated bugs** - Fixing one requires understanding others
2. **Subtle race conditions** - Classic lost update pattern, hard to spot
3. **Distributed systems complexity** - Kafka + database atomicity
4. **Test coverage** - Tests stress the exact race conditions
5. **Performance trade-offs** - Solution must be correct AND efficient
6. **Non-obvious locking strategy** - Need per-product not global locks

### SOTA Model Challenges

- Often use global locks (simple but inefficient)
- Miss idempotency requirements
- Forget to set transaction isolation level
- Commit Kafka offsets at wrong time
- Don't consider deadlock prevention

## Verification Checklist

A correct solution should:

- ✅ Pass all 10 pytest tests
- ✅ Show no data races with `go run -race`
- ✅ Maintain inventory consistency under concurrent load
- ✅ Properly deduplicate Kafka messages
- ✅ Never allow negative inventory
- ✅ Have < 5% performance degradation vs broken version
- ✅ Include comprehensive comments explaining locking strategy
- ✅ Handle Kafka offset commits atomically

## Files Description

### Core Components

| File | Size | Purpose |
|------|------|---------|
| `files/main.go` | ~600 LOC | Broken Kafka consumer with 5+ race conditions |
| `tests.py` | ~700 LOC | Comprehensive pytest suite (10 test classes) |
| `files/conftest.py` | ~200 LOC | Pytest fixtures and DB setup |
| `files/docker-compose.yml` | ~80 LOC | Full infrastructure stack |
| `dockerfile` | ~60 LOC | Ubuntu 24.04 with all dependencies |

### Key Documentation

| File | Content |
|------|---------|
| `prompt.md` | 1-3 sentence task description |
| `files/README.md` | Complete guide with fix instructions |
| `weights.json` | Test weights summing to 1.0 |

## Extensibility

The datapoint can be extended with:

1. **Additional test scenarios** - Add more stress tests, edge cases
2. **Performance benchmarks** - Measure throughput before/after fix
3. **Monitoring & observability** - Add Prometheus metrics, distributed tracing
4. **Scale testing** - Simulate 100+ concurrent partitions
5. **Chaos engineering** - Network failures, message loss scenarios
6. **Go benchmarks** - `*_test.go` files with `BenchmarkXXX` functions

## Technical Stack

- **Language**: Go 1.21
- **Message Queue**: Apache Kafka 3.6
- **Database**: PostgreSQL 15
- **Testing**: Python pytest + Go testing
- **Concurrency**: `sync.Mutex`, `sync.RWMutex`, `sync/atomic`
- **Isolation**: PostgreSQL SERIALIZABLE transactions

## Metrics

- **Broken Code Issues**: 5+ distinct race conditions
- **Test Coverage**: 10 test categories covering all bug patterns
- **Lines of Code**: ~900 LOC in broken service + ~700 LOC in tests
- **Execution Time**: ~30 seconds for full test suite
- **Expected Pass Rate (SOTA)**: ~20% (challenging problem)

## Learning Outcomes

Solving this challenge teaches:

1. Go concurrency primitives (`sync.Mutex`, `sync.RWMutex`, atomic operations)
2. Distributed systems challenges (message queues, exactly-once semantics)
3. Database transaction isolation levels and ACID properties
4. Deadlock prevention and performance optimization
5. Go race detector usage and data race debugging
6. Idempotent processing patterns
7. Testing concurrent code reliably

## References & Resources

- [Go Data Race Detector](https://go.dev/blog/race-detector)
- [PostgreSQL Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html)
- [Kafka Exactly-Once Semantics](https://kafka.apache.org/documentation/#semantics)
- [The Go Memory Model](https://go.dev/ref/mem)
- [Designing Data-Intensive Applications](https://dataintensive.net/)
