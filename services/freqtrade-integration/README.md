# 🤖 Freqtrade AI Integration

Advanced trading bot powered by Freqtrade with AI enhancements from Market Memory and RL Agent.

## 🎯 Features

### Core Trading
- **Freqtrade Framework**: Battle-tested crypto trading bot
- **Custom AI Strategy**: `AIEnhancedStrategy` with dual AI validation
- **Multi-Pair Trading**: Supports BTC/USDT, ETH/USDT, and more
- **Risk Management**: 5% stoploss, trailing stop, position sizing

### AI Integration
1. **Market Memory Risk Validation**
   - Queries similar historical patterns
   - Calculates risk score
   - Rejects high-risk trades

2. **RL Agent Signal Validation**
   - Deep learning trading signals
   - Confidence-based filtering
   - Real-time inference

3. **Dual Approval System**
   - Both AI systems must approve
   - Technical indicators as base layer
   - AI as enhancement layer

## 📊 Strategy Logic

### Entry Signal Requirements
1. **Technical Conditions** (All must be true):
   - RSI < 30 (oversold)
   - Fast EMA > Slow EMA (uptrend)
   - Volume > 20-period average (confirmation)

2. **Market Memory Approval**:
   - Risk score < 0.6 (configurable)
   - Based on similar historical patterns
   - Outcome analysis from past

3. **RL Agent Approval**:
   - Action = BUY (1)
   - Confidence > 0.7 (configurable)
   - Based on current market state

### Exit Signal
- RSI > 70 (overbought)
- Fast EMA < Slow EMA (downtrend)
- MACD bearish crossover
- Final RL confirmation

## 🔧 Configuration

### Strategy Parameters (Optimizable)
```python
risk_threshold = 0.6              # Market Memory risk threshold
rl_confidence_threshold = 0.7     # RL Agent confidence threshold
rsi_buy_threshold = 30            # RSI oversold level
rsi_sell_threshold = 70           # RSI overbought level
```

### Risk Management
```python
stoploss = -0.05                  # 5% stoploss
trailing_stop = True              # Dynamic trailing
trailing_stop_positive = 0.02     # Activate at 2% profit
minimal_roi = {
    "0": 0.10,    # 10% immediate target
    "30": 0.05,   # 5% after 30min
    "60": 0.03,   # 3% after 1h
    "120": 0.01   # 1% after 2h
}
```

## 🚀 API Endpoints

### Control API (Port 8008)
```bash
GET  /health                  # Health check
GET  /bot/status              # Bot status
GET  /bot/trades              # Current trades
POST /bot/start               # Start bot
POST /bot/stop                # Stop bot
POST /bot/reload-config       # Reload config
GET  /ai/stats                # AI system statistics
GET  /strategy/params         # Strategy parameters
POST /strategy/optimize       # Trigger Optuna optimization
```

### Freqtrade API (Port 8080)
```bash
GET  /api/v1/status           # Freqtrade status
GET  /api/v1/trades           # Trade history
POST /api/v1/start            # Start trading
POST /api/v1/stop             # Stop trading
```

## 📈 Usage Examples

### Check Bot Status
```bash
curl http://localhost:8008/bot/status
```

### Get AI Statistics
```bash
curl http://localhost:8008/ai/stats
```

### Trigger Strategy Optimization
```bash
curl -X POST http://localhost:8008/strategy/optimize
```

### Check Current Trades
```bash
curl http://localhost:8008/bot/trades
```

## 🔐 Environment Variables

```bash
# Binance API
BINANCE_API_KEY=your_api_key
BINANCE_SECRET_KEY=your_secret_key

# Service URLs
MARKET_MEMORY_URL=http://market-memory:8004
RL_AGENT_URL=http://rl-agent:8007

# API Port
PORT=8008
```

## 🐳 Docker Deployment

```bash
# Build
docker build -t freqtrade-ai -f services/freqtrade-integration/Dockerfile .

# Run
docker run -d \
  --name freqtrade-ai \
  -p 8008:8008 \
  -p 8080:8080 \
  -e BINANCE_API_KEY=your_key \
  -e BINANCE_SECRET_KEY=your_secret \
  freqtrade-ai
```

