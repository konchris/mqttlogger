# mqttlogger — Claude Context

## Project overview

Home automation sensor logger. HomeMatic IP sensors publish via CCU3/RedMatic over MQTT. mqttlogger subscribes and persists readings to MariaDB. Stack runs on `sietchtabr` (mini PC, not Raspberry Pi) via Docker Compose.

## Previous SE features

- **`002-mqttlogger-baseline`** — INCOSE SE baseline (Phases 0–3). **CLOSED — merged to main 2026-05-10.**
- **`003-cicd-pipeline`** — CI/CD pipeline. **CLOSED — merged to main 2026-05-10.**

---

## Current state

No active feature branch. Next candidates:

- Remove `mqttlogger/__init__.py` legacy code (raises coverage above 80% headroom)
- Schema audit (RISK-019 / NFR-INT-001)

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

RISK-001 (no CI/CD) and RISK-024 (no automated tests for companion_monitor) — **CLOSED** by 003-cicd-pipeline.

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
specs/002-mqttlogger-baseline/ # SE artifacts for current feature
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

**Convention:** a feature branch is not merged until CI is green *and* the change has been verified on `sietchtabr` (deployment test is manual — the live broker and MariaDB cannot be replicated in CI).

No active feature branch.
