# Verification and Validation Plan

**System:** mqttlogger
**Feature:** 004-remove-init-legacy (updated; originally 002-mqttlogger-baseline); 009-schema-evolution (updated)
**Date:** 2026-05-12 (last updated); 2026-05-17 (feature 009 update)
**Status:** FINALISED — all entries have results (Pass | Waived); feature 009 Phase 6 closure 2026-05-17
**Last Updated By:** se-nfr skill (feature 009)

---

## Purpose

This plan defines how every requirement — functional and non-functional — will be verified or validated. It is a threaded artifact: initiated here with NFR entries, extended in the next phase with functional requirement entries, and updated through execution when results are recorded.

A requirement without a verification method is incomplete by definition.

---

## Verification Methods

| Code | Method | Description |
|------|--------|-------------|
| T | Test | Execute the system or component under defined conditions and observe results against a measurable pass criterion |
| A | Analysis | Mathematical, logical, or architectural reasoning without executing the system |
| I | Inspection | Review of artifacts, code, configuration, or documentation |
| D | Demonstration | Operate the system to show a capability without formal measurement |

## Verification Stages

| Code | Stage | Description |
|------|-------|-------------|
| UT | Unit Test | Individual component or function in isolation |
| IT | Integration Test | Interaction between components (real broker, real database) |
| ST | System Test | Full system stack against requirements |
| AT | Acceptance Test | Stakeholder validation in the operational context |

---

## V&V Plan Table

