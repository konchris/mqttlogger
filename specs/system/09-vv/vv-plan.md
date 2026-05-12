# Verification and Validation Plan

**System:** mqttlogger
**Feature:** 004-remove-init-legacy (updated; originally 002-mqttlogger-baseline)
**Date:** 2026-05-12
**Status:** DRAFT — updated by feature 004
**Last Updated By:** se-requirements skill (2026-05-12)

---

## Purpose

This plan defines how every requirement — functional and non-functional — will be verified or validated. It is a threaded artifact: initiated here with NFR entries, extended in the next phase with functional requirement entries, and updated through execution when results are recorded.

A requirement without a verification method is incomplete by definition.

---

## Verification Methods

| Code | Method | Description |
|------|--------|-------------|
| T | Test | Execute the system or component under defined conditions and observe results against a measurable pass criterion |
| A | Analysis | Mathematical, logical, or architectural reasoning without executing the system |
| I | Inspection | Review of artifacts, code, configuration, or documentation |
| D | Demonstration | Operate the system to show a capability without formal measurement |

## Verification Stages

| Code | Stage | Description |
|------|-------|-------------|
| UT | Unit Test | Individual component or function in isolation |
| IT | Integration Test | Interaction between components (real broker, real database) |
| ST | System Test | Full system stack against requirements |
| AT | Acceptance Test | Stakeholder validation in the operational context |

---

## V&V Plan Table

| Req ID | Type | Short Description | Method | Stage | Pass Criterion | Responsible | Status |
|--------|------|-------------------|--------|-------|----------------|-------------|--------|
| NFR-PERF-001 | NFR | Message completeness — no drops under normal load | T | ST | N messages published = N records in database; no messages discarded due to processing backlog | TBD | Planned |
| NFR-PERF-002 | NFR | Timestamp fidelity within sensor publication interval | A | — | Analysis confirms co-hosted latency (sub-ms LAN + NTP) is orders of magnitude below any sensor's publication interval | TBD | Planned |
| NFR-REL-001 | NFR | Automatic recovery from all software faults | D | ST | (a) Container restart without operator action; (b) broker reconnect after drop; (c) service continues after DB write failure | TBD | Planned |
| NFR-REL-002 | NFR | Recovery time ≤ 60 seconds after crash | T | ST | Time from container kill to first successful DB write ≤ 60 seconds | TBD | Planned |
| NFR-SEC-001 | NFR | Credentials not in version control | I | — | .gitignore excludes credential files; git history audit finds no committed credential values | TBD | Planned |
| NFR-USE-001 | NFR | Error messages identify field, source, and attempted value | T | ST | Each invalid input class produces an error message naming the specific field, source, and attempted value | TBD | Planned |
| NFR-USE-002 | NFR | Log entries contain all 6 required fields | I | ST | All log entries across startup, operation, error, and shutdown contain: timestamp, level, module, function, line number, message | TBD | Planned |
| NFR-MAIN-001 | NFR | Test coverage ≥ 80% line coverage | T | UT+IT | pytest-cov reports ≥ 80% line coverage; enforcement deferred to CI/CD establishment | TBD | Planned |
| NFR-PORT-001 | NFR | Deployable via Docker Compose on Linux amd64/arm64 | D | ST | docker compose up -d completes; logger connects, receives a test message, writes to DB | TBD | Planned |
| NFR-INT-001 | NFR | DB schema owned by mqttlogger; all changes via migrations | I | — | Current schema fully described by version-controlled scripts; no out-of-band changes exist in the database | TBD | Planned |

---

## Functional Requirements

*Populated from requirements-register.md (2026-05-10). Core logger FRs (FR-001..FR-014) and monitoring FRs (FR-MON-001..FR-MON-007).*

