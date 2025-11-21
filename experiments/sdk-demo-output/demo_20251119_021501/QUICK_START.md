# Quick Start Guide

## What is This Datapoint?

A challenging debugging exercise for a Go microservice with **race conditions in a Kafka consumer**. The service updates product inventory in PostgreSQL but has critical concurrency bugs causing:

- Lost updates under concurrent load
- Duplicate message processing
- Negative inventory
- Data corruption

**Expected pass rate**: ~20% for SOTA models (difficult!)

## Files at a Glance

| File | Purpose |
|------|---------|
| **prompt.md** | 1-3 sentence task description |
| **tests.py** | 30+ pytest tests that fail initially |
| **weights.json** | Test importance weights (sums to 1.0) |
| **dockerfile** | Ubuntu 24.04 container with all dependencies |
| **files/main.go** | Broken Go code with 12+ documented bugs |
| **files/docker-compose.yml** | Kafka + PostgreSQL infrastructure |
| **files/README.md** | Full documentation + fix guide |

## Quick Test

```bash
cd /Users/suzilewie/benchflow/datagen/.conductor/accra/sdk_demo_output/demo_20251119_021501

# 1. Start infrastructure
docker-compose -f files/docker-compose.yml up -d

# 2. Wait for services
sleep 10

# 3. Run tests (most will FAIL with buggy code)
python -m pytest tests.py -v

# 4. See the race condition
cd files && go run -race main.go
```

## The Main Bug

```go
// BROKEN: Global lock, non-atomic read-modify-write
ic.inventoryLock.Lock()
current := readFromDB()  // T1 reads 100
// ... another thread reads 100 and modifies ...
writeTooDB(current + delta)  // T2 writes, T1's update lost!
ic.inventoryLock.Unlock()
```

## Fix Overview (3 Key Steps)

### 1. Per-Product Locking
```go
// Instead of: inventoryLock sync.Mutex (one lock for ALL)
// Use:       locks sync.Map // map[sku] -> *sync.Mutex
```

### 2. Atomic Database Updates
```go
// Instead of: READ, MODIFY in code, WRITE
// Use:       UPDATE products SET stock = stock + ? WHERE sku = ?
```

### 3. Transaction Isolation
```go
// Instead of: tx := db.BeginTx(ctx, nil)
// Use:       tx := db.BeginTx(ctx, &sql.TxOptions{
//                Isolation: sql.LevelSerializable,
//            })
```

## Test Categories (10 Tests)

| Category | Weight | Tests If... |
|----------|--------|------------|
| Race Conditions | 0.45 | Concurrent updates lose data |
| Idempotency | 0.20 | Duplicate messages are processed twice |
| Isolation | 0.10 | Wrong transaction level allows dirty reads |
| Locking | 0.05 | Global lock hurts concurrency |
| Atomic Ops | 0.05 | Operations aren't atomic |
| Consumer | 0.05 | Kafka offset management is wrong |
| Load Stress | 0.10 | Data corrupts under load |

## Expected Results

### ❌ BEFORE Fix
```
FAILED test_concurrent_updates_consistency
  AssertionError: Lost updates detected: expected 126, got 98

FAILED test_concurrent_partition_simulation
  AssertionError: Stock went negative: -15

... (6-7 tests fail)

go run -race main.go
  WARNING: DATA RACE ...
```

### ✅ AFTER Fix
```
test_no_race_with_sequential_updates PASSED
test_concurrent_updates_consistency PASSED
test_concurrent_partition_simulation PASSED
... (all 10 tests pass)

go run -race main.go
  (no warnings!)
```

## Documentation Map

**For Understanding:**
- `prompt.md` - What to do (1 sentence)
- `files/README.md` - Full context + fix guide (read first!)
- `DATAPOINT_SUMMARY.md` - Deep dive into bugs and solutions

**For Debugging:**
- `files/main.go` - Look for `// BUG:` comments (12 of them!)
- `tests.py` - See what tests expect to pass

**For Verification:**
- `weights.json` - Test importance scoring
- `MANIFEST.md` - Complete file checklist

## Key Insight

The bugs test **distributed systems** thinking:

1. **Concurrency** - Go goroutines + sync primitives
2. **Persistence** - PostgreSQL transactions
3. **Message Queue** - Kafka exactly-once semantics
4. **Correctness** - No lost updates, no duplicates
5. **Performance** - Fast despite safety mechanisms

A common SOTA mistake: Use a **global mutex** for simplicity, but that fails the concurrency tests and the load stress test. The fix requires **per-product locking** for good throughput.

## Success Checklist

- [ ] All 10 tests pass: `pytest tests.py -v`
- [ ] No races detected: `go run -race main.go` (runs clean)
- [ ] Understand the bugs (read main.go comments)
- [ ] Understand the fix (read README.md guide)
- [ ] Code is well-documented
- [ ] Performance is acceptable

## Time Estimate

- **Understanding the problem**: 10-15 min (read prompt, README, main.go)
- **Running tests**: 2-5 min (setup containers, run tests)
- **Implementing fix**: 30-60 min (depends on experience)
- **Verification**: 5 min (run tests, verify no races)

**Total**: ~1-2 hours for skilled developers, 2-4 hours for less experienced

## Common Mistakes

❌ **Global Mutex Only**
- Simple but fails concurrency tests
- No parallelism for different products

❌ **Forgot Transaction Isolation**
- Uses default READ_COMMITTED
- Still allows dirty reads

❌ **Wrong Offset Commit Order**
- Commits before DB write
- Duplicates on crash/replay

❌ **No Deduplication Locking**
- Check and insert can race
- Same message processed twice

## Pro Tips

1. **Start with the test output** - Error messages point to specific bugs
2. **Use `go run -race`** - Immediately shows data races
3. **Read the README** - Has code examples for every fix
4. **Test iteratively** - Fix one bug, run tests, repeat
5. **Check weights** - Focus on high-weight tests first

## Useful Commands

```bash
# Run specific test category
pytest tests.py::TestRaceConditionDetection -v

# Run with detailed output
pytest tests.py -v -s

# Stop at first failure
pytest tests.py -x

# Run race detector
go run -race main.go

# Connect to test database
psql postgres://postgres:postgres@localhost:5432/inventory_test

# View Kafka topics
kafka-topics.sh --bootstrap-server localhost:9092 --list
```

## Need Help?

1. **Understanding the bug**: Read inline comments in `main.go`
2. **How to fix**: See "Expected Solution Approach" in `DATAPOINT_SUMMARY.md`
3. **Code examples**: Check `files/README.md` section "Fix Implementation Guide"
4. **Test details**: Read docstrings in `tests.py`

---

**Status**: ✅ Ready to use
**Difficulty**: ~20% pass rate (challenging)
**Skills Tested**: Go concurrency, distributed systems, database transactions, debugging