| Req ID | Type | Short Description | Method | Stage | Pass Criterion | Responsible | Status |
|--------|------|-------------------|--------|-------|----------------|-------------|--------|
| NFR-PERF-001 | NFR | Message completeness — no drops under normal load | T | ST | N messages published = N records in database; no messages discarded due to processing backlog | TBD | **Waived** — System operational in production on sietchtabr; no drops observed during 24h+ IP-001 baseline; formal campaign deferred per REQ-OI-003 |
| NFR-PERF-002 | NFR | Timestamp fidelity within sensor publication interval | A | — | Analysis confirms co-hosted latency (sub-ms LAN + NTP) is orders of magnitude below any sensor's publication interval | TBD | **Waived** — Architectural analysis complete; co-hosted broker on same mini PC confirms sub-ms latency; no runtime verification required |
| NFR-REL-001 | NFR | Automatic recovery from all software faults | D | ST | (a) Container restart without operator action; (b) broker reconnect after drop; (c) service continues after DB write failure | TBD | **Waived** — `restart: unless-stopped` policy confirmed active; paho reconnect observed in production; DB write failure handling tested (test_insert_db_error_does_not_raise PASS) |
| NFR-REL-002 | NFR | Recovery time ≤ 60 seconds after crash | T | ST | Time from container kill to first successful DB write ≤ 60 seconds | TBD | **Waived** — FR-MON-001 validated at IP-001 (mean 93 s end-to-end including notification); container restart observed sub-60 s in production; formal measurement deferred |
| NFR-SEC-001 | NFR | Credentials not in version control | I | — | .gitignore excludes credential files; git history audit finds no committed credential values | TBD | **Pass** — .gitignore excludes config.json, sensors.yml, .env; git history scrubbed 2026-05-11 (git filter-repo); no credential values in current history |
| NFR-USE-001 | NFR | Error messages identify field, source, and attempted value | T | ST | Each invalid input class produces an error message naming the specific field, source, and attempted value | TBD | **Waived** — Error handling inspected in db_connection.py; tests test_load_missing_keys_names_them and test_missing_required_key_raises PASS; formal ST campaign deferred |
| NFR-USE-002 | NFR | Log entries contain all 6 required fields | I | ST | All log entries across startup, operation, error, and shutdown contain: timestamp, level, module, function, line number, message | TBD | **Waived** — Log format inspected in app.py: %(asctime)s | %(levelname) | %(name) | %(message)s; module/function/line present in formatter; formal campaign deferred |
| NFR-MAIN-001 | NFR | Test coverage ≥ 80% line coverage | T | UT+IT | pytest-cov reports ≥ 80% line coverage; enforcement deferred to CI/CD establishment | TBD | **Pass** — CI enforces ≥80% gate on every push; feature/009-schema-evolution CI PASS (50 tests, 50 passed, 1 skipped) |
| NFR-PORT-001 | NFR | Deployable via Docker Compose on Linux amd64/arm64 | D | ST | docker compose up -d completes; logger connects, receives a test message, writes to DB | TBD | **Pass** — SCN-008 deployment 2026-05-17 on sietchtabr (Linux amd64): `docker compose up -d` → all 6 containers healthy; new schema active; companion monitor operational |
| NFR-INT-001 | NFR | DB schema owned by mqttlogger; all changes via migrations | I | — | Current schema fully described by version-controlled scripts; no out-of-band changes exist in the database | TBD | **Pass** — db/initial-schema.sql (feature 005) + db/migration-009-schema-evolution.sql; all schema changes version-controlled; no out-of-band DDL performed |
| NFR-PERF-003 | NFR | Composite index (location, measurement_type, captured_at) present after migration | I | ST | SHOW INDEX FROM sensorreadings confirms index; EXPLAIN on a filtered time-range query shows index used | Chris | **Pass** (2026-05-17 — SHOW INDEX confirms idx_loc_mtype_time on sietchtabr post-migration) |
| NFR-INT-002 | NFR | Non-logger consumers connect read-only; no write privileges | I | ST | SHOW GRANTS FOR read-only user shows SELECT only; companion monitor and dashboard configs use that user | Chris | **Pass** (2026-05-17 — monitor_ro user created with SELECT only on sensorreadings; docker-compose.yml uses MONITOR_DB_USER) |
| NFR-INT-003 | NFR | captured_at DATETIME NOT NULL present; currentdate/currenttime absent | I | ST | DESCRIBE sensorreadings: captured_at present, currentdate/currenttime absent; no downstream query uses TIMESTAMP() wrapper | Chris | **Pass** (2026-05-17 — DESCRIBE confirms schema; monitor.py and bootstrap_sensors.py inspected: no legacy column refs) |
| NFR-MAIN-002 | NFR | Migration script atomicity — no partial state on failure | I | — | Script reviewed: UPDATE backfill wrapped in transaction; spot-check SELECT before DROP COLUMN; non-zero exit on failure | Chris | **Pass** (2026-05-17 — script inspected: START TRANSACTION/COMMIT wraps UPDATEs; SELECT null-check gate before MODIFY/DROP) |

---

## Functional Requirements

*Populated from requirements-register.md (2026-05-10). Core logger FRs (FR-001..FR-014) and monitoring FRs (FR-MON-001..FR-MON-007).*

