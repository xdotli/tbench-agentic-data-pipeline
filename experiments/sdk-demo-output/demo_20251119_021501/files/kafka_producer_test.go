package main

import (
	"encoding/json"
	"fmt"
	"testing"
	"time"

	"github.com/confluentinc/confluent-kafka-go/v2/kafka"
)

// TestProduceInventoryEvents produces test events to Kafka
func TestProduceInventoryEvents(t *testing.T) {
	producer, err := kafka.NewProducer(&kafka.ConfigMap{
		"bootstrap.servers": "localhost:9092",
	})
	if err != nil {
		t.Fatalf("Failed to create producer: %v", err)
	}
	defer producer.Close()

	// Produce test events
	events := []InventoryEvent{
		{ProductID: "SKU001", QuantityChange: 10, EventID: "event_001"},
		{ProductID: "SKU002", QuantityChange: -5, EventID: "event_002"},
		{ProductID: "SKU001", QuantityChange: 8, EventID: "event_003"},
		{ProductID: "SKU002", QuantityChange: 15, EventID: "event_004"},
		{ProductID: "SKU001", QuantityChange: -3, EventID: "event_005"},
	}

	for _, event := range events {
		msgBytes, _ := json.Marshal(event)
		err := producer.Produce(&kafka.Message{
			TopicPartition: kafka.TopicPartition{
				Topic:     &[]string{"inventory-events"}[0],
				Partition: kafka.PartitionAny,
			},
			Key:   []byte(event.EventID),
			Value: msgBytes,
		}, nil)

		if err != nil {
			t.Logf("Failed to produce event: %v", err)
		}
	}

	producer.Flush(15 * 1000)
	fmt.Println("Test events produced successfully")
}

// BenchmarkConcurrentUpdates benchmarks the performance of concurrent updates
func BenchmarkConcurrentUpdates(b *testing.B) {
	// This would require setting up a test database and Kafka broker
	// For now, it's a placeholder
	b.ReportAllocs()
}
