# Exploration Tasks: Option B — Metabase

**Target Integration Point:** IP-001
**Date:** 2026-05-16

---

## Tasks

| Task ID | Description | Type | Owner | Effort | Target IP | Output |
| ------- | ----------- | ---- | ----- | ------ | --------- | ------ |
| TASK-B-001 | Add Metabase service to docker-compose.yml; connect MySQL datasource to MariaDB with read-only user; measure time from container start to UI available | Prototype | Chris | 1–2 h | IP-001 | Running Metabase container; startup time measurement; pass/fail for NFR-REL-003 |
| TASK-B-002 | Build one time-series question in Metabase showing attic temperature for the last 7 days; record render time; assess chart type adequacy for sensor data | Test | Chris | 1 h | IP-001 | Render time measurement; pass/fail for NFR-PERF-003; subjective experience assessment |
| TASK-B-003 | Investigate provisioning-as-code paths: (a) Metabase environment-variable seeding; (b) API-based dashboard export/import script; (c) external metadata DB approach. Test at least one path for full restore after volume wipe | Research | Chris | 2–3 h | IP-001 | Pass/fail for NFR-USE-003; documented restore procedure or confirmed inability |
| TASK-B-004 | Run both options for 24 hours; compare overall experience for SCN-008 (browse historical sensor data by room and time range) | Demonstration | Chris | 24 h | IP-001 | Operator experience rating 1–5 for each option |

---

## Evidence Collection

At IP-001, record for OPT-B:
- ASM-B-001: startup time to UI available (seconds); pass if ≤120 s
- ASM-B-002: datasource connected? (yes/no)
- ASM-B-003: provisioning restored after volume wipe without manual steps? (yes/no); pass if no manual steps required
- ASM-B-004: subjective time-series chart adequacy for sensor data (low/medium/high)
- Overall experience rating for SCN-008: 1–5
