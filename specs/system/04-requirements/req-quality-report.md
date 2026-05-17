# Requirements Quality Report

**System:** mqttlogger
**Feature:** 004-remove-init-legacy through 009-schema-evolution (all requirements through feature 009)
**Date:** 2026-05-12 (original); 2026-05-17 (feature 009 update)
**Status:** PASS WITH WARNINGS
**Last Updated By:** se-req-quality skill (feature 009)

---

## Summary

| Metric | Count |
| ------ | ----- |
| Total requirements checked | 22 |
| Requirements fully passing (clean PASS) | 8 |
| Requirements with WARNs only | 14 |
| Requirements with FAILs | 0 |
| Coverage gaps (needs without requirements) | 0 |

**Overall Result: PASS WITH WARNINGS**

All 22 requirements are traceable to a stakeholder need or NFR, verifiable by a feasible method,
unambiguous in intent, internally consistent, and feasibly implemented. No requirement fails any
of the eight IEEE 29148 quality attributes. Fourteen requirements carry Singular warnings — a
recurring pattern where a single requirement contains two closely related, causally inseparable
clauses. These do not block Phase 2 closure but are recorded for future refactoring. Two
requirements carry non-Singular warnings that are higher priority: FR-006 (Complete: event count
inconsistency — 7 listed, verification references 8) and FR-MON-004 (Unambiguous: grammatical
ambiguity in the trigger condition). Both are documented with rewrite suggestions below.

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

**Full Text:** "The monitoring system shall notify the operator when a sensor publishes readings
to the database that is not present in the known sensor configuration and is not on the excluded
(event-driven) sensors list."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to OPT-B, RISK-013 |
| Unambiguous | WARN | **"a sensor publishes readings to the database that is not present"** — the relative clause "that is not present" is grammatically ambiguous: does it modify "readings" or "sensor"? The intent (sensor not in config) is clear from context, but a strict reading could interpret it as "readings that are not present" — which is nonsensical. Low severity; intent is recoverable from context and validated test evidence. |
| Verifiable | PASS | D (ST): allow new sensor to publish; verify alert within one poll cycle |
| Consistent | PASS | No conflicts |
| Complete | PASS | Positive condition (not in config) and negative condition (not on excluded list) both stated |
| Singular | PASS | One detection event, one response |
| Feasible | PASS | Validated (IP-001: 3 dining room sensors auto-detected) |
| Traceable | PASS | OPT-B, RISK-013 |

**Rewrite Suggestion (to resolve Unambiguous WARN):**
"The monitoring system shall notify the operator when a sensor whose topic is not present in the
known sensor configuration **and** is not listed in the excluded (event-driven) sensors list
publishes readings to the database."

---

### FR-MON-005 — Alert State Transition Logic

**Full Text:** "The monitoring system shall track alert state in memory so that each alert fires
exactly once on transition (normal → alert, alert → normal), not on every polling cycle."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | WARN | **Traces to "OPT-B design" rather than an explicit stakeholder need ID.** The underlying need is NEED-STK-001-002 (failures surface visibly and immediately) — a flood of duplicate alerts would violate this need's intent. The trace should be made explicit. |
| Unambiguous | PASS | "exactly once", "on transition", both transitions enumerated |
| Verifiable | PASS | T (IT): sustain silence for multiple cycles; verify exactly one alert |
| Consistent | PASS | No conflicts |
| Complete | PASS | Covers both transitions (normal→alert, alert→normal) |
| Singular | PASS | One behavioral property about state management |
| Feasible | PASS | Implemented |
| Traceable | PASS | Source documented as "OPT-B design" — explicit need trace recommended |

**Recommended Action:** Update source field in requirements register to add
`NEED-STK-001-002` as a co-source alongside "OPT-B design".

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

| REQ-ID | Attribute | Concern | Recommendation |
| ------ | --------- | ------- | -------------- |
| FR-006 | Complete | ~~Lists 7 lifecycle events; V&V plan references "8 event types" — inconsistency~~ **RESOLVED at Phase 2 gate: V&V plan corrected to 7 event types.** | |
| FR-MON-004 | Unambiguous | "a sensor publishes readings that is not present" — grammatical ambiguity about what the relative clause modifies | Rewrite as: "…when a sensor **whose topic** is not present in the known sensor configuration and is not listed in the excluded sensors list…" |
| FR-MON-005 | Necessary | Traces to "OPT-B design"; no explicit NEED-ID | Add `NEED-STK-001-002` as co-source in requirements register |

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
| FR-026 | Migration creates composite index `idx_loc_mtype_time` |
| FR-029 | SensorReading model declares `location Text NOT NULL` |
| FR-030 | SensorReading model declares `measurement_type Text NOT NULL` |
| FR-033 | `on_message` sets `measurement_type` from final topic segment |
| FR-034 | `query_active_sensors()` uses `captured_at`; no `TIMESTAMP()` |
| FR-035 | `bootstrap_sensors.py` uses `DATE(captured_at)`; no `currentdate` |

