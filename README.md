# mqttlogger

A lightweight daemon that subscribes to an Eclipse Mosquitto MQTT broker and persists
every sensor reading to a MariaDB database. Designed for continuous, unattended operation
on a home network.

## What it does

- Subscribes to all topics under `environment/#` on the configured MQTT broker
- Stores each reading as a timestamped record (date, time, topic, value) in MariaDB
- Converts boolean payloads (`true`/`false`) to `1.0`/`0.0` for uniform numeric storage
- Logs connection, subscription, message, and error events to rotating log files
- Handles SIGTERM cleanly — finishes any in-flight write before disconnecting

## Quick start

See [specs/001-core-mqtt-logger/quickstart.md](specs/001-core-mqtt-logger/quickstart.md)
for the full local setup guide (Docker Compose, config file, test messages).

## Configuration

Copy `config.json` and fill in your broker and database details:

```json
{
  "mqtt_server_ip": "mqtt",
  "mqtt_server_port": 1883,
  "db_ip": "mariadb",
  "db_port": "3306",
  "db_user": "mqttlogger",
  "db_password": "<password>",
  "db_database": "sensorreadings"
}
```

All connection parameters are read from this file at startup. Missing or malformed
configuration causes an immediate exit with a descriptive error message.

## Running the stack

```bash
docker compose up -d
```

## Running tests

```bash
pip install -r requirements.txt
pytest tests/                        # all tests (requires local Mosquitto on :1883)
pytest -m "not integration"          # unit tests only (no broker needed)
```

## Specification

Full requirements, acceptance criteria, and design documents are in
[specs/001-core-mqtt-logger/spec.md](specs/001-core-mqtt-logger/spec.md).
