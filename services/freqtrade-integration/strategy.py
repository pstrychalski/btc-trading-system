"""
Advanced Freqtrade Strategy with AI Integration
Integrates:
- Market Memory for risk validation
- RL Agent for trading signals
- Real-time market data
"""
import logging
from datetime import datetime
from typing import Optional
import requests
import pandas as pd
import numpy as np
from freqtrade.strategy import IStrategy, DecimalParameter, IntParameter
from pandas import DataFrame

logger = logging.getLogger(__name__)


class AIEnhancedStrategy(IStrategy):
    """
    Advanced strategy integrating:
    1. Market Memory - Risk validation from similar historical patterns
    2. RL Agent - AI-powered trading signals
    3. Technical Indicators - Traditional TA confirmation
    """
    
    # Strategy Configuration
    INTERFACE_VERSION = 3
    
    # Minimal ROI designed to trigger automatic exit
    minimal_roi = {
        "0": 0.10,   # 10% profit target
        "30": 0.05,  # 5% after 30 minutes
        "60": 0.03,  # 3% after 1 hour
        "120": 0.01  # 1% after 2 hours
    }
    
    # Stoploss
    stoploss = -0.05  # 5% stoploss
    
    # Trailing stoploss
    trailing_stop = True
    trailing_stop_positive = 0.02  # Activate after 2% profit
    trailing_stop_positive_offset = 0.03  # Offset at 3%
    trailing_only_offset_is_reached = True
    
    # Timeframe
    timeframe = '5m'
    
    # Service endpoints (configured via environment)
    MARKET_MEMORY_URL = "http://market-memory:8004"
    RL_AGENT_URL = "http://rl-agent:8007"
    
    # Strategy parameters (optimizable via Optuna)
    risk_threshold = DecimalParameter(0.3, 0.8, default=0.6, space='buy')
    rl_confidence_threshold = DecimalParameter(0.5, 0.9, default=0.7, space='buy')
    rsi_buy_threshold = IntParameter(20, 40, default=30, space='buy')
    rsi_sell_threshold = IntParameter(60, 80, default=70, space='sell')
    
    # Enable position adjustment
    position_adjustment_enable = True
    max_entry_position_adjustment = 3
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Add technical indicators to the dataframe
        """
        # RSI
        dataframe['rsi'] = self._calculate_rsi(dataframe['close'], 14)
        
        # Moving Averages
        dataframe['ema_fast'] = dataframe['close'].ewm(span=12).mean()
        dataframe['ema_slow'] = dataframe['close'].ewm(span=26).mean()
        
        # MACD
        dataframe['macd'], dataframe['macdsignal'], dataframe['macdhist'] = self._calculate_macd(dataframe)
        
        # Bollinger Bands
        dataframe['bb_upper'], dataframe['bb_middle'], dataframe['bb_lower'] = self._calculate_bollinger_bands(dataframe)
        
        # Volume indicators
        dataframe['volume_sma'] = dataframe['volume'].rolling(window=20).mean()
        
        # Volatility (ATR)
        dataframe['atr'] = self._calculate_atr(dataframe, 14)
        
        return dataframe
    
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Determine buy signals with AI enhancement
        """
        conditions = []
        
        # Technical conditions
        conditions.append(dataframe['rsi'] < self.rsi_buy_threshold.value)
        conditions.append(dataframe['ema_fast'] > dataframe['ema_slow'])
        conditions.append(dataframe['volume'] > dataframe['volume_sma'])
        
        # Combine technical conditions
        dataframe['tech_signal'] = np.where(
            np.all(conditions, axis=0), 1, 0
        )
        
        # AI Enhancement - check for each row
        ai_signals = []
        for idx, row in dataframe.iterrows():
            ai_approved = self._check_ai_approval(row, metadata)
            ai_signals.append(ai_approved)
        
        dataframe['ai_approved'] = ai_signals
        
        # Final entry signal
        dataframe['enter_long'] = (
            (dataframe['tech_signal'] == 1) &
            (dataframe['ai_approved'] == True)
        )
        
        return dataframe
    
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Determine sell signals
        """
        conditions = []
        
        # Technical exit conditions
        conditions.append(dataframe['rsi'] > self.rsi_sell_threshold.value)
        conditions.append(dataframe['ema_fast'] < dataframe['ema_slow'])
        
        # Exit on MACD crossover
        conditions.append(dataframe['macd'] < dataframe['macdsignal'])
        
        # Combine conditions
        dataframe['exit_long'] = np.all(conditions, axis=0)
        
        return dataframe
    
    def _check_ai_approval(self, row: pd.Series, metadata: dict) -> bool:
        """
        Check both Market Memory and RL Agent for trade approval
        Returns True only if both approve
        """
        try:
            # 1. Market Memory Risk Check
            risk_approved = self._check_market_memory_risk(row, metadata)
            if not risk_approved:
                logger.info(f"Trade rejected by Market Memory - high risk pattern detected")
                return False
            
            # 2. RL Agent Signal Check
            rl_approved = self._check_rl_agent_signal(row, metadata)
            if not rl_approved:
                logger.info(f"Trade rejected by RL Agent - low confidence")
                return False
            
            logger.info(f"Trade APPROVED by both AI systems")
            return True
            
        except Exception as e:
            logger.error(f"AI approval check failed: {e}")
            # Fail-safe: reject on error
            return False
    
    def _check_market_memory_risk(self, row: pd.Series, metadata: dict) -> bool:
        """
        Query Market Memory for risk assessment based on similar patterns
        """
        try:
            market_state = {
                "symbol": metadata['pair'],
                "timestamp": str(datetime.now()),
                "close": float(row['close']),
                "volume": float(row['volume']),
                "rsi": float(row['rsi']),
                "volatility": float(row['atr'])
            }
            
            response = requests.post(
                f"{self.MARKET_MEMORY_URL}/analyze-risk",
                json=market_state,
                timeout=2
            )
            
            if response.status_code == 200:
                risk_data = response.json()
                risk_score = risk_data.get('risk_score', 1.0)
                
                # Approve if risk is below threshold
                return risk_score < self.risk_threshold.value
            else:
                logger.warning(f"Market Memory API error: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Market Memory check failed: {e}")
            return False
    
    def _check_rl_agent_signal(self, row: pd.Series, metadata: dict) -> bool:
        """
        Query RL Agent for trading signal
        """
        try:
            observation = {
                "close": float(row['close']),
                "volume": float(row['volume']),
                "rsi": float(row['rsi']),
                "macd": float(row['macd']),
                "bb_position": (float(row['close']) - float(row['bb_lower'])) / 
                               (float(row['bb_upper']) - float(row['bb_lower']))
            }
            
            response = requests.post(
                f"{self.RL_AGENT_URL}/inference",
                json={"observation": observation},
                timeout=2
            )
            
            if response.status_code == 200:
                rl_data = response.json()
                action = rl_data.get('action', 0)
                confidence = rl_data.get('confidence', 0.0)
                
                # Action: 0=Hold, 1=Buy, 2=Sell
                # Approve BUY signal with sufficient confidence
                return action == 1 and confidence > self.rl_confidence_threshold.value
            else:
                logger.warning(f"RL Agent API error: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"RL Agent check failed: {e}")
            return False
    
    # ============ Technical Indicator Calculations ============
    
    def _calculate_rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_macd(self, dataframe: DataFrame):
        """Calculate MACD"""
        exp1 = dataframe['close'].ewm(span=12).mean()
        exp2 = dataframe['close'].ewm(span=26).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9).mean()
        hist = macd - signal
        return macd, signal, hist
    
    def _calculate_bollinger_bands(self, dataframe: DataFrame, period: int = 20, std: float = 2.0):
        """Calculate Bollinger Bands"""
        middle = dataframe['close'].rolling(window=period).mean()
        std_dev = dataframe['close'].rolling(window=period).std()
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        return upper, middle, lower
    
    def _calculate_atr(self, dataframe: DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high_low = dataframe['high'] - dataframe['low']
        high_close = np.abs(dataframe['high'] - dataframe['close'].shift())
        low_close = np.abs(dataframe['low'] - dataframe['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        return true_range.rolling(window=period).mean()
    
    def confirm_trade_exit(self, pair: str, trade, order_type: str, amount: float,
                           rate: float, time_in_force: str, exit_reason: str,
                           current_time: datetime, **kwargs) -> bool:
        """
        Called before exiting a trade - final check with RL Agent
        """
        try:
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            last_candle = dataframe.iloc[-1]
            
            # Quick RL check for exit confirmation
            observation = {
                "close": float(last_candle['close']),
                "rsi": float(last_candle['rsi']),
                "macd": float(last_candle['macd'])
            }
            
            response = requests.post(
                f"{self.RL_AGENT_URL}/inference",
                json={"observation": observation},
                timeout=1
            )
            
            if response.status_code == 200:
                rl_data = response.json()
                action = rl_data.get('action', 0)
                
                # If RL suggests BUY (1), maybe don't exit
                if action == 1 and exit_reason == 'exit_signal':
                    logger.info(f"Exit postponed - RL Agent still bullish")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Exit confirmation failed: {e}")
            # Default: allow exit
            return True

