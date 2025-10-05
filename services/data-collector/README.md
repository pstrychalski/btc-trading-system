# 📡 Data Collector Service

Real-time market data collector from Binance WebSocket API with automatic validation using Great Expectations.

## 🚀 Features

- **WebSocket Streaming**: Real-time data from Binance
- **Multiple Symbols**: BTC, ETH, and more
- **Multiple Intervals**: 1m, 5m, 15m, 1h candlesticks
- **Automatic Validation**: Integration with Data Validation Service
- **Redis Queue**: Fast message queue and stream
- **Reconnection Logic**: Automatic reconnect on disconnection
- **Health Monitoring**: REST API for status and metrics
- **Prometheus Metrics**: Integration with monitoring stack

## 🔧 Configuration

### Environment Variables

```bash
# Symbols to collect (comma-separated)
SYMBOLS=BTCUSDT,ETHUSDT,BNBUSDT

# Intervals to collect (comma-separated)
INTERVALS=1m,5m,15m,1h

# Redis connection
REDIS_URL=redis://localhost:6379

# Data Validation Service URL
VALIDATION_SERVICE_URL=http://data-validation:8000

# Optional: Binance API credentials (for authenticated endpoints)
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
```

## 📊 Data Flow

```
┌──────────────────────────────────────────────┐
│           Binance WebSocket API              │
│                                              │
│  • Kline/Candlestick streams                │
│  • Trade streams                             │
│  • Ticker streams                            │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│         Data Collector Service               │
│                                              │
│  1. Receive WebSocket messages              │
│  2. Parse and normalize data                │
│  3. Validate with Great Expectations        │
│  4. Store in Redis                          │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│              Redis Queues                    │
│                                              │
│  • kline:{symbol}:{interval}:{timestamp}    │
│  • stream:{symbol} - Real-time stream       │
│  • trades:{symbol} - Trade stream           │
│  • latest:{symbol} - Latest price/volume    │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│         Downstream Services                  │
│                                              │
│  • Pathway (Real-time pipeline)             │
│  • Market Memory (Vector storage)           │
│  • Backtrader (Backtesting)                 │
│  • RL Agent (Training)                      │
└──────────────────────────────────────────────┘
```

## 🎯 Data Structures

### Kline/Candlestick Data

```json
{
  "symbol": "BTCUSDT",
  "timestamp": "2024-01-01T12:00:00+00:00",
  "interval": "1m",
  "open": 45123.45,
  "high": 45200.00,
  "low": 45100.00,
  "close": 45180.50,
  "volume": 123.456,
  "trades": 1234,
  "is_closed": true,
  "quote_volume": 5567890.12,
  "taker_buy_base_volume": 61.728,
  "taker_buy_quote_volume": 2783945.06
}
```

### Trade Data

```json
{
  "symbol": "BTCUSDT",
  "timestamp": "2024-01-01T12:00:00.123+00:00",
  "trade_id": 123456789,
  "price": 45180.50,
  "quantity": 0.123,
  "buyer_order_id": 987654321,
  "seller_order_id": 123456789,
  "is_buyer_maker": true
}
```

## 📡 API Endpoints

### Health Check

```bash
GET /health

Response:
{
  "status": "healthy",
  "service": "data-collector",
  "environment": "production",
  "collector_running": true,
  "messages_received": 12345,
  "messages_validated": 12340,
  "validation_errors": 5
}
```

### Metrics

```bash
GET /metrics

Response:
{
  "messages_received": 12345,
  "messages_validated": 12340,
  "validation_errors": 5,
  "validation_success_rate": 99.96,
  "last_message_seconds_ago": 1.23,
  "is_running": true,
  "symbols": ["BTCUSDT", "ETHUSDT"],
  "intervals": ["1m", "5m", "15m", "1h"]
}
```

### Status

```bash
GET /status

Response:
{
  "running": true,
  "symbols": ["BTCUSDT", "ETHUSDT"],
  "intervals": ["1m", "5m", "15m", "1h"],
  "redis_url": "redis://redis:6379",
  "validation_service_url": "http://data-validation:8000",
  "metrics": { ... }
}
```

### Control (Development only)

```bash
POST /control
{
  "action": "stop"  # or "start"
}

Response:
{
  "status": "stopped"
}
```

### Prometheus Metrics

