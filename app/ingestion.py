"""Ingestion service: subscribes to sensor readings over MQTT, persists
them, and hands them off to the WebSocket connection manager so the
dashboard updates live.
"""
import asyncio
import json
import logging

import paho.mqtt.client as mqtt

from app.config import settings
from app.database import SessionLocal
from app.models import ReadingRecord
from app.ws_manager import ConnectionManager

logger = logging.getLogger("embedwatch.ingestion")


class IngestionService:
    def __init__(self, manager: ConnectionManager, loop: asyncio.AbstractEventLoop):
        self.manager = manager
        self.loop = loop
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

    def start(self) -> None:
        self._client.connect(settings.mqtt_host, settings.mqtt_port)
        self._client.loop_start()

    def stop(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        topic = f"{settings.mqtt_topic_prefix}/#"
        client.subscribe(topic, qos=1)
        logger.info("ingestion subscribed to %s", topic)

    def _on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.warning("dropped malformed message on %s", msg.topic)
            return

        record = self._persist(data)
        if record is None:
            return

        if self.loop.is_closed():
            logger.debug("event loop already closed — dropping broadcast for %s", record.sensor_id)
            return

        asyncio.run_coroutine_threadsafe(
            self.manager.broadcast(
                {
                    "sensor_id": record.sensor_id,
                    "sensor_type": record.sensor_type,
                    "value": record.value,
                    "unit": record.unit,
                    "received_at": record.received_at.isoformat(),
                }
            ),
            self.loop,
        )

    @staticmethod
    def _persist(data: dict) -> ReadingRecord | None:
        required = {"sensor_id", "sensor_type", "value", "unit"}
        if not required.issubset(data):
            logger.warning("dropped message missing required fields: %s", data)
            return None

        db = SessionLocal()
        try:
            record = ReadingRecord(
                sensor_id=data["sensor_id"],
                sensor_type=data["sensor_type"],
                value=float(data["value"]),
                unit=data["unit"],
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return record
        finally:
            db.close()
