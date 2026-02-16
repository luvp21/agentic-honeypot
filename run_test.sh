#!/bin/bash

# Quick Test Script - Runs automated honeypot test
# Usage: ./run_test.sh

echo "🍯 Starting Honeypot API Test..."
echo ""

# Check if server is running
if ! curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "❌ Server not running!"
    echo "💡 Start server first: python3 main.py"
    exit 1
fi

echo "✅ Server detected"
echo ""

# Run the test
python3 test_honeypot_api.py

echo ""
echo "✅ Test complete!"
