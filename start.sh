#!/bin/bash

echo "🚀 Starting Quick File Transfer..."
echo ""

# Make sure we're in the right directory
cd "$(dirname "$0")"

# Check if Python 3 is available
if command -v python3 &> /dev/null; then
    python3 server.py
elif command -v python &> /dev/null; then
    python server.py
else
    echo "❌ Python not found! Please install Python 3 to run this server."
    exit 1
fi
