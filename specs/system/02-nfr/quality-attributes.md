# Quality Attributes and Non-Functional Requirements

**System:** mqttlogger
**Feature:** 002-mqttlogger-baseline (created); 009-schema-evolution (updated)
**Date:** 2026-05-09 (created); 2026-05-17 (updated)
**Status:** DRAFT
**Last Updated By:** se-nfr skill (feature 009)

---

## Summary

| NFR ID | Category | Short Description | Priority | Verification Method | Status |
|--------|----------|-------------------|----------|---------------------|--------|
| NFR-PERF-001 | Performance | Message completeness — no drops due to processing backlog | Must Have | Test | Open |
| NFR-PERF-002 | Performance | Timestamp fidelity within sensor sampling interval | Must Have | Analysis | Open |
| NFR-PERF-003 | Performance | Composite index `(location, measurement_type, captured_at)` for filtered time-range queries | Must Have | Inspection | Open |
| NFR-REL-001 | Reliability | Automatic recovery from all software faults without operator intervention | Must Have | Demonstration | Open |
| NFR-REL-002 | Reliability | Recovery time ≤ 60 seconds after container crash | Must Have | Test | Open |
| NFR-SEC-001 | Security | Credentials not stored in version control | Must Have | Inspection | Open |
| NFR-USE-001 | Usability | Startup and connection errors identify specific field, source, and attempted value | Must Have | Test | Open |
| NFR-USE-002 | Usability | Every log entry contains timestamp, level, module, function, line number | Must Have | Inspection | Open |
| NFR-MAIN-001 | Maintainability | Automated test coverage ≥ 80% line coverage | Should Have | Test | Open |
| NFR-PORT-001 | Portability | Deployable via Docker Compose on Linux (amd64/arm64) only | Must Have | Demonstration | Open |
| NFR-INT-001 | Interoperability | Database schema owned by mqttlogger; all changes via migration scripts | Must Have | Inspection | Open |
| NFR-INT-002 | Interoperability | Non-logger consumers connect to MariaDB read-only; no writes permitted | Must Have | Inspection | Open |
| NFR-INT-003 | Interoperability | `captured_at` directly usable as DATETIME; no computed expressions required in downstream queries | Must Have | Inspection | Open |
| NFR-MAIN-002 | Maintainability | Migration script executes atomically; no partial state persists on failure | Must Have | Inspection | Open |

**Safety (SAF):** Not applicable — system is classified non-safety in the constitution.
**Regulatory (REG):** Not applicable — no regulatory obligations identified.

---

## NFR Details

### NFR-PERF-001 — Message Completeness

**Category:** Performance
**Priority:** Must Have
**Source:** NEED-STK-001-001; replaces SC-001 (5-second latency target — retired as analytically unmotivated)
**Status:** Open

**Statement:**
The system shall capture and persistently store every MQTT message received during normal operation without dropping messages due to processing backlog.

**Rationale:**
At approximately 50 devices publishing on value-change (estimated low tens of messages per minute), the message rate is well within the capacity of the current architecture. Completeness of the historical record is the primary purpose of the system; any dropped message represents a permanent, unrecoverable data gap. The previously stated 5-second capture-to-storage latency target (SC-001) is retired — it was not grounded in an operational requirement for a trend-analysis system.

**Verification Method:** Test
**Verification Notes:** Publish a defined number of messages to the broker at or above the estimated peak rate. Verify that the exact same number of records appears in the database. Test at both normal rate and simulated HomeMatic restart burst.

**Conflicts With:** None
**Conflict Resolution:** N/A

---

### NFR-PERF-002 — Timestamp Fidelity

**Category:** Performance
**Priority:** Must Have
**Source:** NEED-STK-001-010, NEED-STK-001-011
**Status:** Open

**Statement:**
The system shall record a capture timestamp for each reading that is within the sensor device's own publication interval of the actual time of measurement.

