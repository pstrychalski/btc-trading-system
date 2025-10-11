"""
FastAPI REST API for Data Validation Service
Exposes validation endpoints for market data
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
import structlog
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import uuid

from validator import get_validator
from database import get_db_manager
import backtrader as bt
import numpy as np

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="Data Validation Service",
    description="Market data quality validation using Great Expectations",
    version="1.0.0"
)

# Initialize validator and database
validator = get_validator()
db_manager = None  # Will be initialized on startup

# Prometheus metrics
validation_requests_total = Counter(
    'validation_requests_total',
    'Total number of validation requests',
    ['endpoint', 'status']
)
validation_failures_total = Counter(
    'validation_failures_total',
    'Total number of validation failures',
    ['data_type']
)
validation_duration_seconds = Histogram(
    'validation_duration_seconds',
    'Time spent validating data',
    ['endpoint']
)


# ==============================================================================
# PYDANTIC MODELS
# ==============================================================================

class OHLCVData(BaseModel):
    """OHLCV candle data"""
    timestamp: str
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float = Field(ge=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2024-01-01T00:00:00Z",
                "open": 43250.0,
                "high": 43500.0,
                "low": 43200.0,
                "close": 43450.0,
                "volume": 1234.5
            }
        }


class ValidationRequest(BaseModel):
    """Validation request with multiple data points"""
    symbol: str
    timeframe: Optional[str] = "5m"
    data: List[OHLCVData]


class ValidationResponse(BaseModel):
    """Validation response"""
    valid: bool
    validated_at: str
    symbol: str
    data_points: int
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    statistics: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    timestamp: str
    version: str


# ==============================================================================
# API ENDPOINTS
# ==============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "service": "Data Validation Service",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "validate_ohlcv": "/validate/ohlcv",
            "validate_realtime": "/validate/realtime",
            "docs": "/docs"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring
    """
    return HealthResponse(
        status="healthy",
        service="data-validation",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )


@app.post("/validate/ohlcv", response_model=ValidationResponse, tags=["Validation"])
async def validate_ohlcv(request: ValidationRequest, background_tasks: BackgroundTasks):
    """
    Validate OHLCV data
    
    This endpoint validates:
    - Data completeness (no missing values)
    - Price ranges (0 < price < 1M)
    - OHLC logic (high >= low, etc.)
    - Volume sanity
    - Timestamp uniqueness
    - Price change anomalies
    
    Returns validation results with details about any issues found.
    """
    start_time = datetime.now()
    
    try:
        validation_requests_total.labels(endpoint='ohlcv', status='received').inc()
        logger.info(
            "Received validation request",
            symbol=request.symbol,
            timeframe=request.timeframe,
            data_points=len(request.data)
        )
        
        # Convert to DataFrame
        data_dict = [item.model_dump() for item in request.data]
        df = pd.DataFrame(data_dict)
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Validate with Great Expectations
        validation_results = validator.validate_ohlcv(df)
        
        # Validate price changes
        price_change_results = validator.validate_price_change(df)
        
        # Compile results
        errors = []
        warnings = []
        
        if not validation_results['valid']:
            if 'ohlc_errors' in validation_results:
                errors.extend(validation_results['ohlc_errors'])
            
            # Add failed expectations
            for result in validation_results.get('results', []):
                if not result['success']:
                    errors.append(f"{result['expectation_type']}: {result.get('result', {})}")
        
        if not price_change_results['valid']:
            warnings.append(
                f"Unusual price changes detected: {price_change_results.get('anomalies_count', 0)} anomalies"
            )
            if 'max_change_percent' in price_change_results:
                warnings.append(
                    f"Max price change: {price_change_results['max_change_percent']:.2f}%"
                )
        
        response = ValidationResponse(
            valid=validation_results['valid'] and price_change_results['valid'],
            validated_at=datetime.now().isoformat(),
            symbol=request.symbol,
            data_points=len(request.data),
            errors=errors if errors else None,
            warnings=warnings if warnings else None,
            statistics={
                'ge_validation': validation_results.get('statistics'),
                'price_change': price_change_results
            }
        )
        
        # Update metrics
        duration = (datetime.now() - start_time).total_seconds()
        validation_duration_seconds.labels(endpoint='ohlcv').observe(duration)
        validation_requests_total.labels(
            endpoint='ohlcv',
            status='success' if response.valid else 'failed'
        ).inc()
        
        if not response.valid:
            validation_failures_total.labels(data_type='ohlcv').inc()
        
        # Store result in database (background)
        if db_manager:
            background_tasks.add_task(
                store_validation_result,
                validation_results={
                    'run_id': str(uuid.uuid4()),
                    'data_asset_name': f'{request.symbol}_ohlcv',
                    'suite_name': 'market_data_suite',
                    'validated_at': response.validated_at,
                    'valid': response.valid,
                    'statistics': response.statistics,
                    'results': {'errors': errors, 'warnings': warnings}
                }
            )
        
        logger.info(
            "Validation completed",
            symbol=request.symbol,
            valid=response.valid,
            errors=len(errors),
            warnings=len(warnings),
            duration_seconds=duration
        )
        
        return response
        
    except Exception as e:
        logger.error("Validation failed", error=str(e), symbol=request.symbol)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/validate/realtime", tags=["Validation"])
