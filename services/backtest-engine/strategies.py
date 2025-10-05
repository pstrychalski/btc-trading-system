"""
Backtrader Trading Strategies
Advanced strategy implementations z custom indicators
"""
import backtrader as bt
import numpy as np


class BaseStrategy(bt.Strategy):
    """Base strategy z common functionality"""
    
    params = (
        ('stake_percent', 0.95),  # 95% kapitału w każdym trade
        ('print_log', False),
    )
    
    def __init__(self):
        self.order = None
        self.buy_price = None
        self.buy_comm = None
        
    def log(self, txt, dt=None):
        """Logging function"""
        if self.params.print_log:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
    
    def notify_order(self, order):
        """Handle order notifications"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}, '
                        f'Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
                self.buy_price = order.executed.price
                self.buy_comm = order.executed.comm
            else:
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}, '
                        f'Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
            self.bar_executed = len(self)
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
        
        self.order = None
    
    def notify_trade(self, trade):
        """Handle trade notifications"""
        if not trade.isclosed:
            return
        
        self.log(f'OPERATION PROFIT, GROSS: {trade.pnl:.2f}, NET: {trade.pnlcomm:.2f}')


class MovingAverageCrossStrategy(BaseStrategy):
    """
    Classic MA Cross Strategy
    Buy: Fast MA crosses above Slow MA
    Sell: Fast MA crosses below Slow MA
    """
    
    params = (
        ('fast_period', 10),
        ('slow_period', 30),
        ('stop_loss', 0.02),  # 2% stop loss
        ('take_profit', 0.05),  # 5% take profit
    )
    
    def __init__(self):
        super().__init__()
        
        # Moving averages
        self.fast_ma = bt.indicators.SMA(self.data.close, period=self.params.fast_period)
        self.slow_ma = bt.indicators.SMA(self.data.close, period=self.params.slow_period)
        
        # Crossover
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        
    def next(self):
        """Strategy logic"""
        if self.order:
            return
        
        # Check if we are in the market
        if not self.position:
            # Not in market, check for buy signal
            if self.crossover > 0:  # Fast MA crossed above Slow MA
                size = int(self.broker.getvalue() * self.params.stake_percent / self.data.close[0])
                self.log(f'BUY CREATE, {self.data.close[0]:.2f}')
                self.order = self.buy(size=size)
        
        else:
            # In market, check for sell signal or stops
            if self.crossover < 0:  # Fast MA crossed below Slow MA
                self.log(f'SELL CREATE, {self.data.close[0]:.2f}')
                self.order = self.sell(size=self.position.size)
            
            # Check stop loss
            elif self.buy_price and (self.data.close[0] / self.buy_price - 1) < -self.params.stop_loss:
                self.log(f'STOP LOSS, {self.data.close[0]:.2f}')
                self.order = self.sell(size=self.position.size)
            
            # Check take profit
            elif self.buy_price and (self.data.close[0] / self.buy_price - 1) > self.params.take_profit:
                self.log(f'TAKE PROFIT, {self.data.close[0]:.2f}')
                self.order = self.sell(size=self.position.size)


class RSIMeanReversionStrategy(BaseStrategy):
    """
    RSI Mean Reversion Strategy
    Buy: RSI < oversold
    Sell: RSI > overbought
    """
    
    params = (
        ('rsi_period', 14),
        ('oversold', 30),
        ('overbought', 70),
        ('sma_period', 50),  # Trend filter
    )
    
    def __init__(self):
        super().__init__()
        
        # RSI
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        
        # Trend filter
        self.sma = bt.indicators.SMA(self.data.close, period=self.params.sma_period)
    
    def next(self):
        """Strategy logic"""
        if self.order:
            return
        
        # Price above SMA = uptrend
        in_uptrend = self.data.close[0] > self.sma[0]
        
        if not self.position:
            # Buy when RSI is oversold and in uptrend
            if self.rsi[0] < self.params.oversold and in_uptrend:
                size = int(self.broker.getvalue() * self.params.stake_percent / self.data.close[0])
                self.log(f'BUY CREATE (RSI: {self.rsi[0]:.2f}), {self.data.close[0]:.2f}')
                self.order = self.buy(size=size)
        
        else:
            # Sell when RSI is overbought
            if self.rsi[0] > self.params.overbought:
                self.log(f'SELL CREATE (RSI: {self.rsi[0]:.2f}), {self.data.close[0]:.2f}')
                self.order = self.sell(size=self.position.size)


class BollingerBandsStrategy(BaseStrategy):
    """
    Bollinger Bands Breakout Strategy
    Buy: Price touches lower band
    Sell: Price touches upper band
    """
    
    params = (
        ('bb_period', 20),
        ('bb_dev', 2),
    )
    
    def __init__(self):
        super().__init__()
        
        # Bollinger Bands
        self.bb = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.bb_period,
            devfactor=self.params.bb_dev
        )
    
    def next(self):
        """Strategy logic"""
        if self.order:
            return
        
        if not self.position:
            # Buy when price touches or goes below lower band
            if self.data.close[0] <= self.bb.lines.bot[0]:
                size = int(self.broker.getvalue() * self.params.stake_percent / self.data.close[0])
                self.log(f'BUY CREATE (BB Lower: {self.bb.lines.bot[0]:.2f}), {self.data.close[0]:.2f}')
                self.order = self.buy(size=size)
        
        else:
            # Sell when price touches or goes above upper band
            if self.data.close[0] >= self.bb.lines.top[0]:
                self.log(f'SELL CREATE (BB Upper: {self.bb.lines.top[0]:.2f}), {self.data.close[0]:.2f}')
                self.order = self.sell(size=self.position.size)


class MACDStrategy(BaseStrategy):
    """
    MACD Strategy
    Buy: MACD line crosses above signal line
    Sell: MACD line crosses below signal line
    """
    
    params = (
        ('macd_fast', 12),
        ('macd_slow', 26),
        ('macd_signal', 9),
    )
    
    def __init__(self):
        super().__init__()
        
        # MACD
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.params.macd_fast,
            period_me2=self.params.macd_slow,
            period_signal=self.params.macd_signal
        )
        
        # Crossover
        self.crossover = bt.indicators.CrossOver(self.macd.macd, self.macd.signal)
    
    def next(self):
        """Strategy logic"""
        if self.order:
            return
        
        if not self.position:
            # Buy when MACD crosses above signal
            if self.crossover > 0:
                size = int(self.broker.getvalue() * self.params.stake_percent / self.data.close[0])
                self.log(f'BUY CREATE (MACD: {self.macd.macd[0]:.4f}), {self.data.close[0]:.2f}')
                self.order = self.buy(size=size)
        
        else:
            # Sell when MACD crosses below signal
            if self.crossover < 0:
                self.log(f'SELL CREATE (MACD: {self.macd.macd[0]:.4f}), {self.data.close[0]:.2f}')
                self.order = self.sell(size=self.position.size)


# Strategy registry for easy access
STRATEGY_REGISTRY = {
    'ma_cross': MovingAverageCrossStrategy,
    'rsi_mean_reversion': RSIMeanReversionStrategy,
    'bollinger_bands': BollingerBandsStrategy,
    'macd': MACDStrategy,
}


def get_strategy(name: str):
    """Get strategy class by name"""
    if name not in STRATEGY_REGISTRY:
        raise ValueError(f"Strategy '{name}' not found. Available: {list(STRATEGY_REGISTRY.keys())}")
    return STRATEGY_REGISTRY[name]