**Rationale:**
The primary use cases — seasonal trend analysis and renovation impact assessment — require temporal ordering and cross-sensor correlation. Millisecond accuracy is not required; accuracy within the sensor's publication interval (which for a value-change-only system may be minutes to hours) is analytically sufficient. The capture timestamp reflects time-of-receipt at the logger, not time-of-sensor-measurement; clock drift between sensor and host is not compensated.

**Verification Method:** Analysis
**Verification Notes:** With broker and logger co-hosted on the same machine, local network latency is sub-millisecond. NTP synchronisation on the host provides clock accuracy to within a few milliseconds. Both values are orders of magnitude smaller than any sensor's publication interval. Satisfiability is confirmed by architecture analysis rather than explicit timing tests. If the broker is ever moved off-host, this analysis must be repeated.

**Conflicts With:** None
**Conflict Resolution:** N/A

---

### NFR-REL-001 — Automatic Fault Recovery

**Category:** Reliability
**Priority:** Must Have
**Source:** NEED-STK-001-004, MODE-004 (Degraded/Broker), MODE-005 (Degraded/Database)
**Status:** Open

**Statement:**
The system shall recover from all software faults — container crash, broker connection loss, and database write failure — without operator intervention, and shall resume normal capture automatically when the fault condition clears.

**Rationale:**
The sole operator has full-time work and family obligations; manual recovery is impractical as the primary reliability mechanism. A system that requires operator action to recover from transient software faults cannot satisfy the 24/7 unattended operation requirement.

**Verification Method:** Demonstration
**Verification Notes:**
- Container crash: kill the logger container; verify Docker Compose restart policy restores it without operator action.
- Broker loss: stop the broker; verify the logger enters MODE-004 and reconnects automatically when broker is restored.
- Database unavailability: make the database unreachable; verify the logger logs errors, discards messages, and continues running.

**Conflicts With:** None
**Conflict Resolution:** N/A

---

### NFR-REL-002 — Recovery Time Objective

**Category:** Reliability
**Priority:** Must Have
**Source:** Operator-stated target
**Status:** Open

**Statement:**
After an unexpected container crash, the system shall resume capture within 60 seconds without operator intervention.

**Rationale:**
At the current message rate, a 60-second gap represents a negligible and accepted data loss window. The Docker Compose restart policy is the primary recovery mechanism. This target is achievable without redundancy or buffering complexity.

**Verification Method:** Test
**Verification Notes:** Kill the logger container; record the timestamp of the last successful database write before the kill and the timestamp of the first successful write after restart; verify elapsed time is ≤ 60 seconds.

**Conflicts With:** None
**Conflict Resolution:** N/A

---

### NFR-SEC-001 — Credential Non-Exposure

**Category:** Security
**Priority:** Must Have
**Source:** RISK-002, TBD-004, Constitution Principle II (Configuration Over Code)
**Status:** Open

**Statement:**
Database and broker credentials shall not be stored in any file committed to version control. Credentials shall be supplied exclusively via an external configuration file excluded from version control (currently `config.json`; planned migration to `.env`) or via environment variables.

**Rationale:**
Committed credentials create a permanent, irrecoverable exposure in repository history. This risk is already materialised as RISK-002 (config.json may have been committed to Bitbucket history). Migration to `.env`-based credential supply is tracked as TBD-004. Non-root process execution is addressed separately in FR-009.

**Verification Method:** Inspection
**Verification Notes:** Verify `.gitignore` excludes `config.json` and `.env` files. Audit the full git history of the migrated repository for any committed credential values before the Bitbucket → GitHub migration completes.

**Conflicts With:** None
**Conflict Resolution:** N/A

---

### NFR-USE-001 — Diagnostic Error Messages

**Category:** Usability
**Priority:** Must Have
**Source:** NEED-STK-001-007, FR-016
**Status:** Open

**Statement:**
When the system fails to start or encounters a configuration or connection error, it shall emit an error message that identifies: (a) the specific parameter name or field that is missing or invalid, (b) the configuration source (config file or environment variable), and (c) the value that was attempted where applicable — sufficient for the operator to diagnose and correct the problem without further investigation.

