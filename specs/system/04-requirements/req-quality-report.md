# Requirements Quality Report

**System:** mqttlogger
**Feature:** 004-remove-init-legacy through 009-schema-evolution (all requirements through feature 009)
**Date:** 2026-05-12 (original); 2026-05-16 (feature 007 update); 2026-05-17 (feature 009 update)
**Status:** PASS WITH WARNINGS
**Last Updated By:** se-req-quality skill (feature 009)

---

## Summary

| Metric | Count |
| ------ | ----- |
| Total requirements checked | 26 |
| Requirements fully passing (clean PASS) | 10 |
| Requirements with WARNs only | 16 |
| Requirements with FAILs | 0 |
| Coverage gaps (needs without requirements) | 0 |

**Overall Result: PASS WITH WARNINGS**

All 26 requirements are traceable to a stakeholder need or NFR, verifiable by a feasible method,
unambiguous in intent, internally consistent, and feasibly implemented. No requirement fails any
of the eight IEEE 29148 quality attributes. Sixteen requirements carry Singular warnings — a
recurring pattern where a single requirement contains two closely related, causally inseparable
clauses. These do not block Phase 2 closure. Two previously open non-Singular warnings have been
resolved in this update: FR-MON-004 (Unambiguous — grammatical ambiguity, requirement rewritten)
and FR-MON-005 (Necessary — NEED-STK-001-002 co-source added). Four new requirements (FR-023
through FR-026) were added for feature 007-python312-upgrade and assessed in this run; all carry
only Singular warnings.

---

## Results by Requirement

### Clean PASSes

The following requirements satisfy all eight quality attributes without qualification:

| Req ID | Short Description |
| ------ | ----------------- |
| FR-001 | MQTT subscription — receive all messages on configured topic filter |
| FR-002 | Message parsing — device, timestamp, value extracted from payload |
| FR-009 | Non-root container execution |
| FR-010 | Docker Compose deployment — full stack via single command |
| FR-MON-001 | Crash notification ≤ 120 s after heartbeat silence |
| FR-MON-002 | Periodic sensor silence alert |
| FR-MON-003 | Sensor recovery notification |
| FR-MON-004 | Unknown sensor detection (rewritten 2026-05-16 — Unambiguous WARN resolved) |
| FR-MON-005 | Alert state transition logic (NEED-STK-001-002 co-source added 2026-05-16 — Necessary WARN resolved) |
| FR-022 | No dead code in mqttlogger/__init__.py |

---

### FR-003 — Persistent Storage

**Full Text:** "The system shall persistently write each parsed sensor reading to the configured
MariaDB database. A reading is considered captured only when the database transaction has
committed."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to SC-CONOPS-001, NFR-PERF-001 |
| Unambiguous | PASS | "committed" has one interpretation in a database context |
| Verifiable | PASS | T (ST): N published = N committed; verified empirically |
| Consistent | PASS | Consistent with NFR-PERF-001 and FR-002 |
| Complete | PASS | Covers success path; failure path covered by FR-005 |
| Singular | WARN | Two clauses: (1) "shall write" and (2) definitional "a reading is considered captured only when…". The second is a clarifying definition, not an independent capability. Acceptable but worth noting. |
| Feasible | PASS | Implemented |
| Traceable | PASS | SC-CONOPS-001, NFR-PERF-001 |

---

### FR-004 — Broker Reconnection

**Full Text:** "The system shall reconnect to the MQTT broker automatically after any connection
loss without operator intervention, and shall resume capture as soon as the broker is available."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to MODE-004, NFR-REL-001, SC-CONOPS-005 |
| Unambiguous | PASS | "automatically", "without operator intervention" are unambiguous |
| Verifiable | PASS | D (ST): stop broker; restart; verify reconnect and capture resume without operator action |
| Consistent | PASS | No conflicts |
| Complete | PASS | Trigger (connection loss) and response (reconnect + resume) both stated |
| Singular | WARN | "shall reconnect" and "shall resume capture" are joined by "and". They are operationally inseparable — reconnect without resuming capture would be a defect. Acceptable. |
| Feasible | PASS | Implemented via paho-mqtt built-in reconnect |
| Traceable | PASS | MODE-004, NFR-REL-001, SC-CONOPS-005 |

---

### FR-005 — Database Write Failure Handling

