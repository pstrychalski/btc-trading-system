"""
Market State Embeddings
Convert market data into vector embeddings for similarity search
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
from sentence_transformers import SentenceTransformer
import structlog

logger = structlog.get_logger()


class MarketStateEncoder:
    """
    Encode market states into vector embeddings
    
    Methods:
    1. Statistical Features: OHLCV + indicators
    2. Semantic Embeddings: Text descriptions via transformer models
    3. Hybrid: Combine both approaches
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Args:
            model_name: Sentence transformer model for semantic embeddings
        """
        self.model = SentenceTransformer(model_name)
        self.feature_names = []
        
        logger.info("MarketStateEncoder initialized", model=model_name)
    
    def extract_statistical_features(self, ohlcv: pd.Series) -> np.ndarray:
        """
        Extract statistical features from OHLCV data
        
        Features:
        - Price levels (normalized)
        - Price changes (returns)
        - Volume
        - Volatility indicators
        - Trend indicators
        
        Args:
            ohlcv: Series with open, high, low, close, volume
        
        Returns:
            Feature vector
        """
        features = []
        
        # Price levels (normalized by close)
        close = ohlcv['close']
        features.append(ohlcv['open'] / close)
        features.append(ohlcv['high'] / close)
        features.append(ohlcv['low'] / close)
        features.append(1.0)  # close / close
        
        # Volume (log-normalized)
        features.append(np.log1p(ohlcv['volume']))
        
        # Price range
        features.append((ohlcv['high'] - ohlcv['low']) / close)
        
        # Body size
        features.append(abs(ohlcv['close'] - ohlcv['open']) / close)
        
        # Upper/Lower shadows
        if ohlcv['close'] > ohlcv['open']:  # Bullish
            features.append((ohlcv['high'] - ohlcv['close']) / close)  # Upper shadow
            features.append((ohlcv['open'] - ohlcv['low']) / close)    # Lower shadow
        else:  # Bearish
            features.append((ohlcv['high'] - ohlcv['open']) / close)
            features.append((ohlcv['close'] - ohlcv['low']) / close)
        
        return np.array(features, dtype=np.float32)
    
    def extract_window_features(self, ohlcv_window: pd.DataFrame) -> np.ndarray:
        """
        Extract features from a window of OHLCV data
        
        Args:
            ohlcv_window: DataFrame with multiple candles
        
        Returns:
            Feature vector
        """
        features = []
        
        # Returns over window
        returns = ohlcv_window['close'].pct_change().dropna()
        features.extend([
            returns.mean(),
            returns.std(),
            returns.skew(),
            returns.kurt()
        ])
        
        # Volume profile
        features.extend([
            ohlcv_window['volume'].mean(),
            ohlcv_window['volume'].std()
        ])
        
        # Volatility (ATR-like)
        high_low = ohlcv_window['high'] - ohlcv_window['low']
        features.append(high_low.mean() / ohlcv_window['close'].mean())
        
        # Trend strength
        price_change = (ohlcv_window['close'].iloc[-1] - ohlcv_window['close'].iloc[0])
        features.append(price_change / ohlcv_window['close'].iloc[0])
        
        # Recent momentum
        if len(ohlcv_window) >= 5:
            recent_returns = returns.tail(5).sum()
            features.append(recent_returns)
        else:
            features.append(0.0)
        
        return np.array(features, dtype=np.float32)
    
    def create_market_description(self, ohlcv: pd.Series, indicators: Dict[str, float] = None) -> str:
        """
        Create natural language description of market state
        
        Args:
            ohlcv: OHLCV data
            indicators: Optional technical indicators
        
        Returns:
            Text description
        """
        price_change = ((ohlcv['close'] - ohlcv['open']) / ohlcv['open']) * 100
        
        # Trend
        if price_change > 2:
            trend = "strong bullish"
        elif price_change > 0.5:
            trend = "bullish"
        elif price_change < -2:
            trend = "strong bearish"
        elif price_change < -0.5:
            trend = "bearish"
        else:
            trend = "neutral"
        
        # Volatility
        range_pct = ((ohlcv['high'] - ohlcv['low']) / ohlcv['close']) * 100
        if range_pct > 3:
            volatility = "high volatility"
        elif range_pct > 1:
            volatility = "moderate volatility"
        else:
            volatility = "low volatility"
        
        # Volume
        volume_desc = "high volume" if ohlcv.get('volume', 0) > 0 else "normal volume"
        
        description = f"Market showing {trend} movement with {volatility} and {volume_desc}. "
        description += f"Price range from {ohlcv['low']:.2f} to {ohlcv['high']:.2f}. "
        
        if indicators:
            if 'rsi' in indicators:
                rsi = indicators['rsi']
                if rsi > 70:
                    description += "RSI indicates overbought conditions. "
                elif rsi < 30:
                    description += "RSI indicates oversold conditions. "
            
            if 'macd' in indicators:
                description += f"MACD signal at {indicators['macd']:.2f}. "
        
        return description
    
    def encode_semantic(self, description: str) -> np.ndarray:
        """
        Encode text description into semantic embedding
        
        Args:
            description: Natural language description
        
        Returns:
            Embedding vector
        """
        embedding = self.model.encode(description, convert_to_numpy=True)
        return embedding.astype(np.float32)
    
    def encode_hybrid(
        self,
        ohlcv: pd.Series,
        ohlcv_window: pd.DataFrame = None,
        indicators: Dict[str, float] = None
    ) -> np.ndarray:
        """
        Create hybrid embedding combining statistical and semantic features
        
        Args:
            ohlcv: Current candle
            ohlcv_window: Window of recent candles
            indicators: Technical indicators
        
        Returns:
            Hybrid embedding vector
        """
        # Statistical features
        stat_features = self.extract_statistical_features(ohlcv)
        
        if ohlcv_window is not None and len(ohlcv_window) > 1:
            window_features = self.extract_window_features(ohlcv_window)
            stat_features = np.concatenate([stat_features, window_features])
        
        # Semantic features
        description = self.create_market_description(ohlcv, indicators)
        semantic_features = self.encode_semantic(description)
        
        # Combine (concatenate)
        hybrid = np.concatenate([stat_features, semantic_features])
        
        return hybrid.astype(np.float32)
    
    def batch_encode(
        self,
        ohlcv_data: pd.DataFrame,
        window_size: int = 10,
        use_semantic: bool = True
    ) -> List[np.ndarray]:
        """
        Encode multiple market states in batch
        
        Args:
            ohlcv_data: DataFrame with OHLCV data
            window_size: Size of rolling window for context
            use_semantic: Whether to include semantic features
        
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        for i in range(window_size, len(ohlcv_data)):
            current = ohlcv_data.iloc[i]
            window = ohlcv_data.iloc[i-window_size:i]
            
            if use_semantic:
                embedding = self.encode_hybrid(current, window)
            else:
                stat_features = self.extract_statistical_features(current)
                window_features = self.extract_window_features(window)
                embedding = np.concatenate([stat_features, window_features])
            
            embeddings.append(embedding)
        
        logger.info(f"Encoded {len(embeddings)} market states")
        
        return embeddings


