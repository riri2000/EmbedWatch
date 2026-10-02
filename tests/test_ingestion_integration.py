"""End-to-end test: a reading published over real MQTT should be
persisted by the ingestion service and show up both via the REST
history endpoint and the live WebSocket feed.
"""
import time

import paho.mqtt.client as mqtt
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from tests.test_mqtt_integration import _broker_reachable

pytestmark = pytest.mark.skipif(
    not _broker_reachable(),
    reason="No MQTT broker reachable — see README to run one locally.",
)


def _publish_raw(sensor_id: str, value: float):
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(settings.mqtt_host, settings.mqtt_port)
    client.loop_start()
    payload = f'{{"sensor_id": "{sensor_id}", "sensor_type": "temperature", "value": {value}, "unit": "\u00b0C"}}'
    client.publish(f"{settings.mqtt_topic_prefix}/{sensor_id}", payload, qos=1)
    time.sleep(0.3)
    client.loop_stop()
    client.disconnect()


def test_published_reading_appears_in_history():
    from app.main import app  # imported here so conftest's env vars apply first

    with TestClient(app):
        # Give the ingestion service's MQTT connection a moment to establish.
        time.sleep(0.5)
        _publish_raw("history-test", 23.4)
        time.sleep(0.5)

        with TestClient(app) as client:
            resp = client.get("/readings", params={"sensor_id": "history-test"})
            assert resp.status_code == 200
            data = resp.json()
            assert any(r["value"] == 23.4 for r in data)


def test_published_reading_is_broadcast_over_websocket():
    from app.main import app

    with TestClient(app) as client:
        time.sleep(0.5)
        with client.websocket_connect("/ws/live") as ws:
            _publish_raw("ws-test", 18.1)
            message = ws.receive_json()
            assert message["sensor_id"] == "ws-test"
            assert message["value"] == 18.1


def test_malformed_payload_does_not_crash_ingestion():
    """A garbage payload on the topic should be dropped, not bring the
    ingestion service down for every other sensor."""
    from app.main import app

    client_raw = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client_raw.connect(settings.mqtt_host, settings.mqtt_port)
    client_raw.loop_start()

    with TestClient(app):
        time.sleep(0.5)
        client_raw.publish(f"{settings.mqtt_topic_prefix}/garbage", "not json at all", qos=1)
        time.sleep(0.3)
        _publish_raw("after-garbage", 25.0)
        time.sleep(0.5)

        with TestClient(app) as client:
            resp = client.get("/readings", params={"sensor_id": "after-garbage"})
            assert resp.status_code == 200
            assert any(r["value"] == 25.0 for r in resp.json())

    client_raw.loop_stop()
    client_raw.disconnect()
