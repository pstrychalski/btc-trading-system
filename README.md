# 🤖 Zaawansowany System Tradingowy BTC

**Status:** 🚀 W trakcie implementacji  
**Wersja:** 1.0.0-alpha  
**Data:** 2025-10-05

Kompleksowy system tradingowy wykorzystujący Machine Learning, Vector Memory, Reinforcement Learning i Advanced Backtesting dla automatycznego tradingu kryptowalut.

---

## 🎯 Kluczowe Cechy

✅ **Real-time Processing** - Pathway stream processing (<100ms latency)  
✅ **Historical Memory** - Qdrant vector DB z pattern recognition  
✅ **Machine Learning** - FreqAI (supervised) + Ray/RLlib (reinforcement)  
✅ **Advanced Backtesting** - Backtrader z walk-forward optimization  
✅ **Stress Testing** - Mesa agent-based market simulation  
✅ **Data Quality** - Great Expectations validation  
✅ **Full Monitoring** - Grafana + Prometheus + MLflow  
✅ **Production Ready** - Railway deployment, auto-scaling

---

## 📊 Architektura

System składa się z 7 warstw:

```
Monitoring → Execution → Validation → Strategy → 
Intelligence → Processing → Data
```

Szczegółowa dokumentacja: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.10+
- Railway CLI (opcjonalnie, dla cloud deployment)

### Instalacja Lokalna

```bash
# 1. Clone repository
git clone <repo-url>
cd btc

# 2. Utwórz plik .env
cp env.example .env
# Edytuj .env i dodaj API keys

# 3. Start wszystkich serwisów
docker-compose up -d

# 4. Sprawdź status
docker-compose ps

# 5. Dostęp do dashboardów
# Grafana:     http://localhost:3000 (admin/admin123)
# MLflow:      http://localhost:5000
# Freqtrade:   http://localhost:8080
# Prometheus:  http://localhost:9090
```

### Pierwszy Backtest

```bash
# Uruchom backtest na przykładowej strategii
docker-compose exec backtest-engine python run_backtest.py \
  --strategy TrendFollowing \
  --pair BTC/USDT \
  --start-date 2023-01-01 \
  --end-date 2024-01-01

# Wyniki w MLflow: http://localhost:5000
```

---

## 📁 Struktura Projektu

```
btc/
├── services/               # Wszystkie mikroserwisy
│   ├── data-collector/    # WebSocket collectors
│   ├── data-validation/   # Great Expectations
│   ├── pathway/           # Real-time processing
│   ├── qdrant/            # Vector database
│   ├── market-memory/     # Pattern recognition
│   ├── mlflow/            # Experiment tracking
│   ├── backtest-engine/   # Backtesting framework
│   ├── market-sim/        # Agent-based simulation
│   ├── rl-agent/          # Reinforcement learning
│   ├── freqtrade/         # Trading execution
│   └── monitoring/        # Grafana dashboards
├── docs/                  # Dokumentacja
│   └── ARCHITECTURE.md    # Architektura systemu
├── docker-compose.yml     # Local development
├── railway.toml           # Production deployment
├── requirements.txt       # Python dependencies
├── ROADMAP.md            # 3-month implementation plan
└── README.md             # Ten plik
```

---

## 🗺️ Roadmap

### ✅ Faza 0: Setup Infrastruktury (Tydzień 0)
- [x] Struktura projektu
- [x] Docker Compose configuration
- [x] Railway deployment config

### 🔄 Faza 1: Data Validation + MLflow (Tydzień 1-2)
- [ ] Great Expectations setup
- [ ] WebSocket data collector
- [ ] MLflow experiment tracking

### ⏳ Faza 2: Advanced Backtesting (Tydzień 3-4)
- [ ] Backtrader engine
- [ ] Walk-forward optimization
- [ ] Strategy templates

### ⏳ Faza 3: Market Memory + Simulation (Tydzień 5-8)
- [ ] Qdrant vector database
- [ ] Market Memory system
- [ ] Mesa market simulation
- [ ] Pathway integration

### ⏳ Faza 4: RL + Full Integration (Tydzień 9-12)
- [ ] Ray/RLlib setup
- [ ] Trading environment
- [ ] RL agent training
- [ ] Freqtrade integration
- [ ] Complete pipeline

