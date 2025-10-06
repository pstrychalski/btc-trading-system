# 🚀 Railway Deployment - Instrukcje Krok po Kroku

**Data:** 2025-10-06  
**Status:** 🔴 Wymaga Twojej Interwencji  
**Problem:** Railway deployuje cały projekt jako 1 serwis zamiast 13 osobnych

---

## 🔍 CO ZNALAZŁEM

### Aktualny Stan Railway:

✅ **1 Serwis Aktywny:** `btc-trading-system`
- **URL:** `btc-trading-system-production.up.railway.app`
- **Status:** ACTIVE, Deployment successful
- **Root Directory:** `services/data-validation` ⚠️ PROBLEM!
- **Branch:** `main`
- **Auto-deploy:** Włączony (każdy push = redeploy)

### Historia Deploymentów (Wszystkie REMOVED):
1. Freqtrade AI Integration (4 min ago) - ostatni successful
2. Mesa + Pathway + RL (8 min ago) - REMOVED
3. Update PROGRESS.md (9h ago) - REMOVED  
4. Optuna + Market Memory (9h ago) - REMOVED
5. Backtest Engine (10h ago) - REMOVED

### 🔴 GŁÓWNY PROBLEM:

**Railway automatycznie deployuje cały projekt jako JEDEN serwis po każdym pushu do GitHub!**

- Root Directory = `services/data-validation` (ale kod się zmienia)
- Każdy nowy commit **zastępuje** poprzedni deployment
- Potrzebujesz **13 osobnych serwisów**, nie 1

---

## 🎯 ROZWIĄZANIE - 3 Opcje

### **OPCJA 1: Ręczne Dodanie Wszystkich Serwisów** (Rekomendowane)

**Dlaczego:** Pełna kontrola, najlepsza dla multi-service architecture

**Jak:**
1. **Usuń obecny auto-deploy z GitHub (opcjonalne)**
   - Settings → Danger → Disconnect GitHub Branch

2. **Dodaj każdy serwis manualnie**
   - Dla każdego z 13 serwisów:
   - "+ Create" → "GitHub Repo"
   - Select: `pstrychalski/btc-trading-system`
   - **WAŻNE:** Ustaw Root Directory na właściwy folder
   - Ustaw Start Command
   - Dodaj Environment Variables
   
3. **Kolejność dodawania** (według zależności - RAILWAY-DEPLOYMENT-PLAN.md)

**Czas:** ~2-3 godziny (wszystkie serwisy)

---

### **OPCJA 2: Użyj railway.toml** (Automatyczna - wymaga konfiguracji)

**Jak działa:** Railway czyta `railway.toml` i automatycznie konfiguruje multi-service deployment

**Co zrobić:**

1. **Sprawdź czy masz `railway.toml`:**
```bash
cat railway.toml
```

2. **Jeśli masz - aktywuj go:**
   - Railway Dashboard → Settings → Deploy
   - Railway automatycznie wykryje `railway.toml`
   - Deployment powinien utworzyć wszystkie serwisy

3. **Problem:** 
   - `railway.toml` może wymagać aktualizacji
   - Może nie działać z GitHub auto-deploy
   - Wymaga testów

**Czas:** ~30 minut (jeśli działa)

---

### **OPCJA 3: Railway CLI + Skrypt** (Programatyczne)

**Dla zaawansowanych użytkowników:**

```bash
# Zaloguj się
railway login

# Link projekt
railway link

# Deploy każdy serwis
for service in data-validation mlflow-tracking data-collector ...; do
  railway up --service $service --root services/$service
done
```

**Problem:** Railway CLI ma ograniczenia z multi-service projects

---

## ✅ MOJA REKOMENDACJA: OPCJA 1 (Ręcznie)

Ze względu na:
- 13 różnych serwisów
- Różne zależności między nimi
- Różne environment variables dla każdego
- Potrzebę kontroli nad kolejnością deployment

**Najlepiej jest dodać każdy serwis RĘCZNIE przez Railway Dashboard.**

---

## 📋 SZCZEGÓŁOWA INSTRUKCJA - OPCJA 1

### KROK 1: Przygotowanie

**A. Sprawdź czy masz PostgreSQL i Redis:**

1. Railway Dashboard → Architecture view
2. Szukaj serwisów typu "PostgreSQL" lub "Redis"
3. **Jeśli NIE ma:**
   - "+ Create" → "Database" → "Add PostgreSQL"
   - "+ Create" → "Database" → "Add Redis"

**B. Zapisz connection strings:**
- PostgreSQL: `DATABASE_URL`
- Redis: `REDIS_URL`

---

### KROK 2: Dodaj Qdrant (Infrastructure)

```
1. "+ Create" → "Docker Image"
2. Image: qdrant/qdrant:latest
3. Name: "qdrant"
4. Deploy
5. Czekaj na "Healthy" status
```

---

### KROK 3: Dodaj MLflow Tracking