**Full Text:** "The system shall log an error and discard any message for which the database write
fails, then continue processing subsequent messages without interruption or restart."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to MODE-005, NFR-REL-001 |
| Unambiguous | PASS | "log", "discard", "continue" each have one interpretation |
| Verifiable | PASS | D (ST): make DB unreachable; verify service continues; failed writes logged and discarded |
| Consistent | PASS | Consistent with ADR-003 (write-or-discard) |
| Complete | PASS | Failure path fully specified; no TBDs |
| Singular | WARN | Three behaviors (log, discard, continue) describe one failure-handling policy. Decomposing would lose the policy's coherence. Acceptable. |
| Feasible | PASS | Implemented |
| Traceable | PASS | MODE-005, NFR-REL-001 |

---

### FR-006 — Lifecycle Event Logging

**Full Text:** "The system shall emit a structured log entry for each of the following lifecycle
events: broker connect, broker disconnect, message received, database write success, database
write failure, startup complete, and shutdown initiated."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to NFR-USE-002, Constitution IV |
| Unambiguous | PASS | Events enumerated; "structured log entry" defined by NFR-USE-002 |
| Verifiable | PASS | I (ST): exercise all event types; verify format per NFR-USE-002 |
| Consistent | PASS | Consistent with NFR-USE-002 |
| Complete | WARN | **The requirement lists 7 events; the V&V plan entry references "All 8 event types".** Either the requirement is missing one event, or the V&V plan count is wrong. The discrepancy must be resolved. Candidate 8th event: "database write failure" may have been intended to cover two sub-events (transient failure vs. permanent failure), or "message discarded" may be a distinct event not listed. |
| Singular | PASS | One requirement covering one logging policy |
| Feasible | PASS | Implemented |
| Traceable | PASS | NFR-USE-002, Constitution IV |

**Rewrite Suggestion (to resolve Complete WARN):**
Confirm whether 7 or 8 events are required. If 8, add the missing event to the list:
"The system shall emit a structured log entry for each of the following lifecycle events:
broker connect, broker disconnect, message received, database write success, **database write
failure (message discarded)**, startup complete, and shutdown initiated."
— or replace "database write success" and "database write failure" with "each database write
attempt, recording success or failure" and count accordingly.

---

### FR-007 — Graceful Shutdown

**Full Text:** "The system shall respond to SIGTERM and SIGINT by: stopping MQTT message receipt,
completing any in-flight database write, closing the broker connection cleanly, and exiting with
status 0, all within 10 seconds of signal receipt."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to MODE-003, NFR-REL-001, Constitution V, SC-CONOPS-006 |
| Unambiguous | PASS | Signals named; actions enumerated; time bound (10 s) stated |
| Verifiable | PASS | T (ST): send SIGTERM; verify clean exit ≤ 10 s; no orphaned connections; no partial DB rows |
| Consistent | PASS | No conflicts |
| Complete | PASS | All shutdown actions and time bound stated |
| Singular | WARN | Four sequential actions constitute one shutdown sequence. Splitting would produce four requirements for one indivisible operation. Acceptable. |
| Feasible | PASS | Implemented |
| Traceable | PASS | MODE-003, NFR-REL-001, Constitution V, SC-CONOPS-006 |

---

### FR-008 — External Configuration

**Full Text:** "The system shall load all environment-specific values — broker address and port,
database credentials, subscribed topics — exclusively from an external configuration file or
environment variables at startup. No environment-specific value shall be hardcoded in source
code."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to NFR-SEC-001, Constitution II |
| Unambiguous | PASS | "exclusively", "at startup", "hardcoded" are unambiguous |
| Verifiable | PASS | I: no credentials/addresses in source; system starts from config only |
| Consistent | PASS | No conflicts |
| Complete | PASS | Examples given; prohibition on hardcoding covers unlisted values |
| Singular | WARN | Positive statement ("shall load from external source") + negative statement ("no value shall be hardcoded") describe the same principle from two angles. Acceptable; the dual form reduces ambiguity about edge cases. |
| Feasible | PASS | Implemented |
| Traceable | PASS | NFR-SEC-001, Constitution II |

---

### FR-011 — Startup Configuration Validation

