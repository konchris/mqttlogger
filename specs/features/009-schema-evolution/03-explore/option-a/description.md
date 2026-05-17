# Option A: Direct Column Migration

**Status:** Active
**Date Created:** 2026-05-17
**Last Updated:** 2026-05-17

---

## Core Approach

The migration adds three new columns to the existing `sensorreadings` table (`captured_at
DATETIME`, `location TEXT`, `measurement_type TEXT`), backfills all three from the values
already present in `device`, `currentdate`, and `currenttime`, then drops the two old
timestamp columns. A composite index on `(location, measurement_type, captured_at)` is
added as part of the same migration. The logger's SQLAlchemy model and the companion
monitor's SQL queries are updated in the same deployment to use the new column names.

The migration runs against the live production table on `sietchtabr` while the Docker
Compose stack is fully stopped. There is no backup; rollback is a revert migration that
restores `currentdate` and `currenttime` from `captured_at`. The expected downtime is
under 5 minutes.

## Key Characteristics

- Single atomic maintenance operation — stack down, migrate, stack up
- Backfill derives `captured_at` from `TIMESTAMP(currentdate, currenttime)` for all
  existing rows
- `location` is derived from the MQTT topic as the two middle levels
  (e.g. `environment/indoor/attic/temperature` → `indoor/attic`)
- `measurement_type` is derived as the final topic level
  (e.g. `environment/indoor/attic/temperature` → `temperature`)
- `device` is retained unchanged as the canonical full MQTT topic
- `currentdate` and `currenttime` are dropped after backfill is verified
- Composite index `(location, measurement_type, captured_at)` added in the same statement

## NFR Satisfaction Assessment

| NFR ID | Priority | Assessment | Confidence |
| ------ | -------- | ---------- | ---------- |
| NFR-PERF-001 | Must Have | Not affected — logger write path unchanged | High |
| NFR-PERF-002 | Must Have | Not affected — `captured_at` records same timestamp as before | High |
| NFR-PERF-003 | Must Have | Satisfied — composite index added during migration | High |
| NFR-REL-001 | Must Have | Not affected — container restart behaviour unchanged | High |
| NFR-REL-002 | Must Have | Not affected — recovery time characteristics unchanged | High |
| NFR-SEC-001 | Must Have | Not affected — credential handling unchanged | High |
| NFR-USE-001 | Must Have | Not affected — error message behaviour unchanged | High |
| NFR-USE-002 | Must Have | Not affected — log format unchanged | High |
| NFR-MAIN-001 | Should Have | Requires updated tests for new column names in model | Medium — tests need updating |
| NFR-MAIN-002 | Must Have | Satisfied if migration script wraps backfill UPDATE in transaction | Medium — depends on script quality |
| NFR-PORT-001 | Must Have | Not affected — Docker Compose deployment unchanged | High |
| NFR-INT-001 | Must Have | Satisfied — migration is the version-controlled schema change artifact | High |
| NFR-INT-002 | Must Have | Requires read-only DB user to be created as part of deployment | Medium — operational action needed |
| NFR-INT-003 | Must Have | Satisfied — `captured_at DATETIME NOT NULL` on base table; old columns dropped | High |

## Potential Advantages

- Clean outcome: schema exactly matches what downstream consumers need; no computed
  expressions anywhere in the stack after deployment
- Simple mental model: one migration script, one maintenance window, one state change
- NFR-INT-003 and NFR-PERF-003 are fully satisfied at the storage layer, not papered over
  by a view or application-level workaround
- Enables fair re-evaluation of dashboard tool options (feature 008) on equal terms with
  a potential homegrown dashboard

## Potential Weaknesses

- No backup — a bug in the backfill derivation for any topic pattern means correcting rows
  manually after migration; mitigation is the IP-001 dry-run
- Companion monitor and logger code must be updated atomically with the schema — deploying
  the wrong code version after migration breaks both services immediately (RISK-026)
- Topic structure assumption: derivation logic assumes all `device` values follow the
  `environment/{level2}/{level3}/{level4}` pattern; any non-conforming topic will produce
  incorrect `location`/`measurement_type` values — must be verified by IP-001 dry-run
