from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataInsufficientError(Exception):
    """Raised when there's insufficient data for analysis."""
    pass


class IsolationForestDetector:
    """
    Anomaly detection using Isolation Forest algorithm.
    Requires minimum 7 days of data as per LLD §16.7.
    """
    
    CONTAMINATION_MAP = {
        "low": 0.02,
        "medium": 0.05,
        "high": 0.1
    }
    
    MIN_DAYS_REQUIRED = 7
    
    def __init__(self):
        self.scaler = StandardScaler()
    
    def detect(
        self,
        df: pd.DataFrame,
        sensitivity: str = "medium",
        device_id: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies using Isolation Forest.
        
        Args:
            df: DataFrame with timestamp and parameter columns
            sensitivity: Detection sensitivity (low, medium, high)
            device_id: Device identifier for logging
            
        Returns:
            List of anomaly dictionaries
            
        Raises:
            DataInsufficientError: If less than 7 days of data
        """
        if df.empty:
            raise DataInsufficientError("No data available")
        
        if "timestamp" in df.columns and len(df) > 1:
            time_span = pd.to_datetime(df["timestamp"]).max() - pd.to_datetime(df["timestamp"]).min()
            days_covered = time_span.total_seconds() / 86400
            if days_covered < self.MIN_DAYS_REQUIRED - 0.1:
                raise DataInsufficientError(
                    f"Need at least {self.MIN_DAYS_REQUIRED} days of data, "
                    f"only {days_covered:.1f} days available"
                )
        elif len(df) < 10:
            raise DataInsufficientError("Insufficient data points")
        
        # Only use numeric columns — exclude timestamp and any string tag columns
        feature_cols = [
            c for c in df.columns
            if c != "timestamp" and pd.api.types.is_numeric_dtype(df[c])
        ]
        
        if not feature_cols:
            raise ValueError("No feature columns found in data")
        
        X = df[feature_cols].copy()
        
        X = X.fillna(method="ffill").fillna(method="bfill")
        
        if X.isnull().all().all():
            logger.warning(f"All data is null for {device_id}")
            raise DataInsufficientError("No valid data points after preprocessing")
        
        X = X.fillna(0)
        
        X_scaled = self.scaler.fit_transform(X)
        
        contamination = self.CONTAMINATION_MAP.get(sensitivity, 0.05)
        
        iso_forest = IsolationForest(
            contamination=contamination,
            n_estimators=100,
            random_state=42,
            n_jobs=-1
        )
        
        predictions = iso_forest.fit_predict(X_scaled)
        scores = iso_forest.decision_function(X_scaled)
        
        anomaly_indices = np.where(predictions == -1)[0]
        
        means = X.mean()
        stds = X.std()
        
        anomalies = []
        for idx in anomaly_indices:
            timestamp = df.iloc[idx]["timestamp"] if "timestamp" in df.columns else None
            
            if pd.isna(timestamp):
                timestamp = datetime.utcnow()
            
            anomalous_params = []
            severities = []
            
            for col in feature_cols:
                value = X.iloc[idx][col]
                mean = means[col]
                std = stds[col]
                
                if std > 0:
                    z_score = abs((value - mean) / std)
                else:
                    z_score = 0
                
                if z_score > 2:
                    anomalous_params.append(col)
                    
                    if z_score > 4:
                        severities.append("high")
                    elif z_score > 3:
                        severities.append("medium")
                    else:
                        severities.append("low")
            
            if not anomalous_params:
                anomalous_params = [feature_cols[0]] if feature_cols else ["unknown"]
                severities = ["medium"]
            
            overall_severity = max(severities, key=lambda s: {"low": 0, "medium": 1, "high": 2}.get(s, 0))
            
            param_str = anomalous_params[0]
            value = X.iloc[idx][param_str]
            mean = means[param_str]
            std = stds[param_str]
            
            if value > mean:
                context = f"{param_str.capitalize()} spike to {value:.1f} (normal: {mean-std:.1f} to {mean+std:.1f})"
            else:
                context = f"{param_str.capitalize()} dropped to {value:.1f} (normal: {mean-std:.1f} to {mean+std:.1f})"
            
            anomaly = {
                "timestamp": timestamp.isoformat() if isinstance(timestamp, datetime) else str(timestamp),
                "severity": overall_severity,
                "parameters": anomalous_params,
                "context": context,
                "raw_score": float(scores[idx]),
                "index": int(idx)
            }
            
            anomalies.append(anomaly)
        
        logger.info(f"Detected {len(anomalies)} anomalies for {device_id}")
        
        return anomalies


isolation_forest_detector = IsolationForestDetector()
