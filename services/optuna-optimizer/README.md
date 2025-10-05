# 🎯 Optuna Optimizer

Advanced hyperparameter optimization using **Optuna** with **walk-forward validation** and **multi-objective optimization**.

## 🚀 Features

### Walk-Forward Optimization
- Automatic data splitting into IS (In-Sample) / OOS (Out-of-Sample)
- Tests strategy robustness across multiple time periods
- Detects overfitting automatically
- Finds most consistent parameters

### Multi-Objective Optimization
- Optimize multiple metrics simultaneously
- Find Pareto optimal solutions
- Balance return vs. risk

### MLflow Integration
- All trials logged automatically
- Compare optimization runs
- Track parameter distributions

## 📊 Walk-Forward Process

```
Data: ========================

Window 1: [====IS====][==OOS==]
Window 2:       [====IS====][==OOS==]
Window 3:             [====IS====][==OOS==]
Window 4:                   [====IS====][==OOS==]
Window 5:                         [====IS====][==OOS==]

Process:
1. Optimize on IS → get best params
2. Test on OOS → validate performance
3. Repeat for all windows
4. Aggregate results → find robust params
```

## 🔧 API Endpoints

### Walk-Forward Optimization

```bash
POST /optimize/walk-forward
```

**Request:**
```json
{
  "strategy": "ma_cross",
  "symbol": "BTCUSDT",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "param_space": {
    "fast_period": {
      "type": "int",
      "low": 5,
      "high": 20,
      "step": 5
    },
    "slow_period": {
      "type": "int",
      "low": 20,
      "high": 50,
      "step": 10
    }
  },
  "n_splits": 5,
  "is_ratio": 0.7,
  "n_trials": 50,
  "optimization_metric": "sharpe_ratio"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Walk-forward optimization completed",
  "results": {
    "n_windows": 5,
    "avg_is_metric": 1.85,
    "avg_oos_metric": 1.42,
    "overfit_ratio": 0.23,
    "robust_params": {
      "fast_period": 10,
      "slow_period": 30
    },
    "duration_seconds": 245.3
  }
}
```

### Multi-Objective Optimization

```bash
POST /optimize/multi-objective
```

**Request:**
```json
{
  "strategy": "ma_cross",
  "symbol": "BTCUSDT",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "param_space": {
    "fast_period": {"type": "int", "low": 5, "high": 20},
    "slow_period": {"type": "int", "low": 20, "high": 50}
  },
  "objectives": ["sharpe_ratio", "max_drawdown"],
  "directions": ["maximize", "minimize"],
  "n_trials": 100
}
```

**Response:**
```json
{
  "success": true,
  "message": "Multi-objective optimization completed, found 12 Pareto solutions",
  "results": {
    "n_solutions": 12,
    "pareto_solutions": [
      {
        "params": {"fast_period": 10, "slow_period": 30},
        "objectives": {"sharpe_ratio": 1.85, "max_drawdown": 12.5}
      },
      {
        "params": {"fast_period": 15, "slow_period": 40},
        "objectives": {"sharpe_ratio": 1.72, "max_drawdown": 10.2}
      }
    ]
  }
}
```

## 🧪 Python Usage

### Walk-Forward Example

```python
from optimizer import WalkForwardOptimizer, OptimizationConfig
from data_loader import PostgreSQLDataLoader
import pandas as pd

# Load data
loader = PostgreSQLDataLoader()
df = loader.load_ohlcv('BTCUSDT', '2023-01-01', '2023-12-31', '1h')

# Define backtest function
def backtest_func(params, data):
    # Run your backtest
    # Return metrics dict
    return {'sharpe_ratio': 1.5, 'return_pct': 25.0}

# Define parameter space
param_space = {
    'fast_period': {'type': 'int', 'low': 5, 'high': 20, 'step': 5},
    'slow_period': {'type': 'int', 'low': 20, 'high': 50, 'step': 10},
    'stop_loss': {'type': 'float', 'low': 0.01, 'high': 0.05}
}

# Setup optimizer
config = OptimizationConfig(
    n_trials=100,
    n_jobs=4,
    metric='sharpe_ratio',
    direction='maximize'
)

optimizer = WalkForwardOptimizer(backtest_func, param_space, config)

# Run
results = optimizer.run_walk_forward(df, n_splits=5, is_ratio=0.7)

print(f"Robust params: {results['robust_params']}")
print(f"Avg OOS Sharpe: {results['avg_oos_metric']:.2f}")
print(f"Overfit ratio: {results['overfit_ratio']:.2%}")
```

