# 🚀 DigitalOcean Setup - Kompletny Przewodnik

**Data:** 2025-10-06  
**Status:** Migracja z Railway na DigitalOcean  
**Cel:** Deploy 13 serwisów na DigitalOcean App Platform

---

## 📋 **KROK 1: DigitalOcean CLI Setup**

### **Instalacja doctl** ✅ **GOTOWE**
```bash
# macOS (Homebrew)
brew install doctl

# Linux
snap install doctl

# Windows
# Download from: https://github.com/digitalocean/doctl/releases
```

### **Authentication Setup**
```bash
# Opcja 1: Token bezpośrednio
doctl auth init --access-token "your_digitalocean_token"

# Opcja 2: Environment variable (REKOMENDOWANE)
export DIGITALOCEAN_ACCESS_TOKEN="your_digitalocean_token"
doctl auth init

# Weryfikacja
doctl account get
```

---

## 🗄️ **KROK 2: Database Setup**

### **PostgreSQL Database**
```bash
# Stwórz PostgreSQL database
doctl databases create btc-postgres \
  --engine pg \
  --region nyc1 \
  --size db-s-1vcpu-1gb \
  --num-nodes 1

# Pobierz connection string
doctl databases connection btc-postgres --format ConnectionString
```

### **Redis Database**
```bash
# Stwórz Redis database
doctl databases create btc-redis \
  --engine redis \
  --region nyc1 \
  --size db-s-1vcpu-1gb \
  --num-nodes 1

# Pobierz connection string
doctl databases connection btc-redis --format ConnectionString
```

---

## 🐳 **KROK 3: Qdrant Setup**

### **Droplet dla Qdrant**
```bash
# Stwórz Droplet dla Qdrant
doctl compute droplet create qdrant-server \
  --image docker-20-04 \
  --size s-1vcpu-1gb \
  --region nyc1 \
  --ssh-keys your_ssh_key_id

# Po utworzeniu, SSH do serwera i zainstaluj Qdrant
ssh root@droplet_ip
docker run -p 6333:6333 qdrant/qdrant
```

---

## 📝 **KROK 4: App Platform Configuration**

