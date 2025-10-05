"""
Data Loader for Backtrader
Loads OHLCV data from PostgreSQL
"""
import os
import pandas as pd
import backtrader as bt
from sqlalchemy import create_engine
from datetime import datetime
import structlog

logger = structlog.get_logger()


class PostgreSQLDataLoader:
    """Load data from PostgreSQL database"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL not provided")
        
        self.engine = create_engine(self.database_url)
    
    def load_ohlcv(
        self, 
        symbol: str, 
        start_date: str = None, 
        end_date: str = None,
        interval: str = '1h'
    ) -> pd.DataFrame:
        """
        Load OHLCV data from database
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
        
        Returns:
            DataFrame with OHLCV data
        """
        query = f"""
        SELECT 
            timestamp,
            open,
            high,
            low,
            close,
            volume
        FROM market_data_ohlcv
        WHERE symbol = '{symbol}'
        AND interval = '{interval}'
        """
        
        if start_date:
            query += f" AND timestamp >= '{start_date}'"
        if end_date:
            query += f" AND timestamp <= '{end_date}'"
        
        query += " ORDER BY timestamp ASC"
        
        logger.info(f"Loading OHLCV data", symbol=symbol, start=start_date, end=end_date, interval=interval)
        
        try:
            df = pd.read_sql(query, self.engine)
            
            if df.empty:
                logger.warning("No data found", symbol=symbol, start=start_date, end=end_date)
                return df
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # Ensure numeric types
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            logger.info(f"Loaded {len(df)} candles", symbol=symbol, start=df.index[0], end=df.index[-1])
            
            return df
        
        except Exception as e:
            logger.error("Error loading data", error=str(e))
            raise
    
    def get_available_symbols(self) -> list:
        """Get list of available symbols"""
        query = "SELECT DISTINCT symbol FROM market_data_ohlcv ORDER BY symbol"
        try:
            df = pd.read_sql(query, self.engine)
            return df['symbol'].tolist()
        except Exception as e:
            logger.error("Error getting symbols", error=str(e))
            return []
    
    def get_date_range(self, symbol: str, interval: str = '1h') -> dict:
        """Get date range for a symbol"""
        query = f"""
        SELECT 
            MIN(timestamp) as start_date,
            MAX(timestamp) as end_date,
            COUNT(*) as count
        FROM market_data_ohlcv
        WHERE symbol = '{symbol}'
        AND interval = '{interval}'
        """
        try:
            df = pd.read_sql(query, self.engine)
            return {
                'start_date': df['start_date'].iloc[0],
                'end_date': df['end_date'].iloc[0],
                'count': df['count'].iloc[0]
            }
        except Exception as e:
            logger.error("Error getting date range", error=str(e))
            return {}


class PandasDataExtended(bt.feeds.PandasData):
    """
    Extended Pandas Data Feed for Backtrader
    Supports additional columns like indicators
    """
    
    # Define additional lines if needed
    lines = ('volume',)
    
    params = (
        ('datetime', None),
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('openinterest', -1),
    )


def create_backtrader_feed(df: pd.DataFrame) -> PandasDataExtended:
    """
    Convert DataFrame to Backtrader data feed
    
    Args:
        df: DataFrame with OHLCV data (indexed by datetime)
    
    Returns:
        Backtrader PandasDataExtended feed
    """
    # Ensure datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DataFrame must have datetime index")
    
    # Create data feed
    data_feed = PandasDataExtended(dataname=df)
    
    return data_feed


# For local CSV testing
def load_csv_data(csv_path: str) -> pd.DataFrame:
    """
    Load OHLCV data from CSV file
    
    Expected columns: timestamp, open, high, low, close, volume
    """
    df = pd.read_csv(csv_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

