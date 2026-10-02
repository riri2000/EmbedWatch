"""Integration tests against a real MQTT broker (not a mock).

These require a broker reachable at EMBEDWATCH_TEST / settings.mqtt_host:
settings.mqtt_port — in CI this is a Mosquitto service container; locally,
`mosquitto` running on localhost:1883 (see README for setup).
"""
import queue
import time

import paho.mqtt.client as mqtt
import pytest

from app.buffer import LocalBuffer
from app.config import settings
from app.mqtt_client import DeviceClient
from app.sensors import Reading


def _broker_reachable() -> bool:
    try:
        probe = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        probe.connect(settings.mqtt_host, settings.mqtt_port, keepalive=2)
        probe.disconnect()
        return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(
    not _broker_reachable(),
    reason="No MQTT broker reachable at the configured host/port — see README to run one locally.",
)

# A prefix distinct from settings.mqtt_topic_prefix, so these low-level
# pub/sub tests don't get picked up by the ingestion service's own
# subscription in test_ingestion_integration.py (and vice versa).
TEST_PREFIX = f"{settings.mqtt_topic_prefix}-raw"


@pytest.fixture()
def subscriber_messages():
    """Subscribes to the test topic prefix and collects everything
    published to it during the test, via a real MQTT subscription."""
    received: queue.Queue = queue.Queue()

    def on_message(client, userdata, msg):
        received.put(msg)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message
    client.connect(settings.mqtt_host, settings.mqtt_port)
    client.subscribe(f"{TEST_PREFIX}/#", qos=1)
    client.loop_start()
    time.sleep(0.3)  # let the subscription register before the test publishes

    yield received

    client.loop_stop()
    client.disconnect()


def test_publish_reaches_a_real_subscriber(subscriber_messages):
    device = DeviceClient(settings.mqtt_host, settings.mqtt_port, TEST_PREFIX)
    device.connect()
    time.sleep(0.3)

    reading = Reading(sensor_id="integration-temp", sensor_type="temperature", value=22.5, unit="°C")
    sent = device.publish(reading)
    assert sent is True

    msg = subscriber_messages.get(timeout=3)
    assert msg.topic == f"{TEST_PREFIX}/integration-temp"
    assert b"22.5" in msg.payload

    device.disconnect()


def test_publish_while_offline_is_buffered_then_flushed_on_reconnect(subscriber_messages):
    # Point at a port nothing is listening on, so the client starts offline.
    device = DeviceClient("localhost", 1, TEST_PREFIX, buffer=LocalBuffer())

    offline_reading = Reading(sensor_id="integration-offline", sensor_type="temperature", value=19.0, unit="°C")
    sent = device.publish(offline_reading)
    assert sent is False
    assert len(device.buffer) == 1

    # Now point the same buffer at the real broker and connect — the
    # buffered reading should flush automatically on connect.
    device._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    device._client.on_connect = device._on_connect
    device._client.on_disconnect = device._on_disconnect
    device.host, device.port = settings.mqtt_host, settings.mqtt_port
    device.connect()

    msg = subscriber_messages.get(timeout=3)
    assert msg.topic == f"{TEST_PREFIX}/integration-offline"
    assert len(device.buffer) == 0

    device.disconnect()
