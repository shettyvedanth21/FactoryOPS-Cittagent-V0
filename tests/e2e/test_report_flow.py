"""
E2E Test: Report Flow
Seed data → Generate report → Poll → Download
"""
import pytest
import time
import uuid
from datetime import datetime, timedelta, timezone
from influxdb_client import Point
from conftest import BASE_URLS, INFLUX_BUCKET, INFLUX_ORG, poll_until

DEVICE_ID = f"TEST-REPORT-{uuid.uuid4().hex[:6].upper()}"

def seed_influx_data(influx_write):
    """Write 7 days of test telemetry to InfluxDB."""
    now = datetime.now(timezone.utc)
    points = []
    for days_ago in range(7):
        for hour in range(0, 24, 1):
            ts = now - timedelta(days=days_ago, hours=hour)
            p = Point("telemetry") \
                .tag("device_id", DEVICE_ID) \
                .tag("schema_version", "v1") \
                .tag("enrichment_status", "success") \
                .field("power", float(5000 + (hour * 100))) \
                .field("voltage", 228.0) \
                .field("temperature", float(45 + (hour % 10))) \
                .time(ts)
            points.append(p)
    influx_write.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)

class TestReportFlow:

    def test_01_create_device_and_seed_data(self, http, influx_write):
        """Create device and seed historical telemetry."""
        http.post(f"{BASE_URLS['device']}/api/v1/devices", json={
            "device_id": DEVICE_ID,
            "device_name": "E2E Report Test Device",
            "device_type": "compressor",
            "location": "Test Lab"
        })
        seed_influx_data(influx_write)

    def test_02_generate_consumption_report(self, http):
        """Submit consumption report generation request."""
        global report_id
        now = datetime.now(timezone.utc)
        r = http.post(f"{BASE_URLS['reporting']}/api/v1/reports/consumption", json={
            "device_ids": [DEVICE_ID],
            "start_date": (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end_date": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "group_by": "daily",
            "format": "pdf"
        })
        assert r.status_code in [200, 202]
        data = r.json()
        assert data["success"] is True
        self.__class__.report_id = data["data"]["report_id"]

    def test_03_poll_until_completed(self, http):
        """Poll report status until completed (max 120s)."""
        def fetch_report():
            r = http.get(f"{BASE_URLS['reporting']}/api/v1/reports/{self.__class__.report_id}")
            return r.json()

        result = poll_until(
            fetch_report,
            lambda r: r["success"] and r["data"]["status"] in ["completed", "failed"],
            timeout=120
        )
        assert result["data"]["status"] == "completed", \
            f"Report failed: {result['data'].get('error_message')}"

    def test_04_download_report(self, http):
        """Verify download URL is available."""
        r = http.get(f"{BASE_URLS['reporting']}/api/v1/reports/{self.__class__.report_id}/download")
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert data["data"]["download_url"] is not None or r.status_code == 302

    def test_05_cleanup(self, http):
        """Delete test device."""
        http.delete(f"{BASE_URLS['device']}/api/v1/devices/{DEVICE_ID}")
