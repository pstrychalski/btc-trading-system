"""
Pathway Real-Time Pipeline
Stream processing for market data
"""
import pathway as pw
import pandas as pd
import numpy as np
from typing import Dict, Any
import structlog

logger = structlog.get_logger()


class MarketDataPipeline:
    """Real-time market data processing with Pathway"""
    
    def __init__(self, redis_url: str, qdrant_url: str):
        self.redis_url = redis_url
        self.qdrant_url = qdrant_url
        logger.info("MarketDataPipeline initialized")
    
    def create_pipeline(self):
        """Create Pathway streaming pipeline"""
        
        # Input: Redis stream
        market_data = pw.io.redis.read(
            rdcon=self.redis_url,
            channel="market_data",
            format="json",
            schema=MarketDataSchema
        )
        
        # Transform: Calculate indicators
        enriched_data = market_data.select(
            *pw.this,
            sma_10=pw.this.rolling(window=pw.Duration.minutes(10)).reduce(
                pw.reducers.avg(pw.this.close)
            ),
            volatility=pw.this.rolling(window=pw.Duration.minutes(30)).reduce(
                pw.reducers.std(pw.this.close)
            )
        )
        
        # Output: Store to Qdrant
        pw.io.qdrant.write(
            enriched_data,
            qdrant_url=self.qdrant_url,
            collection_name="market_states"
        )
        
        return enriched_data


class MarketDataSchema(pw.Schema):
    """Schema for market data"""
    timestamp: str
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float

