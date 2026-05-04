# Implementation Plan: Core MQTT Sensor Logging Service

**Branch**: `001-core-mqtt-logger` | **Date**: 2026-05-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/001-core-mqtt-logger/spec.md`

## Summary

mqttlogger is a single-purpose, long-running daemon that subscribes to an Eclipse Mosquitto MQTT
broker and persists environmental sensor readings to a MariaDB database. The service is
containerized and orchestrated via Docker Compose alongside the broker and database. This plan
documents the current technical state of the existing codebase, identifies known gaps against the
constitution and specification, and establishes the data model and internal contracts to guide
remediation tasks.

## Technical Context

**Language/Version**: Python 3.10
**Primary Dependencies**: paho-mqtt 1.6.1, SQLAlchemy 1.4.41, mysqlclient 2.1.1
**Storage**: MariaDB (MySQL-compatible), single table `sensorreadings`
**Testing**: pytest, integration-first (real broker via `test.mosquitto.org`)
**Target Platform**: Linux (Docker container, amd64/arm64)
**Project Type**: Long-running background service (daemon)
**Performance Goals**: Message receipt to database commit within 5 seconds (SC-001)
**Constraints**: Non-root execution, bounded log storage (2 MB × 5 files), single-instance
**Scale/Scope**: Household scale — ~10–20 sensors at ~1 reading/minute/sensor, indefinite retention

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Single-Purpose Service — ✅ PASS

The service subscribes to MQTT and persists readings to the database only. No analytics,
alerting, or visualization logic is present in the application package. Notebooks in `notebooks/`
are correctly separated from the service.

### II. Configuration Over Code — ✅ PASS

All connection parameters (broker address/port, database host/port/name/credentials) are read
from `config.json`. No hardcoded IPs or credentials appear in application source files.

### III. Container-First Deployment — ⚠️ PARTIAL

`Dockerfile` and `docker-compose.yml` exist and the container runs as a non-root user (`appuser`).

**Known defect**: `constants.py` is not included in any `COPY` instruction in the Dockerfile.
The application package imports `constants.ROOT_DIR` at module load time; the container will
fail with `ModuleNotFoundError` on startup. Fix: add `COPY constants.py ./` to the Dockerfile.

### IV. Observability by Default — ⚠️ PARTIAL

Rotating log handler (2 MB per file, 5 files retained) and `--debug` CLI flag are implemented.
Log format includes timestamp, level, module, function, and line number.

**Known defect**: `LOG_FOLDER` creation (`LOG_FOLDER.mkdir()`) in `app.py` depends on
`constants.ROOT_DIR`, which fails inside the container because `constants.py` is missing from
the image (see Principle III). This must be resolved together with the Dockerfile fix.

### V. Graceful Lifecycle Management — ⚠️ PARTIAL

A SIGTERM handler is wired in `app.py` and calls `mqttc.loop_stop()` and `mqttc.disconnect()`.

**Known defect**: The handler calls `sys.exti(0)` — a typo; the correct call is `sys.exit(0)`.
This causes an `AttributeError` crash on shutdown instead of a clean exit, violating FR-007 and
SC-004.

### VI. Integration-Preferred Testing — ⚠️ PARTIAL

`conftest.py` correctly sets up fixtures against a real broker (`test.mosquitto.org`) and a real
MQTT client with `on_connect`, `on_message`, and `insert` callbacks. The integration test
architecture is sound.

**Known defect**: The only test in `test_mqtt_client.py` is `assert False` — the test suite has
never passed. Integration tests for the float-payload path, boolean-payload path, malformed-payload
discard behavior, and database write must be implemented.

### VII. Minimal Surface Area — ⚠️ PARTIAL

**Known defect**: `persist.sh` at the repository root is undocumented. Its purpose cannot be
determined from the file name alone. Per the constitution, undocumented scripts at the repo root
are prohibited. It must either be documented with a comment header or removed.

**Gate Decision**: Principles I and II pass cleanly. Principles III–VII have pre-existing defects
in the codebase that predate the constitution ratification. None are design-level violations that
would invalidate the plan; all are concrete, fixable bugs. Plan proceeds. All violations are
tracked as remediation tasks in `tasks.md`.

## Project Structure

### Documentation (this feature)

```text
specs/001-core-mqtt-logger/
├── plan.md              # This file
├── research.md          # Phase 0: technical decisions and rationale
├── data-model.md        # Phase 1: SensorReading entity and schema
├── quickstart.md        # Phase 1: run the stack locally
├── contracts/
│   ├── mqtt-topic-schema.md  # MQTT topic hierarchy contract
│   └── db-schema.md          # Database table schema contract
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
mqttlogger/              # Repository root
├── app.py               # Entry point: MQTT client setup, signal handling, main loop
├── config.json          # Runtime configuration (broker + database connection params)
├── constants.py         # ROOT_DIR path constant (must be added to Dockerfile COPY)
├── requirements.txt     # Pinned Python dependencies
├── Dockerfile           # Container image definition
├── docker-compose.yml   # Multi-service orchestration (mqtt, mqtt_logger, mariadb)
├── persist.sh           # [UNDOCUMENTED — must be documented or removed per constitution]
├── mosquitto/
│   └── config/
│       └── mosquitto.conf   # Mosquitto broker config (anonymous, persistent, port 1883)
├── mqttlogger/          # Application package
│   ├── __init__.py
│   ├── data_model.py    # SQLAlchemy ORM: SensorReading model + table creation helper
│   ├── db_connection.py # Config loader, MySQL connection string builder
│   └── mqtt_client.py   # MQTT callbacks: on_connect, on_message, insert
├── tests/
│   ├── conftest.py      # Integration fixtures (real broker, unique topic per run)
│   └── test_mqtt_client.py  # Integration tests (currently stubs — must be implemented)
└── notebooks/
    ├── Template Notebook.ipynb
    └── cellar_analysis.ipynb
```

**Structure Decision**: Single-project layout at repository root with no `src/` abstraction. This
is consistent with the existing codebase convention. The service is a daemon, not a library;
no additional CLI or API layer beyond the `app.py` entry point is needed or in scope.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| New SQLAlchemy engine + session created per message in `mqtt_client.insert()` | Existing behavior; correct and simple at household-scale message rates | Connection pooling adds lifecycle complexity. At ~20 msg/min, per-message engine creation adds negligible overhead. Revisit only if message rate increases by an order of magnitude. |