**Full Text:** "The system shall reject startup if any required configuration field is absent or
invalid. On rejection, the system shall emit an error message that identifies: (a) the specific
field name, (b) the configuration source (file or environment variable), and (c) the value that
was attempted, where applicable."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to NFR-USE-001, MODE-002 |
| Unambiguous | PASS | Three error message components (a), (b), (c) explicitly specified |
| Verifiable | PASS | T (ST): each invalid input class → error message naming field, source, attempted value |
| Consistent | PASS | Consistent with NFR-USE-001 |
| Complete | PASS | "where applicable" covers cases where attempted value is unavailable |
| Singular | WARN | "reject startup" and "emit error message" are two inseparable actions — rejection without a message would violate the intent. Acceptable. |
| Feasible | PASS | Implemented |
| Traceable | PASS | NFR-USE-001, MODE-002 |

---

### FR-012 — Bounded Log Files

**Full Text:** "The system shall write log output to rotating files with a configured maximum size
per file and a configured maximum number of retained files. Log size shall not grow unboundedly."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to Constitution IV |
| Unambiguous | PASS | "rotating files", "configured maximum size", "maximum number of retained files" are clear |
| Verifiable | PASS | I: RotatingFileHandler or equivalent with non-zero limits |
| Consistent | PASS | No conflicts |
| Complete | PASS | Covers size and count limits |
| Singular | WARN | Second sentence ("Log size shall not grow unboundedly") is redundant — it is a necessary consequence of satisfying the first clause, not an independent requirement. Acceptable for emphasis; no action required. |
| Feasible | PASS | Implemented |
| Traceable | PASS | Constitution IV |

---

### FR-013 — MQTT Last Will and Testament

**Full Text:** "The system shall register a Last Will and Testament (LWT) message with the broker
before establishing its connection. The LWT shall publish to a designated status topic with the
value `"offline"` so that the broker delivers this message automatically if the connection is
unexpectedly dropped."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to OPT-A evaluation log, RISK-016, NFR-REL-001 |
| Unambiguous | PASS | LWT semantics are well-defined in MQTT protocol; value and trigger stated |
| Verifiable | PASS | T (ST): kill process without SIGTERM; verify broker publishes "offline" to status topic |
| Consistent | PASS | No conflicts |
| Complete | PASS | Registration timing ("before establishing"), topic type ("designated status topic"), value ("offline"), trigger ("unexpectedly dropped") all stated |
| Singular | WARN | Two-sentence structure describes one atomic LWT capability. The second sentence elaborates, not adds. Acceptable. |
| Feasible | PASS | Implemented |
| Traceable | PASS | OPT-A, RISK-016, NFR-REL-001 |

---

### FR-014 — HTTP Liveness Heartbeat

**Full Text:** "The system shall emit an HTTP push to a configurable heartbeat endpoint at a
configurable interval (default 60 seconds) when a heartbeat URL is present in configuration. If
no heartbeat URL is configured, the heartbeat shall be silently skipped."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to OPT-A convergence, RISK-016 |
| Unambiguous | PASS | "HTTP push", "configurable interval", "present/absent URL" all clear |
| Verifiable | PASS | T (IT): with URL → push at interval; without URL → silent; both verified |
| Consistent | PASS | No conflicts |
| Complete | PASS | Both the URL-present and URL-absent cases fully specified |
| Singular | WARN | Covers two complementary conditions (URL present / URL absent). They are the complete behavior specification for one configurable feature. Splitting would produce two requirements with no independent value. Acceptable. |
| Feasible | PASS | Implemented |
| Traceable | PASS | OPT-A, RISK-016 |

---

### FR-MON-004 — Unknown Sensor Detection

**Full Text (rewritten 2026-05-16):** "The monitoring system shall notify the operator when a sensor whose topic is not present in the known sensor configuration and is not listed in the excluded (event-driven) sensors list publishes readings to the database."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to OPT-B, RISK-013 |
| Unambiguous | PASS | **RESOLVED 2026-05-16** — "whose topic" unambiguously modifies "sensor"; relative clause ambiguity from prior version eliminated |
| Verifiable | PASS | D (ST): allow new sensor to publish; verify alert within one poll cycle |
| Consistent | PASS | No conflicts |
| Complete | PASS | Positive condition (not in config) and negative condition (not on excluded list) both stated |
| Singular | PASS | One detection event, one response |
| Feasible | PASS | Validated (IP-001: 3 dining room sensors auto-detected) |
| Traceable | PASS | OPT-B, RISK-013 |

---

### FR-MON-005 — Alert State Transition Logic

