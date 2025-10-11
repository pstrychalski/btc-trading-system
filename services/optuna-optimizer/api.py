"""
FastAPI for Optuna Optimizer
REST API for walk-forward and multi-objective optimization
"""
import os
import sys
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import structlog
import pandas as pd

# Import local modules with error handling
try:
    from optimizer import WalkForwardOptimizer, MultiObjectiveOptimizer, OptimizationConfig
except ImportError as e:
    logger.warning(f"Could not import optimizer modules: {e}")
    # Create dummy classes for basic functionality
    class WalkForwardOptimizer:
        def __init__(self):
            pass
    
    class MultiObjectiveOptimizer:
        def __init__(self):
            pass
    
    class OptimizationConfig:
        def __init__(self):
            pass

from prometheus_client import Counter, Gauge, generate_latest

# Setup logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

# Prometheus metrics
optimization_counter = Counter('optimizations_total', 'Total optimizations run')
optimization_duration = Gauge('optimization_duration_seconds', 'Optimization duration')

# FastAPI app
app = FastAPI(
    title="Optuna Optimizer API",
    description="Walk-forward and multi-objective optimization with MLflow",
    version="1.0.0"
)

# Global state
optimization_jobs = {}


# Request/Response Models
class WalkForwardRequest(BaseModel):
    strategy: str = Field(..., description="Strategy name", example="ma_cross")
    symbol: str = Field(default="BTCUSDT", description="Trading pair")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    interval: str = Field(default="1h", description="Timeframe")
    param_space: Dict[str, Dict[str, Any]] = Field(..., description="Parameter search space")
    n_splits: int = Field(default=5, description="Number of walk-forward windows")
    is_ratio: float = Field(default=0.7, description="In-sample ratio (0.7 = 70% IS, 30% OOS)")
    n_trials: int = Field(default=100, description="Number of Optuna trials per window")
    n_jobs: int = Field(default=4, description="Parallel jobs")
    optimization_metric: str = Field(default="sharpe_ratio", description="Metric to optimize")
    initial_cash: float = Field(default=100000.0)


class MultiObjectiveRequest(BaseModel):
    strategy: str
    symbol: str = "BTCUSDT"
    start_date: str
    end_date: str
    interval: str = "1h"
    param_space: Dict[str, Dict[str, Any]]
    objectives: List[str] = Field(..., description="List of metrics to optimize", example=["sharpe_ratio", "max_drawdown"])
    directions: List[str] = Field(..., description="maximize or minimize for each objective", example=["maximize", "minimize"])
    n_trials: int = 100
    initial_cash: float = 100000.0


class OptimizationResponse(BaseModel):
    success: bool
    message: str
    job_id: Optional[str] = None
    results: Optional[Dict[str, Any]] = None


# Endpoints
@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "Optuna Optimizer",
        "status": "running",
        "features": [
            "Walk-forward optimization",
            "Multi-objective optimization",
            "MLflow integration",
            "Parallel execution"
        ]
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "active_jobs": len(optimization_jobs),
        "mlflow_uri": os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000')
    }


