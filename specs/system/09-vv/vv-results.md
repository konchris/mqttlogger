# Verification and Validation Results

**System:** mqttlogger
**Feature:** 009-schema-evolution (Phase 6 closure)
**Date:** 2026-05-17
**Status:** COMPLETE — all entries resolved (Pass | Waived); no Fail results
**Conducted By:** operator (Chris) + se-gate skill

---

## Summary

| Category | Total | Pass | Waived | Fail |
|----------|-------|------|--------|------|
| NFRs | 14 | 7 | 7 | 0 |
| Functional Requirements | 36 | 20 | 16 | 0 |
| Validation Scenarios | 8 | 2 | 6 | 0 |
| Interface Verification | 11 | 4 | 7 | 0 |
| **Total** | **69** | **33** | **36** | **0** |

**Waiver rationale:** Waived entries are operational in production on sietchtabr with no
observed defects. The system is a solo-developer home automation project; a formal
test execution campaign for pre-existing baseline behaviour was not performed during
feature 009. All waived entries have supporting evidence from unit tests, CI runs,
or IP-001 24h baseline validation. Formal campaign execution is deferred per REQ-OI-003.

**No Must Have requirement has a Fail result.**

---

## NFR Results

| Req ID | Result | Evidence |
|--------|--------|----------|
| NFR-PERF-001 | Waived | Companion monitor 24h IP-001 baseline: no drops observed; production operational |
| NFR-PERF-002 | Waived | Architectural analysis: co-hosted broker sub-ms latency confirmed |
| NFR-PERF-003 | **Pass** | SHOW INDEX on sietchtabr 2026-05-17: idx_loc_mtype_time present on (location(255), measurement_type(255), captured_at) |
| NFR-REL-001 | Waived | `restart: unless-stopped` active; paho reconnect confirmed in production; test_insert_db_error_does_not_raise PASS |
| NFR-REL-002 | Waived | FR-MON-001 validated (mean 93 s detection); container restart sub-60 s observed |
| NFR-SEC-001 | **Pass** | .gitignore verified; git history scrubbed 2026-05-11; no credential values in current history |
| NFR-USE-001 | Waived | test_load_missing_keys_names_them PASS; test_missing_required_key_raises PASS |
| NFR-USE-002 | Waived | Log formatter inspected in app.py; all required fields present |
| NFR-MAIN-001 | **Pass** | CI on feature/009-schema-evolution: 50 tests passed, 1 skipped; coverage ≥80% gate enforced |
| NFR-PORT-001 | **Pass** | SCN-008 deployment 2026-05-17: `docker compose up -d` → all 6 containers healthy on sietchtabr (Linux amd64) |
| NFR-INT-001 | **Pass** | db/initial-schema.sql + db/migration-009-schema-evolution.sql; no out-of-band DDL; schema matches data_model.py |
| NFR-INT-002 | **Pass** | monitor_ro user created on sietchtabr with SELECT-only on mqttlogger.sensorreadings; docker-compose.yml uses MONITOR_DB_USER |
| NFR-INT-003 | **Pass** | DESCRIBE sensorreadings 2026-05-17: captured_at DATETIME NOT NULL present; currentdate/currenttime absent; no TIMESTAMP() in monitor.py or bootstrap_sensors.py |
| NFR-MAIN-002 | **Pass** | Migration script inspected: START TRANSACTION/COMMIT wraps UPDATE backfill; SELECT null-check gate (returned 0) before MODIFY/DROP |

---

## Functional Requirement Results

### Core Logger (FR-001..FR-014)

| Req ID | Result | Evidence |
|--------|--------|----------|
| FR-001 | Waived | Production operational; companion monitor 24h baseline confirms continuous capture |
| FR-002 | Waived | test_on_message_float_creates_correct_reading PASS; test_on_message_true/false_payload PASS |
| FR-003 | Waived | test_insert_adds_and_commits PASS; production operational |
| FR-004 | Waived | paho reconnect configured; `restart: unless-stopped` active |
| FR-005 | Waived | test_insert_db_error_does_not_raise PASS; production operational |
| FR-006 | Waived | Logging inspected in mqtt_client.py and app.py; all 7 event types present |
| FR-007 | Waived | test_clean_disconnect PASS; signal handlers in app.py inspected |
| FR-008 | **Pass** | Source inspected: no hardcoded credentials or addresses; config from config.json/env only |
| FR-009 | **Pass** | Dockerfile inspected: USER directive with non-root UID present |
| FR-010 | **Pass** | SCN-008 deployment 2026-05-17: full stack up via single command; capture operational |
| FR-011 | Waived | test_load_missing_keys_names_them PASS; test_missing_required_key_raises PASS |
| FR-012 | **Pass** | app.py inspected: RotatingFileHandler with maxBytes and backupCount configured |
| FR-013 | Waived | client.will_set() inspected in app.py; ADR-006 documents configuration |
| FR-014 | Waived | Heartbeat tests PASS; IP-001 end-to-end validated |

### Monitoring Stack (FR-MON-001..FR-MON-007)

| Req ID | Result | Evidence |
|--------|--------|----------|
| FR-MON-001 | **Pass** | IP-001 validated: mean 93 s, max 120 s, 3/3 fault injection runs |
| FR-MON-002 | **Pass** | IP-001 validated: attic humidity silence correctly detected and alerted |
| FR-MON-003 | **Pass** | IP-001 validated: attic humidity recovery notification confirmed |
| FR-MON-004 | **Pass** | IP-001 validated: 3 new dining room sensors auto-detected within one poll cycle |
| FR-MON-005 | Waived | test_run_check_alert_fires_once_not_on_every_cycle PASS; test_run_check_unknown_alert_fires_once PASS |
| FR-MON-006 | Waived | IP-001 baseline: alerts received on iPhone during 24h run; formal isolation test not feasible (RISK-023) |
| FR-MON-007 | **Pass** | monitor.py inspected: all parameters from os.environ; no hardcoded thresholds |

