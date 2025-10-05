# 🚀 Deployment Guide - Railway

**Cel:** Wdrożenie systemu tradingowego na Railway.app  
**Status:** Data Validation Service - Ready to Deploy  
**Data:** 2025-10-05

---

## ✅ Przed Deploymentem - Checklist

### 1. Railway Account
- [x] Konto Railway założone (piotr.strychalski@icloud.com)
- [ ] Railway CLI zainstalowane (`npm i -g @railway/cli`)
- [ ] Zalogowany do Railway (`railway login`)

### 2. API Keys (Wymaga uzupełnienia)
- [ ] Binance API Key (lub inny exchange)
- [ ] Binance API Secret
- [ ] Edytuj plik `.env.railway` z kluczami

### 3. Serwisy Gotowe do Deploymentu
- [x] **Data Validation Service** ✅ (100% complete)
  - Dockerfile
  - Great Expectations validator
  - FastAPI REST API
  - PostgreSQL integration
  - Prometheus metrics
- [ ] Data Collector (TODO)
- [ ] MLflow (TODO)
- [ ] Pozostałe serwisy (TODO)

---

## 🚀 Quick Start - Deploy Data Validation

### Krok 1: Zaloguj się do Railway

```bash
railway login
```

To otworzy przeglądarkę. Zaloguj się przez:
- Email: piotr.strychalski@icloud.com
- Lub przez GitHub

### Krok 2: Zainicjalizuj Projekt

```bash
cd /Users/piotrstrychalski/Documents/GitHub/btc
railway init
```

Wybierz:
- Create new project: YES
- Nazwa projektu: `btc-trading-system` (lub dowolna)

### Krok 3: Dodaj PostgreSQL

```bash
railway add --plugin postgresql
```

Railway automatycznie:
- Utworzy bazę danych
- Ustawi zmienną `DATABASE_URL`
- Połączy z Twoim projektem

### Krok 4: Dodaj Redis

```bash
railway add --plugin redis
```

Railway automatycznie:
- Utworzy instancję Redis
- Ustawi zmienną `REDIS_URL`

### Krok 5: Deploy Data Validation Service

```bash
cd services/data-validation
railway up
```

Railway:
- Zbuduje Docker image
- Wdroży serwis
- Przydzieli publiczny URL

### Krok 6: Ustaw Zmienne Środowiskowe

```bash
# Z głównego katalogu projektu
railway variables set ENVIRONMENT=production
railway variables set LOG_LEVEL=INFO
railway variables set VALIDATION_MAX_PRICE_CHANGE=50.0
```

Lub użyj Railway Dashboard (łatwiejsze):
https://railway.app/dashboard → Twój projekt → Variables

### Krok 7: Sprawdź Status

```bash
# Status wszystkich serwisów
railway status

# Logi data-validation
railway logs

# Otwórz w przeglądarce
railway open
```

---

## 📋 Automatyczny Deployment (Alternatywa)

Użyj przygotowanego skryptu:

```bash
# Najpierw zaloguj się
railway login

# Potem uruchom skrypt
./deploy-to-railway.sh
```

Skrypt automatycznie:
1. Sprawdzi czy jesteś zalogowany
2. Zainicjalizuje projekt
3. Doda PostgreSQL i Redis
4. Wdroży Data Validation Service
5. Ustawi zmienne środowiskowe z `.env.railway`

---

## 🔧 Konfiguracja - Environment Variables

### Wymagane (Railway ustawi automatycznie)
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `PORT` - Port dla serwisu (Railway przydzieli)

### Do ustawienia ręcznie
```bash
railway variables set ENVIRONMENT=production
railway variables set LOG_LEVEL=INFO
railway variables set VALIDATION_MAX_PRICE_CHANGE=50.0
railway variables set VALIDATION_STORE_FAILURES=true
```

### Exchange API Keys (WAŻNE - Dodaj później)
```bash
railway variables set EXCHANGE_API_KEY=your_key_here
railway variables set EXCHANGE_API_SECRET=your_secret_here
```

**⚠️ UWAGA:** Nie commituj API keys do git!

---

## 🧪 Testowanie Po Deploymencie

### 1. Health Check

```bash
# Znajdź URL swojego serwisu
railway status

# Testuj health endpoint
curl https://your-service-url.railway.app/health
```

Oczekiwany output:
```json
{
  "status": "healthy",
  "service": "data-validation",
  "timestamp": "2025-10-05T...",
  "version": "1.0.0"
}
```

### 2. Test Validation Endpoint

```bash
curl -X POST https://your-service-url.railway.app/validate/ohlcv \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTC/USDT",
    "data": [
      {
        "timestamp": "2024-01-01T00:00:00Z",
        "open": 43250.0,
        "high": 43500.0,
        "low": 43200.0,
        "close": 43450.0,
        "volume": 1234.5
      }
    ]
  }'
```

### 3. Sprawdź Metryki Prometheus

