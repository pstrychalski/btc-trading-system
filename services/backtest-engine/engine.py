"""
Backtrader Engine
Main backtesting engine with MLflow integration
"""
import os
import backtrader as bt
import mlflow
import mlflow.sklearn
from datetime import datetime
from typing import Dict, Any, Optional
import structlog
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

from strategies import get_strategy, STRATEGY_REGISTRY
from data_loader import PostgreSQLDataLoader, create_backtrader_feed
from metrics import PerformanceMetrics

logger = structlog.get_logger()


class BacktestEngine:
    """
    Advanced Backtesting Engine
    - Multiple strategies support
    - MLflow experiment tracking
    - Custom metrics
    - Portfolio analysis
    """
    
    def __init__(
        self,
        initial_cash: float = 100000.0,
        commission: float = 0.001,  # 0.1%
        mlflow_tracking_uri: str = None
    ):
        """
        Initialize backtest engine
        
        Args:
            initial_cash: Starting portfolio value
            commission: Commission per trade (0.001 = 0.1%)
            mlflow_tracking_uri: MLflow tracking server URI
        """
        self.initial_cash = initial_cash
        self.commission = commission
        
        # MLflow setup
        self.mlflow_uri = mlflow_tracking_uri or os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000')
        mlflow.set_tracking_uri(self.mlflow_uri)
        mlflow.set_experiment("backtrader_backtests")
        
        logger.info("BacktestEngine initialized", 
                   cash=initial_cash, 
                   commission=commission,
                   mlflow_uri=self.mlflow_uri)
    
    def run_backtest(
        self,
        strategy_name: str,
        data_feed: bt.feeds.DataBase,
        strategy_params: Dict[str, Any] = None,
        run_name: str = None,
        log_to_mlflow: bool = True
    ) -> Dict[str, Any]:
        """
        Run backtest for a strategy
        
        Args:
            strategy_name: Name of strategy from STRATEGY_REGISTRY
            data_feed: Backtrader data feed
            strategy_params: Strategy parameters override
            run_name: MLflow run name
            log_to_mlflow: Whether to log to MLflow
        
        Returns:
            Dictionary with results and metrics
        """
        logger.info("Starting backtest", strategy=strategy_name, params=strategy_params)
        
        # Get strategy class
        strategy_class = get_strategy(strategy_name)
        
        # Initialize Cerebro
        cerebro = bt.Cerebro()
        
        # Add strategy
        if strategy_params:
            cerebro.addstrategy(strategy_class, **strategy_params)
        else:
            cerebro.addstrategy(strategy_class)
        
        # Add data
        cerebro.adddata(data_feed)
        
        # Set broker parameters
        cerebro.broker.setcash(self.initial_cash)
        cerebro.broker.setcommission(commission=self.commission)
        
        # Add analyzers
        metrics_calculator = PerformanceMetrics(cerebro, strategy_name)
        metrics_calculator.add_analyzers()
        
        # Run backtest
        logger.info("Running backtest...")
        start_time = datetime.now()
        
        results = cerebro.run()
        strat = results[0]
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("Backtest completed", duration_sec=duration)
        
        # Extract metrics
        metrics = metrics_calculator.extract_metrics(strat)
        metrics['strategy_name'] = strategy_name
        metrics['duration_seconds'] = duration
        metrics['strategy_params'] = strategy_params or {}
        
        # Print summary
        metrics_calculator.print_summary(metrics)
        
        # Log to MLflow
        if log_to_mlflow:
            self._log_to_mlflow(
                strategy_name=strategy_name,
                metrics=metrics,
                strategy_params=strategy_params,
                run_name=run_name,
                cerebro=cerebro
            )
        
        return {
            'metrics': metrics,
            'cerebro': cerebro,
            'strategy': strat
        }
    
    def optimize_strategy(
        self,
        strategy_name: str,
        data_feed: bt.feeds.DataBase,
        param_ranges: Dict[str, tuple],
        optimization_metric: str = 'sharpe_ratio',
        log_to_mlflow: bool = True
    ) -> Dict[str, Any]:
        """
        Optimize strategy parameters
        
        Args:
            strategy_name: Name of strategy
            data_feed: Backtrader data feed
            param_ranges: Dict of param_name: (min, max, step)
            optimization_metric: Metric to optimize
            log_to_mlflow: Log results to MLflow
        
        Returns:
            Best parameters and metrics
        """
        logger.info("Starting optimization", strategy=strategy_name, metric=optimization_metric)
        
        strategy_class = get_strategy(strategy_name)
        
        # Initialize Cerebro
        cerebro = bt.Cerebro(optreturn=False)
        
        # Add strategy with optimization ranges
        opt_params = {}
        for param_name, (min_val, max_val, step) in param_ranges.items():
            opt_params[param_name] = range(min_val, max_val + 1, step)
        
        cerebro.optstrategy(strategy_class, **opt_params)
        
        # Add data
        cerebro.adddata(data_feed)
        
        # Set broker
        cerebro.broker.setcash(self.initial_cash)
        cerebro.broker.setcommission(commission=self.commission)
        
        # Add analyzers
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0.02)
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        
        # Run optimization
        logger.info("Running optimization...")
        start_time = datetime.now()
        
        opt_results = cerebro.run()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"Optimization completed in {duration:.2f}s, tested {len(opt_results)} combinations")
        
        # Find best parameters
        best_result = self._find_best_params(opt_results, optimization_metric)
        
        logger.info("Best parameters found", 
                   params=best_result['params'],
                   metric_value=best_result['metric_value'])
        
        # Log to MLflow
        if log_to_mlflow:
            with mlflow.start_run(run_name=f"optimization_{strategy_name}"):
                mlflow.log_params(best_result['params'])
                mlflow.log_metric(optimization_metric, best_result['metric_value'])
                mlflow.log_param("optimization_combinations", len(opt_results))
                mlflow.log_param("optimization_duration_sec", duration)
        
        return best_result
    
    def _find_best_params(self, opt_results: list, metric: str = 'sharpe_ratio') -> Dict[str, Any]:
        """Find best parameters from optimization results"""
        best_value = float('-inf')
        best_params = {}
        
        for result in opt_results:
            strat = result[0]
            
            # Extract metric
            if metric == 'sharpe_ratio':
                value = strat.analyzers.sharpe.get_analysis().get('sharperatio', 0.0) or 0.0
            elif metric == 'return':
                value = strat.analyzers.returns.get_analysis().get('rtot', 0.0)
            elif metric == 'drawdown':
                # For drawdown, lower is better
                dd = strat.analyzers.drawdown.get_analysis().get('max', {}).get('drawdown', 100.0)
                value = -dd  # Negate to make higher better
            else:
                value = 0.0
            
            if value > best_value:
                best_value = value
                # Extract strategy params
                best_params = {}
                for param in strat.params._getpairs():
                    best_params[param[0]] = param[1]
        
        return {
            'params': best_params,
            'metric_value': best_value
        }
    
    def _log_to_mlflow(
        self,
        strategy_name: str,
        metrics: Dict[str, Any],
        strategy_params: Dict[str, Any],
        run_name: Optional[str],
        cerebro: bt.Cerebro
    ):
        """Log backtest results to MLflow"""
        try:
            with mlflow.start_run(run_name=run_name or f"{strategy_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
                # Log parameters
                mlflow.log_param("strategy", strategy_name)
                mlflow.log_param("initial_cash", self.initial_cash)
                mlflow.log_param("commission", self.commission)
                
                if strategy_params:
                    for key, value in strategy_params.items():
                        mlflow.log_param(f"strat_{key}", value)
                
                # Log metrics
                mlflow.log_metric("total_return", metrics['total_return'])
                mlflow.log_metric("return_pct", metrics['return_pct'])
                mlflow.log_metric("sharpe_ratio", metrics['sharpe_ratio'])
                mlflow.log_metric("max_drawdown", metrics['max_drawdown'])
                mlflow.log_metric("win_rate", metrics['win_rate'])
                mlflow.log_metric("total_trades", metrics['total_trades'])
                mlflow.log_metric("profit_factor", metrics['profit_factor'])
                mlflow.log_metric("sqn", metrics['sqn'])
                mlflow.log_metric("vwr", metrics['vwr'])
                mlflow.log_metric("final_value", metrics['final_value'])
                
                # Plot and log chart
                try:
                    fig = cerebro.plot(style='candlestick', barup='green', bardown='red', 
                                      volume=False, figsize=(14, 8))[0][0]
                    plt.savefig('/tmp/backtest_plot.png', dpi=150, bbox_inches='tight')
                    mlflow.log_artifact('/tmp/backtest_plot.png')
                    plt.close(fig)
                except Exception as e:
                    logger.warning(f"Could not generate plot: {e}")
                
                logger.info("Logged to MLflow", run_id=mlflow.active_run().info.run_id)
        
        except Exception as e:
            logger.error("Error logging to MLflow", error=str(e))
    
    @staticmethod
    def compare_strategies(
        results_list: list,
        metric: str = 'sharpe_ratio'
    ) -> pd.DataFrame:
        """
        Compare multiple strategy results
        
        Args:
            results_list: List of result dictionaries from run_backtest
            metric: Metric to sort by
        
        Returns:
            DataFrame with comparison
        """
        import pandas as pd
        
        comparison = []
        for result in results_list:
            metrics = result['metrics']
            comparison.append({
                'Strategy': metrics['strategy_name'],
                'Return %': f"{metrics['return_pct']:.2f}",
                'Sharpe': f"{metrics['sharpe_ratio']:.2f}",
                'Max DD %': f"{metrics['max_drawdown']:.2f}",
                'Win Rate': f"{metrics['win_rate']*100:.1f}",
                'Trades': metrics['total_trades'],
                'Profit Factor': f"{metrics['profit_factor']:.2f}",
                'Final Value': f"${metrics['final_value']:,.0f}"
            })
        
        df = pd.DataFrame(comparison)
        
        # Sort by metric
        if metric in df.columns:
            df = df.sort_values(by=metric, ascending=False)
        
        return df


# Convenience function
def quick_backtest(
    strategy_name: str,
    symbol: str = 'BTCUSDT',
    start_date: str = None,
    end_date: str = None,
    interval: str = '1h',
    initial_cash: float = 100000.0,
    strategy_params: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Quick backtest with default settings
    
    Example:
        results = quick_backtest('ma_cross', 'BTCUSDT', '2023-01-01', '2023-12-31')
    """
    # Load data
    loader = PostgreSQLDataLoader()
    df = loader.load_ohlcv(symbol, start_date, end_date, interval)
    
    if df.empty:
        raise ValueError(f"No data found for {symbol}")
    
    data_feed = create_backtrader_feed(df)
    
    # Run backtest
    engine = BacktestEngine(initial_cash=initial_cash)
    results = engine.run_backtest(strategy_name, data_feed, strategy_params)
    
    return results

