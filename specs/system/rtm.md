# Requirements Traceability Matrix

**System:** mqttlogger
**Feature:** 004-remove-init-legacy (reviewed; originally 002-mqttlogger-baseline); 009-schema-evolution (updated)
**Date:** 2026-05-12 (last architecture review); 2026-05-17 (feature 009 update)
**Status:** DRAFT — updated by feature 009 requirements
**Last Updated By:** se-requirements skill (feature 009)

---

## Purpose

Maps every requirement to its source artifact, the architectural element that implements it, and the V&V event that will verify it. Every row in this matrix must have an entry in all columns before the phase closes.

---

## Column Definitions

| Column | Description |
| ------ | ----------- |
| Req ID | Requirement identifier from requirements-register.md |
| Short Description | One-line summary |
| Source Artifact | ConOps SC, NFR, Risk, or constraint that originated the requirement |
| Design Element | Container, component, or configuration artifact that satisfies the requirement |
| V&V Method | T=Test, A=Analysis, I=Inspection, D=Demonstration |
| V&V Stage | UT=Unit Test, IT=Integration Test, ST=System Test, AT=Acceptance Test, —=No runtime stage |
| Status | Planned / Implemented / Validated |

---

## Section 1 — Core Logger (FR-001 through FR-014)

| Req ID | Short Description | Source Artifact | Design Element | V&V Method | V&V Stage | Status |
| ------ | ----------------- | --------------- | -------------- | ---------- | --------- | ------ |
| FR-001 | MQTT subscription — receive all messages on configured topic filter | SC-CONOPS-001, NEED-STK-001-001 | `mqtt_client.py::on_connect()` subscribes; `mqtt` (Mosquitto) delivers | T | ST | Implemented |
| FR-002 | Message parsing — device, timestamp, value from payload | SC-CONOPS-001, `data_model.py` | `mqtt_client.py::on_message()` parses; `data_model.py::SensorReading` model | T | IT | Implemented |
| FR-003 | Persistent storage — committed to MariaDB before considered captured | SC-CONOPS-001, NFR-PERF-001 | `mqtt_client.py::insert()` → `mariadb` container; ADR-001 (synchronous) | T | ST | Implemented |
| FR-004 | Broker reconnection — automatic, no operator intervention | MODE-004, NFR-REL-001 | `paho-mqtt` loop reconnect; `mqtt_client.py::on_connect()` re-subscribes | D | ST | Implemented |
| FR-005 | DB write failure — log, discard, continue | MODE-005, NFR-REL-001 | `mqtt_client.py::insert()` try/except → log + return; ADR-003 | D | ST | Implemented |
| FR-006 | Lifecycle event logging — all 8 event types | NFR-USE-002, Constitution IV | `mqtt_client.py`, `app.py` structured log calls; Python logging formatter | I | ST | Implemented |
| FR-007 | Graceful shutdown — clean exit ≤ 10 s on SIGTERM/SIGINT | MODE-003, NFR-REL-001 | `app.py` signal handlers → `loop.stop()`; paho clean disconnect | T | ST | Implemented |
| FR-008 | External configuration — no hardcoded values | NFR-SEC-001, Constitution II | `db_connection.py::load_config_file()`; `config.json` (gitignored) | I | — | Implemented |
| FR-009 | Non-root container execution | Constitution III | `Dockerfile` USER directive (non-root UID) | I | — | Implemented |
| FR-010 | Docker Compose deployment — single command, full stack | NFR-PORT-001, Constitution III | `docker-compose.yml` (all 6 services); `depends_on` healthcheck ordering | D | ST | Implemented |
| FR-011 | Startup validation — reject on missing/invalid config with specific error | NFR-USE-001, MODE-002 | `db_connection.py` validation; `mqtt_client.py` connection error handling | T | ST | Implemented |
| FR-012 | Bounded log files — rotating with size and count limits | Constitution IV | `app.py` `RotatingFileHandler`; json-file driver in `docker-compose.yml` | I | — | Implemented |
| FR-013 | MQTT LWT — broker publishes "offline" on unexpected disconnect | RISK-016, NFR-REL-001 | `app.py` `client.will_set()` before `connect()` | T | ST | Implemented |
| FR-014 | HTTP liveness heartbeat — push every interval; skip if no URL | OPT-A, RISK-016 | `heartbeat.py::HeartbeatThread` daemon thread; ADR-006 | T | IT | Implemented |

---

## Section 2 — Monitoring Stack (FR-MON-001 through FR-MON-007)

