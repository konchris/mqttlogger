# Requirements Register

**System:** mqttlogger
**Feature:** 002-mqttlogger-baseline
**Date:** 2026-05-10
**Status:** BASELINED
**Last Updated By:** speckit-plan (adapted for SE workflow)

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

**Statement:** The monitoring system shall notify the operator when a sensor publishes readings to the database that is not present in the known sensor configuration and is not on the excluded (event-driven) sensors list.

**Source:** OPT-B convergence decision, RISK-013 (silent topology change)
**Priority:** Must Have
**Verification Method:** Demonstration (ST) — allow a new sensor to publish; verify notification is received within one polling interval; verify excluded sensors do not trigger alerts
**Status:** Validated (IP-001 PASS — 3 new dining room sensors surfaced automatically during 24h baseline)

---

### FR-MON-005 — Alert State Transition Logic

**Statement:** The monitoring system shall track alert state in memory so that each alert fires exactly once on transition (normal → alert, alert → normal), not on every polling cycle.

**Source:** OPT-B design, prevents alert storm under prolonged fault
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

---

## Open Items

| ID | Description | Target Phase |
|----|-------------|-------------|
| REQ-OI-001 | RISK-014 (historical completeness verification) is not addressed by any requirement in this register — deferred explicitly at IP-002 convergence | Phase 4+ |
| REQ-OI-002 | FR-MON-001 latency evidence (120 s max) was gathered under a 60 s heartbeat interval; if the interval changes, the bound must be re-validated | Ongoing |
| REQ-OI-003 | V&V plan entries for FR-001 through FR-012 (core logger) need to be populated in vv-plan.md | Phase 5 |
