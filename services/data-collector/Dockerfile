FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Railway will set PORT env var)
EXPOSE 8001

# Create entrypoint script
RUN echo '#!/bin/bash\n\
PORT=${PORT:-8001}\n\
exec uvicorn api:app --host 0.0.0.0 --port ${PORT}' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:${PORT:-8001}/health')"

# Start FastAPI with uvicorn
ENTRYPOINT ["/app/entrypoint.sh"]

