# EmbedWatch

A real-time IoT monitoring simulator. Virtual sensors publish readings over MQTT to a backend that persists them and streams them live to a dashboard — the full pipeline a real embedded fleet would use, minus actual hardware.

## Why a simulator

Real hardware (an ESP32 with real sensors) adds shipping delays and hardware debugging that aren't the point of this project — the interesting part is the system design: how a device handles network loss, how a backend ingests a stream of readings, how a dashboard stays in sync in real time. All three are implemented and tested exactly as they would be against real hardware; the only thing simulated is the sensor data itself.

The MQTT layer is real — not mocked. Tests connect to an actual Mosquitto broker (locally or in CI), publish real messages, and verify they arrive, persist, and reach the dashboard.

## What it does

- **Virtual sensors** (`app/sensors.py`) produce realistic data via a small random walk, not pure noise — temperature, humidity, and battery level.
- **Power manager** (`app/power.py`) simulates a low-power sleep/wake cycle: as the simulated battery drains, the device switches to a longer interval between readings, logging every decision.
- **Local buffer** (`app/buffer.py`) queues readings when the device can't reach the broker, and flushes them automatically once reconnected — no data lost to a network blip.
- **Ingestion backend** (`app/ingestion.py`) subscribes to the sensor topics, persists each reading to SQLite, and broadcasts it to connected dashboard clients.
- **Live dashboard** (`static/index.html`) shows incoming readings over a WebSocket, with automatic reconnection if the connection drops.

## Stack

Python 3.12, FastAPI, paho-mqtt, SQLAlchemy (SQLite), Mosquitto (MQTT broker), vanilla JS/WebSocket for the dashboard.

## Running it locally

### 1. Install and start a local Mosquitto broker

macOS:
```bash
brew install mosquitto
mosquitto -c .mosquitto/mosquitto.conf
```

Linux:
```bash
sudo apt-get install mosquitto mosquitto-clients
mosquitto -c .mosquitto/mosquitto.conf
```

Keep this running in its own terminal.

### 2. Install dependencies and start the backend

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements-dev.txt
cp .env.example .env

uvicorn app.main:app --reload
```

Open `http://localhost:8000` — you'll see an empty dashboard waiting for data.

### 3. Run the simulated device

In a third terminal (same venv):
```bash
python simulate_device.py
```

Watch the dashboard update live as readings come in. Stop it with `Ctrl+C` — it disconnects cleanly, and any reading taken right as you kill it gets buffered rather than lost (try killing the Mosquitto broker instead, to see the buffering/reconnect behavior directly).

## Running tests

Tests need a reachable Mosquitto broker (same as step 1 above); tests that need it are automatically skipped if none is found, with a clear reason in the test report.

```bash
pytest -v
```

17 tests: sensor/power/buffer unit tests that need no broker, plus real end-to-end integration tests that publish over actual MQTT and verify the data reaches storage and the WebSocket feed.

## Security scanning

```bash
bandit -r app/ -ll
safety check -r requirements.txt
```

Both run automatically in CI against a real Mosquitto service container (`.github/workflows/ci.yml`).

## Project structure

```
app/
├── main.py          # FastAPI app: dashboard route, REST history, WebSocket feed
├── config.py          # Environment-based configuration
├── sensors.py           # Virtual sensors (random-walk data generation)
├── power.py               # Sleep/wake cycle simulation
├── buffer.py                # Local buffer for offline readings
├── mqtt_client.py             # Device-side MQTT publisher with reconnect/flush
├── ingestion.py                 # Backend-side MQTT subscriber + persistence
├── ws_manager.py                  # WebSocket broadcast to dashboard clients
├── database.py                      # SQLAlchemy connection
├── models.py                          # ReadingRecord model
└── schemas.py                           # Pydantic output schema

simulate_device.py   # Entry point: runs the simulated device standalone
static/index.html      # Live dashboard (WebSocket client)

tests/
├── test_sensors.py          # Sensor bounds and variation
├── test_power.py              # Sleep/wake decision logic
├── test_buffer.py               # Buffer queue/drain behavior
├── test_mqtt_integration.py       # Real MQTT publish/subscribe, offline buffering
└── test_ingestion_integration.py    # Full pipeline: MQTT -> storage -> WebSocket
```

## Known limitations

This is a learning/demo project, not a production deployment. In particular:
- No TLS/authentication on the MQTT connection (fine for local simulation; a real deployment would need both).
- Single SQLite file, no retention/archiving policy for old readings.
- The dashboard has no historical charting yet — only a live table of the most recent readings.
