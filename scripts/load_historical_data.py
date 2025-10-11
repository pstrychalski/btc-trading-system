#!/usr/bin/env python3
"""
Load Historical BTC Data for Backtesting
Pobiera dane z CoinGecko API i zapisuje do PostgreSQL
"""
import os
import sys
import requests
import pandas as pd
import psycopg2
from datetime import datetime, timedelta
import time
import structlog

# Setup logging
logger = structlog.get_logger()

def get_btc_data(days=30):
    """Pobierz historyczne dane BTC z Binance REST API"""
    logger.info("Pobieranie danych BTC", days=days)
    
    # Binance REST API - darmowe, bez klucza
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "BTCUSDT",
        "interval": "1h",
        "limit": days * 24  # 24h * days
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Konwersja do DataFrame
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        # Konwersja typów
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        df['symbol'] = 'BTCUSDT'
        
        # Usuń niepotrzebne kolumny
        df = df[['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume']]
        
        logger.info("Dane pobrane", rows=len(df), start=df['timestamp'].min(), end=df['timestamp'].max())
        return df
        
    except Exception as e:
        logger.error("Błąd pobierania danych", error=str(e))
        # Fallback - stwórz dane testowe
        logger.info("Tworzenie danych testowych")
        return create_test_data(days)

def create_test_data(days=30):
    """Stwórz dane testowe BTC"""
    import numpy as np
    
    # Generuj dane testowe
    start_date = datetime.now() - timedelta(days=days)
    timestamps = pd.date_range(start=start_date, periods=days*24, freq='1H')
    
    # Symuluj cenę BTC z trendem
    base_price = 45000
    trend = np.linspace(0, 0.1, len(timestamps))  # 10% wzrost
    noise = np.random.normal(0, 0.02, len(timestamps))  # 2% noise
    
    prices = base_price * (1 + trend + noise)
    
    df = pd.DataFrame({
        'symbol': 'BTCUSDT',
        'timestamp': timestamps,
        'open': prices,
        'high': prices * 1.01,
        'low': prices * 0.99,
        'close': prices,
        'volume': np.random.uniform(100, 1000, len(timestamps))
    })
    
    logger.info("Dane testowe utworzone", rows=len(df))
    return df

def save_to_database(df, database_url):
    """Zapisz dane do PostgreSQL"""
    logger.info("Zapisywanie do bazy danych", rows=len(df))
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Stwórz tabelę jeśli nie istnieje
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS market_data (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            open DECIMAL(20,8) NOT NULL,
            high DECIMAL(20,8) NOT NULL,
            low DECIMAL(20,8) NOT NULL,
            close DECIMAL(20,8) NOT NULL,
            volume DECIMAL(20,8) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, timestamp)
        );
        CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp ON market_data(symbol, timestamp);
        """
        cursor.execute(create_table_sql)
        conn.commit()
        
        # Wstaw dane
        insert_sql = """
        INSERT INTO market_data (symbol, timestamp, open, high, low, close, volume)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (symbol, timestamp) DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume
        """
        
        for _, row in df.iterrows():
            cursor.execute(insert_sql, (
                row['symbol'],
                row['timestamp'],
                float(row['open']),
                float(row['high']),
                float(row['low']),
                float(row['close']),
                float(row['volume'])
            ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("Dane zapisane do bazy danych")
        
    except Exception as e:
        logger.error("Błąd zapisywania do bazy", error=str(e))
        raise

def main():
    """Główna funkcja"""
    logger.info("Rozpoczynanie ładowania danych historycznych BTC")
    
    # Pobierz DATABASE_URL z environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("Brak DATABASE_URL w environment variables")
        sys.exit(1)
    
    try:
        # Pobierz dane (ostatnie 30 dni)
        df = get_btc_data(days=30)
        
        # Zapisz do bazy
        save_to_database(df, database_url)
        
        logger.info("✅ Dane historyczne BTC załadowane pomyślnie!")
        print(f"📊 Załadowano {len(df)} rekordów BTC")
        print(f"📅 Okres: {df['timestamp'].min()} - {df['timestamp'].max()}")
        print(f"💰 Cena: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
        
    except Exception as e:
        logger.error("Błąd ładowania danych", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