```
1. "+ Create" → "GitHub Repo"
2. Select: pstrychalski/btc-trading-system
3. Service Name: "mlflow-tracking"
4. Root Directory: services/mlflow-tracking
5. Start Command: ./entrypoint.sh
6. Environment Variables:
   - DATABASE_URL: ${{Postgres.DATABASE_URL}}
   - ARTIFACT_ROOT: /app/mlruns
   - PORT: 5000
7. Deploy
```

---

### KROK 4: Dodaj Data Validation

```
1. "+ Create" → "GitHub Repo"
2. Select: pstrychalski/btc-trading-system
3. Service Name: "data-validation"
4. Root Directory: services/data-validation
5. Start Command: uvicorn api:app --host 0.0.0.0 --port $PORT
6. Environment Variables:
   - DATABASE_URL: ${{Postgres.DATABASE_URL}}
   - REDIS_URL: ${{Redis.REDIS_URL}}
   - PORT: 8082
7. Deploy
```

---

### KROK 5: Dodaj Data Collector

```
1. "+ Create" → "GitHub Repo"
2. Select: pstrychalski/btc-trading-system
3. Service Name: "data-collector"
4. Root Directory: services/data-collector
5. Start Command: uvicorn api:app --host 0.0.0.0 --port $PORT
6. Environment Variables:
   - BINANCE_API_KEY: FnbespwleoTxC1VUGAaP5sstXeu4nfuv80enfhwOhpeNz08BM0sC19pdRYayK8ap
   - BINANCE_SECRET_KEY: 3uIce3m26CJv3eE4B9LPUaKZfcbGp39m9VoWleEA9annLYVRpp7h8ILM0RRiLWJ7
   - REDIS_URL: ${{Redis.REDIS_URL}}
   - VALIDATION_SERVICE_URL: ${{DataValidation.RAILWAY_PRIVATE_DOMAIN}}
   - PORT: 8001
   - SYMBOLS: BTCUSDT,ETHUSDT
   - INTERVALS: 1m,5m,15m,1h
   - ENVIRONMENT: production
7. Deploy
```

---

### KROK 6: Dodaj Backtest Engine

```
1. "+ Create" → "GitHub Repo"
2. Select: pstrychalski/btc-trading-system
3. Service Name: "backtest-engine"
4. Root Directory: services/backtest-engine
5. Start Command: uvicorn api:app --host 0.0.0.0 --port $PORT
6. Environment Variables:
   - DATABASE_URL: ${{Postgres.DATABASE_URL}}
   - MLFLOW_TRACKING_URI: ${{MLflowTracking.RAILWAY_PRIVATE_DOMAIN}}
   - PORT: 8002
7. Deploy
```

---

### KROK 7: Dodaj Optuna Optimizer

```
1. "+ Create" → "GitHub Repo"
2. Select: pstrychalski/btc-trading-system
3. Service Name: "optuna-optimizer"
4. Root Directory: services/optuna-optimizer
5. Start Command: uvicorn api:app --host 0.0.0.0 --port $PORT
6. Environment Variables:
   - DATABASE_URL: ${{Postgres.DATABASE_URL}}
   - MLFLOW_TRACKING_URI: ${{MLflowTracking.RAILWAY_PRIVATE_DOMAIN}}
   - PORT: 8003
7. Deploy
```

---

### KROK 8: Dodaj Mesa Simulation

```
1. "+ Create" → "GitHub Repo"
2. Select: pstrychalski/btc-trading-system
3. Service Name: "mesa-simulation"
4. Root Directory: services/mesa-simulation
5. Start Command: uvicorn api:app --host 0.0.0.0 --port $PORT
6. Environment Variables:
   - MLFLOW_TRACKING_URI: ${{MLflowTracking.RAILWAY_PRIVATE_DOMAIN}}
   - PORT: 8005
7. Deploy
```

---

### KROK 9: Dodaj Market Memory

```
1. "+ Create" → "GitHub Repo"
2. Select: pstrychalski/btc-trading-system
3. Service Name: "market-memory"
4. Root Directory: services/market-memory
5. Start Command: uvicorn api:app --host 0.0.0.0 --port $PORT
6. Environment Variables:
   - QDRANT_URL: ${{Qdrant.RAILWAY_PRIVATE_DOMAIN}}:6333
   - REDIS_URL: ${{Redis.REDIS_URL}}
   - PORT: 8004
7. Deploy
```

---

### KROK 10: Dodaj Pathway Pipeline

```
1. "+ Create" → "GitHub Repo"
2. Select: pstrychalski/btc-trading-system
3. Service Name: "pathway-pipeline"
4. Root Directory: services/pathway-pipeline
5. Start Command: uvicorn api:app --host 0.0.0.0 --port $PORT
6. Environment Variables:
   - REDIS_URL: ${{Redis.REDIS_URL}}
   - QDRANT_URL: ${{Qdrant.RAILWAY_PRIVATE_DOMAIN}}:6333
   - PORT: 8006
7. Deploy
```

