"""
E2E Test: Alert Flow
Device → Rule → MQTT trigger → Alert created → Ack → Resolve → Cooldown
"""
import pytest
import time
import uuid
from conftest import BASE_URLS, publish_mqtt, poll_until

DEVICE_ID = f"TEST-ALERT-{uuid.uuid4().hex[:6].upper()}"


class TestAlertFlow:

    def test_01_create_device(self, http):
        """Create test device."""
        r = http.post(f"{BASE_URLS['device']}/api/v1/devices", json={
            "device_id": DEVICE_ID,
            "device_name": "E2E Alert Test Device",
            "device_type": "motor",
            "location": "Test Lab"
        })
        assert r.status_code == 201

    def test_02_create_rule(self, http):
        """Create rule: temperature > 70, severity=critical, cooldown=1min."""
        r = http.post(f"{BASE_URLS['rule']}/api/v1/rules", json={
            "rule_name": "E2E High Temperature Alert",
            "scope": "selected_devices",
            "device_ids": [DEVICE_ID],
            "property": "temperature",
            "condition": ">",
            "threshold": 70.0,
            "severity": "critical",
            "cooldown_minutes": 1,
            "notification_channels": {}
        })
        assert r.status_code == 201, f"Rule creation failed: {r.text}"
        self.__class__.rule_id = r.json()["data"]["rule_id"]
        assert self.__class__.rule_id is not None

    def test_03_publish_trigger_telemetry(self):
        """Publish telemetry that exceeds threshold (temperature=75)."""
        publish_mqtt(DEVICE_ID, {"temperature": 75.0})
        time.sleep(3)

    def test_04_verify_alert_created(self, http):
        """Verify alert was created with status=open."""
        def fetch_alerts():
            r = http.get(
                f"{BASE_URLS['rule']}/api/v1/alerts",
                params={"device_id": DEVICE_ID, "status": "open"}
            )
            return r.json()

        result = poll_until(
            fetch_alerts,
            lambda r: r["success"] and len(r.get("data", [])) > 0,
            timeout=30
        )
        alerts = result["data"]
        assert len(alerts) >= 1
        alert = alerts[0]
        assert alert["status"] == "open"
        assert alert["severity"] == "critical"
        self.__class__.alert_id = alert["alert_id"]
        assert self.__class__.alert_id is not None

    def test_05_acknowledge_alert(self, http):
        """Acknowledge the alert."""
        r = http.put(
            f"{BASE_URLS['rule']}/api/v1/alerts/{self.__class__.alert_id}/ack"
        )
        assert r.status_code == 200, f"Ack failed: {r.text}"
        assert r.json()["data"]["status"] == "acknowledged"

    def test_06_resolve_alert(self, http):
        """Resolve the alert."""
        r = http.put(
            f"{BASE_URLS['rule']}/api/v1/alerts/{self.__class__.alert_id}/resolve"
        )
        assert r.status_code == 200, f"Resolve failed: {r.text}"
        assert r.json()["data"]["status"] == "resolved"

    def test_07_cooldown_prevents_duplicate_alert(self, http):
        """Second trigger within cooldown window should NOT create new alert."""
        r = http.get(
            f"{BASE_URLS['rule']}/api/v1/alerts",
            params={"device_id": DEVICE_ID}
        )
        count_before = len(r.json().get("data", []))

        publish_mqtt(DEVICE_ID, {"temperature": 75.0})
        time.sleep(3)

        r = http.get(
            f"{BASE_URLS['rule']}/api/v1/alerts",
            params={"device_id": DEVICE_ID}
        )
        count_after = len(r.json().get("data", []))

        assert count_after == count_before, \
            f"Cooldown failed: {count_after - count_before} duplicate alert(s) created"

    def test_08_cleanup(self, http):
        """Archive rule and delete device."""
        if hasattr(self.__class__, 'rule_id') and self.__class__.rule_id:
            http.delete(f"{BASE_URLS['rule']}/api/v1/rules/{self.__class__.rule_id}")
        http.delete(f"{BASE_URLS['device']}/api/v1/devices/{DEVICE_ID}")
