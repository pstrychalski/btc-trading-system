"""
Qdrant Vector Storage
Store and query market state embeddings
"""
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue, Range
)
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
import structlog

logger = structlog.get_logger()


class MarketMemoryStorage:
    """
    Store market states in Qdrant vector database
    """
    
    def __init__(
        self,
        qdrant_url: str = "http://localhost:6333",
        collection_name: str = "market_states"
    ):
        """
        Args:
            qdrant_url: Qdrant server URL
            collection_name: Collection name for market states
        """
        self.client = QdrantClient(url=qdrant_url)
        self.collection_name = collection_name
        
        logger.info("MarketMemoryStorage initialized", url=qdrant_url, collection=collection_name)
    
    def create_collection(self, vector_size: int = 393):
        """
        Create Qdrant collection for market states
        
        Args:
            vector_size: Size of embedding vectors (depends on encoder)
        """
        try:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created collection '{self.collection_name}' with vector size {vector_size}")
        
        except Exception as e:
            logger.warning(f"Collection might already exist: {e}")
    
    def store_market_state(
        self,
        embedding: np.ndarray,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Store a single market state
        
        Args:
            embedding: Vector embedding
            metadata: Market state metadata (timestamp, symbol, ohlcv, indicators, outcome)
        
        Returns:
            Point ID
        """
        point_id = metadata.get('id', str(hash(metadata['timestamp'])))
        
        point = PointStruct(
            id=point_id,
            vector=embedding.tolist(),
            payload=metadata
        )
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
        
        return point_id
    
    def store_batch(
        self,
        embeddings: List[np.ndarray],
        metadata_list: List[Dict[str, Any]]
    ):
        """
        Store multiple market states in batch
        
        Args:
            embeddings: List of embeddings
            metadata_list: List of metadata dicts
        """
        if len(embeddings) != len(metadata_list):
            raise ValueError("Embeddings and metadata lists must have same length")
        
        points = []
        for i, (embedding, metadata) in enumerate(zip(embeddings, metadata_list)):
            point_id = metadata.get('id', f"point_{i}_{int(datetime.now().timestamp())}")
            
            point = PointStruct(
                id=point_id,
                vector=embedding.tolist(),
                payload=metadata
            )
            points.append(point)
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        logger.info(f"Stored {len(points)} market states")
    
    def search_similar(
        self,
        query_vector: np.ndarray,
        limit: int = 10,
        filters: Optional[Filter] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar market states
        
        Args:
            query_vector: Query embedding
            limit: Number of results
            filters: Optional filters (symbol, date range, etc.)
        
        Returns:
            List of similar market states with scores
        """
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector.tolist(),
            limit=limit,
            query_filter=filters
        )
        
        similar_states = []
        for result in results:
            similar_states.append({
                'id': result.id,
                'score': result.score,
                'payload': result.payload
            })
        
        return similar_states
    
    def search_by_outcome(
        self,
        query_vector: np.ndarray,
        outcome_type: str,  # 'profitable', 'unprofitable', 'neutral'
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for similar states filtered by outcome
        
        Args:
            query_vector: Query embedding
            outcome_type: Type of outcome to filter by
            limit: Number of results
        
        Returns:
            Similar states with specified outcome
        """
        filters = Filter(
            must=[
                FieldCondition(
                    key="outcome",
                    match=MatchValue(value=outcome_type)
                )
            ]
        )
        
        return self.search_similar(query_vector, limit, filters)
    
    def search_by_date_range(
        self,
        query_vector: np.ndarray,
        start_date: str,
        end_date: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search within date range
        
        Args:
            query_vector: Query embedding
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            limit: Number of results
        
        Returns:
            Similar states within date range
        """
        filters = Filter(
            must=[
                FieldCondition(
                    key="timestamp",
                    range=Range(
                        gte=start_date,
                        lte=end_date
                    )
                )
            ]
        )
        
        return self.search_similar(query_vector, limit, filters)
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                'name': self.collection_name,
                'vectors_count': info.vectors_count,
                'points_count': info.points_count,
                'status': info.status
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}
    
    def delete_collection(self):
        """Delete the collection (use with caution!)"""
        self.client.delete_collection(self.collection_name)
        logger.warning(f"Deleted collection '{self.collection_name}'")


