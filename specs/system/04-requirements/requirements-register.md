# Requirements Register

**System:** mqttlogger
**Feature:** 004-remove-init-legacy (updated; originally 002-mqttlogger-baseline); 009-schema-evolution (updated)
**Date:** 2026-05-12 (last quality gate); 2026-05-17 (feature 009 update)
**Status:** DRAFT — feature 009 requirements added; quality gate not yet run on new entries
**Last Updated By:** se-requirements skill (feature 009)

---

## Overview

This register captures functional requirements for the mqttlogger system, grouped by subsystem. Requirements are derived from ConOps success criteria, operational modes, NFRs, and the IP-002 convergence decision (both OPT-A and OPT-B selected).

All requirements satisfy the IEEE 29148 quality attributes: Necessary · Unambiguous · Verifiable · Consistent · Complete · Singular · Feasible · Traceable.

---

## Requirement Quality Legend

| Attribute | Assessed? |
|-----------|-----------|
| Necessary | Each requirement traces to at least one ConOps criterion, operational mode, NFR, or risk |
| Unambiguous | Single interpretation; measurable acceptance criteria stated |
| Verifiable | Verification method exists in the V&V plan |
| Consistent | No stated conflicts between requirements in this register |
| Complete | All known needs from ConOps and exploration are covered |
| Singular | Each requirement states one thing |
| Feasible | All requirements are demonstrated or demonstrable in the existing implementation |
| Traceable | Each requirement traces to a source artifact ID |

---

## Section 1 — Core Logger (Existing System)

These requirements describe what the core `mqtt_logger` service must do. They formalise existing implemented behaviour as part of the baseline.

---

### FR-001 — MQTT Subscription

**Statement:** The system shall subscribe to all MQTT topics matching the configured topic filter and receive every message published to those topics by the broker.

**Source:** SC-CONOPS-001, NEED-STK-001-001
**Priority:** Must Have
**Verification Method:** Test (ST) — publish N messages; verify N records appear in the database
**Status:** Implemented

---

### FR-002 — Message Parsing

**Statement:** The system shall parse each received MQTT message payload into a sensor reading record containing: device identifier (topic path), capture timestamp (UTC), and measured value.

**Source:** SC-CONOPS-001, data-model.py (SensorReading)
**Priority:** Must Have
**Verification Method:** Test (IT) — send a known payload; verify database row contains correct device, timestamp, and value fields
**Status:** Implemented

---

### FR-003 — Persistent Storage

**Statement:** The system shall persistently write each parsed sensor reading to the configured MariaDB database. A reading is considered captured only when the database transaction has committed.

**Source:** SC-CONOPS-001, NFR-PERF-001
**Priority:** Must Have
**Verification Method:** Test (ST) — publish N messages; verify N rows committed in database; kill the container before commit to verify partial-write handling
**Status:** Implemented

---

### FR-004 — Broker Reconnection

**Statement:** The system shall reconnect to the MQTT broker automatically after any connection loss without operator intervention, and shall resume capture as soon as the broker is available.

**Source:** MODE-004, NFR-REL-001, SC-CONOPS-005
**Priority:** Must Have
**Verification Method:** Demonstration (ST) — stop broker; verify reconnect on restart; no operator action
**Status:** Implemented

---

### FR-005 — Database Write Failure Handling

**Statement:** The system shall log an error and discard any message for which the database write fails, then continue processing subsequent messages without interruption or restart.

**Source:** MODE-005, NFR-REL-001
**Priority:** Must Have
**Verification Method:** Demonstration (ST) — make database unreachable during operation; verify service continues; verify failed writes are logged and discarded
**Status:** Implemented

---

### FR-006 — Lifecycle Event Logging

**Statement:** The system shall emit a structured log entry for each of the following lifecycle events: broker connect, broker disconnect, message received, database write success, database write failure, startup complete, and shutdown initiated.

**Source:** NFR-USE-002, Constitution Principle IV (Observability by Default)
**Priority:** Must Have
**Verification Method:** Inspection (ST) — exercise startup, normal operation, error, and shutdown; verify every log entry contains all six required fields (timestamp, level, module, function, line, message)
**Status:** Implemented

---

### FR-007 — Graceful Shutdown