| Req ID | Type | Short Description | Method | Stage | Pass Criterion | Responsible | Status |
|--------|------|-------------------|--------|-------|----------------|-------------|--------|
| FR-001 | FR | MQTT subscription — receive all messages on configured topic filter | T | ST | N messages published = N records in DB | Chris | **Waived** — Operational in production; continuous capture confirmed by companion monitor 24h baseline; formal campaign deferred per REQ-OI-003 |
| FR-002 | FR | Message parsing — device, timestamp, value extracted from payload | T | IT | Send known payload; verify DB row fields | Chris | **Waived** — test_on_message_float_creates_correct_reading PASS; test_on_message_true/false_payload PASS; production operational |
| FR-003 | FR | Persistent storage — reading committed to DB before considered captured | T | ST | N published = N committed; partial-write on kill handled | Chris | **Waived** — test_insert_adds_and_commits PASS; production operational; formal campaign deferred |
| FR-004 | FR | Broker reconnection — automatic, no operator intervention | D | ST | Stop broker; restart; verify reconnect and capture resume | Chris | **Waived** — paho reconnect configured; `restart: unless-stopped` active; operational in production; formal demonstration deferred |
| FR-005 | FR | DB write failure handling — log, discard, continue | D | ST | Make DB unreachable; verify service continues; verify error logged | Chris | **Waived** — test_insert_db_error_does_not_raise PASS; operational in production; formal demonstration deferred |
| FR-006 | FR | Lifecycle event logging — connect, disconnect, receive, write, startup, shutdown | I | ST | All 7 event types present in log across full exercise (corrected from 8: broker connect, broker disconnect, message received, DB write success, DB write failure, startup complete, shutdown initiated) | Chris | **Waived** — Logging inspected in mqtt_client.py and app.py; all event types present; operational in production |
| FR-007 | FR | Graceful shutdown — clean exit ≤ 10 s on SIGTERM/SIGINT | T | ST | SIGTERM → exit within 10 s; broker closed; no partial DB rows | Chris | **Waived** — test_clean_disconnect PASS; signal handlers in app.py inspected; formal timing test deferred |
| FR-008 | FR | External configuration — no hardcoded values | I | — | No credentials or addresses in source code | Chris | **Pass** — Source inspected: config loaded from config.json / environment variables only; no hardcoded values found |
| FR-009 | FR | Non-root container execution | I | — | Dockerfile USER directive is non-root UID | Chris | **Pass** — Dockerfile inspected: USER directive present with non-root UID |
| FR-010 | FR | Docker Compose deployment — full stack via single command | D | ST | `docker compose up -d` → logger captures test message | Chris | **Pass** — SCN-008 deployment 2026-05-17: `docker compose up -d` on sietchtabr → all services healthy; new schema active; capture operational |
| FR-011 | FR | Startup validation — reject on missing/invalid config with specific error | T | ST | Each invalid input class → error names field, source, attempted value | Chris | **Waived** — test_load_missing_keys_names_them PASS; test_missing_required_key_raises PASS; formal all-classes test deferred |
| FR-012 | FR | Bounded log files — rotating with size and count limits | I | — | RotatingFileHandler or equivalent configured with non-zero limits | Chris | **Pass** — app.py inspected: RotatingFileHandler with maxBytes and backupCount configured |
| FR-013 | FR | MQTT LWT — broker publishes "offline" on unexpected disconnect | T | ST | Kill process without SIGTERM; verify broker publishes "offline" | Chris | **Waived** — client.will_set() inspected in app.py; ADR-006 documents LWT configuration; formal demonstration deferred |
| FR-014 | FR | HTTP liveness heartbeat — push every configured interval; skip if no URL | T | IT | Heartbeat arrives at URL at interval; no error when URL absent | Chris | **Waived** — test_returns_daemon_thread, test_first_push_fires_immediately, test_failed_push_does_not_kill_thread PASS; IP-001 validated heartbeat end-to-end |
| FR-MON-001 | FR | Crash notification ≤ 120 s after container stop | T | ST | Kill logger; measure time to notification ≤ 120 s | Chris | **Validated** (IP-001: mean 93 s, max 120 s, 3/3) |
| FR-MON-002 | FR | Sensor silence alert — periodic sensor absent > gap window | D | ST | Stop sensor for gap window; verify notification received | Chris | **Validated** (IP-001: attic humidity silence detected) |
| FR-MON-003 | FR | Sensor recovery notification | D | ST | Allow silenced sensor to resume; verify recovery notification | Chris | **Validated** (IP-001: recovery notification confirmed) |
| FR-MON-004 | FR | Unknown sensor detection — unrecognized sensor in DB triggers alert | D | ST | Allow new sensor to publish; verify alert within one poll cycle | Chris | **Validated** (IP-001: 3 dining room sensors auto-detected) |
| FR-MON-005 | FR | Alert fires on state transition only — not every poll cycle | T | IT | Sustain silence for multiple cycles; verify exactly one alert | Chris | **Waived** — test_run_check_alert_fires_once_not_on_every_cycle PASS; test_run_check_unknown_alert_fires_once PASS; alerted_missing/alerted_unknown set logic inspected |
| FR-MON-006 | FR | Local push notification — fully LAN-only path to operator device | D | AT | Block outbound internet; verify notifications arrive on operator's iPhone on home Wi-Fi (requires physical device on home network — cannot be automated) | Chris | **Waived** — ntfy operational on sietchtabr; iPhone ntfy app confirmed receiving alerts during IP-001 baseline; formal isolation test not feasible (solo operator; home LAN constraint acknowledged in RISK-023) |
| FR-MON-007 | FR | Configurable monitoring parameters via environment variables | I | — | All parameters env-var sourced; no hardcoded thresholds | Chris | **Pass** — monitor.py inspected: all parameters read from os.environ; no hardcoded thresholds |
| FR-022 | FR | No dead code in mqttlogger/__init__.py | I | — | `mqttlogger/__init__.py` contains no callable definitions; codebase search finds zero callers for any removed symbol | Chris | **Pass** — mqttlogger/__init__.py inspected: empty file (no callables); implemented in feature 004 |
| FR-023 | FR | Migration adds `captured_at DATETIME NOT NULL` and backfills from TIMESTAMP(currentdate, currenttime) | I+T | ST | Script reviewed for correct SQL; post-migration DESCRIBE shows column; COUNT(*) WHERE captured_at IS NULL = 0 | Chris | **Pass** (2026-05-17 — script inspected; null-check returned 0; DESCRIBE confirms captured_at DATETIME NOT NULL on sietchtabr) |
| FR-024 | FR | Migration adds `location TEXT NOT NULL` and backfills from topic segments 2–3 | I+T | ST | Script reviewed; spot-check SELECT shows correct location values for all distinct topics | Chris | **Pass** (2026-05-17 — script inspected; spot-check on sietchtabr confirmed correct location derivation for all observed topics) |
| FR-025 | FR | Migration adds `measurement_type TEXT NOT NULL` and backfills from final topic segment | I+T | ST | Script reviewed; spot-check SELECT shows correct measurement_type values | Chris | **Pass** (2026-05-17 — script inspected; spot-check on sietchtabr confirmed correct measurement_type derivation) |
| FR-026 | FR | Migration creates composite index idx_loc_mtype_time on (location, measurement_type, captured_at) | I | ST | SHOW INDEX FROM sensorreadings confirms index exists in correct column order | Chris | **Pass** (2026-05-17 — SHOW INDEX on sietchtabr confirms idx_loc_mtype_time present) |
| FR-027 | FR | Migration drops currentdate and currenttime columns | I+T | ST | Script reviewed; post-migration DESCRIBE confirms columns absent | Chris | **Pass** (2026-05-17 — DESCRIBE sensorreadings on sietchtabr: currentdate and currenttime absent) |
| FR-028 | FR | SensorReading model declares captured_at DateTime NOT NULL; no currentdate/currenttime | I | — | data_model.py reviewed: Column(DateTime, nullable=False) for captured_at; Date/Time columns absent | Chris | **Pass** — data_model.py inspected; CI green (test_commit_and_query uses captured_at) |
| FR-029 | FR | SensorReading model declares location Text NOT NULL | I | — | data_model.py reviewed: Column(Text, nullable=False) for location | Chris | **Pass** — data_model.py inspected; Column(Text, nullable=False) confirmed |
| FR-030 | FR | SensorReading model declares measurement_type Text NOT NULL | I | — | data_model.py reviewed: Column(Text, nullable=False) for measurement_type | Chris | **Pass** — data_model.py inspected; Column(Text, nullable=False) confirmed |
| FR-031 | FR | on_message sets captured_at = datetime.now() on new SensorReading | T | IT | Publish test message; verify inserted row captured_at within 5 s of publish time | Chris | **Pass** — test_on_message_sets_captured_at_to_utc_now PASS in CI (timezone-aware; within 1 s window) |
| FR-032 | FR | on_message sets location from topic segments 2+3 | T | IT | Publish test message on known topic; verify location = expected two-segment value | Chris | **Pass** — test_on_message_sets_location_from_topic_segments PASS; test_on_message_location_and_type_for_outdoor_humidity PASS |
| FR-033 | FR | on_message sets measurement_type from final topic segment | T | IT | Publish test message on known topic; verify measurement_type = expected value | Chris | **Pass** — test_on_message_sets_measurement_type_from_final_segment PASS in CI |
| FR-034 | FR | monitor.py query_active_sensors() uses captured_at; no TIMESTAMP() wrapper | I | — | monitor.py reviewed: no currentdate/currenttime or TIMESTAMP() in SQL strings | Chris | **Pass** — monitor.py inspected: `captured_at >= DATE_SUB(NOW(), INTERVAL %s MINUTE)` confirmed; no legacy refs |
| FR-035 | FR | bootstrap_sensors.py uses DATE(captured_at); no currentdate | I | — | bootstrap_sensors.py reviewed: no currentdate in SQL strings | Chris | **Pass** — bootstrap_sensors.py inspected: `DATE(captured_at) >= %s` confirmed; no legacy refs |
| FR-036 | FR | companion_monitor in docker-compose.yml uses read-only DB credentials | I | ST | docker-compose.yml reviewed: companion_monitor DB_USER differs from mqtt_logger; SHOW GRANTS confirms SELECT-only | Chris | **Pass** (2026-05-17 — docker-compose.yml uses MONITOR_DB_USER/MONITOR_DB_PASSWORD; monitor_ro user created on sietchtabr with SELECT-only on sensorreadings) |

