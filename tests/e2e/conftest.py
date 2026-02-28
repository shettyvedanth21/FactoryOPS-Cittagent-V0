import pytest
import httpx
import asyncio
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
import paho.mqtt.client as mqtt
import os
import time

BASE_URLS = {
    "device":    os.getenv("DEVICE_SERVICE_URL",    "http://localhost:8000"),
    "data":      os.getenv("DATA_SERVICE_URL",       "http://localhost:8081"),
    "rule":      os.getenv("RULE_ENGINE_URL",        "http://localhost:8002"),
    "analytics": os.getenv("ANALYTICS_SERVICE_URL", "http://localhost:8003"),
    "reporting": os.getenv("REPORTING_SERVICE_URL", "http://localhost:8085"),
    "export":    os.getenv("DATA_EXPORT_URL",        "http://localhost:8080"),
}

INFLUX_URL   = os.getenv("INFLUX_URL",   "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "factoryops-admin-token")
INFLUX_ORG   = os.getenv("INFLUX_ORG",  "factoryops")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "telemetry")
MQTT_BROKER  = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT    = int(os.getenv("MQTT_PORT", "1883"))

@pytest.fixture(scope="session")
def http():
    """Sync httpx client for all services."""
    with httpx.Client(timeout=30) as client:
        yield client

@pytest.fixture(scope="session")
def influx_write():
    """InfluxDB write client."""
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    write_api = client.write_api(write_options=SYNCHRONOUS)
    yield write_api
    client.close()

@pytest.fixture(scope="session")
def influx_query():
    """InfluxDB query client."""
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    yield client.query_api()
    client.close()

def publish_mqtt(device_id: str, data: dict):
    """Publish telemetry via MQTT."""
    import json
    from datetime import datetime, timezone
    import time
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data
    }
    client = mqtt.Client()
    connected = False
    def on_connect(c, userdata, flags, rc):
        nonlocal connected
        connected = (rc == 0)
    client.on_connect = on_connect
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    time.sleep(1)
    if connected:
        client.publish(f"telemetry/{device_id}", json.dumps(payload))
        time.sleep(0.5)
    client.loop_stop()
    client.disconnect()

def poll_until(fn, condition, timeout=120, interval=3):
    """Poll fn() until condition(result) is True or timeout."""
    start = time.time()
    while time.time() - start < timeout:
        result = fn()
        if condition(result):
            return result
        time.sleep(interval)
    raise TimeoutError(f"Condition not met within {timeout}s")
