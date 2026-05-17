# Architecture Documentation

**System:** mqttlogger
**Feature:** 009-schema-evolution (updated; originally 002-mqttlogger-baseline, reviewed through 004)
**Date:** 2026-05-12 (original); 2026-05-17 (feature 009 update)
**Status:** DRAFT — updated for feature 009 schema evolution
**Last Updated By:** se-architecture skill (feature 009)
**Notation:** C4 Model + Views and Beyond + arc42

---

## 1. Introduction and Goals

### 1.1 Purpose of This Document

This document describes the architecture of the mqttlogger system as baselined at feature 002-mqttlogger-baseline. It covers the core MQTT capture service and the monitoring stack added by the IP-001/IP-002 exploration. It is produced as a Phase 3 SE artifact; the implementation it describes is already deployed and operational on `sietchtabr`.

Related artifacts:
- ConOps: `01-conops/conops.md`
- NFRs: `02-nfr/quality-attributes.md`
- Explore summary: `03-explore/explore-summary.md`
- Requirements: `04-requirements/requirements-register.md`
- Plan: `07-plan/plan.md`

### 1.2 Architectural Drivers

The following requirements had the most significant influence on the structural decisions. They appear repeatedly in the ADRs.

| Driver ID | Type | Description | Architectural Impact |
| --------- | ---- | ----------- | -------------------- |
| NFR-PERF-001 | NFR | No message drops due to processing backlog | Synchronous in-callback write (ADR-001); no async queue |
| NFR-REL-001 | NFR | Auto-recovery from all software faults | `restart: unless-stopped` (ADR-004); write-or-discard (ADR-003) |
| NFR-REL-002 | NFR | Recovery within 60 seconds after crash | MariaDB healthcheck gates logger startup |
| NFR-PORT-001 | NFR | Docker Compose on Linux, single orchestration mechanism | All containers in one Compose file (ADR-004) |
| NFR-SEC-001 | NFR | Credentials not in version control | Config loaded from gitignored file (FR-008) |
| No cloud dependency | Constraint | Push notifications must function on isolated LAN | Self-hosted ntfy instead of Telegram/Slack (ADR-005) |
| Solo operation | Constraint | System must operate unattended for months | Monitoring stack added (ADR-002) to make faults visible |
| No CCU3 changes | Constraint | Upstream sensor/broker layer is fixed | Architecture works with whatever MQTT topics CCU3 publishes |
| NFR-INT-003 | NFR | `captured_at` must be native DATETIME NOT NULL on base table, not computed expression | OPT-A direct column migration (ADR-008); view-based approach eliminated |
| NFR-PERF-003 | NFR | Composite index `(location, measurement_type, captured_at)` for filtered time-range queries | Index on base table via migration; cannot index view columns in MariaDB |
| NFR-INT-002 | NFR | Non-logger consumers connect read-only; no write privileges | Dedicated `monitor_ro` MariaDB user (ADR-009); companion_monitor env updated |
| NFR-MAIN-002 | NFR | Migration atomicity — no partial state on failure | UPDATE backfill in START TRANSACTION/COMMIT; null-check gate before irreversible DDL |

### 1.3 Quality Attribute Scenarios

Each Must Have NFR expressed as a stimulus-response scenario:

| NFR | Stimulus | Source | Environment | Artefact | Response | Measure |
| --- | -------- | ------ | ----------- | -------- | -------- | ------- |
| NFR-PERF-001 | Burst of N MQTT messages | HomeMatic CCU3 | Normal operation | mqtt_logger | All N messages committed to MariaDB | N in = N in DB; zero discards |
| NFR-REL-001 | Container OOM kill | Docker runtime | Any time | mqtt_logger | Container restarts; capture resumes | No operator action required |
| NFR-REL-002 | Container kill signal | Test operator | Test environment | mqtt_logger | First DB write after restart | ≤ 60 seconds from kill to write |
| NFR-SEC-001 | Credential inspection | Security audit | Repository state | git history | No credential values in any commit | Zero credential findings in git log |
| NFR-PORT-001 | Fresh Linux amd64 host | New deployment | docker compose up -d | Full stack | All 6 containers healthy; logger captures | Single command deploys, no manual steps |

