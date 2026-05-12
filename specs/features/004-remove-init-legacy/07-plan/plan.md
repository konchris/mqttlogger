# Feature Plan

**System:** mqttlogger
**Feature:** 004-remove-init-legacy
**Date:** 2026-05-12
**Status:** DRAFT
**Last Updated By:** se-plan skill

---

## 1. Technical Approach

### System Decomposition

This feature introduces no new components and removes no running services. The system
decomposition is unchanged from the architecture baseline established in feature
002-mqttlogger-baseline. The only structural change is the content of a single file.

**`mqttlogger/__init__.py` (modified — content removed)**
- Purpose: Python package marker. Currently contains dead code (`parse_agruments()`,
  `main()`, `__author__`, `if __name__ == '__main__'` block) carried over from the
  original monolithic implementation before the refactor into `mqtt_client.py`,
  `heartbeat.py`, `db_connection.py`, and `data_model.py`.
- Change: All callable definitions and module-level executable statements are removed.
  The file is left empty (or containing only the package docstring if required by
  downstream tooling). No symbols in this file have callers anywhere in the codebase.
- Primary requirement satisfied: FR-022
- NFRs respected: NFR-MAIN-001 (coverage ≥ 80%)

All other components — `mqtt_client.py`, `heartbeat.py`, `db_connection.py`,
`data_model.py`, `app.py`, `companion-monitor/monitor.py` — are untouched.

### Key Interactions

No interaction changes. The `__init__.py` file participates in no message flow, no
database write path, and no signal handling path. Removing its contents has zero
runtime-observable effect on the system's behaviour.

### NFR-Driven Design Decisions

| NFR ID | Attribute | Mechanism |
| ------ | --------- | --------- |
| NFR-MAIN-001 | Maintainability — 80% line coverage | Dead code in `__init__.py` contributes 16 uncovered statements to the coverage denominator, suppressing the reported rate. Removing those statements eliminates the suppression effect. Current coverage: 86.36% (132 stmts, 18 missed). Post-removal projection: ~93% (116 stmts, 8 missed). |
| NFR-USE-002 | Usability — log entry completeness | No change. |
| NFR-REL-001 | Reliability — automatic fault recovery | No change. |

Note: coverage already exceeds the 80% gate (CI is green). The value of this change is
(a) satisfying FR-022 (no dead code), (b) raising coverage to ~93% for headroom, and
(c) satisfying Constitution Principle VII (Minimal Surface Area) by removing unreachable
dead code.

### Technology Constraints

| Constraint | Technology/Platform | Source |
| ---------- | ------------------- | ------ |
| Language | Python 3.10+ | Constitution |
| Test framework | pytest + pytest-cov | NFR-MAIN-001, CI pipeline (003-cicd-pipeline) |
| Coverage gate | 80% line coverage | NFR-MAIN-001, `.github/workflows/ci.yml` |
| Linting | ruff | 003-cicd-pipeline |
| Broker (test) | Eclipse Mosquitto (real, via fixture) | Constitution Principle VI |
| Database (test) | MariaDB (real, via fixture) | Constitution Principle VI |

---

## 2. Open Technical Questions

| ID | Question | Affects | Options | Resolution Method |
| -- | -------- | ------- | ------- | ----------------- |
| OTQ-001 | Should `__init__.py` be left completely empty or retain a one-line package docstring? | FR-022, ruff lint | (A) Completely empty file; (B) Single docstring line `"""mqttlogger package."""` | Inspect ruff output on empty `__init__.py`; if ruff or CI warns on missing docstring, add the one-liner. If not, leave empty. |
| OTQ-002 | Does `data_model.py` (76% coverage, 6 missed lines 42–47, 51) warrant additional test coverage in this same PR, or is it a separate concern? | NFR-MAIN-001 | (A) Address in this PR — brings coverage higher; (B) Defer — separate feature | Decision: defer. FR-022 is scoped to `__init__.py`; `data_model.py` coverage is a separate quality item. |

Both questions are low-risk. OTQ-001 resolves at implementation time with a one-command
lint check. OTQ-002 is explicitly deferred.

---

## 3. Implementation Sequence

This feature is a single-step removal. No multi-phase build-up is required.

### Phase Breakdown