**Statement:** The system shall respond to SIGTERM and SIGINT by: stopping MQTT message receipt, completing any in-flight database write, closing the broker connection cleanly, and exiting with status 0, all within 10 seconds of signal receipt.

**Source:** MODE-003, NFR-REL-001, Constitution Principle V, SC-CONOPS-006
**Priority:** Must Have
**Verification Method:** Test (ST) — send SIGTERM; verify clean exit within 10 seconds; verify broker shows connection closed; verify no partial DB rows
**Status:** Implemented

---

### FR-008 — External Configuration

**Statement:** The system shall load all environment-specific values — broker address and port, database credentials, subscribed topics — exclusively from an external configuration file or environment variables at startup. No environment-specific value shall be hardcoded in source code.

**Source:** NFR-SEC-001, Constitution Principle II (Configuration Over Code)
**Priority:** Must Have
**Verification Method:** Inspection — verify no credentials or addresses appear in source code; verify system starts correctly from config only
**Status:** Implemented

---

### FR-009 — Non-Root Container Execution

**Statement:** The system shall execute as a non-root user within the Docker container.

**Source:** Constitution Principle III (Container-First Deployment)
**Priority:** Must Have
**Verification Method:** Inspection — verify Dockerfile contains a USER directive with a non-root UID
**Status:** Implemented

---

### FR-010 — Docker Compose Deployment

**Statement:** The system shall be deployable as a multi-container application via a single `docker compose up -d` command, with the full stack (MQTT broker, logger service, MariaDB database) starting and reaching healthy state without manual intervention.

**Source:** NFR-PORT-001, Constitution Principle III
**Priority:** Must Have
**Verification Method:** Demonstration (ST) — run `docker compose up -d` on a clean Linux amd64 host; verify logger connects, receives a test message, and writes to the database
**Status:** Implemented

---

### FR-011 — Startup Configuration Validation

**Statement:** The system shall reject startup if any required configuration field is absent or invalid. On rejection, the system shall emit an error message that identifies: (a) the specific field name, (b) the configuration source (file or environment variable), and (c) the value that was attempted, where applicable.

**Source:** NFR-USE-001, MODE-002
**Priority:** Must Have
**Verification Method:** Test (ST) — provide each class of invalid input; verify resulting error message names field, source, and attempted value
**Status:** Implemented

---

### FR-012 — Bounded Log Files

**Statement:** The system shall write log output to rotating files with a configured maximum size per file and a configured maximum number of retained files. Log size shall not grow unboundedly.

**Source:** Constitution Principle IV (Observability by Default)
**Priority:** Must Have
**Verification Method:** Inspection — verify logging configuration uses RotatingFileHandler or equivalent with non-zero size and count limits
**Status:** Implemented

---

### FR-013 — MQTT Last Will and Testament

**Statement:** The system shall register a Last Will and Testament (LWT) message with the broker before establishing its connection. The LWT shall publish to a designated status topic with the value `"offline"` so that the broker delivers this message automatically if the connection is unexpectedly dropped.

**Source:** OPT-A evaluation log (LWT observable), NFR-REL-001
**Priority:** Should Have
**Verification Method:** Test (ST) — kill the logger process without SIGTERM; verify broker publishes `"offline"` to the status topic
**Status:** Implemented

---

### FR-014 — HTTP Liveness Heartbeat

**Statement:** The system shall emit an HTTP push to a configurable heartbeat endpoint at a configurable interval (default 60 seconds) when a heartbeat URL is present in configuration. If no heartbeat URL is configured, the heartbeat shall be silently skipped.

**Source:** OPT-A, RISK-016
**Priority:** Should Have
**Verification Method:** Test (IT) — configure a heartbeat URL; verify HTTP push occurs at the configured interval; verify no error when URL is absent
**Status:** Implemented

---

## Section 2 — Monitoring Stack (New — IP-001/IP-002)

These requirements describe the passive monitoring capability added by the OPT-A + OPT-B converged solution. They are new requirements derived from the IP-002 convergence decision.

---

### FR-MON-001 — Process Crash Notification

**Statement:** The monitoring system shall notify the operator when the mqttlogger container has not sent a liveness heartbeat for more than 2× the configured heartbeat interval (nominally 120 seconds).