---

## 2. Constraints

### 2.1 Technical Constraints

| ID | Constraint | Source |
| -- | ---------- | ------ |
| TC-001 | No changes to CCU3/RedMatic/sensor layer — upstream MQTT topology is fixed | Hard constraint from explore-summary |
| TC-002 | Single-host deployment (sietchtabr, consumer mini PC) — no multi-host redundancy | NFR-PORT-001, ConOps |
| TC-003 | Docker Compose is the only supported orchestration mechanism | NFR-PORT-001, Constitution Principle III |
| TC-004 | No cloud-dependent services — all components must function on an isolated home network | Explore summary, IP-001 hard constraint |
| TC-005 | Python 3.12 runtime (upgraded from 3.10 by feature 007-python312-upgrade) | Feature 007 |
| TC-006 | MariaDB for persistence — schema owned by mqttlogger (NFR-INT-001) | Existing implementation |

### 2.2 Organisational Constraints

| ID | Constraint | Source |
| -- | ---------- | ------ |
| OC-001 | Solo developer/operator — bus factor = 1 (RISK-004) | STK-001 / STK-002 |
| OC-002 | CI/CD pipeline established (GitHub Actions: lint + test + 80% coverage gate) — RISK-001 closed by feature 003-cicd-pipeline | Constitution Section VI; TBD-003 closed |
| OC-003 | Automated test coverage enforced at 80% gate in CI — 86.36% at feature 003 baseline; ~93% projected after feature 004 removes dead code from `__init__.py` | NFR-MAIN-001 satisfied |

### 2.3 Regulatory Constraints

None applicable. System is classified non-safety. No regulatory obligations identified in the ConOps or NFRs.

---

## 3. System Scope and Context

*See: `views/context.md`*

The mqttlogger system sits between the HomeMatic home automation sensor network and the operator's data analysis tools. It does not interact with the sensor layer (CCU3/RedMatic is out of scope); it receives only what the MQTT broker delivers. The operator interacts with the system through three channels: log inspection for diagnostics, push notifications via ntfy for alerts, and Jupyter Notebooks for trend analysis against the MariaDB database.

The system boundary includes: mqtt broker (Mosquitto), mqtt_logger, MariaDB, Uptime Kuma, ntfy, and companion_monitor. The CCU3, the operator's analysis tooling, and the operator's iPhone are all external.

The iPhone occupies a special position: it is the terminal delivery point for all monitoring notifications, but it is not within the system boundary. Its availability depends on the operator being on the home Wi-Fi (RISK-023). This constraint is documented in FR-MON-006 and in the ConOps as an operational constraint.

---

## 4. Solution Strategy

The architecture applies two complementary monitoring strategies above a minimal capture core, justified by the IP-002 convergence decision that OPT-A and OPT-B address distinct failure modes.

**Capture core (existing):** The `mqtt_logger` service implements a single-concern synchronous pipeline — receive MQTT message, parse payload, write to MariaDB. The pipeline is intentionally thin: no transformation, no buffering, no secondary logic. Faults at the DB layer cause the message to be discarded and logged; the broker connection is never interrupted by a DB fault (ADR-003). Liveness is proven by the heartbeat thread running inside the same Python process (ADR-006).

**Process monitoring — OPT-A:** A daemon thread inside `mqtt_logger` pushes an HTTP liveness signal to Uptime Kuma every 60 seconds. Uptime Kuma evaluates silence as a fault and routes an alert to the self-hosted ntfy server. This path detects container-level crashes within 120 seconds maximum (FR-MON-001 Validated, IP-001).

**Sensor monitoring — OPT-B:** A second Python service (`companion_monitor`) runs in a separate container and polls the MariaDB database every 5 minutes. It checks two directions: (1) periodic sensors that have gone silent for longer than the gap window (600 minutes), and (2) sensors publishing to the database that are not listed in `sensors.yml`. Both directions push alerts via the same ntfy server. This path detects sensor silence and topology change, which OPT-A cannot observe. The gap window is the latency trade-off: up to 10 hours for silence detection vs. OPT-A's 120-second crash detection.

