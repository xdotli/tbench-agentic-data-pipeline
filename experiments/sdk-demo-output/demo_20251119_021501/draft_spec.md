# Debug Go Microservice with Message Queue Race Condition

## Title
Fix Race Condition in Go Kafka Consumer for Real-Time Inventory Updates

## Description
A Go-based microservice consumes inventory change events from Apache Kafka and updates a PostgreSQL database. When high-throughput events arrive concurrently (multiple partitions), the inventory count becomes inconsistent—overselling products, showing negative stock, or missing updates. The issue stems from unsafe concurrent access to shared inventory state and improper transaction handling. Debug and fix the race condition by implementing proper locking mechanisms, atomic operations, and idempotent message processing.

## Target Difficulty
~20% pass rate for SOTA models

## Technologies Involved
- **Language:** Go (golang)
- **Message Queue:** Apache Kafka
- **Database:** PostgreSQL with transactions
- **Concurrency Primitives:** sync.Mutex, sync.RWMutex, atomic operations
- **Testing:** Go testing framework with goroutine stress tests
- **Monitoring:** Prometheus metrics for race detection

## Core Skills Being Tested

### 1. Concurrency Debugging
- Identifying data races in Go programs using `go run -race`
- Understanding goroutine synchronization issues
- Recognizing patterns of non-atomic read-modify-write operations

### 2. Distributed System Challenges
- Handling concurrent updates from multiple Kafka partitions
- Ensuring idempotent message processing (handling duplicates)
- Managing offset commits atomically with database updates

### 3. Database Transaction Management
- Using PostgreSQL transactions to prevent dirty reads
- Implementing serializable isolation levels for critical operations
- Handling deadlocks and retry logic

### 4. Locking Strategies
- Choosing between sync.Mutex and sync.RWMutex for performance
- Implementing fine-grained locking to avoid bottlenecks
- Detecting and preventing deadlocks in complex scenarios

### 5. Testing & Verification
- Writing concurrent unit tests that reliably reproduce race conditions
- Using stress testing to verify fixes
- Validating inventory consistency under high load

## Problem Context

**Backend Service Architecture:**
- Go microservice with Kafka consumer group reading from `inventory-events` topic
- Consumer processes 4+ partitions concurrently
- Events: `{"product_id": "SKU123", "quantity_change": +5}` or `-3`
- Database schema: `products(id, sku, current_stock, version, updated_at)`

**Current Bug Manifestation:**
```
Request 1 (Thread A): Read stock=100 → Process +10 → Write stock=110
Request 2 (Thread B): Read stock=100 → Process -5 → Write stock=95
Expected final state: stock=105
Actual final state: stock=95 (lost update from Thread A)
```

**Additional Complexities:**
- Kafka offset must be committed AFTER database write (exactly-once semantics)
- Multiple SKUs being updated concurrently may cause deadlocks
- Consumer lag monitoring shows inconsistent inventory deltas

## Expected Solution Approach

1. Identify the race condition using Go race detector
2. Implement per-product locking using sync.Mutex with product ID as key
3. Use database transactions with appropriate isolation levels
4. Ensure idempotency through version numbers or deduplication IDs
5. Atomically commit Kafka offsets after successful DB write
6. Add comprehensive tests simulating concurrent Kafka partitions
7. Verify no deadlocks or data inconsistencies under stress

## Evaluation Criteria

- ✅ Race condition eliminated (verified with `go run -race`)
- ✅ No data corruption under high concurrent load
- ✅ Proper offset management (no message loss or duplication)
- ✅ Performance acceptable (< 5% throughput degradation vs buggy version)
- ✅ Code includes tests that verify concurrency safety
- ✅ Clear documentation of locking strategy
