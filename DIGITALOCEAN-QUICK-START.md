# 🚀 DigitalOcean Quick Start - Minimal Test

**Data:** 2025-10-06  
**Cel:** Szybki test DigitalOcean z minimalnymi parametrami  
**Status:** Gotowe do testu

---

## 🎯 **MINIMAL TEST SETUP**

### **Serwisy do Testu (3)**
1. **data-validation** (basic-xxs) - $5/miesiąc
2. **mlflow-tracking** (basic-xxs) - $5/miesiąc  
3. **data-collector** (basic-xxs) - $5/miesiąc

**Total Cost:** ~$15/miesiąc (vs $170/miesiąc full)

---

## 🔧 **KROK 1: DigitalOcean Authentication**

### **1.1 Pobierz API Token**
```bash
# Idź do: https://cloud.digitalocean.com/account/api/tokens
# Stwórz nowy token z pełnymi uprawnieniami
# Skopiuj token
```

### **1.2 Configure doctl**
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

## 🚀 **KROK 2: Test Deploy**

### **2.1 Sprawdź Konfigurację**
```bash
# Sprawdź czy plik istnieje
ls -la app-minimal.yaml

# Sprawdź składnię (bez dry-run, bo nie ma takiej opcji)
doctl apps create --spec app-minimal.yaml --format ID,Spec.Name
```

### **2.2 Deploy Minimal App**
```bash
# Deploy minimalnej aplikacji
doctl apps create --spec app-minimal.yaml

# Sprawdź status
doctl apps list
```

### **2.3 Monitor Deploy**
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

### **3.1 Sprawdź Serwisy**
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

## 🔧 **TROUBLESHOOTING**

### **Common Issues**

**1. Authentication Error**
```bash
# Sprawdź token
doctl account get

# Re-authenticate
doctl auth init --access-token "your_token"
```

**2. Service Health Check Failed**
```bash
# Sprawdź logi konkretnego serwisu
doctl apps logs $APP_ID --component data-validation --follow

# Restart serwis
doctl apps update $APP_ID --spec app-minimal.yaml --force-rebuild
```

**3. Build Error**
```bash
# Sprawdź build logs
doctl apps logs $APP_ID --component data-validation --follow

# Sprawdź czy source_dir istnieje
ls -la services/data-validation/
```

---

## 📈 **SUCCESS CRITERIA**

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

## 🚀 **NEXT STEPS**

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

# 2. Deploy
doctl apps create --spec app-minimal.yaml

# 3. Monitor
doctl apps list
doctl apps get $APP_ID
doctl apps logs $APP_ID --follow

# 4. Test endpoints
curl https://your-app-url/data-validation/health
curl https://your-app-url/mlflow-tracking/health
curl https://your-app-url/data-collector/health
```

---

## 🎯 **STATUS**

**Minimal Test:** 🧪 **READY TO TEST**  
**Full Deployment:** ⏳ **PENDING**  
**Cost:** $15/miesiąc (minimal) vs $170/miesiąc (full)

**Następna akcja:** 
1. **Pobierz DigitalOcean token**
2. **Configure doctl**
3. **Deploy minimal test**

**Gotowy do testu!** 🚀
