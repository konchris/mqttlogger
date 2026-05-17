# Feature Plan

**System:** mqttlogger
**Feature:** 009-schema-evolution (W-003: add captured_at, location, measurement_type; drop currentdate, currenttime)
**Date:** 2026-05-17
**Status:** DRAFT
**Last Updated By:** se-plan skill

---

## 1. Technical Approach

### System Decomposition

This feature touches six distinct artifacts. Four are source-code changes that travel together on
the feature branch; two are infrastructure changes applied on `sietchtabr` during deployment.

---

**Migration Script** (`db/migration-009-schema-evolution.sql`)
- Purpose: Evolve the live `sensorreadings` schema: add three columns, backfill them from
  existing data, create composite index, drop two legacy columns. Must be idempotent-safe
  (check-before-execute preferred for each step).
- Primary requirements: FR-023, FR-024, FR-025, FR-026, FR-027
- NFRs: NFR-INT-003 (columns on base table), NFR-PERF-003 (index on base table), NFR-MAIN-002 (atomicity)

---

**SQLAlchemy Model** (`mqttlogger/data_model.py`)
- Purpose: Replace `currentdate (Date)` and `currenttime (Time)` with `captured_at (DateTime NOT NULL)`;
  add `location (Text NOT NULL)` and `measurement_type (Text NOT NULL)`. The model is the authoritative
  Python-side schema definition; CI test suites use `create_all()` to build test schemas from it.
- Primary requirements: FR-028, FR-029, FR-030
- NFRs: NFR-INT-003

---

**MQTT Message Handler** (`mqttlogger/mqtt_client.py`)
- Purpose: Update `on_message()` to populate the three new fields on each `SensorReading` instead
  of the two legacy fields. `captured_at` = `datetime.now(timezone.utc)`; `location` = topic segments
  2+3 (e.g. `indoor/attic`); `measurement_type` = final topic segment (e.g. `temperature`).
- Primary requirements: FR-031, FR-032, FR-033
- NFRs: NFR-PERF-002 (sub-sensor-interval timestamp fidelity)

---

**Companion Monitor** (`companion-monitor/monitor.py`, `companion-monitor/bootstrap_sensors.py`)
- Purpose: Replace all SQL references to `currentdate`, `currenttime`, and `TIMESTAMP()` with
  `captured_at`. `query_active_sensors()` in `monitor.py` filters on `captured_at`. The bootstrap
  script filters on `DATE(captured_at)`.
- Primary requirements: FR-034, FR-035
- NFRs: NFR-INT-003 (no downstream use of TIMESTAMP() wrapper)

---

**Docker Compose Service Configuration** (`docker-compose.yml`)
- Purpose: Switch the `companion_monitor` service from write-capable logger credentials
  (`MYSQL_USER`) to a dedicated read-only MariaDB user. Satisfies the principle of least privilege
  and closes RISK-028.
- Primary requirements: FR-036
- NFRs: NFR-INT-002

---

**Read-Only MariaDB User** (applied on `sietchtabr` via MariaDB console)
- Purpose: Create a MariaDB user with `SELECT`-only privileges on `sensorreadings` for use by
  the companion monitor. This is an infrastructure step, not a source-code change — it is performed
  during deployment, not during CI.
- Primary requirements: FR-036
- NFRs: NFR-INT-002

---

**Test Suite** (`tests/`)
- Purpose: Update any test that constructs a `SensorReading` with `currentdate`/`currenttime`
  fields to use `captured_at`, `location`, and `measurement_type` instead. The CI schema is built
  from `data_model.py` via `create_all()`, so the test DB will automatically reflect the new schema
  once the model is updated. No migration script runs in CI — the test DB is always created fresh.
- NFRs: NFR-MAIN-001 (≥80% coverage gate must stay green)

---

### Key Interactions

```
  [Migration SQL] ─────────────────────────────────────────┐
                                                            ↓
  [data_model.py] ─── defines schema for ─────────────── [sensorreadings table]
                                                            ↑         ↑
  [mqtt_client.py::on_message()] ── inserts rows via ──────┘         │
                                                                      │
  [monitor.py / bootstrap_sensors.py] ── reads rows via ─────────────┘
```

