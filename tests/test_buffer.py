"""Local buffer: readings go in, come back out in order, and the buffer
empties after a drain."""
from app.buffer import LocalBuffer
from app.sensors import Reading


def _reading(sensor_id="s1", value=1.0):
    return Reading(sensor_id=sensor_id, sensor_type="temperature", value=value, unit="°C")


def test_add_increases_length():
    buf = LocalBuffer()
    buf.add(_reading())
    assert len(buf) == 1


def test_drain_returns_all_and_empties_buffer():
    buf = LocalBuffer()
    buf.add(_reading(value=1.0))
    buf.add(_reading(value=2.0))

    drained = buf.drain()

    assert [r.value for r in drained] == [1.0, 2.0]
    assert len(buf) == 0


def test_buffer_respects_max_size():
    buf = LocalBuffer(max_size=3)
    for i in range(10):
        buf.add(_reading(value=float(i)))
    assert len(buf) == 3
    drained = buf.drain()
    assert [r.value for r in drained] == [7.0, 8.0, 9.0]


def test_to_payload_is_valid_json_with_expected_fields():
    import json
    payload = LocalBuffer.to_payload(_reading(sensor_id="s9", value=3.5))
    data = json.loads(payload)
    assert data["sensor_id"] == "s9"
    assert data["value"] == 3.5
