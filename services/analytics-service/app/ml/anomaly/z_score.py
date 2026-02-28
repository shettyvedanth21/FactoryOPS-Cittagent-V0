import pandas as pd
import numpy as np
from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ZScoreDetector:
    """
    Simple z-score based anomaly detection.
    Flags values with |z| > 3 as anomalies.
    """
    
    Z_THRESHOLD = 3.0
    
    def detect(
        self,
        df: pd.DataFrame,
        device_id: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies using z-score method.
        
        Args:
            df: DataFrame with timestamp and parameter columns
            device_id: Device identifier for logging
            
        Returns:
            List of anomaly dictionaries
        """
        if df.empty:
            return []
        
        feature_cols = [c for c in df.columns if c != "timestamp"]
        
        if not feature_cols:
            return []
        
        X = df[feature_cols].copy()
        X = X.fillna(method="ffill").fillna(method="bfill").fillna(0)
        
        means = X.mean()
        stds = X.std()
        
        anomalies = []
        
        for idx in range(len(df)):
            row = X.iloc[idx]
            timestamp = df.iloc[idx]["timestamp"] if "timestamp" in df.columns else None
            
            if pd.isna(timestamp):
                timestamp = datetime.utcnow()
            
            anomalous_params = []
            max_z = 0
            
            for col in feature_cols:
                value = row[col]
                mean = means[col]
                std = stds[col]
                
                if std > 0:
                    z = (value - mean) / std
                else:
                    z = 0
                
                if abs(z) > self.Z_THRESHOLD:
                    anomalous_params.append(col)
                    if abs(z) > abs(max_z):
                        max_z = z
            
            if not anomalous_params:
                continue
            
            severity = "high" if abs(max_z) > 4 else "medium"
            
            param = anomalous_params[0]
            value = row[param]
            mean = means[param]
            
            if max_z > 0:
                context = f"{param.capitalize()} at {value:.1f} (normal: {mean - 2*stds[param]:.1f} to {mean + 2*stds[param]:.1f})"
            else:
                context = f"{param.capitalize()} at {value:.1f} (normal: {mean - 2*stds[param]:.1f} to {mean + 2*stds[param]:.1f})"
            
            anomaly = {
                "timestamp": timestamp.isoformat() if isinstance(timestamp, datetime) else str(timestamp),
                "severity": severity,
                "parameters": anomalous_params,
                "context": context,
                "z_score": float(max_z),
                "index": int(idx)
            }
            
            anomalies.append(anomaly)
        
        logger.info(f"Z-score detected {len(anomalies)} anomalies for {device_id}")
        
        return anomalies


z_score_detector = ZScoreDetector()
