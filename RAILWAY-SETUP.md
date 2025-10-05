# 🚂 Railway Infrastructure Setup

Instrukcje dodania PostgreSQL i Redis na Railway.app

## 📋 Wymagania

- Konto Railway.app
- Projekt `btc-trading-system` połączony z GitHub

## 🗄️ 1. Dodaj PostgreSQL

### Via Dashboard:

1. **Otwórz projekt**: https://railway.com/project/6a8d4034-fd86-4c47-8330-a6a21063f4be

2. **Kliknij "Create" → "Database"**

3. **Wybierz "Add PostgreSQL"**

4. **Konfiguracja**:
   - Name: `postgres`
   - Region: `us-west1` (lub najbliższy)
   - Plan: `Hobby` (darmowy do 500MB)

5. **Database zostanie utworzona automatycznie**

6. **Pobierz connection string**:
   - Kliknij na serwis `postgres`
   - Zakładka "Variables"
   - Skopiuj `DATABASE_URL`

### Via CLI:

```bash
# Zaloguj się do Railway (jeśli jeszcze nie)
railway login

# Link projekt (jeśli jeszcze nie)
railway link

# Dodaj PostgreSQL
railway add --plugin postgresql

# Zobacz connection string
railway variables
```

---

## 🔴 2. Dodaj Redis

### Via Dashboard:

1. **W tym samym projekcie kliknij "Create" → "Database"**

2. **Wybierz "Add Redis"**

3. **Konfiguracja**:
   - Name: `redis`
   - Region: `us-west1` (ten sam co PostgreSQL)
   - Plan: `Hobby` (darmowy do 100MB)

4. **Redis zostanie utworzony automatycznie**

5. **Pobierz connection string**:
   - Kliknij na serwis `redis`
   - Zakładka "Variables"
   - Skopiuj `REDIS_URL`

### Via CLI:

```bash
# Dodaj Redis
railway add --plugin redis

# Zobacz connection string
railway variables
```

---

## 🔗 3. Połącz Services z Databases

Railway **automatycznie** tworzy zmienne środowiskowe dla podłączonych serwisów:

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string

### Weryfikacja w Dashboard:

1. **Kliknij na serwis `btc-trading-system`**

2. **Zakładka "Variables"**

3. **Sprawdź czy są dostępne**:
   - `DATABASE_URL`
   - `REDIS_URL`

4. **Jeśli NIE - dodaj ręcznie**:
   - Kliknij "New Variable"
   - Name: `DATABASE_URL`
   - Value: (connection string z PostgreSQL)
   - Repeat dla `REDIS_URL`

---

## 🔌 4. Dodaj pozostałe Environment Variables

Dla każdego serwisu (przez Dashboard lub CLI):

### Data Collector:
```bash
BINANCE_API_KEY=FnbespwleoTxC1VUGAaP5sstXeu4nfuv80enfhwOhpeNz08BM0sC19pdRYayK8ap
BINANCE_SECRET_KEY=3uIce3m26CJv3eE4B9LPUaKZfcbGp39m9VoWleEA9annLYVRpp7h8ILM0RRiLWJ7
SYMBOLS=BTCUSDT,ETHUSDT
INTERVALS=1m,5m,15m,1h,4h,1d
```

### Data Validation:
```bash
POSTGRES_URL=${{DATABASE_URL}}
REDIS_URL=${{REDIS_URL}}
```

### MLflow:
```bash
DATABASE_URL=${{DATABASE_URL}}
ARTIFACT_ROOT=/app/mlruns
```

### Backtest Engine:
```bash
DATABASE_URL=${{DATABASE_URL}}
MLFLOW_TRACKING_URI=https://mlflow-service.railway.app
```

**Uwaga**: Railway automatycznie zastępuje `${{DATABASE_URL}}` rzeczywistą wartością!

---

## 📊 5. Initialize Database Schema

Po dodaniu PostgreSQL, musisz zainicjalizować schemat:

### Option A: Via Local psql

```bash
# Pobierz DATABASE_URL z Railway
export DATABASE_URL="postgresql://postgres:..."

# Run init script
psql $DATABASE_URL < init-db.sql
```

### Option B: Via Railway CLI

```bash
# Connect do Railway PostgreSQL
railway run psql

# W psql prompt:
\i /path/to/init-db.sql
```

### Option C: Via pgAdmin/DBeaver

1. Połącz się z Railway PostgreSQL używając connection string
2. Otwórz `init-db.sql`
3. Execute

---

## ✅ 6. Verify Setup

### Check Databases:

```bash
# PostgreSQL
railway run psql -c "\dt"

# Redis
railway run redis-cli PING
```

### Check Services:

1. **Data Validation**: https://btc-trading-system-production.up.railway.app/health
2. **MLflow**: https://mlflow-production.railway.app/
3. **Backtest Engine**: https://backtest-engine-production.railway.app/health

---

## 🎯 Quick Setup (All in One)

```bash
# 1. Login & Link
railway login
railway link

# 2. Add Databases
railway add --plugin postgresql
railway add --plugin redis

# 3. Initialize DB
railway run psql < init-db.sql

# 4. Add environment variables
railway variables set BINANCE_API_KEY="..."
railway variables set BINANCE_SECRET_KEY="..."
railway variables set SYMBOLS="BTCUSDT,ETHUSDT"

# 5. Redeploy (triggers new build with env vars)
railway up

# 6. Check status
railway status
railway logs
```

---

## 🔧 Troubleshooting

### Database Connection Issues:

```bash
# Test PostgreSQL connection
railway run psql -c "SELECT version();"

# Test Redis connection
railway run redis-cli PING
```

### Service Can't Connect to Database:

1. **Check Variables**:
   ```bash
   railway variables
   ```

2. **Verify DATABASE_URL format**:
   ```
   postgresql://user:pass@host:port/dbname
   ```

3. **Check Service References**:
   - Dashboard → Service → Variables
   - Ensure `${{DATABASE_URL}}` is used for service-to-service refs

### Railway CLI Issues:

```bash
# Relink project
railway unlink
railway link

# Relogin
railway logout
railway login
```

---

## 📚 Resources

- [Railway PostgreSQL Docs](https://docs.railway.com/databases/postgresql)
- [Railway Redis Docs](https://docs.railway.com/databases/redis)
- [Railway Environment Variables](https://docs.railway.com/develop/variables)
- [Railway Service References](https://docs.railway.com/deploy/deployments#service-variables)

---

## 🎉 Next Steps

Po ukończeniu setup:

1. ✅ PostgreSQL + Redis działają
2. ✅ Database schema zainicjalizowana
3. ✅ Environment variables ustawione
4. ✅ Services redeploy'owane

**Możesz przejść do:**
- Testowania Data Collector
- Uruchomienia pierwszego backtesta
- Konfiguracji MLflow experiments
- Deploy pozostałych services (Market Memory, RL Agent, etc.)

---

**Status**: 🚧 Setup w toku - PostgreSQL & Redis gotowe do dodania

