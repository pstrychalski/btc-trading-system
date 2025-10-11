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
    """Pobierz historyczne dane BTC z CoinGecko"""
    logger.info("Pobieranie danych BTC", days=days)
    
    # CoinGecko API - darmowe, bez klucza
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    params = {
        "vs_currency": "usd",
        "days": days,
        "interval": "hourly"  # 1h intervals
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Konwersja do DataFrame
        prices = data['prices']
        volumes = data['total_volumes']
        
        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
        df['volume'] = [v[1] for v in volumes]
        
        # Dodaj kolumny OHLCV (uproszczone - tylko close price)
        df['open'] = df['price'].shift(1).fillna(df['price'])
        df['high'] = df['price'] * 1.01  # Symulacja
        df['low'] = df['price'] * 0.99   # Symulacja
        df['close'] = df['price']
        
        # Konwersja timestamp
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['symbol'] = 'BTCUSDT'
        
        # Usuń NaN
        df = df.dropna()
        
        logger.info("Dane pobrane", rows=len(df), start=df['timestamp'].min(), end=df['timestamp'].max())
        return df
        
    except Exception as e:
        logger.error("Błąd pobierania danych", error=str(e))
        raise

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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
