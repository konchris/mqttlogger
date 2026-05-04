---

description: "Task list for Core MQTT Sensor Logging Service remediation and specification compliance"
---

# Tasks: Core MQTT Sensor Logging Service

**Input**: Design documents from `specs/001-core-mqtt-logger/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Integration tests are included — the existing `tests/conftest.py` uses a real broker
(`test.mosquitto.org`) and the constitution mandates integration-preferred testing (Principle VI).
Test stubs (`assert False`) in `tests/test_mqtt_client.py` must be replaced.

**Organization**: Phase 2 (Foundational) fixes pre-constitution defects that block all story
verification. Phases 3–7 map to the five user stories from spec.md.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1–US5)
- Include exact file paths in all task descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the development environment is operational before any changes.

- [ ] T001 Install Python dependencies and verify pytest discovers tests: `pip install -r requirements.txt && pytest --collect-only tests/`
- [ ] T002 [P] Build Docker image and verify stack starts: `docker compose build && docker compose up -d` — confirm all three services reach running state

**Checkpoint**: Local environment working — proceed to foundational fixes.

---

## Phase 2: Foundational (Constitution Compliance — Blocks All Story Verification)

**Purpose**: Fix pre-existing defects identified in the Constitution Check (plan.md) that prevent
the container from starting or tests from passing. ALL must be complete before user story
validation begins.

**⚠️ CRITICAL**: No user story can be independently verified until this phase is complete.

- [ ] T003 Add `COPY constants.py ./` after `COPY app.py config.json ./` in `Dockerfile` to fix `ModuleNotFoundError` on container startup (Constitution III, Principle IV)
- [ ] T004 Fix typo: change `sys.exti(0)` → `sys.exit(0)` at `app.py` line 83 in the `handle_sigterm` function (Constitution V, FR-007)
- [ ] T005 [P] Document `persist.sh` with a header comment explaining its purpose, or remove the file from the repo root if it is unused (Constitution VII)
- [ ] T006 [P] Update `declarative_base` import from `sqlalchemy.ext.declarative` to `sqlalchemy.orm` in `mqttlogger/data_model.py` line 12 (research.md Decision 3)
- [ ] T007 [P] Remove deprecated `MetaData(engine)` constructor call in `mqttlogger/data_model.py:create()` — use `Base.metadata.create_all(engine)` instead

**Checkpoint**: Container starts cleanly, SIGTERM exits correctly, no deprecation warnings — user
story implementation and tests can now begin.

---

## Phase 3: User Story 1 — Automatic Sensor Data Capture (Priority: P1) 🎯 MVP

**Goal**: Every sensor message is stored as a complete record within 5 seconds of publication.

**Independent Test**: Publish a float reading and a boolean reading to the test broker. Confirm
both records exist in the database within 5 seconds with correct device address and value.

### Implementation for User Story 1

- [ ] T008 [US1] Wrap payload conversion in `on_message` with `try/except (ValueError, TypeError)` — log error with raw payload + device address and return without calling `client.insert()` (FR-013) in `mqttlogger/mqtt_client.py`
- [ ] T009 [US1] Wrap `session.add()` + `session.commit()` in `insert()` with `try/except Exception` — log error with device address, value, and failure cause; do not raise (FR-014) in `mqttlogger/mqtt_client.py`

### Tests for User Story 1

- [ ] T010 [P] [US1] Replace `assert False` stub: write integration test `test_send_floats` publishing a numeric payload and asserting the DB record matches value + device address in `tests/test_mqtt_client.py`
- [ ] T011 [P] [US1] Write integration test `test_send_boolean_true` publishing `b'true'` and asserting `reading == 1.0` in `tests/test_mqtt_client.py`
- [ ] T012 [P] [US1] Write integration test `test_send_boolean_false` publishing `b'false'` and asserting `reading == 0.0` in `tests/test_mqtt_client.py`
- [ ] T013 [US1] Write integration test `test_malformed_payload_discarded` publishing an unparseable payload (e.g., `b'not-a-number'`) and asserting no new DB record is written and service continues to accept messages in `tests/test_mqtt_client.py`

**Checkpoint**: `pytest tests/test_mqtt_client.py` passes for all US1 tests. US1 is fully
functional and independently testable.

---

## Phase 4: User Story 2 — Service Continuity Across Restarts (Priority: P1)

**Goal**: Service restarts automatically after power cycle and reconnects after broker outage
without operator intervention.

**Independent Test**: Restart the broker container while the logger is running. Confirm the
logger reconnects and stores the next published message without any operator action.

### Implementation for User Story 2

- [ ] T014 [US2] Update `mqtt_logger.depends_on` in `docker-compose.yml` to add `condition: service_healthy` for the `mariadb` dependency — ensures DB is ready before the logger attempts its first connection (FR-012)
- [ ] T015 [US2] Write integration test `test_reconnect_after_disconnect` that calls `client.disconnect()` on the test client and verifies messages published after reconnect are still stored in `tests/test_mqtt_client.py`

**Checkpoint**: Broker restart test passes. Stack restarts cleanly after reboot. US2 independently
verified.

---

## Phase 5: User Story 3 — Graceful Service Shutdown (Priority: P2)

**Goal**: Stop signal causes clean disconnect and exit within 10 seconds with no orphaned broker
connections.

**Independent Test**: Send SIGTERM to the running service process. Confirm exit within 10 seconds
and no stale connections on the broker.

### Implementation for User Story 3

- [ ] T016 [US3] Write integration test `test_clean_disconnect` that calls `client.loop_stop()` + `client.disconnect()` and asserts the client is no longer connected to the broker in `tests/test_mqtt_client.py`
- [ ] T017 [P] [US3] Add inline comment at `app.py` line 88 documenting that `loop_forever()` handles SIGINT natively (stops the loop cleanly without a custom handler)

**Checkpoint**: T004 (sys.exit fix) + T016 together verify US3. Clean shutdown confirmed.

---

## Phase 6: User Story 4 — Operational Diagnostics via Logs (Priority: P2)

**Goal**: Connection, subscription, message, write, and error events are all logged to bounded
rotating files; verbose mode available via flag.

**Independent Test**: Point the service at an unreachable broker, read the log file, and confirm
the failure is recorded. Confirm log files do not grow unboundedly.

### Implementation for User Story 4

- [ ] T018 [US4] Add an inline comment at `app.py` lines 32–33 documenting that the log rotation parameters (2 MB per file, 5 files maximum) were chosen per `specs/001-core-mqtt-logger/research.md` Decision 4
- [ ] T019 [P] [US4] Write integration test `test_debug_flag_enables_verbose_logging` that instantiates the logger with `--debug` and asserts debug-level entries appear in log output in `tests/test_mqtt_client.py`

**Checkpoint**: Log files written inside container (Dockerfile fix from T003 is prerequisite).
Rotating handler parameters verified. US4 independently verified.

---

## Phase 7: User Story 5 — Zero-Code Deployment Configuration (Priority: P3)

**Goal**: Service is deployable by modifying only `config.json` — no code changes required.
Missing or malformed configuration exits immediately with a clear error.

**Independent Test**: Start the service with `config.json` deleted. Confirm non-zero exit with a
human-readable error message identifying the missing file. Then restore config and confirm the
service starts successfully.

### Implementation for User Story 5

- [ ] T020 [US5] Replace `assert config_path.exists()` in `mqttlogger/db_connection.py:load_config_file` with an explicit `if not config_path.exists(): raise FileNotFoundError(f"Configuration file not found: {config_path}")` (FR-016)
- [ ] T021 [US5] Add validation in `mqttlogger/db_connection.py:load_config_file` that all required keys (`mqtt_server_ip`, `mqtt_server_port`, `db_ip`, `db_port`, `db_user`, `db_password`, `db_database`) are present — raise `KeyError` with a human-readable message listing the missing key(s) (FR-016)

### Tests for User Story 5

- [ ] T022 [P] [US5] Write unit test `test_missing_config_file_raises` in `tests/test_db_connection.py` asserting `load_config_file` raises `FileNotFoundError` for a non-existent path
- [ ] T023 [P] [US5] Write unit test `test_malformed_json_raises` in `tests/test_db_connection.py` asserting `load_config_file` raises `json.JSONDecodeError` for a file containing invalid JSON
- [ ] T024 [US5] Write unit test `test_missing_required_key_raises` in `tests/test_db_connection.py` asserting `load_config_file` raises `KeyError` when a required config key is absent

**Checkpoint**: `pytest tests/test_db_connection.py` passes. Config validation confirmed. US5
independently verified.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories or overall project quality.

- [ ] T025 [P] Update `README.md`: replace the Bitbucket placeholder content with a project overview, link to `specs/001-core-mqtt-logger/quickstart.md`, and link to `specs/001-core-mqtt-logger/spec.md`
- [ ] T026 Normalize terminology: replace all occurrences of "device identifier" with "device address" in docstrings and inline comments across `mqttlogger/mqtt_client.py` and `mqttlogger/data_model.py` (data-model.md canonical naming)
- [ ] T027 [P] Fix `docker-compose.yml` `mqtt_logger` volume: replace `./:/code` with `./config.json:/code/config.json` to prevent host/container dependency divergence in production deployments

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — **BLOCKS all user story verification**
- **User Stories (Phases 3–7)**: All depend on Foundational completion
  - US1 (Phase 3) and US2 (Phase 4) are both P1 — can proceed in parallel after Phase 2
  - US3 (Phase 5) depends on T004 from Phase 2 — can start alongside US1/US2
  - US4 (Phase 6) depends on T003 from Phase 2 — can start alongside US1/US2
  - US5 (Phase 7) is P3 — start after US1/US2 complete
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: No dependencies on other stories — start after Phase 2
- **US2 (P1)**: No dependencies on other stories — start after Phase 2 (parallel with US1)
- **US3 (P2)**: Depends on T004 only (already in Phase 2) — start after Phase 2
- **US4 (P2)**: Depends on T003 only (already in Phase 2) — start after Phase 2
- **US5 (P3)**: No dependencies on other stories — start after Phase 2 (but lower priority)

### Within Each User Story

- Implementation tasks before test tasks within the same story where the implementation enables the test
- T008 (malformed payload handler) before T013 (test for malformed payload)
- T009 (DB failure handler) before tests that exercise DB failure paths

---

## Parallel Opportunities

### Phase 2 (Foundational) — Run Together

```
T003  Dockerfile constants.py fix
T004  sys.exit typo fix             ← can run in parallel (different files)
T005  persist.sh document/remove    ← can run in parallel (different file)
T006  SQLAlchemy declarative_base   ← can run in parallel (different file)
T007  MetaData deprecation fix      ← depends on T006 (same file, sequence within data_model.py)
```

### Phase 3 (US1 Tests) — Launch Together

```
T010  test_send_floats
T011  test_send_boolean_true        ← all parallel (same file, independent test functions)
T012  test_send_boolean_false
```

### Phases 3 + 4 — Run After Phase 2 Completes

```
Phase 3 (US1) — P1
Phase 4 (US2) — P1                 ← US1 and US2 can proceed in parallel
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — container must start before anything can be tested)
3. Complete Phase 3: US1 — Data Capture (T008–T013)
4. **STOP and VALIDATE**: Run `pytest tests/test_mqtt_client.py`, publish test messages, confirm DB records
5. If validated: container starts, messages are stored, malformed payloads are discarded safely

### Incremental Delivery

1. Phase 1 + Phase 2 → Container starts, SIGTERM works, no deprecation warnings
2. Phase 3 (US1) → Data capture verified with passing integration tests (MVP!)
3. Phase 4 (US2) → Reconnect and restart verified
4. Phase 5 (US3) → Graceful shutdown verified
5. Phase 6 (US4) → Log bounds and debug mode verified
6. Phase 7 (US5) → Config validation verified
7. Phase 8 (Polish) → README updated, terminology normalized, volume mount fixed

---

## Notes

- [P] tasks = different files or independent test functions, safe to run in parallel
- [Story] label maps each task to a user story from spec.md for traceability
- T003 and T004 (Phase 2) are the highest-priority fixes — without them the container cannot
  start and the SIGTERM handler crashes
- Tests require internet access to `test.mosquitto.org`; for offline testing, spin up a local
  Mosquitto container and update `test_mqtt_server` fixture in `tests/conftest.py`
- `tests/test_db_connection.py` (US5 tests) does not exist yet — create it alongside T022