**Full Text:** "The monitoring system shall track alert state in memory so that each alert fires
exactly once on transition (normal → alert, alert → normal), not on every polling cycle."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | **RESOLVED 2026-05-16** — Source field updated to include NEED-STK-001-002 alongside "OPT-B design"; explicit stakeholder need trace now in place |
| Unambiguous | PASS | "exactly once", "on transition", both transitions enumerated |
| Verifiable | PASS | T (IT): sustain silence for multiple cycles; verify exactly one alert |
| Consistent | PASS | No conflicts |
| Complete | PASS | Covers both transitions (normal→alert, alert→normal) |
| Singular | PASS | One behavioral property about state management |
| Feasible | PASS | Implemented |
| Traceable | PASS | Source: OPT-B design, NEED-STK-001-002 |

---

### FR-MON-006 — Local Push Notification Delivery

**Full Text:** "All monitoring notifications shall be delivered via a self-hosted push notification
server without requiring any internet connectivity. The full path from event detection to operator
device notification shall function on an isolated local network."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to no-cloud constraint from explore-summary |
| Unambiguous | PASS | "self-hosted", "without internet connectivity", "isolated local network" are clear |
| Verifiable | PASS | D (AT): block outbound internet; verify notifications arrive on operator device via LAN |
| Consistent | PASS | RISK-023 (LAN-only limitation) is documented; requirement is not contradicted by it |
| Complete | PASS | Full path described |
| Singular | WARN | Two sentences describing the same LAN-only constraint from two angles. Acceptable; the second sentence emphasises end-to-end scope, which aids verification. |
| Feasible | PASS | Implemented; RISK-023 notes the off-LAN gap, which is an accepted operational limitation |
| Traceable | PASS | IP-001 constraint, explore-summary |

---

### FR-MON-007 — Configurable Monitoring Parameters

**Full Text:** "The monitoring system shall accept the following parameters exclusively via
environment variables: polling interval (seconds), gap window (minutes), database connection
details, notification server URL, and sensor configuration file path. No monitoring parameter
shall be hardcoded."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to Constitution II, NFR-SEC-001 |
| Unambiguous | PASS | Parameters enumerated; "exclusively" is unambiguous |
| Verifiable | PASS | I: verify env var reads in monitor.py; verify no hardcoded thresholds |
| Consistent | PASS | Consistent with FR-008 (logger configuration) |
| Complete | PASS | All known parameters listed; prohibition covers unlisted ones |
| Singular | WARN | Positive + negative statements of same principle (same pattern as FR-008). Acceptable. |
| Feasible | PASS | Implemented |
| Traceable | PASS | Constitution II, NFR-SEC-001 |

---

---

### FR-023 — Main App Python 3.12 Runtime

**Full Text:** "The main application container image shall use Python 3.12 as its base runtime. The `Dockerfile` shall specify `FROM python:3.12-slim` as its base image."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to RISK-003 (Python 3.10 EOL October 2026), NEED-STK-001-004 (continuous unattended operation) |
| Unambiguous | PASS | "Python 3.12", "`Dockerfile`", "`FROM python:3.12-slim`" — all precise and single-interpretation |
| Verifiable | PASS | I: grep `Dockerfile` for `FROM python:3.12-slim`; binary pass/fail |
| Consistent | PASS | No conflicts with existing requirements or NFRs; aligns with NFR-PORT-001 |
| Complete | PASS | Goal (Python 3.12 runtime) and verification artifact (Dockerfile FROM line) both specified |
| Singular | WARN | Two sentences: first states the goal; second specifies the implementation artifact. They are not independent — the Dockerfile FROM line is the only mechanism. Acceptable; the second sentence makes verification unambiguous. |
| Feasible | PASS | `python:3.12-slim` is available on Docker Hub with amd64/arm64 multi-arch support |
| Traceable | PASS | FR-023, traces to RISK-003, NEED-STK-001-004 |

---

### FR-024 — Companion Monitor Python 3.12 Runtime

**Full Text:** "The companion monitor container image shall use Python 3.12 as its base runtime. The `companion-monitor/Dockerfile` shall specify `FROM python:3.12-slim` as its base image."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to RISK-003, NEED-STK-001-004; companion monitor runs on a Python runtime that is independent of the main app |
| Unambiguous | PASS | Specific file path and FROM value stated |
| Verifiable | PASS | I: grep `companion-monitor/Dockerfile` for `FROM python:3.12-slim`; binary pass/fail |
| Consistent | PASS | No conflicts; aligns with FR-023 (same upgrade obligation for both containers) |
| Complete | PASS | Goal and artifact both specified; no TBDs |
| Singular | WARN | Same two-sentence pattern as FR-023; acceptable for same reason |
| Feasible | PASS | Same base image as FR-023 |
| Traceable | PASS | FR-024, traces to RISK-003, NEED-STK-001-004 |

