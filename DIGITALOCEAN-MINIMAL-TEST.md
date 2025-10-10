# 🧪 DigitalOcean Minimal Test - Sprawdzenie Działania

**Data:** 2025-10-06  
**Cel:** Test minimalnej konfiguracji na DigitalOcean  
**Serwisy:** 3 (data-validation, mlflow-tracking, data-collector)

---

## 🎯 **MINIMAL TEST PLAN**

### **Serwisy do Testu**
1. **data-validation** (basic-xxs) - $5/miesiąc
2. **mlflow-tracking** (basic-xxs) - $5/miesiąc  
3. **data-collector** (basic-xxs) - $5/miesiąc

**Total Cost:** ~$15/miesiąc (vs $170/miesiąc full)

---

## 🔧 **KROK 1: DigitalOcean CLI Setup**

### **1.1 Sprawdź czy doctl działa**
```bash
# Sprawdź wersję
doctl version

# Sprawdź czy jest skonfigurowany
doctl account get
```

### **1.2 Jeśli nie ma tokenu, skonfiguruj**
```bash
# Pobierz token z: https://cloud.digitalocean.com/account/api/tokens
export DIGITALOCEAN_ACCESS_TOKEN="your_token"
doctl auth init

# Weryfikacja
doctl account get
```

---

## 🚀 **KROK 2: Test Deploy**

### **2.1 Sprawdź app-minimal.yaml**
```bash
# Sprawdź czy plik istnieje
ls -la app-minimal.yaml

# Sprawdź składnię (dry-run)
doctl apps create --spec app-minimal.yaml --dry-run
```

### **2.2 Deploy Minimal App**
```bash
# Deploy minimalnej aplikacji
doctl apps create --spec app-minimal.yaml

# Sprawdź status
doctl apps list
```

### **2.3 Sprawdź Status**
```bash
# Pobierz App ID
APP_ID=$(doctl apps list --format ID,Name --no-header | grep "btc-trading-system-minimal" | awk '{print $1}')

# Sprawdź status
doctl apps get $APP_ID

# Sprawdź logi
doctl apps logs $APP_ID --follow
```

---

## 📊 **KROK 3: Verification**

### **3.1 Sprawdź Wszystkie Serwisy**
```bash
# Sprawdź status serwisów
doctl apps get $APP_ID --format json | jq '.spec.services[].name'

# Sprawdź health checks
doctl apps get $APP_ID --format json | jq '.spec.services[].health_check'
```

### **3.2 Test Health Endpoints**
```bash
# Pobierz URLs
doctl apps get $APP_ID --format json | jq '.spec.services[].ingress'

# Test health endpoints
curl -f https://your-app-url/data-validation/health
curl -f https://your-app-url/mlflow-tracking/health  
curl -f https://your-app-url/data-collector/health
```

---

## 🔧 **KROK 4: Troubleshooting**

### **4.1 Common Issues**

**Authentication Error**
```bash
# Sprawdź token
doctl account get

# Re-authenticate
doctl auth init --access-token "your_token"
```

**Service Health Check Failed**
```bash
# Sprawdź logi konkretnego serwisu
doctl apps logs $APP_ID --component data-validation --follow

# Restart serwis
doctl apps update $APP_ID --spec app-minimal.yaml --force-rebuild
```

**Build Error**
```bash
# Sprawdź build logs
doctl apps logs $APP_ID --component data-validation --follow

# Sprawdź czy source_dir istnieje
ls -la services/data-validation/
```

---

## 📈 **KROK 5: Success Criteria**

### **✅ Checklist**
- [ ] DigitalOcean CLI działa
- [ ] App deployed successfully
- [ ] Wszystkie 3 serwisy działają
- [ ] Health checks przechodzą
- [ ] API endpoints odpowiadają
- [ ] Logi są dostępne

### **📊 Expected Results**
- **Deployment time:** ~5-10 minut
- **Cost:** ~$15/miesiąc
- **Services:** 3 działające
- **Health checks:** Wszystkie ✅

---

## 🚀 **KROK 6: Next Steps (Po Sukcesie)**

### **Jeśli minimal test działa:**
1. **Add databases** (PostgreSQL, Redis)
2. **Add Qdrant** (Droplet)
3. **Deploy full app.yaml** (13 serwisów)
4. **Monitor** i optimize

### **Jeśli minimal test nie działa:**
1. **Debug** specific issues
2. **Fix** configuration
3. **Retry** minimal test
4. **Scale up** dopiero po sukcesie

---

## 💰 **COST COMPARISON**

| Test | Serwisy | Koszt/miesiąc | Czas |
|------|---------|---------------|------|
| **Minimal** | 3 | $15 | 5-10 min |
| **Full** | 13 | $170 | 2-3h |

**Strategy:** Start minimal → Scale up

---

## 🎯 **COMMANDS SUMMARY**

```bash
# 1. Setup
doctl auth init --access-token "your_token"

# 2. Test
doctl apps create --spec app-minimal.yaml --dry-run

# 3. Deploy
doctl apps create --spec app-minimal.yaml

# 4. Monitor
doctl apps list
doctl apps get $APP_ID
doctl apps logs $APP_ID --follow

# 5. Test endpoints
curl https://your-app-url/data-validation/health
curl https://your-app-url/mlflow-tracking/health
curl https://your-app-url/data-collector/health
```

---

## 🎯 **STATUS**

**Minimal Test:** 🧪 **READY TO TEST**  
**Full Deployment:** ⏳ **PENDING**  
**Cost:** $15/miesiąc (minimal) vs $170/miesiąc (full)

**Następna akcja:** Test minimalnej konfiguracji! 🚀
