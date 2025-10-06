"""FastAPI for Pathway Pipeline"""
import os
import uvicorn
from fastapi import FastAPI
import structlog

structlog.configure(processors=[structlog.processors.TimeStamper(fmt="iso"), structlog.processors.JSONRenderer()])
logger = structlog.get_logger()

app = FastAPI(title="Pathway Pipeline", version="1.0.0")

@app.get("/")
async def root():
    return {"service": "Pathway Pipeline", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8006))
    uvicorn.run(app, host="0.0.0.0", port=port)

