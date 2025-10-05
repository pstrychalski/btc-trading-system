# 🏗️ Architektura Systemu - Zaawansowany Trading Bot BTC

**Wersja:** 1.0.0  
**Data:** 2025-10-05  
**Status:** Design Complete, Implementation in Progress

---

## 📋 Spis Treści

1. [Przegląd Systemu](#przegląd-systemu)
2. [Architektura Warstwowa](#architektura-warstwowa)
3. [Komponenty Systemu](#komponenty-systemu)
4. [Data Flow](#data-flow)
5. [Technologie](#technologie)
6. [Deployment](#deployment)
7. [Skalowanie](#skalowanie)
8. [Security](#security)

---

## 🎯 Przegląd Systemu

### Cel

Zaawansowany system tradingowy wykorzystujący:
- **Machine Learning** (supervised + reinforcement learning)
- **Vector Memory** (Qdrant) dla pattern recognition
- **Real-time Processing** (Pathway) dla low-latency decisions
- **Advanced Backtesting** (walk-forward optimization)
- **Stress Testing** (agent-based simulation)

### Kluczowe Cechy

✅ **Real-time Processing:** <100ms latency od market data do trading decision  
✅ **Historical Memory:** Pattern recognition z 100k+ historical situations  
✅ **Multi-Strategy:** Ensemble of strategies z automatic regime detection  
✅ **Risk-Aware:** Memory-based risk scoring i anomaly detection  
✅ **Self-Learning:** Reinforcement learning agent continuously improving  
✅ **Production-Ready:** Full monitoring, alerting, disaster recovery

---

## 🏛️ Architektura Warstwowa

```
┌─────────────────────────────────────────────────────────────────┐
│                   7. MONITORING LAYER                            │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │   Grafana    │  │  Prometheus  │  │  MLflow Tracking   │   │
│  └──────────────┘  └──────────────┘  └────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────────┐
│                   6. EXECUTION LAYER                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                      Freqtrade                            │  │
│  │  • Order execution                                        │  │
│  │  • Position management                                    │  │
│  │  • Risk management                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────────┐
│                   5. VALIDATION LAYER                            │
│  ┌────────────────────┐  ┌───────────────────────────────────┐ │
│  │ Backtrader Engine  │  │   Mesa Simulation                 │ │
│  │ • Backtesting      │  │   • Agent-based modeling          │ │
│  │ • Walk-forward opt │  │   • Stress testing                │ │
│  └────────────────────┘  └───────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────────┐
│                   4. STRATEGY LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ Trend Follow │  │ Mean Revert  │  │  Regime Detection    │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────────┐
│                   3. INTELLIGENCE LAYER                          │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                   Qdrant Vector DB                         │ │
│  │  ┌─────────────────────────────────────────────────────┐  │ │
│  │  │        Market Memory System                         │  │ │
│  │  │  • Pattern recognition                              │  │ │
│  │  │  • Similarity search                                │  │ │
│  │  │  • Risk scoring                                     │  │ │
│  │  │  • Anomaly detection                                │  │ │
│  │  └─────────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────────┘ │
│  ┌──────────────────┐  ┌─────────────────────────────────────┐ │
│  │   FreqAI (ML)    │  │   Ray/RLlib (RL Agent)              │ │
│  │   Supervised     │  │   Reinforcement Learning            │ │
│  └──────────────────┘  └─────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────────┐
│                   2. PROCESSING LAYER                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Pathway                                │  │
│  │  • Real-time stream processing                           │  │
│  │  • Feature engineering                                   │  │
│  │  • Signal generation                                     │  │
│  │  • Memory enhancement                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────────┐
│                   1. DATA LAYER                                  │
│  ┌────────────────────┐  ┌────────────────────────────────────┐│
│  │  Data Collector    │  │   Great Expectations               ││
│  │  • WebSocket       │→ │   • Schema validation              ││
│  │  • REST API        │  │   • Anomaly detection              ││
│  │  • Normalization   │  │   • Data quality monitoring        ││
│  └────────────────────┘  └────────────────────────────────────┘│
│  ┌──────────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │   PostgreSQL     │  │    Redis     │  │   Qdrant        │  │
│  │   (Historical)   │  │   (Stream)   │  │   (Vectors)     │  │
│  └──────────────────┘  └──────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Komponenty Systemu

### 1. DATA LAYER

#### 1.1 Data Collector
**Responsibility:** Collect real-time market data from exchanges

**Features:**
- WebSocket connections (Binance, Coinbase, etc.)
- REST API fallback
- Data normalization
- Automatic reconnection
- Multi-exchange support

**Technology:** Python + `ccxt` + `websockets`

**Output:** Structured market data → Redis streams

**Metrics:**
- Latency: <50ms from exchange
- Uptime: >99.9%
- Data loss: <0.1%

#### 1.2 Great Expectations (Data Validation)
**Responsibility:** Ensure data quality

**Validations:**
- Price: 0 < price < 1M, no nulls, reasonable changes (<50%)
- Volume: non-negative, outlier detection
- Timestamp: unique, chronological, no gaps >5s
- Orderbook: balanced (-1 < imbalance < 1)
- Indicators: within valid ranges

**Actions on Failure:**
- Log to PostgreSQL
- Alert via Prometheus
- Block invalid data
- Trigger manual review

#### 1.3 Databases

**PostgreSQL:**
- Historical OHLCV data
- Trade history
- Backtest results
- MLflow experiment data
- System logs

**Redis:**
- Real-time message broker
- Feature cache
- Session storage
- Rate limiting counters

**Qdrant:**
- Market state vectors (128-dim)
- Historical patterns
- Similarity search index

---

### 2. PROCESSING LAYER

#### 2.1 Pathway - Real-time Stream Processing
**Responsibility:** Transform raw data → actionable signals

**Pipeline:**
```
Redis Stream → Feature Engineering → ML Predictions → 
Memory Enhancement → Signal Generation → Output
```

**Features:**
- <100ms end-to-end latency
- Stateful processing (windowed aggregations)
- Fault tolerance (exactly-once semantics)
- Dynamic feature engineering

**Key Features Generated:**
- Technical indicators (50+)
- Price patterns
- Volume profile
- Sentiment score
- Market microstructure
- Time encoding

**Output:** Enhanced signals → Freqtrade

---

### 3. INTELLIGENCE LAYER

#### 3.1 Qdrant + Market Memory System

**Core Concept:** "Have we seen this market situation before?"

**Market State Embedding (128-dim vector):**
```python
[
  # Price features (3)
  price_change_1h, price_change_24h, volume_surge,
  
  # Technical indicators (5)
  rsi, macd, adx, bb_width, atr,
  
  # Market microstructure (2)
  sentiment, orderbook_imbalance,
  
  # Time features (4)
  hour_sin, hour_cos, day_sin, day_cos,
  
  # Trend features (3)
  ema_cross, trend_strength, volatility,
  
  # ... padded to 128 dims
]
```

**Functionality:**

1. **Risk Analysis:**
   - Find 20 most similar historical situations
   - Calculate win rate, avg profit, drawdown
   - Weight by similarity
   - Output: risk_score (0-1), recommendation

2. **Anomaly Detection:**
   - Compare current state to all historical
   - If similarity < 0.7 → anomaly
   - Warn of unprecedented situations

3. **Strategy Recommendation:**
   - Which strategy worked best in similar regimes?
   - Output: best_strategy, confidence, win_rate

**Performance:**
- Search latency: <50ms
- Storage: 100k+ vectors
- Accuracy: TBD (will measure in production)

#### 3.2 FreqAI (Supervised Learning)

**Models:**
- XGBoost (primary)
- LightGBM (secondary)
- CatBoost (for categorical features)

**Training:**
- Rolling window: 30 days
- Retrain: every 24h
- Features: 100+ technical + market microstructure
- Target: next_candle_profit (classification or regression)

**Integration:**
- Predictions fed to Pathway
- All experiments logged to MLflow
- Model versioning + A/B testing

#### 3.3 Ray/RLlib (Reinforcement Learning)

**Environment:**
- State: 50-dim (market + memory features)
- Action: [buy/sell/hold, position_size]
- Reward: profit - risk_penalty - drawdown_penalty

**Algorithm:** PPO (Proximal Policy Optimization)
- Distributed: 4 workers
- Batch size: 4000
- Learning rate: 0.0001
- Training time: ~24-48h

**Advantage over Supervised:**
- Learns from own mistakes
- Adapts to changing market
- Multi-objective optimization (profit + risk)

---

### 4. STRATEGY LAYER

#### 4.1 Multiple Strategies

**Trend Following:**
- EMA crossovers (9/21, 21/50)
- ADX > 25
- Volume confirmation
- Best in: trending markets

**Mean Reversion:**
- RSI overbought/oversold
- Bollinger Band touches
- Volume spike
- Best in: ranging markets

**Breakout:**
- Support/resistance breaks
- Volume surge
- Pattern recognition
- Best in: volatile markets

**Memory-Enhanced:**
- All above + Qdrant validation
- Risk score < 0.5 required
- Anomaly block
- Best in: all markets (safest)

#### 4.2 Regime Detection

**Market Regimes:**
1. **Trending Up:** ADX > 25, price > EMA50, positive momentum
2. **Trending Down:** ADX > 25, price < EMA50, negative momentum
3. **Ranging:** ADX < 20, low volatility
4. **Volatile:** High ATR, large price swings
5. **Crisis:** Extreme volume, >10% moves

**Strategy Selection:**
- Trending → Trend Following
- Ranging → Mean Reversion
- Volatile → Breakout
- Crisis → CLOSE ALL POSITIONS

---

### 5. VALIDATION LAYER

#### 5.1 Backtrader Engine

**Advanced Backtesting:**
- Multi-timeframe (1m, 5m, 1h, 1d)
- Realistic commission (0.1%)
- Slippage modeling (0.05%)
- Portfolio-level (multiple pairs)
- Market impact simulation

**Analyzers:**
- Sharpe ratio
- Sortino ratio
- Max drawdown
- Win rate
- Profit factor
- Recovery time
- Risk-adjusted returns

**Walk-Forward Optimization:**
```
Train: Month 1-6 → Test: Month 7
Train: Month 2-7 → Test: Month 8
...
Train: Month 6-11 → Test: Month 12
```
Average performance = robust estimate

#### 5.2 Mesa Market Simulation

**Agent Types:**

1. **Your Bot:** Strategy under test
2. **Market Makers:** Provide liquidity, adjust spread
3. **Noise Traders:** Random trades, add volatility
4. **Manipulators:** Pump & dump, spoofing

**Scenarios:**

1. **Normal Market:** 70% noise, 20% MM, 10% your bot
2. **Crash:** Sudden -30% price drop
3. **Pump & Dump:** Manipulator pumps +50%, dumps -60%
4. **Flash Crash:** -20% in 10 minutes, recover in 1h
5. **High Volatility:** 3x normal ATR

**Success Criteria:**
- Survive all scenarios
- Max drawdown < 15%
- No blown accounts

---

### 6. EXECUTION LAYER

#### 6.1 Freqtrade

**Configuration:**
- Dry-run mode initially (paper trading)
- Max open trades: 3
- Stake amount: 10% per trade
- Stop loss: -3%
- Trailing stop: enabled
- ROI: 5% target

**Strategy:**
```python
class MemoryEnhancedStrategy(IStrategy):
    def populate_indicators(self, dataframe, metadata):
        # Standard indicators
        dataframe['rsi'] = ta.RSI(dataframe)
        
        # Get memory analysis
        memory = self.query_memory_api(dataframe)
        dataframe['memory_risk'] = memory['risk_score']
        dataframe['memory_confidence'] = memory['confidence']
        
        return dataframe
    
    def populate_entry_trend(self, dataframe, metadata):
        dataframe.loc[
            (dataframe['rsi'] < 40) &           # Technical
            (dataframe['memory_risk'] < 0.5) &  # Low risk
            (dataframe['memory_confidence'] > 0.6),  # High confidence
            'enter_long'
        ] = 1
        return dataframe
```

**Risk Management:**
- Max position size: 10% of capital
- Max total exposure: 30%
- Stop loss: always active
- Daily loss limit: -5%
- Circuit breaker: -10% triggers pause

---

### 7. MONITORING LAYER

#### 7.1 Grafana Dashboards

**Dashboard 1: Trading Performance**
- Real-time P&L
- Win rate (hourly, daily, weekly)
- Open positions
- Risk exposure
- Sharpe ratio (rolling)

**Dashboard 2: Strategy Performance**
- Per-strategy metrics
- Regime detection accuracy
- Signal quality
- Entry/exit timing

**Dashboard 3: System Health**
- Service uptime
- API latency (all services)
- Error rates
- Queue depths
- Memory usage

**Dashboard 4: Data Quality**
- Validation pass rate
- Data completeness
- Anomaly count
- Drift detection

**Dashboard 5: ML Performance**
- Model accuracy (live vs backtest)
- Prediction latency
- Feature importance
- Training status

#### 7.2 Prometheus Metrics

**Custom Metrics:**
```
# Trading
trading_pnl_total
trading_trades_total
trading_win_rate
trading_open_positions

# Data
data_validation_failures_total
data_latency_seconds
data_points_processed_total

# ML
ml_prediction_latency_seconds
ml_model_accuracy
qdrant_search_latency_seconds

# System
service_health_status
api_requests_total
api_errors_total
```

**Alerts:**
- P&L drops >5% → notify immediately
- Service down >1min → page on-call
- Data quality <95% → investigate
- ML accuracy drops >10% → retrain

---

## 🔄 Data Flow - End to End

### Normal Trading Flow (Real-time)

```
1. Exchange WebSocket
   ↓ (10ms)
2. Data Collector
   ↓ (5ms)
3. Great Expectations Validation
   ↓ (10ms)
4. Redis Stream
   ↓ (5ms)
5. Pathway Processing
   ├─→ Feature Engineering (20ms)
   ├─→ ML Prediction (10ms)
   └─→ Memory Query (30ms)
   ↓ (Total: 60ms)
6. Signal Generation
   ↓ (5ms)
7. Freqtrade
   ├─→ Risk Check (5ms)
   └─→ Order Execution (20ms)
   ↓
8. Exchange Order

TOTAL LATENCY: ~120ms
```

### Backtest Flow (Offline)

```
1. Historical Data (PostgreSQL)
   ↓
2. Backtrader Engine
   ├─→ Strategy Execution
   ├─→ Performance Calculation
   └─→ Optimization (Optuna)
   ↓
3. Results → MLflow
4. Best Parameters → Production Config
```

### Training Flow (Periodic)

```
1. Historical Data + Recent Trades
   ↓
2. Feature Engineering
   ↓
3. Model Training
   ├─→ FreqAI: XGBoost/LightGBM (daily)
   └─→ RL Agent: PPO (weekly)
   ↓
4. Validation
   ↓
5. MLflow Registry
   ↓
6. A/B Testing (new vs old)
   ↓
7. Promote to Production (if better)
```

### Memory Storage Flow (Continuous)

```
1. Trade Completed
   ↓
2. Extract:
   - Entry market state
   - Trade outcome (profit, duration, drawdown)
   - Strategy used
   ↓
3. Create 128-dim embedding
   ↓
4. Store in Qdrant
   ↓
5. Future similar situations → informed by this history
```

---

## 🛠️ Technologie

### Languages
- **Python 3.10+:** Primary language
- **SQL:** PostgreSQL queries
- **YAML/TOML:** Configuration

### Frameworks
- **Pathway:** Real-time stream processing
- **Ray/RLlib:** Distributed RL
- **Backtrader:** Backtesting
- **Freqtrade:** Trading execution
- **FastAPI:** REST APIs
- **Mesa:** Agent-based simulation

### Databases
- **PostgreSQL 16:** Relational data
- **Redis 7:** Caching & streams
- **Qdrant:** Vector database

### ML/AI
- **XGBoost, LightGBM, CatBoost:** Supervised learning
- **PyTorch:** Deep learning (RL)
- **scikit-learn:** Preprocessing, metrics
- **MLflow:** Experiment tracking

### DevOps
- **Docker:** Containerization
- **Docker Compose:** Local orchestration
- **Railway.app:** Production deployment
- **Prometheus:** Metrics
- **Grafana:** Visualization
- **GitHub Actions:** CI/CD (future)

### Data Quality
- **Great Expectations:** Data validation
- **Pydantic:** Schema validation

---

## 🚀 Deployment

### Local Development

```bash
# Start all services
docker-compose up -d

# Check health
docker-compose ps

# View logs
docker-compose logs -f pathway

# Stop
docker-compose down
```

### Railway Production

```bash
# Initialize Railway
railway init

# Deploy service by service
railway up --service postgres
railway up --service redis
railway up --service qdrant
railway up --service mlflow
railway up --service data-collector
railway up --service pathway
railway up --service market-memory
railway up --service freqtrade

# Check status
railway status
```

### Environment Variables

**Required:**
- `POSTGRES_PASSWORD`
- `EXCHANGE_API_KEY`
- `EXCHANGE_API_SECRET`
- `GRAFANA_PASSWORD`

**Optional:**
- `REDIS_URL` (auto-configured locally)
- `QDRANT_URL` (auto-configured locally)
- `MLFLOW_TRACKING_URI` (auto-configured locally)

---

## 📈 Skalowanie

### Horizontal Scaling

**Can scale:**
- Data collectors (multiple exchange streams)
- Pathway workers (partitioned by symbol)
- RL training workers (Ray cluster)
- API servers (load balanced)

**Cannot easily scale:**
- Qdrant (single instance, but can use cluster)
- PostgreSQL (read replicas possible)
- Freqtrade (one instance per account)

### Vertical Scaling Needs

**High CPU:**
- RL training: 2-4 vCPU
- Backtesting: 1-2 vCPU

**High Memory:**
- Qdrant: 1-2GB (depends on vector count)
- Ray: 2-4GB during training
- Pathway: 512MB-1GB

**High I/O:**
- PostgreSQL: SSD required
- Redis: In-memory

### Performance Targets

- **Data ingestion:** 1000 msg/s
- **Pathway processing:** 500 msg/s
- **Qdrant queries:** 100 qps
- **Freqtrade:** 10 orders/minute
- **Total system:** Handle 1M data points/day

---

## 🔒 Security

### Data Protection

- **Secrets:** Environment variables (Railway secrets)
- **API Keys:** Encrypted at rest
- **Database:** Strong passwords, network isolation
- **Logs:** No sensitive data logged

### Network Security

- **Internal:** Services communicate within private network
- **External:** Only necessary ports exposed
- **TLS:** All external communication encrypted
- **Rate Limiting:** Prevent abuse

### Access Control

- **Grafana:** Admin login required
- **MLflow:** Internal network only
- **APIs:** API key authentication
- **Database:** Role-based access

### Disaster Recovery

- **Backups:** Daily PostgreSQL dumps
- **Qdrant:** Weekly snapshots
- **MLflow artifacts:** S3/object storage
- **Config:** Git version control

**RTO (Recovery Time Objective):** <1 hour  
**RPO (Recovery Point Objective):** <1 day

---

## 📊 Monitoring & Alerting

### Health Checks

All services expose `/health` endpoint:
- 200 OK: Service healthy
- 503 Service Unavailable: Degraded
- Checks: DB connections, memory, disk

### Alerts (Prometheus)

**Critical (Page immediately):**
- Service down >1min
- P&L drop >10%
- Data loss detected

**High (Notify in 5min):**
- Service degraded >5min
- P&L drop >5%
- ML accuracy drop >10%
- Data quality <95%

**Medium (Notify in 30min):**
- High latency (>500ms)
- Error rate >1%
- Memory >80%

**Low (Daily digest):**
- Minor errors
- Performance degradation
- Data drift detected

---

## 🎯 Success Metrics

### System Performance
- **Uptime:** >99% (target: 99.9%)
- **Latency:** <100ms 95th percentile
- **Data Quality:** >99% validation pass rate

### Trading Performance
- **Sharpe Ratio:** >1.5
- **Win Rate:** >55%
- **Max Drawdown:** <15%
- **Recovery Time:** <7 days
- **Annual Return:** >20% (target, not guaranteed)

### ML Performance
- **Prediction Accuracy:** >60%
- **RL vs Baseline:** +10% improvement
- **Memory Search Accuracy:** TBD (measure in production)

---

## 📚 References

- Pathway Documentation: https://pathway.com
- Qdrant Documentation: https://qdrant.tech
- MLflow Documentation: https://mlflow.org
- Freqtrade Documentation: https://www.freqtrade.io
- Ray RLlib: https://docs.ray.io/en/latest/rllib

---

**Document Version:** 1.0.0  
**Last Updated:** 2025-10-05  
**Next Review:** After each major phase completion