## 📊 Integration Architecture

```
┌─────────────────────────────────────────────┐
│         Freqtrade AI-Enhanced Bot           │
├─────────────────────────────────────────────┤
│                                             │
│  ┌────────────────────────────────────┐   │
│  │    AIEnhancedStrategy              │   │
│  │                                    │   │
│  │  1. Technical Analysis             │   │
│  │     ├─ RSI, MACD, BB              │   │
│  │     ├─ EMA, Volume                │   │
│  │     └─ ATR (Volatility)           │   │
│  │                                    │   │
│  │  2. Market Memory Check            │   │
│  │     ├─ Similar Pattern Search     │◄──┼─ Market Memory (8004)
│  │     ├─ Risk Score Calculation     │   │
│  │     └─ Historical Outcome Analysis│   │
│  │                                    │   │
│  │  3. RL Agent Validation            │   │
│  │     ├─ Current State Observation  │◄──┼─ RL Agent (8007)
│  │     ├─ Action Prediction (0/1/2) │   │
│  │     └─ Confidence Score           │   │
│  │                                    │   │
│  │  4. Final Decision                 │   │
│  │     └─ Trade if both AI approve   │   │
│  └────────────────────────────────────┘   │
│                                             │
│  ┌────────────────────────────────────┐   │
│  │    Control API (8008)              │   │
│  │    ├─ Status monitoring            │   │
│  │    ├─ AI statistics                │   │
│  │    └─ Trade management             │   │
│  └────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

## 🎯 AI Decision Flow

```
Market Signal
     ↓
Technical Analysis
     ├─ RSI < 30? ✓
     ├─ EMA Cross? ✓
     └─ Volume > Avg? ✓
     ↓
Market Memory API
     ├─ Find Similar Patterns
     ├─ Calculate Risk Score
     └─ Risk < 0.6? ✓/✗
     ↓
RL Agent API
     ├─ Current State Observation
     ├─ Action Prediction
     └─ Confidence > 0.7? ✓/✗
     ↓
Both AI Approve?
     ├─ YES → Execute Trade ✓
     └─ NO → Reject Signal ✗
```

## 🧪 Testing

### Dry Run Mode (Default)
```json
{
  "dry_run": true,
  "dry_run_wallet": 10000
}
```

### Backtesting
```bash
freqtrade backtesting \
  --config config.json \
  --strategy AIEnhancedStrategy \
  --timerange 20240101-20240131
```

### Hyperopt (with Optuna)
```bash
freqtrade hyperopt \
  --config config.json \
  --strategy AIEnhancedStrategy \
  --hyperopt-loss SharpeHyperOptLoss \
  --epochs 100
```

## 📝 Monitoring

### Prometheus Metrics
- `freqtrade_trades_total` - Total number of trades
- `freqtrade_trades_profit` - Current profit/loss
- `freqtrade_ai_approvals` - AI approved trades by type
- `freqtrade_ai_rejections` - AI rejected trades by type

### Logs
- Freqtrade logs: `/freqtrade/user_data/logs/freqtrade.log`
- Control API logs: stdout

## ⚠️ Important Notes

1. **Dry Run First**: Always test with `dry_run: true` before live trading
2. **API Keys**: Keep your Binance keys secure
3. **Risk Management**: Never risk more than you can afford to lose
4. **AI Validation**: Both systems must approve for trade execution
5. **Monitoring**: Regularly check bot status and AI statistics

## 🔗 Dependencies

- Market Memory Service (port 8004)
- RL Agent Service (port 8007)
- Binance API (live market data)
- PostgreSQL (via Market Memory)
- Redis (via RL Agent)

## 📚 Resources

- [Freqtrade Docs](https://www.freqtrade.io/en/stable/)
- [Strategy Development](https://www.freqtrade.io/en/stable/strategy-customization/)
- [API Documentation](https://www.freqtrade.io/en/stable/rest-api/)

