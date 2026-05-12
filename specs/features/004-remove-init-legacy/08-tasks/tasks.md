# Tasks: Remove __init__.py Legacy Code

**Feature:** 004-remove-init-legacy
**Input:** `specs/004-remove-init-legacy/spec.md`, `specs/features/004-remove-init-legacy/07-plan/plan.md`
**Date:** 2026-05-12
**Status:** Complete

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel
- **[Story]**: User story this task belongs to
- **No tests requested** — existing test suite is the verification; no new tests are needed

---

## Phase 1: Pre-Change Verification

**Purpose:** Confirm the dead code is truly dead before touching anything. The plan identified
zero callers via grep; this phase repeats that check at implementation time.

- [x] T001 Grep entire codebase for callers of `parse_agruments`, `main`, and `__author__` from `mqttlogger/__init__.py` — confirm zero results before making any change

**Checkpoint:** Zero callers confirmed → safe to proceed to Phase 2.

---

## Phase 2: Dead Code Removal (User Story 1 — P1)

**Goal:** Remove all dead code from `mqttlogger/__init__.py`, leaving the file empty (or with a
single-line package docstring if ruff requires one).

**Independent Test:** `pytest --cov=mqttlogger` passes with ≥ 80% coverage; `python -c "import mqttlogger"` succeeds.

- [x] T002 [US1] Remove `__author__`, `parse_agruments()`, `main()`, and the `if __name__ == '__main__'` block from `mqttlogger/__init__.py` — leave file empty or with a single newline
- [x] T003 [US1] Run `python -m ruff check mqttlogger/__init__.py` — if ruff warns on empty file, add a single-line package docstring `"""mqttlogger package."""`; otherwise leave empty (resolves OTQ-001 from plan.md)

**Checkpoint:** `mqttlogger/__init__.py` contains no callable definitions, no `__author__`, no `if __name__` block.

---

## Phase 3: Verification (User Stories 1 and 2)

**Goal:** Confirm zero regressions, coverage gate passes, importability preserved, and all
spec success criteria met.

- [x] T004 [P] [US1] Run `python -m ruff check` across the full project — verify lint passes with no new errors
- [x] T005 [P] [US2] Run `python -c "import mqttlogger"` — verify exit code 0 and no output (SC-004)
- [x] T006 [US1] Run `python -m pytest --cov=mqttlogger --cov-report=term-missing` — verify all tests pass and coverage ≥ 80% (SC-001, SC-002)
- [x] T007 [US1] Run `grep -r "parse_agruments\|mqttlogger\.main" .` — verify zero matches in the codebase (SC-003)

**Checkpoint:** All four verification tasks pass → both user stories are complete.

---

## Phase 4: Threaded Artifact Updates

**Purpose:** Update SE artifacts to reflect that FR-022 is now implemented. These are
documentation tasks, not code tasks.

- [x] T008 [P] Update `specs/system/04-requirements/requirements-register.md` — change FR-022 status from `Open (feature 004)` to `Implemented`
- [x] T009 [P] Update `specs/system/rtm.md` — change FR-022 status from `Open` to `Implemented`
- [x] T010 [P] Update `specs/system/09-vv/vv-plan.md` — change FR-022 status from `Planned` to `Implemented`

**Checkpoint:** SE artifacts reflect the implementation state. Ready for Phase 5 gate.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Pre-change verification):** No dependencies — start immediately
- **Phase 2 (Removal):** Depends on Phase 1 PASS (zero callers confirmed)
- **Phase 3 (Verification):** Depends on Phase 2 completion (T002 + T003 done)
  - T004, T005 can run in parallel with each other and before T006
  - T006 must come after T002 (measures the effect of the removal)
  - T007 can run in parallel with T006 (independent grep check)
- **Phase 4 (Artifact updates):** Can start after Phase 3 all-pass; T008, T009, T010 all run in parallel

### Requirement Coverage

| Spec FR | Task(s) | Phase |
| ------- | ------- | ----- |
| FR-001 (no `parse_agruments`) | T002 | 2 |
| FR-002 (no `main`) | T002 | 2 |
| FR-003 (no `__author__`) | T002 | 2 |
| FR-004 (`__init__.py` retained) | T002 | 2 |
| FR-005 (no other files changed) | T001 + T007 | 1 + 3 |
| FR-006 (all tests pass) | T006 | 3 |
| FR-007 (coverage ≥ 80%) | T006 | 3 |
| SE FR-022 (no dead code) | T002 + T007 | 2 + 3 |

All 8 requirements (7 spec FRs + SE FR-022) are covered. Coverage: 100%.

### Parallel Opportunities

```bash
# After T002 + T003 complete, run these in parallel:
T004  python -m ruff check .
T005  python -c "import mqttlogger"

# After T004, T005 pass:
T006  pytest --cov (sequential: measures the change)
T007  grep check (parallel with T006)

# After T006, T007 both pass:
T008  Update requirements-register.md  (parallel)
T009  Update rtm.md                    (parallel)
T010  Update vv-plan.md                (parallel)
```

---

## Implementation Strategy

### MVP (User Story 1 Only)

1. Phase 1: Confirm zero callers (T001)
2. Phase 2: Remove dead code (T002, T003)
3. Phase 3: Run lint + tests + coverage (T004–T007)
4. **VALIDATE**: All green → User Story 1 complete

User Story 2 (`python -c "import mqttlogger"`) is covered by T005 within Phase 3 — no
additional implementation work required. Both stories complete simultaneously.

### Total Estimated Effort

This is a 10-minute implementation: one file edit, three shell commands. The SE artifact
updates (Phase 4) take slightly longer. The task list exists to satisfy the SE workflow
traceability obligation, not to manage complexity.
