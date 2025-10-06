#!/bin/bash
set -e

echo "🤖 Starting AI-Enhanced Freqtrade Bot..."

# Start Control API in background
echo "📊 Starting Control API on port 8008..."
python /freqtrade/api.py &

# Wait a moment for API to start
sleep 2

# Start Freqtrade
echo "🚀 Starting Freqtrade with AIEnhancedStrategy..."
freqtrade trade \
    --config /freqtrade/config.json \
    --strategy AIEnhancedStrategy \
    --logfile /freqtrade/user_data/logs/freqtrade.log

# Keep container running
wait