@app.post("/optimize/walk-forward", response_model=OptimizationResponse)
async def walk_forward_optimization(request: WalkForwardRequest):
    """
    Run walk-forward optimization
    
    Example:
    ```json
    {
      "strategy": "ma_cross",
      "symbol": "BTCUSDT",
      "start_date": "2023-01-01",
      "end_date": "2023-12-31",
      "param_space": {
        "fast_period": {"type": "int", "low": 5, "high": 20, "step": 5},
        "slow_period": {"type": "int", "low": 20, "high": 50, "step": 10}
      },
      "n_splits": 5,
      "is_ratio": 0.7,
      "n_trials": 50,
      "optimization_metric": "sharpe_ratio"
    }
    ```
    """
    try:
        optimization_counter.inc()
        logger.info("Walk-forward optimization request", strategy=request.strategy)
        
        # Load data
        loader = PostgreSQLDataLoader()
        df = loader.load_ohlcv(
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            interval=request.interval
        )
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data found")
        
        logger.info(f"Loaded {len(df)} candles")
        
        # Create backtest function
        def backtest_func(params: Dict[str, Any], data: pd.DataFrame) -> Dict[str, Any]:
            """Run backtest with given parameters"""
            data_feed = create_backtrader_feed(data)
            engine = BacktestEngine(initial_cash=request.initial_cash)
            results = engine.run_backtest(
                strategy_name=request.strategy,
                data_feed=data_feed,
                strategy_params=params,
                log_to_mlflow=False  # We'll log from optimizer
            )
            return results['metrics']
        
        # Setup optimizer
        config = OptimizationConfig(
            n_trials=request.n_trials,
            n_jobs=request.n_jobs,
            direction="maximize",  # Always maximize for now
            metric=request.optimization_metric,
            study_name=f"{request.strategy}_{request.symbol}"
        )
        
        optimizer = WalkForwardOptimizer(
            backtest_func=backtest_func,
            param_space=request.param_space,
            config=config
        )
        
        # Run optimization
        start_time = datetime.now()
        
        results = optimizer.run_walk_forward(
            data=df,
            n_splits=request.n_splits,
            is_ratio=request.is_ratio
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        optimization_duration.set(duration)
        
        logger.info("Walk-forward optimization complete",
                   duration_sec=duration,
                   avg_oos_metric=results['avg_oos_metric'])
        
        return OptimizationResponse(
            success=True,
            message="Walk-forward optimization completed",
            results={
                'n_windows': results['n_windows'],
                'avg_is_metric': results['avg_is_metric'],
                'avg_oos_metric': results['avg_oos_metric'],
                'overfit_ratio': results['overfit_ratio'],
                'robust_params': results['robust_params'],
                'duration_seconds': duration
            }
        )
    
    except Exception as e:
        logger.error("Walk-forward optimization failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/optimize/multi-objective", response_model=OptimizationResponse)
async def multi_objective_optimization(request: MultiObjectiveRequest):
    """
    Run multi-objective optimization
    
    Example:
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
    """
    try:
        optimization_counter.inc()
        logger.info("Multi-objective optimization request", strategy=request.strategy)
        
        # Load data
        loader = PostgreSQLDataLoader()
        df = loader.load_ohlcv(
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            interval=request.interval
        )
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data found")
        
        # Create backtest function
        def backtest_func(params: Dict[str, Any], data: pd.DataFrame) -> Dict[str, Any]:
            data_feed = create_backtrader_feed(data)
            engine = BacktestEngine(initial_cash=request.initial_cash)
            results = engine.run_backtest(
                strategy_name=request.strategy,
                data_feed=data_feed,
                strategy_params=params,
                log_to_mlflow=False
            )
            return results['metrics']
        
        # Setup optimizer
        optimizer = MultiObjectiveOptimizer(
            backtest_func=backtest_func,
            param_space=request.param_space,
            objectives=request.objectives,
            directions=request.directions,
            n_trials=request.n_trials
        )
        
        # Run optimization
        start_time = datetime.now()
        results = optimizer.optimize(df)
        duration = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Multi-objective optimization complete, found {results['n_solutions']} Pareto solutions")
        
        # Extract Pareto solutions
        pareto_solutions = []
        for trial in results['pareto_trials']:
            solution = {
                'params': trial.params,
                'objectives': {obj: val for obj, val in zip(request.objectives, trial.values)}
            }
            pareto_solutions.append(solution)
        
        return OptimizationResponse(
            success=True,
            message=f"Multi-objective optimization completed, found {results['n_solutions']} Pareto solutions",
            results={
                'n_solutions': results['n_solutions'],
                'pareto_solutions': pareto_solutions[:10],  # Return top 10
                'duration_seconds': duration
            }
        )
    
    except Exception as e:
        logger.error("Multi-objective optimization failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(generate_latest())


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)

