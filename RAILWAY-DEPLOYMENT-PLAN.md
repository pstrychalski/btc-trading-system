# 🚀 Railway Deployment Plan - Complete System

## 📋 Deployment Overview

### Infrastructure Services (3)
- ✅ PostgreSQL - Already deployed
- ✅ Redis - Already deployed  
- ⏳ Qdrant - To deploy

### Application Services (10)
1. ⏳ Data Validation (Port 8082)
2. ⏳ MLflow Tracking (Port 5000)
3. ⏳ Data Collector (Port 8001)
4. ⏳ Backtest Engine (Port 8002)
5. ⏳ Optuna Optimizer (Port 8003)
6. ⏳ Market Memory (Port 8004)
7. ⏳ Mesa Simulation (Port 8005)
8. ⏳ Pathway Pipeline (Port 8006)
9. ⏳ RL Agent (Port 8007)
10. ⏳ Freqtrade Integration (Port 8008 + 8080)

### Monitoring Services (2)
- ⏳ Prometheus (Port 9090)
- ⏳ Grafana (Port 3000)

**Total Services to Deploy: 13**

---

## 🔧 Railway Configuration per Service

### 1. Data Validation Service

**Root Directory:** `services/data-validation`

**Start Command:**
```bash
uvicorn api:app --host 0.0.0.0 --port $PORT
```

**Environment Variables:**
```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
PORT=8082
```

**Dependencies:** PostgreSQL, Redis

---

### 2. MLflow Tracking Service

**Root Directory:** `services/mlflow-tracking`

**Build Command:**
```bash
chmod +x entrypoint.sh
```

**Start Command:**
```bash
./entrypoint.sh
```

**Environment Variables:**
```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
ARTIFACT_ROOT=/app/mlruns
PORT=5000
```

**Dependencies:** PostgreSQL

---

### 3. Data Collector Service

**Root Directory:** `services/data-collector`

**Start Command:**
```bash
uvicorn api:app --host 0.0.0.0 --port $PORT
```

**Environment Variables:**
```bash
BINANCE_API_KEY=<user_key>
BINANCE_SECRET_KEY=<user_secret>
REDIS_URL=${{Redis.REDIS_URL}}
VALIDATION_SERVICE_URL=${{DataValidation.RAILWAY_PUBLIC_DOMAIN}}
PORT=8001
SYMBOLS=BTCUSDT,ETHUSDT
INTERVALS=1m,5m,15m,1h
ENVIRONMENT=production
```

**Dependencies:** Redis, Data Validation

---

### 4. Backtest Engine Service

**Root Directory:** `services/backtest-engine`

**Start Command:**
```bash
uvicorn api:app --host 0.0.0.0 --port $PORT
```

**Environment Variables:**
```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
MLFLOW_TRACKING_URI=${{MLflow.RAILWAY_PUBLIC_DOMAIN}}
PORT=8002
```

**Dependencies:** PostgreSQL, MLflow

---

### 5. Optuna Optimizer Service

**Root Directory:** `services/optuna-optimizer`

**Start Command:**
```bash
uvicorn api:app --host 0.0.0.0 --port $PORT
```

**Environment Variables:**
```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
MLFLOW_TRACKING_URI=${{MLflow.RAILWAY_PUBLIC_DOMAIN}}
PORT=8003
```

**Dependencies:** PostgreSQL, MLflow

---

### 6. Market Memory Service

**Root Directory:** `services/market-memory`

**Start Command:**
```bash
uvicorn api:app --host 0.0.0.0 --port $PORT
```

**Environment Variables:**
```bash
QDRANT_URL=${{Qdrant.RAILWAY_PRIVATE_DOMAIN}}:6333
REDIS_URL=${{Redis.REDIS_URL}}
PORT=8004
```

**Dependencies:** Qdrant, Redis

---

### 7. Mesa Simulation Service

**Root Directory:** `services/mesa-simulation`

**Start Command:**
```bash
uvicorn api:app --host 0.0.0.0 --port $PORT
```

**Environment Variables:**
```bash
MLFLOW_TRACKING_URI=${{MLflow.RAILWAY_PUBLIC_DOMAIN}}
PORT=8005
```

**Dependencies:** MLflow

---

### 8. Pathway Pipeline Service

**Root Directory:** `services/pathway-pipeline`

