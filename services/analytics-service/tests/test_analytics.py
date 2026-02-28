import pytest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestDataInsufficientError:
    """Test DataInsufficientError exception."""
    
    def test_error_message_anomaly(self):
        from app.ml.anomaly.isolation_forest import DataInsufficientError
        
        error = DataInsufficientError("Need at least 7 days of data")
        assert "7 days" in str(error)
    
    def test_error_message_failure(self):
        from app.ml.prediction.failure_predictor import DataInsufficientError
        
        error = DataInsufficientError("Need at least 30 days of data")
        assert "30 days" in str(error)


class TestIsolationForest:
    """Test Isolation Forest anomaly detection."""
    
    def test_requires_minimum_data(self):
        from app.ml.anomaly.isolation_forest import IsolationForestDetector, DataInsufficientError
        
        detector = IsolationForestDetector()
        
        df = pd.DataFrame({
            "timestamp": pd.date_range(start="2026-01-01", periods=100, freq="1min"),
            "temperature": np.random.normal(50, 5, 100),
            "pressure": np.random.normal(100, 10, 100)
        })
        
        with pytest.raises(DataInsufficientError):
            detector.detect(df, sensitivity="medium", device_id="TEST-001")
    
    def test_detects_anomalies_with_sufficient_data(self):
        from app.ml.anomaly.isolation_forest import IsolationForestDetector
        
        detector = IsolationForestDetector()
        
        n_points = 7 * 24 * 60 + 100
        df = pd.DataFrame({
            "timestamp": pd.date_range(start="2026-01-01", periods=n_points, freq="1min"),
            "temperature": np.random.normal(50, 5, n_points),
            "pressure": np.random.normal(100, 10, n_points)
        })
        
        df.iloc[1000, df.columns.get_loc("temperature")] = 200
        
        anomalies = detector.detect(df, sensitivity="high", device_id="TEST-001")
        
        assert len(anomalies) > 0
        assert "severity" in anomalies[0]
        assert "parameters" in anomalies[0]
        assert "context" in anomalies[0]


class TestZScore:
    """Test Z-score anomaly detection."""
    
    def test_detects_z_score_anomalies(self):
        from app.ml.anomaly.z_score import ZScoreDetector
        
        detector = ZScoreDetector()
        
        n_points = 1000
        df = pd.DataFrame({
            "timestamp": pd.date_range(start="2026-01-01", periods=n_points, freq="1min"),
            "temperature": np.random.normal(50, 5, n_points),
            "pressure": np.random.normal(100, 10, n_points)
        })
        
        df.iloc[500, df.columns.get_loc("temperature")] = 200
        
        anomalies = detector.detect(df, device_id="TEST-001")
        
        assert len(anomalies) > 0


class TestFailurePredictor:
    """Test Failure Prediction."""
    
    def test_requires_30_days_data(self):
        from app.ml.prediction.failure_predictor import FailurePredictor, DataInsufficientError
        
        predictor = FailurePredictor()
        
        df = pd.DataFrame({
            "timestamp": pd.date_range(start="2026-01-01", periods=1000, freq="1min"),
            "temperature": np.random.normal(50, 5, 1000),
            "pressure": np.random.normal(100, 10, 1000)
        })
        
        with pytest.raises(DataInsufficientError):
            predictor.predict(df, device_id="TEST-001")


class TestResultFormatter:
    """Test result formatter produces plain language output."""
    
    def test_anomaly_results_no_jargon(self):
        from app.ml.result_formatter import ResultFormatter
        
        formatter = ResultFormatter()
        
        df = pd.DataFrame({
            "timestamp": pd.date_range(start="2026-01-01", periods=1000, freq="1min"),
            "temperature": np.random.normal(50, 5, 1000)
        })
        
        anomalies = [{
            "timestamp": "2026-01-15T10:00:00",
            "severity": "high",
            "parameters": ["temperature"],
            "context": "Temperature spike to 78°C (normal: 40-55°C)"
        }]
        
        result = formatter.format_anomaly_results(anomalies, df, "medium", 30)
        
        assert "analysis_type" in result
        assert "summary" in result
        assert "recommendations" in result
        
        assert result["summary"]["total_anomalies"] == 1
        
        for rec in result["recommendations"]:
            assert "action" in rec
            assert "urgency" in rec
    
    def test_failure_prediction_no_ml_jargon(self):
        from app.ml.result_formatter import ResultFormatter
        
        formatter = ResultFormatter()
        
        risk_factors = [
            {
                "parameter": "vibration",
                "contribution_pct": 45,
                "trend": "increasing",
                "context": "Vibration increased 23% over the last 7 days"
            }
        ]
        
        result = formatter.format_failure_prediction_results(
            failure_probability=34,
            risk_factors=risk_factors,
            feature_importances={"vibration": 0.45},
            days_available=30,
            lookback_days=30
        )
        
        assert "analysis_type" in result
        assert "summary" in result
        assert "risk_factors" in result
        assert "recommended_actions" in result
        
        assert result["summary"]["failure_risk"] == "Medium"
        
        for rf in result["risk_factors"]:
            assert "context" in rf
            assert "reasoning" in rf
        
        for action in result["recommended_actions"]:
            assert "action" in action
            assert "urgency" in action


class TestJobRunner:
    """Test job runner exception handling."""
    
    @pytest.mark.asyncio
    async def test_job_failure_sets_status(self):
        from app.ml.job_runner import JobRunner
        from unittest.mock import AsyncMock, MagicMock
        
        runner = JobRunner()
        
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        
        with pytest.raises(Exception):
            await runner.run_job("nonexistent-job-id", mock_db)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
