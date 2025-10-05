#!/bin/bash
# Prosty deployment - projekt już utworzony przez API!

set -e

GREEN='\033[0;32m'
NC='\033[0m'

echo "🚀 Deployment do Railway - btc-trading-system"
echo ""

# Link do projektu
echo -e "${GREEN}1. Linkowanie projektu...${NC}"
railway link 6a8d4034-fd86-4c47-8330-a6a21063f4be

# Dodaj bazy danych
echo -e "${GREEN}2. Dodawanie PostgreSQL...${NC}"
railway add -d postgresql || echo "PostgreSQL może już istnieć"

echo -e "${GREEN}3. Dodawanie Redis...${NC}"
railway add -d redis || echo "Redis może już istnieć"

# Poczekaj na deployment baz
echo -e "${GREEN}4. Oczekiwanie na deployment baz (30s)...${NC}"
sleep 30

# Deploy serwis
echo -e "${GREEN}5. Deploying Data Validation Service...${NC}"
cd services/data-validation
railway up --detach
cd ../..

# Zmienne środowiskowe
echo -e "${GREEN}6. Ustawianie zmiennych...${NC}"
railway variables set ENVIRONMENT=production
railway variables set LOG_LEVEL=INFO
railway variables set VALIDATION_MAX_PRICE_CHANGE=50.0
railway variables set VALIDATION_STORE_FAILURES=true

# Status
echo ""
echo -e "${GREEN}✅ DEPLOYMENT ZAKOŃCZONY!${NC}"
echo ""
railway status
echo ""
echo "🌐 Dashboard: https://railway.app/project/6a8d4034-fd86-4c47-8330-a6a21063f4be"
echo ""
echo "📝 Sprawdź URL serwisu:"
echo "   railway domain"