async def validate_realtime(data: OHLCVData, background_tasks: BackgroundTasks):
    """
    Fast validation for real-time data (single candle)
    
    Performs quick checks suitable for streaming data:
    - Basic range validation
    - OHLC logic
    - Returns immediately
    - Logs to database in background
    """
    try:
        # Quick validation
        errors = []
        
        # OHLC logic
        if data.high < data.low:
            errors.append("High < Low")
        if data.high < data.open:
            errors.append("High < Open")
        if data.high < data.close:
            errors.append("High < Close")
        if data.low > data.open:
            errors.append("Low > Open")
        if data.low > data.close:
            errors.append("Low > Close")
        
        # Price range (basic)
        if data.close > 1000000 or data.close <= 0:
            errors.append("Price out of reasonable range")
        
        # Volume
        if data.volume < 0:
            errors.append("Volume cannot be negative")
        
        valid = len(errors) == 0
        
        # Log to database in background
        if not valid:
            background_tasks.add_task(
                log_validation_failure,
                data=data.model_dump(),
                errors=errors
            )
        
        return {
            "valid": valid,
            "timestamp": data.timestamp,
            "errors": errors if errors else None,
            "validated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Real-time validation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/validate/drift", tags=["Validation"])
async def detect_drift(
    current_data: ValidationRequest,
    reference_symbol: str,
    reference_days: int = 30
):
    """
    Detect data drift by comparing current data to historical reference
    
    Args:
        current_data: Current data sample
        reference_symbol: Symbol to use for reference data
        reference_days: Number of days of historical data to use as reference
    
    Returns:
        Drift detection results
    """
    try:
        # Convert current data to DataFrame
        current_dict = [item.model_dump() for item in current_data.data]
        current_df = pd.DataFrame(current_dict)
        current_df['timestamp'] = pd.to_datetime(current_df['timestamp'])
        
        # TODO: Fetch reference data from database
        # For now, return placeholder
        logger.warning("Drift detection not fully implemented - returning placeholder")
        
        return {
            "drift_detected": False,
            "message": "Drift detection requires historical data - not yet implemented",
            "current_data_points": len(current_data.data),
            "reference_days": reference_days
        }
        
    except Exception as e:
        logger.error("Drift detection failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", tags=["Statistics"])
