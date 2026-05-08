# Risk Register — mqttlogger Baseline

**Feature:** 002-mqttlogger-baseline
**Created:** 2026-05-08
**Status:** ACTIVE

Columns: ID · Description · Category · Probability (1–5) · Consequence (1–5) · Risk Level (P×C) · Handling Strategy · Mitigation / Evidence Action · Phase Identified

| ID | Description | Category | P | C | Risk Level | Handling | Mitigation / Evidence Action | Phase |
|----|-------------|----------|---|---|------------|----------|------------------------------|-------|
| RISK-001 | No CI/CD pipeline — regressions or quality drift may reach `main` undetected | Assumption/Unknown | 3 | 4 | 12 | Plan | Establish GitHub Actions pipeline with lint + test + 80% coverage gate; track as TBD-003 | Phase 0 |
| RISK-002 | config.json may have been committed to Bitbucket history with live credentials | Assumption/Unknown | 3 | 4 | 12 | Plan | Audit Bitbucket commit history before migration; sanitise or drop history with justification; track as TBD-004 | Phase 0 |
| RISK-003 | Python 3.10 reaches EOL October 2026 — security patches cease | Known Constraint | 4 | 2 | 8 | Plan | Upgrade to Python 3.11+ before EOL; track as TBD-005 | Phase 0 |
| RISK-004 | Single developer — no knowledge redundancy; bus factor = 1 | Known Constraint | 2 | 4 | 8 | Monitor | SE documentation, architecture docs, and clear spec artefacts reduce impact; continue SE pack | Phase 0 |
| RISK-005 | No linting enforcement — code quality drift over time | Assumption | 3 | 2 | 6 | Plan | Add ruff configuration and CI lint gate; track as TBD-001 | Phase 0 |
| RISK-006 | MQTT transport assumption — if sensor devices change protocol, service cannot adapt | Assumption | 2 | 3 | 6 | Monitor | Abstract ingestion interface in future architecture; noted as TBD-008 | Phase 0 |
| RISK-007 | Indefinite retention without archival strategy — unbounded database growth over years | Assumption/Unknown | 3 | 2 | 6 | Monitor | Define retention/archival policy; measure actual growth rate in Phase 3+; track as TBD-010 | Phase 0 |
| RISK-008 | Bitbucket → GitHub migration may drop commit history — traceability loss | Known Constraint | 3 | 2 | 6 | Accept | Credential hygiene justifies history drop; document decision as ADR before migration | Phase 0 |
| RISK-009 | Data schema may not satisfy future analysis needs — analyses are undefined at capture time | Assumption | 2 | 3 | 6 | Monitor | Define at least one target analysis before any schema change; track as TBD-009 | Phase 0 |
| RISK-010 | No dependency scanner — vulnerable transitive dependencies may go undetected | Unknown | 2 | 2 | 4 | Monitor | Add pip-audit or Dependabot to CI pipeline when pipeline is established | Phase 0 |
| RISK-011 | STK-002 (Future Maintainer) needs are inferred, not directly elicited — actual re-orientation needs may differ | Elicitation Assumption | 3 | 4 | 12 | Monitor | Validate STK-002 needs after the first real return-to-codebase session; update needs register with findings | Phase 0 |
| RISK-012 | HomeMatic/RedMatic identified as upstream system not listed in original interfaces — spurious startup zeros are a confirmed data quality issue | Unknown | 4 | 3 | 12 | Plan | Document HomeMatic interface in ICD; evaluate whether startup zeros can be suppressed in RedMatic ("publish cached values on start" setting); add constitution interface entry | Phase 0 |
| RISK-013 | Silent drift — upstream sensor topology changes (topic renamed, sensor stops publishing, new sensor added) are undetectable by the current service | Known Gap | 4 | 4 | 16 | Plan | Define sensor topology monitoring mechanism; consider periodic "expected sensors seen" health check; address in architecture phase | Phase 0 |
| RISK-014 | No mechanism exists to verify data completeness for a given time period — gaps cannot be detected without manual inspection | Known Gap | 4 | 4 | 16 | Plan | Design completeness verification capability (e.g. expected-vs-actual reading count per sensor per period); address in architecture or NFR phase | Phase 0 |
