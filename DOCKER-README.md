# 🐳 BTC Trading System - Docker Setup

## 🚀 Quick Start

### 1. Build and Start All Services
```bash
# Build all Docker images
./docker-manage.sh build

# Start all services
./docker-manage.sh start

# Check status
./docker-manage.sh status

# Check health
./docker-manage.sh health
```

### 2. Access Services
- **Data Validation**: http://localhost:8082
- **MLflow Tracking**: http://localhost:5000
- **Freqtrade Integration**: http://localhost:8089
- **Market Memory**: http://localhost:8085
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Qdrant**: http://localhost:6333

## 📋 Available Commands

```bash
# Build all services
./docker-manage.sh build

# Start all services
./docker-manage.sh start

# Stop all services
./docker-manage.sh stop

# Restart all services
./docker-manage.sh restart

# Show logs (all services)
./docker-manage.sh logs

# Show logs (specific service)
./docker-manage.sh logs data-validation

# Check service status
./docker-manage.sh status

# Health check
./docker-manage.sh health

# Clean up
./docker-manage.sh clean
```

## 🔧 Development

### Individual Service Management
```bash
# Build specific service
docker-compose build data-validation

# Start specific service
docker-compose up -d data-validation

# View logs for specific service
docker-compose logs -f data-validation

# Stop specific service
docker-compose stop data-validation
```

### Database Access
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d btc_trading

# Connect to Redis
docker-compose exec redis redis-cli

# Access Qdrant
curl http://localhost:6333/collections
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL   │    │      Redis      │    │     Qdrant      │
│   (Database)   │    │   (Cache/Queue) │    │ (Vector Store)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
    ┌────────────────────────────┼────────────────────────────┐
    │                            │                            │
┌───▼───┐  ┌─────────────┐  ┌────▼────┐  ┌─────────────────┐
│ Data  │  │    MLflow   │  │Freqtrade│  │  Market Memory  │
│Validation│  │  Tracking  │  │Integration│  │   Service      │
└───────┘  └─────────────┘  └─────────┘  └─────────────────┘
```

## 🔍 Troubleshooting

### Common Issues

1. **Port conflicts**
   ```bash
   # Check what's using the ports
   lsof -i :8082
   lsof -i :5000
   lsof -i :8089
   lsof -i :8085
   ```

2. **Service not starting**
   ```bash
   # Check logs
   ./docker-manage.sh logs [service-name]
   
   # Check service status
   ./docker-manage.sh status
   ```

3. **Database connection issues**
   ```bash
   # Check if PostgreSQL is running
   docker-compose exec postgres pg_isready -U postgres
   
   # Check Redis
   docker-compose exec redis redis-cli ping
   ```

4. **Clean restart**
   ```bash
   # Stop everything and clean up
   ./docker-manage.sh clean
   
   # Rebuild and start
   ./docker-manage.sh build
   ./docker-manage.sh start
   ```

## 📊 Monitoring

### Health Checks
All services have health checks configured:
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3

### Logs
```bash
# View all logs
./docker-manage.sh logs

# View specific service logs
./docker-manage.sh logs data-validation
```

## 🚀 Production Deployment

### Option 1: DigitalOcean Droplets
```bash
# Deploy to DigitalOcean Droplet
docker-compose -f docker-compose.prod.yml up -d
```

### Option 2: Railway
```bash
# Deploy to Railway
railway up
```

### Option 3: Kubernetes
```bash
# Deploy to Kubernetes
kubectl apply -f k8s/
```

## 🔐 Environment Variables

Create `.env` file for production:
```env
DATABASE_URL=postgresql://user:password@host:5432/database
REDIS_URL=redis://host:6379
QDRANT_URL=http://host:6333
MLFLOW_TRACKING_URI=http://host:5000
```

## 📈 Benefits of Docker Approach

✅ **Stability** - No auto-rebuild on every commit
✅ **Control** - All dependencies in Dockerfile
✅ **Isolation** - Each service in its own container
✅ **Reproducibility** - Identical environment everywhere
✅ **Debugging** - Easier to debug issues
✅ **Performance** - Faster deployments
✅ **Flexibility** - Deploy anywhere (Droplets, Railway, K8s)