**Rationale:**
The operator is a solo developer who may return to the system after months of absence. Vague error messages ("connection failed," "configuration error") require additional diagnostic steps that consume productive time. Actionable error messages are the primary self-service diagnostic for a headless, unattended service.

**Acceptance Examples:**
- Acceptable: `Cannot connect to MQTT broker at 192.168.1.x:1883 — connection refused`
- Acceptable: `Missing required configuration field: db_password`
- Not acceptable: `Configuration error` or `Connection failed`

**Verification Method:** Test
**Verification Notes:** Provide each class of invalid input — missing required field, invalid broker address, invalid database credentials, missing config file — and verify the resulting error message satisfies all three specificity criteria.

**Conflicts With:** None
**Conflict Resolution:** N/A

---

### NFR-USE-002 — Log Entry Completeness

**Category:** Usability
**Priority:** Must Have
**Source:** NEED-STK-001-002, NEED-STK-001-006, Constitution Principle IV (Observability by Default)
**Status:** Open

**Statement:**
Every log entry emitted by the system shall include: timestamp (with UTC offset), log level, module name, function name, line number, and a human-readable message. This standard applies across all modes of operation and all log levels.

**Rationale:**
Logs are the sole operational diagnostic instrument for a headless, unattended daemon. Log entries that omit contextual fields require source code inspection to diagnose the source of an event. Complete entries allow fault diagnosis from log files alone, satisfying NEED-STK-001-002 (loud failure) and success criterion SC-CONOPS-006.

**Verification Method:** Inspection
**Verification Notes:** Exercise the system through startup, normal operation (receiving and storing messages), a simulated error condition, and shutdown. Review log output and verify every entry contains all six required fields. Automated log format validation is a future improvement candidate.

**Conflicts With:** None
**Conflict Resolution:** N/A

---

### NFR-MAIN-001 — Automated Test Coverage

**Category:** Maintainability
**Priority:** Should Have
**Source:** Constitution Section VI (Integration-Preferred Testing), TBD-002
**Status:** Open — currently not enforced; target for CI/CD pipeline gate

**Statement:**
The automated test suite shall achieve a minimum of 80% line coverage across the application codebase, as measured by `pytest-cov`. Coverage shall be enforced as a mandatory pipeline gate when the CI/CD pipeline is established.

**Rationale:**
A solo maintainer returning after months away needs confidence that changes have not introduced regressions. The 80% threshold is a minimum floor; integration tests covering real MQTT broker and database connections are the preferred coverage mechanism, per the Integration-Preferred Testing principle. The threshold does not lower for integration test presence — it shapes how coverage is achieved, not the target itself.

**Verification Method:** Test
**Verification Notes:** Run `pytest --cov` and verify reported line coverage ≥ 80%. Currently: "tests must pass" gate only. Enforcement deferred until CI/CD pipeline is established (TBD-003).

**Conflicts With:** None
**Conflict Resolution:** N/A

---

### NFR-PORT-001 — Container Deployment Target

**Category:** Portability
**Priority:** Must Have
**Source:** Constitution Principle III (Container-First Deployment)
**Status:** Open

**Statement:**
The system shall be deployable exclusively via Docker Compose on Linux (amd64/arm64). No bare-metal Python installation path is supported, tested, or documented. No other operating systems or platforms are supported.

**Rationale:**
Container-First Deployment is a constitutional principle ensuring reproducibility and environment isolation. A bare-metal path would create an untested and divergent deployment surface.

**Verification Method:** Demonstration
**Verification Notes:** Deploy the full stack via `docker compose up -d` on a Linux amd64 host. Verify the logger connects, receives a test message, and writes it to the database.

**Conflicts With:** None
**Conflict Resolution:** N/A

---

### NFR-INT-001 — Database Schema Ownership

**Category:** Interoperability
**Priority:** Must Have
**Source:** NEED-STK-001-008, Constitution Principle VII (Minimal Surface Area)
**Status:** Open

**Statement:**
The MariaDB schema used by the system shall be owned and managed exclusively by mqttlogger. All schema changes shall be applied via explicit, version-controlled migration scripts. Ad-hoc schema modifications applied directly to the database are prohibited.

