# Quickstart: Core MQTT Sensor Logging Service

**Date**: 2026-05-04

This guide covers running the full mqttlogger stack locally using Docker Compose.

---

## Prerequisites

- Docker and Docker Compose installed
- A `.env` file at the repository root with the following variables:

```env
MYSQL_ROOT_PASSWORD=<choose a root password>
MYSQL_DATABASE=sensorreadings
MYSQL_USER=mqttlogger
MYSQL_PASSWORD=<choose a user password>
```

- `config.json` at the repository root configured to match the `.env` values:

```json
{
  "db_ip": "mariadb",
  "db_port": "3306",
  "db_user": "mqttlogger",
  "db_password": "<same as MYSQL_PASSWORD above>",
  "db_database": "sensorreadings",
  "mqtt_server_ip": "mqtt",
  "mqtt_server_port": 1883
}
```

---

## Start the Stack

```bash
docker compose up -d
```

This starts three services:
- **mqtt** — Eclipse Mosquitto broker (port 1883)
- **mariadb** — MariaDB database (port 3306)
- **mqtt_logger** — the logging service

Wait approximately 30 seconds for MariaDB to initialize before the logger attempts its first
connection. The `healthcheck` in `docker-compose.yml` signals readiness.

---

## Verify the Logger Is Running

```bash
docker compose logs -f mqtt_logger
```

Expected output (INFO level):

```
2026-05-04 12:00:00 | INFO     | mqttlogger.mqtt_client:on_connect:57 | Successfully subscribed to topic environment/#
```

---

## Publish a Test Message

Using the Mosquitto CLI tools (install separately or run from the broker container):

```bash
# Numeric reading
docker compose exec mqtt mosquitto_pub -h localhost -t environment/indoor/cellar_front/temperature -m "18.3"

# Boolean state
docker compose exec mqtt mosquitto_pub -h localhost -t environment/indoor/bedroom/fan_state -m "true"
```

---

## Verify a Record Was Stored

```bash
docker compose exec mariadb mysql -u mqttlogger -p sensorreadings \
  -e "SELECT * FROM sensorreadings ORDER BY id DESC LIMIT 5;"
```

---

## Enable Debug Logging

Stop the logger and restart with the debug flag:

```bash
docker compose stop mqtt_logger
docker compose run --rm mqtt_logger python app.py --debug
```

---

## Stop the Stack

```bash
docker compose down
```

The logger handles SIGTERM cleanly and disconnects from the broker before exiting.

---

## Run Tests

Tests use the public `test.mosquitto.org` broker and require internet access:

```bash
pip install -r requirements.txt
pytest tests/
```

> **Note**: The test suite currently contains stub tests (`assert False`) that will fail.
> Implementing integration tests is tracked as a remediation task.

---

## Known Issues

| Issue | Effect | Fix |
|-------|--------|-----|
| `constants.py` missing from Dockerfile | `ModuleNotFoundError` on container startup | Add `COPY constants.py ./` to Dockerfile |
| `sys.exti(0)` typo in SIGTERM handler | `AttributeError` on shutdown instead of clean exit | Fix to `sys.exit(0)` in `app.py:83` |
| Volume mounts full repo into container | Image and host dependencies can diverge | Mount only `config.json` in production |
| Test suite stubs | `pytest` always fails | Implement integration tests |