### Code Quality (FR-022)

| Req ID | Result | Evidence |
|--------|--------|----------|
| FR-022 | **Pass** | mqttlogger/__init__.py inspected: empty file; no callables; implemented in feature 004 |

### Schema Evolution (FR-023..FR-036)

| Req ID | Result | Evidence |
|--------|--------|----------|
| FR-023 | **Pass** | Migration SQL inspected; null-check returned 0 on sietchtabr; DESCRIBE confirms captured_at DATETIME NOT NULL |
| FR-024 | **Pass** | Migration SQL inspected; spot-check on sietchtabr: location derivation correct for all observed topics |
| FR-025 | **Pass** | Migration SQL inspected; spot-check on sietchtabr: measurement_type derivation correct |
| FR-026 | **Pass** | SHOW INDEX on sietchtabr 2026-05-17: idx_loc_mtype_time present |
| FR-027 | **Pass** | DESCRIBE sensorreadings on sietchtabr 2026-05-17: currentdate and currenttime absent |
| FR-028 | **Pass** | data_model.py inspected: Column(DateTime, nullable=False) for captured_at; Date/Time columns absent; CI green |
| FR-029 | **Pass** | data_model.py inspected: Column(Text, nullable=False) for location |
| FR-030 | **Pass** | data_model.py inspected: Column(Text, nullable=False) for measurement_type |
| FR-031 | **Pass** | test_on_message_sets_captured_at_to_utc_now PASS in CI (timezone-aware; within 1 s window) |
| FR-032 | **Pass** | test_on_message_sets_location_from_topic_segments PASS; test_on_message_location_and_type_for_outdoor_humidity PASS |
| FR-033 | **Pass** | test_on_message_sets_measurement_type_from_final_segment PASS in CI |
| FR-034 | **Pass** | monitor.py inspected: `captured_at >= DATE_SUB(NOW(), INTERVAL %s MINUTE)`; no legacy column refs |
| FR-035 | **Pass** | bootstrap_sensors.py inspected: `DATE(captured_at) >= %s`; no legacy column refs |
| FR-036 | **Pass** | docker-compose.yml inspected; monitor_ro user created on sietchtabr with SELECT-only on sensorreadings |

---

## Validation Scenario Results

| SCN ID | Name | Result | Evidence |
|--------|------|--------|----------|
| SCN-001 | Continuous sensor capture | Waived | Companion monitor 24h baseline confirms continuous capture |
| SCN-002 | Recovery after power outage | Waived | `restart: unless-stopped` active; RISK-015 (BIOS auto-restart) carried forward |
| SCN-003 | Silent logger crash | Waived | FR-MON-001 validated at IP-001; recovery bounded by restart policy |
| SCN-004 | Misconfigured startup | Waived | Config validation unit tests PASS |
| SCN-005 | Broker temporarily unavailable | Waived | paho reconnect confirmed in production |
| SCN-006 | HomeMatic startup zeros | Waived | RISK-012 carried forward; known issue; no service interruption observed |
| SCN-007 | Planned maintenance | **Pass** | SCN-008 migration required docker compose down/up; service resumed correctly 2026-05-17 |
| SCN-008 | Live schema migration | **Pass** | Executed 2026-05-17 on sietchtabr: DESCRIBE/SHOW INDEX/spot-check all PASS; companion monitor healthy; new rows confirmed |

---

## Interface Verification Results

| IF ID | Name | Result | Evidence |
|-------|------|--------|----------|
| IF-001 | MQTT sensor ingestion | Waived | Production operational; 24h baseline confirms continuous ingestion |
| IF-002 | Push notification delivery | Waived | IP-001 baseline: alerts received on iPhone; formal isolation test not feasible (RISK-023) |
| IF-003 | Database read access | **Pass** | docker-compose.yml inspected; credentials not in VCS; schema matches data_model.py |
| IF-004 | Operator deployment and operations | **Pass** | SCN-008 deployment 2026-05-17: all 6 containers healthy; capture confirmed |
| IF-005 | Monitoring dashboard (Uptime Kuma) | Waived | FR-MON-001 validated at IP-001; :3001 operational |
| IF-006 | MQTT broker ↔ logger (internal) | Waived | Production operational; paho reconnect confirmed; LWT configured |
| IF-007 | Logger → database write | Waived | Insert tests PASS; production operational |
| IF-008 | Logger → heartbeat monitor | Waived | Heartbeat tests PASS; IP-001 end-to-end validated |
| IF-009 | Heartbeat monitor → ntfy | Waived | FR-MON-001 validated at IP-001 (mean 93 s, max 120 s, 3/3) |
| IF-010 | Sensor monitor → database read | Waived | State-transition tests PASS; IP-001 operational validation |
| IF-011 | Sensor monitor → ntfy | **Pass** | IP-001 validated: attic humidity silence/recovery; 3 dining room sensors auto-detected |

---

## Open Items Carried Forward

| ID | Description | Owner |
|----|-------------|-------|
| REQ-OI-003 | Formal test execution campaign for FR-001..FR-014 (core logger) and NFR-PERF-001, NFR-REL-001/002, NFR-USE-001/002 deferred; waived at feature 009 Phase 6 closure | Chris |
| RISK-014 | Historical completeness verification — no mechanism exists; explicitly deferred post-009+008 | Chris |
| RISK-015 | BIOS auto-restart on sietchtabr not configured | Chris |
| RISK-023 | ntfy LAN-only — notifications not delivered when operator is off home network | Chris |
| RISK-024 | companion_monitor has no automated tests | Chris |
