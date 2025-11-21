#!/bin/bash
# Start Redis in background
redis-server --daemonize yes --bind 0.0.0.0 --port 6379
sleep 2
echo "Redis started"
