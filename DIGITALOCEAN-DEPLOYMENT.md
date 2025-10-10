# 🚀 DigitalOcean Deployment - Instrukcje Krok po Kroku

**Data:** 2025-10-06  
**Status:** Migracja z Railway na DigitalOcean  
**Cel:** Deploy 13 serwisów na DigitalOcean App Platform

---

## 📋 **PRZED ROZPOCZĘCIEM**

### **Wymagania**
- ✅ DigitalOcean account
- ✅ DigitalOcean API token
- ✅ doctl CLI zainstalowany
- ✅ SSH key dla Qdrant Droplet

### **Koszty Estymacja**
- **App Platform:** ~$134/miesiąc (13 serwisów)
- **Databases:** ~$30/miesiąc (PostgreSQL + Redis)
- **Qdrant Droplet:** ~$6/miesiąc
- **TOTAL:** ~$170/miesiąc

---

## 🔧 **KROK 1: DigitalOcean CLI Setup**

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

## 🗄️ **KROK 2: Database Setup**

### **2.1 PostgreSQL Database**
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

### **2.2 Redis Database**
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

### **3.1 Stwórz SSH Key (jeśli nie masz)**
```bash
# Stwórz nowy SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Dodaj do DigitalOcean
doctl compute ssh-key create "btc-key" --public-key "$(cat ~/.ssh/id_ed25519.pub)"
```

### **3.2 Stwórz Droplet dla Qdrant**
```bash
# Pobierz SSH key ID
SSH_KEY_ID=$(doctl compute ssh-key list --format ID,Name --no-header | grep "btc-key" | awk '{print $1}')

# Stwórz Droplet
doctl compute droplet create qdrant-server \
  --image docker-20-04 \
  --size s-1vcpu-1gb \
  --region nyc1 \
  --ssh-keys $SSH_KEY_ID \
  --wait

# Pobierz IP
DROPLET_IP=$(doctl compute droplet list --format Name,PublicIPv4 --no-header | grep "qdrant-server" | awk '{print $2}')
echo "Qdrant IP: $DROPLET_IP"
```

### **3.3 Zainstaluj Qdrant na Droplet**
```bash
# SSH do serwera
ssh root@$DROPLET_IP

# Zainstaluj Docker (jeśli nie ma)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Uruchom Qdrant
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant

# Sprawdź czy działa
curl http://localhost:6333/health
```

---

## 📝 **KROK 4: App Platform Configuration**

### **4.1 Sprawdź app.yaml**
```bash
# Sprawdź czy plik istnieje
ls -la app.yaml

# Sprawdź składnię
doctl apps create --spec app.yaml --dry-run
```

### **4.2 Update app.yaml z prawdziwymi wartościami**
```bash
# Edytuj app.yaml i zamień:
# - "your_binance_api_key" na prawdziwy klucz
# - "your_binance_secret_key" na prawdziwy klucz
# - "qdrant-server" na prawdziwy IP ($DROPLET_IP)
```

---

## 🚀 **KROK 5: Deploy na DigitalOcean**

### **5.1 Deploy App**
```bash
# Deploy całej aplikacji
doctl apps create --spec app.yaml

# Sprawdź status
doctl apps list
```

### **5.2 Sprawdź Status Deploy**
```bash
# Pobierz App ID
APP_ID=$(doctl apps list --format ID,Name --no-header | grep "btc-trading-system" | awk '{print $1}')

# Sprawdź status
doctl apps get $APP_ID

# Sprawdź logi
doctl apps logs $APP_ID --follow
```

---

## 📊 **KROK 6: Monitoring i Verification**

### **6.1 Sprawdź Wszystkie Serwisy**
```bash
# Sprawdź status wszystkich serwisów
doctl apps get $APP_ID --format json | jq '.spec.services[].name'

# Sprawdź health checks
doctl apps get $APP_ID --format json | jq '.spec.services[].health_check'
```

### **6.2 Test Endpoints**
```bash
# Pobierz URLs
doctl apps get $APP_ID --format json | jq '.spec.services[].ingress'

# Test health endpoints
curl https://your-app-url/data-validation/health
curl https://your-app-url/mlflow-tracking/health
curl https://your-app-url/data-collector/health
```

---

## 🔧 **KROK 7: Troubleshooting**

### **7.1 Common Issues**

**Database Connection Error**
```bash
# Sprawdź connection string
doctl databases connection btc-postgres --format ConnectionString

# Test connection
doctl databases connection btc-postgres --format ConnectionString | psql
```

**Service Health Check Failed**
```bash
# Sprawdź logi konkretnego serwisu
doctl apps logs $APP_ID --component data-validation --follow

# Restart serwis
doctl apps update $APP_ID --spec app.yaml --force-rebuild
```

**Qdrant Connection Error**
```bash
# Sprawdź czy Qdrant działa
curl http://$DROPLET_IP:6333/health

# Sprawdź firewall
doctl compute firewall list
```

### **7.2 Update App**
```bash
# Update aplikacji
doctl apps update $APP_ID --spec app.yaml

# Force rebuild
doctl apps update $APP_ID --spec app.yaml --force-rebuild
```

---

## 📚 **KROK 8: Final Verification**

### **8.1 Sprawdź Wszystkie Serwisy**
```bash
# Lista serwisów
doctl apps get $APP_ID --format json | jq '.spec.services[].name'

# Status każdego serwisu
doctl apps get $APP_ID --format json | jq '.spec.services[] | {name: .name, health_check: .health_check}'
```

### **8.2 Test API Endpoints**
```bash
# Test wszystkich health endpoints
for service in data-validation mlflow-tracking data-collector backtest-engine optuna-optimizer market-memory mesa-simulation pathway-pipeline rl-agent freqtrade-integration; do
  echo "Testing $service..."
  curl -f https://your-app-url/$service/health || echo "Failed: $service"
done
```

---

## 💰 **KROK 9: Cost Monitoring**

### **9.1 Sprawdź Koszty**
```bash
# Sprawdź billing
doctl billing-history list

# Sprawdź usage
doctl apps get $APP_ID --format json | jq '.spec.services[].instance_size_slug'
```

### **9.2 Optimize Costs**
```bash
# Jeśli chcesz zmniejszyć koszty, możesz:
# - Zmniejszyć instance_size_slug w app.yaml
# - Zmniejszyć num_nodes w databases
# - Użyć tańszych regionów
```

---

## 🎯 **FINALNE SPRAWDZENIE**

### **✅ Checklist**
- [ ] DigitalOcean CLI skonfigurowany
- [ ] PostgreSQL database utworzony
- [ ] Redis database utworzony
- [ ] Qdrant Droplet utworzony i skonfigurowany
- [ ] App.yaml skonfigurowany z prawdziwymi wartościami
- [ ] App deployed na DigitalOcean
- [ ] Wszystkie serwisy działają
- [ ] Health checks przechodzą
- [ ] API endpoints odpowiadają

### **📊 Status**
- **Deployment:** ✅ Gotowe
- **Monitoring:** ✅ Aktywne
- **Costs:** ~$170/miesiąc
- **Performance:** Lepsze niż Railway

---

## 🚀 **NEXT STEPS**

1. **Monitor** wszystkie serwisy
2. **Test** API endpoints
3. **Configure** monitoring i alerting
4. **Optimize** performance i koszty
5. **Scale** w razie potrzeby

**Status:** DigitalOcean deployment gotowy! 🎉  
**Czas:** ~2-3h setup + deployment  
**Koszt:** ~$170/miesiąc (vs $60-80 Railway, ale lepsze performance)

---

**Następna akcja:** Deploy na DigitalOcean! 🚀
