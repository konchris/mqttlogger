# mqttlogger — Claude Context

## Project overview

Home automation sensor logger. HomeMatic IP sensors publish via CCU3/RedMatic over MQTT. mqttlogger subscribes and persists readings to MariaDB. Stack runs on `sietchtabr` (mini PC, not Raspberry Pi) via Docker Compose.

## Completed SE features

- **`002-mqttlogger-baseline`** — INCOSE SE baseline (Phases 0–3). **CLOSED — merged to main 2026-05-10.**
- **`003-cicd-pipeline`** — CI/CD pipeline. **CLOSED — merged to main 2026-05-10.**
- **`004-remove-init-legacy`** — removed dead code from `mqttlogger/__init__.py`. **CLOSED — merged to main 2026-05-16.**
- **`005-schema-audit`** — schema reference document + `db/initial-schema.sql`. **CLOSED — merged to main 2026-05-16.**
- **`007-python312-upgrade`** — Python 3.10 → 3.12 runtime upgrade. **CLOSED — merged to main 2026-05-16.**

---

## Current state

**Active feature branch: `feature/009-schema-evolution`** — SE Phase 1 in progress (W-003 schema migration).

**Paused: `feature/008-grafana-dashboard`** — SE Phase 1 complete; OPT-A (Grafana) and OPT-B (Metabase) docker-compose setup committed; IP-001 evaluation deferred until schema is clean. Resumes after 009 merges; 008 will rebase onto updated develop and rebuild dashboard queries against the new schema.

**Decision record (2026-05-17):** 009 was promoted ahead of 008 because a clean schema removes the ergonomic advantage of 3rd-party dashboard tools (Grafana/Metabase), making a homegrown dashboard a genuine option. Evaluating dashboard tools before the schema is clean would bias the comparison.

**W-003 scope (resolved):**
- Merge `currentdate` (Date) + `currenttime` (Time) → `captured_at DATETIME`
- Add `location TEXT` (derived from MQTT topic levels 3–4, e.g. `indoor/attic`)
- Add `measurement_type TEXT` (derived from MQTT topic level 5, e.g. `temperature`)
- Keep `device TEXT` (full MQTT topic) — retained as canonical source; a single location can have multiple devices with the same measurement type (e.g. thermostat + radiators all reporting temperature)

Next candidates (after 009 + 008):

- **RISK-012**: evaluate RedMatic startup zero suppression (OI-004)
- **RISK-015**: configure BIOS power-restore on sietchtabr (OI-001)

W-001 and W-002 were completed in feature `006-log-and-topic-fixes` (merged 2026-05-16).

### Architecture status — COMPLETE (2026-05-10)

**OPT-A — Uptime Kuma heartbeat push** (process layer)
- Heartbeat emitted from `mqttlogger/heartbeat.py` every 60 s to Uptime Kuma push endpoint
- Uptime Kuma notifies via self-hosted ntfy (`http://ntfy:80/mqttlogger-alerts`)
- Fault injection: 3/3 runs detected, mean 93 s, max 120 s ✓; 24h baseline PASS
- Covers: **RISK-016** (crash detection) — ≤120 s latency; documented in ADR-006

**OPT-B — Companion DB monitor** (sensor layer)
- `companion-monitor/monitor.py` polls MariaDB every 5 min, 600-min gap window
- Dual-direction check: missing periodic sensors → alert; new unknown sensors → alert
- 13 periodic sensors monitored (temp/humidity); 15 event-driven sensors excluded
- 24h baseline PASS — 4 genuine alerts (attic humidity recovery + 3 new dining room sensors)
- Covers: **RISK-013** (sensor topology changes silently); documented in ADR-002, ADR-007

**RISK-014** (historical completeness): deferred to a later iteration.

**Key open risks from architecture phase:**
- RISK-020: heartbeat proves liveness, not capture activity (ADR-006 consequence)
- RISK-023: ntfy is LAN-only — operator off home network misses notifications

RISK-001 (no CI/CD) — **CLOSED** by 003-cicd-pipeline.
RISK-024 (no automated tests for companion_monitor) — **Carried Forward** to a future iteration.

## Repository layout

