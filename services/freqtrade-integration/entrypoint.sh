#!/bin/bash
set -e

echo "🤖 Starting AI-Enhanced Trading Bot API..."

# Start Control API
echo "📊 Starting Control API on port $PORT..."
uvicorn api:app --host 0.0.0.0 --port $PORT

