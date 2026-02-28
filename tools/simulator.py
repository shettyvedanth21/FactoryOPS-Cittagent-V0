#!/usr/bin/env python3
"""
FactoryOPS Device Simulator

Generates realistic industrial telemetry and publishes via MQTT.
Useful for testing, demos, and development without physical hardware.

Usage:
    python3 simulator.py --device-id COMPRESSOR-001
    python3 simulator.py --device-id MOTOR-001 --interval 2
    python3 simulator.py --device-id PUMP-001 --broker localhost --port 1883
"""

import argparse
import json
import random
import signal
import sys
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt


class DeviceSimulator:
    def __init__(
        self,
        device_id: str,
        broker: str = "localhost",
        port: int = 1883,
        interval: int = 5,
    ):
        self.device_id = device_id
        self.broker = broker
        self.port = port
        self.interval = interval
        self.running = False
        self.client = None

        self.base_values = {
            "temperature": 45.0,
            "pressure": 8.0,
            "vibration": 2.5,
            "power": 5000.0,
            "current": 24.0,
            "voltage": 415.0,
            "rpm": 1450.0,
            "humidity": 60.0,
        }

    def connect(self):
        self.client = mqtt.Client(client_id=f"simulator-{self.device_id}")
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish

        try:
            print(f"Connecting to MQTT broker at {self.broker}:{self.port}...")
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            self.running = True
        except Exception as e:
            print(f"Failed to connect to MQTT broker: {e}")
            sys.exit(1)

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"Connected to MQTT broker (return code: {rc})")
        else:
            print(f"Failed to connect to MQTT broker (return code: {rc})")

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            print(f"Unexpected disconnect (return code: {rc})")
            self._reconnect()

    def _on_publish(self, client, userdata, mid):
        pass

    def _reconnect(self):
        print("Attempting to reconnect...")
        try:
            self.client.reconnect()
            print("Reconnected successfully")
        except Exception as e:
            print(f"Reconnection failed: {e}")

    def generate_telemetry(self):
        data = {}
        spike = random.random() < 0.01

        for param, base_value in self.base_values.items():
            noise = random.uniform(-0.05, 0.05)
            value = base_value * (1 + noise)

            if spike:
                spike_param = random.choice(list(self.base_values.keys()))
                if param == spike_param:
                    direction = random.choice([-1, 1])
                    value = base_value * (1 + direction * random.uniform(0.2, 0.4))

            if param in ["temperature", "pressure", "vibration"]:
                value = round(value, 2)
            else:
                value = round(value, 1)

            data[param] = float(value)

        return data

    def publish(self):
        telemetry = self.generate_telemetry()

        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": telemetry,
        }

        topic = f"telemetry/{self.device_id}"
        result = self.client.publish(topic, json.dumps(payload))

        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Published to {topic}")
            print(f"  {json.dumps(payload)}")
        else:
            print(f"Failed to publish (error code: {result.rc})")

    def run(self):
        print(f"Starting simulator for device: {self.device_id}")
        print(f"Publishing every {self.interval} seconds")
        print(f"Press Ctrl+C to stop")
        print("-" * 50)

        while self.running:
            self.publish()
            time.sleep(self.interval)

    def stop(self):
        print("\nStopping simulator...")
        self.running = False
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
        print("Simulator stopped")


def main():
    parser = argparse.ArgumentParser(
        description="FactoryOPS Device Simulator - Generate realistic telemetry data"
    )
    parser.add_argument(
        "--device-id",
        required=True,
        help="Device ID to simulate (e.g., COMPRESSOR-001)",
    )
    parser.add_argument(
        "--broker",
        default="localhost",
        help="MQTT broker hostname (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=1883,
        help="MQTT broker port (default: 1883)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Publish interval in seconds (default: 5)",
    )

    args = parser.parse_args()

    simulator = DeviceSimulator(
        device_id=args.device_id,
        broker=args.broker,
        port=args.port,
        interval=args.interval,
    )

    def signal_handler(sig, frame):
        simulator.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    simulator.connect()
    simulator.run()


if __name__ == "__main__":
    main()
