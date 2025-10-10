# 🔑 DigitalOcean Token Setup - Krok po Kroku

**Data:** 2025-10-06  
**Cel:** Pobranie i konfiguracja DigitalOcean API token  
**Status:** W trakcie

---

## 🎯 **KROK 1: Pobierz DigitalOcean Token**

### **1.1 Otwórz DigitalOcean Dashboard**
```bash
# Otwórz w przeglądarce
open https://cloud.digitalocean.com/account/api/tokens
```

### **1.2 Stwórz Nowy Token**
1. **Kliknij "Generate New Token"**
2. **Nazwa:** `btc-trading-system`
3. **Scopes:** Wybierz "Full Access" (lub minimum: Apps, Databases, Droplets)
4. **Kliknij "Generate Token"**
5. **Skopiuj token** (będzie widoczny tylko raz!)

### **1.3 Zapisz Token**
```bash
# Zapisz token w bezpiecznym miejscu
echo "Twój DigitalOcean token: [WSTAW_TUTAJ_TOKEN]"
```

---

## 🔧 **KROK 2: Configure doctl**

### **2.1 Sprawdź czy doctl działa**
```bash
# Sprawdź wersję
doctl version

# Sprawdź czy jest skonfigurowany
doctl account get
```

### **2.2 Configure Authentication**
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

## 🚀 **KROK 3: Test Authentication**

### **3.1 Sprawdź Account Info**
```bash
# Sprawdź informacje o koncie
doctl account get

# Sprawdź dostępne regiony
doctl apps list-regions

# Sprawdź dostępne instance sizes
doctl apps list-instance-sizes
```

### **3.2 Test App Creation (Dry Run)**
```bash
# Sprawdź czy app-minimal.yaml jest poprawny
doctl apps create --spec app-minimal.yaml --format ID,Spec.Name
```

---

## 📊 **KROK 4: Deploy Minimal Test**

### **4.1 Deploy App**
```bash
# Deploy minimalnej aplikacji
doctl apps create --spec app-minimal.yaml

# Sprawdź status
doctl apps list
```

### **4.2 Monitor Deploy**
```bash
# Pobierz App ID
APP_ID=$(doctl apps list --format ID,Name --no-header | grep "btc-trading-system-minimal" | awk '{print $1}')

# Sprawdź status
doctl apps get $APP_ID

# Sprawdź logi
doctl apps logs $APP_ID --follow
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

**2. Token Expired**
```bash
# Stwórz nowy token w DigitalOcean Dashboard
# Configure ponownie
doctl auth init --access-token "new_token"
```

**3. Permission Denied**
```bash
# Sprawdź czy token ma odpowiednie uprawnienia
# Potrzebne: Apps, Databases, Droplets
```

---

## 📈 **SUCCESS CRITERIA**

### **✅ Checklist**
- [ ] DigitalOcean token pobrany
- [ ] doctl skonfigurowany
- [ ] Authentication działa
- [ ] App deployed successfully
- [ ] Wszystkie 3 serwisy działają
- [ ] Health checks przechodzą

### **📊 Expected Results**
- **Authentication:** ✅ Success
- **Deployment time:** ~5-10 minut
- **Cost:** ~$15/miesiąc
- **Services:** 3 działające

---

## 🎯 **NEXT STEPS**

### **Po sukcesie minimal test:**
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

## 🎯 **STATUS**

**Token Setup:** 🔑 **IN PROGRESS**  
**Minimal Test:** ⏳ **PENDING**  
**Full Deployment:** ⏳ **PENDING**

**Następna akcja:** Pobierz token i skonfiguruj doctl! 🚀
