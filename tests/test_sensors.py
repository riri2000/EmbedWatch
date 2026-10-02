"""Virtual sensors should stay within their physical bounds and actually
vary over time (not just return a constant)."""
from app.sensors import VirtualSensor, make_default_sensors


def test_reading_stays_within_bounds():
    sensor = VirtualSensor("t1", "temperature", "°C", baseline=20.0, drift=5.0, bounds=(0, 30), seed=42)
    for _ in range(200):
        reading = sensor.read()
        assert 0 <= reading.value <= 30


def test_reading_value_changes_over_time():
    sensor = VirtualSensor("t1", "temperature", "°C", baseline=20.0, drift=2.0, seed=1)
    values = {sensor.read().value for _ in range(20)}
    # A real drifting sensor shouldn't produce the exact same value
    # twenty times in a row.
    assert len(values) > 1


def test_same_seed_is_reproducible():
    s1 = VirtualSensor("t1", "temperature", "°C", baseline=20.0, drift=2.0, seed=7)
    s2 = VirtualSensor("t1", "temperature", "°C", baseline=20.0, drift=2.0, seed=7)
    assert [s1.read().value for _ in range(10)] == [s2.read().value for _ in range(10)]


def test_default_sensor_fleet_has_expected_ids():
    sensors = make_default_sensors(seed=0)
    ids = {s.sensor_id for s in sensors}
    assert ids == {"temp-01", "hum-01", "batt-01"}