| Req ID | Type | Short Description | Method | Stage | Pass Criterion | Responsible | Status |
|--------|------|-------------------|--------|-------|----------------|-------------|--------|
| FR-001 | FR | MQTT subscription — receive all messages on configured topic filter | T | ST | N messages published = N records in DB | Chris | Planned |
| FR-002 | FR | Message parsing — device, timestamp, value extracted from payload | T | IT | Send known payload; verify DB row fields | Chris | Planned |
| FR-003 | FR | Persistent storage — reading committed to DB before considered captured | T | ST | N published = N committed; partial-write on kill handled | Chris | Planned |
| FR-004 | FR | Broker reconnection — automatic, no operator intervention | D | ST | Stop broker; restart; verify reconnect and capture resume | Chris | Planned |
| FR-005 | FR | DB write failure handling — log, discard, continue | D | ST | Make DB unreachable; verify service continues; verify error logged | Chris | Planned |
| FR-006 | FR | Lifecycle event logging — connect, disconnect, receive, write, startup, shutdown | I | ST | All 7 event types present in log across full exercise (corrected from 8: broker connect, broker disconnect, message received, DB write success, DB write failure, startup complete, shutdown initiated) | Chris | Planned |
| FR-007 | FR | Graceful shutdown — clean exit ≤ 10 s on SIGTERM/SIGINT | T | ST | SIGTERM → exit within 10 s; broker closed; no partial DB rows | Chris | Planned |
| FR-008 | FR | External configuration — no hardcoded values | I | — | No credentials or addresses in source code | Chris | Planned |
| FR-009 | FR | Non-root container execution | I | — | Dockerfile USER directive is non-root UID | Chris | Planned |
| FR-010 | FR | Docker Compose deployment — full stack via single command | D | ST | `docker compose up -d` → logger captures test message | Chris | Planned |
| FR-011 | FR | Startup validation — reject on missing/invalid config with specific error | T | ST | Each invalid input class → error names field, source, attempted value | Chris | Planned |
| FR-012 | FR | Bounded log files — rotating with size and count limits | I | — | RotatingFileHandler or equivalent configured with non-zero limits | Chris | Planned |
| FR-013 | FR | MQTT LWT — broker publishes "offline" on unexpected disconnect | T | ST | Kill process without SIGTERM; verify broker publishes "offline" | Chris | Planned |
| FR-014 | FR | HTTP liveness heartbeat — push every configured interval; skip if no URL | T | IT | Heartbeat arrives at URL at interval; no error when URL absent | Chris | Planned |
| FR-MON-001 | FR | Crash notification ≤ 120 s after container stop | T | ST | Kill logger; measure time to notification ≤ 120 s | Chris | **Validated** (IP-001: mean 93 s, max 120 s, 3/3) |
| FR-MON-002 | FR | Sensor silence alert — periodic sensor absent > gap window | D | ST | Stop sensor for gap window; verify notification received | Chris | **Validated** (IP-001: attic humidity silence detected) |
| FR-MON-003 | FR | Sensor recovery notification | D | ST | Allow silenced sensor to resume; verify recovery notification | Chris | **Validated** (IP-001: recovery notification confirmed) |
| FR-MON-004 | FR | Unknown sensor detection — unrecognized sensor in DB triggers alert | D | ST | Allow new sensor to publish; verify alert within one poll cycle | Chris | **Validated** (IP-001: 3 dining room sensors auto-detected) |
| FR-MON-005 | FR | Alert fires on state transition only — not every poll cycle | T | IT | Sustain silence for multiple cycles; verify exactly one alert | Chris | Planned |
| FR-MON-006 | FR | Local push notification — fully LAN-only path to operator device | D | AT | Block outbound internet; verify notifications arrive on operator's iPhone on home Wi-Fi (requires physical device on home network — cannot be automated) | Chris | Planned |
| FR-MON-007 | FR | Configurable monitoring parameters via environment variables | I | — | All parameters env-var sourced; no hardcoded thresholds | Chris | Planned |
| FR-022 | FR | No dead code in mqttlogger/__init__.py | I | — | `mqttlogger/__init__.py` contains no callable definitions; codebase search finds zero callers for any removed symbol | Chris | Planned |

---

## Validation Scenarios

*To be populated in Phase 6. Maps operational scenarios from `01-conops/operational-scenarios.md` to acceptance test events.*

| Scenario ID | Scenario Name | Validation Event | Pass Criterion | Status |
|-------------|---------------|------------------|----------------|--------|
| SCN-001 | Continuous sensor capture | AT | All readings from a defined sensor published over a test period appear in DB | Planned |
| SCN-002 | Recovery after power outage | AT | After host power cycle, service restarts and resumes capture without operator action (after manual power-on) | Planned |
| SCN-003 | Silent logger crash | AT | After container kill, service recovers within 60 seconds; gap in record bounded to recovery window | Planned |
| SCN-004 | Misconfigured startup | AT | Each invalid config class produces a specific, actionable error message | Planned |
| SCN-005 | Broker temporarily unavailable | AT | After broker restart, logger reconnects automatically and resumes capture | Planned |
| SCN-006 | HomeMatic startup zeros | AT | After CCU3 restart, spurious zeros are stored (or suppressed if RedMatic mitigation applied); no service interruption | Planned |
| SCN-007 | Planned maintenance | AT | After docker compose down/up cycle, service resumes capture; operator confirms via DB inspection | Planned |

---

## Results

*To be populated during Phase 6 execution.*
