"""Thin wrapper around paho-mqtt for the simulated device side: publishes
readings, buffers them locally on disconnect, and flushes the buffer
automatically once the connection is restored.
"""
import logging

import paho.mqtt.client as mqtt

from app.buffer import LocalBuffer
from app.sensors import Reading

logger = logging.getLogger("embedwatch.mqtt_client")


class DeviceClient:
    def __init__(self, host: str, port: int, topic_prefix: str, buffer: LocalBuffer | None = None):
        self.host = host
        self.port = port
        self.topic_prefix = topic_prefix
        self.buffer = buffer or LocalBuffer()
        self.connected = False

        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect

    def connect(self) -> None:
        self._client.connect(self.host, self.port)
        self._client.loop_start()

    def disconnect(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        self.connected = reason_code == 0
        if self.connected:
            logger.info("connected to broker at %s:%s", self.host, self.port)
            self._flush_buffer()
        else:
            logger.warning("connection failed: %s", reason_code)

    def _on_disconnect(self, client, userdata, flags, reason_code, properties=None):
        self.connected = False
        logger.warning("disconnected from broker (reason=%s) — buffering readings locally", reason_code)

    def publish(self, reading: Reading) -> bool:
        """Publish a reading, or buffer it locally if currently offline.

        Returns True if the reading was sent immediately, False if it was
        buffered instead.
        """
        if not self.connected:
            self.buffer.add(reading)
            return False

        topic = f"{self.topic_prefix}/{reading.sensor_id}"
        payload = self.buffer.to_payload(reading)
        result = self._client.publish(topic, payload, qos=1)

        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            logger.warning("publish failed (rc=%s) — buffering instead", result.rc)
            self.buffer.add(reading)
            return False

        return True

    def _flush_buffer(self) -> None:
        pending = self.buffer.drain()
        if not pending:
            return
        logger.info("flushing %d buffered reading(s) after reconnect", len(pending))
        for reading in pending:
            topic = f"{self.topic_prefix}/{reading.sensor_id}"
            self._client.publish(topic, self.buffer.to_payload(reading), qos=1)
