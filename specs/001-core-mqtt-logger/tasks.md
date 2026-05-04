---

description: "Task list for Core MQTT Sensor Logging Service remediation and specification compliance"
---

# Tasks: Core MQTT Sensor Logging Service

**Input**: Design documents from `specs/001-core-mqtt-logger/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, checklists/spec-review.md ✅

**Tests**: Integration tests are included — the existing `tests/conftest.py` uses a real broker
(`test.mosquitto.org`) and the constitution mandates integration-preferred testing (Principle VI).
Test stubs (`assert False`) in `tests/test_mqtt_client.py` must be replaced.

**Organization**: Phase 2 (Foundational) fixes both pre-constitution code defects and spec
ambiguities surfaced by the requirements review checklist (CHK001–CHK026) before any story
verification begins. Phases 3–7 map to the five user stories from spec.md.

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

## Phase 2: Foundational (Constitution Compliance + Spec Hardening — Blocks All Story Verification)

**Purpose**: Fix pre-existing code defects (Constitution Check violations from plan.md) and
resolve spec ambiguities surfaced by the requirements review checklist. ALL must be complete
before user story validation begins.

**⚠️ CRITICAL**: No user story can be independently verified until this phase is complete.

### 2a — Code Defects (Constitution Compliance)

- [ ] T003 Add `COPY constants.py ./` after `COPY app.py config.json ./` in `Dockerfile` to fix `ModuleNotFoundError` on container startup (Constitution III, Principle IV)
- [ ] T004 Fix typo: change `sys.exti(0)` → `sys.exit(0)` at `app.py` line 83 in the `handle_sigterm` function — note: already applied, verify the fix is present (Constitution V, FR-007)
- [ ] T005 [P] Document `persist.sh` with a header comment explaining its purpose, or remove the file from the repo root if it is unused (Constitution VII)
- [ ] T006 [P] Update `declarative_base` import from `sqlalchemy.ext.declarative` to `sqlalchemy.orm` in `mqttlogger/data_model.py` line 12 (research.md Decision 3)
- [ ] T007 [P] Remove deprecated `MetaData(engine)` constructor call in `mqttlogger/data_model.py:create()` — replace with `Base.metadata.create_all(engine)`

### 2b — Spec Hardening (Checklist Findings CHK004, CHK006, CHK010–CHK012, CHK024)

- [ ] T008 [P] Resolve integer vs. float ambiguity: update FR-003 in `specs/001-core-mqtt-logger/spec.md` to specify "1.0 for true, 0.0 for false" (float, not integer) to align with `contracts/mqtt-topic-schema.md` and `data-model.md` `reading` column type (CHK006, CHK010)
- [ ] T009 [P] Resolve data-loss vs. shutdown guarantee conflict in `specs/001-core-mqtt-logger/spec.md`: add a clarifying sentence to the Edge Cases section specifying that the "data loss accepted" policy applies to runtime DB failures but NOT to in-flight writes during a graceful shutdown (which FR-007 MUST complete) (CHK011)
- [ ] T010 [P] Normalize terminology in `specs/001-core-mqtt-logger/spec.md`: replace all occurrences of "device identifier" with "device address" to match the canonical term established in `data-model.md` (CHK012)
- [ ] T011 [P] Add timezone specification to FR-002 in `specs/001-core-mqtt-logger/spec.md`: clarify that `currentdate` and `currenttime` are recorded in the host system's local timezone (CHK004)
- [ ] T012 [P] Update `specs/001-core-mqtt-logger/contracts/db-schema.md`: add an explanatory note under the Column Reference table clarifying that `currentdate`, `currenttime`, `device`, and `reading` are nullable at the DDL level due to ORM default behavior, but FR-002 requires the application to always supply values — NULL values indicate a data integrity error (CHK024)

**Checkpoint**: Container starts cleanly, SIGTERM exits correctly, no deprecation warnings, spec
ambiguities resolved — user story implementation and tests can now begin.

---

## Phase 3: User Story 1 — Automatic Sensor Data Capture (Priority: P1) 🎯 MVP

**Goal**: Every sensor message is stored as a complete record within 5 seconds of publication.

**Independent Test**: Publish a float reading and a boolean reading to the test broker. Confirm
both records exist in the database within 5 seconds with correct device address and value.

### Implementation for User Story 1

- [ ] T013 [US1] Wrap payload conversion in `on_message` with `try/except (ValueError, TypeError)` — log an ERROR entry with raw payload + device address and return without calling `client.insert()` (FR-013) in `mqttlogger/mqtt_client.py`
- [ ] T014 [US1] Wrap `session.add()` + `session.commit()` in `insert()` with `try/except Exception` — log an ERROR entry with device address, value, and failure cause; do not raise (FR-014) in `mqttlogger/mqtt_client.py`

### Tests for User Story 1

- [ ] T015 [P] [US1] Replace `assert False` stub: write integration test `test_send_floats` publishing a numeric payload and asserting the DB record matches value + device address in `tests/test_mqtt_client.py`
- [ ] T016 [P] [US1] Write integration test `test_send_boolean_true` publishing `b'true'` and asserting `reading == 1.0` in `tests/test_mqtt_client.py`
- [ ] T017 [P] [US1] Write integration test `test_send_boolean_false` publishing `b'false'` and asserting `reading == 0.0` in `tests/test_mqtt_client.py`
- [ ] T018 [US1] Write integration test `test_malformed_payload_discarded` publishing an unparseable payload (e.g., `b'not-a-number'`) and asserting no new DB record is written and service continues to accept messages in `tests/test_mqtt_client.py`

**Checkpoint**: `pytest tests/test_mqtt_client.py::test_send_floats tests/test_mqtt_client.py::test_send_boolean_true tests/test_mqtt_client.py::test_send_boolean_false tests/test_mqtt_client.py::test_malformed_payload_discarded` all pass. US1 independently verified.

---

## Phase 4: User Story 2 — Service Continuity Across Restarts (Priority: P1)

**Goal**: Service restarts automatically after power cycle and reconnects after broker outage
without operator intervention.

**Independent Test**: Restart the broker container while the logger is running. Confirm the
logger reconnects and stores the next published message without any operator action.

### Implementation for User Story 2

- [ ] T019 [US2] Update `mqtt_logger.depends_on` in `docker-compose.yml` to add `condition: service_healthy` for the `mariadb` dependency — ensures DB is ready before the logger attempts its first connection (FR-012)
- [ ] T020 [US2] Write integration test `test_reconnect_after_disconnect` that calls `client.disconnect()` on the test client and verifies messages published after reconnect are still stored in `tests/test_mqtt_client.py`

**Checkpoint**: Broker restart test passes. Stack restarts cleanly after reboot. US2 independently
verified.

---

## Phase 5: User Story 3 — Graceful Service Shutdown (Priority: P2)

**Goal**: Stop signal causes clean disconnect and exit within 10 seconds with no orphaned broker
connections.

**Independent Test**: Send SIGTERM to the running service process. Confirm exit within 10 seconds
and no stale connections on the broker.

### Implementation for User Story 3

- [ ] T021 [US3] Write integration test `test_clean_disconnect` that calls `client.loop_stop()` + `client.disconnect()` and asserts the client is no longer connected to the broker in `tests/test_mqtt_client.py`
- [ ] T022 [P] [US3] Add inline comment at `app.py` line 88 documenting that `loop_forever()` handles SIGINT natively (stops the loop cleanly without a custom handler)

**Checkpoint**: T004 (sys.exit fix) + T021 together verify US3. Clean shutdown confirmed.

---

## Phase 6: User Story 4 — Operational Diagnostics via Logs (Priority: P2)

**Goal**: Connection, subscription, message, write, and error events are all logged to bounded
rotating files; verbose mode available via flag.

**Independent Test**: Point the service at an unreachable broker, read the log file, and confirm
the failure is recorded. Confirm log files do not grow unboundedly.

### Implementation for User Story 4

- [ ] T023 [US4] Add an inline comment at `app.py` lines 32–33 documenting the log rotation parameters (2 MB per file, 5 files maximum) and their rationale per `specs/001-core-mqtt-logger/research.md` Decision 4
- [ ] T024 [P] [US4] Write integration test `test_debug_flag_enables_verbose_logging` that instantiates the logger with `--debug` and asserts debug-level entries appear in log output in `tests/test_mqtt_client.py`

**Checkpoint**: Log files written inside container (T003 Dockerfile fix prerequisite). Rotating
handler parameters documented. US4 independently verified.

---

## Phase 7: User Story 5 — Zero-Code Deployment Configuration (Priority: P3)

**Goal**: Service is deployable by modifying only `config.json` — no code changes required.
Missing or malformed configuration exits immediately with a clear error.

**Independent Test**: Start the service with `config.json` deleted. Confirm non-zero exit with a
human-readable error message identifying the missing file. Then restore config and confirm the
service starts successfully.

### Implementation for User Story 5

- [ ] T025 [US5] Replace `assert config_path.exists()` in `mqttlogger/db_connection.py:load_config_file` with `if not config_path.exists(): raise FileNotFoundError(f"Configuration file not found: {config_path}")` (FR-016)
- [ ] T026 [US5] Add validation in `mqttlogger/db_connection.py:load_config_file` that all required keys (`mqtt_server_ip`, `mqtt_server_port`, `db_ip`, `db_port`, `db_user`, `db_password`, `db_database`) are present — raise `KeyError` with a human-readable message listing the missing key(s) (FR-016)

### Tests for User Story 5

- [ ] T027 [P] [US5] Write unit test `test_missing_config_file_raises` in `tests/test_db_connection.py` asserting `load_config_file` raises `FileNotFoundError` for a non-existent path
- [ ] T028 [P] [US5] Write unit test `test_malformed_json_raises` in `tests/test_db_connection.py` asserting `load_config_file` raises `json.JSONDecodeError` for a file containing invalid JSON
- [ ] T029 [US5] Write unit test `test_missing_required_key_raises` in `tests/test_db_connection.py` asserting `load_config_file` raises `KeyError` when a required config key is absent

**Checkpoint**: `pytest tests/test_db_connection.py` passes. Config validation confirmed. US5
independently verified.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories or overall project quality.

- [ ] T030 [P] Update `README.md`: replace the Bitbucket placeholder content with a project overview, link to `specs/001-core-mqtt-logger/quickstart.md`, and link to `specs/001-core-mqtt-logger/spec.md`
- [ ] T031 [P] Fix `docker-compose.yml` `mqtt_logger` volume: replace `./:/code` with `./config.json:/code/config.json` to prevent host/container dependency divergence in production deployments
- [ ] T032 Run `pytest tests/` to confirm all tests pass after all implementation phases complete; address any failures before merging to `develop`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — **BLOCKS all user story verification**
  - 2a (Code defects) and 2b (Spec hardening) can run in parallel with each other
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
- **US5 (P3)**: No dependencies on other stories — start after Phase 2 (lower priority)

### Within Each User Story

- Implementation tasks (T013, T014) before tests that require the implementation (T018)
- T015, T016, T017 can run in parallel (independent test functions, same file)

---

## Parallel Opportunities

### Phase 2 — Run Together

```
T003  Dockerfile constants.py fix
T004  Verify sys.exit fix              ← different files, all parallel
T005  persist.sh document/remove
T006  SQLAlchemy declarative_base
T008  Spec FR-003 float fix
T009  Spec data-loss/shutdown conflict
T010  Spec terminology normalize
T011  Spec timezone add
T012  Contract db-schema nullable note
```
*(T007 depends on T006 — same file)*

### Phase 3 (US1 Tests) — Launch Together After T013, T014

```
T015  test_send_floats
T016  test_send_boolean_true           ← all parallel (independent test functions)
T017  test_send_boolean_false
```

### Phases 3 + 4 — Run After Phase 2 Completes

```
Phase 3 (US1) — P1
Phase 4 (US2) — P1                    ← US1 and US2 can proceed in parallel
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — container must start; spec must be consistent)
3. Complete Phase 3: US1 — Data Capture (T013–T018)
4. **STOP and VALIDATE**: Run `pytest tests/test_mqtt_client.py`, publish test messages, confirm DB records
5. If validated: container starts, messages are stored, malformed payloads are discarded safely

### Incremental Delivery

1. Phase 1 + Phase 2 → Container starts, SIGTERM works, no deprecation warnings, spec consistent
2. Phase 3 (US1) → Data capture verified with passing integration tests (MVP!)
3. Phase 4 (US2) → Reconnect and restart verified
4. Phase 5 (US3) → Graceful shutdown verified
5. Phase 6 (US4) → Log bounds and debug mode verified
6. Phase 7 (US5) → Config validation verified
7. Phase 8 (Polish) → README updated, volume mount fixed, full test suite passes

---

## Notes

- [P] tasks = different files or independent test functions, safe to run in parallel
- [Story] label maps each task to a user story from spec.md for traceability
- T003 and T004 (Phase 2) remain the highest-priority code fixes — without them the container
  cannot start and the SIGTERM handler is broken
- T008–T012 (Phase 2b) resolve spec ambiguities that the checklist (CHK004, CHK006, CHK010–CHK012,
  CHK024) flagged as blockers for unambiguous implementation
- Tests require internet access to `test.mosquitto.org`; for offline testing, spin up a local
  Mosquitto container and update the `test_mqtt_server` fixture in `tests/conftest.py`
- `tests/test_db_connection.py` (US5 tests, T027–T029) does not exist yet — create it alongside T027
