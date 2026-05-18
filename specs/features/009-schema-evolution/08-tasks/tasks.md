# Tasks: Feature 009 — Schema Evolution (W-003)

**System:** mqttlogger
**Feature:** 009-schema-evolution (W-003: add captured_at, location, measurement_type; drop currentdate, currenttime)
**Date:** 2026-05-17
**Status:** ACTIVE
**Last Updated By:** speckit-tasks (SE-adapted)

---

## Requirement Groups

This feature has no user stories (SE feature). Tasks are grouped by the requirement clusters
they satisfy. The groups are ordered by implementation dependency.

| Group | Requirements | Focus |
| ----- | ------------ | ----- |
| G1 | ASM-A-001..A-004 | Pre-migration dry-run verification on sietchtabr |
| G2 | FR-023..FR-027 | Migration SQL script |
| G3 | FR-028..FR-030 | SQLAlchemy model update |
| G4 | FR-031..FR-033 | MQTT message handler update |
| G5 | FR-034..FR-035 | Companion monitor query update |
| G6 | FR-036 | Docker Compose + read-only MariaDB user |
| G7 | NFR-MAIN-001 | Test suite update (coverage gate) |
| G8 | All | RTM + deployment |

---

## Phase 1 — Pre-Migration Verification (IP-001 Dry-Run)

**Goal:** Resolve assumptions ASM-A-001..A-004 against the live database on sietchtabr before
writing production migration SQL. All tasks are read-only (no schema changes). Must complete
before Phase 2 begins.

**Independent pass criterion:** All three queries return expected results; no anomalous topics
found; null count is zero.

- [x] T001 Run `SELECT DISTINCT device FROM sensorreadings ORDER BY device` on sietchtabr — confirm every device is a 4-level topic matching `environment/L2/L3/L4` pattern (resolves ASM-A-001)
- [x] T002 [P] Run preview SELECT on sietchtabr showing derived `location`, `measurement_type`, `captured_at` for 50 rows: `SELECT device, SUBSTRING_INDEX(SUBSTRING_INDEX(device,'/',3),'/',-2) AS location, SUBSTRING_INDEX(device,'/',-1) AS measurement_type, TIMESTAMP(currentdate,currenttime) AS captured_at FROM sensorreadings LIMIT 50` — verify derivation is correct for all observed topics (resolves ASM-A-002, ASM-A-003)
- [x] T003 [P] Run `SELECT COUNT(*) FROM sensorreadings WHERE currentdate IS NULL OR currenttime IS NULL` on sietchtabr — confirm result is 0 (resolves ASM-A-004)

---

## Phase 2 — Migration SQL Script (G2: FR-023..FR-027)

**Goal:** A complete, correct migration script that can be staged on sietchtabr and executed
during the SCN-008 deployment window. Prerequisite: Phase 1 all-pass.

**Independent pass criterion:** Script can be reviewed end-to-end; all 15 steps present in
correct order; null-check gate separates transactional backfill from DDL; `DROP COLUMN`
statements are last.

- [x] T004 [G2] Create `db/migration-009-schema-evolution.sql` with the full 15-step migration sequence: (1) ADD captured_at DATETIME NULL; (2) ADD location TEXT NULL; (3) ADD measurement_type TEXT NULL; (4) START TRANSACTION; (5) UPDATE SET captured_at = TIMESTAMP(currentdate, currenttime); (6) UPDATE SET location = SUBSTRING_INDEX(SUBSTRING_INDEX(device,'/',3),'/',-2); (7) UPDATE SET measurement_type = SUBSTRING_INDEX(device,'/',-1); (8) COMMIT; (9) SELECT COUNT(*) null-check gate; (10) MODIFY captured_at DATETIME NOT NULL; (11) MODIFY location TEXT NOT NULL; (12) MODIFY measurement_type TEXT NOT NULL; (13) CREATE INDEX idx_loc_mtype_time ON sensorreadings(location, measurement_type, captured_at); (14) DROP COLUMN currentdate; (15) DROP COLUMN currenttime — satisfies FR-023, FR-024, FR-025, FR-026, FR-027

---

## Phase 3 — SQLAlchemy Model (G3: FR-028..FR-030)

**Goal:** `data_model.py` reflects the new schema. CI `create_all()` will build test
databases from this model — once updated, the test schema automatically matches production.

**Independent pass criterion:** Inspection of `data_model.py` shows `captured_at Column(DateTime, nullable=False)`, `location Column(Text, nullable=False)`, `measurement_type Column(Text, nullable=False)`; no `currentdate` or `currenttime` columns present.

- [x] T005 [G3] Update `mqttlogger/data_model.py`: remove `Column(Date)` for `currentdate` and `Column(Time)` for `currenttime`; add `Column(DateTime, nullable=False)` for `captured_at`, `Column(Text, nullable=False)` for `location`, `Column(Text, nullable=False)` for `measurement_type` — satisfies FR-028, FR-029, FR-030

---

## Phase 4 — MQTT Message Handler (G4: FR-031..FR-033)

**Goal:** `on_message()` populates the three new fields on every captured `SensorReading`.
Prerequisite: T005 (model must define the new columns before handler can reference them).

**Independent pass criterion:** Integration test publishes a known topic; inserted row has
`captured_at` within 5 s of publish time, `location == 'indoor/attic'`, `measurement_type == 'temperature'`.

- [x] T006 [G4] Update `mqttlogger/mqtt_client.py`: add `from datetime import timezone` import; in `on_message()`, set `captured_at=datetime.now(timezone.utc)`, `location='/'.join(msg.topic.split('/')[1:3])`, `measurement_type=msg.topic.split('/')[-1]`; remove assignments to `currentdate` and `currenttime` — satisfies FR-031, FR-032, FR-033

---

## Phase 5 — Companion Monitor Queries (G5: FR-034..FR-035)

**Goal:** Companion monitor no longer references legacy timestamp columns. Both files can
be updated in parallel since they are independent.
Prerequisite: T005 (conceptual — must not reference removed columns; actual runtime
dependency is the migration script, not the model file).

**Independent pass criterion:** Inspection of `monitor.py` and `bootstrap_sensors.py` shows
no reference to `currentdate`, `currenttime`, or `TIMESTAMP()`; `captured_at` used in all SQL WHERE clauses.

- [x] T007 [G5] Update `companion-monitor/monitor.py` `query_active_sensors()`: replace `TIMESTAMP(currentdate, currenttime) >= DATE_SUB(NOW(), INTERVAL %s MINUTE)` with `captured_at >= DATE_SUB(NOW(), INTERVAL %s MINUTE)` — satisfies FR-034
- [x] T008 [P] [G5] Update `companion-monitor/bootstrap_sensors.py`: replace `currentdate >= %s` with `DATE(captured_at) >= %s` in the lookback query — satisfies FR-035

---

## Phase 6 — Docker Compose + Read-Only Credentials (G6: FR-036)

**Goal:** `companion_monitor` service uses dedicated read-only database credentials.
The docker-compose.yml change and `.env.example` update can proceed in parallel with
Phase 5.

**Independent pass criterion:** Inspection of `docker-compose.yml` shows `companion_monitor`
references `MONITOR_DB_USER` / `MONITOR_DB_PASSWORD` (not the logger's credentials);
`.env.example` documents both variables.

- [x] T009 [G6] Update `docker-compose.yml` `companion_monitor` service: replace `DB_USER: ${MYSQL_USER}` / `DB_PASSWORD: ${MYSQL_PASSWORD}` with `DB_USER: ${MONITOR_DB_USER}` / `DB_PASSWORD: ${MONITOR_DB_PASSWORD}` environment variables — satisfies FR-036
- [x] T010 [P] [G6] Update `.env.example`: add `MONITOR_DB_USER=monitor_ro` and `MONITOR_DB_PASSWORD=` placeholder entries with explanatory comment referencing ADR-009

---

## Phase 7 — Test Suite Update (NFR-MAIN-001 coverage gate)

**Goal:** CI passes at ≥80% coverage after model and handler are updated.
`test_data_model.py` currently constructs `SensorReading` with `currentdate`/`currenttime`
fields — these will cause test failures once T005 merges. Must update tests before CI gate
is expected to pass.
Prerequisite: T005, T006.

**Independent pass criterion:** `pytest` passes with coverage ≥80%; no test references
`currentdate` or `currenttime`; integration tests verify FR-031, FR-032, FR-033 behaviour.

- [x] T011 [G7] Update `tests/mqttlogger/test_data_model.py`: replace all `SensorReading(currentdate=..., currenttime=...)` constructor calls with `SensorReading(captured_at=..., location=..., measurement_type=...)` using appropriate test values — required for CI green after T005
- [x] T012 [G7] Add integration tests to `tests/mqttlogger/test_mqtt_client.py` for FR-031, FR-032, FR-033: publish a known topic `environment/indoor/attic/temperature` with payload `{"val": 21.5}`; assert inserted row has `captured_at` within 5 s of publish, `location == 'indoor/attic'`, `measurement_type == 'temperature'`

---

## Phase 8 — RTM Update

**Goal:** RTM task reference column populated for all FR-023..FR-036 before Phase 4 gate.

- [x] T013 Update `specs/system/rtm.md` task reference column for FR-023..FR-036 with task IDs from this file (T004..T012)

---

## Phase 9 — Infrastructure + Deployment (SCN-008)

**Goal:** Deploy feature on sietchtabr per SCN-008 procedure. Prerequisite: all Phase 1–8
tasks complete and CI green on feature branch.

**Pass criterion:** Post-migration spot-check shows `captured_at`, `location`, `measurement_type`
populated on new rows; `DESCRIBE sensorreadings` shows no `currentdate` or `currenttime`;
`SHOW INDEX` shows `idx_loc_mtype_time`; companion_monitor logs show successful poll cycle.

- [x] T014 On sietchtabr: create read-only MariaDB user inside running `mariadb` container: `CREATE USER 'monitor_ro'@'%' IDENTIFIED BY '<password>'; GRANT SELECT ON mqttlogger.sensorreadings TO 'monitor_ro'@'%'; FLUSH PRIVILEGES;` — infrastructure prerequisite for FR-036
- [x] T015 On sietchtabr: stage `db/migration-009-schema-evolution.sql`; execute SCN-008 migration procedure: `docker compose down` → run migration SQL inside mariadb container → verify null-check returns 0 → `docker compose up -d` — satisfies SCN-008
- [x] T016 On sietchtabr: post-migration verification: `DESCRIBE sensorreadings` (no currentdate/currenttime); `SHOW INDEX FROM sensorreadings` (idx_loc_mtype_time present); spot-check new rows for captured_at, location, measurement_type; `docker compose logs companion_monitor` shows successful poll cycle

---

## Dependencies

```
T001, T002, T003 (Phase 1 — must all pass before T004)
       ↓
      T004 (Phase 2 — migration SQL)
       ↓
      T005 (Phase 3 — model)
       ↓
   T006    T007    T008    T009    T010
(handler)(mon.py)(boot.py)(dc.yml)(.env)
       ↓    ↓
   T011, T012 (Phase 7 — tests)
       ↓
      T013 (RTM update)
       ↓
   T014, T015, T016 (Phase 9 — deployment)
```

T002 ∥ T003 (independent queries, different SQL)
T007 ∥ T008 (different files, no shared state)
T009 ∥ T010 (different files, no shared state)
T014 → T015 → T016 (strict sequence — infrastructure before deployment before verification)

---

## Requirements Coverage

| Req ID | Addressed By | Task(s) | Phase |
| ------ | ------------ | ------- | ----- |
| FR-023 | Migration SQL | T004 | 2 |
| FR-024 | Migration SQL | T004 | 2 |
| FR-025 | Migration SQL | T004 | 2 |
| FR-026 | Migration SQL | T004 | 2 |
| FR-027 | Migration SQL | T004 | 2 |
| FR-028 | data_model.py | T005 | 3 |
| FR-029 | data_model.py | T005 | 3 |
| FR-030 | data_model.py | T005 | 3 |
| FR-031 | mqtt_client.py | T006, T012 | 4, 7 |
| FR-032 | mqtt_client.py | T006, T012 | 4, 7 |
| FR-033 | mqtt_client.py | T006, T012 | 4, 7 |
| FR-034 | monitor.py | T007 | 5 |
| FR-035 | bootstrap_sensors.py | T008 | 5 |
| FR-036 | docker-compose.yml + MariaDB user | T009, T014 | 6, 9 |

**Coverage: 14/14 requirements addressed. 0 gaps.**

---

## Parallel Execution Opportunities

- **T002 ∥ T003** — Two independent read-only queries on sietchtabr; run in separate DB sessions simultaneously
- **T007 ∥ T008** — `monitor.py` and `bootstrap_sensors.py` are independent files; edit in parallel
- **T009 ∥ T010** — `docker-compose.yml` and `.env.example` are independent files; edit in parallel
- **T011 ∥ T012** — Test files are independent; write in parallel after T005 and T006 complete

---

## Implementation Strategy

**MVP scope:** All 14 requirements are Must Have — there is no partial MVP. The minimum
viable implementation is the complete implementation.

**Correct order for feature branch commits:**
1. T004 — migration SQL (review artifact; no runtime dependency)
2. T005, T006 — model + handler (commit together; runtime-consistent pair)
3. T007, T008 — companion monitor (independent of model change at source level)
4. T009, T010 — docker-compose + env.example
5. T011, T012 — tests (must follow T005+T006 so test schema is correct)
6. T013 — RTM update (admin artifact)

**sietchtabr deployment order (Phase 9):** T014 → T015 → T016 (strictly sequential; no
parallelism; stack must be down during T015).