**Rationale:**
Schema drift without a migration trail makes the database state non-reproducible from the repository. Any future migration to a different host or database instance requires the schema to be fully recoverable from version control alone. A schema changed without a migration script is invisible to future-maintainer (STK-002) and violates the Everything-as-Code principle.

**Verification Method:** Inspection
**Verification Notes:** Verify that the current schema is fully described by version-controlled migration scripts (or an initial schema definition file). Verify no schema changes exist in the database that are not represented in the repository.

**Conflicts With:** None
**Conflict Resolution:** N/A

---

### NFR-PERF-003 — Filtered Time-Range Query Index

**Category:** Performance
**Priority:** Must Have
**Source:** Feature 009 design decision; NEED-STK-001-010 (seasonal/renovation analysis)
**Status:** Open

**Statement:**
The `sensorreadings` table shall have a composite index on `(location, measurement_type, captured_at)` so that filtered time-range queries — the primary access pattern for dashboard panels and ad-hoc analysis — execute without a full table scan.

**Rationale:**
Dashboard queries and analysis queries filter by location and measurement type before applying a time-range predicate (e.g. "attic temperature for the last 7 days"). Without an index on these columns, the database performs a full table scan that grows linearly with history depth. At the current sensor count and publication rate, the table grows at approximately 2–4 million rows per year; a full scan over that volume produces multi-second query times unsuitable for interactive dashboard use. The composite column order `(location, measurement_type, captured_at)` matches the most selective filtering pattern. Duplicate `captured_at` values (e.g. from the CCU3 startup flood) are handled correctly by a non-unique index.

**Note:** This index does not accelerate queries that filter only on `captured_at` without a leading `location` or `measurement_type` predicate. Such queries remain as table scans; at current data volumes this is acceptable. A standalone `captured_at` index may be added in a future iteration if needed.

**Verification Method:** Inspection
**Verification Notes:** After migration, run `SHOW INDEX FROM sensorreadings` and verify an index exists with `(location, measurement_type, captured_at)` in that column order. Optionally, run `EXPLAIN SELECT ... WHERE location = ... AND measurement_type = ... AND captured_at >= ...` and verify the index is used (key column is not NULL).

**Conflicts With:** None
**Conflict Resolution:** N/A

---

### NFR-INT-002 — Read-Only Database Access for Non-Logger Consumers

**Category:** Interoperability
**Priority:** Must Have
**Source:** Feature 008 explore tasks (referenced but not formally captured); Constitution Principle I (Single-Purpose Service)
**Status:** Open

**Statement:**
All consumers of the `sensorreadings` table other than the mqttlogger service (currently: companion monitor, future dashboard tooling) shall connect to MariaDB using a dedicated database user with `SELECT`-only privileges on `sensorreadings`. No write, update, delete, or DDL privileges shall be granted to this user.

**Rationale:**
The mqttlogger service is the sole authorised writer to the database. Constitution Principle I prohibits any other component from writing to the store. Enforcing this at the database privilege level makes the constraint structural rather than merely conventional — a misconfigured or compromised consumer cannot corrupt the historical record. The companion monitor currently uses the same `MYSQL_USER` credentials as the logger; this must be corrected as part of feature 009 or feature 008.

**Verification Method:** Inspection
**Verification Notes:** Verify a read-only MariaDB user exists (e.g. `grafana_ro` or `reader`). Verify `SHOW GRANTS FOR 'reader'@'%'` shows only `SELECT` on `sensorreadings`. Verify companion monitor and dashboard services use this user, not the logger credentials.

**Conflicts With:** None
**Conflict Resolution:** N/A

---

### NFR-INT-003 — Direct DATETIME Timestamp Column

**Category:** Interoperability
**Priority:** Must Have
**Source:** Feature 009 W-003 scope; NEED-STK-001-010; OI-005 (closed)
**Status:** Open

**Statement:**
The schema shall expose a single `captured_at DATETIME NOT NULL` column as the timestamp for every reading. No downstream query shall be required to use `TIMESTAMP()`, `CONCAT()`, or any computed expression to reconstruct a usable timestamp from multiple columns.