**Phase 1 — Pre-Change Verification**
Confirm zero callers for all symbols defined in `mqttlogger/__init__.py` before any
edit. The caller audit has already been performed (grep across full codebase, 2026-05-12);
this step repeats it at implementation time as a safety check.
Requirements addressed: FR-022 (pre-condition verification)

**Phase 2 — Dead Code Removal**
Remove `parse_agruments()`, `main()`, `__author__`, and the `if __name__ == '__main__'`
block from `mqttlogger/__init__.py`. Leave the file empty (or with a single package
docstring if linting requires it).
Requirements addressed: FR-022

**Phase 3 — Verification**
Run the full test suite and confirm:
- All 46 tests pass, 1 skipped (same as baseline)
- `pytest-cov` reports ≥ 80% (expected ~93%)
- `ruff` lint passes on the modified file
- No import errors from any module that imports `mqttlogger`

Requirements verified: FR-022, NFR-MAIN-001

### Minimum Viable Implementation

The minimum (and complete) implementation is Phase 2 alone: remove the dead code.
Phases 1 and 3 are verification steps, not implementation steps.

Requirements: FR-022

### External Dependencies and Schedule Constraints

| Dependency | Type | Affects | Notes |
| ---------- | ---- | ------- | ----- |
| GitHub Actions CI | Internal CI | FR-022, NFR-MAIN-001 | CI must run green on the feature branch before merge to develop |
| sietchtabr deployment test | Manual | All FRs | Per branching convention, change must be verified on sietchtabr before merge |

No third-party dependencies are introduced or modified.

---

## 4. Requirements Coverage Check

| Req ID | Addressed By | Phase | Notes |
| ------ | ------------ | ----- | ----- |
| FR-001 | Unchanged — `mqtt_client.py::on_connect()` | — | No change; continues to be satisfied |
| FR-002 | Unchanged — `mqtt_client.py::on_message()` | — | No change |
| FR-003 | Unchanged — `mqtt_client.py::insert()` | — | No change |
| FR-004 | Unchanged — paho reconnect loop | — | No change |
| FR-005 | Unchanged — `mqtt_client.py` try/except | — | No change |
| FR-006 | Unchanged — structured log calls in `mqtt_client.py`, `app.py` | — | No change |
| FR-007 | Unchanged — `app.py` signal handlers | — | No change |
| FR-008 | Unchanged — `db_connection.py::load_config_file()` | — | No change |
| FR-009 | Unchanged — `Dockerfile` USER directive | — | No change |
| FR-010 | Unchanged — `docker-compose.yml` | — | No change |
| FR-011 | Unchanged — `db_connection.py` validation | — | No change |
| FR-012 | Unchanged — `app.py` RotatingFileHandler | — | No change |
| FR-013 | Unchanged — `app.py` `client.will_set()` | — | No change |
| FR-014 | Unchanged — `heartbeat.py::HeartbeatThread` | — | No change |
| FR-MON-001 | Unchanged — heartbeat → uptime_kuma → ntfy | — | Validated; no change |
| FR-MON-002 | Unchanged — `companion-monitor/monitor.py` | — | Validated; no change |
| FR-MON-003 | Unchanged — `companion-monitor/monitor.py` | — | Validated; no change |
| FR-MON-004 | Unchanged — `companion-monitor/monitor.py` | — | Validated; no change |
| FR-MON-005 | Unchanged — in-memory sets in `monitor.py` | — | No change |
| FR-MON-006 | Unchanged — ntfy container + LAN | — | No change |
| FR-MON-007 | Unchanged — env var reads in `monitor.py` | — | No change |
| FR-022 | `mqttlogger/__init__.py` — content removed | Phase 2 | This feature's sole deliverable |

Uncovered requirements: None — all 22 requirements are addressed. FR-022 is the only
one whose implementation is part of this feature.

---

## 5. Risks Introduced by This Plan

This plan introduces no new risks. The change is a file-content deletion with zero
runtime effect. All risks documented in the risk register that are relevant to this
feature were identified during Phases 0–2 and remain unchanged:

| Risk ID | Description | Mitigation in Plan |
| ------- | ----------- | ------------------ |
| RISK-004 | Bus factor = 1 (solo developer) | SE artifacts and this plan document the intent; mitigated by thorough V&V in Phase 3 |
| NFR-MAIN-001 (RISK residual) | Coverage gate already passing at 86%; removing dead code is improvement, not a fix | Coverage baseline confirmed before change; post-change measurement is the verification event |

No new risk register entries are required.
