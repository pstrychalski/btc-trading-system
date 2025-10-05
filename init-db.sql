-- ==============================================================================
-- PostgreSQL Initialization Script
-- Zaawansowany System Tradingowy BTC
-- ==============================================================================

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ==============================================================================
-- TABLES: Historical Market Data
-- ==============================================================================

CREATE TABLE IF NOT EXISTS market_data_ohlcv (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(5) NOT NULL,  -- 1m, 5m, 1h, etc.
    open NUMERIC(20, 8) NOT NULL,
    high NUMERIC(20, 8) NOT NULL,
    low NUMERIC(20, 8) NOT NULL,
    close NUMERIC(20, 8) NOT NULL,
    volume NUMERIC(20, 8) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(timestamp, symbol, timeframe)
);

CREATE INDEX idx_ohlcv_symbol_timestamp ON market_data_ohlcv(symbol, timestamp DESC);
CREATE INDEX idx_ohlcv_timeframe ON market_data_ohlcv(timeframe);

-- ==============================================================================
-- TABLES: Trade History
-- ==============================================================================

CREATE TABLE IF NOT EXISTS trades (
    id BIGSERIAL PRIMARY KEY,
    trade_id VARCHAR(100) UNIQUE NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,  -- buy, sell
    entry_price NUMERIC(20, 8) NOT NULL,
    exit_price NUMERIC(20, 8),
    amount NUMERIC(20, 8) NOT NULL,
    fee NUMERIC(20, 8),
    profit NUMERIC(20, 8),
    profit_percent NUMERIC(10, 4),
    entry_time TIMESTAMPTZ NOT NULL,
    exit_time TIMESTAMPTZ,
    duration_seconds INTEGER,
    strategy_name VARCHAR(100),
    signal_strength NUMERIC(5, 4),
    max_drawdown NUMERIC(10, 4),
    status VARCHAR(20) DEFAULT 'open',  -- open, closed, cancelled
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_entry_time ON trades(entry_time DESC);
CREATE INDEX idx_trades_strategy ON trades(strategy_name);
CREATE INDEX idx_trades_status ON trades(status);

-- ==============================================================================
-- TABLES: Data Quality (Great Expectations)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS data_validation_results (
    id BIGSERIAL PRIMARY KEY,
    run_id UUID DEFAULT uuid_generate_v4(),
    data_asset_name VARCHAR(200) NOT NULL,
    expectation_suite_name VARCHAR(200) NOT NULL,
    run_time TIMESTAMPTZ NOT NULL,
    success BOOLEAN NOT NULL,
    statistics JSONB,
    results JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_validation_data_asset ON data_validation_results(data_asset_name);
CREATE INDEX idx_validation_run_time ON data_validation_results(run_time DESC);
CREATE INDEX idx_validation_success ON data_validation_results(success);

-- ==============================================================================
-- TABLES: Strategy Performance
-- ==============================================================================

CREATE TABLE IF NOT EXISTS strategy_performance (
    id BIGSERIAL PRIMARY KEY,
    strategy_name VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    win_rate NUMERIC(5, 4),
    total_profit NUMERIC(20, 8),
    total_profit_percent NUMERIC(10, 4),
    avg_profit_per_trade NUMERIC(20, 8),
    max_profit NUMERIC(20, 8),
    max_loss NUMERIC(20, 8),
    sharpe_ratio NUMERIC(10, 4),
    sortino_ratio NUMERIC(10, 4),
    max_drawdown NUMERIC(10, 4),
    recovery_time_days NUMERIC(10, 2),
    profit_factor NUMERIC(10, 4),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_strategy_perf_name ON strategy_performance(strategy_name);
CREATE INDEX idx_strategy_perf_period ON strategy_performance(period_start DESC);

-- ==============================================================================
-- TABLES: Backtest Results
-- ==============================================================================

CREATE TABLE IF NOT EXISTS backtest_results (
    id BIGSERIAL PRIMARY KEY,
    backtest_id UUID DEFAULT uuid_generate_v4(),
    strategy_name VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(5) NOT NULL,
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    initial_capital NUMERIC(20, 8),
    final_capital NUMERIC(20, 8),
    total_return NUMERIC(10, 4),
    sharpe_ratio NUMERIC(10, 4),
    sortino_ratio NUMERIC(10, 4),
    max_drawdown NUMERIC(10, 4),
    win_rate NUMERIC(5, 4),
    profit_factor NUMERIC(10, 4),
    total_trades INTEGER,
    parameters JSONB,
    metrics JSONB,
    equity_curve JSONB,
    mlflow_run_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_backtest_strategy ON backtest_results(strategy_name);
CREATE INDEX idx_backtest_symbol ON backtest_results(symbol);
CREATE INDEX idx_backtest_sharpe ON backtest_results(sharpe_ratio DESC);

-- ==============================================================================
-- TABLES: ML Model Registry
-- ==============================================================================

CREATE TABLE IF NOT EXISTS ml_models (
    id BIGSERIAL PRIMARY KEY,
    model_id UUID DEFAULT uuid_generate_v4(),
    model_name VARCHAR(200) NOT NULL,
    model_type VARCHAR(50) NOT NULL,  -- xgboost, lightgbm, rl_agent, etc.
    version VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'training',  -- training, production, archived
    mlflow_run_id VARCHAR(100),
    mlflow_model_uri TEXT,
    training_start TIMESTAMPTZ,
    training_end TIMESTAMPTZ,
    training_metrics JSONB,
    validation_metrics JSONB,
    hyperparameters JSONB,
    feature_importance JSONB,
    promoted_to_production_at TIMESTAMPTZ,
    archived_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ml_models_name ON ml_models(model_name);
CREATE INDEX idx_ml_models_status ON ml_models(status);
CREATE INDEX idx_ml_models_type ON ml_models(model_type);

-- ==============================================================================
-- TABLES: Market Memory (Qdrant metadata)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS market_memory_states (
    id BIGSERIAL PRIMARY KEY,
    state_id VARCHAR(100) UNIQUE NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    market_data JSONB NOT NULL,
    trade_outcome JSONB,
    strategy_used VARCHAR(100),
    qdrant_point_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_memory_symbol ON market_memory_states(symbol);
CREATE INDEX idx_memory_timestamp ON market_memory_states(timestamp DESC);
CREATE INDEX idx_memory_strategy ON market_memory_states(strategy_used);

-- ==============================================================================
-- TABLES: System Logs
-- ==============================================================================

CREATE TABLE IF NOT EXISTS system_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    level VARCHAR(20) NOT NULL,  -- DEBUG, INFO, WARNING, ERROR, CRITICAL
    service_name VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    context JSONB,
    exception TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_logs_timestamp ON system_logs(timestamp DESC);
CREATE INDEX idx_logs_level ON system_logs(level);
CREATE INDEX idx_logs_service ON system_logs(service_name);

-- ==============================================================================
-- TABLES: Alerts & Notifications
-- ==============================================================================

CREATE TABLE IF NOT EXISTS alerts (
    id BIGSERIAL PRIMARY KEY,
    alert_id UUID DEFAULT uuid_generate_v4(),
    alert_type VARCHAR(50) NOT NULL,  -- risk, performance, system, data_quality
    severity VARCHAR(20) NOT NULL,  -- low, medium, high, critical
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    source_service VARCHAR(100),
    metadata JSONB,
    status VARCHAR(20) DEFAULT 'active',  -- active, acknowledged, resolved
    triggered_at TIMESTAMPTZ DEFAULT NOW(),
    acknowledged_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_alerts_type ON alerts(alert_type);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_triggered ON alerts(triggered_at DESC);

-- ==============================================================================
-- VIEWS: Trading Statistics
-- ==============================================================================

CREATE OR REPLACE VIEW daily_trading_stats AS
SELECT 
    DATE(entry_time) as trade_date,
    symbol,
    strategy_name,
    COUNT(*) as total_trades,
    SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as winning_trades,
    SUM(CASE WHEN profit <= 0 THEN 1 ELSE 0 END) as losing_trades,
    ROUND(AVG(CASE WHEN profit > 0 THEN 1.0 ELSE 0.0 END)::NUMERIC, 4) as win_rate,
    SUM(profit) as total_profit,
    ROUND(AVG(profit)::NUMERIC, 8) as avg_profit,
    MAX(profit) as max_profit,
    MIN(profit) as max_loss,
    ROUND(AVG(duration_seconds)::NUMERIC / 60, 2) as avg_duration_minutes
FROM trades
WHERE status = 'closed'
GROUP BY DATE(entry_time), symbol, strategy_name
ORDER BY trade_date DESC;

-- ==============================================================================
-- FUNCTIONS: Update Timestamp
-- ==============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- TRIGGERS
-- ==============================================================================

CREATE TRIGGER update_trades_updated_at
    BEFORE UPDATE ON trades
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ml_models_updated_at
    BEFORE UPDATE ON ml_models
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ==============================================================================
-- INITIAL DATA
-- ==============================================================================

-- Insert initial system log
INSERT INTO system_logs (level, service_name, message, context)
VALUES ('INFO', 'postgres', 'Database initialized successfully', '{"version": "1.0.0"}');

-- ==============================================================================
-- GRANTS (dla trading_user)
-- ==============================================================================

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trading_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO trading_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO trading_user;

-- ==============================================================================
-- COMPLETED
-- ==============================================================================

SELECT 'Database initialization completed successfully!' AS status;

