# Phase 2 Gate Report

**System:** mqttlogger
**Feature:** 007-python312-upgrade — Python 3.10 → 3.12 runtime upgrade
**Phase:** 2 — Requirements
**Date:** 2026-05-16
**Result:** FAIL
**Conducted By:** se-gate skill

---

## Summary

**Total Checks:** 11
**Passed:** 8
**Failed:** 3
**Not Applicable:** 0

Three failures prevent Phase 2 from closing. The most significant is that `req-quality-report.md` was last updated for feature 004 and covers only 22 requirements; the register now contains 26. FR-023 through FR-026 (added by feature 007) have not been formally assessed by `/se-req-quality`. The other two failures are pre-existing "Should Fix Before Phase 3" items from the feature 004 quality run (FR-MON-004 Unambiguous and FR-MON-005 Necessary) that have no documented acceptance rationale and have not been resolved across three feature cycles.

---

## Check Results

| Check | Artifact | Result | Notes |
| ----- | -------- | ------ | ----- |
| requirements-register.md exists | `specs/system/04-requirements/requirements-register.md` | PASS | 26 requirements across 5 sections |
| No "TBD" in mandatory fields | requirements-register.md | PASS | grep returns no matches |
| Every requirement has a unique ID | requirements-register.md | PASS | FR-001–014, FR-MON-001–007, FR-022–026; all unique |
| req-quality-report.md exists | `specs/system/04-requirements/req-quality-report.md` | PASS | File present; last updated for feature 004 |
| Quality report covers all requirements | req-quality-report.md | **FAIL** | Report states "22 requirements checked"; register contains 26; FR-023, FR-024, FR-025, FR-026 are not in the report |
| No requirement failing Necessary, Unambiguous, or Verifiable | req-quality-report.md | PASS | Existing 22 requirements: no FAILs on these attributes; FR-023–026 were inline-assessed in se-requirements with no failures, but are not formally recorded |
| All Should Fix items resolved or have acceptance rationale | req-quality-report.md | **FAIL** | Two "Should Fix Before Phase 3" items remain open: FR-MON-004 (Unambiguous — grammatical ambiguity not rewritten) and FR-MON-005 (Necessary — NEED-STK-001-002 co-source not added); neither has documented acceptance rationale |
| rtm.md exists | `specs/system/rtm.md` | PASS | File present |
| RTM contains one row per requirement | rtm.md | PASS | 26 rows; FR-023–026 added by se-requirements in this session |
| V&V plan updated — one entry per FR | `specs/system/09-vv/vv-plan.md` | PASS | 26 FR entries; FR-023–026 added by se-requirements in this session |
| V&V Must Have entries have verification methods | vv-plan.md | PASS | FR-023 (I), FR-024 (I), FR-025 (I+T), FR-026 (I+T) — all non-TBD |
| Risk register reviewed against requirements | `specs/system/10-risk/risk-register.md` | PASS | RISK-003 updated to reference feature 007; RISK-025 added for greenlet marker OTQ |

---

## Failures — Action Required

### FAIL 1: Quality report does not cover FR-023 through FR-026

**Artifact:** `specs/system/04-requirements/req-quality-report.md`
**Finding:** The report header states "Total requirements checked: 22." The requirements register now contains 26 requirements. FR-023, FR-024, FR-025, and FR-026 were added during this feature's se-requirements run and have not been formally assessed against all eight IEEE 29148 quality attributes.
**Action Required:** Run `/se-req-quality` to extend the quality report to cover all 26 requirements. FR-023–026 are expected to pass (they were inline-assessed in se-requirements with no attribute failures), but the formal record must exist before Phase 2 can close.
**Owner:** Chris
**Must Resolve Before:** Re-running `/se-gate 2`

---

### FAIL 2: FR-MON-004 Unambiguous WARN — no resolution or acceptance rationale

**Artifact:** `specs/system/04-requirements/req-quality-report.md` (Section FR-MON-004), `specs/system/04-requirements/requirements-register.md` (FR-MON-004 statement)
**Finding:** The quality report identifies a grammatical ambiguity in FR-MON-004: "a sensor publishes readings to the database that is not present" — the relative clause is ambiguous about whether it modifies "readings" or "sensor." A rewrite is suggested in the report but has not been applied, and no acceptance rationale is documented in any artifact. This item has persisted unresolved through features 004, 005, and 006.
**Action Required:** Either (a) apply the suggested rewrite to FR-MON-004 in requirements-register.md: *"…when a sensor whose topic is not present in the known sensor configuration and is not listed in the excluded (event-driven) sensors list publishes readings to the database"* — or (b) add an explicit acceptance note in req-quality-report.md documenting why the current wording is acceptable.
**Owner:** Chris
**Must Resolve Before:** Re-running `/se-gate 2`

---

### FAIL 3: FR-MON-005 Necessary WARN — no resolution or acceptance rationale

**Artifact:** `specs/system/04-requirements/req-quality-report.md` (Section FR-MON-005), `specs/system/04-requirements/requirements-register.md` (FR-MON-005 Source field)
**Finding:** The quality report flags that FR-MON-005 traces to "OPT-B design" with no explicit stakeholder need ID. The recommended action is to add `NEED-STK-001-002` as a co-source. This has not been done, and no acceptance rationale exists. This item has persisted unresolved through features 004, 005, and 006.
**Action Required:** Either (a) update the Source field in requirements-register.md for FR-MON-005 to add `NEED-STK-001-002` as a co-source — or (b) add an explicit acceptance note in req-quality-report.md explaining why the current trace is sufficient.
**Owner:** Chris
**Must Resolve Before:** Re-running `/se-gate 2`

---

## Not Applicable Items

None — all checks apply to this feature and system.

---

## Gate Decision

**Result:** FAIL

Phase 2 is NOT complete. The 3 failures listed above must be resolved before this gate can pass.

The fastest resolution path:
1. Apply the FR-MON-004 rewrite and FR-MON-005 source addition directly in `requirements-register.md` (Failures 2 and 3 — ~5 minutes)
2. Run `/se-req-quality` to extend the quality report to cover FR-023–026 (Failure 1)
3. Re-run `/se-gate 2`

Re-run `/se-gate 2` after resolving all three failures.