```bash
GET /metrics/prometheus

Response:
# HELP data_collector_messages_received_total Total messages received
# TYPE data_collector_messages_received_total counter
data_collector_messages_received_total 12345.0

# HELP data_collector_messages_validated_total Total messages validated
# TYPE data_collector_messages_validated_total counter
data_collector_messages_validated_total 12340.0

...
```

## 🐳 Docker Deployment

```bash
# Build image
docker build -t btc-data-collector .

# Run container
docker run -d \
  --name data-collector \
  -p 8001:8001 \
  -e SYMBOLS=BTCUSDT,ETHUSDT \
  -e INTERVALS=1m,5m,15m \
  -e REDIS_URL=redis://redis:6379 \
  -e VALIDATION_SERVICE_URL=http://data-validation:8000 \
  btc-data-collector
```

## 🧪 Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SYMBOLS=BTCUSDT
export INTERVALS=1m,5m
export REDIS_URL=redis://localhost:6379
export VALIDATION_SERVICE_URL=http://localhost:8000

# Run service
python api.py

# Or with uvicorn for development
uvicorn api:app --reload --port 8001
```

## 📈 Monitoring

### Check if collector is running

```bash
curl http://localhost:8001/health
```

### View real-time metrics

```bash
watch -n 1 'curl -s http://localhost:8001/metrics | jq'
```

### Monitor Redis streams

```bash
# Watch latest prices
redis-cli --json GET latest:BTCUSDT

# Monitor stream
redis-cli XREAD BLOCK 0 STREAMS stream:BTCUSDT $

# Count messages in stream
redis-cli XLEN stream:BTCUSDT
```

## 🔍 Troubleshooting

### No messages received

```bash
# Check Binance API status
curl https://api.binance.com/api/v3/ping

# Check WebSocket connection
curl http://localhost:8001/status
```

### Validation errors

```bash
# Check validation service health
curl http://localhost:8000/health

# View recent validation errors
curl http://localhost:8001/metrics | jq '.validation_errors'
```

### Redis connection issues

```bash
# Test Redis connection
redis-cli -u $REDIS_URL ping

# Check Redis memory usage
redis-cli INFO memory
```

## 🎨 Integration Examples

### Python Client

```python
import redis
import json

# Connect to Redis
r = redis.from_url("redis://localhost:6379")

# Get latest price
latest = r.hgetall("latest:BTCUSDT")
print(f"BTC Price: ${latest['price']}")

# Subscribe to real-time stream
for message in r.xread({"stream:BTCUSDT": "$"}, block=0):
    stream_name, messages = message
    for msg_id, data in messages:
        market_data = json.loads(data['data'])
        print(f"New candle: {market_data}")
```

### Consume with Pathway

```python
import pathway as pw

# Read from Redis stream
table = pw.io.redis.read(
    rdxclient,
    stream="stream:BTCUSDT",
    format="json"
)

# Process real-time data
result = table.select(
    symbol=pw.this.symbol,
    price=pw.this.close,
    volume=pw.this.volume
)
```

## 📚 Resources

- [Binance WebSocket API Docs](https://binance-docs.github.io/apidocs/spot/en/#websocket-market-streams)
- [python-binance Documentation](https://python-binance.readthedocs.io/)
- [Redis Streams](https://redis.io/docs/data-types/streams/)
- [Great Expectations](https://docs.greatexpectations.io/)

## 🔧 Advanced Configuration

### Custom Validation Rules

Edit the Data Validation Service to add custom rules for your use case.

### Multiple Exchange Support

Extend `BinanceDataCollector` to support other exchanges like Coinbase, Kraken, etc.

### Data Persistence

Add PostgreSQL writer to store historical data for backtesting:

```python
# In collector.py
async def store_in_postgres(self, data: Dict):
    async with self.pg_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO market_data_ohlcv 
            (symbol, timestamp, open, high, low, close, volume, interval)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, data['symbol'], data['timestamp'], ...)
```

## 🚀 Performance Tips

1. **Rate Limiting**: Respect Binance rate limits (max 1000 msg/min per connection)
2. **Connection Pooling**: Reuse Redis connections
3. **Batch Processing**: Process multiple messages before validation
4. **Async I/O**: Use async/await for all I/O operations
5. **Memory Management**: Use Redis TTL to prevent memory issues

## 🔒 Security

- Never commit API keys to git
- Use environment variables or secrets management
- Validate all incoming data before processing
- Rate limit API endpoints
- Use TLS for production Redis connections

