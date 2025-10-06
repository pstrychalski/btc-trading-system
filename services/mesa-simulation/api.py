"""
FastAPI for Mesa Simulation
Run agent-based market simulations
"""
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional, List
import pandas as pd
import mlflow
import structlog

from market_model import MarketModel

structlog.configure(
    processors=[structlog.processors.TimeStamper(fmt="iso"), structlog.processors.JSONRenderer()]
)
logger = structlog.get_logger()

app = FastAPI(title="Mesa Market Simulation", version="1.0.0")


class SimulationRequest(BaseModel):
    n_agents: int = 100
    n_steps: int = 500
    initial_price: float = 100.0
    agent_distribution: Optional[Dict[str, float]] = None
    log_to_mlflow: bool = True


@app.get("/")
async def root():
    return {"service": "Mesa Market Simulation", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/simulate")
async def run_simulation(request: SimulationRequest):
    """Run market simulation"""
    try:
        logger.info("Starting simulation", n_agents=request.n_agents, n_steps=request.n_steps)
        
        model = MarketModel(
            n_agents=request.n_agents,
            agent_distribution=request.agent_distribution,
            initial_price=request.initial_price
        )
        
        model_data, agent_data = model.run_simulation(request.n_steps)
        
        # Calculate metrics
        final_price = model.get_current_price()
        price_return = (final_price - request.initial_price) / request.initial_price
        avg_volume = model_data['Volume'].mean()
        
        results = {
            "initial_price": request.initial_price,
            "final_price": final_price,
            "return_pct": price_return * 100,
            "avg_volume": int(avg_volume),
            "n_steps": request.n_steps,
            "price_history": model.price_history[-50:]  # Last 50 prices
        }
        
        if request.log_to_mlflow:
            mlflow.set_experiment("mesa_simulations")
            with mlflow.start_run():
                mlflow.log_params({
                    "n_agents": request.n_agents,
                    "n_steps": request.n_steps,
                    "initial_price": request.initial_price
                })
                mlflow.log_metrics({
                    "final_price": final_price,
                    "return_pct": price_return * 100,
                    "avg_volume": avg_volume
                })
        
        logger.info("Simulation complete", final_price=final_price)
        
        return {"success": True, "results": results}
    
    except Exception as e:
        logger.error("Simulation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8005))
    uvicorn.run(app, host="0.0.0.0", port=port)

