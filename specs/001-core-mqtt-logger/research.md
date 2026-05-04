# Research: Core MQTT Sensor Logging Service

**Branch**: `001-core-mqtt-logger` | **Date**: 2026-05-04
**Input**: Existing codebase analysis + spec.md

This document records the technical decisions already embodied in the existing mqttlogger
codebase. Because this is a documentation project rather than a greenfield feature, "research"
means auditing what was chosen and why, and flagging where the current state diverges from the
specification.

---

## Decision 1: MQTT Protocol Version

**Decision**: MQTT 3.1.1 (implicit default of paho-mqtt 1.6.1)

**Rationale**: paho-mqtt 1.6.1 creates MQTT 3.1.1 clients by default. MQTT 3.1.1 is the
most widely supported version; Eclipse Mosquitto supports it fully and it is the standard for
home automation sensor networks.

**Alternatives considered**:
- MQTT 5.0: Adds session expiry, reason codes, and better reconnect semantics. Not used because
  paho-mqtt 1.6.1 predates stable MQTT 5.0 support in the library, and the added complexity is
  unnecessary at household scale.

**Spec alignment**: No MQTT version constraint in spec. MQTT 3.1.1 satisfies all FR requirements.
FR-015 (indefinite reconnect) is natively handled by paho's `loop_forever()` which auto-reconnects
on connection loss.

---

## Decision 2: MQTT Subscription Scope

**Decision**: Subscribe to `environment/#` — all topics under the `environment/` root

**Rationale**: A single wildcard subscription covers all current and future sensor locations and
reading types without requiring configuration changes when new sensors are added. The `#` wildcard
matches all levels below `environment/`.

**Alternatives considered**:
- Explicit topic subscriptions per room/type: Would require a configuration change every time a
  new sensor is deployed. Rejected as operationally brittle.
- Top-level wildcard `#`: Would capture broker control messages and unrelated topics. Rejected
  as too broad.

**Spec alignment**: FR-001 requires subscription to all topics under `environment/`. Satisfied.

---

## Decision 3: Database Session Management

**Decision**: Create a new SQLAlchemy engine and session per message in `insert()`

**Rationale**: The simplest correct approach. At household scale (~20 sensors, ~1 reading/minute
each = ~20 messages/minute), the overhead of creating a new connection per message is negligible.
SQLAlchemy's connection pool is bypassed but not needed at this throughput.

**Alternatives considered**:
- Shared connection pool (engine created once at startup): Reduces per-message overhead; adds
  lifecycle complexity (engine must be passed between callbacks or stored as global state).
  Deferred until message rate requires it.
- SQLAlchemy session-per-request pattern with scoped_session: More correct for multi-threaded
  use; overkill for a single-threaded callback model.

**Known issue**: SQLAlchemy 1.4.41 uses the legacy `declarative_base()` import path from
`sqlalchemy.ext.declarative` (deprecated; moved to `sqlalchemy.orm` in 2.0). The
`MetaData(engine)` constructor call in `data_model.py` is also deprecated. Both work in 1.4
but will break on upgrade to 2.0.

**Spec alignment**: FR-002 requires persistent storage of each message. Satisfied. SC-001
(5-second commit window) easily met at current message rates.

---

## Decision 4: Log File Parameters

**Decision**: 2 MB per file, 5 files maximum (RotatingFileHandler)

**Rationale**: 10 MB total log footprint is a practical bound for a Raspberry Pi or small home
server. At ~20 messages/minute with a compact log format, 2 MB holds approximately 50,000 log
lines — several weeks of normal operation before rotation.

**Alternatives considered**:
- TimedRotatingFileHandler (daily/weekly rotation): Size-based is more predictable on embedded
  hardware where disk space is the primary constraint.
- Configurable via config.json: Log parameters are not currently configurable at runtime.
  Could be added but adds complexity with little practical benefit for a single-operator system.

**Spec alignment**: FR-006 requires bounded log file count and size. SC-007 requires bounded disk
usage. Satisfied.

---

## Decision 5: Payload Type Coercion

**Decision**: Check for exact byte strings `b'true'` and `b'false'`; otherwise attempt `float()` cast

**Rationale**: Sensor firmware in home automation systems commonly publishes boolean states as
the literal strings "true" and "false". Numeric sensors publish floating-point strings. Checking
exact byte strings before float conversion handles both cases without ambiguity.

**Known gap**: If payload is neither a boolean string nor a parseable float, the current code
(`float(message.payload)`) raises a `ValueError` that is not caught. This violates FR-013.
A try/except block must wrap the conversion and log + discard on failure.

**Spec alignment**: FR-003 (boolean to numeric), FR-013 (malformed payload handling). FR-003
satisfied; FR-013 not yet implemented.

---

## Decision 6: Broker Authentication

**Decision**: Anonymous connections (no credentials)

**Rationale**: The broker (`mosquitto.conf`: `allow_anonymous true`) runs on a private home
network with no public exposure. Credential management adds operational overhead with no
meaningful security benefit in this deployment context. Clarified in session 2026-05-04.

**Spec alignment**: FR-008 (anonymous, no broker credentials in config). Satisfied.

---

## Decision 7: Container Orchestration

**Decision**: Docker Compose with three services on isolated bridge networks

**Rationale**: Two isolated networks (`mqtt_net` for broker↔logger traffic, `mqtt_db` for
logger↔database traffic) provide defense-in-depth at the network level even on a local host.
The broker is not reachable from the database network and vice versa.

**Known defect**: The `mqtt_logger` service mounts the full repository as a volume
(`./:/code`). This means the container image's dependencies and the host's working directory
can diverge. In production, volumes should mount only configuration files, not the full source.

**Spec alignment**: FR-010 (single orchestration command), FR-012 (database healthcheck present
for mariadb). Both satisfied in docker-compose.yml.

---

## Open Items (Deferred)

The following edge cases from the spec are not resolved by existing code and are deferred to
task implementation:

- **Retained message flood on (re)connect**: paho-mqtt delivers retained messages synchronously
  on subscribe. A large number of retained messages will queue up in the `on_message` callback.
  At household scale this is unlikely to be a problem, but no explicit throttle exists.

- **Disk exhaustion during log rotation**: If the filesystem is full, `RotatingFileHandler`
  will raise an `OSError` that will propagate to the logging framework. Python's logging module
  silently suppresses most handler errors by default (`logging.raiseExceptions = False` in
  production). This means disk exhaustion would silently disable logging but not crash the
  service — acceptable behavior.