**Notification delivery:** Both monitoring paths converge on a single self-hosted ntfy server. This is the only notification delivery mechanism; it requires the operator's iPhone to be on the home Wi-Fi (RISK-023). No internet path is configured or planned in the current phase.

The approach satisfies the "no cloud dependency" constraint (TC-004) and the "no changes to the upstream sensor layer" constraint (TC-001). Both OPT-A and OPT-B have passed 24-hour false-positive baselines.

---

## 5. Building Block View

### 5.1 Container Level

*See: `views/container.md`*

Six containers form the deployed stack:

**mqtt (Mosquitto broker):** MQTT message bus. Receives all sensor publishes from CCU3/RedMatic over the home LAN. Forwards messages to mqtt_logger via the MQTT protocol. The broker is the only component that touches the external sensor network. It has no connection to MariaDB.

**mqtt_logger (Python service):** The capture core. Subscribes to all MQTT topics on the broker, parses each message into a `SensorReading` record, and writes it to MariaDB via SQLAlchemy. Also runs the OPT-A heartbeat daemon thread. All message processing is synchronous and in-callback (ADR-001). Writes to MariaDB on `mqtt_db`; connects to broker on `mqtt_net`.

**mariadb (MariaDB database):** Persistent store for all sensor readings. The `sensorreadings` table is owned by mqtt_logger; schema is defined by `data_model.py`. Data is retained indefinitely (no TTL, no archival — RISK-007). Accessible by companion_monitor on `mqtt_db` for read queries.

**uptime_kuma (Uptime Kuma monitoring server):** Receives liveness heartbeat pushes from mqtt_logger. Evaluates silence after 2× the heartbeat interval and routes alerts to ntfy. Exposed on port 3001 for operator UI access. Part of OPT-A.

**ntfy (self-hosted push notification server):** Terminal delivery point for all monitoring alerts. Receives HTTP POST messages from both Uptime Kuma (OPT-A) and companion_monitor (OPT-B) on the topic `mqttlogger-alerts`. The operator's iPhone ntfy app subscribes to this topic via LAN IP. Log level set to `warn` (configured via Docker Compose command) to suppress per-minute INFO statistics. Exposed on port 8080.

**companion_monitor (Python service):** Implements OPT-B gap and topology detection. Polls MariaDB every 5 minutes. Reads `sensors.yml` for expected periodic sensors and excluded event-driven sensors. Pushes alerts to ntfy directly via HTTP POST. Maintains in-memory state sets (`alerted_missing`, `alerted_unknown`) to enforce state-transition alerting (FR-MON-005).

### 5.2 Component Level

*See: `views/component.md`*

**mqtt_logger components:**

`app.py` is the entry point. It loads configuration via `db_connection.py`, establishes the SQLAlchemy connection, creates the paho-mqtt client with LWT, starts the heartbeat daemon thread (if `heartbeat_url` is configured), and enters the paho-mqtt network loop. All component wiring is done here.

`mqtt_client.py` implements the paho-mqtt callbacks: `on_connect` (subscribe to configured topic filter, log connection), `on_message` (parse payload, build `SensorReading`, call `insert()`), and `insert()` (commit to MariaDB within a session). The `insert()` call is made directly inside `on_message` — synchronous, no queue (ADR-001).

`heartbeat.py` implements `HeartbeatThread(threading.Thread, daemon=True)`. The thread sleeps for `heartbeat_interval_seconds`, wakes, issues `HTTP POST heartbeat_url`, and repeats. Activated only when `heartbeat_url` is present in config; otherwise the thread is not started. Daemon mode ensures it exits automatically with the process (ADR-006).

`data_model.py` defines the `SensorReading` SQLAlchemy model: `id` (PK), `captured_at` (DateTime NOT NULL — UTC capture time), `location` (Text NOT NULL — MQTT topic segments 2+3, e.g. `indoor/attic`), `measurement_type` (Text NOT NULL — final topic segment, e.g. `temperature`), `device` (Text — full MQTT topic, canonical source retained for re-derivation), `reading` (Float). The `currentdate` and `currenttime` columns were removed by the feature 009 migration (ADR-008). This is the only schema definition for the `sensorreadings` table.

