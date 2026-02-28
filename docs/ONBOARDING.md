# FactoryOPS Device Onboarding Guide

This guide covers device onboarding for three audiences: plant operators, developers, and firmware/hardware teams.

---

## 1. DEVICE REGISTRATION (For Plant Operators)

### Step 1 — Register the device via API

Register a new device with the FactoryOPS platform:

```bash
curl -s -X POST http://localhost:8000/api/v1/devices \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "COMPRESSOR-001",
    "device_name": "Main Air Compressor",
    "device_type": "compressor",
    "location": "Factory Floor A",
    "manufacturer": "Atlas Copco",
    "model_number": "GA-55"
  }'
```

**Field descriptions:**

| Field | Required | Format | Example |
|-------|----------|--------|---------|
| `device_id` | Yes | `{TYPE}-{NUMBER}` uppercase | COMPRESSOR-001 |
| `device_name` | Yes | Human-readable string | Main Air Compressor |
| `device_type` | Yes | compressor / motor / pump / conveyor / hvac / generator | compressor |
| `location` | Yes | Physical location string | Factory Floor A |
| `manufacturer` | No | String | Atlas Copco |
| `model_number` | No | String | GA-55 |

**Example response:**

```json
{
  "success": true,
  "data": {
    "device_id": "COMPRESSOR-001",
    "device_name": "Main Air Compressor",
    "device_type": "compressor",
    "location": "Factory Floor A",
    "manufacturer": "Atlas Copco",
    "model": "GA-55",
    "status": "stopped",
    "created_at": "2026-02-28T10:00:00"
  }
}
```

### Step 2 — Verify registration

```bash
curl -s http://localhost:8000/api/v1/devices/COMPRESSOR-001
```

A healthy registered device shows:
- `status`: "running" (if telemetry received in last 5 min) or "stopped"
- `last_seen_timestamp`: timestamp of last telemetry received

### Step 3 — Configure health parameters (optional)

Set up weighted health scoring for the device:

```bash
curl -s -X POST http://localhost:8000/api/v1/devices/COMPRESSOR-001/health-config \
  -H "Content-Type: application/json" \
  -d '{
    "parameter_name": "temperature",
    "weight": 25,
    "min_threshold": 0,
    "max_threshold": 100,
    "optimal_min": 40,
    "optimal_max": 60
  }'
```

**Health config fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `parameter_name` | Yes | Telemetry field name (temperature, pressure, etc.) |
| `weight` | Yes | Weight percentage (all weights must sum to 100) |
| `min_threshold` | No | Minimum valid value |
| `max_threshold` | No | Maximum valid value |
| `optimal_min` | No | Ideal minimum for health score |
| `optimal_max` | No | Ideal maximum for health score |

Add configs for multiple parameters (weights must total 100%):

```bash
# pressure (25%)
curl -s -X POST http://localhost:8000/api/v1/devices/COMPRESSOR-001/health-config \
  -H "Content-Type: application/json" \
  -d '{"parameter_name": "pressure", "weight": 25, "min_threshold": 0, "max_threshold": 15, "optimal_min": 6, "optimal_max": 10}'

# vibration (25%)
curl -s -X POST http://localhost:8000/api/v1/devices/COMPRESSOR-001/health-config \
  -H "Content-Type: application/json" \
  -d '{"parameter_name": "vibration", "weight": 25, "min_threshold": 0, "max_threshold": 10, "optimal_min": 0, "optimal_max": 4}'

# power (25%)
curl -s -X POST http://localhost:8000/api/v1/devices/COMPRESSOR-001/health-config \
  -H "Content-Type: application/json" \
  -d '{"parameter_name": "power", "weight": 25, "min_threshold": 0, "max_threshold": 10000, "optimal_min": 4000, "optimal_max": 6000}'
```

### Step 4 — Set device shifts (optional)

Configure operating shifts for accurate uptime calculations:

```bash
curl -s -X POST http://localhost:8000/api/v1/devices/COMPRESSOR-001/shifts \
  -H "Content-Type: application/json" \
  -d '{
    "day_of_week": "monday",
    "shifts": [
      {"shift_name": "Morning", "start_time": "06:00", "end_time": "14:00"},
      {"shift_name": "Afternoon", "start_time": "14:00", "end_time": "22:00"}
    ]
  }'
```

---

## 2. DEVICE SIMULATOR (For Developers)

### What is the simulator

The simulator generates realistic industrial telemetry data and publishes it via MQTT. It's useful for testing, demos, and development without physical hardware.

### Run the simulator

```bash
python3 tools/simulator.py --device-id COMPRESSOR-001
```

**Command-line arguments:**

| Argument | Default | Description |
|----------|---------|-------------|
| `--device-id` | (required) | Device ID to simulate |
| `--broker` | localhost | MQTT broker hostname |
| `--port` | 1883 | MQTT broker port |
| `--interval` | 5 | Publish interval in seconds |

