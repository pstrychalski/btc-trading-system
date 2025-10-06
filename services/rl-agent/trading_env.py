"""
Gymnasium Trading Environment
For Reinforcement Learning
"""
import gymnasium as gym
import numpy as np
from gymnasium import spaces


class TradingEnv(gym.Env):
    """Custom Trading Environment for RL"""
    
    def __init__(self, data, initial_balance=10000):
        super().__init__()
        
        self.data = data
        self.initial_balance = initial_balance
        
        # Action: 0=Hold, 1=Buy, 2=Sell
        self.action_space = spaces.Discrete(3)
        
        # Observation: [price, position, balance, indicators...]
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(10,), dtype=np.float32
        )
        
        self.reset()
    
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        self.balance = self.initial_balance
        self.position = 0
        self.entry_price = 0
        return self._get_observation(), {}
    
    def step(self, action):
        current_price = self.data[self.current_step]['close']
        
        # Execute action
        if action == 1:  # Buy
            if self.position == 0 and self.balance > current_price:
                self.position = 1
                self.entry_price = current_price
                self.balance -= current_price
        
        elif action == 2:  # Sell
            if self.position > 0:
                self.balance += current_price
                reward = current_price - self.entry_price
                self.position = 0
        
        # Calculate reward
        reward = self._calculate_reward()
        
        self.current_step += 1
        done = self.current_step >= len(self.data) - 1
        
        return self._get_observation(), reward, done, False, {}
    
    def _get_observation(self):
        price = self.data[self.current_step]['close']
        return np.array([price, self.position, self.balance, 0, 0, 0, 0, 0, 0, 0], dtype=np.float32)
    
    def _calculate_reward(self):
        current_price = self.data[self.current_step]['close']
        total_value = self.balance + (self.position * current_price)
        return (total_value - self.initial_balance) / self.initial_balance