`db_connection.py` provides `load_config_file()` (reads and validates `config.json`) and `create_connection_string()` (builds a SQLAlchemy MariaDB+pymysql connection string). Raises actionable errors on missing or invalid fields (NFR-USE-001).

**companion_monitor components:**

`main()` reads all parameters from environment variables, calls `load_sensor_config()`, and runs the poll loop: sleep `POLL_INTERVAL_SECONDS`, call `run_check()`, repeat.

`load_sensor_config()` reads `sensors.yml` and returns two Python sets: `monitored_sensors` (periodic, subject to gap alerts) and `excluded_sensors` (event-driven, suppressed from both gap and unknown alerts).

`run_check()` is the detection heart. It calls `query_active_sensors()` to get the set of sensors that published within the gap window. It then computes: (a) `missing = monitored_sensors - active_sensors` → fire alert for each newly missing sensor; (b) `unknown = active_sensors - monitored_sensors - excluded_sensors` → fire alert for each newly unknown sensor. Alerts fire only on state transition (state sets updated after push).

`query_active_sensors()` issues a MariaDB SELECT to retrieve all distinct `device` values that have a `captured_at` timestamp within the last `GAP_WINDOW_MINUTES`.

`push_notification()` issues an HTTP POST to the ntfy URL with the alert message as the request body. Failures are logged but do not stop the monitor.

`get_db_connection()` builds a pymysql connection from environment variables. Errors are logged; the poll loop continues on connection failure.

---

## 6. Runtime View

*See: `views/functional-flow.md`*

**Normal message capture (MODE-001):** A CCU3 sensor publishes an MQTT message to the broker. The broker delivers it to mqtt_logger via the paho-mqtt network loop. `on_message` is called synchronously. The payload is parsed; a `SensorReading` is constructed and committed to MariaDB within the same callback. The callback returns; paho resumes listening. No queuing, no buffering, no background threads involved in this path.

**Crash detection (OPT-A):** The heartbeat daemon thread inside mqtt_logger wakes every 60 seconds and issues an HTTP POST to Uptime Kuma's push endpoint. As long as pushes arrive, Uptime Kuma resets its timer. If the logger crashes (container OOM, Python exception, host kill), the thread stops. Uptime Kuma times out after 120 seconds (2× interval) and routes an alert to ntfy. The ntfy iOS app delivers the push notification to the operator's iPhone (if on home Wi-Fi). Uptime Kuma detects recovery when the next heartbeat arrives after the logger restarts. The maximum detection latency is 120 seconds (IP-001 fault injection evidence: mean 93 s, max 120 s, 3/3 runs pass).

**Sensor gap detection (OPT-B):** companion_monitor wakes every 5 minutes. `query_active_sensors()` returns the set of sensors that have published within the last 600 minutes. `run_check()` computes the difference against `monitored_sensors` (from `sensors.yml`). If a previously-active sensor is absent, and its ID is not already in `alerted_missing`, a silence alert is pushed to ntfy and the ID is added to `alerted_missing`. When the sensor resumes publishing (appears in the active set again), a recovery notification is pushed and the ID is removed from `alerted_missing`. This state-transition logic ensures exactly one alert per fault event regardless of how many poll cycles the fault spans (FR-MON-005). The maximum detection latency is 600 minutes (gap window) + up to 5 minutes (poll interval) = approximately 10 hours.

**Startup (MODE-002):** Docker Compose brings up services in dependency order. MariaDB starts and passes its healthcheck (30 s timeout, 10 s interval). Only then do mqtt_logger and companion_monitor containers start. mqtt_logger loads config, creates the SQLAlchemy engine, registers the LWT, connects to the broker, subscribes, starts the heartbeat thread, and enters the paho loop. companion_monitor loads env vars, reads `sensors.yml`, and enters the poll loop.

