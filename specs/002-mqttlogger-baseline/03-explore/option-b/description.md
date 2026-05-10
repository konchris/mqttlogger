# Option B: Companion Database Monitor

**Status:** Active
**Date Created:** 2026-05-09
**Last Updated:** 2026-05-09

---

## Core Approach

A separate lightweight Python process — running as a Docker Compose service or scheduled task — periodically queries the MariaDB database to check for data quality and completeness issues. It compares recent database activity against a hardcoded sensor configuration file and reports anomalies to the operator via a self-hosted push notification tool (ntfy.sh or Gotify — both open source, local-only, zero cost).

The sensor config file defines the expected set of sensors. The monitor applies dual-direction checking: it flags sensors in the config that have not appeared in the database within the expected window (sensor silent or logger stopped), and sensors appearing in the database that are not in the config (new sensor discovered, or config is stale). This dual-direction approach makes the config self-auditing — discrepancies surface in both directions without manual review.

This option makes no changes to the mqttlogger codebase. The core capture logic is completely untouched. Observability is achieved through a decoupled companion process that reads from the same database.

## Key Characteristics

- Zero changes to the mqttlogger core — separation of concerns is preserved
- Directly addresses all three risks: RISK-016 (gap in DB = crash or stop detected), RISK-013 (sensor not in DB = topology drift), RISK-014 (DB query defines completeness for any window)
- Introduces a second codebase to maintain, test, and keep running — solo developer maintenance burden is a real cost
- Polling interval determines detection latency — a 5-minute poll means up to 5 minutes before a crash is detected
- Dual-direction sensor config checking is self-auditing: the config is kept honest by operation, not by manual maintenance
- Push notification tool (ntfy.sh or Gotify) is an additional service in the stack

## NFR Satisfaction Assessment

| NFR ID | Priority | Assessment | Confidence |
|--------|----------|------------|------------|
| NFR-PERF-001 | Must Have | Satisfied — companion process reads from DB; does not touch capture path | High |
| NFR-PERF-002 | Must Have | Satisfied — no effect on timestamping | High |
| NFR-REL-001 | Must Have | Satisfied — companion process failure does not affect mqttlogger recovery | High |
| NFR-REL-002 | Must Have | Satisfied — no effect on mqttlogger restart time | High |
| NFR-SEC-001 | Must Have | Companion process requires DB read credentials — must be excluded from version control | Medium |
| NFR-USE-001 | Must Have | Satisfied — unaffected in mqttlogger; companion reports must also be actionable | Medium |
| NFR-USE-002 | Must Have | Companion process must follow same log standard as mqttlogger | Medium |
| NFR-MAIN-001 | Should Have | Medium risk — second codebase requires its own test coverage to 80% threshold | Medium |
| NFR-PORT-001 | Must Have | Companion container added to Docker Compose stack | High |
| NFR-INT-001 | Must Have | Read-only DB access; no schema changes | High |

## Potential Advantages

- Directly addresses all three level-16 risks in one option — the most comprehensive coverage of the three
- mqttlogger codebase remains unchanged — no regression risk to the capture path
- DB-level detection is authoritative — if a record isn't in the database, it genuinely didn't get captured
- Dual-direction sensor config creates an emergent inventory of the actual sensor fleet over time
- Decoupled design means the monitor can be improved, replaced, or extended without touching the logger

## Potential Weaknesses

- Second codebase: additional maintenance burden for a solo developer; risk of neglect after initial implementation
- Polling latency: detection speed is bounded by polling interval; crash detection is slower than OPT-A heartbeat
- Expected sensor list: hardcoded config requires initial setup effort and ongoing discipline to update when sensors are added or removed (mitigated by dual-direction checking, but not eliminated)
- Self-hosted notification tool (ntfy.sh or Gotify) adds another service to the stack — another thing to keep running and updated
- NFR-MAIN-001 applies to the companion codebase too — 80% coverage on a second codebase is additional work
