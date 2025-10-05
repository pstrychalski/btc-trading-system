#!/bin/bash
set -e

# Default values
PORT=${PORT:-5000}
DATABASE_URL=${DATABASE_URL:-sqlite:///mlflow.db}
ARTIFACT_ROOT=${ARTIFACT_ROOT:-./mlruns}

echo "🚀 Starting MLflow Tracking Server..."
echo "📊 Backend Store: ${DATABASE_URL}"
echo "📦 Artifact Root: ${ARTIFACT_ROOT}"
echo "🌐 Port: ${PORT}"

# Start MLflow server
exec mlflow server \
  --host 0.0.0.0 \
  --port ${PORT} \
  --backend-store-uri "${DATABASE_URL}" \
  --default-artifact-root "${ARTIFACT_ROOT}" \
  --serve-artifacts