**Live schema migration (SCN-008, feature 009):** The operator brings the stack down, runs the migration SQL against the live MariaDB instance, then brings the stack up with the new image. The migration adds `captured_at`, `location`, and `measurement_type` columns, backfills all existing rows within a transaction, verifies via null-check SELECT, then enforces NOT NULL and creates the composite index before dropping the legacy `currentdate` and `currenttime` columns. The code changes (data_model.py, mqtt_client.py, monitor.py, bootstrap_sensors.py, docker-compose.yml) are deployed atomically with the schema — no intermediate state where old code runs against the new schema is possible. See ADR-008 and Flow 5 in functional-flow.md.

**Graceful shutdown (MODE-003):** SIGTERM is received by the mqtt_logger container (from `docker compose down`). app.py signal handler calls `loop.stop()`. paho-mqtt publishes the LWT `"online"` message (configured will only fires on unexpected disconnect; on clean disconnect, the MQTT spec does not send the LWT — the status topic retains the last published value). The container exits with status 0. The heartbeat daemon thread exits automatically because it is a daemon thread. companion_monitor receives SIGTERM; Python exits the poll loop at the next sleep boundary.

---

## 7. Deployment View

*See: `views/deployment.md`*

All six containers run on a single physical host: `sietchtabr`, a consumer-grade mini PC on the home LAN. The host runs Linux (amd64). Docker Compose is the sole orchestration mechanism (ADR-004).

**Docker networks:**
- `mqtt_net`: connects `mqtt` (Mosquitto broker) and `mqtt_logger`. MQTT protocol (TCP 1883, internal only — not exposed to host).
- `mqtt_db`: connects `mqtt_logger`, `companion_monitor`, and `mariadb`. MariaDB protocol (TCP 3306, internal only).
- `monitoring_net`: connects `uptime_kuma`, `ntfy`, and `companion_monitor`. HTTP (TCP 80/ntfy, TCP 3001/uptime_kuma; ntfy exposed to host on 8080, uptime_kuma on 3001).

**External exposure:** Only ports 3001 (Uptime Kuma UI) and 8080 (ntfy) are exposed to the host and accessible on the home LAN. The broker (1883) and MariaDB (3306) are not exposed outside Docker networks.

**Restart topology:** All six containers carry `restart: unless-stopped`. mqtt_logger and companion_monitor have `depends_on: mariadb: condition: service_healthy`, ensuring they do not start until MariaDB passes its healthcheck. This bounds the startup race condition that would otherwise cause connection errors on fresh deployment.

**Log management:** All containers use the json-file driver with `max-size: 10m, max-file: 3` via a YAML anchor in docker-compose.yml. mqtt_logger additionally writes application logs to `/code/logs/mqttlogger.log` via a Python `RotatingFileHandler` (application-level rotation). ntfy is configured with `--log-level warn` to suppress per-minute INFO statistics.

---

## 9. Architecture Decisions

*See: `decisions/` folder*

### Decision Index

| ADR | Title | Status | Key Drivers |
| --- | ----- | ------ | ----------- |
| ADR-001 | Synchronous In-Callback Message Processing | Accepted | NFR-PERF-001, Constitution Principle I |
| ADR-002 | Two-Layer Out-of-Process Monitoring (OPT-A + OPT-B) | Accepted | RISK-013, RISK-016, FR-MON-001..004 |
| ADR-003 | Write-or-Discard Persistence — No Message Buffer | Accepted | MODE-005, NFR-REL-001, Constitution Principle VII |
| ADR-004 | Docker Compose as Sole Orchestration Mechanism | Accepted | NFR-PORT-001, NFR-REL-001, Constitution Principle III |
| ADR-005 | ntfy as the Self-Hosted Push Notification Server | Accepted | FR-MON-006, No-cloud constraint |
| ADR-006 | Heartbeat Implemented as Daemon Thread Inside mqtt_logger | Accepted | FR-013, FR-014, NFR-REL-001, RISK-016 |
| ADR-007 | Static Sensor Classification via sensors.yml Exclusion List | Accepted | FR-MON-002, FR-MON-004, FR-MON-005, FR-MON-007 |
| ADR-008 | Direct Column Migration for Schema Evolution | Accepted | NFR-INT-003, NFR-PERF-003, NFR-MAIN-002, FR-023..FR-027 |
| ADR-009 | Read-Only Database Access for Companion Monitor | Accepted | NFR-INT-002, FR-036 |