class RiskAnalyzer:
    """
    Analyze risk based on historical patterns
    """
    
    def __init__(self, storage: MarketMemoryStorage):
        """
        Args:
            storage: MarketMemoryStorage instance
        """
        self.storage = storage
        logger.info("RiskAnalyzer initialized")
    
    def analyze_current_risk(
        self,
        current_embedding: np.ndarray,
        lookback: int = 50
    ) -> Dict[str, Any]:
        """
        Analyze risk of current market state
        
        Process:
        1. Find similar historical patterns
        2. Analyze outcomes of those patterns
        3. Calculate risk metrics
        
        Args:
            current_embedding: Current market state embedding
            lookback: Number of similar patterns to analyze
        
        Returns:
            Risk analysis dict
        """
        # Find similar patterns
        similar_states = self.storage.search_similar(
            current_embedding,
            limit=lookback
        )
        
        if not similar_states:
            return {
                'risk_level': 'unknown',
                'confidence': 0.0,
                'message': 'No historical patterns found'
            }
        
        # Analyze outcomes
        profitable_count = 0
        unprofitable_count = 0
        neutral_count = 0
        
        total_return = 0.0
        max_drawdown_seen = 0.0
        
        for state in similar_states:
            payload = state['payload']
            outcome = payload.get('outcome', 'neutral')
            
            if outcome == 'profitable':
                profitable_count += 1
            elif outcome == 'unprofitable':
                unprofitable_count += 1
            else:
                neutral_count += 1
            
            # Aggregate metrics
            total_return += payload.get('return', 0.0)
            max_dd = payload.get('max_drawdown', 0.0)
            if max_dd > max_drawdown_seen:
                max_drawdown_seen = max_dd
        
        # Calculate risk score
        total_patterns = len(similar_states)
        win_rate = profitable_count / total_patterns if total_patterns > 0 else 0.0
        avg_return = total_return / total_patterns if total_patterns > 0 else 0.0
        
        # Risk level
        if win_rate > 0.6 and avg_return > 0:
            risk_level = 'low'
        elif win_rate > 0.4:
            risk_level = 'medium'
        else:
            risk_level = 'high'
        
        # Confidence based on similarity scores
        avg_similarity = np.mean([s['score'] for s in similar_states])
        confidence = avg_similarity  # 0-1 score
        
        return {
            'risk_level': risk_level,
            'confidence': confidence,
            'win_rate': win_rate,
            'avg_return': avg_return,
            'max_historical_drawdown': max_drawdown_seen,
            'similar_patterns_count': total_patterns,
            'profitable_outcomes': profitable_count,
            'unprofitable_outcomes': unprofitable_count,
            'neutral_outcomes': neutral_count,
            'avg_similarity_score': avg_similarity
        }
    
    def compare_strategies(
        self,
        current_embedding: np.ndarray,
        strategy_names: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compare how different strategies performed in similar market states
        
        Args:
            current_embedding: Current market state
            strategy_names: List of strategy names to compare
        
        Returns:
            Performance comparison by strategy
        """
        results = {}
        
        for strategy in strategy_names:
            # Search for similar states where this strategy was used
            filters = Filter(
                must=[
                    FieldCondition(
                        key="strategy",
                        match=MatchValue(value=strategy)
                    )
                ]
            )
            
            similar_states = self.storage.search_similar(
                current_embedding,
                limit=30,
                filters=filters
            )
            
            if not similar_states:
                results[strategy] = {'message': 'No historical data'}
                continue
            
            # Calculate metrics
            returns = [s['payload'].get('return', 0.0) for s in similar_states]
            outcomes = [s['payload'].get('outcome', 'neutral') for s in similar_states]
            
            results[strategy] = {
                'avg_return': np.mean(returns),
                'win_rate': outcomes.count('profitable') / len(outcomes),
                'sample_size': len(similar_states),
                'avg_similarity': np.mean([s['score'] for s in similar_states])
            }
        
        return results
    
    def get_regime_classification(
        self,
        current_embedding: np.ndarray
    ) -> str:
        """
        Classify current market regime based on historical patterns
        
        Returns:
            Regime name (e.g., 'bull_trending', 'bear_volatile', 'sideways')
        """
        similar_states = self.storage.search_similar(
            current_embedding,
            limit=20
        )
        
        if not similar_states:
            return 'unknown'
        
        # Count regime classifications from similar states
        regimes = [s['payload'].get('regime', 'unknown') for s in similar_states]
        
        # Most common regime
        from collections import Counter
        regime_counts = Counter(regimes)
        most_common_regime = regime_counts.most_common(1)[0][0]
        
        return most_common_regime

