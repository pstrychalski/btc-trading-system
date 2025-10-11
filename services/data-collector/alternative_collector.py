"""
Alternative Data Collector for BTC Trading System
Uses CoinGecko API as fallback when Binance is restricted
"""
import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
import structlog
import redis.asyncio as redis
import httpx

logger = structlog.get_logger()


class CoinGeckoDataCollector:
    """Collects market data from CoinGecko API as Binance alternative"""
    
    def __init__(
        self,
        symbols: List[str],
        redis_url: str,
        validation_service_url: str,
        intervals: List[str] = ["1m", "5m", "15m", "1h"],
    ):
        self.symbols = symbols
        self.redis_url = redis_url
        self.validation_service_url = validation_service_url
        self.intervals = intervals
        
        self.redis_client: Optional[redis.Redis] = None
        self.http_client = httpx.AsyncClient(timeout=10.0)
        
        self.running = False
        self.collection_interval = 60  # CoinGecko free tier: 1 request per minute
        
        # Metrics
        self.messages_received = 0
        self.messages_validated = 0
        self.validation_errors = 0
        self.last_message_time = 0
        
    async def connect(self):
        """Initialize connections to Redis"""
        logger.info("Initializing connections...")
        
        try:
            # Connect to Redis
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Redis connection established")
            
            # Test validation service
            response = await self.http_client.get(f"{self.validation_service_url}/health")
            if response.status_code == 200:
                logger.info("Validation service connection established")
            else:
                logger.warning("Validation service not available")
                
        except Exception as e:
            logger.error("Failed to initialize connections", error=str(e))
            raise
    
    async def collect_market_data(self):
        """Collect market data from CoinGecko API"""
        try:
            # Map symbols to CoinGecko IDs
            symbol_map = {
                "BTCUSDT": "bitcoin",
                "ETHUSDT": "ethereum",
                "ADAUSDT": "cardano",
                "DOTUSDT": "polkadot",
                "LINKUSDT": "chainlink"
            }
            
            # Get current prices
            coin_ids = [symbol_map.get(symbol, "bitcoin") for symbol in self.symbols]
            coin_ids_str = ",".join(coin_ids)
            
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": coin_ids_str,
                "vs_currencies": "usd",
                "include_24hr_change": "true",
                "include_24hr_vol": "true"
            }
            
            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Process data for each symbol
            for symbol in self.symbols:
                coin_id = symbol_map.get(symbol, "bitcoin")
                if coin_id in data:
                    price_data = data[coin_id]
                    
                    # Create OHLCV-like data structure
                    current_time = int(time.time() * 1000)
                    ohlcv_data = {
                        "symbol": symbol,
                        "timestamp": current_time,
                        "open": price_data["usd"],
                        "high": price_data["usd"] * 1.01,  # Simulate high
                        "low": price_data["usd"] * 0.99,   # Simulate low
                        "close": price_data["usd"],
                        "volume": price_data.get("usd_24h_vol", 0),
                        "change_24h": price_data.get("usd_24h_change", 0),
                        "source": "coingecko"
                    }
                    
                    await self.process_message(ohlcv_data)
                    
        except Exception as e:
            logger.error("Failed to collect market data", error=str(e))
            raise
    
    async def process_message(self, data: Dict):
        """Process and validate market data message"""
        try:
            self.messages_received += 1
            self.last_message_time = time.time()
            
            # Publish to Redis
            if self.redis_client:
                channel = f"market_data:{data['symbol']}"
                await self.redis_client.publish(channel, json.dumps(data))
            
            # Validate with validation service
            try:
                response = await self.http_client.post(
                    f"{self.validation_service_url}/validate",
                    json=data,
                    timeout=5.0
                )
                if response.status_code == 200:
                    self.messages_validated += 1
                else:
                    self.validation_errors += 1
                    logger.warning("Validation failed", status=response.status_code)
            except Exception as e:
                self.validation_errors += 1
                logger.warning("Validation service error", error=str(e))
                
        except Exception as e:
            logger.error("Failed to process message", error=str(e))
            self.validation_errors += 1
    
    async def start(self):
        """Start data collection loop (compatible with BinanceDataCollector)"""
        logger.info("Starting CoinGecko data collection...")
        self.running = True
        
        while self.running:
            try:
                await self.collect_market_data()
                logger.info("Data collection cycle completed", 
                          messages_received=self.messages_received,
                          messages_validated=self.messages_validated,
                          validation_errors=self.validation_errors)
                
                # Wait before next collection (respect rate limits)
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error("Collection error", error=str(e))
                await asyncio.sleep(10)  # Wait before retry
    
    async def start_collection(self):
        """Alias for start() method"""
        await self.start()
    
    async def stop(self):
        """Stop data collection (compatible with BinanceDataCollector)"""
        logger.info("Stopping data collection...")
        self.running = False
    
    async def stop_collection(self):
        """Alias for stop() method"""
        await self.stop()
    
    def get_metrics(self) -> Dict:
        """Get collector metrics (compatible with BinanceDataCollector)"""
        return {
            "messages_received": self.messages_received,
            "messages_validated": self.messages_validated,
            "validation_errors": self.validation_errors,
            "last_message_time": self.last_message_time,
            "source": "coingecko"
        }
    
    async def get_status(self) -> Dict:
        """Get collector status"""
        return {
            "running": self.running,
            "messages_received": self.messages_received,
            "messages_validated": self.messages_validated,
            "validation_errors": self.validation_errors,
            "last_message_time": self.last_message_time,
            "source": "coingecko"
        }
    
    async def close(self):
        """Close connections"""
        if self.redis_client:
            await self.redis_client.close()
        await self.http_client.aclose()
        logger.info("Connections closed")