---

## 10. Quality Scenarios

How the architecture satisfies each Must Have NFR:

| NFR | Architectural Mechanism | Evidence |
| --- | ----------------------- | -------- |
| NFR-PERF-001 — Message completeness | Synchronous in-callback write (ADR-001): each message is committed before the callback returns; paho cannot deliver the next message until the callback returns; no queue means no queue overflow | Architecture analysis; no drops observed at current HomeMatic message rates |
| NFR-REL-001 — Auto-recovery | `restart: unless-stopped` (ADR-004) restarts crashed containers; paho-mqtt reconnect loop handles broker loss (FR-004); discard-on-fail (ADR-003) keeps the service alive during DB fault | IP-001 fault injection: 3/3 restarts detected by OPT-A; companion_monitor 24h baseline: zero false positives |
| NFR-REL-002 — Recovery ≤ 60 s | MariaDB healthcheck ensures DB is ready before logger starts; `restart: unless-stopped` triggers immediately after crash; paho reconnect is fast on same-host broker | IP-001 evidence: mean 93 s for notification; actual restart/reconnect time is seconds — notification latency is OPT-A monitor window (120 s), not restart time |
| NFR-SEC-001 — No credentials in VCS | `config.json` is gitignored; `sensors.yml` is gitignored; credentials loaded exclusively from config file at runtime (FR-008); `.gitignore` verified | `.gitignore` inspected; RISK-002 tracks historical credential exposure pre-migration |
| NFR-USE-002 — Complete log entries | Python `logging.Formatter` configured with `%(asctime)s %(levelname)s %(module)s %(funcName)s:%(lineno)d %(message)s`; applied to all handlers in app.py | Visual inspection of log output during IP-001 baseline |
| NFR-PORT-001 — Docker Compose deployment | All 6 services defined in `docker-compose.yml`; single `docker compose up -d` starts the full stack; Linux amd64 verified on sietchtabr | IP-001 deployment successful; stack deployed and running |
| NFR-INT-003 — `captured_at` as native DATETIME | OPT-A direct column migration (ADR-008) adds `captured_at DATETIME NOT NULL` directly to `sensorreadings`; `TIMESTAMP()` computation eliminated from all downstream queries | Post-migration: DESCRIBE sensorreadings; no TIMESTAMP() in monitor.py or bootstrap_sensors.py |
| NFR-PERF-003 — Composite index | Migration creates `idx_loc_mtype_time ON sensorreadings(location, measurement_type, captured_at)` after backfill completes | Post-migration: SHOW INDEX FROM sensorreadings; EXPLAIN on filtered time-range query |
| NFR-INT-002 — Read-only companion monitor access | Dedicated `monitor_ro` MariaDB user with GRANT SELECT only; companion_monitor docker-compose.yml uses MONITOR_DB_USER (ADR-009) | SHOW GRANTS FOR 'monitor_ro'@'%' confirms SELECT-only |
| NFR-MAIN-002 — Migration atomicity | UPDATE backfill in START TRANSACTION/COMMIT; null-check SELECT acts as gate before MODIFY COLUMN and DROP COLUMN (which are non-transactional DDL) | Script reviewed; null-check result 0 confirmed before DDL proceeds |

---

## 11. Risks and Technical Debt

Risks with architectural relevance (full register in `10-risk/risk-register.md`):