**Rationale:**
The previous two-column form (`currentdate DATE`, `currenttime TIME`) required every consumer — dashboard panels, analysis queries, companion monitor — to compute `TIMESTAMP(currentdate, currenttime)` in every query. This made queries verbose, error-prone, and incompatible with dashboard tools that expect a native datetime column for automatic time-axis detection. A single `DATETIME` column eliminates the workaround universally. The schema cannot simultaneously satisfy this NFR and retain `currentdate`/`currenttime` as the primary timestamp representation.

**Verification Method:** Inspection
**Verification Notes:** After migration, run `DESCRIBE sensorreadings` and verify `captured_at DATETIME NOT NULL` is present and `currentdate`/`currenttime` columns are absent. Verify the companion monitor and any provisioned dashboard queries reference `captured_at` directly without a computed wrapper.

**Conflicts With:** None
**Conflict Resolution:** N/A

---

### NFR-MAIN-002 — Migration Script Atomicity

**Category:** Maintainability
**Priority:** Must Have
**Source:** RISK-027; SCN-008 failure modes
**Status:** Open

**Statement:**
The migration script shall execute as a single atomic database transaction. If any statement within the migration fails, the entire transaction shall roll back and the schema shall be left in its pre-migration state. No partial migration state — such as new columns added but old columns not yet dropped, or backfill incomplete — shall persist after a failure.

**Rationale:**
The migration runs against live production data with no backup. A partial migration leaves the schema in an indeterminate state: the logger's ORM model and the companion monitor's queries would both be broken simultaneously, with no clean rollback path. Wrapping the migration in a single `START TRANSACTION ... COMMIT` block ensures the outcome is binary — either the migration completes fully or nothing changes.

**Note:** MariaDB DDL statements (`ALTER TABLE`, `ADD COLUMN`, `DROP COLUMN`) are not transactional in the same way as DML. In practice, `ADD COLUMN` and `DROP COLUMN` on InnoDB tables in MariaDB 10.x are metadata-only operations that are effectively atomic at the storage engine level. The backfill `UPDATE` statement is fully transactional. The migration script shall be structured to run the `UPDATE` (backfill) within a transaction, and the DDL steps (ADD/DROP) shall be verified individually with row-count spot checks before proceeding.

**Verification Method:** Inspection
**Verification Notes:** Review the migration script and verify the `UPDATE` backfill is wrapped in `START TRANSACTION ... COMMIT`. Verify the script performs a spot-check `SELECT` after backfill before executing `DROP COLUMN`. Verify the script exits with a non-zero status and printed error if any statement fails.

**Conflicts With:** None
**Conflict Resolution:** N/A

---

## Conflicts and Priorities

No conflicts identified between NFRs. All ten requirements are aligned: the performance requirements support the reliability requirements; the security requirement is a deployment constraint orthogonal to operational NFRs; the usability requirements strengthen maintainability.

## Future Improvement Candidates (Not Current Requirements)

The following quality improvements were identified during elicitation and explicitly deferred:

| Item | Category | Rationale for Deferral |
|------|----------|------------------------|
| Periodic heartbeat log line confirming active capture + message count | Maintainability | No current requirement; significant observability improvement — revisit in architecture phase |
| HTTP health endpoint (e.g. for Uptime Kuma) | Maintainability | Future tooling decision; dependent on observability architecture |
| Signal-based debug toggling (SIGUSR1) | Usability | Future improvement; container restart acceptable for current context |
| Structured/JSON log format | Usability | Future improvement for machine-readable log processing |
| Unknown/unrecognised MQTT topic logging at WARN level | Interoperability | Directly addresses silent drift (RISK-013); future improvement candidate |
| Fault/gap detection mechanism | Maintainability | Addresses RISK-014/RISK-016; future architecture decision |
| MariaDB port locked to Docker internal network only | Security | Future hardening candidate; not a current requirement |
| Data export / portability utility | Portability | Future version candidate |
