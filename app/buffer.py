"""Local buffer that retains readings taken while the device can't reach
the broker, and replays them once the connection comes back — so a
network blip doesn't silently lose data.
"""
import json
import logging
from collections import deque
from dataclasses import asdict

from app.sensors import Reading

logger = logging.getLogger("embedwatch.buffer")


class LocalBuffer:
    def __init__(self, max_size: int = 1000):
        self._queue: deque[Reading] = deque(maxlen=max_size)

    def add(self, reading: Reading) -> None:
        self._queue.append(reading)
        logger.debug("buffered reading %s (%d pending)", reading.sensor_id, len(self._queue))

    def __len__(self) -> int:
        return len(self._queue)

    def drain(self) -> list[Reading]:
        """Return everything currently buffered and empty the buffer."""
        items = list(self._queue)
        self._queue.clear()
        return items

    @staticmethod
    def to_payload(reading: Reading) -> str:
        return json.dumps(asdict(reading))
