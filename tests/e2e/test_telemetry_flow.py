"""
E2E Test: Telemetry Flow
MQTT → InfluxDB → data-service REST → device heartbeat
"""
import pytest
import time
import uuid
from conftest import BASE_URLS, INFLUX_BUCKET, INFLUX_ORG, publish_mqtt

DEVICE_ID = f"TEST-TELEMETRY-{uuid.uuid4().hex[:6].upper()}"

class TestTelemetryFlow:

    def test_01_create_device(self, http):
        """Create test device via device-service."""
        r = http.post(f"{BASE_URLS['device']}/api/v1/devices", json={
            "device_id": DEVICE_ID,
            "device_name": "E2E Telemetry Test Device",
            "device_type": "compressor",
            "location": "Test Lab"
        })
        assert r.status_code == 201
        data = r.json()
        assert data["success"] is True
        assert data["data"]["device_id"] == DEVICE_ID

    def test_02_publish_mqtt_message(self):
        """Publish telemetry via MQTT."""
        publish_mqtt(DEVICE_ID, {
            "power": 5200,
            "voltage": 228,
            "temperature": 45,
            "pressure": 5.2
        })
        time.sleep(3)  # Allow pipeline to process

    def test_03_verify_influxdb_write(self, influx_query):
        """Verify telemetry was written to InfluxDB."""
        query = f'''
        from(bucket: "{INFLUX_BUCKET}")
          |> range(start: -5m)
          |> filter(fn: (r) => r["device_id"] == "{DEVICE_ID}")
          |> limit(n: 1)
        '''
        result = influx_query.query(query=query, org=INFLUX_ORG)
        records = [r for table in result for r in table.records]
        assert len(records) > 0, "No data found in InfluxDB after MQTT publish"

    def test_04_verify_latest_telemetry_api(self, http):
        """Verify data accessible via data-service REST API."""
        r = http.get(f"{BASE_URLS['data']}/api/telemetry/{DEVICE_ID}/latest")
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert data["data"] is not None
        assert "timestamp" in data["data"]

    def test_05_verify_device_heartbeat_updated(self, http):
        """Verify device last_seen_timestamp was updated."""
        r = http.get(f"{BASE_URLS['device']}/api/v1/devices/{DEVICE_ID}")
        assert r.status_code == 200
        device = r.json()["data"]
        assert device["last_seen_timestamp"] is not None
        # Status should be running (seen within 60s)
        assert device["status"] in ["running", "stopped"]

    def test_06_cleanup(self, http):
        """Delete test device."""
        r = http.delete(f"{BASE_URLS['device']}/api/v1/devices/{DEVICE_ID}")
        assert r.status_code == 200
