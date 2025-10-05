FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY services/market-memory/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY services/market-memory/ /app/

# Expose port
EXPOSE 8004

# Start FastAPI server
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8004"]