**Examples:**

```bash
# Basic usage
python3 tools/simulator.py --device-id COMPRESSOR-001

# Fast mode (2 second interval)
python3 tools/simulator.py --device-id MOTOR-001 --interval 2

# Custom broker
python3 tools/simulator.py --device-id PUMP-001 --broker 1.100 --port 1883
```

###192.168. Run multiple simulators

Run 3 devices simultaneously in background:

```bash
# Terminal 1
python3 tools/simulator.py --device-id COMPRESSOR-001 &

# Terminal 2
python3 tools/simulator.py --device-id MOTOR-001 &

# Terminal 3
python3 tools/simulator.py --device-id PUMP-001 &
```

Or use a shell loop:

```bash
for device in COMPRESSOR-001 MOTOR-001 PUMP-001; do
  python3 tools/simulator.py --device-id $device &
done
```

---

## 3. FIRMWARE / HARDWARE TEAM INTEGRATION SPEC

This section is the complete technical reference for embedded teams integrating devices with FactoryOPS.

### 3.1 MQTT Broker Connection Details

| Parameter | Value |
|-----------|-------|
| Broker Host | (your server IP or hostname) |
| Port | 1883 (TCP) |
| WebSocket Port | 8083 |
| Protocol | MQTT v3.1.1 |
| Authentication | None (v1.0) |
| TLS | Not required (v1.0) |
| Keep Alive | 60 seconds |
| Clean Session | true |

### 3.2 Topic Structure

Exact topic format:
```
telemetry/{device_id}
```

**Examples:**
```
telemetry/COMPRESSOR-001
telemetry/MOTOR-005
telemetry/PUMP-012
```

**Rules:**
- `device_id` must be registered in FactoryOPS before sending data
- `device_id` format: `{TYPE}-{NUMBER}` uppercase only
- No wildcards, no subtopics

### 3.3 Payload Format (JSON)

Exact JSON schema the firmware must send:

```json
{
  "timestamp": "2026-02-28T10:30:00.000Z",
  "data": {
    "temperature": 72.5,
    "pressure": 8.2,
    "vibration": 3.1,
    "power": 5500.0,
    "current": 24.3,
    "voltage": 415.0,
    "rpm": 1450.0,
    "humidity": 65.0
  }
}
```

**Rules:**
- All numeric values must be float (not integer) — InfluxDB type enforcement
- `timestamp` must be ISO 8601 UTC format
- `data` object must have at least 1 field
- Field names must be lowercase with underscores
- Unknown fields are stored and ignored (no rejection)
- Maximum payload size: 64KB

### 3.4 Send Frequency

| Recommendation | Interval |
|---------------|----------|
| Minimum | 1 reading per minute |
| Recommended | 1 reading per 30 seconds |
| Maximum | 1 reading per second |

### 3.5 What Happens After Publish

1. EMQX receives message on topic `telemetry/{device_id}`
2. data-service MQTT subscriber picks it up
3. JSON parsed and validated
4. Device metadata enriched from device-service
5. Written to InfluxDB (bucket: telemetry)
6. Rule engine evaluated — alerts fired if thresholds breached
7. Device heartbeat updated (last_seen_timestamp)
8. WebSocket broadcast to any connected dashboards
9. Properties auto-discovered and stored

### 3.6 Error Handling on Firmware Side

- If broker unreachable: retry with exponential backoff
- If publish fails: store locally and retry (store-and-forward)
- Recommended QoS: 1 (at least once delivery)
- If device_id not registered: data is still stored, enrichment_status = "failed"

### 3.7 Verification — Test Your Integration

Test using mosquitto_pub:

```bash
mosquitto_pub -h localhost -p 1883 \
  -t "telemetry/COMPRESSOR-001" \
  -m '{"timestamp":"2026-02-28T10:00:00Z","data":{"temperature":45.0,"power":5000.0}}'
```

Then verify receipt:

```bash
curl -s http://localhost:8081/api/telemetry/COMPRESSOR-001/latest
```

### 3.8 Client Library Examples

#### Python (paho-mqtt)

```python
import paho.mqtt.client as mqtt
import json
from datetime import datetime, timezone

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker")
    else:
        print(f"Connection failed with code {rc}")

client = mqtt.Client(client_id="COMPRESSOR-001")
client.on_connect = on_connect
client.connect("localhost", 1883, keepalive=60)
client.loop_start()

while True:
    payload = json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {
            "temperature": 45.0,
            "pressure": 8.0,
            "power": 5000.0
        }
    })
    client.publish("telemetry/COMPRESSOR-001", payload)
    print(f"Published: {payload}")
    import time
    time.sleep(5)
```

