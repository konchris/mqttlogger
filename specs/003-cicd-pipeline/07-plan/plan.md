# Implementation Plan — 003-cicd-pipeline

**Feature:** 003-cicd-pipeline
**Date:** 2026-05-10
**Status:** DRAFT
**Branch:** `003-cicd-pipeline`

---

## Goal

Establish a GitHub Actions CI pipeline with automated lint (ruff), test (pytest), and coverage gate (≥80%) for both `mqttlogger/` and `companion-monitor/`. Closes RISK-001, RISK-024, and enforces NFR-MAIN-001.

---

## Scope

Three parallel work streams that are gated on each other in this order:

1. **Test suite — mqttlogger/** (FR-TEST-001, FR-TEST-002)
2. **Test suite — companion-monitor/** (FR-TEST-003)
3. **GitHub Actions pipeline** (FR-CI-001 through FR-CI-005) — wire up after tests pass locally

---

## Technical Context

| Item | Detail |
|------|--------|
| Python version | 3.10 (matches deployment; upgrade to 3.11+ tracked as RISK-003 / separate feature) |
| Test runner | `pytest` |
| Coverage | `pytest-cov` |
| Linter | `ruff` |
| Config file | `pyproject.toml` (single config for ruff, pytest, coverage) |
| CI platform | GitHub Actions (repo is mirrored or will be migrated — confirm before wiring) |
| MariaDB in CI | `services: mariadb` container in workflow |
| MQTT broker in CI | TBD — see CI-OI-001; start with unit tests, add broker service if integration tests require it |

---

## Deliverables

| File | Purpose |
|------|---------|
| `pyproject.toml` | ruff config, pytest config, coverage config |
| `tests/__init__.py` | marks tests as a package |
| `tests/mqttlogger/test_db_connection.py` | config loading, validation, connection string |
| `tests/mqttlogger/test_data_model.py` | SensorReading model, table mapping |
| `tests/mqttlogger/test_mqtt_client.py` | insert(), on_message() parse logic |
| `tests/mqttlogger/test_heartbeat.py` | HeartbeatThread start/skip, HTTP push |
| `tests/companion_monitor/test_monitor.py` | run_check(), load_sensor_config(), push_notification() |
| `.github/workflows/ci.yml` | lint + test + coverage pipeline |

---

## Implementation Steps

### Step 1 — Project config (pyproject.toml)

Create `pyproject.toml` at repo root with:

```toml
[tool.ruff]
line-length = 100
select = ["E", "F", "W", "I"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]

[tool.coverage.run]
source = ["mqttlogger", "companion-monitor"]
omit = ["tests/*", "*/migrations/*"]

[tool.coverage.report]
fail_under = 80
show_missing = true
```

### Step 2 — mqttlogger tests

**`test_db_connection.py`** — unit tests (no DB required):
- `load_config_file()` with valid config → returns dict
- `load_config_file()` with missing required field → raises with field name in message (NFR-USE-001)
- `load_config_file()` with missing file → raises with path in message
- `create_connection_string()` → correct SQLAlchemy URL format

**`test_data_model.py`** — integration tests (real MariaDB):
- `SensorReading` can be committed and queried
- `captured_at` defaults to UTC now

**`test_mqtt_client.py`** — unit + integration:
- `insert()` with valid session → row appears in DB (integration)
- `insert()` with DB error → logs error, does not raise (unit — mock session)
- `on_message()` with known payload → calls insert with correct device/value (unit — mock client)

**`test_heartbeat.py`** — unit tests (mock HTTP):
- `HeartbeatThread` starts when `heartbeat_url` is set
- No thread started when `heartbeat_url` is absent
- Thread issues POST to configured URL (mock `requests.post`)
- Thread is daemon (`thread.daemon == True`)

### Step 3 — companion_monitor tests

**`test_monitor.py`** — unit tests (mock DB responses):

*load_sensor_config():*
- Valid sensors.yml → returns correct monitored and excluded sets
- Missing file → raises with actionable message
- Empty sensors list → returns empty set (not an error)

*run_check() — missing sensor detection:*
- Sensor in monitored set, absent from active set → alert fires, added to alerted_missing
- Sensor already in alerted_missing → no second alert
- Sensor returns to active set → recovery alert fires, removed from alerted_missing

*run_check() — unknown sensor detection:*
- Sensor in active set, not in monitored or excluded → alert fires, added to alerted_unknown
- Sensor in excluded set → no alert
- Sensor in alerted_unknown returns to monitored set → cleared from alerted_unknown

*push_notification():*
- Successful POST → no exception
- Network error (requests.ConnectionError) → logged, does not raise

### Step 4 — GitHub Actions workflow

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
  pull_request:
    branches: [main, develop]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.10"
      - run: pip install ruff
      - run: ruff check .

  test:
    runs-on: ubuntu-latest
    services:
      mariadb:
        image: mariadb:10.11
        env:
          MARIADB_ROOT_PASSWORD: test
          MARIADB_DATABASE: mqttlogger_test
        ports:
          - 3306:3306
        options: --health-cmd="mariadb-admin ping" --health-interval=10s --health-timeout=5s --health-retries=3
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.10"
      - run: pip install -r requirements.txt -r requirements-test.txt
      - run: pytest --cov --cov-report=term-missing
        env:
          TEST_DB_HOST: 127.0.0.1
          TEST_DB_PORT: 3306
          TEST_DB_NAME: mqttlogger_test
          TEST_DB_USER: root
          TEST_DB_PASS: test
```

### Step 5 — requirements-test.txt

```
pytest>=7.0
pytest-cov>=4.0
requests-mock>=1.11
```

---

## Constitution Check

| Principle | Assessment |
|-----------|------------|
| I — No business logic in logger | Not applicable; no changes to logger code |
| II — Config over code | Test DB credentials supplied via environment variables in CI (FR-CI-005) |
| III — Container-first | Tests run on ubuntu-latest in GitHub Actions; integration tests use real MariaDB service container |
| IV — Observability | Not applicable |
| V — Clean shutdown | Not applicable |
| VI — Integration-preferred testing | **Directly addressed** — integration tests use real MariaDB; mock usage limited to HTTP calls (push_notification) and unavoidable paho-mqtt interactions |
| VII — Minimal surface area | pyproject.toml is one file; no new runtime dependencies added to production code |

---

## Open Questions

| ID | Question | Impact |
|----|----------|--------|
| CI-OI-001 | Does `on_message()` testing require a live Mosquitto broker, or is mocking the paho client sufficient? | If broker required, add mosquitto service to CI workflow |
| CI-OI-002 | Is the repo on GitHub (Actions available) or only on Bitbucket? Bitbucket Pipelines has a different YAML format. | Determines workflow file location and syntax |