---

## FR-023 — Migration: Add `captured_at`

**Full Text:** "The migration script shall add a column `captured_at DATETIME NOT NULL` to the
`sensorreadings` table and populate it for every existing row with `TIMESTAMP(currentdate,
currenttime)` for that row, executed within a transaction before any `DROP COLUMN` statement."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to NEED-STK-001-008, NEED-STK-001-010, NFR-INT-003, NFR-MAIN-002 |
| Unambiguous | PASS | SQL expression stated explicitly; transaction placement stated |
| Verifiable | PASS | I+T (ST): inspect SQL; DESCRIBE confirms column; COUNT(*) WHERE IS NULL = 0 |
| Consistent | PASS | Consistent with FR-028 (model), FR-031 (on_message) |
| Complete | PASS | ADD, POPULATE, and transaction ordering all specified |
| Singular | WARN | "add column" and "populate every row" are inseparable for a NOT NULL column — MariaDB requires a DEFAULT or immediate UPDATE; splitting would produce an unexecutable requirement. Acceptable per FR-011 precedent. |
| Feasible | PASS | Standard InnoDB ALTER TABLE + UPDATE pattern |
| Traceable | PASS | SCN-008 Step 4; NFR-INT-003; NFR-MAIN-002 |

---

## FR-024 — Migration: Add `location`

**Full Text:** "The migration script shall add a column `location TEXT NOT NULL` to the
`sensorreadings` table and populate it for every existing row with
`SUBSTRING_INDEX(SUBSTRING_INDEX(device, '/', 3), '/', -2)` — the second and third
slash-delimited path segments of `device`, joined by a forward slash."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to NEED-STK-001-008, NEED-STK-001-010, NFR-INT-003 |
| Unambiguous | PASS | SQL expression stated explicitly; example given |
| Verifiable | PASS | I+T (ST): inspect SQL; spot-check SELECT confirms derivation |
| Consistent | PASS | Consistent with FR-029, FR-032 |
| Complete | PASS | Expression, example, and NOT NULL constraint all specified |
| Singular | WARN | ADD + POPULATE inseparable for NOT NULL. Same pattern as FR-023. Acceptable. |
| Feasible | PASS | SQL expression correct; validated in ASM-A-002 design phase |
| Traceable | PASS | SCN-008; NFR-INT-003; OPT-A convergence |

---

## FR-025 — Migration: Add `measurement_type`

**Full Text:** "The migration script shall add a column `measurement_type TEXT NOT NULL` to the
`sensorreadings` table and populate it for every existing row with `SUBSTRING_INDEX(device, '/',
-1)` — the final slash-delimited path segment of `device`."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to NEED-STK-001-008, NEED-STK-001-010, NFR-INT-003 |
| Unambiguous | PASS | SQL expression and example stated |
| Verifiable | PASS | I+T (ST): inspect SQL; spot-check SELECT confirms derivation |
| Consistent | PASS | Consistent with FR-030, FR-033 |
| Complete | PASS | Expression and example specified |
| Singular | WARN | ADD + POPULATE inseparable for NOT NULL. Same pattern as FR-023. Acceptable. |
| Feasible | PASS | Simple SUBSTRING_INDEX; validated in ASM-A-003 design phase |
| Traceable | PASS | SCN-008; NFR-INT-003; OPT-A convergence |

---

## FR-027 — Migration: Drop Legacy Timestamp Columns

**Full Text:** "The migration script shall drop the `currentdate` and `currenttime` columns from
`sensorreadings` after all three new columns have been populated and verified."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to NEED-STK-001-008, NFR-INT-003 |
| Unambiguous | PASS | Target columns named; sequencing stated |
| Verifiable | PASS | I+T: DROP COLUMN statements in script after backfill; DESCRIBE confirms absence |
| Consistent | PASS | Consistent with FR-023–FR-025 |
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

## FR-028 — Model: `captured_at` Column

**Full Text:** "The `SensorReading` SQLAlchemy model in `mqttlogger/data_model.py` shall declare
`captured_at` as a `DateTime` column that does not permit null values, and shall not declare
`currentdate` or `currenttime` columns."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to NEED-STK-001-008, NFR-INT-003 |
| Unambiguous | PASS | Column name, type, nullable constraint, and excluded column names all stated |
| Verifiable | PASS | I: Column(DateTime, nullable=False) present; Date/Time columns absent |
| Consistent | PASS | Consistent with FR-023 (migration adds column), FR-031 (handler sets it) |
| Complete | PASS | Positive (declare captured_at) + negative (no currentdate/currenttime) fully specifies the obligation |
| Singular | WARN | Positive + negative form of same class property. Same pattern as FR-008. Acceptable. |
| Feasible | PASS | Standard SQLAlchemy column declaration |
| Traceable | PASS | SCN-008; NFR-INT-003 |

