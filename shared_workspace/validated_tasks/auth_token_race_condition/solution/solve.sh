#!/bin/bash
# Solution: Restore the correct token_service.py with atomic Redis operations

# Copy the working implementation with Lua script for atomic refresh
cp /solution/reference/auth_gateway/token_service.py /workspace/auth_gateway/token_service.py

# Restart the gateway to load the fixed code
pkill -f uvicorn
sleep 2
cd /workspace && python -m uvicorn auth_gateway.main:app --host 0.0.0.0 --port 8000 --workers 3 &

sleep 3
echo "Fixed: Restored atomic token refresh implementation using Redis Lua scripts"