---

### KROK 11: Dodaj RL Agent

```
1. "+ Create" → "GitHub Repo"
2. Select: pstrychalski/btc-trading-system
3. Service Name: "rl-agent"
4. Root Directory: services/rl-agent
5. Start Command: uvicorn api:app --host 0.0.0.0 --port $PORT
6. Environment Variables:
   - MLFLOW_TRACKING_URI: ${{MLflowTracking.RAILWAY_PRIVATE_DOMAIN}}
   - REDIS_URL: ${{Redis.REDIS_URL}}
   - QDRANT_URL: ${{Qdrant.RAILWAY_PRIVATE_DOMAIN}}:6333
   - PORT: 8007
7. Deploy
```

---

### KROK 12: Dodaj Freqtrade Integration

```
1. "+ Create" → "GitHub Repo"
2. Select: pstrychalski/btc-trading-system
3. Service Name: "freqtrade-integration"
4. Root Directory: services/freqtrade-integration
5. Start Command: ./entrypoint.sh
6. Environment Variables:
   - BINANCE_API_KEY: FnbespwleoTxC1VUGAaP5sstXeu4nfuv80enfhwOhpeNz08BM0sC19pdRYayK8ap
   - BINANCE_SECRET_KEY: 3uIce3m26CJv3eE4B9LPUaKZfcbGp39m9VoWleEA9annLYVRpp7h8ILM0RRiLWJ7
   - MARKET_MEMORY_URL: ${{MarketMemory.RAILWAY_PRIVATE_DOMAIN}}
   - RL_AGENT_URL: ${{RLAgent.RAILWAY_PRIVATE_DOMAIN}}
   - REDIS_URL: ${{Redis.REDIS_URL}}
   - MLFLOW_TRACKING_URI: ${{MLflowTracking.RAILWAY_PRIVATE_DOMAIN}}
7. Deploy
```

---

### KROK 13: Usuń Stary Serwis (Opcjonalne)

```
1. Wróć do stareg serwisu "btc-trading-system"
2. Settings → Danger → Delete Service
3. Potwierdź
```

---

## ✅ WERYFIKACJA

Po dodaniu wszystkich serwisów:

### 1. Sprawdź Status
```
Railway Dashboard → Architecture View
- Wszystkie serwisy powinny być zielone (Healthy)
```

### 2. Test Health Endpoints
```bash
# MLflow
curl https://<mlflow-url>/health

# Data Validation
curl https://<data-validation-url>/health

# Data Collector
curl https://<data-collector-url>/health

# Backtest Engine
curl https://<backtest-url>/health

# Optuna Optimizer
curl https://<optuna-url>/health

# Market Memory
curl https://<market-memory-url>/health

# Mesa Simulation
curl https://<mesa-url>/health

# Pathway Pipeline
curl https://<pathway-url>/health

# RL Agent
curl https://<rl-agent-url>/health

# Freqtrade
curl https://<freqtrade-url>/health
```

### 3. Test Integration
```bash
# Start Data Collector
curl -X POST https://<data-collector-url>/start

# Check Stats
curl https://<data-validation-url>/stats

# Check Freqtrade Bot Status
curl https://<freqtrade-url>/bot/status
```

---

## 💰 Koszty

**Szacunkowe koszty miesięczne:**
- PostgreSQL: $5
- Redis: $3
- Qdrant: $5
- MLflow: $5
- Data Validation: $3
- Data Collector: $3
- Backtest Engine: $5
- Optuna Optimizer: $5
- Market Memory: $5
- Mesa Simulation: $3
- Pathway Pipeline: $3
- RL Agent: $10 (wymaga więcej resources)
- Freqtrade: $5

**TOTAL: ~$60-80/miesiąc**

Railway offers:
- $5 free credit/month
- Pay-as-you-go pricing

---

## 🆘 Potrzebujesz Pomocy?

Jeśli cokolwiek nie działa:

1. Sprawdź **Logs** dla każdego serwisu
2. Sprawdź **Variables** - czy wszystkie są ustawione
3. Sprawdź **Dependencies** - czy poprzednie serwisy są healthy
4. Zobacz `RAILWAY-DEPLOYMENT-PLAN.md` dla więcej szczegółów

---

## 📝 Podsumowanie

**CO MUSISZ ZROBIĆ:**

1. ✅ Przeczytaj tę instrukcję
2. ⏳ Dodaj PostgreSQL i Redis (jeśli nie ma)
3. ⏳ Dodaj 11 application services (KROK 2-12)
4. ⏳ Usuń stary serwis "btc-trading-system"
5. ✅ Zweryfikuj wszystkie health endpoints
6. ✅ Przetestuj integrację

**CZAS:** ~2-3 godziny dla wszystkich serwisów

**WYNIK:** 13 w pełni działających, połączonych ze sobą serwisów na Railway! 🚀

---

**Pytania?** Napisz do mnie! 

**Powodzenia!** 🎉

