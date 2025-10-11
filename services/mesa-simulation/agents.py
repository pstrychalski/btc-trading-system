"""
Trading Agents for Simple Simulation
Different agent types with various strategies
"""
import numpy as np
from enum import Enum
import structlog

logger = structlog.get_logger()


class AgentType(Enum):
    """Types of trading agents"""
    RANDOM = "random"
    TREND_FOLLOWER = "trend_follower"
    CONTRARIAN = "contrarian"
    MARKET_MAKER = "market_maker"
    INFORMED = "informed"
    NOISE = "noise"


class BaseTrader:
    """Base trading agent"""
    
    def __init__(self, unique_id, model, agent_type: AgentType, initial_cash: float = 10000):
        self.unique_id = unique_id
        self.model = model
        self.agent_type = agent_type
        self.cash = initial_cash
        self.position = 0  # Number of shares held
        self.avg_entry_price = 0.0
        self.trades = []
        self.pnl = 0.0
        
    def get_wealth(self, current_price: float) -> float:
        """Calculate total wealth"""
        return self.cash + (self.position * current_price)
    
    def execute_trade(self, side: str, quantity: int, price: float):
        """Execute a trade"""
        if side == "buy":
            cost = quantity * price
            if cost <= self.cash:
                self.cash -= cost
                old_position = self.position
                self.position += quantity
                
                # Update avg entry price
                if old_position > 0:
                    self.avg_entry_price = (
                        (old_position * self.avg_entry_price + cost) / 
                        (old_position + quantity)
                    )
                else:
                    self.avg_entry_price = price
                
                self.trades.append({
                    'step': self.model.schedule.steps,
                    'side': 'buy',
                    'quantity': quantity,
                    'price': price
                })
                
        elif side == "sell":
            if quantity <= self.position:
                revenue = quantity * price
                self.cash += revenue
                self.position -= quantity
                
                # Calculate PnL
                if self.avg_entry_price > 0:
                    pnl = (price - self.avg_entry_price) * quantity
                    self.pnl += pnl
                
                self.trades.append({
                    'step': self.model.schedule.steps,
                    'side': 'sell',
                    'quantity': quantity,
                    'price': price
                })
    
    def step(self):
        """Agent step - to be overridden by subclasses"""
        pass


class RandomTrader(BaseTrader):
    """Trades randomly"""
    
    def __init__(self, unique_id, model, initial_cash: float = 10000):
        super().__init__(unique_id, model, AgentType.RANDOM, initial_cash)
        self.trade_probability = 0.1
    
    def step(self):
        """Random trading decisions"""
        if np.random.random() < self.trade_probability:
            current_price = self.model.get_current_price()
            
            action = np.random.choice(['buy', 'sell', 'hold'])
            quantity = np.random.randint(1, 5)
            
            if action == 'buy':
                self.execute_trade('buy', quantity, current_price)
            elif action == 'sell' and self.position > 0:
                quantity = min(quantity, self.position)
                self.execute_trade('sell', quantity, current_price)


class TrendFollower(BaseTrader):
    """Follows price trends"""
    
    def __init__(self, unique_id, model, initial_cash: float = 10000):
        super().__init__(unique_id, model, AgentType.TREND_FOLLOWER, initial_cash)
        self.lookback = 10
    
    def step(self):
        """Buy uptrends, sell downtrends"""
        price_history = self.model.get_price_history(self.lookback)
        
        if len(price_history) < self.lookback:
            return
        
        # Calculate trend
        returns = np.diff(price_history) / price_history[:-1]
        trend = np.mean(returns)
        
        current_price = self.model.get_current_price()
        quantity = 2
        
        # Buy in uptrend
        if trend > 0.01:
            if self.position == 0:
                self.execute_trade('buy', quantity, current_price)
        
        # Sell in downtrend
        elif trend < -0.01:
            if self.position > 0:
                quantity = min(quantity, self.position)
                self.execute_trade('sell', quantity, current_price)


