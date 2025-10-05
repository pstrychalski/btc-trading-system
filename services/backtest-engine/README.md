# 📊 Backtest Engine

Advanced backtesting service built with **Backtrader** and **MLflow** integration.

## 🎯 Features

- **Multiple Strategies**: MA Cross, RSI Mean Reversion, Bollinger Bands, MACD
- **MLflow Integration**: Automatic experiment tracking and metrics logging
- **Advanced Metrics**: Sharpe Ratio, Max Drawdown, Win Rate, Profit Factor, SQN
- **Parameter Optimization**: Grid search optimization with custom metrics
- **REST API**: FastAPI endpoints for programmatic access
- **PostgreSQL Integration**: Load historical data from database

## 🚀 Quick Start

### Local Development

```bash
# Install dependencies
cd services/backtest-engine
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost:5432/trading"
export MLFLOW_TRACKING_URI="http://localhost:5000"

# Run API server
python api.py
```

### Docker

```bash
# Build
docker build -t backtest-engine -f services/backtest-engine/Dockerfile .

# Run
docker run -p 8002:8002 \
  -e DATABASE_URL="postgresql://..." \
  -e MLFLOW_TRACKING_URI="http://mlflow:5000" \
  backtest-engine
```

## 📡 API Endpoints

### Run Backtest

```bash
POST /backtest
```

**Request:**
```json
{
  "strategy": "ma_cross",
  "symbol": "BTCUSDT",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "interval": "1h",
  "initial_cash": 100000,
  "strategy_params": {
    "fast_period": 10,
    "slow_period": 30,
    "stop_loss": 0.02
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Backtest completed successfully",
  "metrics": {
    "total_return": 0.342,
    "return_pct": 34.2,
    "sharpe_ratio": 1.85,
    "max_drawdown": 12.5,
    "win_rate": 0.62,
    "total_trades": 145,
    "profit_factor": 2.1
  }
}
```

### Optimize Strategy

```bash
POST /optimize
```

**Request:**
```json
{
  "strategy": "ma_cross",
  "symbol": "BTCUSDT",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "param_ranges": {
    "fast_period": [5, 20, 5],
    "slow_period": [20, 50, 10]
  },
  "optimization_metric": "sharpe_ratio"
}
```

### List Strategies

```bash
GET /strategies
```

## 📈 Available Strategies

### 1. Moving Average Cross (`ma_cross`)

**Parameters:**
- `fast_period`: Fast MA period (default: 10)
- `slow_period`: Slow MA period (default: 30)
- `stop_loss`: Stop loss percentage (default: 0.02)
- `take_profit`: Take profit percentage (default: 0.05)

**Logic:**
- Buy: Fast MA crosses above Slow MA
- Sell: Fast MA crosses below Slow MA, or stop loss/take profit hit

### 2. RSI Mean Reversion (`rsi_mean_reversion`)

**Parameters:**
- `rsi_period`: RSI calculation period (default: 14)
- `oversold`: Oversold threshold (default: 30)
- `overbought`: Overbought threshold (default: 70)
- `sma_period`: Trend filter period (default: 50)

**Logic:**
- Buy: RSI < oversold AND price > SMA (uptrend filter)
- Sell: RSI > overbought

### 3. Bollinger Bands (`bollinger_bands`)

**Parameters:**
- `bb_period`: BB calculation period (default: 20)
- `bb_dev`: Standard deviations (default: 2)

**Logic:**
- Buy: Price touches lower band
- Sell: Price touches upper band

### 4. MACD (`macd`)

**Parameters:**
- `macd_fast`: Fast EMA period (default: 12)
- `macd_slow`: Slow EMA period (default: 26)
- `macd_signal`: Signal line period (default: 9)

**Logic:**
- Buy: MACD line crosses above signal line
- Sell: MACD line crosses below signal line

## 🔬 Python Usage