**Source:** OPT-A convergence decision, RISK-016, SC-CONOPS-003
**Priority:** Must Have
**Verification Method:** Test (ST) — kill the logger container; measure elapsed time to operator notification; verify ≤ 120 seconds (fault injection evidence: mean 93 s, max 120 s — 3/3 runs)
**Status:** Validated (IP-001 PASS)

---

### FR-MON-002 — Periodic Sensor Silence Alert

**Statement:** The monitoring system shall notify the operator when a periodic sensor that is listed in the known sensor configuration has not published any reading to the database within a configurable gap window.

**Source:** OPT-B convergence decision, RISK-013, SC-CONOPS-003
**Priority:** Must Have
**Verification Method:** Demonstration (ST) — stop a sensor from publishing for the gap window duration; verify notification is received; verify recovery notification when sensor resumes
**Status:** Validated (IP-001 PASS — attic humidity silence correctly detected)

---

### FR-MON-003 — Sensor Recovery Notification

**Statement:** The monitoring system shall notify the operator when a sensor that was previously detected as silent resumes publishing to the database.

**Source:** OPT-B, ConOps MODE-001 (normal operation resumption)
**Priority:** Should Have
**Verification Method:** Demonstration (ST) — allow a silenced sensor to resume; verify recovery notification is sent
**Status:** Validated (IP-001 PASS — attic humidity recovery notification confirmed genuine)

---

### FR-MON-004 — Unknown Sensor Detection

**Statement:** The monitoring system shall notify the operator when a sensor whose topic is not present in the known sensor configuration and is not listed in the excluded (event-driven) sensors list publishes readings to the database.

**Source:** OPT-B convergence decision, RISK-013 (silent topology change)
**Priority:** Must Have
**Verification Method:** Demonstration (ST) — allow a new sensor to publish; verify notification is received within one polling interval; verify excluded sensors do not trigger alerts
**Status:** Validated (IP-001 PASS — 3 new dining room sensors surfaced automatically during 24h baseline)

---

### FR-MON-005 — Alert State Transition Logic

**Statement:** The monitoring system shall track alert state in memory so that each alert fires exactly once on transition (normal → alert, alert → normal), not on every polling cycle.

**Source:** OPT-B design, NEED-STK-001-002 (failures must surface visibly, not flood)
**Priority:** Must Have
**Verification Method:** Test (IT) — sustain a sensor silence for multiple poll cycles; verify exactly one alert notification is sent; verify one recovery notification on resume
**Status:** Implemented (in-memory sets `alerted_missing`, `alerted_unknown` in monitor.py)

---

### FR-MON-006 — Local Push Notification Delivery

**Statement:** All monitoring notifications shall be delivered via a self-hosted push notification server without requiring any internet connectivity. The full path from event detection to operator device notification shall function on an isolated local network.

**Source:** IP-001 constraint (no cloud dependency), solution constraints in explore-summary.md
**Priority:** Must Have
**Verification Method:** Demonstration — block outbound internet on the host; verify notifications still arrive on operator device via LAN-connected notification server
**Status:** Implemented (ntfy self-hosted on local network; phone app connects to LAN IP)

**Acceptance Constraint:** This requirement is satisfied only when the operator's iPhone is connected to the home Wi-Fi network. The ntfy app connects directly to the LAN IP of the ntfy container; there is no cloud relay. An alert generated while the operator is away from home will not be delivered to the device until the device reconnects to the home network. This is a known operational limitation, accepted at IP-002 convergence. See RISK-023.

---

### FR-MON-007 — Configurable Monitoring Parameters

**Statement:** The monitoring system shall accept the following parameters exclusively via environment variables: polling interval (seconds), gap window (minutes), database connection details, notification server URL, and sensor configuration file path. No monitoring parameter shall be hardcoded.

**Source:** Constitution Principle II (Configuration Over Code), NFR-SEC-001
**Priority:** Must Have
**Verification Method:** Inspection — verify all parameters are read from environment variables in monitor.py; verify no hardcoded thresholds
**Status:** Implemented

---

## Section 3 — Traceability Summary