```
app.py                        # Main entry point — MQTT client, heartbeat, LWT
mqttlogger/
  mqtt_client.py              # on_connect, on_message, insert
  heartbeat.py                # OPT-A: background HTTP push thread
  db_connection.py            # load_config_file, create_connection_string
  data_model.py               # SensorReading SQLAlchemy model (table: sensorreadings)
companion-monitor/
  monitor.py                  # OPT-B: gap detection + dual-direction config check
  bootstrap_sensors.py        # One-shot: query DB history → sensors.yml
  sensors.yml                 # Deployment config (gitignored — edit on sietchtabr)
  sensors.yml.example         # Template
config.json                   # Deployment config (gitignored — edit on sietchtabr)
config.json.example           # Template with all supported keys including heartbeat_url
docker-compose.yml            # All services: mqtt, mqtt_logger, mariadb,
                              # uptime_kuma (OPT-A), ntfy, companion_monitor (OPT-B)
db/
  initial-schema.sql            # Version-controlled DDL artifact (generated from data_model.py)
specs/system/                   # Living SE artifacts (RTM, risk register, V&V plan/results, architecture, etc.)
specs/005-schema-audit/         # Feature SE artifacts (gate reports, tasks, plan, explore)
```

## Stack on sietchtabr

```
sietchtabr:~/docker/mqttlogger
```

Services: `mqtt`, `mqtt_logger`, `mariadb`, `uptime_kuma` (port 3001), `ntfy` (port 8080), `companion_monitor`

Logs: `docker compose exec mqtt_logger tail -f /code/logs/mqttlogger.log`
(mqtt_logger writes to rotating file, not stdout — `docker compose logs mqtt_logger` shows nothing)
**Log timestamps are UTC.** Add 2 h for CEST.

`docker compose logs uptime_kuma` works normally (Node.js writes to stdout).

## Key known issues / constraints

- `mosquitto/config/mosquitto.conf: Permission denied` warning on `git status` on sietchtabr — pre-existing filesystem permission issue, harmless
- CCU3/RedMatic publishes zero values for all sensors on startup (RISK-012)
- `config.json` previously tracked with credentials in git history — **scrubbed from history 2026-05-11** (git filter-repo; both secrets replaced)
- BIOS auto-restart after power loss not configured on sietchtabr (OI-001)
- attic/thermostat_humidity was silent >25 h on 2026-05-09 — resolved itself; monitor if it recurs
- **After rotating DB credentials**, run `ALTER USER 'mqttlogger'@'%' IDENTIFIED BY '<new_password>'; FLUSH PRIVILEGES;` inside the mariadb container — the linuxserver/mariadb image does not reapply `MYSQL_PASSWORD` from the env if the data volume already exists.
- **Uptime Kuma push monitor interval** should be 120 s (not 60 s) so a single late heartbeat doesn't trigger a false alert.
- **Heartbeat 404 after `docker compose` restart**: `mqtt_logger` is on three networks and can get corrupt routing tables in its network namespace, causing 404s to `uptime_kuma` even though DNS resolves correctly. Fix: `docker compose restart mqtt_logger`.

## SE constitution

`.specify/memory/constitution.md` — read before invoking any SE skill.

## Repository

GitHub: https://github.com/konchris/mqttlogger
CI: GitHub Actions (`.github/workflows/ci.yml`) — lint (ruff) + test + coverage ≥80% on every push.

## Branching

**Flow:** `feature/<name>` → `develop` → `main`

**Rules (enforced via GitHub branch protection on both `main` and `develop`):**
- No direct pushes — all changes via PR
- Both CI jobs (`Lint (ruff)` and `Test`) must pass before merge
- Branch must be up-to-date with the target before merging
- Force pushes and deletions are blocked

**Convention:** a feature branch is not merged until all four conditions are met:
1. CI is green on the feature branch
2. Phase 5 gate PASS artifact committed to the feature branch
3. Phase 6 V&V closure artifact committed to the feature branch
4. Deployment on `sietchtabr` performed **from the feature branch** (not after merge)

The PR is opened only after all four conditions are met. The CI gate-check job enforces condition 2.

Active feature: `feature/009-schema-evolution` (W-003 schema migration). Paused: `feature/008-grafana-dashboard`.
