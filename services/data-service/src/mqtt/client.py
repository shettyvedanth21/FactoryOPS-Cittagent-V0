import json
import logging
import asyncio
from typing import Optional, Callable
import paho.mqtt.client as mqtt

from src.config import settings
from src.mqtt.handler import TelemetryHandler


logger = logging.getLogger(__name__)


class MQTTClient:
    def __init__(self, message_handler: Optional[TelemetryHandler] = None):
        self._client: Optional[mqtt.Client] = None
        self._message_handler = message_handler
        self._connected = False
        self._reconnect_delay = 1
        self._max_reconnect_delay = 60
        self._running = False
    
    def connect(self):
        """Connect to MQTT broker."""
        self._client = mqtt.Client(client_id="data-service")
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        
        try:
            logger.info(f"Connecting to MQTT broker at {settings.MQTT_BROKER}:{settings.MQTT_PORT}")
            self._client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, keepalive=60)
            self._client.loop_start()
            self._running = True
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {str(e)}")
    
    def disconnect(self):
        """Disconnect from MQTT broker."""
        self._running = False
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            logger.info("Disconnected from MQTT broker")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker."""
        if rc == 0:
            logger.info("Connected to MQTT broker")
            self._connected = True
            self._reconnect_delay = 1
            client.subscribe("telemetry/+")
            logger.info("Subscribed to topic: telemetry/+")
        else:
            logger.error(f"Failed to connect to MQTT broker, return code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker."""
        self._connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnect from MQTT broker, return code: {rc}")
            self._schedule_reconnect()
        else:
            logger.info("Disconnected from MQTT broker")
    
    def _on_message(self, client, userdata, msg):
        """Callback when message received."""
        try:
            topic = msg.topic
            payload = msg.payload.decode("utf-8")
            
            if topic.startswith("telemetry/"):
                device_id = topic.split("/")[1]
                logger.info(f"Received telemetry for device: {device_id}")
                
                if self._message_handler:
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    if loop.is_running():
                        asyncio.run_coroutine_threadsafe(
                            self._message_handler.handle_telemetry(device_id, payload),
                            loop
                        )
                    else:
                        loop.run_until_complete(
                            self._message_handler.handle_telemetry(device_id, payload)
                        )
            else:
                logger.warning(f"Received message on unexpected topic: {topic}")
        
        except Exception as e:
            logger.error(f"Error processing MQTT message: {str(e)}")
    
    def _schedule_reconnect(self):
        """Schedule reconnection with exponential backoff."""
        if self._running:
            logger.info(f"Scheduling reconnection in {self._reconnect_delay} seconds")
            asyncio.create_task(self._reconnect())
    
    async def _reconnect(self):
        """Attempt to reconnect to MQTT broker."""
        await asyncio.sleep(self._reconnect_delay)
        
        if not self._connected and self._running:
            try:
                logger.info("Attempting to reconnect to MQTT broker")
                self._client.reconnect()
                self._reconnect_delay = min(
                    self._reconnect_delay * 2,
                    self._max_reconnect_delay
                )
            except Exception as e:
                logger.error(f"Failed to reconnect to MQTT broker: {str(e)}")
                self._schedule_reconnect()
    
    def is_connected(self) -> bool:
        """Check if connected to MQTT broker."""
        return self._connected


mqtt_client = MQTTClient()


async def get_mqtt_client() -> MQTTClient:
    return mqtt_client
