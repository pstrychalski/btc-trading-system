# 🧪 DigitalOcean Endpoints Testing

**Data:** 2025-10-10  
**Cel:** Testowanie endpoints po ustawieniu environment variables  
**Status:** Gotowe do testu

---

## 🎯 **ENDPOINTS DO TESTOWANIA:**

### **1. Data Validation Service**
```bash
# Health check
curl https://btc-trading-system-minimal-h7me6.ondigitalocean.app/data-validation/health

# Expected: {"status": "healthy", "service": "data-validation"}
```

### **2. MLflow Tracking Service**
```bash
# Health check
curl https://btc-trading-system-minimal-h7me6.ondigitalocean.app/mlflow-tracking/health

# Expected: {"status": "healthy", "service": "mlflow-tracking"}
```

### **3. Data Collector Service**
```bash
# Health check
curl https://btc-trading-system-minimal-h7me6.ondigitalocean.app/data-collector/health

# Expected: {"status": "healthy", "service": "data-collector"}
```

---

## 🔍 **TESTOWANIE KROK PO KROKU:**

### **KROK 1: Test Health Checks**
```bash
# Test all endpoints
curl -s https://btc-trading-system-minimal-h7me6.ondigitalocean.app/data-validation/health | jq
curl -s https://btc-trading-system-minimal-h7me6.ondigitalocean.app/mlflow-tracking/health | jq
curl -s https://btc-trading-system-minimal-h7me6.ondigitalocean.app/data-collector/health | jq
```

### **KROK 2: Test Database Connections**
```bash
# Sprawdź logi - powinny być bez błędów PostgreSQL/Redis
doctl apps logs 4a9a6683-cb21-46fd-a81a-e573be09f218 --type run | grep -E "(database|redis|connection)"
```

### **KROK 3: Test MLflow UI**
```bash
# Otwórz MLflow UI
open https://btc-trading-system-minimal-h7me6.ondigitalocean.app/mlflow-tracking
```

---

## 📊 **EXPECTED RESULTS:**

### ✅ **SUCCESS INDICATORS:**
- All health checks return `200 OK`
- No PostgreSQL connection errors
- No Redis connection errors
- MLflow UI accessible
- All services running

### ❌ **FAILURE INDICATORS:**
- Health checks return `500` or timeout
- PostgreSQL connection refused
- Redis connection refused
- MLflow UI not accessible

---

## 🚀 **QUICK TEST SCRIPT:**

```bash
#!/bin/bash
echo "🧪 Testing DigitalOcean Endpoints..."

echo "1. Data Validation Health:"
curl -s https://btc-trading-system-minimal-h7me6.ondigitalocean.app/data-validation/health

echo -e "\n2. MLflow Tracking Health:"
curl -s https://btc-trading-system-minimal-h7me6.ondigitalocean.app/mlflow-tracking/health

echo -e "\n3. Data Collector Health:"
curl -s https://btc-trading-system-minimal-h7me6.ondigitalocean.app/data-collector/health

echo -e "\n✅ Testing complete!"
```

---

## 📋 **CHECKLIST:**

- [ ] Environment variables ustawione w Dashboard
- [ ] App zrestartowany po zmianach
- [ ] Data Validation health check OK
- [ ] MLflow Tracking health check OK  
- [ ] Data Collector health check OK
- [ ] MLflow UI accessible
- [ ] No database connection errors
- [ ] All services running

**STATUS: Gotowe do testowania!** 🚀
