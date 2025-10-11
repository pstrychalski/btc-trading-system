"""
Data Validation Service using Great Expectations
Validates incoming market data for quality and consistency
"""

import os
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
import structlog

import great_expectations as gx
from great_expectations.core import ExpectationSuite
from great_expectations.checkpoint import Checkpoint

logger = structlog.get_logger()


class MarketDataValidator:
    """
    Validates market data using Great Expectations
    """
    
    def __init__(self):
        """Initialize Great Expectations context and expectations"""
        self.context = gx.get_context()
        self.setup_expectations()
        logger.info("MarketDataValidator initialized")
    
    def setup_expectations(self):
        """
        Define data quality expectations for market data
        """
        try:
            # Try to get existing suite
            self.suite = self.context.get_expectation_suite("market_data_suite")
            logger.info("Loaded existing expectation suite")
        except:
            # Create new suite
            self.suite = self.context.add_expectation_suite("market_data_suite")
            logger.info("Created new expectation suite")
            
            # Define expectations
            self._define_ohlcv_expectations()
            self._define_orderbook_expectations()
            self._define_trade_expectations()
            
            logger.info("Expectations configured", suite_name="market_data_suite")
    
    def _define_ohlcv_expectations(self):
        """Define expectations for OHLCV data"""
        
        # Price expectations
        expectations = [
            # Columns must exist
            {
                "expectation_type": "expect_column_to_exist",
                "kwargs": {"column": "timestamp"}
            },
            {
                "expectation_type": "expect_column_to_exist",
                "kwargs": {"column": "open"}
            },
            {
                "expectation_type": "expect_column_to_exist",
                "kwargs": {"column": "high"}
            },
            {
                "expectation_type": "expect_column_to_exist",
                "kwargs": {"column": "low"}
            },
            {
                "expectation_type": "expect_column_to_exist",
                "kwargs": {"column": "close"}
            },
            {
                "expectation_type": "expect_column_to_exist",
                "kwargs": {"column": "volume"}
            },
            
            # No null values in critical columns
            {
                "expectation_type": "expect_column_values_to_not_be_null",
                "kwargs": {"column": "timestamp"}
            },
            {
                "expectation_type": "expect_column_values_to_not_be_null",
                "kwargs": {"column": "close"}
            },
            {
                "expectation_type": "expect_column_values_to_not_be_null",
                "kwargs": {"column": "volume"}
            },
            
            # Price values must be positive
            {
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {
                    "column": "open",
                    "min_value": 0,
                    "max_value": 1000000
                }
            },
            {
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {
                    "column": "high",
                    "min_value": 0,
                    "max_value": 1000000
                }
            },
            {
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {
                    "column": "low",
                    "min_value": 0,
                    "max_value": 1000000
                }
            },
            {
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {
                    "column": "close",
                    "min_value": 0,
                    "max_value": 1000000
                }
            },
            
            # Volume must be non-negative
            {
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {
                    "column": "volume",
                    "min_value": 0
                }
            },
            
            # Timestamp should be unique (for same timeframe)
            {
                "expectation_type": "expect_column_values_to_be_unique",
                "kwargs": {"column": "timestamp"}
            },
            
            # OHLC relationship: High >= Low, High >= Open, High >= Close, Low <= Open, Low <= Close
            # Note: These are custom expectations that might need to be added separately
        ]
        
        for exp in expectations:
            try:
                # Use the new Great Expectations API
                expectation_type = exp["expectation_type"]
                kwargs = exp["kwargs"]
                
                if expectation_type == "expect_column_to_exist":
                    self.suite.add_expectation(
                        gx.expectations.ExpectColumnToExist(**kwargs)
                    )
                elif expectation_type == "expect_column_values_to_not_be_null":
                    self.suite.add_expectation(
                        gx.expectations.ExpectColumnValuesToNotBeNull(**kwargs)
                    )
                elif expectation_type == "expect_column_values_to_be_between":
                    self.suite.add_expectation(
                        gx.expectations.ExpectColumnValuesToBeBetween(**kwargs)
                    )
                elif expectation_type == "expect_column_values_to_be_unique":
                    self.suite.add_expectation(
                        gx.expectations.ExpectColumnValuesToBeUnique(**kwargs)
                    )
            except Exception as e:
                logger.warning(f"Failed to add expectation: {exp['expectation_type']}", error=str(e))
    
    def _define_orderbook_expectations(self):
        """Define expectations for orderbook data"""
        
        expectations = [
            # Required columns
            {
                "expectation_type": "expect_column_to_exist",
                "kwargs": {"column": "bids"}
            },
            {
                "expectation_type": "expect_column_to_exist",
                "kwargs": {"column": "asks"}
            },
            
            # Imbalance must be between -1 and 1
            {
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {
                    "column": "imbalance",
                    "min_value": -1,
                    "max_value": 1
                }
            },
        ]
        
        for exp in expectations:
            try:
                # Use the new Great Expectations API
                expectation_type = exp["expectation_type"]
                kwargs = exp["kwargs"]
                
                if expectation_type == "expect_column_to_exist":
                    self.suite.add_expectation(
                        gx.expectations.ExpectColumnToExist(**kwargs)
                    )
                elif expectation_type == "expect_column_values_to_not_be_null":
                    self.suite.add_expectation(
                        gx.expectations.ExpectColumnValuesToNotBeNull(**kwargs)
                    )
                elif expectation_type == "expect_column_values_to_be_between":
                    self.suite.add_expectation(
                        gx.expectations.ExpectColumnValuesToBeBetween(**kwargs)
                    )
                elif expectation_type == "expect_column_values_to_be_unique":
                    self.suite.add_expectation(
                        gx.expectations.ExpectColumnValuesToBeUnique(**kwargs)
                    )
            except Exception as e:
                logger.warning(f"Failed to add expectation: {exp['expectation_type']}", error=str(e))
    
    def _define_trade_expectations(self):
        """Define expectations for trade data"""
        
        expectations = [
            # Trade price must be positive
            {
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {
                    "column": "price",
                    "min_value": 0
                }
            },
            
            # Trade amount must be positive
            {
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {
                    "column": "amount",
                    "min_value": 0
                }
            },
        ]
        
        for exp in expectations:
            try:
                # Use the new Great Expectations API
                expectation_type = exp["expectation_type"]
                kwargs = exp["kwargs"]
                
                if expectation_type == "expect_column_to_exist":
                    self.suite.add_expectation(
                        gx.expectations.ExpectColumnToExist(**kwargs)
                    )
                elif expectation_type == "expect_column_values_to_not_be_null":
                    self.suite.add_expectation(
                        gx.expectations.ExpectColumnValuesToNotBeNull(**kwargs)
                    )
                elif expectation_type == "expect_column_values_to_be_between":
                    self.suite.add_expectation(
                        gx.expectations.ExpectColumnValuesToBeBetween(**kwargs)
                    )
                elif expectation_type == "expect_column_values_to_be_unique":
                    self.suite.add_expectation(
                        gx.expectations.ExpectColumnValuesToBeUnique(**kwargs)
                    )
            except Exception as e:
                logger.warning(f"Failed to add expectation: {exp['expectation_type']}", error=str(e))
    
    def validate_ohlcv(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate OHLCV data
        
        Args:
            data: DataFrame with columns: timestamp, open, high, low, close, volume
            
        Returns:
            Validation results dictionary
        """
        try:
            # Additional OHLC logic validation
            ohlc_valid = self._validate_ohlc_logic(data)
            
            if not ohlc_valid['valid']:
                logger.warning("OHLC logic validation failed", errors=ohlc_valid['errors'])
            
            # Validate with Great Expectations
            validator = self.context.sources.pandas_default.read_dataframe(data)
            validator.expectation_suite_name = "market_data_suite"
            
            results = validator.validate()
            
            return {
                'valid': results.success and ohlc_valid['valid'],
                'ge_success': results.success,
                'ohlc_logic_valid': ohlc_valid['valid'],
                'statistics': results.statistics,
                'results': [
                    {
                        'expectation_type': r.expectation_config.expectation_type,
                        'success': r.success,
                        'result': r.result
                    }
                    for r in results.results
                ],
                'ohlc_errors': ohlc_valid.get('errors', []),
                'validated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Validation failed", error=str(e))
            return {
                'valid': False,
                'error': str(e),
                'validated_at': datetime.now().isoformat()
            }
    
    def _validate_ohlc_logic(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate OHLC logic rules:
        - High >= Low
        - High >= Open
        - High >= Close
        - Low <= Open
        - Low <= Close
        """
        errors = []
        
        if 'high' in data.columns and 'low' in data.columns:
            invalid_hl = data[data['high'] < data['low']]
            if len(invalid_hl) > 0:
                errors.append(f"Found {len(invalid_hl)} rows where high < low")
        
        if 'high' in data.columns and 'open' in data.columns:
            invalid_ho = data[data['high'] < data['open']]
            if len(invalid_ho) > 0:
                errors.append(f"Found {len(invalid_ho)} rows where high < open")
        
        if 'high' in data.columns and 'close' in data.columns:
            invalid_hc = data[data['high'] < data['close']]
            if len(invalid_hc) > 0:
                errors.append(f"Found {len(invalid_hc)} rows where high < close")
        
        if 'low' in data.columns and 'open' in data.columns:
            invalid_lo = data[data['low'] > data['open']]
            if len(invalid_lo) > 0:
                errors.append(f"Found {len(invalid_lo)} rows where low > open")
        
        if 'low' in data.columns and 'close' in data.columns:
            invalid_lc = data[data['low'] > data['close']]
            if len(invalid_lc) > 0:
                errors.append(f"Found {len(invalid_lc)} rows where low > close")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def validate_price_change(self, data: pd.DataFrame, max_change_percent: float = 50.0) -> Dict[str, Any]:
        """
        Validate that price changes are reasonable (detect anomalies)
        
        Args:
            data: DataFrame with 'close' column
            max_change_percent: Maximum allowed price change percentage
            
        Returns:
            Validation results
        """
        try:
            if len(data) < 2:
                return {'valid': True, 'message': 'Not enough data points'}
            
            # Calculate percentage changes
            data_copy = data.copy()
            data_copy['pct_change'] = data_copy['close'].pct_change() * 100
            
            # Find anomalies
            anomalies = data_copy[abs(data_copy['pct_change']) > max_change_percent]
            
            if len(anomalies) > 0:
                logger.warning(
                    "Price change anomalies detected",
                    count=len(anomalies),
                    max_change=float(anomalies['pct_change'].abs().max())
                )
                
                return {
                    'valid': False,
                    'anomalies_count': len(anomalies),
                    'max_change_percent': float(anomalies['pct_change'].abs().max()),
                    'anomalies': anomalies[['timestamp', 'close', 'pct_change']].to_dict('records')
                }
            
            return {
                'valid': True,
                'max_change_percent': float(data_copy['pct_change'].abs().max()) if len(data_copy) > 0 else 0
            }
            
        except Exception as e:
            logger.error("Price change validation failed", error=str(e))
            return {'valid': False, 'error': str(e)}
    
    def detect_data_drift(self, current_data: pd.DataFrame, reference_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect data drift by comparing current data to reference distribution
        
        Args:
            current_data: Current data sample
            reference_data: Historical reference data
            
        Returns:
            Drift detection results
        """
        try:
            drift_detected = False
            drift_details = {}
            
            # Compare distributions for key metrics
            for column in ['close', 'volume']:
                if column in current_data.columns and column in reference_data.columns:
                    current_mean = current_data[column].mean()
                    reference_mean = reference_data[column].mean()
                    
                    current_std = current_data[column].std()
                    reference_std = reference_data[column].std()
                    
                    # Simple drift check: >20% change in mean or std
                    mean_change = abs((current_mean - reference_mean) / reference_mean) * 100
                    std_change = abs((current_std - reference_std) / reference_std) * 100 if reference_std > 0 else 0
                    
                    if mean_change > 20 or std_change > 20:
                        drift_detected = True
                        drift_details[column] = {
                            'mean_change_percent': float(mean_change),
                            'std_change_percent': float(std_change)
                        }
            
            return {
                'drift_detected': drift_detected,
                'details': drift_details
            }
            
        except Exception as e:
            logger.error("Drift detection failed", error=str(e))
            return {'drift_detected': False, 'error': str(e)}


# Singleton instance
_validator_instance = None

def get_validator() -> MarketDataValidator:
    """Get singleton validator instance"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = MarketDataValidator()
    return _validator_instance