---

### FR-025 — CI Pipeline Python 3.12 Alignment

**Full Text:** "The CI pipeline shall execute all lint, test, and coverage jobs using Python 3.12. All `python-version` entries in `.github/workflows/ci.yml` shall specify `"3.12"`."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to RISK-003, NFR-MAIN-001; CI must validate on the runtime the containers use — divergence would make test results non-representative |
| Unambiguous | PASS | "all lint, test, and coverage jobs", "all `python-version` entries", `"3.12"` — all precise |
| Verifiable | PASS | I: verify `ci.yml` entries; T: CI jobs pass on Python 3.12 |
| Consistent | PASS | Aligns with NFR-MAIN-001 (80% coverage gate) and FR-023/FR-024 (Python 3.12 runtime) |
| Complete | PASS | Covers all jobs ("all entries"); no TBDs |
| Singular | WARN | Two sentences: goal + mechanism. Same acceptable pattern as FR-023/FR-024 |
| Feasible | PASS | `setup-python@v5` in GitHub Actions supports Python 3.12 |
| Traceable | PASS | FR-025, traces to RISK-003, NFR-MAIN-001 |

---

### FR-026 — Python 3.12-Compatible Dependency Pins

**Full Text:** "All Python packages in `requirements.txt` shall be pinned to versions that support Python 3.12. The following minimum versions shall be satisfied: `greenlet >= 3.0.0`, `SQLAlchemy >= 1.4.50,<2.0`, and `mysqlclient >= 2.2.0`. All other existing pins shall remain unchanged unless upgrading them is required to achieve Python 3.12 compatibility."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to RISK-003, NEED-STK-001-004; without compatible dependency pins the containers cannot be built on Python 3.12 |
| Unambiguous | PASS | Package names and version constraints are explicit; "remain unchanged unless required" has clear intent (minimum-change principle) |
| Verifiable | PASS | I: inspect `requirements.txt` for specified minimum versions; T: CI passes on Python 3.12 with the updated pins |
| Consistent | PASS | Aligns with Constitution Development Workflow Rule 5 (pinned versions in requirements.txt) |
| Complete | PASS | Three specific packages named with minimum versions; "all other pins unchanged" closes the scope |
| Singular | WARN | Three package constraints stated in one requirement — all serve the single Python 3.12 compatibility obligation. Per FR-003/FR-004/FR-007 precedent, combining causally inseparable obligations is acceptable |
| Feasible | PASS | greenlet 3.0.0, SQLAlchemy 1.4.50, mysqlclient 2.2.0 all exist on PyPI and support Python 3.12 |
| Traceable | PASS | FR-026, traces to RISK-003, NEED-STK-001-004, Constitution Development Workflow Rule 5 |

---

## Coverage Gaps

None. All 14 stakeholder needs (NEED-STK-001-001 through NEED-STK-002-003) are covered by at
least one functional requirement or NFR.

---

## Consistency Issues

None. No requirements contradict each other or any NFR or constitutional principle.

---

## Action Summary

### Must Fix (FAIL items — Phase 2 cannot close until resolved)

None. No requirements fail any quality attribute.

### Should Fix Before Phase 3 (WARN items worth addressing)

| REQ-ID | Attribute | Concern | Resolution |
| ------ | --------- | ------- | ---------- |
| FR-006 | Complete | ~~Lists 7 lifecycle events; V&V plan references "8 event types" — inconsistency~~ | **RESOLVED** — V&V plan corrected to 7 event types |
| FR-MON-004 | Unambiguous | ~~"a sensor publishes readings that is not present" — grammatical ambiguity~~ | **RESOLVED 2026-05-16** — requirement rewritten; "whose topic" now unambiguously modifies "sensor" |
| FR-MON-005 | Necessary | ~~Traces to "OPT-B design"; no explicit NEED-ID~~ | **RESOLVED 2026-05-16** — NEED-STK-001-002 added as co-source in requirements register |

No open "Should Fix" items remain.

### Acceptable WARNs (low priority, no action required)