### **Stwórz app.yaml**
```yaml
name: btc-trading-system
region: nyc
services:
  # 1. Data Validation Service
  - name: data-validation
    source_dir: services/data-validation
    run_command: uvicorn api:app --host 0.0.0.0 --port $PORT
    environment_slug: python
    instance_count: 1
    instance_size_slug: basic-xxs
    envs:
    - key: DATABASE_URL
      value: ${btc-postgres.DATABASE_URL}
    - key: PORT
      value: "8082"
    - key: ENVIRONMENT
      value: "production"
    health_check:
      http_path: "/health"
      initial_delay_seconds: 30
      period_seconds: 10
      timeout_seconds: 5
      success_threshold: 1
      failure_threshold: 3

  # 2. MLflow Tracking Service
  - name: mlflow-tracking
    source_dir: services/mlflow-tracking
    run_command: ./entrypoint.sh
    environment_slug: python
    instance_count: 1
    instance_size_slug: basic-xxs
    envs:
    - key: DATABASE_URL
      value: ${btc-postgres.DATABASE_URL}
    - key: PORT
      value: "5000"
    - key: MLFLOW_TRACKING_URI
      value: "http://localhost:5000"
    health_check:
      http_path: "/health"
      initial_delay_seconds: 30
      period_seconds: 10
      timeout_seconds: 5
      success_threshold: 1
      failure_threshold: 3

  # 3. Data Collector Service
  - name: data-collector
    source_dir: services/data-collector
    run_command: uvicorn api:app --host 0.0.0.0 --port $PORT
    environment_slug: python
    instance_count: 1
    instance_size_slug: basic-xxs
    envs:
    - key: PORT
      value: "8001"
    - key: SYMBOLS
      value: "BTCUSDT,ETHUSDT"
    - key: INTERVALS
      value: "1m,5m,15m,1h"
    - key: REDIS_URL
      value: ${btc-redis.DATABASE_URL}
    - key: VALIDATION_SERVICE_URL
      value: "http://data-validation:8082"
    - key: ENVIRONMENT
      value: "production"
    health_check:
      http_path: "/health"
      initial_delay_seconds: 30
      period_seconds: 10
      timeout_seconds: 5
      success_threshold: 1
      failure_threshold: 3

  # 4. Backtest Engine Service
  - name: backtest-engine
    source_dir: services/backtest-engine
    run_command: uvicorn api:app --host 0.0.0.0 --port $PORT
    environment_slug: python
    instance_count: 1
    instance_size_slug: basic-xs
    envs:
    - key: PORT
      value: "8002"
    - key: MLFLOW_TRACKING_URI
      value: "http://mlflow-tracking:5000"
    - key: DATABASE_URL
      value: ${btc-postgres.DATABASE_URL}
    - key: QDRANT_URL
      value: "http://qdrant-server:6333"
    health_check:
      http_path: "/health"
      initial_delay_seconds: 30
      period_seconds: 10
      timeout_seconds: 5
      success_threshold: 1
      failure_threshold: 3

  # 5. Optuna Optimizer Service
  - name: optuna-optimizer
    source_dir: services/optuna-optimizer
    run_command: uvicorn api:app --host 0.0.0.0 --port $PORT
    environment_slug: python
    instance_count: 1
    instance_size_slug: basic-xs
    envs:
    - key: PORT
      value: "8003"
    - key: MLFLOW_TRACKING_URI
      value: "http://mlflow-tracking:5000"
    - key: DATABASE_URL
      value: ${btc-postgres.DATABASE_URL}
    health_check:
      http_path: "/health"
      initial_delay_seconds: 30
      period_seconds: 10
      timeout_seconds: 5
      success_threshold: 1
      failure_threshold: 3

  # 6. Market Memory Service
  - name: market-memory
    source_dir: services/market-memory
    run_command: uvicorn api:app --host 0.0.0.0 --port $PORT
    environment_slug: python
    instance_count: 1
    instance_size_slug: basic-xs
    envs:
    - key: PORT
      value: "8004"
    - key: QDRANT_URL
      value: "http://qdrant-server:6333"
    - key: REDIS_URL
      value: ${btc-redis.DATABASE_URL}
    health_check:
      http_path: "/health"
      initial_delay_seconds: 30
      period_seconds: 10
      timeout_seconds: 5
      success_threshold: 1
      failure_threshold: 3

  # 7. Mesa Simulation Service
  - name: mesa-simulation
    source_dir: services/mesa-simulation
    run_command: uvicorn api:app --host 0.0.0.0 --port $PORT
    environment_slug: python
    instance_count: 1
    instance_size_slug: basic-xs
    envs:
    - key: PORT
      value: "8005"
    - key: MLFLOW_TRACKING_URI
      value: "http://mlflow-tracking:5000"
    health_check:
      http_path: "/health"
      initial_delay_seconds: 30
      period_seconds: 10
      timeout_seconds: 5
      success_threshold: 1
      failure_threshold: 3

  # 8. Pathway Pipeline Service
  - name: pathway-pipeline
    source_dir: services/pathway-pipeline
    run_command: uvicorn api:app --host 0.0.0.0 --port $PORT
    environment_slug: python
    instance_count: 1
    instance_size_slug: basic-xs
    envs:
    - key: PORT
      value: "8006"
    - key: REDIS_URL
      value: ${btc-redis.DATABASE_URL}
    - key: QDRANT_URL
      value: "http://qdrant-server:6333"
    health_check:
      http_path: "/health"
      initial_delay_seconds: 30
      period_seconds: 10
      timeout_seconds: 5
      success_threshold: 1
      failure_threshold: 3

  # 9. RL Agent Service
  - name: rl-agent
    source_dir: services/rl-agent
    run_command: uvicorn api:app --host 0.0.0.0 --port $PORT
    environment_slug: python
    instance_count: 1
    instance_size_slug: basic-s
    envs:
    - key: PORT
      value: "8007"
    - key: MLFLOW_TRACKING_URI
      value: "http://mlflow-tracking:5000"
    - key: REDIS_URL
      value: ${btc-redis.DATABASE_URL}
    - key: QDRANT_URL
      value: "http://qdrant-server:6333"
    health_check:
      http_path: "/health"
      initial_delay_seconds: 30
      period_seconds: 10
      timeout_seconds: 5
      success_threshold: 1
      failure_threshold: 3

  # 10. Freqtrade Integration Service
  - name: freqtrade-integration
    source_dir: services/freqtrade-integration
    run_command: ./entrypoint.sh
    environment_slug: python
    instance_count: 1
    instance_size_slug: basic-s
    envs:
    - key: BINANCE_API_KEY
      value: "your_binance_api_key"
    - key: BINANCE_SECRET_KEY
      value: "your_binance_secret_key"
    - key: MARKET_MEMORY_URL
      value: "http://market-memory:8004"
    - key: RL_AGENT_URL
      value: "http://rl-agent:8007"
    - key: REDIS_URL
      value: ${btc-redis.DATABASE_URL}
    - key: MLFLOW_TRACKING_URI
      value: "http://mlflow-tracking:5000"
    health_check:
      http_path: "/health"
      initial_delay_seconds: 60
      period_seconds: 10
      timeout_seconds: 5
      success_threshold: 1
      failure_threshold: 3

# Databases
databases:
  - name: btc-postgres
    engine: PG
    num_nodes: 1
    size: db-s-1vcpu-1gb
    region: nyc1

  - name: btc-redis
    engine: REDIS
    num_nodes: 1
    size: db-s-1vcpu-1gb
    region: nyc1
```

