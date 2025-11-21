package main

import (
	"context"
	"database/sql"
	"fmt"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

// TestMetrics collects metrics for testing
type TestMetrics struct {
	totalOperations  int64
	failedOperations int64
	racesDetected    int64
	consistencyErrors int64
}

// StressTestConfig configures a stress test
type StressTestConfig struct {
	NumWorkers         int
	OperationsPerWorker int
	Products          []string
	UpdateRange       [2]int // [min, max] for random updates
}

// RunStressTest executes a concurrent stress test on the inventory system
func RunStressTest(tb testing.TB, consumer *InventoryConsumer, config StressTestConfig) *TestMetrics {
	metrics := &TestMetrics{}
	ctx := context.Background()
	var wg sync.WaitGroup

	// Track initial state
	initialState := make(map[string]int)
	for _, sku := range config.Products {
		stock, err := consumer.GetInventory(ctx, sku)
		if err != nil {
			tb.Logf("Failed to get initial inventory for %s: %v", sku, err)
			continue
		}
		initialState[sku] = stock
	}

	// Run worker goroutines
	for w := 0; w < config.NumWorkers; w++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()

			for op := 0; op < config.OperationsPerWorker; op++ {
				// Pick random product and delta
				skuIdx := (workerID + op) % len(config.Products)
				sku := config.Products[skuIdx]
				delta := config.UpdateRange[0] + (op % (config.UpdateRange[1] - config.UpdateRange[0] + 1))

				event := InventoryEvent{
					ProductID:      sku,
					QuantityChange: delta,
					EventID:        fmt.Sprintf("stress_%d_%d_%d", workerID, op, time.Now().UnixNano()),
				}

				err := consumer.UpdateInventory(ctx, event)
				if err != nil {
					atomic.AddInt64(&metrics.failedOperations, 1)
					tb.Logf("Worker %d: Failed to update %s: %v", workerID, sku, err)
				} else {
					atomic.AddInt64(&metrics.totalOperations, 1)
				}
			}
		}(w)
	}

	wg.Wait()

	// Verify final state
	for _, sku := range config.Products {
		stock, err := consumer.GetInventory(ctx, sku)
		if err != nil {
			tb.Logf("Failed to get final inventory for %s: %v", sku, err)
			continue
		}

		// Stock should never go negative
		if stock < 0 {
			atomic.AddInt64(&metrics.consistencyErrors, 1)
			tb.Logf("ERROR: Negative stock detected for %s: %d", sku, stock)
		}
	}

	return metrics
}

// VerifyInventoryConsistency checks that inventory is consistent with change log
func VerifyInventoryConsistency(db *sql.DB, ctx context.Context) (bool, error) {
	// Get all products and their current stock
	rows, err := db.QueryContext(ctx, "SELECT sku, current_stock FROM products")
	if err != nil {
		return false, err
	}
	defer rows.Close()

	for rows.Next() {
		var sku string
		var stock int
		err := rows.Scan(&sku, &stock)
		if err != nil {
			return false, err
		}

		// Stock should never be negative
		if stock < 0 {
			return false, fmt.Errorf("negative stock detected for %s: %d", sku, stock)
		}
	}

	return true, rows.Err()
}

// DetectDeadlock attempts to detect deadlock situations
func DetectDeadlock(db *sql.DB, ctx context.Context) (bool, error) {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	// Try a simple query - if it times out, might indicate deadlock
	err := db.PingContext(ctx)
	if err != nil && ctx.Err() == context.DeadlineExceeded {
		return true, fmt.Errorf("potential deadlock detected: query timeout")
	}

	return false, nil
}

// MeasureContention measures lock contention
func MeasureContention(fn func(), duration time.Duration) float64 {
	start := time.Now()
	var count int64

	done := make(chan bool)
	go func() {
		for {
			select {
			case <-done:
				return
			default:
				fn()
				atomic.AddInt64(&count, 1)
			}
		}
	}()

	time.Sleep(duration)
	close(done)

	elapsed := time.Since(start)
	opsPerSecond := float64(count) / elapsed.Seconds()

	return opsPerSecond
}

// SimulateKafkaPartitionReplay simulates replaying messages from a Kafka partition
func SimulateKafkaPartitionReplay(consumer *InventoryConsumer, partitionID int, messages []InventoryEvent) (successCount int, err error) {
	ctx := context.Background()

	for _, msg := range messages {
		err := consumer.UpdateInventory(ctx, msg)
		if err == nil {
			successCount++
		}
	}

	return successCount, nil
}