| Req ID | ConOps SC | Risk(s) | NFR(s) | Status |
|--------|-----------|---------|--------|--------|
| FR-001 | SC-CONOPS-001 | — | NFR-PERF-001 | Implemented |
| FR-002 | SC-CONOPS-001 | — | NFR-PERF-001 | Implemented |
| FR-003 | SC-CONOPS-001 | — | NFR-PERF-001 | Implemented |
| FR-004 | SC-CONOPS-005 | — | NFR-REL-001 | Implemented |
| FR-005 | — | — | NFR-REL-001 | Implemented |
| FR-006 | SC-CONOPS-006 | — | NFR-USE-002 | Implemented |
| FR-007 | SC-CONOPS-006 | — | NFR-REL-001 | Implemented |
| FR-008 | — | RISK-002 | NFR-SEC-001 | Implemented |
| FR-009 | — | — | NFR-PORT-001 | Implemented |
| FR-010 | — | — | NFR-PORT-001 | Implemented |
| FR-011 | — | — | NFR-USE-001 | Implemented |
| FR-012 | — | — | NFR-USE-002 | Implemented |
| FR-013 | — | RISK-016 | NFR-REL-001 | Implemented |
| FR-014 | SC-CONOPS-003 | RISK-016 | — | Implemented |
| FR-MON-001 | SC-CONOPS-003 | RISK-016 | — | Validated |
| FR-MON-002 | SC-CONOPS-003 | RISK-013 | — | Validated |
| FR-MON-003 | — | — | — | Validated |
| FR-MON-004 | SC-CONOPS-003 | RISK-013 | — | Validated |
| FR-MON-005 | — | — | — | Implemented |
| FR-MON-006 | — | — | NFR-PORT-001 | Implemented |
| FR-MON-007 | — | — | NFR-SEC-001 | Implemented |
| FR-022 | — | — | NFR-MAIN-001 | Implemented |
| FR-023 | SCN-008 | — | NFR-INT-003, NFR-MAIN-002 | Planned |
| FR-024 | SCN-008 | — | NFR-INT-003 | Planned |
| FR-025 | SCN-008 | — | NFR-INT-003 | Planned |
| FR-026 | SCN-008 | — | NFR-PERF-003 | Planned |
| FR-027 | SCN-008 | — | NFR-INT-003 | Planned |
| FR-028 | SCN-008 | — | NFR-INT-003 | Planned |
| FR-029 | SCN-008 | — | NFR-INT-003 | Planned |
| FR-030 | SCN-008 | — | NFR-INT-003 | Planned |
| FR-031 | SCN-008 | — | NFR-PERF-002 | Planned |
| FR-032 | SCN-008 | — | NFR-INT-003 | Planned |
| FR-033 | SCN-008 | — | NFR-INT-003 | Planned |
| FR-034 | SCN-008 | RISK-026 | NFR-INT-003 | Planned |
| FR-035 | SCN-008 | RISK-026 | NFR-INT-003 | Planned |
| FR-036 | — | RISK-028 | NFR-INT-002 | Planned |

---

## Quality Gate Summary

| Req ID | Quality Status | Notes |
| ------ | -------------- | ----- |
| FR-001 | PASS | |
| FR-002 | PASS | |
| FR-003 | PASS WITH WARNINGS | Singular: two-clause definition (acceptable) |
| FR-004 | PASS WITH WARNINGS | Singular: "reconnect and resume" inseparable (acceptable) |
| FR-005 | PASS WITH WARNINGS | Singular: failure-handling policy described in one statement (acceptable) |
| FR-006 | PASS WITH WARNINGS | Complete: lists 7 events, V&V plan says 8 — resolve before Phase 3 |
| FR-007 | PASS WITH WARNINGS | Singular: multi-step shutdown sequence (acceptable) |
| FR-008 | PASS WITH WARNINGS | Singular: positive+negative form of same principle (acceptable) |
| FR-009 | PASS | |
| FR-010 | PASS | |
| FR-011 | PASS WITH WARNINGS | Singular: reject+emit are inseparable (acceptable) |
| FR-012 | PASS WITH WARNINGS | Singular: redundant second clause (acceptable) |
| FR-013 | PASS WITH WARNINGS | Singular: two-sentence single capability (acceptable) |
| FR-014 | PASS WITH WARNINGS | Singular: presence+absence cases (acceptable) |
| FR-MON-001 | PASS | |
| FR-MON-002 | PASS | |
| FR-MON-003 | PASS | |
| FR-MON-004 | PASS WITH WARNINGS | Unambiguous: rewritten to resolve grammatical ambiguity |
| FR-MON-005 | PASS WITH WARNINGS | Necessary: NEED-STK-001-002 added as co-source |
| FR-MON-006 | PASS WITH WARNINGS | Singular: two sentences for same LAN-only constraint (acceptable) |
| FR-MON-007 | PASS WITH WARNINGS | Singular: positive+negative form of same principle (acceptable) |
| FR-022 | PASS | |

