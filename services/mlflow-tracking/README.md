# 🎯 MLflow Tracking Server

Centralny system do trackingu eksperymentów ML, model registry i artifact storage.

## 🚀 Features

- **Experiment Tracking**: Log parameters, metrics, artifacts
- **Model Registry**: Versioning, staging, production deployment
- **Artifact Storage**: Models, plots, datasets
- **REST API**: Programmatic access
- **UI Dashboard**: Visual experiment comparison

## 🔧 Configuration

### Environment Variables

```bash
# Database (PostgreSQL)
DATABASE_URL=postgresql://user:pass@host:5432/mlflow

# Artifact Storage (S3 compatible or local)
ARTIFACT_ROOT=s3://bucket/mlflow-artifacts  # or ./artifacts for local

# Optional
MLFLOW_TRACKING_USERNAME=admin
MLFLOW_TRACKING_PASSWORD=secret
```

### Railway Deployment

```bash
# Set environment variables in Railway dashboard
DATABASE_URL=postgresql://...  # from Railway PostgreSQL plugin
ARTIFACT_ROOT=./mlflow-artifacts  # local for now, S3 later

# Deploy
railway up
```

## 📊 Usage

### Python Client

```python
import mlflow

# Set tracking URI
mlflow.set_tracking_uri("https://mlflow.railway.app")

# Start experiment
with mlflow.start_run():
    # Log parameters
    mlflow.log_param("learning_rate", 0.001)
    mlflow.log_param("epochs", 100)
    
    # Train model
    model = train_model()
    
    # Log metrics
    mlflow.log_metric("accuracy", 0.95)
    mlflow.log_metric("loss", 0.05)
    
    # Log model
    mlflow.sklearn.log_model(model, "model")
    
    # Log artifacts
    mlflow.log_artifact("confusion_matrix.png")
```

### REST API

```bash
# List experiments
curl https://mlflow.railway.app/api/2.0/mlflow/experiments/list

# Get run
curl https://mlflow.railway.app/api/2.0/mlflow/runs/get?run_id=<run_id>

# Search runs
curl -X POST https://mlflow.railway.app/api/2.0/mlflow/runs/search \
  -H "Content-Type: application/json" \
  -d '{"experiment_ids":["0"]}'
```

## 🎨 UI Dashboard

Access at: `https://mlflow.railway.app`

Features:
- Compare multiple runs side-by-side
- Visualize metrics over time
- Download artifacts
- Register models
- Transition model stages

## 🔗 Integration

### Optuna + MLflow

```python
import optuna
from optuna.integration.mlflow import MLflowCallback

mlflc = MLflowCallback(
    tracking_uri="https://mlflow.railway.app",
    metric_name="validation_accuracy"
)

study = optuna.create_study()
study.optimize(objective, n_trials=100, callbacks=[mlflc])
```

### Backtrader + MLflow

```python
import mlflow

class MLflowStrategy(bt.Strategy):
    def __init__(self):
        with mlflow.start_run():
            mlflow.log_param("strategy", self.__class__.__name__)
    
    def stop(self):
        with mlflow.start_run(run_id=self.run_id):
            mlflow.log_metric("total_return", self.broker.getvalue())
            mlflow.log_metric("sharpe_ratio", self.analyzers.sharpe.get_analysis())
```

## 📦 Model Registry

```python
# Register model
mlflow.register_model(
    model_uri="runs:/<run_id>/model",
    name="btc_predictor"
)

# Transition to staging
client = mlflow.tracking.MlflowClient()
client.transition_model_version_stage(
    name="btc_predictor",
    version=1,
    stage="Staging"
)

# Load model for inference
model = mlflow.pyfunc.load_model("models:/btc_predictor/Production")
predictions = model.predict(data)
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         MLflow Tracking Server          │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │         FastAPI REST API          │ │
│  └───────────────────────────────────┘ │
│                 │                       │
│        ┌────────┴────────┐             │
│        │                 │             │
│  ┌─────▼──────┐   ┌─────▼──────┐     │
│  │ PostgreSQL │   │  Artifacts  │     │
│  │  (Metadata)│   │  (S3/Local) │     │
│  └────────────┘   └─────────────┘     │
└─────────────────────────────────────────┘
         │                    │
         │                    │
    ┌────▼────────────────────▼────┐
    │    ML Services/Clients       │
    │  • Optuna                    │
    │  • Backtrader                │
    │  • Ray/RLlib                 │
    │  • Custom scripts            │
    └──────────────────────────────┘
```

## 🔒 Security

### Authentication (Optional)

```bash
# Set basic auth
export MLFLOW_TRACKING_USERNAME=admin
export MLFLOW_TRACKING_PASSWORD=secret

# Client usage
mlflow.set_tracking_uri("https://admin:secret@mlflow.railway.app")
```

## 📈 Monitoring

### Health Check

```bash
curl https://mlflow.railway.app/health
```

### Prometheus Metrics

```bash
curl https://mlflow.railway.app/metrics
```

## 🧪 Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set env vars
export DATABASE_URL=sqlite:///mlflow.db
export ARTIFACT_ROOT=./mlruns

# Run server
mlflow server \
  --host 0.0.0.0 \
  --port 5000 \
  --backend-store-uri ${DATABASE_URL} \
  --default-artifact-root ${ARTIFACT_ROOT}

# Access UI
open http://localhost:5000
```

## 🔍 Troubleshooting

### Database Connection

```python
# Test connection
from sqlalchemy import create_engine
engine = create_engine(DATABASE_URL)
engine.connect()
```

### Artifact Storage

```bash
# Test S3 access
aws s3 ls s3://bucket/mlflow-artifacts/
```

## 📚 Resources

- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [MLflow REST API](https://mlflow.org/docs/latest/rest-api.html)
- [Model Registry](https://mlflow.org/docs/latest/model-registry.html)

