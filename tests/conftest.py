"""Test-wide setup: points the app at a disposable SQLite file and a
dedicated MQTT topic prefix, so tests never touch a real deployment's
database or collide with other traffic on the broker.

These must be set before anything imports app.config, since pydantic
reads them once at import time — that's why this file has no fixtures,
just module-level code that runs before pytest collects any test module.
"""
import os
import tempfile

_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_db_path}")
os.environ.setdefault("MQTT_TOPIC_PREFIX", "embedwatch/test")
