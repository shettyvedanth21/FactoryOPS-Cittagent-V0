"""
E2E Test: Analytics Flow
Seed 30 days data → Submit job → Poll → Verify results
"""
import pytest
import time
import uuid
from datetime import datetime, timedelta, timezone
from influxdb_client import Point
from conftest import BASE_URLS, INFLUX_BUCKET, INFLUX_ORG, poll_until

DEVICE_ID = f"TEST-ANALYTICS-{uuid.uuid4().hex[:6].upper()}"
ML_JARGON = [
    "isolation forest", "random forest", "z-score", "contamination",
    "n_estimators", "feature_importance", "hyperparameter", "overfitting",
    "underfitting", "gradient boosting", "StandardScaler", "fit_transform"
]

def seed_30_days(influx_write):
    """Write 30 days of telemetry data to InfluxDB."""
    now = datetime.now(timezone.utc)
    points = []
    for days_ago in range(30):
        for hour in range(0, 24, 2):
            ts = now - timedelta(days=days_ago, hours=hour)
            # Introduce anomalies in last 5 days
            temp = 45 + (hour % 8)
            vibration = 2.3
            if days_ago < 5:
                vibration = 2.3 + (days_ago * 0.5)  # Increasing vibration
            p = Point("telemetry") \
                .tag("device_id", DEVICE_ID) \
                .tag("schema_version", "v1") \
                .tag("enrichment_status", "success") \
                .field("power", 5000.0) \
                .field("temperature", float(temp)) \
                .field("vibration", float(vibration)) \
                .field("pressure", 5.2) \
                .time(ts)
            points.append(p)
    influx_write.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)

class TestAnalyticsFlow:

    def test_01_create_device_and_seed_data(self, http, influx_write):
        """Create device and seed 30 days of telemetry."""
        http.post(f"{BASE_URLS['device']}/api/v1/devices", json={
            "device_id": DEVICE_ID,
            "device_name": "E2E Analytics Test Device",
            "device_type": "motor",
            "location": "Test Lab"
        })
        seed_30_days(influx_write)

    def test_02_submit_failure_prediction_job(self, http):
        """Submit failure prediction analysis job."""
        r = http.post(f"{BASE_URLS['analytics']}/api/v1/analytics/run", json={
            "device_id": DEVICE_ID,
            "analysis_type": "failure_prediction",
            "parameters": {
                "lookback_days": 30,
                "target_parameters": ["temperature", "vibration", "pressure"]
            }
        })
        assert r.status_code in [200, 201, 202]
        data = r.json()
        assert data["success"] is True
        self.__class__.job_id = data["data"]["job_id"]

    def test_03_poll_until_completed(self, http):
        """Poll job status until completed (max 300s)."""
        def fetch_job():
            r = http.get(f"{BASE_URLS['analytics']}/api/v1/analytics/jobs/{self.__class__.job_id}")
            return r.json()

        result = poll_until(
            fetch_job,
            lambda r: r["success"] and r["data"]["status"] in ["completed", "failed"],
            timeout=300,
            interval=5
        )
        assert result["data"]["status"] == "completed", \
            f"Analytics job failed: {result['data'].get('error_message')}"

    def test_04_fetch_results(self, http):
        """Fetch completed job results."""
        r = http.get(f"{BASE_URLS['analytics']}/api/v1/analytics/results/{self.__class__.job_id}")
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        self.__class__.results = data["data"]

    def test_05_verify_result_structure(self):
        """Verify results contain expected fields."""
        results = self.__class__.results
        assert "summary" in results
        assert "risk_factors" in results or "anomalies" in results
        assert "recommendations" in results or "recommended_actions" in results

        summary = results["summary"]
        assert "failure_risk" in summary or "total_anomalies" in summary

    def test_06_verify_no_ml_jargon(self):
        """Verify results use plain language — no ML jargon."""
        import json
        results_str = json.dumps(self.__class__.results).lower()
        for jargon in ML_JARGON:
            assert jargon.lower() not in results_str, \
                f"ML jargon found in results: '{jargon}'"

    def test_07_cleanup(self, http):
        """Delete test device."""
        http.delete(f"{BASE_URLS['device']}/api/v1/devices/{DEVICE_ID}")
