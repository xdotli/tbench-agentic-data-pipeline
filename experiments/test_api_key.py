#!/usr/bin/env python3
"""Simple test to verify API key works"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('ANTHROPIC_API_KEY')
print(f"API Key loaded: {api_key[:20]}...{api_key[-10:]}")
print(f"Length: {len(api_key)}")

# Try a direct API call
url = "https://api.anthropic.com/v1/messages"
headers = {
    "x-api-key": api_key,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json"
}
data = {
    "model": "claude-3-haiku-20240307",
    "max_tokens": 10,
    "messages": [{"role": "user", "content": "Hi"}]
}

print("\nTesting API key with direct HTTP call...")
try:
    response = httpx.post(url, headers=headers, json=data, timeout=30.0)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ API key is valid!")
        print(f"Response: {response.json()}")
    else:
        print(f"❌ API key rejected: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")