#### Arduino/C++ (PubSubClient)

```cpp
#include <PubSubClient.h>
#include <WiFi.h>

const char* mqtt_server = "192.168.1.100";
const char* device_id = "COMPRESSOR-001";

WiFiClient espClient;
PubSubClient client(espClient);

void setup() {
    client.setServer(mqtt_server, 1883);
}

void reconnect() {
    while (!client.connected()) {
        if (client.connect(device_id)) {
            break;
        }
        delay(5000);
    }
}

void loop() {
    if (!client.connected()) {
        reconnect();
    }
    client.loop();

    StaticJsonDocument<256> doc;
    doc["timestamp"] = String(millis());
    JsonObject data = doc.createNestedObject("data");
    data["temperature"] = 45.0;
    data["pressure"] = 8.0;
    data["power"] = 5000.0;

    String payload;
    serializeJson(doc, payload);
    
    String topic = "telemetry/" + String(device_id);
    client.publish(topic.c_str(), payload.c_str());
    
    delay(5000);
}
```

#### Node.js (mqtt.js)

```javascript
const mqtt = require('mqtt');
const client = mqtt.connect('mqtt://localhost:1883', {
    clientId: 'COMPRESSOR-001',
    clean: true,
    connectTimeout: 4000,
    reconnectPeriod: 1000,
});

client.on('connect', () => {
    console.log('Connected to MQTT broker');
    setInterval(() => {
        const payload = JSON.stringify({
            timestamp: new Date().toISOString(),
            data: {
                temperature: 45.0,
                pressure: 8.0,
                power: 5000.0
            }
        });
        client.publish('telemetry/COMPRESSOR-001', payload);
        console.log('Published:', payload);
    }, 5000);
});
```

---

## 4. ALERT RULES QUICK REFERENCE

Create rules for common monitoring scenarios:

### High Temperature Alert

```bash
curl -s -X POST http://localhost:8002/api/v1/rules \
  -H "Content-Type: application/json" \
  -d '{
    "rule_name": "High Temperature Alert",
    "scope": "selected_devices",
    "device_ids": ["COMPRESSOR-001"],
    "property": "temperature",
    "condition": ">",
    "threshold": 70.0,
    "severity": "critical",
    "cooldown_minutes": 1,
    "notification_channels": {}
  }'
```

### Low Pressure Alert

```bash
curl -s -X POST http://localhost:8002/api/v1/rules \
  -H "Content-Type: application/json" \
  -d '{
    "rule_name": "Low Pressure Alert",
    "scope": "selected_devices",
    "device_ids": ["COMPRESSOR-001"],
    "property": "pressure",
    "condition": "<",
    "threshold": 5.0,
    "severity": "warning",
    "cooldown_minutes": 5,
    "notification_channels": {}
  }'
```

### High Vibration Alert

```bash
curl -s -X POST http://localhost:8002/api/v1/rules \
  -H "Content-Type: application/json" \
  -d '{
    "rule_name": "High Vibration Alert",
    "scope": "selected_devices",
    "device_ids": ["COMPRESSOR-001"],
    "property": "vibration",
    "condition": ">",
    "threshold": 5.0,
    "severity": "critical",
    "cooldown_minutes": 1,
    "notification_channels": {}
  }'
```

### Power Overconsumption Alert

```bash
curl -s -X POST http://localhost:8002/api/v1/rules \
  -H "Content-Type: application/json" \
  -d '{
    "rule_name": "Power Overconsumption",
    "scope": "selected_devices",
    "device_ids": ["COMPRESSOR-001"],
    "property": "power",
    "condition": ">",
    "threshold": 7000.0,
    "severity": "warning",
    "cooldown_minutes": 5,
    "notification_channels": {}
  }'
```

---

## 5. TROUBLESHOOTING

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Device shows status=stopped | No telemetry in last 5 min | Check MQTT connection |
| Alert not firing | Rule not active or cooldown active | Check rule status at GET /api/v1/rules/{rule_id} |
| enrichment_status=failed | device_id not registered | Register device first at POST /api/v1/devices |
| InfluxDB write error | Float/int type mismatch | Send all values as float (e.g., 45.0 not 45) |
| MQTT publish succeeds but no data | Wrong topic format | Use `telemetry/{DEVICE_ID}` with uppercase device_id |
| WebSocket not receiving | Client not connected | Check WebSocket connection to ws://localhost:8081/ws |
| Rule evaluation fails | Property name mismatch | Ensure telemetry field matches rule property exactly |

---

## Quick Start Checklist

- [ ] Register device at POST /api/v1/devices
- [ ] Configure health parameters (optional but recommended)
- [ ] Set up alert rules for critical parameters
- [ ] Verify telemetry flow: MQTT → API query
- [ ] Check device status shows "running"