### ⏳ Faza 5: Production Deployment (Tydzień 13-16)
- [ ] Production hardening
- [ ] Railway deployment
- [ ] Performance optimization
- [ ] Paper trading
- [ ] Go live

Szczegółowy roadmap: [`ROADMAP.md`](ROADMAP.md)

---

## 🛠️ Technologie

### Core Frameworks
- **Pathway** - Real-time stream processing
- **Qdrant** - Vector database
- **MLflow** - Experiment tracking
- **Backtrader** - Advanced backtesting
- **Ray/RLlib** - Reinforcement learning
- **Freqtrade** - Trading execution

### Data & ML
- **Great Expectations** - Data validation
- **XGBoost/LightGBM** - Supervised learning
- **PyTorch** - Deep learning
- **Mesa** - Agent-based simulation

### Infrastructure
- **PostgreSQL** - Relational database
- **Redis** - Message broker & cache
- **Prometheus** - Metrics
- **Grafana** - Dashboards
- **Docker** - Containerization
- **Railway.app** - Cloud hosting

---

## 📈 Success Metrics

### System Performance
- Uptime: >99%
- Latency: <100ms (95th percentile)
- Data Quality: >99% validation pass rate

### Trading Performance (Target)
- Sharpe Ratio: >1.5
- Win Rate: >55%
- Max Drawdown: <15%
- Annual Return: >20%

---

## 🔧 Development

### Uruchomienie Pojedynczego Serwisu

```bash
# Data collector
docker-compose up data-collector

# Pathway processing
docker-compose up pathway

# Freqtrade (dry-run)
docker-compose up freqtrade
```

### Testy

```bash
# Unit tests
pytest services/data-validation/tests/

# Integration tests
pytest tests/integration/

# Backtests
python services/backtest-engine/run_backtest.py
```

### Logi

```bash
# Wszystkie serwisy
docker-compose logs -f

# Konkretny serwis
docker-compose logs -f pathway

# Real-time monitoring
docker-compose logs -f | grep ERROR
```

---

## 🚀 Production Deployment (Railway)

```bash
# 1. Install Railway CLI
npm i -g @railway/cli

# 2. Login
railway login

# 3. Initialize project
railway init

# 4. Deploy services (w kolejności)
railway up --service postgres
railway up --service redis
railway up --service qdrant
railway up --service mlflow
railway up --service data-collector
railway up --service data-validation
railway up --service pathway
railway up --service market-memory
railway up --service freqtrade

# 5. Set environment variables
railway variables set EXCHANGE_API_KEY=<your_key>
railway variables set EXCHANGE_API_SECRET=<your_secret>

# 6. Check status
railway status

# 7. View logs
railway logs --service freqtrade
```

**Estimated Monthly Cost:** $50-85

---

## 📚 Dokumentacja

- [Architektura Systemu](docs/ARCHITECTURE.md) - Szczegółowa architektura
- [Roadmap](ROADMAP.md) - Plan implementacji (3 miesiące)
- [Railway Deployment](railway-deploy.sh) - Skrypt deployment

### External Resources
- [Pathway Documentation](https://pathway.com/developers/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [Freqtrade Documentation](https://www.freqtrade.io/)
- [Railway Documentation](https://docs.railway.app/)

---

## ⚠️ Disclaimer

**Ten system jest w fazie development. NIE używaj na prawdziwych pieniądzach bez dokładnego testowania.**

Trading kryptowalut niesie wysokie ryzyko. Możesz stracić całą zainwestowaną kwotę. Ten software jest dostarczany "as is" bez żadnych gwarancji.

Zawsze:
1. Testuj na paper trading przez minimum 30 dni
2. Zaczynaj z małymi kwotami
3. Monitoruj system 24/7 przez pierwsze tygodnie
4. Miej plan awaryjny (kill switch)

---

## 🤝 Contributing

Pull requests są mile widziane. Dla większych zmian, najpierw otwórz issue.

---

## 📄 Licencja

MIT License - możesz swobodnie używać i modyfikować.

---

## 📞 Contact

W razie pytań lub problemów, otwórz issue na GitHub.

---

**Status Implementacji:** 🔄 Faza 0 Zakończona, Faza 1 W Trakcie  
**Last Updated:** 2025-10-05