```bash
curl https://your-service-url.railway.app/metrics
```

### 4. Sprawdź Statystyki

```bash
curl https://your-service-url.railway.app/stats
```

---

## 📊 Monitoring

### Railway Dashboard

1. Przejdź do: https://railway.app/dashboard
2. Wybierz swój projekt: `btc-trading-system`
3. Zobacz:
   - **Deployments:** Status wdrożeń
   - **Metrics:** CPU, Memory, Network
   - **Logs:** Real-time logs
   - **Variables:** Environment variables

### Logi w Czasie Rzeczywistym

```bash
# Wszystkie logi
railway logs

# Follow mode (jak tail -f)
railway logs --follow

# Tylko z data-validation
railway logs --service data-validation
```

### Metrics

Railway Dashboard pokazuje:
- CPU usage (%)
- Memory usage (MB)
- Network (in/out)
- Request count
- Response time

---

## 🐛 Troubleshooting

### Problem: Service won't start

**Check:**
```bash
railway logs
```

**Common issues:**
- Missing environment variables
- Database connection failed
- Port conflict

**Fix:**
```bash
# Sprawdź zmienne
railway variables

# Sprawdź czy DATABASE_URL jest ustawione
railway variables | grep DATABASE_URL

# Restart service
railway restart
```

### Problem: Cannot connect to database

**Check:**
```bash
railway variables | grep DATABASE_URL
```

**Fix:**
```bash
# Jeśli brak, dodaj PostgreSQL
railway add --plugin postgresql

# Sprawdź połączenie
railway run psql $DATABASE_URL
```

### Problem: 502 Bad Gateway

**Możliwe przyczyny:**
- Service nie odpowiada na porcie
- Health check failing
- Service crashuje

**Fix:**
```bash
# Sprawdź logi
railway logs --service data-validation

# Sprawdź czy PORT jest poprawnie używany
# W Dockerfile: EXPOSE 8082
# W api.py: port=8082
# Railway automatycznie mapuje

# Restart
railway restart
```

### Problem: Out of memory

**Check:**
```bash
railway status
```

**Fix:**
- Upgrade Railway plan (więcej RAM)
- Optymalizuj kod (memory leaks?)
- Zmniejsz batch size w validatorze

---

## 💰 Koszty

### Railway Pricing (aktualne 2025)

**Hobby Plan (FREE):**
- $5 credit/month
- Wystarczy na development/testing
- 512MB RAM per service
- Współdzielone CPU

**Developer Plan ($5/month):**
- $5 subscription + usage
- 8GB RAM per service
- Priority support

**Team Plan ($20/month):**
- $20 subscription + usage
- Team collaboration
- More resources

### Szacunkowe koszty dla naszego systemu:

**Faza 1 (tylko Data Validation):**
- PostgreSQL: ~$0-5/month
- Redis: ~$0-3/month
- Data Validation Service: ~$0-5/month
- **Total: $0-13/month** (może zmieścić się w free tier!)

**Full System (wszystkie serwisy):**
- PostgreSQL: ~$5/month
- Redis: ~$5/month
- Qdrant: ~$10/month
- 6 custom services: ~$30/month
- **Total: ~$50-85/month**

### Optymalizacja kosztów:

1. **Użyj Railway free tier dla dev/test**
2. **Qdrant Cloud free tier** (zamiast self-hosted)
3. **Combine services** gdzie możliwe
4. **Auto-sleep** dla dev services (Railway feature)

---

## 📈 Następne Kroki

### Po wdrożeniu Data Validation:

1. **Monitoruj przez tydzień**
   - Sprawdzaj logi codziennie
   - Mierz performance
   - Szukaj errors

2. **Deploy Data Collector**
   - Potrzebny do zbierania danych z exchange
   - Integracja z Data Validation

3. **Deploy MLflow**
   - Tracking eksperymentów ML
   - Model registry

4. **Iteruj według ROADMAP.md**

### Continuous Deployment

Railway wspiera auto-deploy z Git:

```bash
# Link GitHub repo
railway link

# Auto-deploy on push to main
railway environment production
```

Każdy push do `main` → automatic deployment!

---

## 🔗 Linki

- **Railway Dashboard:** https://railway.app/dashboard
- **Railway Docs:** https://docs.railway.app
- **Railway CLI Docs:** https://docs.railway.app/develop/cli
- **Status Page:** https://status.railway.app

---

## 📝 Quick Reference

```bash
# Login
railway login

# Initialize project
railway init

# Add database
railway add --plugin postgresql
railway add --plugin redis

# Deploy service
cd services/data-validation && railway up

# Set variables
railway variables set KEY=value

# View logs
railway logs

# Check status
railway status

# Open dashboard
railway open

# Get service URL
railway domain

# Restart service
railway restart

# Delete service (careful!)
railway delete
```

---

**Last Updated:** 2025-10-05  
**Service Ready:** Data Validation ✅  
**Next:** Data Collector, MLflow

