---
description: "Task list for 007-python312-upgrade — Python 3.10 → 3.12 runtime upgrade"
---

# Tasks: 007-python312-upgrade — Python 3.10 → 3.12 Runtime Upgrade

**Input**: `specs/features/007-python312-upgrade/07-plan/plan.md`
**Feature requirements**: FR-023, FR-024, FR-025, FR-026
**Risk addressed**: RISK-003 (Python 3.10 EOL October 2026)

**Organization**: Tasks are grouped by implementation phase from plan.md. No spec.md exists for this SE feature — plan phases substitute for user stories.

## Format: `[ID] [P?] Description`

- **[P]**: Can run in parallel (different files, no block on incomplete tasks)
- All phases are Must Have; the entire feature ships in one PR

---

## Phase 1: Dependency Pin Updates (FR-026)

**Purpose**: Update `requirements.txt` so the main app container can be built on Python 3.12. This phase gates Phase 2 — the Dockerfiles cannot be meaningfully verified until these pins are correct.

**Independent Test**: `pip install -r requirements.txt` succeeds in a Python 3.12 environment (CI confirms this).

- [x] T001 Update `requirements.txt` — replace `greenlet==1.1.3` (with its auto-generated platform markers) with `greenlet>=3.0.0` (no platform marker required; wheels exist for all supported platforms)
- [x] T002 Update `requirements.txt` — replace `sqlalchemy==1.4.41` with `sqlalchemy>=1.4.50,<2.0`
- [x] T003 Update `requirements.txt` — replace `mysqlclient==2.1.1` with `mysqlclient>=2.2.0`

**Checkpoint**: `requirements.txt` specifies greenlet ≥ 3.0.0, SQLAlchemy ≥ 1.4.50 < 2.0, mysqlclient ≥ 2.2.0. All other pins unchanged.

---

## Phase 2: Container Image Updates (FR-023, FR-024)

**Purpose**: Point both Dockerfiles at `python:3.12-slim`. These tasks are independent of each other and can be applied in parallel.

**Independent Test**: `docker build -t mqttlogger-test .` completes without error (CI confirms this via the full test run).

- [x] T004 [P] Update `Dockerfile` — change `FROM python:3.10-slim` to `FROM python:3.12-slim` (line 2)
- [x] T005 [P] Update `companion-monitor/Dockerfile` — change `FROM python:3.11-slim` to `FROM python:3.12-slim` (line 1)

**Checkpoint**: Both Dockerfiles reference `python:3.12-slim`. No other lines change.

---

## Phase 3: CI Pipeline Update (FR-025)

**Purpose**: Align the CI pipeline with the upgraded runtime so that test results are representative of the deployed container.

**Independent Test**: CI jobs (`Lint (ruff)` and `Test`) both complete successfully against Python 3.12.

- [x] T006 Update `.github/workflows/ci.yml` — change both `python-version: "3.10"` entries to `python-version: "3.12"` (one in the `lint` job, one in the `test` job)

**Checkpoint**: `ci.yml` contains no reference to Python 3.10; both jobs specify `"3.12"`.

---

## Phase 4: Governance and Documentation

**Purpose**: Close the governance obligations created when RISK-003 was identified. These tasks are independent of each other and of Phases 1–3.

- [x] T007 [P] Update `.specify/memory/constitution.md` — change "Python 3.10+" to "Python 3.12+" in the Deployment Constraints section and the Development Standards section; in the Open Issues table, mark TBD-005 as closed (add "CLOSED — feature 007-python312-upgrade")
- [x] T008 [P] Update `CLAUDE.md` — in the "Current state / Next candidates" section, move RISK-003 out of the open candidates list and add a note that it is addressed by feature 007-python312-upgrade; set the active feature to `007-python312-upgrade`

**Checkpoint**: No reference to "Python 3.10+" remains in constitution.md; CLAUDE.md reflects the active feature.

---

## Phase 5: Verification

**Purpose**: Confirm the upgrade is correct end-to-end before merging and before deploying to sietchtabr.

- [ ] T009 Open PR from `feature/007-python312-upgrade` → `develop` and verify CI passes — both `Lint (ruff)` and `Test + Coverage` jobs must be green on Python 3.12; coverage must remain ≥ 80%
- [ ] T010 Deploy to sietchtabr: `git pull && docker compose build && docker compose up -d`; verify the `mqtt_logger` container starts cleanly; confirm `docker compose exec mqtt_logger python --version` returns `Python 3.12.x`; confirm a new reading appears in the database within 5 minutes of startup

**Checkpoint**: CI green; sietchtabr running Python 3.12; at least one reading confirmed in MariaDB post-upgrade.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Dependency Pins)**: No dependencies — start immediately
- **Phase 2 (Dockerfiles)**: Logically depends on Phase 1 (pins must be correct before image build is meaningful), but the file edits themselves can be made in parallel
- **Phase 3 (CI)**: Independent of Phases 1 and 2; can be applied at any time
- **Phase 4 (Governance)**: Independent of all other phases; can be applied at any time
- **Phase 5 (Verification)**: Depends on Phases 1–4 complete and PR open

### Task Dependencies

- T001, T002, T003 all modify `requirements.txt` — apply sequentially within Phase 1
- T004 and T005 modify different files — can be applied in parallel
- T007 and T008 modify different files — can be applied in parallel
- T009 (CI verification) must follow T001–T008 all committed to the branch
- T010 (sietchtabr deployment) must follow T009 (PR merged to develop)

### Parallel Opportunities

```
Phase 1:  T001 → T002 → T003  (sequential, same file)
Phase 2:  T004 ‖ T005          (parallel, different files)
Phase 3:  T006                 (independent, any time)
Phase 4:  T007 ‖ T008          (parallel, different files)
Phase 5:  T009 → T010          (sequential, T010 requires merged PR)
```

---

## Implementation Strategy

### Minimum Viable Implementation (All Must Have)

All 10 tasks are required — this feature has no optional scope. Complete all phases, open the PR, verify CI, then deploy.

### Recommended Order for a Single Session

1. T001, T002, T003 — update `requirements.txt`
2. T004, T005 — update both Dockerfiles
3. T006 — update `ci.yml`
4. T007, T008 — update constitution and CLAUDE.md
5. T009 — push branch, open PR, wait for CI
6. T010 — merge and deploy to sietchtabr

---

## Notes

- [P] tasks modify different files; apply them in any order or simultaneously
- T009 (CI) is the primary quality gate — do not deploy until it passes
- T010 is a manual deployment test on `sietchtabr`; per branching convention, the branch is not considered done until the deployment test passes
- If CI fails due to OTQ-001 (greenlet platform marker syntax), simplify T001 further: drop all markers, use plain `greenlet>=3.0.0`
- If CI fails due to OTQ-002 (SQLAlchemy 1.4.50 behaviour delta), check the SQLAlchemy 1.4.x changelog for breaking changes between 1.4.41 and the resolved version
