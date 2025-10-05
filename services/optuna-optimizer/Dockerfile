FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install TA-Lib (needed for backtrader strategies)
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib/ && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Copy requirements
COPY services/optuna-optimizer/requirements.txt .
COPY services/backtest-engine/requirements.txt ./backtest-requirements.txt

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r backtest-requirements.txt

# Copy application code
COPY services/optuna-optimizer/ /app/
COPY services/backtest-engine/ /app/backtest-engine/

# Expose port
EXPOSE 8003

# Start FastAPI server
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8003"]