---

## Section 4 — Code Quality (Feature 004)

Requirements derived from NFR-MAIN-001 and the 004-remove-init-legacy feature. No new operational scenarios — the change has zero runtime-observable effect. The single requirement formalises the structural obligation that enables NFR-MAIN-001 to be satisfied.

---

### FR-022 — No Dead Code in Package Module

**Statement:** The `mqttlogger/__init__.py` file shall contain no callable definitions (functions or classes) or module-level executable statements that are not reachable from the application's production execution path or exercised by the automated test suite.

**Source:** NFR-MAIN-001, NEED-STK-001-007
**Priority:** Should Have
**Verification Method:** Inspection — verify `mqttlogger/__init__.py` contains no callable definitions; confirm zero callers for any definition found via codebase search
**IEEE 29148 Quality:** PASS on all 8 attributes
**Status:** Implemented

---

---

## Section 5 — Schema Evolution (Feature 009)

Requirements derived from SCN-008 (Live Schema Migration), NFR-INT-002, NFR-INT-003,
NFR-PERF-003, and the OPT-A convergence decision. They cover the migration script, the
updated SQLAlchemy model, the updated `on_message` handler, the updated companion monitor
queries, and the read-only database user.

All requirements trace to NEED-STK-001-008 (consistent, predictable structure with audit
trail), NEED-STK-001-010 (temporal and device-level resolution for analysis), and/or
NEED-STK-001-011 (trustworthy data).

---

### FR-023 — Migration: Add `captured_at`

**Statement:** The migration script shall add a column `captured_at DATETIME NOT NULL` to the `sensorreadings` table and populate it for every existing row with `TIMESTAMP(currentdate, currenttime)` for that row, executed within a transaction before any `DROP COLUMN` statement.

**Source:** SCN-008 Step 4; NFR-INT-003; NFR-MAIN-002
**Traced Need:** NEED-STK-001-008, NEED-STK-001-010
**Priority:** Must Have
**Verification Method:** Inspection + Test — inspect migration script for correct SQL; post-migration: `DESCRIBE sensorreadings` confirms `captured_at DATETIME NOT NULL` present; `SELECT COUNT(*) FROM sensorreadings WHERE captured_at IS NULL` returns 0
**IEEE 29148 Quality:** PASS WITH WARNINGS — "add + populate" are inseparable for a NOT NULL column (acceptable per FR-011 precedent)
**Status:** Planned

---

### FR-024 — Migration: Add `location`

**Statement:** The migration script shall add a column `location TEXT NOT NULL` to the `sensorreadings` table and populate it for every existing row with `SUBSTRING_INDEX(SUBSTRING_INDEX(device, '/', 3), '/', -2)` — the second and third slash-delimited path segments of `device`, joined by a forward slash (e.g. `environment/indoor/attic/temperature` → `indoor/attic`).

**Source:** SCN-008 Step 4; NFR-INT-003; OPT-A convergence
**Traced Need:** NEED-STK-001-008, NEED-STK-001-010
**Priority:** Must Have
**Verification Method:** Inspection + Test — inspect migration script for correct SQL expression; post-migration: spot-check `SELECT device, location FROM sensorreadings LIMIT 20` and verify derivation is correct for all observed topics
**IEEE 29148 Quality:** PASS WITH WARNINGS — "add + populate" inseparable for NOT NULL (acceptable)
**Status:** Planned

---

### FR-025 — Migration: Add `measurement_type`

**Statement:** The migration script shall add a column `measurement_type TEXT NOT NULL` to the `sensorreadings` table and populate it for every existing row with `SUBSTRING_INDEX(device, '/', -1)` — the final slash-delimited path segment of `device` (e.g. `environment/indoor/attic/temperature` → `temperature`).

