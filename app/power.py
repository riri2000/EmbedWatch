"""Simulates a microcontroller's low-power sleep/wake cycle.

Real embedded devices don't poll sensors continuously — they wake up,
take a reading, publish it, then go back to sleep to save battery. This
module reproduces that decision logic (not the actual hardware sleep,
obviously) and logs every decision, which is what we'd inspect on a real
device's serial output to debug power behavior.
"""
import logging
from dataclasses import dataclass

logger = logging.getLogger("embedwatch.power")


@dataclass
class PowerManager:
    """Decides how long to sleep between readings based on battery level.

    Below `low_battery_threshold`, the device switches to a longer sleep
    interval to conserve what's left of the battery — a common strategy
    on real low-power devices.
    """

    normal_interval: float
    low_battery_interval: float
    low_battery_threshold: float
    battery_level: float = 100.0
    drain_per_cycle: float = 0.05

    def tick(self) -> float:
        """Call once per cycle. Drains the battery a bit and returns how
        long to sleep before the next reading."""
        self.battery_level = max(0.0, self.battery_level - self.drain_per_cycle)

        if self.battery_level <= self.low_battery_threshold:
            logger.info(
                "battery at %.1f%% (<= %.1f%% threshold) — switching to low-power interval (%.1fs)",
                self.battery_level,
                self.low_battery_threshold,
                self.low_battery_interval,
            )
            return self.low_battery_interval

        logger.debug("battery at %.1f%% — normal interval (%.1fs)", self.battery_level, self.normal_interval)
        return self.normal_interval