---

## FR-031 — `on_message`: Populate `captured_at`

**Full Text:** "The `on_message` handler in `mqttlogger/mqtt_client.py` shall set `captured_at`
on each new `SensorReading` to `datetime.now()` at the time the MQTT message is received."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to NEED-STK-001-001, NEED-STK-001-010 |
| Unambiguous | WARN | **`datetime.now()` is timezone-naive.** Whether the stored value is UTC, local time, or system-dependent is unspecified. If the host clock drifts or is in a non-UTC timezone, `datetime.now()` produces a timezone-ambiguous value that cannot be reliably compared across systems. Requirement should specify `datetime.now(timezone.utc)` or equivalent to make the semantic explicit. |
| Verifiable | PASS | T (IT): insert row; verify captured_at within 5 s of publish time |
| Consistent | PASS | Consistent with FR-023 (migration backfill uses TIMESTAMP() which is also server-local) |
| Complete | PASS | Trigger and value both specified |
| Singular | PASS | One field assignment |
| Feasible | PASS | `datetime.now()` or `datetime.now(timezone.utc)` are both trivial |
| Traceable | PASS | SCN-008; FR-002 |

**Rewrite Suggestion (to resolve Unambiguous WARN):**
"The `on_message` handler shall set `captured_at` on each new `SensorReading` to
`datetime.now(timezone.utc)` at the time the MQTT message is received."

---

## FR-032 — `on_message`: Populate `location`

**Full Text:** "The `on_message` handler shall set `location` on each new `SensorReading` to
the second and third slash-delimited path segments of the MQTT message topic, joined by a
forward slash (e.g. topic `environment/indoor/attic/temperature` → `location = 'indoor/attic'`)."

| Attribute | Result | Finding |
| --------- | ------ | ------- |
| Necessary | PASS | Traces to NEED-STK-001-010 |
| Unambiguous | PASS | Algorithm stated; example given |
| Verifiable | PASS | T (IT): publish on known topic; verify location matches expected value |
| Consistent | PASS | Consistent with FR-024 (migration uses same derivation) |
| Complete | WARN | **Behavior for a non-conforming topic (fewer than 4 segments) is not specified.** The requirement assumes all topics follow the 4-level pattern. If a message arrives on a 3-level topic, `SUBSTRING_INDEX(topic, '/', -2)` would silently produce an incorrect value. The requirement does not state whether this should raise an error, log a warning, or is simply assumed impossible. ASM-A-001 pre-validates this assumption, but the code requirement itself is silent on error handling. |
| Singular | PASS | One field assignment |
| Feasible | PASS | Python string split or topic.split('/')[2:4] is trivial |
| Traceable | PASS | SCN-008; OPT-A convergence |

**Note:** The Complete WARN is mitigated by TASK-A-001 (pre-migration topic inventory) and
ASM-A-001 (assumption validated before production deployment). Once ASM-A-001 is resolved at
IP-001, the operational risk is negligible. No rewrite required before Phase 2 gate; the WARN
is recorded for implementation guidance.

---

## FR-036 — Companion Monitor: Read-Only Database Credentials

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
(trustworthy data) is covered by FR-036.

---

## Consistency Issues (Feature 009)

None. The migration requirements (FR-023–FR-027), model requirements (FR-028–FR-030),
handler requirements (FR-031–FR-033), companion monitor requirements (FR-034–FR-035),
and infrastructure requirement (FR-036) are mutually consistent. Each new field introduced
in the migration has a corresponding model declaration, handler assignment, and (where
applicable) companion monitor update.

---

## Action Summary (Feature 009)

### Must Fix (FAIL items — Phase 2 cannot close until resolved)

None.

### Should Fix Before Phase 3

| REQ-ID | Attribute | Concern | Recommendation |
| ------ | --------- | ------- | -------------- |
| FR-027 | Complete | "populated and verified" is vague — no criterion for what constitutes verified | Rewrite to specify: "…after executing `SELECT COUNT(*) FROM sensorreadings WHERE captured_at IS NULL` and confirming the result is zero" |
| FR-031 | Unambiguous | `datetime.now()` is timezone-naive; semantic (UTC vs. local time) unspecified | Rewrite to use `datetime.now(timezone.utc)` |

### Acceptable WARNs (no action required)

The Singular WARNs on FR-023, FR-024, FR-025, FR-028, FR-036 follow the add+populate / positive+negative
pattern common across this codebase (see FR-008, FR-011 precedent). The Complete WARN on FR-032 is
mitigated by the pre-deployment ASM-A-001 topic inventory check. No refactoring required before Phase 2 gate.
