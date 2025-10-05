FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create mlruns directory for local artifact storage
RUN mkdir -p /app/mlruns

# Copy entrypoint script
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Expose MLflow port (Railway will use PORT env var)
EXPOSE 5000

# Start MLflow server
ENTRYPOINT ["./entrypoint.sh"]