**Start Command:**
```bash
uvicorn api:app --host 0.0.0.0 --port $PORT
```

**Environment Variables:**
```bash
REDIS_URL=${{Redis.REDIS_URL}}
QDRANT_URL=${{Qdrant.RAILWAY_PRIVATE_DOMAIN}}:6333
PORT=8006
```

**Dependencies:** Redis, Qdrant

---

### 9. RL Agent Service

**Root Directory:** `services/rl-agent`

**Start Command:**
```bash
uvicorn api:app --host 0.0.0.0 --port $PORT
```

**Environment Variables:**
```bash
MLFLOW_TRACKING_URI=${{MLflow.RAILWAY_PUBLIC_DOMAIN}}
REDIS_URL=${{Redis.REDIS_URL}}
QDRANT_URL=${{Qdrant.RAILWAY_PRIVATE_DOMAIN}}:6333
PORT=8007
```

**Dependencies:** MLflow, Redis, Qdrant

---

### 10. Freqtrade Integration Service

**Root Directory:** `services/freqtrade-integration`

**Build Command:**
```bash
chmod +x entrypoint.sh
```

**Start Command:**
```bash
./entrypoint.sh
```

**Environment Variables:**
```bash
BINANCE_API_KEY=<user_key>
BINANCE_SECRET_KEY=<user_secret>
MARKET_MEMORY_URL=${{MarketMemory.RAILWAY_PRIVATE_DOMAIN}}
RL_AGENT_URL=${{RLAgent.RAILWAY_PRIVATE_DOMAIN}}
REDIS_URL=${{Redis.REDIS_URL}}
MLFLOW_TRACKING_URI=${{MLflow.RAILWAY_PUBLIC_DOMAIN}}
```

**Dependencies:** Market Memory, RL Agent, Redis, MLflow

---

## 📊 Deployment Order (By Dependencies)

### Phase 1: Infrastructure (Already Done ✅)
1. ✅ PostgreSQL
2. ✅ Redis

### Phase 2: Vector Database
3. ⏳ Qdrant

### Phase 3: Core Services (No inter-service dependencies)
4. ⏳ MLflow Tracking (depends on PostgreSQL)
5. ⏳ Data Validation (depends on PostgreSQL, Redis)

### Phase 4: Data & Intelligence Services
6. ⏳ Data Collector (depends on Data Validation, Redis)
7. ⏳ Backtest Engine (depends on PostgreSQL, MLflow)
8. ⏳ Optuna Optimizer (depends on PostgreSQL, MLflow)
9. ⏳ Mesa Simulation (depends on MLflow)

### Phase 5: Memory & Processing Services
10. ⏳ Market Memory (depends on Qdrant, Redis)
11. ⏳ Pathway Pipeline (depends on Redis, Qdrant)
12. ⏳ RL Agent (depends on MLflow, Redis, Qdrant)

### Phase 6: Trading Execution
13. ⏳ Freqtrade Integration (depends on Market Memory, RL Agent, Redis, MLflow)

### Phase 7: Monitoring (Optional)
14. ⏳ Prometheus
15. ⏳ Grafana

---

## 🔐 Required Secrets

### Binance API (for Data Collector & Freqtrade)
```
BINANCE_API_KEY=FnbespwleoTxC1VUGAaP5sstXeu4nfuv80enfhwOhpeNz08BM0sC19pdRYayK8ap
BINANCE_SECRET_KEY=3uIce3m26CJv3eE4B9LPUaKZfcbGp39m9VoWleEA9annLYVRpp7h8ILM0RRiLWJ7
```

### PostgreSQL (Auto-generated by Railway)
```
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

### Redis (Auto-generated by Railway)
```
REDIS_URL=${{Redis.REDIS_URL}}
```

---

## 📝 Deployment Steps

### Option A: Railway Dashboard (Recommended)

1. **Open Railway Dashboard**
   - Navigate to: https://railway.app/dashboard
   - Select your project: `btc-trading-system`

2. **Deploy Qdrant**
   - Click "New Service"
   - Select "Docker Image"
   - Image: `qdrant/qdrant:latest`
   - Add to project

3. **Deploy Each Application Service**
   - Click "New Service"
   - Select "GitHub Repo"
   - Connect to: `pstrychalski/btc-trading-system`
   - Configure:
     - Root Directory: `services/<service-name>`
     - Start Command: (see above)
     - Environment Variables: (see above)
   - Deploy

4. **Configure Service References**
   - Use Railway's `${{ServiceName.VARIABLE}}` syntax
   - Private networking for internal communication
   - Public domains for external APIs

5. **Monitor Deployments**
   - Check build logs
   - Verify health endpoints
   - Test API endpoints

### Option B: Railway CLI (If logged in)

```bash
# Deploy all services
./deploy-all-railway.sh
```

### Option C: GitHub Actions (Future)

```yaml
# .github/workflows/deploy.yml
# Automated deployments on push to main
```

---

## 🧪 Post-Deployment Verification

### Check Health Endpoints

```bash
# Data Validation
curl https://<service-url>/health

