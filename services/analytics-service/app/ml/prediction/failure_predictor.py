from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np
from typing import Dict, Any, List
import logging

from app.ml.prediction.feature_extractor import feature_extractor
from app.ml.anomaly.isolation_forest import DataInsufficientError, isolation_forest_detector

logger = logging.getLogger(__name__)


class FailurePredictor:
    """
    Failure prediction using Random Forest classifier.
    Requires minimum 30 days of data as per LLD §16.7.
    """
    
    MIN_DAYS_REQUIRED = 30
    
    def predict(
        self,
        df: pd.DataFrame,
        target_parameters: List[str] = None,
        device_id: str = ""
    ) -> Dict[str, Any]:
        """
        Predict failure probability using Random Forest.
        
        Args:
            df: DataFrame with telemetry data
            target_parameters: Parameters to use for prediction
            device_id: Device identifier
            
        Returns:
            Dictionary with prediction results
            
        Raises:
            DataInsufficientError: If less than 30 days of data
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
        
        try:
            anomalies = isolation_forest_detector.detect(
                df, sensitivity="medium", device_id=device_id
            )
            anomaly_indices = [a["index"] for a in anomalies]
        except DataInsufficientError:
            anomaly_indices = []
        
        features_df = feature_extractor.extract_features(df, target_parameters)
        
        # Only use numeric columns — exclude timestamp and any string tag columns
        feature_cols = [
            c for c in features_df.columns
            if c != "timestamp" and pd.api.types.is_numeric_dtype(features_df[c])
        ]
        
        X = features_df[feature_cols].copy()
        X = X.fillna(0)
        
        labels = feature_extractor.create_synthetic_labels(
            features_df, anomaly_indices
        )
        
        if labels.sum() < 5:
            labels = self._create_threshold_based_labels(X)
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        rf_classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1,
            class_weight="balanced"
        )
        
        rf_classifier.fit(X_scaled, labels)
        
        probabilities = rf_classifier.predict_proba(X_scaled)
        
        if len(probabilities[0]) > 1:
            failure_probs = probabilities[:, 1]
        else:
            failure_probs = probabilities[:, 0]
        
        current_prob = float(failure_probs[-1])
        
        recent_probs = failure_probs[-60:] if len(failure_probs) >= 60 else failure_probs
        avg_recent_prob = float(np.mean(recent_probs))
        
        final_probability = max(current_prob, avg_recent_prob) * 100
        
        feature_importances = rf_classifier.feature_importances_
        
        risk_factors = feature_extractor.compute_feature_importance_context(
            feature_cols, feature_importances
        )
        
        days_available = len(df) / (24 * 60)
        
        logger.info(
            f"Failure prediction for {device_id}: "
            f"probability={final_probability:.1f}%, risk_factors={len(risk_factors)}"
        )
        
        return {
            "failure_probability": final_probability,
            "risk_factors": risk_factors,
            "feature_importances": dict(zip(feature_cols, feature_importances.tolist())),
            "days_available": int(days_available),
            "anomalies_detected": len(anomaly_indices)
        }
    
    def _create_threshold_based_labels(self, X: pd.DataFrame) -> pd.Series:
        """Create labels based on parameter thresholds."""
        n = len(X)
        labels = pd.Series([0] * n, index=X.index)
        
        threshold = 0.95
        
        for col in X.columns:
            col_data = X[col]
            q95 = col_data.quantile(threshold)
            q05 = col_data.quantile(1 - threshold)
            
            extreme_indices = (col_data > q95) | (col_data < q05)
            labels[extreme_indices] = 1
        
        return labels


failure_predictor = FailurePredictor()