**Source:** SCN-008 Step 4; NFR-INT-003; OPT-A convergence
**Traced Need:** NEED-STK-001-008, NEED-STK-001-010
**Priority:** Must Have
**Verification Method:** Inspection + Test — inspect migration script for correct SQL expression; post-migration: spot-check `SELECT device, measurement_type FROM sensorreadings LIMIT 20` and verify correctness
**IEEE 29148 Quality:** PASS WITH WARNINGS — "add + populate" inseparable for NOT NULL (acceptable)
**Status:** Planned

---

### FR-026 — Migration: Composite Index

**Statement:** The migration script shall create a composite index named `idx_loc_mtype_time` on `sensorreadings(location, measurement_type, captured_at)` after the three new columns have been populated.

**Source:** NFR-PERF-003; SCN-008 Step 4
**Traced Need:** NEED-STK-001-010
**Priority:** Must Have
**Verification Method:** Inspection — post-migration: `SHOW INDEX FROM sensorreadings` confirms index `idx_loc_mtype_time` exists on columns `(location, measurement_type, captured_at)` in that order
**IEEE 29148 Quality:** PASS
**Status:** Planned

---

### FR-027 — Migration: Drop Legacy Timestamp Columns

**Statement:** The migration script shall drop the `currentdate` and `currenttime` columns from `sensorreadings` after all three new columns have been populated and verified.

**Source:** SCN-008 Step 4; NFR-INT-003
**Traced Need:** NEED-STK-001-008
**Priority:** Must Have
**Verification Method:** Inspection + Test — inspect migration script for DROP COLUMN statements positioned after backfill; post-migration: `DESCRIBE sensorreadings` confirms neither `currentdate` nor `currenttime` is present
**IEEE 29148 Quality:** PASS WITH WARNINGS — "drop currentdate and currenttime" is two columns, one logical action (acceptable)
**Status:** Planned

---

### FR-028 — Model: `captured_at` Column

**Statement:** The `SensorReading` SQLAlchemy model in `mqttlogger/data_model.py` shall declare `captured_at` as a `DateTime` column that does not permit null values, and shall not declare `currentdate` or `currenttime` columns.

**Source:** SCN-008 Step 6; NFR-INT-003
**Traced Need:** NEED-STK-001-008
**Priority:** Must Have
**Verification Method:** Inspection — `data_model.py` reviewed: `Column(DateTime, nullable=False)` present for `captured_at`; `Column(Date, ...)` and `Column(Time, ...)` absent
**IEEE 29148 Quality:** PASS WITH WARNINGS — positive + negative form of same class property (acceptable per FR-008 precedent)
**Status:** Planned

---

### FR-029 — Model: `location` Column

**Statement:** The `SensorReading` SQLAlchemy model shall declare `location` as a `Text` column that does not permit null values.

**Source:** SCN-008 Step 6; OPT-A convergence
**Traced Need:** NEED-STK-001-008
**Priority:** Must Have
**Verification Method:** Inspection — `data_model.py` reviewed: `Column(Text, nullable=False)` present for `location`
**IEEE 29148 Quality:** PASS
**Status:** Planned

---

### FR-030 — Model: `measurement_type` Column

**Statement:** The `SensorReading` SQLAlchemy model shall declare `measurement_type` as a `Text` column that does not permit null values.

**Source:** SCN-008 Step 6; OPT-A convergence
**Traced Need:** NEED-STK-001-008
**Priority:** Must Have
**Verification Method:** Inspection — `data_model.py` reviewed: `Column(Text, nullable=False)` present for `measurement_type`
**IEEE 29148 Quality:** PASS
**Status:** Planned

---

### FR-031 — `on_message`: Populate `captured_at`

**Statement:** The `on_message` handler in `mqttlogger/mqtt_client.py` shall set `captured_at` on each new `SensorReading` to `datetime.now()` at the time the MQTT message is received.

**Source:** SCN-008 Step 6; FR-002 (extends message parsing to new field)
**Traced Need:** NEED-STK-001-001, NEED-STK-001-010
**Priority:** Must Have
**Verification Method:** Test (IT) — publish a test message; query the database for the inserted row; verify `captured_at` is a `DATETIME` value within 5 seconds of the publish time
**IEEE 29148 Quality:** PASS
**Status:** Planned

---