```python
from engine import BacktestEngine, quick_backtest
from data_loader import PostgreSQLDataLoader, create_backtrader_feed

# Quick backtest
results = quick_backtest(
    strategy_name='ma_cross',
    symbol='BTCUSDT',
    start_date='2023-01-01',
    end_date='2023-12-31',
    strategy_params={'fast_period': 10, 'slow_period': 30}
)

print(f"Return: {results['metrics']['return_pct']:.2f}%")
print(f"Sharpe: {results['metrics']['sharpe_ratio']:.2f}")

# Advanced usage
engine = BacktestEngine(initial_cash=100000, commission=0.001)

loader = PostgreSQLDataLoader()
df = loader.load_ohlcv('BTCUSDT', '2023-01-01', '2023-12-31', '1h')
data_feed = create_backtrader_feed(df)

results = engine.run_backtest(
    strategy_name='rsi_mean_reversion',
    data_feed=data_feed,
    strategy_params={'rsi_period': 14, 'oversold': 25, 'overbought': 75}
)
```

## 📊 Metrics Explained

### Performance Metrics

- **Total Return**: Absolute return as decimal (0.34 = 34%)
- **Return %**: Percentage return on initial capital
- **Sharpe Ratio**: Risk-adjusted return (>1 good, >2 excellent)
- **SQN (System Quality Number)**: Quality of trading system (>2 good, >3 excellent)
- **VWR (Variability Weighted Return)**: Stability-adjusted return

### Risk Metrics

- **Max Drawdown**: Largest peak-to-trough decline (%)
- **Max DD Period**: Duration of max drawdown (days)
- **Max DD Money**: Dollar value of max drawdown

### Trading Stats

- **Total Trades**: Number of completed trades
- **Win Rate**: Percentage of winning trades
- **Profit Factor**: Gross profit / Gross loss (>1.5 good, >2 excellent)
- **Avg Win**: Average winning trade value
- **Avg Loss**: Average losing trade value

## 🎓 MLflow Integration

All backtests are automatically logged to MLflow:

- **Parameters**: Strategy type, params, initial cash, commission
- **Metrics**: All performance and risk metrics
- **Artifacts**: Strategy performance chart (PNG)

Access MLflow UI:
```bash
mlflow ui --backend-store-uri postgresql://...
# Open http://localhost:5000
```

## 🔧 Creating Custom Strategies

```python
from strategies import BaseStrategy
import backtrader as bt

class MyStrategy(BaseStrategy):
    """My custom strategy"""
    
    params = (
        ('my_param', 20),
    )
    
    def __init__(self):
        super().__init__()
        # Add indicators
        self.sma = bt.indicators.SMA(self.data.close, period=self.params.my_param)
    
    def next(self):
        """Strategy logic"""
        if not self.position:
            if self.data.close[0] > self.sma[0]:
                self.buy()
        else:
            if self.data.close[0] < self.sma[0]:
                self.sell()

# Register strategy
from strategies import STRATEGY_REGISTRY
STRATEGY_REGISTRY['my_strategy'] = MyStrategy
```

## 🧪 Testing

```bash
# Test locally with sample data
python -c "
from engine import quick_backtest
results = quick_backtest('ma_cross', 'BTCUSDT', '2023-01-01', '2023-06-01')
print(f\"Return: {results['metrics']['return_pct']:.2f}%\")
"
```

## 📦 Dependencies

- **backtrader**: Backtesting framework
- **mlflow**: Experiment tracking
- **fastapi**: REST API
- **pandas**: Data manipulation
- **ta-lib**: Technical indicators
- **matplotlib**: Charting

## 🌐 Environment Variables

```bash
DATABASE_URL=postgresql://user:pass@host:5432/db
MLFLOW_TRACKING_URI=http://mlflow:5000
PORT=8002
```

## 📝 Next Steps

- [ ] Add more strategies (momentum, breakout, etc.)
- [ ] Implement walk-forward optimization
- [ ] Add position sizing strategies
- [ ] Portfolio backtesting (multiple assets)
- [ ] Real-time paper trading mode
- [ ] Advanced risk management

## 🔗 Integration

This service integrates with:
- **Data Validation**: Validated OHLCV data
- **MLflow**: Experiment tracking
- **PostgreSQL**: Historical data storage
- **Optuna**: (Future) Advanced optimization

---

**Status**: ✅ Ready for Production Testing

