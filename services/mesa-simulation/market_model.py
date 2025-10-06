"""
Mesa Market Model
Agent-based market simulation
"""
import numpy as np
import pandas as pd
from mesa import Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
import structlog

from agents import create_agent

logger = structlog.get_logger()


class MarketModel(Model):
    """Agent-based market simulation model"""
    
    def __init__(
        self,
        n_agents: int = 100,
        agent_distribution: dict = None,
        initial_price: float = 100.0,
        price_volatility: float = 0.02,
        external_data: pd.Series = None
    ):
        """
        Args:
            n_agents: Total number of agents
            agent_distribution: Dict of agent_type: proportion
            initial_price: Starting price
            price_volatility: Random price volatility
            external_data: External price data (optional)
        """
        super().__init__()
        self.n_agents = n_agents
        self.schedule = RandomActivation(self)
        
        # Price dynamics
        self.price_history = [initial_price]
        self.external_data = external_data
        self.price_volatility = price_volatility
        
        # Default agent distribution
        if agent_distribution is None:
            agent_distribution = {
                'random': 0.2,
                'trend_follower': 0.2,
                'contrarian': 0.2,
                'market_maker': 0.1,
                'informed': 0.1,
                'noise': 0.2
            }
        
        # Create agents
        self._create_agents(agent_distribution)
        
        # Data collector
        self.datacollector = DataCollector(
            model_reporters={
                "Price": lambda m: m.get_current_price(),
                "Volume": lambda m: m.get_volume(),
                "Total_Wealth": lambda m: m.get_total_wealth(),
                "Bid_Ask_Spread": lambda m: m.get_spread()
            },
            agent_reporters={
                "Wealth": lambda a: a.get_wealth(a.model.get_current_price()),
                "Position": "position",
                "PnL": "pnl",
                "Type": lambda a: a.agent_type.value
            }
        )
        
        logger.info(f"MarketModel initialized with {n_agents} agents")
    
    def _create_agents(self, distribution: dict):
        """Create agents according to distribution"""
        agent_id = 0
        
        for agent_type, proportion in distribution.items():
            count = int(self.n_agents * proportion)
            for _ in range(count):
                agent = create_agent(agent_id, self, agent_type)
                self.schedule.add(agent)
                agent_id += 1
    
    def step(self):
        """Execute one step of the model"""
        # Agents act
        self.schedule.step()
        
        # Update price
        self._update_price()
        
        # Collect data
        self.datacollector.collect(self)
    
    def _update_price(self):
        """Update market price based on agent actions"""
        current_price = self.price_history[-1]
        
        # If external data provided, use it
        if self.external_data is not None:
            step = self.schedule.steps
            if step < len(self.external_data):
                new_price = self.external_data.iloc[step]
                self.price_history.append(new_price)
                return
        
        # Otherwise, simulate price based on order flow
        buy_pressure = 0
        sell_pressure = 0
        
        for agent in self.schedule.agents:
            if len(agent.trades) > 0:
                last_trade = agent.trades[-1]
                if last_trade['step'] == self.schedule.steps:
                    if last_trade['side'] == 'buy':
                        buy_pressure += last_trade['quantity']
                    else:
                        sell_pressure += last_trade['quantity']
        
        # Price impact
        net_pressure = buy_pressure - sell_pressure
        impact_factor = 0.001  # Price impact per unit
        price_change = net_pressure * impact_factor
        
        # Add random walk
        random_change = np.random.normal(0, self.price_volatility)
        
        new_price = current_price * (1 + price_change + random_change)
        new_price = max(new_price, 0.01)  # Price floor
        
        self.price_history.append(new_price)
    
    def get_current_price(self) -> float:
        """Get current market price"""
        return self.price_history[-1]
    
    def get_price_history(self, lookback: int) -> list:
        """Get recent price history"""
        return self.price_history[-lookback:]
    
    def get_future_price(self, foresight: int) -> float:
        """Get future price (for informed traders)"""
        if self.external_data is None:
            return None
        
        future_step = self.schedule.steps + foresight
        if future_step < len(self.external_data):
            return self.external_data.iloc[future_step]
        return None
    
    def get_volume(self) -> int:
        """Get trading volume in current step"""
        volume = 0
        for agent in self.schedule.agents:
            if len(agent.trades) > 0:
                last_trade = agent.trades[-1]
                if last_trade['step'] == self.schedule.steps:
                    volume += last_trade['quantity']
        return volume
    
    def get_total_wealth(self) -> float:
        """Get total wealth of all agents"""
        current_price = self.get_current_price()
        return sum(agent.get_wealth(current_price) for agent in self.schedule.agents)
    
    def get_spread(self) -> float:
        """Estimate bid-ask spread"""
        # Simplified spread estimation
        return self.get_current_price() * 0.001
    
    def run_simulation(self, n_steps: int) -> pd.DataFrame:
        """Run full simulation"""
        logger.info(f"Running simulation for {n_steps} steps")
        
        for _ in range(n_steps):
            self.step()
        
        # Get results
        model_data = self.datacollector.get_model_vars_dataframe()
        agent_data = self.datacollector.get_agent_vars_dataframe()
        
        logger.info(f"Simulation complete. Final price: {self.get_current_price():.2f}")
        
        return model_data, agent_data