| Req ID | Short Description | Source Artifact | Design Element | V&V Method | V&V Stage | Status |
| ------ | ----------------- | --------------- | -------------- | ---------- | --------- | ------ |
| FR-MON-001 | Crash notification ≤ 120 s | OPT-A, RISK-016, SC-CONOPS-003 | `heartbeat.py` → `uptime_kuma` → `ntfy`; ADR-006; 60 s interval, 2× threshold | T | ST | **Validated** (IP-001: mean 93 s, max 120 s, 3/3) |
| FR-MON-002 | Sensor silence alert — periodic sensor absent > gap window | OPT-B, RISK-013 | `companion_monitor/monitor.py::run_check()` gap detection; `sensors.yml` sensor list; ADR-007 | D | ST | **Validated** (IP-001: attic humidity silence correctly detected) |
| FR-MON-003 | Sensor recovery notification | OPT-B, MODE-001 | `companion_monitor/monitor.py::run_check()` recovery path; `alerted_missing` set removal | D | ST | **Validated** (IP-001: attic humidity recovery notification confirmed) |
| FR-MON-004 | Unknown sensor detection — unrecognized sensor triggers alert | OPT-B, RISK-013 | `companion_monitor/monitor.py::run_check()` unknown detection; `sensors.yml` excluded list; ADR-007 | D | ST | **Validated** (IP-001: 3 dining room sensors auto-detected) |
| FR-MON-005 | Alert fires on state transition only — not every poll cycle | OPT-B design | `companion_monitor/monitor.py` in-memory sets `alerted_missing`, `alerted_unknown` | T | IT | Implemented |
| FR-MON-006 | Local push notification — fully LAN-only to operator device | No-cloud constraint, explore-summary | `ntfy` container (binwiederhier/ntfy); `monitoring_net`; iPhone ntfy app → LAN IP; ADR-005 | D | AT | Implemented |
| FR-MON-007 | Configurable monitoring parameters via environment variables | Constitution II, NFR-SEC-001 | `companion_monitor/monitor.py` env var reads (POLL_INTERVAL_SECONDS, GAP_WINDOW_MINUTES, etc.) | I | — | Implemented |

---

## Section 3 — Non-Functional Requirements

| NFR ID | Short Description | Source Artifact | Design Element | V&V Method | V&V Stage | Status |
| ------ | ----------------- | --------------- | -------------- | ---------- | --------- | ------ |
| NFR-PERF-001 | Message completeness — no drops under normal load | NEED-STK-001-001 | Synchronous in-callback write (ADR-001); paho single-threaded delivery | T | ST | Planned |
| NFR-PERF-002 | Timestamp fidelity within sensor publication interval | NEED-STK-001-010/011 | Co-hosted broker → sub-ms LAN latency; NTP host clock sync | A | — | Planned |
| NFR-REL-001 | Auto-recovery from all software faults | MODE-004/005, NEED-STK-001-004 | `restart: unless-stopped` (ADR-004); paho reconnect; discard-on-fail (ADR-003) | D | ST | Planned |
| NFR-REL-002 | Recovery ≤ 60 s after container crash | Operator-stated target | `restart: unless-stopped`; MariaDB healthcheck; paho fast reconnect (co-hosted broker) | T | ST | Planned |
| NFR-SEC-001 | Credentials not in version control | RISK-002, TBD-004 | `config.json` gitignored; `sensors.yml` gitignored; `.gitignore` verified | I | — | Planned |
| NFR-USE-001 | Error messages identify field, source, value | NEED-STK-001-007 | `db_connection.py` validation errors; `mqtt_client.py` connection error messages | T | ST | Planned |
| NFR-USE-002 | Log entries contain all 6 required fields | NEED-STK-001-002/006 | Python `logging.Formatter` in `app.py` with all 6 fields | I | ST | Planned |
| NFR-MAIN-001 | Test coverage ≥ 80% line coverage (Should Have) | Constitution VI, TBD-002 | pytest + pytest-cov; `mqttlogger/` 86% (feature 003); ~93% projected (feature 004); GitHub Actions CI enforces 80% gate | T | UT+IT | Implemented |
| NFR-PORT-001 | Docker Compose on Linux amd64/arm64 | Constitution III | `docker-compose.yml`; Linux amd64 deployment on sietchtabr | D | ST | Planned |
| NFR-INT-001 | DB schema owned by mqttlogger; all changes via migrations | NEED-STK-001-008, Constitution VII | `data_model.py` SQLAlchemy schema; migration scripts (audit required — RISK-019) | I | — | Planned |
| NFR-PERF-003 | Composite index (location, measurement_type, captured_at) | NEED-STK-001-010 | `db/migration-009-schema-evolution.sql` | I | ST | Planned |
| NFR-INT-002 | Non-logger consumers connect read-only; no write privileges | NEED-STK-001-008, -011 | MariaDB read-only user; `docker-compose.yml` companion_monitor env | I | ST | Planned |
| NFR-INT-003 | captured_at DATETIME NOT NULL on base table; no computed expressions downstream | NEED-STK-001-010 | `db/migration-009-schema-evolution.sql`; `data_model.py`; `mqtt_client.py`; `monitor.py` | I | ST | Planned |
| NFR-MAIN-002 | Migration script atomicity — no partial state on failure | SCN-008, RISK-027 | `db/migration-009-schema-evolution.sql` transaction structure | I | — | Planned |

