"""
FastAPI for Backtest Engine
REST API for running backtests and optimizations
"""
import os
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import structlog

from engine import BacktestEngine, quick_backtest
from strategies import STRATEGY_REGISTRY
from data_loader import PostgreSQLDataLoader, create_backtrader_feed
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
backtest_counter = Counter('backtests_total', 'Total backtests run')
backtest_duration = Gauge('backtest_duration_seconds', 'Backtest duration')
backtest_return = Gauge('backtest_return_percent', 'Backtest return percentage')

# FastAPI app
app = FastAPI(
    title="Backtest Engine API",
    description="Advanced backtesting with Backtrader + MLflow",
    version="1.0.0"
)

# Global state
backtest_jobs = {}  # Store running jobs


# Request/Response Models
class BacktestRequest(BaseModel):
    strategy: str = Field(..., description="Strategy name", example="ma_cross")
    symbol: str = Field(default="BTCUSDT", description="Trading pair")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)", example="2023-01-01")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)", example="2023-12-31")
    interval: str = Field(default="1h", description="Timeframe", example="1h")
    initial_cash: float = Field(default=100000.0, description="Starting capital")
    strategy_params: Optional[Dict[str, Any]] = Field(default=None, description="Strategy parameters")
    log_to_mlflow: bool = Field(default=True, description="Log results to MLflow")


class OptimizationRequest(BaseModel):
    strategy: str = Field(..., description="Strategy name")
    symbol: str = Field(default="BTCUSDT", description="Trading pair")
    start_date: str = Field(..., description="Start date")
    end_date: str = Field(..., description="End date")
    interval: str = Field(default="1h", description="Timeframe")
    param_ranges: Dict[str, List[int]] = Field(..., description="Parameter ranges: {param: [min, max, step]}")
    optimization_metric: str = Field(default="sharpe_ratio", description="Metric to optimize")
    initial_cash: float = Field(default=100000.0)


class BacktestResponse(BaseModel):
    success: bool
    message: str
    metrics: Optional[Dict[str, Any]] = None
    job_id: Optional[str] = None


# Endpoints
@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "Backtest Engine",
        "status": "running",
        "strategies": list(STRATEGY_REGISTRY.keys()),
        "mlflow_uri": os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000')
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    # Check database connection
    try:
        loader = PostgreSQLDataLoader()
        symbols = loader.get_available_symbols()
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"
        symbols = []
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "available_symbols": symbols[:5],  # First 5
        "strategies": list(STRATEGY_REGISTRY.keys())
    }


@app.get("/strategies")
async def list_strategies():
    """List available strategies"""
    strategies = {}
    for name, strategy_class in STRATEGY_REGISTRY.items():
        params = {}
        for param in strategy_class.params._getpairs():
            params[param[0]] = param[1]
        
        strategies[name] = {
            "name": name,
            "description": strategy_class.__doc__ or "No description",
            "default_params": params
        }
    
    return {"strategies": strategies}


@app.get("/symbols")
async def list_symbols():
    """List available trading symbols"""
    try:
        loader = PostgreSQLDataLoader()
        symbols = loader.get_available_symbols()
        return {"symbols": symbols, "count": len(symbols)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/backtest", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """
    Run a backtest
    
    Example:
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
        "slow_period": 30
      }
    }
    ```
    """
    try:
        backtest_counter.inc()
        logger.info("Backtest request received", strategy=request.strategy, symbol=request.symbol)
        
        # Validate strategy
        if request.strategy not in STRATEGY_REGISTRY:
            raise HTTPException(
                status_code=400,
                detail=f"Strategy '{request.strategy}' not found. Available: {list(STRATEGY_REGISTRY.keys())}"
            )
        
        # Load data
        loader = PostgreSQLDataLoader()
        df = loader.load_ohlcv(
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            interval=request.interval
        )
        
        if df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for {request.symbol} between {request.start_date} and {request.end_date}"
            )
        
        data_feed = create_backtrader_feed(df)
        
        # Run backtest
        engine = BacktestEngine(initial_cash=request.initial_cash)
        
        start_time = datetime.now()
        results = engine.run_backtest(
            strategy_name=request.strategy,
            data_feed=data_feed,
            strategy_params=request.strategy_params,
            log_to_mlflow=request.log_to_mlflow
        )
        duration = (datetime.now() - start_time).total_seconds()
        
        backtest_duration.set(duration)
        backtest_return.set(results['metrics']['return_pct'])
        
        logger.info("Backtest completed", 
                   strategy=request.strategy,
                   return_pct=results['metrics']['return_pct'],
                   duration_sec=duration)
        
        return BacktestResponse(
            success=True,
            message="Backtest completed successfully",
            metrics=results['metrics']
        )
    
    except Exception as e:
        logger.error("Backtest failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/optimize", response_model=BacktestResponse)
async def optimize_strategy(request: OptimizationRequest):
    """
    Optimize strategy parameters
    
    Example:
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
    """
    try:
        logger.info("Optimization request received", strategy=request.strategy)
        
        # Validate strategy
        if request.strategy not in STRATEGY_REGISTRY:
            raise HTTPException(
                status_code=400,
                detail=f"Strategy '{request.strategy}' not found"
            )
        
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
        
        data_feed = create_backtrader_feed(df)
        
        # Convert param ranges
        param_ranges = {}
        for param, values in request.param_ranges.items():
            if len(values) != 3:
                raise HTTPException(
                    status_code=400,
                    detail=f"param_ranges must be [min, max, step] for each parameter"
                )
            param_ranges[param] = tuple(values)
        
        # Run optimization
        engine = BacktestEngine(initial_cash=request.initial_cash)
        results = engine.optimize_strategy(
            strategy_name=request.strategy,
            data_feed=data_feed,
            param_ranges=param_ranges,
            optimization_metric=request.optimization_metric
        )
        
        logger.info("Optimization completed", best_params=results['params'])
        
        return BacktestResponse(
            success=True,
            message="Optimization completed",
            metrics=results
        )
    
    except Exception as e:
        logger.error("Optimization failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(generate_latest())


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)

