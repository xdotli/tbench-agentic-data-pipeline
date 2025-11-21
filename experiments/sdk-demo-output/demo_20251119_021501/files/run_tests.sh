#!/bin/bash

# Test runner script for inventory service

set -e

echo "=========================================="
echo "Inventory Service - Race Condition Tests"
echo "=========================================="
echo ""

# Check if PostgreSQL is running
echo "Checking PostgreSQL connection..."
if ! psql -h localhost -U postgres -d postgres -c "SELECT 1" &> /dev/null; then
    echo "❌ PostgreSQL not running on localhost:5432"
    echo "Start with: docker-compose up -d postgres"
    exit 1
fi
echo "✓ PostgreSQL is ready"
echo ""

# Check if Kafka is running
echo "Checking Kafka connection..."
if ! timeout 5 bash -c "echo > /dev/tcp/localhost/9092" &> /dev/null; then
    echo "⚠ Kafka not running on localhost:9092"
    echo "Start with: docker-compose up -d kafka"
    echo "Note: Some tests may still run without Kafka"
    echo ""
else
    echo "✓ Kafka is ready"
    echo ""
fi

# Run pytest tests
echo "Running pytest test suite..."
echo ""

export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=inventory_test
export DB_USER=postgres
export DB_PASSWORD=postgres
export KAFKA_BROKERS=localhost:9092

# Run all tests with verbose output
pytest tests.py -v \
    --tb=short \
    --color=yes \
    -x

echo ""
echo "=========================================="
echo "Test run complete!"
echo "=========================================="
