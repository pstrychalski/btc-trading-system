"""
Performance Metrics for Backtrader
Advanced metrics calculation and analysis
"""
import numpy as np
import pandas as pd
from typing import Dict, Any
import structlog

logger = structlog.get_logger()


class PerformanceMetrics:
    """Calculate comprehensive performance metrics"""
    
    def __init__(self, cerebro, strategy_name: str = None):
        """
        Args:
            cerebro: Backtrader Cerebro instance after run
            strategy_name: Name of the strategy
        """
        self.cerebro = cerebro
        self.strategy_name = strategy_name
        self.analyzers = {}
        
    def add_analyzers(self):
        """Add all analyzers to cerebro before run"""
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0.02)
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        self.cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
        self.cerebro.addanalyzer(bt.analyzers.VWR, _name='vwr')
        
    def extract_metrics(self, strat) -> Dict[str, Any]:
        """
        Extract all metrics from strategy analyzers
        
        Args:
            strat: Strategy instance after run
        
        Returns:
            Dictionary with all metrics
        """
        metrics = {}
        
        # Returns
        returns = strat.analyzers.returns.get_analysis()
        metrics['total_return'] = returns.get('rtot', 0.0)
        metrics['avg_annual_return'] = returns.get('rnorm', 0.0)
        metrics['avg_monthly_return'] = returns.get('rnorm100', 0.0) / 12
        
        # Sharpe Ratio
        sharpe = strat.analyzers.sharpe.get_analysis()
        metrics['sharpe_ratio'] = sharpe.get('sharperatio', 0.0) or 0.0
        
        # Drawdown
        drawdown = strat.analyzers.drawdown.get_analysis()
        metrics['max_drawdown'] = drawdown.get('max', {}).get('drawdown', 0.0)
        metrics['max_drawdown_period'] = drawdown.get('max', {}).get('len', 0)
        metrics['max_drawdown_money'] = drawdown.get('max', {}).get('moneydown', 0.0)
        
        # Trades
        trades = strat.analyzers.trades.get_analysis()
        metrics['total_trades'] = trades.get('total', {}).get('total', 0)
        metrics['winning_trades'] = trades.get('won', {}).get('total', 0)
        metrics['losing_trades'] = trades.get('lost', {}).get('total', 0)
        
        if metrics['total_trades'] > 0:
            metrics['win_rate'] = metrics['winning_trades'] / metrics['total_trades']
        else:
            metrics['win_rate'] = 0.0
        
        # Average PnL
        if metrics['winning_trades'] > 0:
            metrics['avg_win'] = trades.get('won', {}).get('pnl', {}).get('average', 0.0)
        else:
            metrics['avg_win'] = 0.0
            
        if metrics['losing_trades'] > 0:
            metrics['avg_loss'] = abs(trades.get('lost', {}).get('pnl', {}).get('average', 0.0))
        else:
            metrics['avg_loss'] = 0.0
        
        # Profit Factor
        if metrics['avg_loss'] > 0:
            metrics['profit_factor'] = (metrics['avg_win'] * metrics['winning_trades']) / (metrics['avg_loss'] * metrics['losing_trades'])
        else:
            metrics['profit_factor'] = 0.0
        
        # SQN (System Quality Number)
        sqn = strat.analyzers.sqn.get_analysis()
        metrics['sqn'] = sqn.get('sqn', 0.0) or 0.0
        
        # VWR (Variability Weighted Return)
        vwr = strat.analyzers.vwr.get_analysis()
        metrics['vwr'] = vwr.get('vwr', 0.0) or 0.0
        
        # Portfolio value
        metrics['starting_value'] = self.cerebro.broker.startingcash
        metrics['final_value'] = self.cerebro.broker.getvalue()
        metrics['net_profit'] = metrics['final_value'] - metrics['starting_value']
        metrics['return_pct'] = (metrics['net_profit'] / metrics['starting_value']) * 100
        
        logger.info(
            "Metrics calculated",
            strategy=self.strategy_name,
            return_pct=f"{metrics['return_pct']:.2f}%",
            sharpe=f"{metrics['sharpe_ratio']:.2f}",
            max_dd=f"{metrics['max_drawdown']:.2f}%",
            win_rate=f"{metrics['win_rate']*100:.2f}%"
        )
        
        return metrics
    
    def print_summary(self, metrics: Dict[str, Any]):
        """Print formatted metrics summary"""
        print("\n" + "="*60)
        print(f"BACKTEST RESULTS: {self.strategy_name or 'Strategy'}")
        print("="*60)
        
        print(f"\n📊 Portfolio Performance:")
        print(f"  Starting Value: ${metrics['starting_value']:,.2f}")
        print(f"  Final Value:    ${metrics['final_value']:,.2f}")
        print(f"  Net Profit:     ${metrics['net_profit']:,.2f}")
        print(f"  Return:         {metrics['return_pct']:.2f}%")
        
        print(f"\n📈 Risk-Adjusted Returns:")
        print(f"  Sharpe Ratio:   {metrics['sharpe_ratio']:.2f}")
        print(f"  SQN:            {metrics['sqn']:.2f}")
        print(f"  VWR:            {metrics['vwr']:.2f}")
        
        print(f"\n📉 Drawdown:")
        print(f"  Max Drawdown:   {metrics['max_drawdown']:.2f}%")
        print(f"  DD Period:      {metrics['max_drawdown_period']} days")
        print(f"  DD Money:       ${metrics['max_drawdown_money']:,.2f}")
        
        print(f"\n💼 Trading Stats:")
        print(f"  Total Trades:   {metrics['total_trades']}")
        print(f"  Winning:        {metrics['winning_trades']} ({metrics['win_rate']*100:.2f}%)")
        print(f"  Losing:         {metrics['losing_trades']}")
        print(f"  Avg Win:        ${metrics['avg_win']:,.2f}")
        print(f"  Avg Loss:       ${metrics['avg_loss']:,.2f}")
        print(f"  Profit Factor:  {metrics['profit_factor']:.2f}")
        
        print("="*60 + "\n")
    
    @staticmethod
    def calculate_kelly_criterion(win_rate: float, avg_win: float, avg_loss: float) -> float:
        """
        Calculate Kelly Criterion for optimal position sizing
        
        Args:
            win_rate: Winning percentage (0-1)
            avg_win: Average winning trade
            avg_loss: Average losing trade (positive number)
        
        Returns:
            Kelly percentage (0-1)
        """
        if avg_loss == 0:
            return 0.0
        
        win_loss_ratio = avg_win / avg_loss
        kelly = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
        
        # Conservative: use half Kelly
        return max(0, kelly * 0.5)


import backtrader as bt


def get_strategy_params_info(strategy_class) -> Dict[str, Any]:
    """Get information about strategy parameters"""
    params = {}
    for param in strategy_class.params._getpairs():
        params[param[0]] = param[1]
    return params

