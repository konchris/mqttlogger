# Exploration Tasks: Option A — Grafana OSS

**Target Integration Point:** IP-001
**Date:** 2026-05-16

---

## Tasks

| Task ID | Description | Type | Owner | Effort | Target IP | Output |
| ------- | ----------- | ---- | ----- | ------ | --------- | ------ |
| TASK-A-001 | Add Grafana OSS service to docker-compose.yml; configure MySQL datasource pointing at MariaDB with read-only user; verify datasource health check passes | Prototype | Chris | 1–2 h | IP-001 | Running Grafana container with working MariaDB datasource |
| TASK-A-002 | Build one panel in Grafana UI showing attic temperature for the last 7 days; record render time; note panel authoring effort | Test | Chris | 1 h | IP-001 | Render time measurement; pass/fail for NFR-PERF-003; subjective effort assessment |
| TASK-A-003 | Export the panel/dashboard as JSON; write datasource provisioning YAML; commit both to the repo under a provisioning directory | Research | Chris | 1 h | IP-001 | Version-controlled provisioning files |
| TASK-A-004 | Delete the Grafana Docker volume; run `docker compose up -d`; verify datasource and dashboard appear without any manual UI steps | Test | Chris | 30 min | IP-001 | Pass/fail for NFR-USE-003; confirms full provisioning-as-code recovery |

---

## Evidence Collection

At IP-001, record for OPT-A:
- ASM-A-001: datasource connected? (yes/no)
- ASM-A-002: 7-day panel render time (seconds); pass if ≤10 s
- ASM-A-003: provisioning restored after volume wipe? (yes/no); pass if no manual steps required
- ASM-A-004: subjective dashboard authoring effort (low/medium/high)
- Overall experience rating for SCN-008 (browse historical sensor data): 1–5
