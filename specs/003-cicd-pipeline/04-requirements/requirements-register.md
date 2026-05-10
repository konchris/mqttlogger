# Requirements Register

**System:** mqttlogger
**Feature:** 003-cicd-pipeline
**Date:** 2026-05-10
**Status:** BASELINED
**Last Updated By:** feature init

---

## Overview

Lightweight requirements for establishing a CI/CD pipeline with automated lint, test, and coverage enforcement. Closes RISK-001, RISK-024, and NFR-MAIN-001 from the 002-mqttlogger-baseline risk register.

No ConOps or exploration phase — the problem is well-understood and the solution space has no competing options worth evaluating.

---

## Requirements

### FR-CI-001 — Automated Lint on Every Push

**Statement:** The CI pipeline shall run `ruff check` against all Python source files on every push to any branch and on every pull request. A lint failure shall block the pipeline.

**Source:** RISK-001, TBD-001
**Priority:** Must Have
**Verification:** Inspect `.github/workflows/ci.yml`; introduce a lint error and verify pipeline fails.

---

### FR-CI-002 — Automated Test Execution

**Statement:** The CI pipeline shall run the full pytest test suite on every push and pull request. A test failure shall block the pipeline.

**Source:** RISK-001, TBD-003
**Priority:** Must Have
**Verification:** Inspect workflow; introduce a failing test and verify pipeline fails.

---

### FR-CI-003 — Coverage Gate

**Statement:** The CI pipeline shall measure pytest line coverage and fail if coverage is below 80% across `mqttlogger/` and `companion-monitor/`. A coverage failure shall block the pipeline.

**Source:** NFR-MAIN-001, TBD-002
**Priority:** Must Have (implements Should Have NFR — the gate is the enforcement mechanism)
**Verification:** Reduce coverage below 80% by removing tests; verify pipeline fails.

---

### FR-CI-004 — Linux amd64 Runtime

**Statement:** The CI pipeline shall execute on a Linux runner (ubuntu-latest) to match the production deployment target (sietchtabr, Linux amd64).

**Source:** NFR-PORT-001, TC-001 (deployment target)
**Priority:** Must Have
**Verification:** Inspect workflow `runs-on` field.

---

### FR-CI-005 — MariaDB Integration Test Service

**Statement:** The CI pipeline shall provide a live MariaDB instance as a service container so that integration tests can exercise real database connections without mocking.

**Source:** Constitution Section VI (Integration-Preferred Testing)
**Priority:** Must Have
**Verification:** Inspect workflow `services` block; verify integration tests connect to real DB in CI.

---

### FR-TEST-001 — mqttlogger Unit and Integration Tests

**Statement:** The test suite shall cover `mqttlogger/` at ≥80% line coverage, including: config loading and validation (`db_connection.py`), `SensorReading` model (`data_model.py`), and message insert logic (`mqtt_client.py`). Integration tests shall use a real MariaDB connection.

**Source:** RISK-001, NFR-MAIN-001, FR-002, FR-003, FR-008, FR-011
**Priority:** Must Have
**Verification:** `pytest --cov=mqttlogger` reports ≥80%.

---

### FR-TEST-002 — heartbeat Unit Tests

**Statement:** The test suite shall cover `mqttlogger/heartbeat.py` including: thread starts when URL is configured, thread does not start when URL is absent, HTTP push is issued at the configured interval.

**Source:** RISK-001, FR-014, ADR-006
**Priority:** Must Have
**Verification:** `pytest --cov=mqttlogger` includes heartbeat.py in coverage report at ≥80%.

---

### FR-TEST-003 — companion_monitor Unit Tests

**Statement:** The test suite shall cover `companion-monitor/monitor.py` including: `run_check()` missing-sensor detection, `run_check()` unknown-sensor detection, state-transition logic (alert fires once, not every cycle), `load_sensor_config()` parsing, and `push_notification()` failure handling (network error does not crash the monitor).

**Source:** RISK-024, FR-MON-002, FR-MON-004, FR-MON-005, FR-MON-007
**Priority:** Must Have
**Verification:** `pytest --cov=companion-monitor` reports ≥80%.

---

## Open Items

| ID | Description |
|----|-------------|
| CI-OI-001 | Broker (Mosquitto) service container needed for any MQTT integration tests — evaluate whether paho-mqtt on_message tests require a live broker or can be tested with mocks |
| CI-OI-002 | Coverage threshold of 80% applies to both codebases independently; combined coverage must not mask one codebase's gap with the other's surplus |
