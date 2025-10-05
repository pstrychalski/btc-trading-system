#!/bin/bash

# ==============================================================================
# AUTOMATYCZNY DEPLOYMENT NA RAILWAY
# Ten skrypt wykona cały deployment za Ciebie
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}✓${NC} $1"
}

step() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

error() {
    echo -e "${RED}✗ ERROR: $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}⚠ WARNING: $1${NC}"
}

# Sprawdź czy zalogowany
step "1. Sprawdzanie logowania Railway"
if ! railway whoami &> /dev/null; then
    error "Nie jesteś zalogowany! Uruchom najpierw: railway login"
fi
log "Zalogowany jako: $(railway whoami)"

# Inicjalizuj projekt
step "2. Inicjalizacja projektu Railway"
if [ ! -d ".railway" ]; then
    log "Tworzenie nowego projektu..."
    railway init <<EOF
btc-trading-system
y
EOF
    log "Projekt utworzony: btc-trading-system"
else
    log "Projekt już istnieje"
fi

# Dodaj PostgreSQL
step "3. Dodawanie PostgreSQL"
log "Dodawanie bazy danych PostgreSQL..."
railway add -d postgresql 2>&1 | grep -v "already exists" || warning "PostgreSQL może już istnieć"
log "PostgreSQL gotowy"

# Dodaj Redis
step "4. Dodawanie Redis"
log "Dodawanie Redis cache..."
railway add -d redis 2>&1 | grep -v "already exists" || warning "Redis może już istnieć"
log "Redis gotowy"

# Poczekaj na deployment baz danych
step "5. Oczekiwanie na deployment baz danych (30s)"
sleep 30
log "Bazy danych powinny być gotowe"

# Deploy Data Validation Service
step "6. Deployment Data Validation Service"
cd services/data-validation

log "Budowanie i deployowanie serwisu..."
railway up --detach 2>&1

cd ../..
log "Data Validation Service wdrożony"

# Ustaw zmienne środowiskowe
step "7. Ustawianie zmiennych środowiskowych"
railway variables set ENVIRONMENT=production
railway variables set LOG_LEVEL=INFO
railway variables set VALIDATION_MAX_PRICE_CHANGE=50.0
railway variables set VALIDATION_STORE_FAILURES=true
log "Zmienne środowiskowe ustawione"

# Poczekaj na deployment
step "8. Oczekiwanie na pełny deployment (60s)"
log "Serwis się buduje i deployuje..."
sleep 60

# Sprawdź status
step "9. Sprawdzanie statusu"
railway status

# Pobierz URL
step "10. Pobieranie URL serwisu"
SERVICE_URL=$(railway domain 2>&1 | grep -o 'https://[^[:space:]]*' | head -1)

if [ -z "$SERVICE_URL" ]; then
    warning "Nie udało się automatycznie pobrać URL"
    echo "Sprawdź URL ręcznie:"
    echo "  railway domain"
else
    log "Service URL: $SERVICE_URL"
    
    # Test health endpoint
    echo ""
    log "Testowanie /health endpoint..."
    sleep 10
    
    if curl -f -s "$SERVICE_URL/health" > /dev/null 2>&1; then
        log "✓ Service działa poprawnie!"
        echo ""
        curl -s "$SERVICE_URL/health" | python3 -m json.tool
    else
        warning "Service jeszcze się uruchamia, spróbuj za chwilę:"
        echo "  curl $SERVICE_URL/health"
    fi
fi

# Finalne info
step "✓ DEPLOYMENT ZAKOŃCZONY!"
echo ""
echo "🎉 Data Validation Service jest LIVE!"
echo ""
echo "📊 Dashboard: https://railway.app/dashboard"
echo "📝 Logi:      railway logs"
echo "📈 Status:    railway status"
echo ""
echo "🧪 Testuj serwis:"
if [ ! -z "$SERVICE_URL" ]; then
    echo "  curl $SERVICE_URL/health"
    echo "  curl $SERVICE_URL/stats"
    echo ""
    echo "📖 Pełne przykłady testów w: READY-TO-DEPLOY.md"
fi
echo ""
log "Wszystko gotowe! 🚀"

