"""
FastAPI application for Data Collector service
Provides REST API for controlling and monitoring the collector
"""
import asyncio
import os
from contextlib import asynccontextmanager
from typing import Dict, List

import structlog
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from collector import BinanceDataCollector

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Service settings
    service_name: str = "data-collector"
    environment: str = "development"
    
    # Binance settings
    symbols: str = "BTCUSDT,ETHUSDT"  # Comma-separated
    intervals: str = "1m,5m,15m,1h"   # Comma-separated
    
    # Redis settings
    redis_url: str = "redis://localhost:6379"
    
    # Data Validation Service URL
    validation_service_url: str = "http://localhost:8000"
    
    class Config:
        env_file = ".env"
    
    def get_symbols_list(self) -> List[str]:
        return [s.strip().upper() for s in self.symbols.split(",")]
    
    def get_intervals_list(self) -> List[str]:
        return [i.strip() for i in self.intervals.split(",")]


settings = Settings()

# Prometheus metrics
messages_received = Counter(
    "data_collector_messages_received_total",
    "Total number of messages received from Binance"
)
messages_validated = Counter(
    "data_collector_messages_validated_total",
    "Total number of messages successfully validated"
)
validation_errors = Counter(
    "data_collector_validation_errors_total",
    "Total number of validation errors"
)
collector_running = Gauge(
    "data_collector_running",
    "Whether the collector is currently running (1=running, 0=stopped)"
)

# Global collector instance
collector: BinanceDataCollector = None
collector_task: asyncio.Task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global collector, collector_task
    
    logger.info(
        "starting_application",
        symbols=settings.get_symbols_list(),
        intervals=settings.get_intervals_list()
    )
    
    # Initialize collector
    collector = BinanceDataCollector(
        symbols=settings.get_symbols_list(),
        intervals=settings.get_intervals_list(),
        redis_url=settings.redis_url,
        validation_service_url=settings.validation_service_url,
    )
    
    # Start collector in background
    collector_task = asyncio.create_task(collector.start())
    collector_running.set(1)
    
    logger.info("application_started")
    
    yield
    
    # Cleanup
    logger.info("shutting_down")
    await collector.stop()
    if collector_task:
        collector_task.cancel()
    collector_running.set(0)
    logger.info("application_shutdown_complete")


app = FastAPI(
    title="BTC Trading System - Data Collector",
    description="Real-time market data collector from Binance with validation",
    version="1.0.0",
    lifespan=lifespan
)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    environment: str
    collector_running: bool
    messages_received: int
    messages_validated: int
    validation_errors: int


class MetricsResponse(BaseModel):
    """Collector metrics response"""
    messages_received: int
    messages_validated: int
    validation_errors: int
    validation_success_rate: float
    last_message_seconds_ago: float
    is_running: bool
    symbols: List[str]
    intervals: List[str]


class CollectorControlRequest(BaseModel):
    """Collector control request"""
    action: str  # "start" or "stop"


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "data-collector",
        "status": "running",
        "description": "Real-time market data collector from Binance"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns service health status and basic metrics
    """
    if not collector:
        raise HTTPException(status_code=503, detail="Collector not initialized")
    
    metrics = collector.get_metrics()
    
    return HealthResponse(
        status="healthy" if collector.running else "stopped",
        service=settings.service_name,
        environment=settings.environment,
        collector_running=collector.running,
        messages_received=metrics["messages_received"],
        messages_validated=metrics["messages_validated"],
        validation_errors=metrics["validation_errors"]
    )


@app.get("/metrics/prometheus")
async def prometheus_metrics():
    """
    Prometheus metrics endpoint
    
    Returns metrics in Prometheus format
    """
    # Update Prometheus metrics from collector
    if collector:
        metrics = collector.get_metrics()
        messages_received._value.set(metrics["messages_received"])
        messages_validated._value.set(metrics["messages_validated"])
        validation_errors._value.set(metrics["validation_errors"])
        collector_running.set(1 if metrics["is_running"] else 0)
    
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Get detailed collector metrics
    
    Returns comprehensive metrics about collector performance
    """
    if not collector:
        raise HTTPException(status_code=503, detail="Collector not initialized")
    
    metrics = collector.get_metrics()
    
    return MetricsResponse(**metrics)


@app.get("/status")
async def get_status():
    """
    Get collector status
    
    Returns current status and configuration
    """
    if not collector:
        raise HTTPException(status_code=503, detail="Collector not initialized")
    
    return {
        "running": collector.running,
        "symbols": collector.symbols,
        "intervals": collector.intervals,
        "redis_url": settings.redis_url,
        "validation_service_url": settings.validation_service_url,
        "metrics": collector.get_metrics()
    }


@app.post("/control")
async def control_collector(request: CollectorControlRequest):
    """
    Control collector (start/stop)
    
    Note: This is mainly for development. In production,
    the collector should run continuously.
    """
    if not collector:
        raise HTTPException(status_code=503, detail="Collector not initialized")
    
    global collector_task
    
    if request.action == "stop":
        if collector.running:
            await collector.stop()
            if collector_task:
                collector_task.cancel()
            collector_running.set(0)
            return {"status": "stopped"}
        else:
            return {"status": "already_stopped"}
    
    elif request.action == "start":
        if not collector.running:
            collector_task = asyncio.create_task(collector.start())
            collector_running.set(1)
            return {"status": "started"}
        else:
            return {"status": "already_running"}
    
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action: {request.action}. Use 'start' or 'stop'"
        )


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8001"))
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )

