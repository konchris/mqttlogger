# Verification and Validation Plan

**System:** mqttlogger
**Feature:** 002-mqttlogger-baseline
**Date:** 2026-05-09
**Status:** DRAFT — initiated by se-nfr; updated continuously
**Last Updated By:** se-nfr skill

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

*To be populated in the next phase when functional requirements are formally elicited and baselined. Each functional requirement (FR-001 through FR-016 from the existing spec.md) will receive a V&V plan entry.*

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
