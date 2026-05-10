# Needs Register

**System:** mqttlogger
**Feature:** 002-mqttlogger-baseline
**Date:** 2026-05-08
**Status:** DRAFT
**Last Updated By:** se-stakeholders skill

---

## Needs

| Need ID | Stakeholder | Verbatim Statement | Normalised Need | Category | Priority | Status |
|---------|-------------|--------------------|-----------------|----------|----------|--------|
| NEED-STK-001-001 | Developer / Operator | "The system reliably captures readings from all sensors with no gaps" | Capture every sensor reading published to the broker without loss during normal operation | Functional | High | Open |
| NEED-STK-001-002 | Developer / Operator | "A system that fails invisibly is worse than one that fails loudly" | Surface any failure that prevents normal data capture visibly and immediately, without requiring manual inspection to discover | Quality | High | Open |
| NEED-STK-001-003 | Developer / Operator | "The inability to confidently say 'the record is complete for this period' undermines the entire purpose of the system" | Provide a means to verify that the captured record is complete for any given time period | Quality | High | Open |
| NEED-STK-001-004 | Developer / Operator | "The system must be able to run unattended for extended periods without requiring intervention" | Operate continuously without manual intervention for periods of months under normal home network conditions | Quality | High | Open |
| NEED-STK-001-005 | Developer / Operator | "The HomeMatic system publishes zero values for all readings on startup — these pollute the dataset" | Identify or flag readings that are known to be spurious (e.g. HomeMatic startup zeros) so they can be excluded from analysis | Functional | Medium | Open |
| NEED-STK-001-006 | Developer / Operator | "Any improvement here — even a simple structured log line confirming successful writes — would be valuable" | Provide observable evidence of healthy data capture without requiring manual container inspection | Quality | Medium | Open |
| NEED-STK-001-007 | Developer / Operator | "When attention is available, it must be spent productively — not on re-learning how the system works" | Enable a returning developer to understand the current system state and resume work within a single orientation session | Quality | High | Open |
| NEED-STK-001-008 | Developer / Operator | "Querying the database and finding unexpected nulls, wrong units, or missing sensors with no clear audit trail would be deeply unsettling" | Store all sensor readings with consistent, predictable structure; record any schema changes with a clear audit trail | Quality | High | Open |
| NEED-STK-001-009 | Developer / Operator | "A sensor stopped publishing, a HomeMatic topic was renamed, or a new sensor was added but never picked up — everything appears healthy but the record is silently incomplete" | Detect and surface changes in the upstream sensor topology — including sensors that stop publishing, renamed topics, and new sensors not yet captured | Functional | High | Open |
| NEED-STK-001-010 | Developer / Operator | "I can look back over months and see meaningful patterns — how the house behaves across seasons, what effect a renovation or temporary measure had" | Retain all readings with sufficient temporal and device-level resolution to support seasonal and renovation-impact analysis | Functional | High | Open |
| NEED-STK-001-011 | Developer / Operator | "The data is trustworthy enough to draw real conclusions from" | Capture and store data with sufficient integrity that it can serve as evidence for energy-use and comfort decisions | Quality | High | Open |
| NEED-STK-002-001 | Future Maintainer | "The running version in production should be unambiguously identifiable from the repository. Tags, a CHANGELOG, and a clear branching state mean there is no question of 'which version is actually deployed right now.'" | Maintain a clear, tagged version history and CHANGELOG so the deployed version is identifiable without ambiguity | Constraint | High | Open |
| NEED-STK-002-002 | Future Maintainer | "A concise reference that answers the questions future-me will actually ask: how do I get the dev environment running, what has been implemented, what is still outstanding, where are the known issues" | Provide a current developer quick-start document that enables re-orientation after an extended absence | Interface | High | Open |
| NEED-STK-002-003 | Future Maintainer | "Having a lightweight backlog — even just a tracked list — means the new idea has somewhere to land immediately, and existing ideas from the last session are not lost" | Maintain a lightweight improvement backlog that is updated at the end of each work session | Constraint | Medium | Open |

---

## Conflicts

| Conflict ID | Need A | Need B | Description | Resolution Status |
|-------------|--------|--------|-------------|-------------------|
| — | — | — | No conflicts identified. STK-001 and STK-002 are the same person; all needs are aligned. | N/A |

---

## Coverage Check

- Total stakeholders identified: 2
- Stakeholders with at least one need captured: 2
- Stakeholders with no needs captured (gap): None
- Notes: STK-002 needs are inferred (unrepresented stakeholder). All STK-002 needs carry an assumption flag — see RISK-011.