async def get_validation_stats(hours: int = 24):
    """
    Get validation statistics
    
    Args:
        hours: Number of hours to look back (default: 24)
    
    Returns counts of validation runs, failures, etc.
    """
    try:
        if db_manager is None:
            return {
                "message": "Database not initialized",
                "error": "Database connection not available"
            }
        
        stats = db_manager.get_validation_stats(hours=hours)
        recent_failures = db_manager.get_recent_failures(limit=5)
        
        return {
            "statistics": stats,
            "recent_failures": recent_failures,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error("Failed to get stats", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """
    Prometheus metrics endpoint
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# ==============================================================================
# BACKGROUND TASKS
# ==============================================================================

async def log_validation_failure(data: Dict[str, Any], errors: List[str]):
    """Log validation failure to database"""
    try:
        logger.warning(
            "Validation failure logged",
            data=data,
            errors=errors
        )
        if db_manager:
            db_manager.store_validation_result({
                'run_id': str(uuid.uuid4()),
                'data_asset_name': 'realtime_validation',
                'suite_name': 'quick_checks',
                'validated_at': datetime.now().isoformat(),
                'valid': False,
                'results': {'data': data, 'errors': errors}
            })
    except Exception as e:
        logger.error("Failed to log validation failure", error=str(e))


async def store_validation_result(validation_results: Dict[str, Any]):
    """Store validation result in database"""
    try:
        if db_manager:
            db_manager.store_validation_result(validation_results)
    except Exception as e:
        logger.error("Failed to store validation result", error=str(e))


# ==============================================================================
# STARTUP / SHUTDOWN
# ==============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    global db_manager
    
    logger.info("Data Validation Service starting up")
    
    # Initialize validator
    get_validator()
    
    # Initialize database
    try:
        db_manager = get_db_manager()
        logger.info("Database connection established")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        logger.warning("Service will continue without database persistence")
    
    logger.info("Data Validation Service ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Data Validation Service shutting down")


# ==============================================================================
# ERROR HANDLERS
# ==============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc)
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )


# Optimized Moving Average Strategy
class MovingAverageStrategy(bt.Strategy):
    params = (
        ('fast_ma', 5),    # Fast MA
        ('slow_ma', 15),   # Slow MA
    )
    
    def __init__(self):
        self.fast_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.fast_ma)
        self.slow_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.slow_ma)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        
        # Add RSI for additional confirmation
        self.rsi = bt.indicators.RSI(self.data.close, period=14)
        
        # Track trades
        self.trade_count = 0
        
    def next(self):
        # Only trade if RSI is not in extreme zones
        if self.rsi[0] > 30 and self.rsi[0] < 70:
            if not self.position:
                if self.crossover > 0:  # Fast MA crosses above Slow MA
                    self.buy()
                    self.trade_count += 1
            else:
                if self.crossover < 0:  # Fast MA crosses below Slow MA
                    self.sell()
                    self.trade_count += 1

# RSI Strategy
class RSIStrategy(bt.Strategy):
    params = (
        ('rsi_period', 14),
        ('rsi_oversold', 30),
        ('rsi_overbought', 70),
    )
    
    def __init__(self):
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        self.trade_count = 0
        
    def next(self):
        if not self.position:
            if self.rsi[0] < self.params.rsi_oversold:  # Oversold - Buy
                self.buy()
                self.trade_count += 1
        else:
            if self.rsi[0] > self.params.rsi_overbought:  # Overbought - Sell
                self.sell()
                self.trade_count += 1

# Bollinger Bands Strategy
class BollingerBandsStrategy(bt.Strategy):
    params = (
        ('bb_period', 20),
        ('bb_std', 2),
    )
    
    def __init__(self):
        self.bb = bt.indicators.BollingerBands(self.data.close, period=self.params.bb_period, devfactor=self.params.bb_std)
        self.trade_count = 0
        
    def next(self):
        if not self.position:
            if self.data.close[0] < self.bb.lines.bot[0]:  # Price below lower band - Buy
                self.buy()
                self.trade_count += 1
        else:
            if self.data.close[0] > self.bb.lines.top[0]:  # Price above upper band - Sell
                self.sell()
                self.trade_count += 1

@app.post("/backtest")
async def run_backtest(
    strategy: str = "MovingAverage",
    start_date: str = "2025-09-11",
    end_date: str = "2025-10-11",
    initial_cash: float = 10000.0
):
    """Run simple backtest"""
    try:
        logger.info("Starting backtest", strategy=strategy, start_date=start_date, end_date=end_date)
        
        # Get data from database
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        query = """
        SELECT timestamp, open, high, low, close, volume 
        FROM market_data 
        WHERE symbol = 'BTCUSDT' 
        AND timestamp BETWEEN %s::timestamp AND %s::timestamp
        ORDER BY timestamp
        """
        
        df = db_manager.execute_query(query, (start_date, end_date))
        logger.info("Query executed", rows=len(df), start_date=start_date, end_date=end_date)
        if df.empty:
            # Debug: check what data exists
            debug_query = "SELECT COUNT(*) as total, MIN(timestamp) as min_date, MAX(timestamp) as max_date FROM market_data WHERE symbol = 'BTCUSDT'"
            debug_df = db_manager.execute_query(debug_query)
            logger.error("No data found", debug_info=debug_df.to_dict('records')[0] if not debug_df.empty else "No debug data")
            raise HTTPException(status_code=404, detail="No data found for the specified period")
        
        # Create Backtrader data feed
        data = bt.feeds.PandasData(
            dataname=df,
            datetime='timestamp',
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume'
        )
        
        # Create Cerebro engine
        cerebro = bt.Cerebro()
        cerebro.adddata(data)
        
        # Select strategy
        if strategy == "MovingAverage":
            cerebro.addstrategy(MovingAverageStrategy)
        elif strategy == "RSI":
            cerebro.addstrategy(RSIStrategy)
        elif strategy == "BollingerBands":
            cerebro.addstrategy(BollingerBandsStrategy)
        else:
            cerebro.addstrategy(MovingAverageStrategy)  # Default
        
        cerebro.broker.setcash(initial_cash)
        cerebro.broker.setcommission(commission=0.001)  # 0.1% commission
        
        # Run backtest
        initial_value = cerebro.broker.getvalue()
        results = cerebro.run()
        final_value = cerebro.broker.getvalue()
        
        # Calculate metrics
        total_return = (final_value - initial_value) / initial_value * 100
        trades = len([x for x in results[0] if hasattr(x, 'trades')])
        
        logger.info("Backtest completed", 
                  initial_value=initial_value, 
                  final_value=final_value, 
                  total_return=total_return)
        
        return {
            "strategy": strategy,
            "start_date": start_date,
            "end_date": end_date,
            "initial_cash": initial_value,
            "final_value": final_value,
            "total_return_percent": round(total_return, 2),
            "trades": trades,
            "data_points": len(df),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Backtest failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")

@app.post("/backtest/compare")
async def compare_strategies(
    start_date: str = "2025-09-11",
    end_date: str = "2025-10-11",
    initial_cash: float = 10000.0
):
    """Compare all available strategies"""
    strategies = ["MovingAverage", "RSI", "BollingerBands"]
    results = []
    
    for strategy in strategies:
        try:
            # Get data from database
            if not db_manager:
                raise HTTPException(status_code=500, detail="Database not initialized")
            
            query = """
            SELECT timestamp, open, high, low, close, volume 
            FROM market_data 
            WHERE symbol = 'BTCUSDT' 
            AND timestamp BETWEEN %s::timestamp AND %s::timestamp
            ORDER BY timestamp
            """
            
            df = db_manager.execute_query(query, (start_date, end_date))
            if df.empty:
                continue
            
            # Create Backtrader data feed
            data = bt.feeds.PandasData(
                dataname=df,
                datetime='timestamp',
                open='open',
                high='high',
                low='low',
                close='close',
                volume='volume'
            )
            
            # Create Cerebro engine
            cerebro = bt.Cerebro()
            cerebro.adddata(data)
            
            # Select strategy
            if strategy == "MovingAverage":
                cerebro.addstrategy(MovingAverageStrategy)
            elif strategy == "RSI":
                cerebro.addstrategy(RSIStrategy)
            elif strategy == "BollingerBands":
                cerebro.addstrategy(BollingerBandsStrategy)
            
            cerebro.broker.setcash(initial_cash)
            cerebro.broker.setcommission(commission=0.001)
            
            # Run backtest
            initial_value = cerebro.broker.getvalue()
            results_backtest = cerebro.run()
            final_value = cerebro.broker.getvalue()
            
            # Calculate metrics
            total_return = (final_value - initial_value) / initial_value * 100
            
            results.append({
                "strategy": strategy,
                "initial_cash": initial_value,
                "final_value": final_value,
                "total_return_percent": round(total_return, 2),
                "data_points": len(df)
            })
            
        except Exception as e:
            logger.error(f"Strategy {strategy} failed", error=str(e))
            results.append({
                "strategy": strategy,
                "error": str(e)
            })
    
    return {
        "comparison": results,
        "best_strategy": max(results, key=lambda x: x.get('total_return_percent', -999)) if results else None,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082)

