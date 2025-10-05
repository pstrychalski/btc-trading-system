"""
Optuna Optimizer
Advanced walk-forward optimization with MLflow integration
"""
import optuna
import mlflow
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime, timedelta
import structlog
from dataclasses import dataclass

logger = structlog.get_logger()


@dataclass
class OptimizationConfig:
    """Configuration for optimization"""
    n_trials: int = 100
    n_jobs: int = 4
    timeout: Optional[int] = None
    direction: str = "maximize"  # maximize or minimize
    metric: str = "sharpe_ratio"
    study_name: Optional[str] = None
    storage: Optional[str] = None


class WalkForwardOptimizer:
    """
    Walk-Forward Optimization
    
    Splits data into multiple periods:
    - In-Sample (IS): Training period for optimization
    - Out-of-Sample (OOS): Testing period for validation
    
    Process:
    1. Split data into N windows
    2. For each window:
       a. Optimize on IS period
       b. Test on OOS period
       c. Record results
    3. Aggregate results across all windows
    """
    
    def __init__(
        self,
        backtest_func: Callable,
        param_space: Dict[str, Any],
        config: OptimizationConfig = None
    ):
        """
        Args:
            backtest_func: Function that runs backtest, signature: func(params, data) -> metrics
            param_space: Optuna search space definition
            config: Optimization configuration
        """
        self.backtest_func = backtest_func
        self.param_space = param_space
        self.config = config or OptimizationConfig()
        
        # MLflow setup
        mlflow.set_experiment("optuna_walk_forward")
        
        logger.info("WalkForwardOptimizer initialized",
                   n_trials=self.config.n_trials,
                   metric=self.config.metric)
    
    def split_walk_forward(
        self,
        data: pd.DataFrame,
        n_splits: int = 5,
        is_ratio: float = 0.7
    ) -> List[tuple]:
        """
        Split data into walk-forward windows
        
        Args:
            data: DataFrame with datetime index
            n_splits: Number of walk-forward windows
            is_ratio: Ratio of in-sample to total window size
        
        Returns:
            List of (is_data, oos_data) tuples
        """
        total_len = len(data)
        window_size = total_len // n_splits
        is_size = int(window_size * is_ratio)
        oos_size = window_size - is_size
        
        splits = []
        for i in range(n_splits):
            start_idx = i * window_size
            is_end_idx = start_idx + is_size
            oos_end_idx = min(is_end_idx + oos_size, total_len)
            
            if oos_end_idx > total_len:
                break
            
            is_data = data.iloc[start_idx:is_end_idx]
            oos_data = data.iloc[is_end_idx:oos_end_idx]
            
            splits.append((is_data, oos_data))
            
            logger.info(f"Window {i+1}: IS={len(is_data)} bars, OOS={len(oos_data)} bars")
        
        return splits
    
    def optimize_window(
        self,
        is_data: pd.DataFrame,
        oos_data: pd.DataFrame,
        window_idx: int
    ) -> Dict[str, Any]:
        """
        Optimize single walk-forward window
        
        Args:
            is_data: In-sample data
            oos_data: Out-of-sample data
            window_idx: Window index
        
        Returns:
            Results dictionary with best params and metrics
        """
        logger.info(f"Optimizing window {window_idx}...")
        
        # Create objective function
        def objective(trial):
            # Sample parameters from search space
            params = {}
            for param_name, param_config in self.param_space.items():
                if param_config['type'] == 'int':
                    params[param_name] = trial.suggest_int(
                        param_name,
                        param_config['low'],
                        param_config['high'],
                        step=param_config.get('step', 1)
                    )
                elif param_config['type'] == 'float':
                    params[param_name] = trial.suggest_float(
                        param_name,
                        param_config['low'],
                        param_config['high'],
                        log=param_config.get('log', False)
                    )
                elif param_config['type'] == 'categorical':
                    params[param_name] = trial.suggest_categorical(
                        param_name,
                        param_config['choices']
                    )
            
            # Run backtest on IS data
            try:
                metrics = self.backtest_func(params, is_data)
                
                # Extract target metric
                metric_value = metrics.get(self.config.metric, 0.0)
                
                # Log to MLflow
                with mlflow.start_run(nested=True):
                    mlflow.log_params(params)
                    mlflow.log_metrics(metrics)
                    mlflow.log_param("window", window_idx)
                    mlflow.log_param("phase", "in_sample")
                
                return metric_value
            
            except Exception as e:
                logger.error(f"Backtest failed: {e}")
                return float('-inf') if self.config.direction == "maximize" else float('inf')
        
        # Create and run study
        study_name = f"{self.config.study_name}_window_{window_idx}" if self.config.study_name else f"window_{window_idx}"
        
        study = optuna.create_study(
            study_name=study_name,
            direction=self.config.direction,
            storage=self.config.storage,
            load_if_exists=True
        )
        
        study.optimize(
            objective,
            n_trials=self.config.n_trials,
            n_jobs=self.config.n_jobs,
            timeout=self.config.timeout
        )
        
        # Get best parameters
        best_params = study.best_params
        best_is_value = study.best_value
        
        logger.info(f"Best IS {self.config.metric}: {best_is_value:.4f}", params=best_params)
        
        # Test on OOS data
        oos_metrics = self.backtest_func(best_params, oos_data)
        oos_value = oos_metrics.get(self.config.metric, 0.0)
        
        logger.info(f"OOS {self.config.metric}: {oos_value:.4f}")
        
        # Log OOS results to MLflow
        with mlflow.start_run(nested=True):
            mlflow.log_params(best_params)
            mlflow.log_metrics(oos_metrics)
            mlflow.log_param("window", window_idx)
            mlflow.log_param("phase", "out_of_sample")
            mlflow.log_metric("is_metric", best_is_value)
            mlflow.log_metric("oos_metric", oos_value)
            mlflow.log_metric("is_oos_diff", best_is_value - oos_value)
        
        return {
            'window': window_idx,
            'best_params': best_params,
            'is_metric': best_is_value,
            'oos_metric': oos_value,
            'is_oos_diff': best_is_value - oos_value,
            'n_trials': len(study.trials),
            'study': study
        }
    
    def run_walk_forward(
        self,
        data: pd.DataFrame,
        n_splits: int = 5,
        is_ratio: float = 0.7
    ) -> Dict[str, Any]:
        """
        Run complete walk-forward optimization
        
        Args:
            data: Full dataset
            n_splits: Number of walk-forward windows
            is_ratio: In-sample ratio
        
        Returns:
            Aggregated results across all windows
        """
        with mlflow.start_run(run_name=f"walk_forward_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
            # Split data
            splits = self.split_walk_forward(data, n_splits, is_ratio)
            
            # Optimize each window
            results = []
            for i, (is_data, oos_data) in enumerate(splits):
                window_result = self.optimize_window(is_data, oos_data, i+1)
                results.append(window_result)
            
            # Aggregate results
            avg_is_metric = np.mean([r['is_metric'] for r in results])
            avg_oos_metric = np.mean([r['oos_metric'] for r in results])
            avg_diff = np.mean([r['is_oos_diff'] for r in results])
            
            # Check for overfitting
            overfit_ratio = (avg_is_metric - avg_oos_metric) / avg_is_metric if avg_is_metric != 0 else 0
            
            # Find most consistent parameters
            # (parameters that performed well across multiple windows)
            all_params = [r['best_params'] for r in results]
            param_frequency = {}
            for params in all_params:
                params_tuple = tuple(sorted(params.items()))
                param_frequency[params_tuple] = param_frequency.get(params_tuple, 0) + 1
            
            most_common_params = max(param_frequency.items(), key=lambda x: x[1])
            robust_params = dict(most_common_params[0])
            
            summary = {
                'n_windows': len(results),
                'avg_is_metric': avg_is_metric,
                'avg_oos_metric': avg_oos_metric,
                'avg_is_oos_diff': avg_diff,
                'overfit_ratio': overfit_ratio,
                'robust_params': robust_params,
                'window_results': results
            }
            
            # Log summary to MLflow
            mlflow.log_param("n_windows", len(results))
            mlflow.log_metric("avg_is_metric", avg_is_metric)
            mlflow.log_metric("avg_oos_metric", avg_oos_metric)
            mlflow.log_metric("avg_is_oos_diff", avg_diff)
            mlflow.log_metric("overfit_ratio", overfit_ratio)
            mlflow.log_params(robust_params)
            
            logger.info("Walk-forward optimization complete",
                       avg_oos_metric=f"{avg_oos_metric:.4f}",
                       overfit_ratio=f"{overfit_ratio:.2%}")
            
            return summary


class MultiObjectiveOptimizer:
    """
    Multi-Objective Optimization
    Optimize multiple metrics simultaneously (e.g., return vs risk)
    """
    
    def __init__(
        self,
        backtest_func: Callable,
        param_space: Dict[str, Any],
        objectives: List[str],
        directions: List[str],
        n_trials: int = 100
    ):
        """
        Args:
            backtest_func: Backtest function
            param_space: Parameter search space
            objectives: List of metric names to optimize
            directions: List of 'maximize' or 'minimize' for each objective
            n_trials: Number of trials
        """
        self.backtest_func = backtest_func
        self.param_space = param_space
        self.objectives = objectives
        self.directions = directions
        self.n_trials = n_trials
        
        mlflow.set_experiment("optuna_multi_objective")
        
        logger.info("MultiObjectiveOptimizer initialized",
                   objectives=objectives,
                   directions=directions)
    
    def optimize(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Run multi-objective optimization
        
        Returns:
            Pareto front solutions
        """
        def objective(trial):
            # Sample parameters
            params = {}
            for param_name, param_config in self.param_space.items():
                if param_config['type'] == 'int':
                    params[param_name] = trial.suggest_int(
                        param_name,
                        param_config['low'],
                        param_config['high']
                    )
                elif param_config['type'] == 'float':
                    params[param_name] = trial.suggest_float(
                        param_name,
                        param_config['low'],
                        param_config['high']
                    )
            
            # Run backtest
            metrics = self.backtest_func(params, data)
            
            # Return multiple objectives
            return tuple(metrics.get(obj, 0.0) for obj in self.objectives)
        
        # Create multi-objective study
        study = optuna.create_study(
            directions=self.directions,
            study_name=f"multi_obj_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        study.optimize(objective, n_trials=self.n_trials)
        
        # Get Pareto front
        pareto_trials = [trial for trial in study.best_trials]
        
        logger.info(f"Found {len(pareto_trials)} Pareto optimal solutions")
        
        # Log to MLflow
        with mlflow.start_run():
            mlflow.log_param("n_pareto_solutions", len(pareto_trials))
            
            for i, trial in enumerate(pareto_trials):
                with mlflow.start_run(nested=True, run_name=f"pareto_{i+1}"):
                    mlflow.log_params(trial.params)
                    for obj_name, obj_value in zip(self.objectives, trial.values):
                        mlflow.log_metric(obj_name, obj_value)
        
        return {
            'n_solutions': len(pareto_trials),
            'pareto_trials': pareto_trials,
            'study': study
        }


def suggest_params_from_space(trial: optuna.Trial, param_space: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to suggest parameters from space definition"""
    params = {}
    for param_name, config in param_space.items():
        if config['type'] == 'int':
            params[param_name] = trial.suggest_int(
                param_name,
                config['low'],
                config['high'],
                step=config.get('step', 1)
            )
        elif config['type'] == 'float':
            params[param_name] = trial.suggest_float(
                param_name,
                config['low'],
                config['high'],
                log=config.get('log', False)
            )
        elif config['type'] == 'categorical':
            params[param_name] = trial.suggest_categorical(
                param_name,
                config['choices']
            )
    return params

