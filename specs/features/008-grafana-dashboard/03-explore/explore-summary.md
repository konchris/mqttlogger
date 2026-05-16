# Solution Exploration Summary

**System:** mqttlogger
**Feature:** 008-grafana-dashboard
**Date:** 2026-05-16
**Status:** ACTIVE — options under exploration
**Last Updated By:** se-explore skill

---

## Solution Set Boundaries

### Hard Constraints (Immediate Disqualifiers)

- Must run as a Docker container in the existing Compose stack on sietchtabr
- Must be open-source with no paid licence requirement
- Must connect to MariaDB read-only; no writes to any table (NFR-INT-002)
- Must not require internet connectivity — LAN-only deployment
- Must provision datasource and dashboard configuration from version control without manual UI steps (NFR-USE-003)

### Soft Constraints (Differentiators)

- Dashboard panels render within 10 seconds for a 7-day query (NFR-PERF-003)
- Available within 2 minutes of Docker Compose stack startup (NFR-REL-003)
- Speed to first working panel is the primary operator value in this exploration phase

### Known Failed Approaches

| Approach | Evidence of Failure | Source |
| -------- | ------------------- | ------ |
| Custom Python/Streamlit dashboard (`hem_dashboard`) | LLM vibe-coded; currently broken; high maintenance burden relative to a solo operator's available time; operator confirmed too complex for current scope | Operator statement 2026-05-16; `../hem_dashboard` codebase |

---

## Active Options

| Option ID | Name | Core Approach | Status | Eliminated At |
| --------- | ---- | ------------- | ------ | ------------- |
| OPT-A | Grafana OSS | Purpose-built time-series dashboard with native MariaDB datasource and JSON file provisioning | Active | — |
| OPT-B | Metabase | Open-source BI tool with MySQL auto-discovery; limited native provisioning-as-code support | Active | — |

---

## Integration Points

| IP ID | Milestone | Question to Answer | Evidence Threshold | Status |
| ----- | --------- | ------------------ | ------------------ | ------ |
| IP-001 | 24 hours after both options running | Which option satisfies all Must Have NFRs AND provides the better experience for SCN-008 (browse historical sensor data)? | Both tools running with ≥1 working sensor panel; NFR-USE-003 tested via volume-wipe experiment; operator has used both for the primary scenario | Pending |

---

## Convergence Target

**Final Integration Point:** IP-001 — 24 hours after both options are running
**Convergence Criterion:** One option satisfies all Must Have NFRs (PERF-003, REL-003, SEC-002, USE-003, INT-002) and provides equal or better experience for SCN-008 than the alternative. If both satisfy all NFRs, operator experience is the deciding factor.
**Deadline:** End of May 2026 (before summer cooling experiment begins)

---

## Current Status

**Options Active:** 2
**Options Eliminated:** 0
**Next Integration Point:** IP-001 — pending both options being started
