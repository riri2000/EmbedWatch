"""Entry point simulating a physical device: wakes up on a cycle, reads
its virtual sensors, publishes over MQTT (buffering locally if the
broker is unreachable), and sleeps according to the power manager.

Run with the ingestion backend (app.main) already running to see
readings flow through to the dashboard in real time:

    python simulate_device.py
"""
import logging
import time

from app.config import settings
from app.mqtt_client import DeviceClient
from app.power import PowerManager
from app.sensors import make_default_sensors

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("embedwatch.simulate_device")


def run(cycles: int | None = None) -> None:
    sensors = make_default_sensors()
    client = DeviceClient(settings.mqtt_host, settings.mqtt_port, settings.mqtt_topic_prefix)
    power = PowerManager(
        normal_interval=settings.sensor_interval_seconds,
        low_battery_interval=settings.sensor_interval_seconds * 4,
        low_battery_threshold=settings.low_battery_threshold,
    )

    client.connect()
    time.sleep(1)  # give the client a moment to connect before the first publish

    count = 0
    try:
        while cycles is None or count < cycles:
            for sensor in sensors:
                reading = sensor.read()
                sent = client.publish(reading)
                status = "sent" if sent else "buffered"
                logger.info("%s: %s %s%s (%s)", reading.sensor_id, reading.value, reading.unit, "", status)

            sleep_for = power.tick()
            count += 1
            time.sleep(sleep_for)
    except KeyboardInterrupt:
        logger.info("stopping device simulator")
    finally:
        client.disconnect()


if __name__ == "__main__":
    run()