The migration script and the code changes are logically independent during development but
must be applied atomically during deployment. The migration transforms the persisted schema;
the code changes transform the read/write behavior. If either is applied without the other,
the system crashes immediately.

### NFR-Driven Design Decisions

| NFR ID | Attribute | Mechanism |
| ------ | --------- | --------- |
| NFR-INT-003 | `captured_at` must be native DATETIME NOT NULL on base table | ALTER TABLE ADD COLUMN approach (OPT-A); view-based approach eliminated because it cannot satisfy this constraint |
| NFR-PERF-003 | Composite index `(location, measurement_type, captured_at)` on base table | `CREATE INDEX idx_loc_mtype_time` in migration script, after backfill completes |
| NFR-MAIN-002 | Migration atomicity — no partial state on failure | UPDATE backfill statements wrapped in `START TRANSACTION` / `COMMIT`; `DROP COLUMN` placed after null-check SELECT |
| NFR-INT-002 | Read-only access for non-logger consumers | Dedicated MariaDB user with `GRANT SELECT` only; companion_monitor `docker-compose.yml` env updated to reference that user |
| NFR-MAIN-001 | Test coverage ≥ 80% | Test suite updated alongside model + handler; CI `create_all()` uses new schema automatically |

### Technology Constraints

| Constraint | Technology/Platform | Source |
| ---------- | ------------------- | ------ |
| Database | MariaDB (InnoDB) | Constitution — only supported DB |
| ORM | SQLAlchemy | Constitution — only sanctioned ORM |
| Language | Python 3.12 | Feature 007 upgrade (current runtime) |
| Deployment | Docker Compose on Linux amd64 | Constitution Principle III |
| Migration style | Ad-hoc SQL script (not Alembic) | Constitution Principle VII (minimal surface area); Alembic is not installed |
| Timestamp semantics | UTC (`datetime.now(timezone.utc)`) | FR-031 (timezone-explicit per quality gate finding); consistent with MariaDB `NOW()` behavior |

---

## 2. Open Technical Questions

| ID | Question | Affects | Options | Resolution Method |
| -- | -------- | ------- | ------- | ----------------- |
| OTQ-001 | Python topic parsing: `split('/')` vs `re.split()` vs string slicing? | FR-032, FR-033 | `topic.split('/')[1:3]` joined with `/` is simplest; regex adds no value for a fixed delimiter | Use `split('/')`: `location = '/'.join(topic.split('/')[1:3])`, `measurement_type = topic.split('/')[-1]` — no external dependency, readable, consistent with SQL derivation |
| OTQ-002 | Migration script safety: should DROP COLUMN be inside the transaction or after it? | FR-027, NFR-MAIN-002 | (A) Inside transaction — DDL in MariaDB/InnoDB is NOT transactional; ALTER TABLE auto-commits. (B) After transaction — correct: UPDATE backfill in transaction, then DESCRIBE + SELECT null-check, then DROP COLUMN separately | Use approach (B): UPDATE inside transaction; null-check SELECT between transaction and DROP; DDL (ALTER TABLE DROP COLUMN) executes as a separate auto-commit operation after verification |
| OTQ-003 | Should the migration use `DEFAULT NULL` temporarily then `ALTER TABLE MODIFY COLUMN ... NOT NULL`? | FR-023, FR-024, FR-025 | MariaDB allows `ADD COLUMN ... NOT NULL DEFAULT ''` then UPDATE then `MODIFY COLUMN ... NOT NULL DROP DEFAULT`. But for TEXT columns, an empty default may be worse than a temporary NULL. Simplest: `ADD COLUMN ... NOT NULL DEFAULT 'PENDING_BACKFILL'` for TEXT, then UPDATE, then `MODIFY ... NOT NULL`. For DATETIME: `ADD COLUMN ... NULL` then UPDATE then `MODIFY ... NOT NULL`. | Use the NULL-then-NOT-NULL pattern for all three columns: `ADD COLUMN ... NULL`, UPDATE backfill, verify null count = 0, then `MODIFY COLUMN ... NOT NULL` — this is the cleanest and avoids placeholder sentinel values in TEXT columns |