### FR-032 — `on_message`: Populate `location`

**Statement:** The `on_message` handler shall set `location` on each new `SensorReading` to the second and third slash-delimited path segments of the MQTT message topic, joined by a forward slash (e.g. topic `environment/indoor/attic/temperature` → `location = 'indoor/attic'`).

**Source:** SCN-008 Step 6; OPT-A convergence
**Traced Need:** NEED-STK-001-010
**Priority:** Must Have
**Verification Method:** Test (IT) — publish a test message on a known topic; verify the `location` column in the inserted row matches the expected two-segment value
**IEEE 29148 Quality:** PASS
**Status:** Planned

---

### FR-033 — `on_message`: Populate `measurement_type`

**Statement:** The `on_message` handler shall set `measurement_type` on each new `SensorReading` to the final slash-delimited path segment of the MQTT message topic (e.g. topic `environment/indoor/attic/temperature` → `measurement_type = 'temperature'`).

**Source:** SCN-008 Step 6; OPT-A convergence
**Traced Need:** NEED-STK-001-010
**Priority:** Must Have
**Verification Method:** Test (IT) — publish a test message on a known topic; verify the `measurement_type` column in the inserted row matches the expected value
**IEEE 29148 Quality:** PASS
**Status:** Planned

---

### FR-034 — Companion Monitor: Use `captured_at` for Gap Detection

**Statement:** The `query_active_sensors()` function in `companion-monitor/monitor.py` shall filter rows using the expression `captured_at >= DATE_SUB(NOW(), INTERVAL %s MINUTE)` in place of `TIMESTAMP(currentdate, currenttime) >= DATE_SUB(NOW(), INTERVAL %s MINUTE)`.

**Source:** SCN-008 Step 9; NFR-INT-003; RISK-026
**Traced Need:** NEED-STK-001-002, NEED-STK-001-009
**Priority:** Must Have
**Verification Method:** Inspection — `companion-monitor/monitor.py` reviewed: no reference to `currentdate`, `currenttime`, or `TIMESTAMP()` in any SQL string; `captured_at` used as time filter
**IEEE 29148 Quality:** PASS
**Status:** Planned

---

### FR-035 — Companion Monitor: Use `captured_at` in Bootstrap Query

**Statement:** The `bootstrap_sensors.py` script shall filter rows using the expression `DATE(captured_at) >= %s` in place of `currentdate >= %s` when querying for sensors active within a lookback period.

**Source:** SCN-008 Step 9; NFR-INT-003; RISK-026
**Traced Need:** NEED-STK-001-009
**Priority:** Must Have
**Verification Method:** Inspection — `companion-monitor/bootstrap_sensors.py` reviewed: no reference to `currentdate` in any SQL string; `DATE(captured_at)` used as date filter
**IEEE 29148 Quality:** PASS
**Status:** Planned

---

### FR-036 — Companion Monitor: Read-Only Database Credentials

**Statement:** The `companion_monitor` service definition in `docker-compose.yml` shall supply database credentials for a MariaDB user that has `SELECT`-only privileges on `sensorreadings`, distinct from the write-capable credentials used by the `mqtt_logger` service.

**Source:** NFR-INT-002; RISK-028; Constitution Principle I (Single-Purpose Service)
**Traced Need:** NEED-STK-001-008, NEED-STK-001-011
**Priority:** Must Have
**Verification Method:** Inspection — `docker-compose.yml` reviewed: `companion_monitor` environment specifies a different `DB_USER` than `mqtt_logger`; `SHOW GRANTS FOR '<db_user>'@'%'` on `sietchtabr` confirms SELECT-only on `sensorreadings`
**IEEE 29148 Quality:** PASS
**Status:** Planned

---

## Open Items

| ID | Description | Target Phase |
|----|-------------|-------------|
| REQ-OI-001 | RISK-014 (historical completeness verification) is not addressed by any requirement in this register — deferred explicitly at IP-002 convergence | Phase 4+ |
| REQ-OI-002 | FR-MON-001 latency evidence (120 s max) was gathered under a 60 s heartbeat interval; if the interval changes, the bound must be re-validated | Ongoing |
| REQ-OI-003 | V&V plan entries for FR-001 through FR-012 (core logger) need to be populated in vv-plan.md | Phase 5 |
