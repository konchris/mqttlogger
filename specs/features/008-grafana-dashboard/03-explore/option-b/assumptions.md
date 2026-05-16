# Assumptions: Option B — Metabase

**Date:** 2026-05-16

---

## Assumptions Register

| ID | Assumption | If False, Then | Validation Approach | Status |
| -- | ---------- | -------------- | ------------------- | ------ |
| ASM-B-001 | Metabase container is available and serving the UI within 2 minutes of `docker compose up` | NFR-REL-003 fails; OPT-B is eliminated unless startup time can be reduced via tuning | TASK-B-001: measure time from container start to UI available | Unvalidated |
| ASM-B-002 | Metabase's MySQL driver is compatible with MariaDB 10.11 on sietchtabr | Datasource connection fails; option eliminated | TASK-B-001: connect to MariaDB and verify query succeeds | Unvalidated |
| ASM-B-003 | A viable provisioning-as-code path exists for Metabase (via API scripting or environment-based seeding) that satisfies NFR-USE-003 without manual UI steps | NFR-USE-003 fails; OPT-B is eliminated — this is the most likely elimination cause | TASK-B-003: investigate and test volume-wipe restore | Unvalidated |
| ASM-B-004 | Metabase's time-series chart types are adequate for the primary use case (temperature/humidity over time by room) | User experience is worse than OPT-A for SCN-008; OPT-A preferred on experience grounds | TASK-B-002: build one time-series panel and assess | Unvalidated |

---

## Assumption Risk Summary

- **ASM-B-001** and **ASM-B-002** are gating assumptions — resolve at TASK-B-001 (first task).
- **ASM-B-003** is the highest-risk assumption and the most likely cause of elimination at IP-001. Metabase's provisioning-as-code story is known to be weaker than Grafana's. If no viable path exists, NFR-USE-003 fails and OPT-B is eliminated.
- **ASM-B-004** is a usability/fitness risk — if Metabase's time-series charts are inferior, OPT-A is preferred on experience grounds even if both satisfy all NFRs.
