import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """
    Extract features for failure prediction ML model.
    Creates rolling statistics and rate of change features.
    """
    
    def extract_features(
        self,
        df: pd.DataFrame,
        target_parameters: List[str] = None
    ) -> pd.DataFrame:
        """
        Extract features from raw telemetry data.
        
        Args:
            df: DataFrame with timestamp and parameter columns
            target_parameters: List of parameters to extract features from
            
        Returns:
            DataFrame with extracted features
        """
        if df.empty:
            return df
        
        feature_cols = [c for c in df.columns if c != "timestamp"]
        
        if target_parameters:
            feature_cols = [c for c in feature_cols if c in target_parameters]
        
        if not feature_cols:
            logger.warning("No valid feature columns found")
            return df
        
        X = df[feature_cols].copy()
        X = X.fillna(method="ffill").fillna(method="bfill").fillna(0)
        
        features = pd.DataFrame()
        
        for col in feature_cols:
            col_data = X[col]
            
            for window in [1, 6, 24]:
                window_str = f"{window}h"
                
                rolling_mean = col_data.rolling(
                    window=window * 60,
                    min_periods=1
                ).mean()
                features[f"{col}_rolling_mean_{window_str}"] = rolling_mean
                
                rolling_std = col_data.rolling(
                    window=window * 60,
                    min_periods=1
                ).std().fillna(0)
                features[f"{col}_rolling_std_{window_str}"] = rolling_std
            
            diff_1h = col_data.diff(periods=60).fillna(0)
            features[f"{col}_rate_of_change_1h"] = diff_1h
            
            features[col] = col_data
        
        features["timestamp"] = df["timestamp"]
        
        logger.info(f"Extracted {len(features.columns)} features from {len(feature_cols)} parameters")
        
        return features
    
    def compute_correlations(
        self,
        df: pd.DataFrame,
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Compute cross-parameter correlations.
        
        Args:
            df: DataFrame with feature columns
            top_n: Number of top correlations to return
            
        Returns:
            List of correlation dictionaries
        """
        feature_cols = [c for c in df.columns if c != "timestamp"]
        
        if len(feature_cols) < 2:
            return []
        
        corr_matrix = df[feature_cols].corr()
        
        correlations = []
        for i in range(len(feature_cols)):
            for j in range(i + 1, len(feature_cols)):
                param1 = feature_cols[i]
                param2 = feature_cols[j]
                corr = corr_matrix.iloc[i, j]
                
                if abs(corr) > 0.5:
                    correlations.append({
                        "parameter_1": param1,
                        "parameter_2": param2,
                        "correlation": float(corr)
                    })
        
        correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        
        return correlations[:top_n]
    
    def create_synthetic_labels(
        self,
        df: pd.DataFrame,
        anomaly_indices: List[int] = None
    ) -> pd.Series:
        """
        Create synthetic labels for failure prediction.
        
        Mark points as "pre-failure" if they are anomalous
        and occur 24-48 hours before data gaps.
        
        Args:
            df: DataFrame with features
            anomaly_indices: Indices of known anomalous points
            
        Returns:
            Series with labels (0=normal, 1=pre-failure)
        """
        n = len(df)
        labels = pd.Series([0] * n, index=df.index)
        
        if anomaly_indices:
            for idx in anomaly_indices:
                labels.iloc[idx] = 1
        
        gap_threshold = 60 * 60 * 2
        
        if "timestamp" in df.columns:
            timestamps = pd.to_datetime(df["timestamp"])
            
            for i in range(1, len(timestamps)):
                time_diff = (timestamps.iloc[i] - timestamps.iloc[i-1]).total_seconds()
                
                if time_diff > gap_threshold:
                    labels.iloc[max(0, i-48):i] = 1
        
        logger.info(f"Created synthetic labels: {labels.sum()} pre-failure points out of {n}")
        
        return labels
    
    def compute_feature_importance_context(
        self,
        feature_names: List[str],
        importance_scores: np.ndarray
    ) -> List[Dict[str, Any]]:
        """
        Convert raw feature importance to context-rich information.
        
        Args:
            feature_names: List of feature names
            importance_scores: Array of importance scores
            
        Returns:
            List of feature importance with context
        """
        importance_map = dict(zip(feature_names, importance_scores))
        
        total = sum(importance_scores)
        
        risk_factors = []
        
        for feat, score in sorted(importance_map.items(), key=lambda x: x[1], reverse=True)[:5]:
            contribution = (score / total * 100) if total > 0 else 0
            
            param = feat.split("_rolling")[0] if "_rolling" in feat else feat.split("_rate")[0]
            
            if "increasing" in feat or "rate_of_change" in feat:
                trend = "increasing"
            elif "decreasing" in feat:
                trend = "decreasing"
            else:
                trend = "stable"
            
            context = f"{param} feature shows {contribution:.1f}% importance"
            
            risk_factors.append({
                "parameter": param,
                "contribution_pct": round(contribution, 1),
                "trend": trend,
                "context": context,
                "feature": feat
            })
        
        return risk_factors


feature_extractor = FeatureExtractor()