The Singular WARNs on FR-003, FR-004, FR-005, FR-007, FR-008, FR-011, FR-012, FR-013, FR-014,
FR-MON-006, FR-MON-007 all follow the same pattern: two closely related, causally inseparable
clauses in one requirement. This is a common and accepted pattern in system-level requirements
where splitting would reduce rather than improve clarity. No refactoring required.

---

# Feature 009 — Schema Evolution Quality Review

**Date:** 2026-05-17
**Last Updated By:** se-req-quality skill

---

## Summary (Feature 009 Batch)

| Metric | Count |
| ------ | ----- |
| Total requirements checked | 14 |
| Requirements fully passing (clean PASS) | 6 |
| Requirements with WARNs only | 8 |
| Requirements with FAILs | 0 |
| Coverage gaps (needs without requirements) | 0 |

**Overall Result: PASS WITH WARNINGS**

All 14 schema-evolution requirements are traceable to a stakeholder need or NFR, verifiable by a
feasible method, and feasibly implemented by the selected migration approach (OPT-A). No requirement
fails any of the eight IEEE 29148 quality attributes. Eight requirements carry warnings: six are
acceptable Singular/Complete patterns (add+populate for NOT NULL columns is an indivisible operation)
and two are higher-priority Should Fix items — FR-027 (vague "verified" criterion) and FR-031
(timezone-ambiguous `datetime.now()` call). Neither blocks Phase 2 closure.

---

## Clean PASSes

| Req ID | Short Description |
| ------ | ----------------- |
| FR-030 | Migration creates composite index `idx_loc_mtype_time` |
| FR-033 | SensorReading model declares `location Text NOT NULL` |
| FR-034 | SensorReading model declares `measurement_type Text NOT NULL` |
| FR-037 | `on_message` sets `measurement_type` from final topic segment |
| FR-038 | `query_active_sensors()` uses `captured_at`; no `TIMESTAMP()` |
| FR-039 | `bootstrap_sensors.py` uses `DATE(captured_at)`; no `currentdate` |

---

## FR-027 — Migration: Add `captured_at`

**Full Text:** "The migration script shall add a column `captured_at DATETIME NOT NULL` to the
`sensorreadings` table and populate it for every existing row with `TIMESTAMP(currentdate,
currenttime)` for that row, executed within a transaction before any `DROP COLUMN` statement."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to NEED-STK-001-008, NEED-STK-001-010, NFR-INT-003, NFR-MAIN-002 |
| Unambiguous | PASS | SQL expression stated explicitly; transaction placement stated |
| Verifiable | PASS | I+T (ST): inspect SQL; DESCRIBE confirms column; COUNT(*) WHERE IS NULL = 0 |
| Consistent | PASS | Consistent with FR-032 (model), FR-035 (on_message) |
| Complete | PASS | ADD, POPULATE, and transaction ordering all specified |
| Singular | WARN | "add column" and "populate every row" are inseparable for a NOT NULL column — MariaDB requires a DEFAULT or immediate UPDATE; splitting would produce an unexecutable requirement. Acceptable per FR-011 precedent. |
| Feasible | PASS | Standard InnoDB ALTER TABLE + UPDATE pattern |
| Traceable | PASS | SCN-008 Step 4; NFR-INT-003; NFR-MAIN-002 |

---

## FR-028 — Migration: Add `location`

**Full Text:** "The migration script shall add a column `location TEXT NOT NULL` to the
`sensorreadings` table and populate it for every existing row with
`SUBSTRING_INDEX(SUBSTRING_INDEX(device, '/', 3), '/', -2)` — the second and third
slash-delimited path segments of `device`, joined by a forward slash."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to NEED-STK-001-008, NEED-STK-001-010, NFR-INT-003 |
| Unambiguous | PASS | SQL expression stated explicitly; example given |
| Verifiable | PASS | I+T (ST): inspect SQL; spot-check SELECT confirms derivation |
| Consistent | PASS | Consistent with FR-033, FR-036 |
| Complete | PASS | Expression, example, and NOT NULL constraint all specified |
| Singular | WARN | ADD + POPULATE inseparable for NOT NULL. Same pattern as FR-027. Acceptable. |
| Feasible | PASS | SQL expression correct; validated in ASM-A-002 design phase |
| Traceable | PASS | SCN-008; NFR-INT-003; OPT-A convergence |

---

## FR-029 — Migration: Add `measurement_type`