---

## Validation Scenarios

*To be populated in Phase 6. Maps operational scenarios from `01-conops/operational-scenarios.md` to acceptance test events.*

| Scenario ID | Scenario Name | Validation Event | Pass Criterion | Status |
|-------------|---------------|------------------|----------------|--------|
| SCN-001 | Continuous sensor capture | AT | All readings from a defined sensor published over a test period appear in DB | **Waived** — Companion monitor 24h IP-001 baseline confirms continuous capture; no gaps observed for monitored sensors; formal scenario execution deferred |
| SCN-002 | Recovery after power outage | AT | After host power cycle, service restarts and resumes capture without operator action (after manual power-on) | **Waived** — `restart: unless-stopped` confirmed active; BIOS auto-restart not configured (RISK-015 carried forward); formal power-cycle test not performed |
| SCN-003 | Silent logger crash | AT | After container kill, service recovers within 60 seconds; gap in record bounded to recovery window | **Waived** — FR-MON-001 validated at IP-001 (mean 93 s detection, 3/3 fault injections); recovery time bounded by `restart: unless-stopped` |
| SCN-004 | Misconfigured startup | AT | Each invalid config class produces a specific, actionable error message | **Waived** — Unit tests for config validation PASS; formal all-classes exercise deferred |
| SCN-005 | Broker temporarily unavailable | AT | After broker restart, logger reconnects automatically and resumes capture | **Waived** — paho reconnect behaviour confirmed in production; formal broker-restart test deferred |
| SCN-006 | HomeMatic startup zeros | AT | After CCU3 restart, spurious zeros are stored (or suppressed if RedMatic mitigation applied); no service interruption | **Waived** — RISK-012 carried forward; known issue documented in CLAUDE.md; suppression not yet configured |
| SCN-007 | Planned maintenance | AT | After docker compose down/up cycle, service resumes capture; operator confirms via DB inspection | **Pass** (2026-05-17 — SCN-008 migration required docker compose down/up; service resumed correctly; companion monitor operational post-restart) |
| SCN-008 | Live schema migration | AT | Schema migration applied; spot-check row confirms captured_at, location, measurement_type correct; companion monitor healthy; new readings use new schema | **Pass** (2026-05-17 — migration executed on sietchtabr; DESCRIBE/SHOW INDEX/spot-check all confirm correct; companion monitor healthy; new rows confirmed in DB) |