class MarketPatternMatcher:
    """
    Match current market state to historical patterns
    """
    
    def __init__(self):
        self.encoder = MarketStateEncoder()
    
    def find_similar_patterns(
        self,
        current_state: np.ndarray,
        historical_embeddings: List[np.ndarray],
        top_k: int = 10
    ) -> List[int]:
        """
        Find most similar historical patterns
        
        Args:
            current_state: Current market embedding
            historical_embeddings: List of historical embeddings
            top_k: Number of similar patterns to return
        
        Returns:
            Indices of most similar patterns
        """
        # Cosine similarity
        similarities = []
        for hist_emb in historical_embeddings:
            sim = np.dot(current_state, hist_emb) / (
                np.linalg.norm(current_state) * np.linalg.norm(hist_emb)
            )
            similarities.append(sim)
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        return top_indices.tolist()
    
    def cluster_patterns(
        self,
        embeddings: List[np.ndarray],
        n_clusters: int = 10
    ) -> np.ndarray:
        """
        Cluster market patterns
        
        Args:
            embeddings: List of embeddings
            n_clusters: Number of clusters
        
        Returns:
            Cluster labels
        """
        from sklearn.cluster import KMeans
        
        X = np.array(embeddings)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        labels = kmeans.fit_predict(X)
        
        logger.info(f"Clustered {len(embeddings)} patterns into {n_clusters} clusters")
        
        return labels

