# 🔧 DigitalOcean Environment Variables Setup

**Data:** 2025-10-10  
**Cel:** Ustawienie environment variables w DigitalOcean Dashboard  
**Status:** W trakcie

---

## 🎯 **KROK 1: Otwórz DigitalOcean Dashboard**

**1.1 Otwórz App Settings**
- ✅ Otworzyłem: https://cloud.digitalocean.com/apps/4a9a6683-cb21-46fd-a81a-e573be09f218/settings
- 🔄 **Teraz musisz:**
  1. **Kliknij "Environment Variables" w lewym menu**
  2. **Dodaj nowe environment variables**

---

## 🔑 **KROK 2: Dodaj Environment Variables**

### **2.1 DATABASE_URL (PostgreSQL)**
```
Key: DATABASE_URL
Value: [POSTGRESQL_CONNECTION_STRING]
```

### **2.2 REDIS_URL (Redis/Valkey)**
```
Key: REDIS_URL
Value: [REDIS_CONNECTION_STRING]
```

### **2.3 BINANCE_API_KEY (Optional)**
```
Key: BINANCE_API_KEY
Value: [TWÓJ_BINANCE_API_KEY]
```

### **2.4 BINANCE_SECRET_KEY (Optional)**
```
Key: BINANCE_SECRET_KEY
Value: [TWÓJ_BINANCE_SECRET_KEY]
```

---

## 🚀 **KROK 3: Deploy Changes**

### **3.1 Po dodaniu environment variables:**
1. **Kliknij "Save"**
2. **App automatycznie się zrestartuje**
3. **Sprawdź logi deployment**

### **3.2 Sprawdź status:**
```bash
# Sprawdź status app
doctl apps get 4a9a6683-cb21-46fd-a81a-e573be09f218

# Sprawdź logi
doctl apps logs 4a9a6683-cb21-46fd-a81a-e573be09f218 --type run
```

---

## 🔍 **KROK 4: Weryfikacja**

### **4.1 Sprawdź endpoints:**
- **Data Validation:** https://btc-trading-system-minimal-h7me6.ondigitalocean.app/data-validation/health
- **MLflow Tracking:** https://btc-trading-system-minimal-h7me6.ondigitalocean.app/mlflow-tracking/health
- **Data Collector:** https://btc-trading-system-minimal-h7me6.ondigitalocean.app/data-collector/health

### **4.2 Sprawdź logi:**
- **Brak błędów PostgreSQL connection**
- **Brak błędów Redis connection**
- **Health checks OK**

---

## 📊 **STATUS:**

### ✅ **GOTOWE:**
- PostgreSQL database: `online`
- Redis/Valkey database: `online`
- App deployment: `ACTIVE (12/12)`
- MLflow permissions: `fixed`

### 🔄 **W TRAKCIE:**
- Environment variables setup
- Database connections test

### ❌ **PROBLEMY:**
- Binance API restrictions (Service unavailable from restricted location)
- Environment variables nie ustawione

---

## 🎯 **NASTĘPNE KROKI:**

1. **Ustaw environment variables w Dashboard**
2. **Test database connections**
3. **Fix Binance API restrictions**
4. **Verify all endpoints**

**STATUS: Gotowe do ustawienia environment variables!** 🚀
