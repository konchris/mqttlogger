# Assumptions: Option A — Grafana OSS

**Date:** 2026-05-16

---

## Assumptions Register

| ID | Assumption | If False, Then | Validation Approach | Status |
| -- | ---------- | -------------- | ------------------- | ------ |
| ASM-A-001 | Grafana's MySQL datasource is compatible with the MariaDB version running on sietchtabr (10.11) | Datasource connection fails; option eliminated or Grafana version must be pinned | TASK-A-001: connect datasource and verify query succeeds | Unvalidated |
| ASM-A-002 | A 7-day query against sensorreadings returns results within 10 seconds without additional indexing | NFR-PERF-003 fails; additional index must be added to sensorreadings before feature 008 can close | TASK-A-002: time a 7-day panel render; check EXPLAIN output | Unvalidated |
| ASM-A-003 | Grafana provisioning (mounted YAML + JSON) loads completely on first container start with no manual steps | NFR-USE-003 fails; provisioning configuration must be debugged before proceeding | TASK-A-003 + TASK-A-004: write provisioning files and verify via volume wipe | Unvalidated |
| ASM-A-004 | The initial dashboard JSON can be authored without excessive effort (via UI export or hand-written) | Dashboard authoring becomes a significant time cost, undermining the speed objective | TASK-A-002: build one panel in UI and assess effort | Unvalidated |

---

## Assumption Risk Summary

- **ASM-A-001** is the gating assumption — if the datasource is incompatible, OPT-A fails immediately. Resolve at TASK-A-001 (first task).
- **ASM-A-002** is the performance risk — most likely to require remediation (adding a DB index). Resolve at TASK-A-002.
- **ASM-A-003** is the NFR-USE-003 risk — Grafana's provisioning is well-documented but requires correct file structure. Resolve at TASK-A-003/A-004.
- **ASM-A-004** is a usability/effort risk — acceptable effort is subjective; resolve at TASK-A-002 based on operator experience.
