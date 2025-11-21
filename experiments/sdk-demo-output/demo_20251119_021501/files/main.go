package main

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"os"
	"os/signal"
	"sync"
	"sync/atomic"
	"syscall"

	"github.com/confluentinc/confluent-kafka-go/v2/kafka"
	_ "github.com/lib/pq"
)

// InventoryConsumer represents the Kafka consumer for inventory updates
type InventoryConsumer struct {
	consumer       *kafka.Consumer
	db             *sql.DB
	// BUG: This map doesn't protect concurrent access to inventory state
	inventoryLock  sync.Mutex
	metrics        *Metrics
}

// Metrics tracks consumer performance
type Metrics struct {
	messagesProcessed  int64
	racesDetected      int64
	dataInconsistencies int64
}

// InventoryEvent represents an inventory update event from Kafka
type InventoryEvent struct {
	ProductID      string `json:"product_id"`
	QuantityChange int    `json:"quantity_change"`
	EventID        string `json:"event_id"`
}

// Product represents a product record in the database
type Product struct {
	ID           int
	SKU          string
	CurrentStock int
	Version      int
}

func NewInventoryConsumer(brokers, groupID string) (*InventoryConsumer, error) {
	// Configure Kafka consumer
	config := kafka.ConfigMap{
		"bootstrap.servers": brokers,
		"group.id":          groupID,
		"auto.offset.reset": "earliest",
		"isolation.level":   "read_committed",
	}

	consumer, err := kafka.NewConsumer(&config)
	if err != nil {
		return nil, fmt.Errorf("failed to create consumer: %w", err)
	}

	return &InventoryConsumer{
		consumer: consumer,
		metrics:  &Metrics{},
	}, nil
}

// ConnectDB establishes connection to PostgreSQL
func (ic *InventoryConsumer) ConnectDB(dsn string) error {
	db, err := sql.Open("postgres", dsn)
	if err != nil {
		return err
	}

	if err := db.Ping(); err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}

	ic.db = db
	return nil
}

// InitSchema creates the products table if it doesn't exist
func (ic *InventoryConsumer) InitSchema() error {
	schema := `
	CREATE TABLE IF NOT EXISTS products (
		id SERIAL PRIMARY KEY,
		sku VARCHAR(100) UNIQUE NOT NULL,
		current_stock INTEGER NOT NULL DEFAULT 0,
		version INTEGER NOT NULL DEFAULT 0,
		updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		last_event_id VARCHAR(255)
	);

	CREATE TABLE IF NOT EXISTS processed_events (
		event_id VARCHAR(255) PRIMARY KEY,
		product_id VARCHAR(100) NOT NULL,
		processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);
	`

	_, err := ic.db.Exec(schema)
	return err
}

// UpdateInventory processes a single inventory event
// BUG: This function has a classic read-modify-write race condition
func (ic *InventoryConsumer) UpdateInventory(ctx context.Context, event InventoryEvent) error {
	// RACE CONDITION: No per-product locking - multiple goroutines can race here
	ic.inventoryLock.Lock()
	defer ic.inventoryLock.Unlock()

	// BUG: Transaction not using proper isolation level
	tx, err := ic.db.BeginTx(ctx, nil)
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	// BUG: Check for duplicate events without proper row-level locking
	var processed bool
	err = tx.QueryRowContext(ctx,
		"SELECT COUNT(*) > 0 FROM processed_events WHERE event_id = $1",
		event.EventID).Scan(&processed)
	if err != nil && err != sql.ErrNoRows {
		return err
	}

	if processed {
		// Event already processed - but no atomic commit guarantee
		return nil
	}

	// Step 1: Read current stock (RACE CONDITION: Not locked in database)
	var currentStock int
	err = tx.QueryRowContext(ctx,
		"SELECT current_stock FROM products WHERE sku = $1",
		event.ProductID).Scan(&currentStock)
	if err != nil && err != sql.ErrNoRows {
		return fmt.Errorf("failed to read stock: %w", err)
	}

	newStock := currentStock + event.QuantityChange

	// BUG: No check for negative stock or overselling
	if newStock < 0 {
		log.Printf("WARNING: Negative stock detected for %s: %d", event.ProductID, newStock)
	}

	// Step 2: Update stock (LOST UPDATE RACE: Another goroutine might have updated between read and write)
	_, err = tx.ExecContext(ctx,
		`INSERT INTO products (sku, current_stock, version)
		 VALUES ($1, $2, 1)
		 ON CONFLICT (sku) DO UPDATE SET
		 current_stock = products.current_stock + $3,
		 version = products.version + 1`,
		event.ProductID, newStock, event.QuantityChange)
	if err != nil {
		return fmt.Errorf("failed to update stock: %w", err)
	}

	// BUG: Event marked as processed BEFORE Kafka offset commit
	// If we crash here, we'll reprocess the message but have already marked it
	_, err = tx.ExecContext(ctx,
		"INSERT INTO processed_events (event_id, product_id) VALUES ($1, $2)",
		event.EventID, event.ProductID)
	if err != nil {
		return fmt.Errorf("failed to mark event processed: %w", err)
	}

	// BUG: Commit happens before offset commit - potential message loss
	err = tx.Commit()
	if err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}

	atomic.AddInt64(&ic.metrics.messagesProcessed, 1)
	return nil
}

