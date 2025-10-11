"""
Database operations for Data Validation Service
Stores validation results in PostgreSQL
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import structlog

logger = structlog.get_logger()

Base = declarative_base()


class ValidationResult(Base):
    """Table for storing validation results"""
    __tablename__ = 'data_validation_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(100), unique=True, nullable=False)
    data_asset_name = Column(String(200), nullable=False)
    expectation_suite_name = Column(String(200), nullable=False)
    run_time = Column(DateTime, nullable=False)
    success = Column(Boolean, nullable=False)
    statistics = Column(JSON)
    results = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)


class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database manager
        
        Args:
            database_url: PostgreSQL connection string
        """
        self.database_url = database_url or os.getenv(
            'DATABASE_URL',
            'postgresql://trading_user:changeme123@localhost:5432/trading_db'
        )
        
        try:
            self.engine = create_engine(self.database_url)
            self.SessionLocal = sessionmaker(bind=self.engine)
            
            # Create tables if they don't exist
            Base.metadata.create_all(self.engine)
            
            logger.info("Database connection established", url=self._mask_password(self.database_url))
        except Exception as e:
            logger.error("Failed to connect to database", error=str(e))
            raise
    
    def _mask_password(self, url: str) -> str:
        """Mask password in connection string for logging"""
        if '@' in url and ':' in url:
            parts = url.split('@')
            credentials = parts[0].split(':')
            if len(credentials) >= 3:
                credentials[2] = '***'
                parts[0] = ':'.join(credentials)
                return '@'.join(parts)
        return url
    
    def store_validation_result(self, result: Dict[str, Any]) -> bool:
        """
        Store validation result in database
        
        Args:
            result: Validation result dictionary
            
        Returns:
            True if stored successfully
        """
        session = self.SessionLocal()
        
        try:
            validation_record = ValidationResult(
                run_id=result.get('run_id', f"validation_{datetime.now().isoformat()}"),
                data_asset_name=result.get('data_asset_name', 'market_data'),
                expectation_suite_name=result.get('suite_name', 'market_data_suite'),
                run_time=datetime.fromisoformat(result.get('validated_at', datetime.now().isoformat())),
                success=result.get('valid', False),
                statistics=result.get('statistics'),
                results=result.get('results')
            )
            
            session.add(validation_record)
            session.commit()
            
            logger.info(
                "Validation result stored",
                run_id=validation_record.run_id,
                success=validation_record.success
            )
            
            return True
            
        except Exception as e:
            session.rollback()
            logger.error("Failed to store validation result", error=str(e))
            return False
            
        finally:
            session.close()
    
    def get_validation_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get validation statistics for the last N hours
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Statistics dictionary
        """
        session = self.SessionLocal()
        
        try:
            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            total_validations = session.query(ValidationResult).filter(
                ValidationResult.run_time >= cutoff_time
            ).count()
            
            successful_validations = session.query(ValidationResult).filter(
                ValidationResult.run_time >= cutoff_time,
                ValidationResult.success == True
            ).count()
            
            failed_validations = total_validations - successful_validations
            
            success_rate = (successful_validations / total_validations * 100) if total_validations > 0 else 0
            
            return {
                'time_window_hours': hours,
                'total_validations': total_validations,
                'successful_validations': successful_validations,
                'failed_validations': failed_validations,
                'success_rate_percent': round(success_rate, 2)
            }
            
        except Exception as e:
            logger.error("Failed to get validation stats", error=str(e))
            return {
                'error': str(e),
                'time_window_hours': hours
            }
            
        finally:
            session.close()
    
    def get_recent_failures(self, limit: int = 10) -> list:
        """
        Get recent validation failures
        
        Args:
            limit: Maximum number of failures to return
            
        Returns:
            List of recent failures
        """
        session = self.SessionLocal()
        
        try:
            failures = session.query(ValidationResult).filter(
                ValidationResult.success == False
            ).order_by(
                ValidationResult.run_time.desc()
            ).limit(limit).all()
            
            return [
                {
                    'run_id': f.run_id,
                    'data_asset': f.data_asset_name,
                    'run_time': f.run_time.isoformat(),
                    'results': f.results
                }
                for f in failures
            ]
            
        except Exception as e:
            logger.error("Failed to get recent failures", error=str(e))
            return []
            
        finally:
            session.close()


# Singleton instance
_db_manager = None

def get_db_manager() -> DatabaseManager:
    """Get singleton database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager

