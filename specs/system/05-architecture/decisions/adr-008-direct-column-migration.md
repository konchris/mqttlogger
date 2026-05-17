# ADR-008: Direct Column Migration for Schema Evolution

**Date:** 2026-05-17
**Status:** Accepted
**Deciders:** Chris (sole operator)
**Feature:** 009-schema-evolution

---

## Context

The `sensorreadings` table stores timestamps as two separate columns (`currentdate DATE`,
`currenttime TIME`) because the original schema was defined before the capture timestamp
was identified as a first-class query dimension. Every downstream consumer — the companion
monitor (`monitor.py`, `bootstrap_sensors.py`) and any future dashboard tool — must
reconstruct the timestamp by calling `TIMESTAMP(currentdate, currenttime)`, a computed
expression that cannot be indexed.

Three NFRs drive the need to change this:

- **NFR-INT-003**: `captured_at` must be a native `DATETIME NOT NULL` column on the base
  table, not a computed expression in a view or query.
- **NFR-PERF-003**: A composite index `(location, measurement_type, captured_at)` must
  exist on the base table to accelerate filtered time-range queries. MariaDB cannot index
  computed columns in a view.
- **NFR-MAIN-002**: The migration must be atomic — no partial state on failure.

Additionally, the MQTT topic structure encodes `location` (segments 2–3) and
`measurement_type` (final segment) which downstream consumers need for filtering. Requiring
every query to re-derive these from the raw `device` string is error-prone and inconsistent.

The migration approach must satisfy all hard constraints from explore-summary.md:
- Preserve all existing data (no row may be deleted; `reading` and `device` must be unchanged)
- Execute within a short stack downtime window (target < 5 minutes at current row count)
- Satisfy NFR-INT-003 and NFR-PERF-003 with columns on the base table, not in a view

---

## Decision

Use a **direct column migration** (OPT-A from explore-summary): ALTER TABLE to add new
nullable columns, UPDATE to backfill all rows within a transaction, verify with a null-check
SELECT, then MODIFY COLUMN to enforce NOT NULL, CREATE INDEX, and DROP the legacy columns.

Migration sequence:

1. `ALTER TABLE sensorreadings ADD COLUMN captured_at DATETIME NULL`
2. `ALTER TABLE sensorreadings ADD COLUMN location TEXT NULL`
3. `ALTER TABLE sensorreadings ADD COLUMN measurement_type TEXT NULL`
4. `START TRANSACTION`
5. `UPDATE sensorreadings SET captured_at = TIMESTAMP(currentdate, currenttime)`
6. `UPDATE sensorreadings SET location = SUBSTRING_INDEX(SUBSTRING_INDEX(device, '/', 3), '/', -2)`
7. `UPDATE sensorreadings SET measurement_type = SUBSTRING_INDEX(device, '/', -1)`
8. `COMMIT`
9. Null-check: `SELECT COUNT(*) … WHERE captured_at IS NULL OR location IS NULL OR measurement_type IS NULL` → must return 0
10. `ALTER TABLE sensorreadings MODIFY COLUMN captured_at DATETIME NOT NULL`
11. `ALTER TABLE sensorreadings MODIFY COLUMN location TEXT NOT NULL`
12. `ALTER TABLE sensorreadings MODIFY COLUMN measurement_type TEXT NOT NULL`
13. `CREATE INDEX idx_loc_mtype_time ON sensorreadings(location, measurement_type, captured_at)`
14. `ALTER TABLE sensorreadings DROP COLUMN currentdate`
15. `ALTER TABLE sensorreadings DROP COLUMN currenttime`

The UPDATE backfill (steps 5–7) runs inside a transaction; the MODIFY COLUMN and DROP
COLUMN steps (10–15) are DDL that auto-commit in MariaDB/InnoDB and cannot be rolled back.
The null-check (step 9) acts as an explicit verification gate between the transactional
backfill and the irreversible DDL. If the null-check fails, the operator stops and
investigates before proceeding with the MODIFY/DROP steps.

---

## Consequences

### Positive

- `captured_at`, `location`, and `measurement_type` are first-class columns with full
  index support — NFR-PERF-003 and NFR-INT-003 satisfied without any downstream workarounds
- Backfill expressions are inspectable via a dry-run preview SELECT before the production
  migration runs — reduces deployment risk
- No external migration tool (Alembic, Flyway) needed — consistent with Constitution
  Principle VII (minimal surface area) and the fact that no migration tool is currently installed
- The migration script is a self-contained, version-controlled SQL file that can be reviewed,
  diffed, and understood by a returning developer

### Negative

- DDL operations (ADD/MODIFY/DROP COLUMN) on InnoDB are metadata-only for small tables but
  block concurrent writes on large tables; at current data volume (low millions) the risk is
  negligible (ASM-A-005, accepted)
- No transactional rollback is available once MODIFY COLUMN or DROP COLUMN executes —
  the null-check gate (step 9) is the only safety between backfill and irreversible DDL
- No automated migration runner — the script must be executed manually via the MariaDB
  console during the stack-down window

### Neutral

- The `device` column (full MQTT topic) is retained — `location` and `measurement_type` are
  convenience derivations. This preserves the ability to re-derive them if the derivation
  formula changes in the future.

---

## Alternatives Considered

### Alternative 1: View-Based Schema Exposure (OPT-B, eliminated pre-exploration)

**Description:** Create a database view `sensorreadings_v` that exposes `captured_at` as
`TIMESTAMP(currentdate, currenttime)`, `location` as the SUBSTRING_INDEX expression, and
`measurement_type` similarly. All consumers query the view; the base table is unchanged.

**Rejected because:**

1. Fails NFR-INT-003: The base table still contains `currentdate` and `currenttime`; the
   `TIMESTAMP()` expression still exists, just relocated from consumer queries into the view
   definition. The goal was to eliminate the computed expression, not move it.
2. Fails NFR-PERF-003: MariaDB does not support indexes on view columns. The composite index
   on `(location, measurement_type, captured_at)` cannot be created on a view.

Evidence: architecture analysis, 2026-05-17. Recorded in `03-explore/elimination-record.md`.

### Alternative 2: Add columns only; do not drop legacy columns

**Description:** Add `captured_at`, `location`, `measurement_type` but leave `currentdate`
and `currenttime` in place indefinitely. Write new code to use new columns; old columns
become dead data.

**Rejected because:** Retaining dead columns violates NFR-INT-003 (the goal is to remove the
legacy timestamp representation entirely), increases row width, and leaves a maintenance trap
for future developers who might not know which columns are authoritative.

### Alternative 3: Full table rebuild (CREATE new table, INSERT … SELECT, RENAME)

**Description:** Create a new `sensorreadings_new` table with the target schema, bulk-copy
all rows with derived values, verify counts, then RENAME TABLE.

**Rejected because:** The table rename approach requires the same stack-down window but is
more complex, more risky (a failed rename leaves the system in a split state), and provides
no additional data safety over the null-then-not-null direct migration — which already gates
on a null-check before irreversible DDL. The direct migration is simpler and sufficient.

---

## Related

- Supersedes: None
- Related requirements: FR-023, FR-024, FR-025, FR-026, FR-027
- Related NFRs: NFR-INT-003, NFR-PERF-003, NFR-MAIN-002
- Related explore option: OPT-A (active, converged)
- Related risks: RISK-026, RISK-027, RISK-029
