# Exploration Tasks: Option A — Direct Column Migration

**Target Integration Point:** IP-001
**Date:** 2026-05-17

---

## Tasks

| Task ID | Description | Type | Owner | Effort | Target IP | Output |
| ------- | ----------- | ---- | ----- | ------ | --------- | ------ |
| TASK-A-001 | Run `SELECT DISTINCT device FROM sensorreadings ORDER BY device` against the live database on `sietchtabr`; inspect every distinct topic string to confirm all follow the `environment/{level2}/{level3}/{level4}` four-level pattern | Research | Chris | 15 min | IP-001 | Confirmed topic inventory; any non-conforming patterns identified and handled in migration SQL |
| TASK-A-002 | Run a dry-run preview SELECT: `SELECT device, SUBSTRING_INDEX(SUBSTRING_INDEX(device, '/', 3), '/', -2) AS location, SUBSTRING_INDEX(device, '/', -1) AS measurement_type, TIMESTAMP(currentdate, currenttime) AS captured_at FROM sensorreadings LIMIT 50` — inspect results for correctness across a representative sample of device topics (expected: `environment/indoor/attic/temperature` → `location=indoor/attic`, `measurement_type=temperature`) | Analysis | Chris | 15 min | IP-001 | Confirmed backfill derivation is correct for all observed topic patterns |
| TASK-A-003 | Run `SELECT COUNT(*) FROM sensorreadings WHERE currentdate IS NULL OR currenttime IS NULL` to confirm zero NULL rows in source columns before migration | Analysis | Chris | 5 min | IP-001 | Confirmed no NULL source rows; NOT NULL constraint on `captured_at` will not be violated |
| TASK-A-004 | Review updated `monitor.py` and `bootstrap_sensors.py` queries against the new column names; verify no reference to `currentdate`, `currenttime`, or `TIMESTAMP()` remains | Inspection | Chris | 15 min | IP-001 | Confirmed companion monitor code is compatible with new schema |

---

## Evidence Collection

At IP-001, record for OPT-A:

- ASM-A-001 resolved: all distinct `device` values confirmed as four-level topics (yes/no; list any exceptions)
- ASM-A-002/ASM-A-003 resolved: dry-run SELECT output reviewed; `location` and `measurement_type` correct for sample (yes/no; note any anomalies)
- ASM-A-004 resolved: NULL count in source columns = 0 (yes/no)
- TASK-A-004 complete: companion monitor queries updated and reviewed (yes/no)
- IP-001 overall: proceed to production deployment (pass/fail)
