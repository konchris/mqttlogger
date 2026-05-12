# Feature Specification: Remove __init__.py Legacy Code

**Feature Branch**: `feature/004-remove-init-legacy`
**Created**: 2026-05-12
**Status**: Draft
**Feature ID**: 004-remove-init-legacy

## Background

When the mqttlogger package was first created, `mqttlogger/__init__.py` contained the entire
application entry point: an argument parser (`parse_agruments`) and a `main()` function. This
code was later superseded when the application was refactored into dedicated modules
(`mqtt_client.py`, `heartbeat.py`, `db_connection.py`, `data_model.py`) and the true entry
point moved to `app.py`.

The old functions in `__init__.py` are never called — they are dead code. Because the coverage
tool measures which lines were executed during tests, these uncovered lines artificially suppress
the overall coverage percentage and prevent the project from achieving its 80% coverage
threshold.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Developer removes dead code and coverage clears (Priority: P1)

A developer (the sole maintainer) notices that the CI coverage gate is not met. Tracing the
shortfall, they find that `mqttlogger/__init__.py` contains functions that are never called
by the application or the test suite. The developer removes the dead code, runs the test suite,
and observes that all tests still pass and coverage now meets or exceeds the 80% threshold.

**Why this priority**: This is the entire purpose of the feature. Without it, CI will continue
to fail the coverage gate, blocking future merges.

**Independent Test**: Run the full test suite with coverage after removing the legacy code.
Verify zero test failures and coverage ≥ 80%.

**Acceptance Scenarios**:

1. **Given** `mqttlogger/__init__.py` contains only the legacy `parse_agruments`, `main`, and
   `__author__` symbols, **When** those symbols are removed and the test suite is run,
   **Then** all existing tests pass with no modifications.

2. **Given** the dead code has been removed, **When** coverage is measured across the
   `mqttlogger` package, **Then** the reported line coverage is ≥ 80%.

3. **Given** the dead code has been removed, **When** any other module in the project is
   inspected, **Then** no module imports `parse_agruments`, `main`, or `__author__` from
   `mqttlogger/__init__.py`.

---

### User Story 2 — Package remains importable after cleanup (Priority: P2)

After removal, the `mqttlogger` package must continue to be importable as a package with no
errors. The `__init__.py` file may be left empty or contain only a version string if one is
needed; it must not be deleted (Python requires it for the package to be recognised).

**Why this priority**: Removing the file entirely or introducing a syntax error would break
the application at runtime, not just at test time.

**Independent Test**: After cleanup, `python -c "import mqttlogger"` exits with code 0 and
produces no output or errors.

**Acceptance Scenarios**:

1. **Given** the legacy code has been removed, **When** the `mqttlogger` package is imported
   in isolation, **Then** the import succeeds with no errors or warnings.

2. **Given** the cleaned `__init__.py` is in place, **When** the full application is started
   via `app.py`, **Then** the application initialises and connects to the broker without error.

---

### Edge Cases

- What happens if `__init__.py` is deleted entirely? — Python 3 implicit namespace packages
  mean the package may still import, but to be safe the file is retained (empty or minimal).
- What if a future linter or tool imports from `mqttlogger` directly? — An empty `__init__.py`
  is the standard, safe answer; it exposes nothing unexpected.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `mqttlogger/__init__.py` file MUST NOT contain the `parse_agruments`
  function after this change is applied.
- **FR-002**: The `mqttlogger/__init__.py` file MUST NOT contain the `main` function after
  this change is applied.
- **FR-003**: The `mqttlogger/__init__.py` file MUST NOT contain the `__author__` module-level
  variable after this change is applied (it is a remnant of the old entry-point pattern and
  is not used or tested).
- **FR-004**: The `mqttlogger/__init__.py` file MUST remain present in the repository (not
  deleted), as its absence would break standard Python package conventions relied upon by the
  existing test suite and application entry point.
- **FR-005**: No other source file in the project MUST be modified to compensate for the
  removal — the dead code must have zero callers.
- **FR-006**: All existing automated tests MUST continue to pass without modification after
  the legacy code is removed.
- **FR-007**: The measured line coverage of the `mqttlogger` package MUST be ≥ 80% after
  the dead code is removed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The test suite passes with zero failures after the change (same pass count as
  before the change).
- **SC-002**: Measured line coverage of the `mqttlogger` package is ≥ 80% with no new tests
  added — the improvement comes entirely from removing untested dead code.
- **SC-003**: A `grep` search of the entire codebase finds zero references to
  `parse_agruments` or to `mqttlogger.main`.
- **SC-004**: `python -c "import mqttlogger"` exits with code 0 and no output.
- **SC-005**: CI (lint + test + coverage gate) passes on the feature branch.

## Assumptions

- The `parse_agruments` function (note: typo in original) and `main()` in `__init__.py` are
  confirmed dead code — they are not called by `app.py`, any other module, or any test.
- The `__author__` variable is not used by any documentation tooling, packaging metadata, or
  runtime code (it is not referenced anywhere else in the project).
- Removing this code does not affect the `companion-monitor` package (a separate directory
  with its own `monitor.py`; it has no dependency on `mqttlogger.__init__`).
- The project's 80% coverage threshold is measured over the `mqttlogger/` package; companion
  monitor coverage is measured separately.
- `mqttlogger/__init__.py` will be left as an empty file (zero bytes or a single newline)
  after removal — no replacement content is needed.
