"""
FastAPI for Market Memory
REST API for market state storage and similarity search
"""
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
import structlog

from embeddings import MarketStateEncoder
from qdrant_storage import MarketMemoryStorage, RiskAnalyzer
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
search_counter = Counter('memory_searches_total', 'Total similarity searches')
store_counter = Counter('memory_stores_total', 'Total market states stored')

# FastAPI app
app = FastAPI(
    title="Market Memory API",
    description="Vector similarity search for market patterns",
    version="1.0.0"
)

# Initialize components
encoder = MarketStateEncoder()
storage = MarketMemoryStorage(
    qdrant_url=os.getenv('QDRANT_URL', 'http://localhost:6333')
)
risk_analyzer = RiskAnalyzer(storage)


# Request/Response Models
class OHLCVData(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class StoreMarketStateRequest(BaseModel):
    ohlcv: OHLCVData
    ohlcv_window: Optional[List[OHLCVData]] = None
    symbol: str = "BTCUSDT"
    indicators: Optional[Dict[str, float]] = None
    outcome: Optional[str] = None  # 'profitable', 'unprofitable', 'neutral'
    strategy: Optional[str] = None
    return_value: Optional[float] = None
    max_drawdown: Optional[float] = None
    regime: Optional[str] = None


class SearchSimilarRequest(BaseModel):
    ohlcv: OHLCVData
    ohlcv_window: Optional[List[OHLCVData]] = None
    symbol: str = "BTCUSDT"
    indicators: Optional[Dict[str, float]] = None
    limit: int = 10
    outcome_filter: Optional[str] = None


class RiskAnalysisRequest(BaseModel):
    ohlcv: OHLCVData
    ohlcv_window: Optional[List[OHLCVData]] = None
    symbol: str = "BTCUSDT"
    indicators: Optional[Dict[str, float]] = None
    lookback: int = 50


# Endpoints
@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "Market Memory",
        "status": "running",
        "features": [
            "Vector embeddings",
            "Similarity search",
            "Risk analysis",
            "Pattern matching"
        ]
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    collection_info = storage.get_collection_info()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "qdrant_url": os.getenv('QDRANT_URL'),
        "collection": collection_info
    }


@app.post("/store")
async def store_market_state(request: StoreMarketStateRequest):
    """
    Store a market state with its embedding
    
    Example:
    ```json
    {
      "ohlcv": {
        "timestamp": "2024-01-01T00:00:00Z",
        "open": 43000, "high": 43500, "low": 42800, "close": 43200, "volume": 1234
      },
      "symbol": "BTCUSDT",
      "outcome": "profitable",
      "return_value": 2.5
    }
    ```
    """
    try:
        store_counter.inc()
        
        # Convert to pandas Series
        import pandas as pd
        ohlcv_series = pd.Series(request.ohlcv.dict())
        
        # Create embedding
        if request.ohlcv_window:
            window_df = pd.DataFrame([o.dict() for o in request.ohlcv_window])
            embedding = encoder.encode_hybrid(ohlcv_series, window_df, request.indicators)
        else:
            embedding = encoder.encode_hybrid(ohlcv_series, indicators=request.indicators)
        
        # Prepare metadata
        metadata = {
            'timestamp': request.ohlcv.timestamp,
            'symbol': request.symbol,
            'open': request.ohlcv.open,
            'high': request.ohlcv.high,
            'low': request.ohlcv.low,
            'close': request.ohlcv.close,
            'volume': request.ohlcv.volume,
            'outcome': request.outcome,
            'strategy': request.strategy,
            'return': request.return_value,
            'max_drawdown': request.max_drawdown,
            'regime': request.regime
        }
        
        # Store
        point_id = storage.store_market_state(embedding, metadata)
        
        logger.info("Stored market state", point_id=point_id, symbol=request.symbol)
        
        return {
            "success": True,
            "point_id": point_id,
            "embedding_size": len(embedding)
        }
    
    except Exception as e:
        logger.error("Error storing market state", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/similar")
async def search_similar(request: SearchSimilarRequest):
    """
    Search for similar market states
    
    Returns top-K most similar historical patterns
    """
    try:
        search_counter.inc()
        
        # Create query embedding
        import pandas as pd
        ohlcv_series = pd.Series(request.ohlcv.dict())
        
        if request.ohlcv_window:
            window_df = pd.DataFrame([o.dict() for o in request.ohlcv_window])
            query_embedding = encoder.encode_hybrid(ohlcv_series, window_df, request.indicators)
        else:
            query_embedding = encoder.encode_hybrid(ohlcv_series, indicators=request.indicators)
        
        # Search
        if request.outcome_filter:
            similar_states = storage.search_by_outcome(
                query_embedding,
                request.outcome_filter,
                request.limit
            )
        else:
            similar_states = storage.search_similar(query_embedding, request.limit)
        
        logger.info(f"Found {len(similar_states)} similar states")
        
        return {
            "success": True,
            "count": len(similar_states),
            "similar_states": similar_states
        }
    
    except Exception as e:
        logger.error("Error searching similar states", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/risk")
async def analyze_risk(request: RiskAnalysisRequest):
    """
    Analyze risk of current market state
    
    Returns risk metrics based on historical similar patterns
    """
    try:
        # Create embedding
        import pandas as pd
        ohlcv_series = pd.Series(request.ohlcv.dict())
        
        if request.ohlcv_window:
            window_df = pd.DataFrame([o.dict() for o in request.ohlcv_window])
            embedding = encoder.encode_hybrid(ohlcv_series, window_df, request.indicators)
        else:
            embedding = encoder.encode_hybrid(ohlcv_series, indicators=request.indicators)
        
        # Analyze risk
        risk_analysis = risk_analyzer.analyze_current_risk(embedding, request.lookback)
        
        logger.info("Risk analysis complete", risk_level=risk_analysis['risk_level'])
        
        return {
            "success": True,
            "risk_analysis": risk_analysis
        }
    
    except Exception as e:
        logger.error("Error analyzing risk", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/collection/info")
async def get_collection_info():
    """Get collection statistics"""
    info = storage.get_collection_info()
    return {"collection_info": info}


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(generate_latest())


if __name__ == "__main__":
    # Create collection on startup
    try:
        storage.create_collection(vector_size=393)  # Hybrid embedding size
    except:
        pass
    
    port = int(os.getenv("PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)