class Contrarian(BaseTrader):
    """Trades against the trend (mean reversion)"""
    
    def __init__(self, unique_id, model, initial_cash: float = 10000):
        super().__init__(unique_id, model, AgentType.CONTRARIAN, initial_cash)
        self.lookback = 20
        self.threshold = 0.02
    
    def step(self):
        """Buy oversold, sell overbought"""
        price_history = self.model.get_price_history(self.lookback)
        
        if len(price_history) < self.lookback:
            return
        
        current_price = self.model.get_current_price()
        mean_price = np.mean(price_history)
        deviation = (current_price - mean_price) / mean_price
        
        quantity = 2
        
        # Buy when price below mean (oversold)
        if deviation < -self.threshold:
            if self.position == 0:
                self.execute_trade('buy', quantity, current_price)
        
        # Sell when price above mean (overbought)
        elif deviation > self.threshold:
            if self.position > 0:
                quantity = min(quantity, self.position)
                self.execute_trade('sell', quantity, current_price)


class MarketMaker(BaseTrader):
    """Provides liquidity with bid-ask spread"""
    
    def __init__(self, unique_id, model, initial_cash: float = 50000):
        super().__init__(unique_id, model, AgentType.MARKET_MAKER, initial_cash)
        self.spread = 0.001  # 0.1% spread
        self.inventory_target = 10
    
    def step(self):
        """Maintain balanced inventory"""
        current_price = self.model.get_current_price()
        
        # Adjust position towards target
        if self.position < self.inventory_target:
            # Buy at bid
            bid_price = current_price * (1 - self.spread)
            quantity = min(2, self.inventory_target - self.position)
            if np.random.random() < 0.3:  # 30% chance
                self.execute_trade('buy', quantity, bid_price)
        
        elif self.position > self.inventory_target:
            # Sell at ask
            ask_price = current_price * (1 + self.spread)
            quantity = min(2, self.position - self.inventory_target)
            if np.random.random() < 0.3:
                self.execute_trade('sell', quantity, ask_price)


class InformedTrader(BaseTrader):
    """Has access to 'insider' information (future price direction)"""
    
    def __init__(self, unique_id, model, initial_cash: float = 20000):
        super().__init__(unique_id, model, AgentType.INFORMED, initial_cash)
        self.foresight = 5  # Can 'see' 5 steps ahead
    
    def step(self):
        """Trade based on future price knowledge"""
        current_price = self.model.get_current_price()
        future_price = self.model.get_future_price(self.foresight)
        
        if future_price is None:
            return
        
        expected_return = (future_price - current_price) / current_price
        quantity = 3
        
        # Buy if price will increase
        if expected_return > 0.01:
            if self.position == 0:
                self.execute_trade('buy', quantity, current_price)
        
        # Sell if price will decrease
        elif expected_return < -0.01:
            if self.position > 0:
                quantity = min(quantity, self.position)
                self.execute_trade('sell', quantity, current_price)


class NoiseTrader(BaseTrader):
    """Trades on noise/emotions rather than fundamentals"""
    
    def __init__(self, unique_id, model, initial_cash: float = 10000):
        super().__init__(unique_id, model, AgentType.NOISE, initial_cash)
        self.volatility_threshold = 0.02
    
    def step(self):
        """Overreact to price changes"""
        price_history = self.model.get_price_history(5)
        
        if len(price_history) < 5:
            return
        
        recent_return = (price_history[-1] - price_history[-2]) / price_history[-2]
        current_price = self.model.get_current_price()
        quantity = np.random.randint(1, 4)
        
        # Overreact to large moves
        if abs(recent_return) > self.volatility_threshold:
            if recent_return > 0 and np.random.random() < 0.6:
                # Panic buy
                self.execute_trade('buy', quantity, current_price)
            elif recent_return < 0 and self.position > 0 and np.random.random() < 0.6:
                # Panic sell
                quantity = min(quantity, self.position)
                self.execute_trade('sell', quantity, current_price)


# Agent factory
def create_agent(agent_id: int, model, agent_type: str, initial_cash: float = 10000):
    """Factory function to create agents"""
    agent_classes = {
        'random': RandomTrader,
        'trend_follower': TrendFollower,
        'contrarian': Contrarian,
        'market_maker': MarketMaker,
        'informed': InformedTrader,
        'noise': NoiseTrader
    }
    
    agent_class = agent_classes.get(agent_type, RandomTrader)
    return agent_class(agent_id, model, initial_cash)