### Multi-Objective Example

```python
from optimizer import MultiObjectiveOptimizer

optimizer = MultiObjectiveOptimizer(
    backtest_func=backtest_func,
    param_space=param_space,
    objectives=['sharpe_ratio', 'max_drawdown'],
    directions=['maximize', 'minimize'],
    n_trials=100
)

results = optimizer.optimize(df)

print(f"Found {results['n_solutions']} Pareto optimal solutions")
for trial in results['pareto_trials'][:5]:
    print(f"Params: {trial.params}, Sharpe: {trial.values[0]:.2f}, DD: {trial.values[1]:.2f}%")
```

## 📈 Parameter Space Definition

### Integer Parameters

```python
{
    "param_name": {
        "type": "int",
        "low": 5,
        "high": 50,
        "step": 5  # Optional
    }
}
```

### Float Parameters

```python
{
    "param_name": {
        "type": "float",
        "low": 0.01,
        "high": 0.1,
        "log": False  # Use log scale? (for wide ranges)
    }
}
```

### Categorical Parameters

```python
{
    "param_name": {
        "type": "categorical",
        "choices": ["sma", "ema", "wma"]
    }
}
```

## 🎯 Best Practices

### Walk-Forward Settings

- **n_splits**: 5-10 windows (more = more robust, but slower)
- **is_ratio**: 0.6-0.8 (70% IS, 30% OOS is common)
- **n_trials**: 50-200 per window (depends on param space size)

### Overfit Detection

- **Overfit ratio < 20%**: Good generalization
- **Overfit ratio 20-40%**: Moderate overfitting
- **Overfit ratio > 40%**: High overfitting risk

### Parameter Space Tips

1. **Start wide**: Use broad ranges initially
2. **Refine**: Narrow down based on results
3. **Log scale**: Use for exponential parameters (e.g., learning rates)
4. **Step size**: Larger steps = faster, but less precise

## 🔬 Advanced Features

### Pruning (Early Stopping)

```python
import optuna

# Use MedianPruner to stop unpromising trials
pruner = optuna.pruners.MedianPruner(n_warmup_steps=10)

study = optuna.create_study(pruner=pruner)
```

### Custom Samplers

```python
# Use TPE sampler for better performance
sampler = optuna.samplers.TPESampler(seed=42)

study = optuna.create_study(sampler=sampler)
```

### Visualization

```python
import optuna.visualization as vis

# Plot optimization history
fig = vis.plot_optimization_history(study)
fig.show()

# Plot parameter importances
fig = vis.plot_param_importances(study)
fig.show()

# Plot parallel coordinate
fig = vis.plot_parallel_coordinate(study)
fig.show()
```

## 📊 MLflow Integration

All optimizations are logged to MLflow:

- **Parameters**: All tested parameter combinations
- **Metrics**: All performance metrics
- **Tags**: Window number, phase (IS/OOS)
- **Artifacts**: Plots and reports

Access MLflow UI:
```bash
mlflow ui --backend-store-uri postgresql://...
# Open http://localhost:5000
```

## 🌐 Environment Variables

```bash
DATABASE_URL=postgresql://user:pass@host:5432/db
MLFLOW_TRACKING_URI=http://mlflow:5000
PORT=8003
```

## 🧪 Testing

```bash
# Test walk-forward locally
curl -X POST http://localhost:8003/optimize/walk-forward \
  -H "Content-Type: application/json" \
  -d @walk_forward_request.json

# Test multi-objective
curl -X POST http://localhost:8003/optimize/multi-objective \
  -H "Content-Type: application/json" \
  -d @multi_obj_request.json
```

## 📦 Dependencies

- **optuna**: Hyperparameter optimization framework
- **mlflow**: Experiment tracking
- **backtrader**: Backtesting (via backtest-engine)
- **fastapi**: REST API
- **pandas, numpy**: Data manipulation

## 🔗 Integration

This service integrates with:
- **Backtest Engine**: Uses backtest strategies
- **MLflow**: Logs all optimization runs
- **PostgreSQL**: Historical data loading

## 📝 Next Steps

- [ ] Add Bayesian optimization
- [ ] Implement early stopping
- [ ] Add custom visualizations
- [ ] Support for portfolio optimization
- [ ] Distributed optimization (Ray)

---

**Status**: ✅ Ready for Production

