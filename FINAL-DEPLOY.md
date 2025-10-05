# 🎯 FINALNA INSTRUKCJA DEPLOYMENTU

**Status:** Projekt utworzony przez API ✅  
**Projekt:** btc-trading-system  
**ID:** 6a8d4034-fd86-4c47-8330-a6a21063f4be

---

## ✅ Co Już Jest Gotowe

1. ✅ **Projekt utworzony** przez Railway API
2. ✅ **Jesteś zalogowany** do Railway  
3. ✅ **Dashboard działa** - https://railway.app/project/6a8d4034-fd86-4c47-8330-a6a21063f4be
4. ✅ **Kod gotowy** - Data Validation Service w `services/data-validation/`

---

## 🚀 CO MUSISZ ZROBIĆ (3 minuty)

### Metoda A: Railway CLI (Szybsza - Zalecane)

Otwórz Terminal i wklej te komendy **po kolei**:

```bash
# 1. Przejdź do projektu
cd /Users/piotrstrychalski/Documents/GitHub/btc

# 2. Połącz się z projektem
railway link 6a8d4034-fd86-4c47-8330-a6a21063f4be

# 3. Dodaj PostgreSQL
railway add -d postgresql

# 4. Dodaj Redis  
railway add -d redis

# 5. Poczekaj 30 sekund na deployment baz
sleep 30

# 6. Deploy Data Validation Service
cd services/data-validation
railway up --detach

# 7. Wróć do głównego katalogu
cd ../..

# 8. Ustaw zmienne środowiskowe
railway variables set ENVIRONMENT=production
railway variables set LOG_LEVEL=INFO
railway variables set VALIDATION_MAX_PRICE_CHANGE=50.0

# 9. Sprawdź status
railway status

# 10. Pobierz URL serwisu
railway domain
```

**Czas: ~3 minuty**

---

### Metoda B: Railway Dashboard (Wolniejsza)

1. **Otwórz:** https://railway.app/project/6a8d4034-fd86-4c47-8330-a6a21063f4be

2. **Kliknij "Create" → "Database"**
   - Wybierz "PostgreSQL"
   - Kliknij "Add"

3. **Kliknij "Create" → "Database"** (ponownie)
   - Wybierz "Redis"
   - Kliknij "Add"

4. **Kliknij "Create" → "GitHub Repo"**
   - Wybierz swój fork/repo z kodem
   - Lub kliknij "Deploy from GitHub" i podaj URL: `https://github.com/twoj-user/btc`

5. **W Settings serwisu ustaw:**
   - Root Directory: `services/data-validation`
   - Build Command: (auto)
   - Start Command: `uvicorn api:app --host 0.0.0.0 --port $PORT`

6. **Deploy!**

---

## 📊 Sprawdzenie Po Deploymencie

```bash
# Pobierz URL
URL=$(railway domain)

# Test health
curl $URL/health

# Powinno zwrócić:
# {"status":"healthy","service":"data-validation",...}
```

---

## 💡 Jeśli CLI Nie Działa

Najprostsze rozwiązanie - użyj Dashboard:

1. Przejdź do: https://railway.app/project/6a8d4034-fd86-4c47-8330-a6a21063f4be
2. Kliknij "+ New" (prawy górny róg)
3. Wybierz "Database" → "Add PostgreSQL"
4. Ponownie "+ New" → "Database" → "Add Redis"
5. Poczekaj 1-2 minuty
6. "+ New" → "Empty Service"
7. W Settings:
   - Source: GitHub (połącz repo)
   - Root Directory: `services/data-validation`
8. Deploy!

---

## 🎯 Ostateczny Test

Po deploymencie:

```bash
# 1. Sprawdź czy działa
railway status

# 2. Zobacz logi
railway logs

# 3. Pobierz URL
export SERVICE_URL=$(railway domain)

# 4. Test health endpoint
curl $SERVICE_URL/health | jq

# 5. Test validation  
curl -X POST $SERVICE_URL/validate/ohlcv \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTC/USDT",
    "data": [{
      "timestamp": "2024-01-01T00:00:00Z",
      "open": 43250.0,
      "high": 43500.0,
      "low": 43200.0,
      "close": 43450.0,
      "volume": 1234.5
    }]
  }' | jq
```

---

## ✨ Sukces!

Jeśli wszystko działa, zobaczysz:

```json
{
  "valid": true,
  "validated_at": "2025-10-05T...",
  "symbol": "BTC/USDT",
  "data_points": 1,
  "errors": null
}
```

---

## 📞 Potrzebujesz Pomocy?

- **Dashboard:** https://railway.app/project/6a8d4034-fd86-4c47-8330-a6a21063f4be
- **Logi:** `railway logs`
- **Status:** `railway status`
- **Railway Docs:** https://docs.railway.app

---

**WYBIERZ METODĘ I URUCHOM!** 🚀

Metoda A (CLI) jest **najszybsza** - wszystko za 3 minuty!