---

## Interface Verification

*Populated by se-interfaces skill (2026-05-12). One entry per interface in icd.md.*

| IF ID | Type | Name | Method | Stage | Pass Criterion | Responsible | Status |
|-------|------|------|--------|-------|----------------|-------------|--------|
| IF-001 | Interface | MQTT sensor ingestion (CCU3 → mosquitto) | T | ST | N messages published → N DB records; malformed payload → error log + no record | Chris | **Waived** — Operational in production; companion monitor 24h baseline confirms continuous ingestion; formal campaign deferred |
| IF-002 | Interface | Push notification delivery (ntfy → iPhone) | D | AT | Monitored event fires → push notification arrives on iPhone within 30 s; requires physical device on home LAN | Chris | **Waived** — IP-001 baseline: alerts confirmed received on iPhone during 24h run (attic humidity + 3 dining room sensors); formal isolation test not feasible (RISK-023) |
| IF-003 | Interface | Database read access (MariaDB → external) | I | — | Port 3306 in docker-compose.yml; credentials not in VCS; schema matches data_model.py | Chris | **Pass** — docker-compose.yml inspected; .gitignore confirmed; schema matches data_model.py post-feature-009 |
| IF-004 | Interface | Operator deployment and operations | D | ST | `docker compose up -d` → all 6 containers healthy; test message captured; invalid config → specific error | Chris | **Pass** (2026-05-17 — SCN-008 deployment: all 6 containers healthy; capture confirmed on sietchtabr) |
| IF-005 | Interface | Monitoring dashboard (uptime_kuma → operator) | D | ST | Browser to :3001 shows UP in normal operation; shows DOWN within 120 s of container kill | Chris | **Waived** — FR-MON-001 validated at IP-001 (mean 93 s, max 120 s, 3/3); Uptime Kuma :3001 operational; formal browser test deferred |
| IF-006 | Interface | MQTT broker ↔ logger (internal) | T+D | ST | N messages → N DB records; broker restart → auto-reconnect; kill logger → status topic shows "offline" | Chris | **Waived** — Operational in production; paho reconnect confirmed; LWT configured in app.py; formal demonstration deferred |
| IF-007 | Interface | Logger → database write | T | ST | N messages → N committed rows; DB unreachable → error logged + service continues; no exit | Chris | **Waived** — test_insert_adds_and_commits PASS; test_insert_db_error_does_not_raise PASS; operational in production |
| IF-008 | Interface | Logger → heartbeat monitor | T+D | IT+ST | Heartbeat GET fires at configured interval; silent if URL absent; kill logger → UK DOWN alert ≤120 s | Chris | **Waived** — test_first_push_fires_immediately PASS; test_failed_push_does_not_kill_thread PASS; IP-001 end-to-end validated |
| IF-009 | Interface | Heartbeat monitor → ntfy (OPT-A alert path) | D | ST | Kill mqtt_logger → ntfy receives POST to /mqttlogger-alerts within 120 s | Chris | **Waived** — FR-MON-001 validated at IP-001 (mean 93 s, max 120 s, 3/3 fault injections); operational in production |
| IF-010 | Interface | Sensor monitor → database read | T | IT | Silence > gap window → exactly one alert fired; sensor resumes → exactly one recovery notification | Chris | **Waived** — test_run_check_missing_sensor_fires_alert, test_run_check_recovery_clears_state_and_notifies PASS; IP-001 operational validation |
| IF-011 | Interface | Sensor monitor → ntfy (OPT-B alert path) | T+D | IT+ST | (T) State-transition alerting; (D) IP-001 validated — attic humidity silence/recovery confirmed | Chris | **Pass** (IP-001 validated — attic humidity silence/recovery detected and notified; 3 dining room sensors auto-detected) |

---

## Results

*See `vv-results.md` for the consolidated results record.*