---

## 🚀 **KROK 5: Deploy na DigitalOcean**

### **Deploy App**
```bash
# Deploy całej aplikacji
doctl apps create --spec app.yaml

# Sprawdź status
doctl apps list

# Sprawdź logi
doctl apps logs your_app_id --follow
```

### **Update App**
```bash
# Update aplikacji
doctl apps update your_app_id --spec app.yaml

# Restart serwisu
doctl apps update your_app_id --spec app.yaml --force-rebuild
```

---

## 📊 **KROK 6: Monitoring i Logging**

### **Sprawdź Status**
```bash
# Lista aplikacji
doctl apps list

# Status aplikacji
doctl apps get your_app_id

# Logi aplikacji
doctl apps logs your_app_id --follow

# Logi konkretnego serwisu
doctl apps logs your_app_id --component data-validation --follow
```

### **Metrics i Monitoring**
```bash
# Sprawdź metryki
doctl apps get your_app_id --format json

# Sprawdź health checks
doctl apps get your_app_id --format json | jq '.spec.services[].health_check'
```

---

## 💰 **KOSZTY ESTYMACJA**

### **App Platform Services**
- **10 serwisów basic-xxs:** $5/miesiąc × 10 = $50/miesiąc
- **3 serwisy basic-xs:** $12/miesiąc × 3 = $36/miesiąc
- **2 serwisy basic-s:** $24/miesiąc × 2 = $48/miesiąc

**Total App Platform:** ~$134/miesiąc

### **Databases**
- **PostgreSQL:** $15/miesiąc
- **Redis:** $15/miesiąc

**Total Databases:** $30/miesiąc

### **Qdrant Droplet**
- **Droplet s-1vcpu-1gb:** $6/miesiąc

**Total Qdrant:** $6/miesiąc

### **TOTAL ESTIMATED COST: ~$170/miesiąc**

---

## 🔧 **TROUBLESHOOTING**

### **Common Issues**

**1. Authentication Error**
```bash
# Sprawdź token
doctl account get

# Re-authenticate
doctl auth init --access-token "your_token"
```

**2. Database Connection Error**
```bash
# Sprawdź connection string
doctl databases connection btc-postgres --format ConnectionString

# Test connection
doctl databases connection btc-postgres --format ConnectionString | psql
```

**3. Service Health Check Failed**
```bash
# Sprawdź logi
doctl apps logs your_app_id --component service-name --follow

# Restart serwis
doctl apps update your_app_id --spec app.yaml --force-rebuild
```

**4. Qdrant Connection Error**
```bash
# Sprawdź czy Qdrant działa
curl http://qdrant-server-ip:6333/health

# Sprawdź firewall
doctl compute firewall list
```

---

## 📚 **DOKUMENTACJA**

### **DigitalOcean CLI**
- [doctl Documentation](https://docs.digitalocean.com/reference/doctl/)
- [App Platform Documentation](https://docs.digitalocean.com/products/app-platform/)
- [Database Documentation](https://docs.digitalocean.com/products/databases/)

### **Useful Commands**
```bash
# Help
doctl apps --help
doctl databases --help
doctl compute --help

# List resources
doctl apps list
doctl databases list
doctl compute droplet list

# Get details
doctl apps get your_app_id
doctl databases get your_db_id
doctl compute droplet get your_droplet_id
```

---

## 🎯 **NEXT STEPS**

1. **Setup DigitalOcean Account** i pobierz token
2. **Configure doctl** z tokenem
3. **Create databases** (PostgreSQL, Redis)
4. **Setup Qdrant** na Droplet
5. **Deploy app.yaml** na App Platform
6. **Monitor** i testuj wszystkie serwisy

**Status:** Gotowe do deployment  
**Czas:** ~2-3h setup + deployment  
**Koszt:** ~$170/miesiąc (vs $60-80 Railway)

---

**Następna akcja:** Setup DigitalOcean account i token! 🚀
