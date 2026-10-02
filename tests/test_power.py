"""Power manager: battery should drain over time, and the sleep interval
should lengthen once the low-battery threshold is crossed."""
from app.power import PowerManager


def test_battery_drains_each_tick():
    pm = PowerManager(normal_interval=2.0, low_battery_interval=8.0, low_battery_threshold=20.0, drain_per_cycle=1.0)
    start = pm.battery_level
    pm.tick()
    assert pm.battery_level < start


def test_normal_interval_used_above_threshold():
    pm = PowerManager(
        normal_interval=2.0, low_battery_interval=8.0, low_battery_threshold=20.0,
        battery_level=100.0, drain_per_cycle=1.0,
    )
    assert pm.tick() == 2.0


def test_low_power_interval_used_below_threshold():
    pm = PowerManager(
        normal_interval=2.0, low_battery_interval=8.0, low_battery_threshold=20.0,
        battery_level=19.0, drain_per_cycle=1.0,
    )
    assert pm.tick() == 8.0


def test_battery_never_goes_negative():
    pm = PowerManager(
        normal_interval=2.0, low_battery_interval=8.0, low_battery_threshold=20.0,
        battery_level=0.5, drain_per_cycle=5.0,
    )
    pm.tick()
    assert pm.battery_level == 0.0
