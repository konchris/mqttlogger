# Assumptions: Option A — Direct Column Migration

**Date:** 2026-05-17

---

## Assumptions Register

| ID | Assumption | If False, Then | Validation Approach | Status |
| -- | ---------- | -------------- | ------------------- | ------ |
| ASM-A-001 | All `device` values in `sensorreadings` follow the four-level pattern `environment/{level2}/{level3}/{level4}` — no shorter, longer, or differently structured topics exist in the table | Backfill produces NULL or incorrect `location`/`measurement_type` for non-conforming rows; those rows must be corrected manually post-migration | IP-001 dry-run: `SELECT DISTINCT device FROM sensorreadings` and inspect all distinct topic strings before committing the migration | Unvalidated |
| ASM-A-002 | `SUBSTRING_INDEX(SUBSTRING_INDEX(device, '/', 3), '/', -2)` correctly extracts the two-level location string (e.g. `environment/indoor/attic/temperature` → `indoor/attic`) for all topic patterns in the dataset | `location` values are incorrect for some rows | IP-001 dry-run: preview SELECT showing `device`, derived `location`, derived `measurement_type` for a representative sample | Unvalidated |
| ASM-A-003 | `SUBSTRING_INDEX(device, '/', -1)` correctly extracts the measurement type (e.g. `temperature`) for all topic patterns in the dataset | `measurement_type` values are incorrect for some rows | IP-001 dry-run: same preview SELECT as ASM-A-002 | Unvalidated |
| ASM-A-004 | `TIMESTAMP(currentdate, currenttime)` produces a valid, non-NULL `captured_at` value for every row — no rows have NULL in either source column | Some rows get NULL `captured_at` after backfill, violating the NOT NULL constraint | IP-001 dry-run: `SELECT COUNT(*) FROM sensorreadings WHERE currentdate IS NULL OR currenttime IS NULL` before migration | Unvalidated |
| ASM-A-005 | The MariaDB `ALTER TABLE ... ADD COLUMN` and `DROP COLUMN` operations on the `sensorreadings` table complete within the target maintenance window (< 5 minutes) at current row count | Migration takes longer than expected, extending downtime and data gap | Acceptable risk: at current data volumes (low millions of rows), InnoDB metadata-only DDL operations are near-instant; no explicit pre-validation required | Accepted |
| ASM-A-006 | The feature/009 branch code (updated `data_model.py`, `mqtt_client.py`, `monitor.py`, `bootstrap_sensors.py`) is deployed atomically with the schema migration — no intermediate state where old code runs against new schema or vice versa | Companion monitor crashes immediately; logger may fail to write new readings | Enforced by deployment procedure in SCN-008: code and schema are applied in the same stack-down/stack-up cycle | Accepted (procedure) |

---

## Assumption Risk Summary

**Highest risk:** ASM-A-001 — if any device topic deviates from the expected four-level
structure, the backfill will silently produce wrong values. This is the primary purpose of
the IP-001 dry-run. Resolution required before production deployment.

**Second highest:** ASM-A-004 — NULL source columns would break the NOT NULL constraint on
`captured_at`, causing the migration to fail partway. Easy to check before migration; must
be resolved at IP-001.

ASM-A-005 and ASM-A-006 are accepted without explicit validation: ASM-A-005 because the
risk is low at current data volumes; ASM-A-006 because it is enforced procedurally rather
than technically.
