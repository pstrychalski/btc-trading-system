"""
WebSocket Data Collector for BTC Trading System
Collects real-time market data from Binance and validates with Great Expectations
"""
import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
import structlog
from binance import AsyncClient, BinanceSocketManager
import redis.asyncio as redis
import httpx

logger = structlog.get_logger()


class BinanceDataCollector:
    """Collects real-time market data from Binance WebSocket API"""
    
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
        
        self.client: Optional[AsyncClient] = None
        self.bm: Optional[BinanceSocketManager] = None
        self.redis_client: Optional[redis.Redis] = None
        self.http_client = httpx.AsyncClient(timeout=10.0)
        
        self.running = False
        self.reconnect_delay = 5
        self.max_reconnect_delay = 60
        
        # Metrics
        self.messages_received = 0
        self.messages_validated = 0
        self.validation_errors = 0
        self.last_message_time = 0
        
    async def connect(self):
        """Initialize connections to Binance and Redis"""
        logger.info("Initializing connections...")
        
        try:
            # Connect to Binance
            self.client = await AsyncClient.create()
            self.bm = BinanceSocketManager(self.client)
            logger.info("Connected to Binance API")
            
            # Connect to Redis
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Connected to Redis")
            
            return True
            
        except Exception as e:
            logger.error("connection_error", error=str(e))
            return False
    
    async def disconnect(self):
        """Close all connections"""
        logger.info("Closing connections...")
        
        if self.bm:
            await self.bm.close()
        
        if self.client:
            await self.client.close_connection()
        
        if self.redis_client:
            await self.redis_client.close()
        
        await self.http_client.aclose()
        
        logger.info("All connections closed")
    
    async def validate_data(self, data: Dict) -> bool:
        """
        Validate data using the Data Validation Service
        
        Args:
            data: Market data to validate
            
        Returns:
            True if validation passed, False otherwise
        """
        try:
            response = await self.http_client.post(
                f"{self.validation_service_url}/validate/realtime",
                json=data,
                timeout=5.0
            )
            
            if response.status_code == 200:
                result = response.json()
                validation_passed = result.get("success", False)
                
                if validation_passed:
                    self.messages_validated += 1
                    logger.debug(
                        "validation_success",
                        symbol=data.get("symbol"),
                        price=data.get("price")
                    )
                else:
                    self.validation_errors += 1
                    logger.warning(
                        "validation_failed",
                        symbol=data.get("symbol"),
                        errors=result.get("errors", [])
                    )
                
                return validation_passed
            else:
                logger.error(
                    "validation_service_error",
                    status_code=response.status_code
                )
                return False
                
        except Exception as e:
            logger.error("validation_error", error=str(e))
            return False
    
    async def store_in_redis(self, key: str, data: Dict, ttl: int = 3600):
        """
        Store data in Redis with TTL
        
        Args:
            key: Redis key
            data: Data to store
            ttl: Time-to-live in seconds
        """
        try:
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(data)
            )
            
            # Also push to stream for real-time consumers
            await self.redis_client.xadd(
                f"stream:{data['symbol']}",
                {"data": json.dumps(data)},
                maxlen=1000  # Keep last 1000 messages
            )
            
            logger.debug(
                "data_stored",
                key=key,
                symbol=data.get("symbol")
            )
            
        except Exception as e:
            logger.error("redis_store_error", error=str(e), key=key)
    
    async def process_kline_message(self, msg: Dict):
        """
        Process kline/candlestick WebSocket message
        
        Args:
            msg: WebSocket message from Binance
        """
        try:
            if msg.get("e") != "kline":
                return
            
            kline = msg["k"]
            
            # Extract OHLCV data
            data = {
                "symbol": msg["s"],
                "timestamp": datetime.fromtimestamp(
                    kline["t"] / 1000,
                    tz=timezone.utc
                ).isoformat(),
                "interval": kline["i"],
                "open": float(kline["o"]),
                "high": float(kline["h"]),
                "low": float(kline["l"]),
                "close": float(kline["c"]),
                "volume": float(kline["v"]),
                "trades": kline["n"],
                "is_closed": kline["x"],
                "quote_volume": float(kline["q"]),
                "taker_buy_base_volume": float(kline["V"]),
                "taker_buy_quote_volume": float(kline["Q"]),
            }
            
            self.messages_received += 1
            self.last_message_time = time.time()
            
            # Only process closed candles
            if not data["is_closed"]:
                return
            
            # Validate data
            if await self.validate_data(data):
                # Store in Redis
                redis_key = f"kline:{data['symbol']}:{data['interval']}:{data['timestamp']}"
                await self.store_in_redis(redis_key, data)
                
                # Update latest price
                latest_key = f"latest:{data['symbol']}"
                await self.redis_client.hset(
                    latest_key,
                    mapping={
                        "price": data["close"],
                        "volume": data["volume"],
                        "timestamp": data["timestamp"],
                        "interval": data["interval"],
                    }
                )
                
                logger.info(
                    "kline_processed",
                    symbol=data["symbol"],
                    interval=data["interval"],
                    close=data["close"],
                    volume=data["volume"]
                )
            
        except Exception as e:
            logger.error("process_kline_error", error=str(e), msg=msg)
    
    async def process_trade_message(self, msg: Dict):
        """
        Process trade WebSocket message
        
        Args:
            msg: WebSocket message from Binance
        """
        try:
            if msg.get("e") != "trade":
                return
            
            data = {
                "symbol": msg["s"],
                "timestamp": datetime.fromtimestamp(
                    msg["T"] / 1000,
                    tz=timezone.utc
                ).isoformat(),
                "trade_id": msg["t"],
                "price": float(msg["p"]),
                "quantity": float(msg["q"]),
                "buyer_order_id": msg["b"],
                "seller_order_id": msg["a"],
                "is_buyer_maker": msg["m"],
            }
            
            self.messages_received += 1
            self.last_message_time = time.time()
            
            # Store in Redis stream for real-time processing
            await self.redis_client.xadd(
                f"trades:{data['symbol']}",
                {"data": json.dumps(data)},
                maxlen=10000  # Keep last 10k trades
            )
            
            logger.debug(
                "trade_processed",
                symbol=data["symbol"],
                price=data["price"],
                quantity=data["quantity"]
            )
            
        except Exception as e:
            logger.error("process_trade_error", error=str(e), msg=msg)
    
    async def subscribe_klines(self):
        """Subscribe to kline/candlestick streams for all symbols and intervals"""
        tasks = []
        
        for symbol in self.symbols:
            for interval in self.intervals:
                socket = self.bm.kline_socket(symbol, interval=interval)
                task = asyncio.create_task(self._handle_socket(socket, "kline"))
                tasks.append(task)
                
                logger.info(
                    "subscribed_klines",
                    symbol=symbol,
                    interval=interval
                )
        
        return tasks
    
    async def subscribe_trades(self):
        """Subscribe to trade streams for all symbols"""
        tasks = []
        
        for symbol in self.symbols:
            socket = self.bm.trade_socket(symbol)
            task = asyncio.create_task(self._handle_socket(socket, "trade"))
            tasks.append(task)
            
            logger.info("subscribed_trades", symbol=symbol)
        
        return tasks
    
    async def _handle_socket(self, socket, msg_type: str):
        """
        Handle WebSocket connection with automatic reconnection
        
        Args:
            socket: BinanceSocketManager socket
            msg_type: Type of message ("kline" or "trade")
        """
        reconnect_delay = self.reconnect_delay
        
        while self.running:
            try:
                async with socket as stream:
                    logger.info(f"WebSocket connected", type=msg_type)
                    reconnect_delay = self.reconnect_delay  # Reset delay on success
                    
                    while self.running:
                        msg = await stream.recv()
                        
                        if msg_type == "kline":
                            await self.process_kline_message(msg)
                        elif msg_type == "trade":
                            await self.process_trade_message(msg)
                            
            except Exception as e:
                if not self.running:
                    break
                    
                logger.error(
                    "websocket_error",
                    type=msg_type,
                    error=str(e),
                    reconnect_in=reconnect_delay
                )
                
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(
                    reconnect_delay * 2,
                    self.max_reconnect_delay
                )
    
    async def start(self):
        """Start the data collector"""
        logger.info("Starting Data Collector...")
        
        if not await self.connect():
            logger.error("Failed to connect, exiting...")
            return
        
        self.running = True
        
        try:
            # Subscribe to all streams
            kline_tasks = await self.subscribe_klines()
            trade_tasks = await self.subscribe_trades()
            
            all_tasks = kline_tasks + trade_tasks
            
            logger.info(
                "data_collector_started",
                symbols=self.symbols,
                intervals=self.intervals,
                total_streams=len(all_tasks)
            )
            
            # Wait for all tasks
            await asyncio.gather(*all_tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error("start_error", error=str(e))
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the data collector"""
        logger.info("Stopping Data Collector...")
        self.running = False
        await self.disconnect()
    
    def get_metrics(self) -> Dict:
        """Get collector metrics"""
        uptime = time.time() - self.last_message_time if self.last_message_time else 0
        
        return {
            "messages_received": self.messages_received,
            "messages_validated": self.messages_validated,
            "validation_errors": self.validation_errors,
            "validation_success_rate": (
                self.messages_validated / self.messages_received * 100
                if self.messages_received > 0
                else 0
            ),
            "last_message_seconds_ago": uptime,
            "is_running": self.running,
            "symbols": self.symbols,
            "intervals": self.intervals,
        }