**Full Text:** "The migration script shall add a column `measurement_type TEXT NOT NULL` to the
`sensorreadings` table and populate it for every existing row with `SUBSTRING_INDEX(device, '/',
-1)` — the final slash-delimited path segment of `device`."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to NEED-STK-001-008, NEED-STK-001-010, NFR-INT-003 |
| Unambiguous | PASS | SQL expression and example stated |
| Verifiable | PASS | I+T (ST): inspect SQL; spot-check SELECT confirms derivation |
| Consistent | PASS | Consistent with FR-034, FR-037 |
| Complete | PASS | Expression and example specified |
| Singular | WARN | ADD + POPULATE inseparable for NOT NULL. Same pattern as FR-027. Acceptable. |
| Feasible | PASS | Simple SUBSTRING_INDEX; validated in ASM-A-003 design phase |
| Traceable | PASS | SCN-008; NFR-INT-003; OPT-A convergence |

---

## FR-031 — Migration: Drop Legacy Timestamp Columns

**Full Text:** "The migration script shall drop the `currentdate` and `currenttime` columns from
`sensorreadings` after all three new columns have been populated and verified."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to NEED-STK-001-008, NFR-INT-003 |
| Unambiguous | PASS | Target columns named; sequencing stated |
| Verifiable | PASS | I+T: DROP COLUMN statements in script after backfill; DESCRIBE confirms absence |
| Consistent | PASS | Consistent with FR-027–FR-029 |
| Complete | WARN | **"populated and verified" is vague.** What constitutes verified? An engineer could interpret this as any informal check. Should specify the explicit SQL criterion used to verify before dropping. |
| Singular | WARN | Dropping two columns is one logical operation (remove the legacy timestamp pair). Acceptable. |
| Feasible | PASS | Standard DDL |
| Traceable | PASS | SCN-008; NFR-INT-003 |

**Rewrite Suggestion (to resolve Complete WARN):**
"The migration script shall drop the `currentdate` and `currenttime` columns from
`sensorreadings` after all three new columns have been populated **and after executing
`SELECT COUNT(*) FROM sensorreadings WHERE captured_at IS NULL` and confirming the result
is zero.**"

---

## FR-032 — Model: `captured_at` Column

**Full Text:** "The `SensorReading` SQLAlchemy model in `mqttlogger/data_model.py` shall declare
`captured_at` as a `DateTime` column that does not permit null values, and shall not declare
`currentdate` or `currenttime` columns."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to NEED-STK-001-008, NFR-INT-003 |
| Unambiguous | PASS | Column name, type, nullable constraint, and excluded column names all stated |
| Verifiable | PASS | I: Column(DateTime, nullable=False) present; Date/Time columns absent |
| Consistent | PASS | Consistent with FR-027 (migration adds column), FR-035 (handler sets it) |
| Complete | PASS | Positive (declare captured_at) + negative (no currentdate/currenttime) fully specifies the obligation |
| Singular | WARN | Positive + negative form of same class property. Same pattern as FR-008. Acceptable. |
| Feasible | PASS | Standard SQLAlchemy column declaration |
| Traceable | PASS | SCN-008; NFR-INT-003 |

---

## FR-035 — `on_message`: Populate `captured_at`

**Full Text:** "The `on_message` handler in `mqttlogger/mqtt_client.py` shall set `captured_at`
on each new `SensorReading` to `datetime.now()` at the time the MQTT message is received."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to NEED-STK-001-001, NEED-STK-001-010 |
| Unambiguous | WARN | **`datetime.now()` is timezone-naive.** Whether the stored value is UTC, local time, or system-dependent is unspecified. If the host clock drifts or is in a non-UTC timezone, `datetime.now()` produces a timezone-ambiguous value that cannot be reliably compared across systems. Requirement should specify `datetime.now(timezone.utc)` or equivalent to make the semantic explicit. |
| Verifiable | PASS | T (IT): insert row; verify captured_at within 5 s of publish time |
| Consistent | PASS | Consistent with FR-027 (migration backfill uses TIMESTAMP() which is also server-local) |
| Complete | PASS | Trigger and value both specified |
| Singular | PASS | One field assignment |
| Feasible | PASS | `datetime.now()` or `datetime.now(timezone.utc)` are both trivial |
| Traceable | PASS | SCN-008; FR-002 |

**Rewrite Suggestion (to resolve Unambiguous WARN):**
"The `on_message` handler shall set `captured_at` on each new `SensorReading` to
`datetime.now(timezone.utc)` at the time the MQTT message is received."

---