| Risk ID | Description | Architectural Relevance | Handling |
| ------- | ----------- | ----------------------- | -------- |
| RISK-020 | Heartbeat proves process liveness, not capture activity (ADR-006 consequence) | OPT-A monitoring has a blind spot for stuck-thread scenarios | Monitor; future: write-confirming heartbeat |
| RISK-023 | LAN-only ntfy — notifications not delivered when operator is off home network | ADR-005 consequence; accepted at IP-002 | Accept; future: ntfy cloud relay or Tailscale |
| RISK-024 | companion_monitor has no automated tests — Constitution Principle VI gap | New codebase added at IP-001; not covered by any test runner | Plan; addressed when CI/CD established (TBD-003) |
| RISK-001 | No CI/CD pipeline | No automated verification of any architectural quality claim | Plan; TBD-003 |
| RISK-013 | Silent sensor topology change (resolved by OPT-B, but gap window is up to 10 hours) | ADR-007 consequence; accepted at IP-002 | Monitor; gap window tuning if needed |
| RISK-019 | DB schema may not be fully version-controlled | NFR-INT-001 not yet fully verifiable | Plan; schema audit needed |
| RISK-026 | Schema migration and companion monitor code must be deployed atomically | Non-atomic deployment causes immediate crash | Plan; SCN-008 procedure enforces atomic stack-down/migrate/up sequence |
| RISK-027 | No database backup before migration | Data loss if migration SQL contains a bug | Accept; IP-001 dry-run validates derivation before migration runs; data volume is low |
| RISK-028 | Companion monitor used write-capable credentials | Closed by ADR-009 (feature 009) | Closed — read-only user created; docker-compose.yml updated |
| RISK-029 | ASM-A-001: topic pattern assumption unvalidated | Incorrect backfill for non-4-level topics | Plan; TASK-A-001 dry-run must pass before migration runs |

**Known technical debt:**

- `mqttlogger/` test suite established by feature 003; CI enforces 80% gate. `companion-monitor/` still has no automated tests (RISK-024).
- Python 3.12 runtime (upgraded from 3.10 by feature 007). RISK-003 closed.
- Historical credential exposure in Bitbucket/git history (RISK-002). Scrubbed with git filter-repo on 2026-05-11; both secrets replaced.
- `sensors.yml` is not version-controlled (by design — deployment-specific data). No automated check that it is current with the deployed sensor topology.
- companion_monitor has no health endpoint and no liveness signal of its own. A crashed companion_monitor is invisible to OPT-A (which monitors only mqtt_logger). This is a known gap: monitoring the monitor requires a separate mechanism not implemented in this phase.

---

## 12. Glossary

| Term | Definition |
| ---- | ---------- |
| CCU3 | HomeMatic Central Control Unit 3 — the home automation controller that aggregates sensor readings |
| RedMatic | HomeMatic extension that runs an MQTT broker on the CCU3 and publishes sensor values as MQTT messages |
| Gap window | The time period over which companion_monitor checks for sensor activity. A sensor absent for the full window triggers a silence alert. Calibrated to 600 minutes to avoid false positives from the slowest periodic sensor (thermostat set point, ~288 min interval). |
| Periodic sensor | A sensor that publishes readings on a schedule (e.g. temperature/humidity). Subject to gap monitoring. Silence is a fault indicator. |
| Event-driven sensor | A sensor that publishes only on state change (e.g. door/window contact, motion). May legitimately be silent for hours or days. Excluded from gap monitoring via `sensors.yml`. |
| LWT | Last Will and Testament — an MQTT feature where the broker publishes a designated message if the client disconnects unexpectedly. Used by mqtt_logger to publish `"offline"` to a status topic. |
| ntfy | Self-hosted push notification server (`binwiederhier/ntfy`). Accepts HTTP POST messages; delivers push notifications to iOS/Android apps via LAN or internet relay. |
| Uptime Kuma | Self-hosted monitoring service. Monitors the heartbeat push from mqtt_logger; routes alerts to ntfy on heartbeat silence. |
| sietchtabr | The physical host machine — a consumer-grade mini PC on the home LAN running Docker Compose and all six system containers. |
| OPT-A | Exploration option A: process-layer monitoring via heartbeat + Uptime Kuma. Selected at IP-002. |
| OPT-B | Exploration option B: sensor-layer monitoring via companion_monitor gap detection. Selected at IP-002. |
| mqtt_net | Docker internal network connecting the Mosquitto broker and mqtt_logger. |
| mqtt_db | Docker internal network connecting mqtt_logger, companion_monitor, and MariaDB. |
| monitoring_net | Docker internal network connecting Uptime Kuma, ntfy, and companion_monitor. |