# MLflow
curl https://<service-url>/health

# Data Collector
curl https://<service-url>/health

# Backtest Engine
curl https://<service-url>/health

# Optuna Optimizer
curl https://<service-url>/health

# Market Memory
curl https://<service-url>/health

# Mesa Simulation
curl https://<service-url>/health

# Pathway Pipeline
curl https://<service-url>/health

# RL Agent
curl https://<service-url>/health

# Freqtrade
curl https://<service-url>/health
```

### Test Integration

```bash
# 1. Start Data Collector
curl -X POST https://<data-collector-url>/start

# 2. Check Data Validation Stats
curl https://<data-validation-url>/stats

# 3. Run Backtest
curl -X POST https://<backtest-url>/backtest \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "moving_average_cross",
    "symbol": "BTC/USDT",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  }'

# 4. Check Freqtrade Bot Status
curl https://<freqtrade-url>/bot/status

# 5. View AI Stats
curl https://<freqtrade-url>/ai/stats
```

---

## 💰 Railway Cost Estimate

### Resource Usage per Service

| Service | Memory | CPU | Monthly Cost |
|---------|--------|-----|--------------|
| PostgreSQL | 512MB | 0.5 | $5 |
| Redis | 256MB | 0.25 | $3 |
| Qdrant | 512MB | 0.5 | $5 |
| Data Validation | 256MB | 0.25 | $3 |
| MLflow | 512MB | 0.5 | $5 |
| Data Collector | 256MB | 0.25 | $3 |
| Backtest Engine | 512MB | 0.5 | $5 |
| Optuna Optimizer | 512MB | 0.5 | $5 |
| Market Memory | 512MB | 0.5 | $5 |
| Mesa Simulation | 256MB | 0.25 | $3 |
| Pathway Pipeline | 256MB | 0.25 | $3 |
| RL Agent | 1GB | 1.0 | $10 |
| Freqtrade | 512MB | 0.5 | $5 |

**Total Estimated: ~$60-80/month**

Railway offers:
- $5 free credit/month
- $0.000463/GB-hour
- $0.000231/vCPU-hour

---

## 🔍 Troubleshooting

### Common Issues

1. **Build Failures**
   - Check Dockerfile syntax
   - Verify all dependencies in requirements.txt
   - Check root directory configuration

2. **Startup Failures**
   - Verify environment variables
   - Check start command syntax
   - Review service logs

3. **Connection Issues**
   - Verify service references (`${{ServiceName.VARIABLE}}`)
   - Check private networking configuration
   - Ensure dependent services are healthy

4. **Memory Issues**
   - Increase service resources
   - Optimize Docker image size
   - Use multi-stage builds

### Logs

```bash
# View logs via Railway CLI
railway logs <service-name>

# Or via Dashboard
# Navigate to service → Deployments → View Logs
```

---

## 📈 Next Steps After Deployment

1. **Monitor Performance**
   - Check Prometheus metrics
   - View Grafana dashboards
   - Monitor Railway resource usage

2. **Configure Alerts**
   - Set up health check monitoring
   - Configure error notifications
   - Set resource usage alerts

3. **Optimize Resources**
   - Adjust memory/CPU allocations
   - Enable autoscaling if needed
   - Optimize Docker images

4. **Security**
   - Enable Railway's firewall rules
   - Configure authentication
   - Set up API rate limiting

5. **Backup & Recovery**
   - Regular PostgreSQL backups
   - Redis persistence configuration
   - Qdrant data backups

---

**Last Updated:** 2025-10-06  
**Status:** Ready for deployment  
**Next Action:** Deploy via Railway Dashboard