## FR-036 — `on_message`: Populate `location`

**Full Text:** "The `on_message` handler shall set `location` on each new `SensorReading` to
the second and third slash-delimited path segments of the MQTT message topic, joined by a
forward slash (e.g. topic `environment/indoor/attic/temperature` → `location = 'indoor/attic'`)."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to NEED-STK-001-010 |
| Unambiguous | PASS | Algorithm stated; example given |
| Verifiable | PASS | T (IT): publish on known topic; verify location matches expected value |
| Consistent | PASS | Consistent with FR-028 (migration uses same derivation) |
| Complete | WARN | **Behavior for a non-conforming topic (fewer than 4 segments) is not specified.** The requirement assumes all topics follow the 4-level pattern. If a message arrives on a 3-level topic, `SUBSTRING_INDEX(topic, '/', -2)` would silently produce an incorrect value. The requirement does not state whether this should raise an error, log a warning, or is simply assumed impossible. ASM-A-001 pre-validates this assumption, but the code requirement itself is silent on error handling. |
| Singular | PASS | One field assignment |
| Feasible | PASS | Python string split or topic.split('/')[2:4] is trivial |
| Traceable | PASS | SCN-008; OPT-A convergence |

**Note:** The Complete WARN is mitigated by TASK-A-001 (pre-migration topic inventory) and
ASM-A-001 (assumption validated before production deployment). Once ASM-A-001 is resolved at
IP-001, the operational risk is negligible. No rewrite required before Phase 2 gate; the WARN
is recorded for implementation guidance.

---

## FR-040 — Companion Monitor: Read-Only Database Credentials

**Full Text:** "The `companion_monitor` service definition in `docker-compose.yml` shall supply
database credentials for a MariaDB user that has `SELECT`-only privileges on `sensorreadings`,
distinct from the write-capable credentials used by the `mqtt_logger` service."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to NEED-STK-001-008, NEED-STK-001-011, NFR-INT-002, RISK-028 |
| Unambiguous | PASS | "SELECT-only", "distinct from write-capable" are unambiguous |
| Verifiable | PASS | I+D: docker-compose.yml reviewed; SHOW GRANTS confirms SELECT-only |
| Consistent | PASS | Consistent with NFR-INT-002 |
| Complete | PASS | Credential separation and privilege level both specified |
| Singular | WARN | "supply credentials for a SELECT-only user" + "distinct from write-capable user" are two facets of one access-control policy. Same pattern as FR-008. Acceptable. |
| Feasible | PASS | MariaDB read-only user creation is standard |
| Traceable | PASS | NFR-INT-002; RISK-028; Constitution Principle I |

---

## Coverage Gaps (Feature 009)

None. All 14 feature 009 requirements are covered by at least one stakeholder need.
NEED-STK-001-008 (consistent schema with audit trail) and NEED-STK-001-010 (temporal and
device-level resolution) each have ≥6 requirements addressing them. NEED-STK-001-011
(trustworthy data) is covered by FR-040.

---

## Consistency Issues (Feature 009)

None. The migration requirements (FR-027–FR-031), model requirements (FR-032–FR-034),
handler requirements (FR-035–FR-037), companion monitor requirements (FR-038–FR-039),
and infrastructure requirement (FR-040) are mutually consistent. Each new field introduced
in the migration has a corresponding model declaration, handler assignment, and (where
applicable) companion monitor update.

---

## Action Summary (Feature 009)

### Must Fix (FAIL items — Phase 2 cannot close until resolved)

None.

### Should Fix Before Phase 3

| REQ-ID | Attribute | Concern | Recommendation |
| ------ | --------- | ------- | -------------- |
| FR-031 | Complete | "populated and verified" is vague — no criterion for what constitutes verified | Rewrite to specify: "…after executing `SELECT COUNT(*) FROM sensorreadings WHERE captured_at IS NULL` and confirming the result is zero" |
| FR-035 | Unambiguous | `datetime.now()` is timezone-naive; semantic (UTC vs. local time) unspecified | Rewrite to use `datetime.now(timezone.utc)` |

### Acceptable WARNs (no action required)

The Singular WARNs on FR-027, FR-028, FR-029, FR-032, FR-040 follow the add+populate / positive+negative
pattern common across this codebase (see FR-008, FR-011 precedent). The Complete WARN on FR-036 is
mitigated by the pre-deployment ASM-A-001 topic inventory check. No refactoring required before Phase 2 gate.
