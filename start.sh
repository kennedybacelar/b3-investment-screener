#!/bin/bash
# Quick start script for B3 Investment Screener

echo "🚀 Starting B3 Investment Screener..."
echo ""

# Check if dependencies are installed
if ! python -c "import fastapi" &> /dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

echo "🌐 Starting server on http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

uvicorn app:app --reload --host 127.0.0.1 --port 8000