// ConsumeMessages starts consuming messages from Kafka
func (ic *InventoryConsumer) ConsumeMessages(ctx context.Context, topicName string, numWorkers int) error {
	err := ic.consumer.SubscribeTopics([]string{topicName}, nil)
	if err != nil {
		return fmt.Errorf("failed to subscribe: %w", err)
	}

	// BUG: Using unbounded goroutines without proper worker pool limits
	// This can cause goroutine explosion and make the race condition worse
	msgChan := make(chan *kafka.Message, 100)
	var wg sync.WaitGroup

	// Start worker goroutines - but they all share the global lock!
	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		go ic.messageWorker(ctx, &wg, msgChan)
	}

	// Main consumer loop
	go func() {
		for {
			select {
			case <-ctx.Done():
				ic.consumer.Close()
				close(msgChan)
				return
			default:
				msg, err := ic.consumer.ReadMessage(100 * 1000) // 100ms timeout
				if err != nil {
					if err.(kafka.Error).Code() != kafka.ErrTimedOut {
						log.Printf("Consumer error: %v", err)
					}
					continue
				}
				msgChan <- msg
			}
		}
	}()

	wg.Wait()
	return nil
}

// messageWorker processes messages from the channel
func (ic *InventoryConsumer) messageWorker(ctx context.Context, wg *sync.WaitGroup, msgChan chan *kafka.Message) {
	defer wg.Done()

	for msg := range msgChan {
		// Parse message value as JSON
		event := InventoryEvent{
			ProductID:      string(msg.Headers[0].Value),
			QuantityChange: int(msg.Value[0]), // Simplified parsing - BUG in real code
			EventID:        string(msg.Key),
		}

		// BUG: No timeout or context propagation
		err := ic.UpdateInventory(ctx, event)
		if err != nil {
			log.Printf("Error updating inventory: %v", err)
			// BUG: No retry logic or dead letter queue
		}

		// BUG: Offset commit happens AFTER processing, not atomically with database write
		// If service crashes, we lose the offset but have updated the database
		_, err = ic.consumer.CommitMessage(msg)
		if err != nil {
			log.Printf("Failed to commit offset: %v", err)
		}
	}
}

// GetInventory retrieves the current inventory for a product
// BUG: This read operation doesn't use read lock, can read while Write is happening
func (ic *InventoryConsumer) GetInventory(ctx context.Context, sku string) (int, error) {
	ic.inventoryLock.Lock() // Should be RLock for read operations
	defer ic.inventoryLock.Unlock()

	var stock int
	err := ic.db.QueryRowContext(ctx, "SELECT current_stock FROM products WHERE sku = $1", sku).Scan(&stock)
	if err != nil {
		return 0, err
	}
	return stock, nil
}

// GetMetrics returns current metrics
func (ic *InventoryConsumer) GetMetrics() map[string]interface{} {
	return map[string]interface{}{
		"messages_processed": atomic.LoadInt64(&ic.metrics.messagesProcessed),
	}
}

func main() {
	// Configuration
	brokers := os.Getenv("KAFKA_BROKERS")
	if brokers == "" {
		brokers = "localhost:9092"
	}

	groupID := os.Getenv("KAFKA_GROUP_ID")
	if groupID == "" {
		groupID = "inventory-consumer-group"
	}

	dsn := os.Getenv("DATABASE_URL")
	if dsn == "" {
		dsn = "postgres://postgres:postgres@localhost:5432/inventory?sslmode=disable"
	}

	// Create consumer
	consumer, err := NewInventoryConsumer(brokers, groupID)
	if err != nil {
		log.Fatalf("Failed to create consumer: %v", err)
	}

	// Connect to database
	if err := consumer.ConnectDB(dsn); err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer consumer.db.Close()

	// Initialize schema
	if err := consumer.InitSchema(); err != nil {
		log.Fatalf("Failed to initialize schema: %v", err)
	}

	// Setup graceful shutdown
	ctx, cancel := context.WithCancel(context.Background())
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-sigChan
		log.Println("Shutting down...")
		cancel()
	}()

	// Start consuming messages
	numWorkers := 4
	if err := consumer.ConsumeMessages(ctx, "inventory-events", numWorkers); err != nil {
		log.Fatalf("Error consuming messages: %v", err)
	}

	log.Println("Consumer stopped")
}