---

## 3. Implementation Sequence

### Phase 1 — Pre-Migration Verification (IP-001 Dry-Run)

Run IP-001 tasks on `sietchtabr` against the live database **before writing any production
migration SQL**. This resolves assumptions ASM-A-001 through ASM-A-004.

Tasks to run on sietchtabr:
- TASK-A-001: `SELECT DISTINCT device FROM sensorreadings ORDER BY device` — confirm all are 4-level topics
- TASK-A-002: Preview SELECT showing derived `location`, `measurement_type`, `captured_at` for 50 rows
- TASK-A-003: `SELECT COUNT(*) FROM sensorreadings WHERE currentdate IS NULL OR currenttime IS NULL` → must be 0

These tasks have no production impact (read-only). They must complete before the migration SQL is
finalised. If TASK-A-001 reveals non-conforming topics, the migration SQL must handle them explicitly.

Requirements addressed: ASM-A-001 (resolved), ASM-A-002 (resolved), ASM-A-003 (resolved), ASM-A-004 (resolved)

### Phase 2 — Migration Script

Write `db/migration-009-schema-evolution.sql`. Structure:

1. Add `captured_at DATETIME NULL` (temporary nullable)
2. Add `location TEXT NULL` (temporary nullable)
3. Add `measurement_type TEXT NULL` (temporary nullable)
4. `START TRANSACTION`
5. `UPDATE sensorreadings SET captured_at = TIMESTAMP(currentdate, currenttime)`
6. `UPDATE sensorreadings SET location = SUBSTRING_INDEX(SUBSTRING_INDEX(device, '/', 3), '/', -2)`
7. `UPDATE sensorreadings SET measurement_type = SUBSTRING_INDEX(device, '/', -1)`
8. `COMMIT`
9. Null-check: `SELECT COUNT(*) FROM sensorreadings WHERE captured_at IS NULL OR location IS NULL OR measurement_type IS NULL` → must be 0
10. `ALTER TABLE sensorreadings MODIFY COLUMN captured_at DATETIME NOT NULL`
11. `ALTER TABLE sensorreadings MODIFY COLUMN location TEXT NOT NULL`
12. `ALTER TABLE sensorreadings MODIFY COLUMN measurement_type TEXT NOT NULL`
13. `CREATE INDEX idx_loc_mtype_time ON sensorreadings(location, measurement_type, captured_at)`
14. `ALTER TABLE sensorreadings DROP COLUMN currentdate`
15. `ALTER TABLE sensorreadings DROP COLUMN currenttime`

Requirements addressed: FR-023, FR-024, FR-025, FR-026, FR-027

### Phase 3 — Source Code Changes

Update all four source-code artifacts in a single commit (or coordinated commits on the feature branch):

1. `mqttlogger/data_model.py` — remove `currentdate`, `currenttime`; add `captured_at`, `location`, `measurement_type`
2. `mqttlogger/mqtt_client.py` — update `on_message()` to populate new fields with `datetime.now(timezone.utc)`, `location`, `measurement_type`; add `from datetime import timezone` import
3. `companion-monitor/monitor.py` — replace `TIMESTAMP(currentdate, currenttime)` with `captured_at`
4. `companion-monitor/bootstrap_sensors.py` — replace `currentdate` with `DATE(captured_at)`
5. `tests/` — update any test constructing `SensorReading` with old field names; add integration tests for FR-031, FR-032, FR-033

Requirements addressed: FR-028, FR-029, FR-030, FR-031, FR-032, FR-033, FR-034, FR-035

### Phase 4 — Infrastructure Changes

Apply on `sietchtabr` before deployment:

1. Create read-only MariaDB user (inside running `mariadb` container):
   ```sql
   CREATE USER 'monitor_ro'@'%' IDENTIFIED BY '<password>';
   GRANT SELECT ON mqttlogger.sensorreadings TO 'monitor_ro'@'%';
   FLUSH PRIVILEGES;
   ```
2. Add `MONITOR_DB_USER` and `MONITOR_DB_PASSWORD` to `.env` or equivalent configuration
3. Update `docker-compose.yml` to use `MONITOR_DB_USER` / `MONITOR_DB_PASSWORD` for `companion_monitor`