---

## Section 5 — Schema Evolution (FR-023..FR-036, Feature 009)

| Req ID | Short Description | Source Need | Design Element | V&V Method | V&V Stage | Status |
| ------ | ----------------- | ----------- | -------------- | ---------- | --------- | ------ |
| FR-023 | Migration adds captured_at DATETIME NOT NULL; backfills from TIMESTAMP(currentdate, currenttime) | NEED-STK-001-008, -010 | `db/migration-009-schema-evolution.sql` (to be created) | I+T | ST | Planned |
| FR-024 | Migration adds location TEXT NOT NULL; backfills from topic segments 2–3 | NEED-STK-001-008, -010 | `db/migration-009-schema-evolution.sql` | I+T | ST | Planned |
| FR-025 | Migration adds measurement_type TEXT NOT NULL; backfills from final topic segment | NEED-STK-001-008, -010 | `db/migration-009-schema-evolution.sql` | I+T | ST | Planned |
| FR-026 | Migration creates composite index idx_loc_mtype_time | NEED-STK-001-010 | `db/migration-009-schema-evolution.sql` | I | ST | Planned |
| FR-027 | Migration drops currentdate and currenttime columns | NEED-STK-001-008 | `db/migration-009-schema-evolution.sql` | I+T | ST | Planned |
| FR-028 | SensorReading model: captured_at DateTime NOT NULL; no currentdate/currenttime | NEED-STK-001-008 | `mqttlogger/data_model.py::SensorReading` | I | — | Planned |
| FR-029 | SensorReading model: location Text NOT NULL | NEED-STK-001-008 | `mqttlogger/data_model.py::SensorReading` | I | — | Planned |
| FR-030 | SensorReading model: measurement_type Text NOT NULL | NEED-STK-001-008 | `mqttlogger/data_model.py::SensorReading` | I | — | Planned |
| FR-031 | on_message sets captured_at = datetime.now() | NEED-STK-001-001, -010 | `mqttlogger/mqtt_client.py::on_message()` | T | IT | Planned |
| FR-032 | on_message sets location from topic segments 2+3 | NEED-STK-001-010 | `mqttlogger/mqtt_client.py::on_message()` | T | IT | Planned |
| FR-033 | on_message sets measurement_type from final topic segment | NEED-STK-001-010 | `mqttlogger/mqtt_client.py::on_message()` | T | IT | Planned |
| FR-034 | monitor.py query_active_sensors() uses captured_at; no TIMESTAMP() | NEED-STK-001-002, -009 | `companion-monitor/monitor.py::query_active_sensors()` | I | — | Planned |
| FR-035 | bootstrap_sensors.py uses DATE(captured_at); no currentdate | NEED-STK-001-009 | `companion-monitor/bootstrap_sensors.py` | I | — | Planned |
| FR-036 | companion_monitor in docker-compose.yml uses read-only DB credentials | NEED-STK-001-008, -011 | `docker-compose.yml` companion_monitor env; MariaDB read-only user | I | ST | Planned |

---

## Section 4 — Code Quality (FR-022, Feature 004)

| Req ID | Short Description | Source Need | Design Element | V&V Method | V&V Stage | Status |
| ------ | ----------------- | ----------- | -------------- | ---------- | --------- | ------ |
| FR-022 | No dead code in mqttlogger/__init__.py | NFR-MAIN-001, NEED-STK-001-007 | `mqttlogger/__init__.py` (emptied) | I | — | Implemented — Task: T002, T007 (feature-004) |

---

## Open Items

| ID | Description | Target |
| -- | ----------- | ------ |
| RTM-OI-001 | CLOSED — NFR-MAIN-001 test suite established by feature 003-cicd-pipeline; CI enforces 80% coverage gate | Closed by 003-cicd-pipeline |
| RTM-OI-002 | NFR-INT-001 design element depends on RISK-019 schema audit completing | Phase 4+ |
| RTM-OI-003 | FR-MON-006 stage is AT (acceptance test) because it requires the operator's iPhone on the home LAN; cannot be fully verified in an isolated test environment | Phase 6 |
