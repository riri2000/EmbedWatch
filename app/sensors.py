"""Virtual sensors: generate realistic-looking readings without any real
hardware. Each sensor does a small random walk around a baseline rather
than pure noise, so a reading history looks like something a real
temperature/humidity probe would produce.
"""
import random
import time
from dataclasses import dataclass, field


@dataclass
class Reading:
    sensor_id: str
    sensor_type: str
    value: float
    unit: str
    timestamp: float = field(default_factory=time.time)


class VirtualSensor:
    """A single simulated sensor with a slowly drifting value."""

    def __init__(
        self,
        sensor_id: str,
        sensor_type: str,
        unit: str,
        baseline: float,
        drift: float = 0.3,
        bounds: tuple[float, float] = (-1e9, 1e9),
        seed: int | None = None,
    ):
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.unit = unit
        self.bounds = bounds
        self.drift = drift
        self._value = baseline
        self._rng = random.Random(seed)  # nosec B311 — simulated data only, not security-sensitive

    def read(self) -> Reading:
        step = self._rng.uniform(-self.drift, self.drift)
        self._value = max(self.bounds[0], min(self.bounds[1], self._value + step))
        return Reading(
            sensor_id=self.sensor_id,
            sensor_type=self.sensor_type,
            value=round(self._value, 2),
            unit=self.unit,
        )


def make_default_sensors(seed: int | None = None) -> list[VirtualSensor]:
    """A small fleet of sensors representative of a simple IoT monitoring
    station (temperature, humidity, battery level)."""
    return [
        VirtualSensor("temp-01", "temperature", "°C", baseline=21.0, drift=0.2, bounds=(-10, 45), seed=seed),
        VirtualSensor("hum-01", "humidity", "%", baseline=45.0, drift=1.0, bounds=(0, 100), seed=seed),
        VirtualSensor("batt-01", "battery", "%", baseline=100.0, drift=0.0, bounds=(0, 100), seed=seed),
    ]