Requirements addressed: FR-036

### Phase 5 — Deployment (SCN-008)

Apply atomically on `sietchtabr` per the SCN-008 procedure:

1. Pre-stage migration SQL (`db/migration-009-schema-evolution.sql`) on sietchtabr
2. `docker compose down` (stack stops; data gap begins)
3. Execute migration SQL inside the mariadb container or directly against MariaDB
4. Verify null-checks from Step 9 above pass before proceeding
5. `docker compose up -d` (new image with updated code)
6. Verify companion monitor healthy (`docker compose logs companion_monitor`)
7. Spot-check a new reading in the DB: confirm `captured_at`, `location`, `measurement_type` populated

Requirements addressed: TASK-A-004 (monitor query review completed), SCN-008

### Minimum Viable Implementation

All 14 requirements in Section 5 of the requirements register are Must Have. The MVI is therefore
the complete implementation: migration SQL + model update + handler update + monitor update + read-only
user + docker-compose update. No subset satisfies all Must Have requirements.

### External Dependencies and Schedule Constraints

| Dependency | Type | Affects | Notes |
| ---------- | ---- | ------- | ----- |
| IP-001 dry-run results | Data validation (live DB) | FR-024, FR-025, Migration SQL correctness | Must run TASK-A-001..A-003 against sietchtabr before finalising migration SQL; read-only, no downtime |
| Stack downtime window | Operational | SCN-008 deployment | Must bring stack down to run migration; estimated <5 min (RISK-027 accepted); plan during a period of low sensor activity |
| MONITOR_DB_USER credentials | Configuration | FR-036 | Must be set in `.env` on sietchtabr before `docker compose up` |

---

## 4. Requirements Coverage Check

| Req ID | Addressed By | Phase | Notes |
|--------|-------------|-------|-------|
| FR-023 | Migration script | 2 | ADD + backfill captured_at |
| FR-024 | Migration script | 2 | ADD + backfill location |
| FR-025 | Migration script | 2 | ADD + backfill measurement_type |
| FR-026 | Migration script | 2 | CREATE INDEX after backfill |
| FR-027 | Migration script | 2 | DROP COLUMN after null-check |
| FR-028 | data_model.py | 3 | Remove Date/Time columns; add DateTime NOT NULL |
| FR-029 | data_model.py | 3 | Add Text NOT NULL location |
| FR-030 | data_model.py | 3 | Add Text NOT NULL measurement_type |
| FR-031 | mqtt_client.py | 3 | captured_at = datetime.now(timezone.utc) |
| FR-032 | mqtt_client.py | 3 | location from topic.split('/')[1:3] |
| FR-033 | mqtt_client.py | 3 | measurement_type from topic.split('/')[-1] |
| FR-034 | monitor.py | 3 | Replace TIMESTAMP() with captured_at |
| FR-035 | bootstrap_sensors.py | 3 | Replace currentdate with DATE(captured_at) |
| FR-036 | docker-compose.yml + MariaDB user | 4 | Read-only credentials for companion_monitor |

**Uncovered requirements:** None — all 14 requirements are addressed.

---

## 5. Risks Introduced by This Plan

| Risk ID | Description | Mitigation in Plan |
| ------- | ----------- | ------------------ |
| RISK-026 | Code and schema must be deployed atomically | SCN-008 procedure: stack down → migrate → stack up; both code and SQL staged before window |
| RISK-027 | No backup before migration | Accepted; IP-001 dry-run validates derivation; migration data gap bounded to stack-down window |
| RISK-028 | Companion monitor currently uses write-capable credentials | Resolved in Phase 4 by creating read-only user and updating docker-compose.yml |
| RISK-029 | ASM-A-001: topic pattern assumption unvalidated | Resolved by Phase 1 (TASK-A-001) before migration SQL is finalised |
| OTQ-002 | DDL not transactional in MariaDB/InnoDB | Resolved by placing UPDATE backfill in transaction; DROP COLUMN after verified null-check, not inside transaction |

Full risk entries in `specs/system/10-risk/risk-register.md`.
