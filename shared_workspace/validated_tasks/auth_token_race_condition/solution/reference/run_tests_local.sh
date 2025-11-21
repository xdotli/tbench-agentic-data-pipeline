#!/bin/bash
set -e

echo "Starting Redis..."
./start_redis.sh

echo "Starting FastAPI gateway..."
./start_gateway.sh &
GATEWAY_PID=$!

# Wait for gateway to start
sleep 5

echo "Running tests..."
python -m pytest test_concurrent_refresh.py -v -s

# Cleanup
kill $GATEWAY_PID || true
redis-cli shutdown || true

echo "Tests completed!"
