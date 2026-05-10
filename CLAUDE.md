# mqttlogger — Claude Context

## Project overview

Home automation sensor logger. HomeMatic IP sensors publish via CCU3/RedMatic over MQTT. mqttlogger subscribes and persists readings to MariaDB. Stack runs on `sietchtabr` (mini PC, not Raspberry Pi) via Docker Compose.

## Current SE feature

**`002-mqttlogger-baseline`** — INCOSE SE baseline analysis of the existing system.

- Phase 0 (Problem Space): **PASS**
- Phase 1 (Solution Space): **PASS** — gate report at `specs/002-mqttlogger-baseline/gate-reports/gate-1-pass.md`
- Phase 2 (Exploration): **PASS** — both OPT-A and OPT-B selected; explore-summary at `specs/002-mqttlogger-baseline/03-explore/explore-summary.md`
- Phase 3 (Architecture): **COMPLETE** — 6 views, 7 ADRs, arc42 narrative, RTM; see `specs/002-mqttlogger-baseline/05-architecture/`
- Phase 4+: not yet started

Active branch: **`002-mqttlogger-baseline-ip001`** (IP-001/IP-002/Phase 3 complete)

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
- RISK-024: `companion_monitor` has no automated tests (Constitution Principle VI gap)

**Next step:** Phase 4+ (detailed design) or CI/CD pipeline (TBD-003) to close RISK-001/RISK-024.

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
(mqtt_logger writes to rotating file, not stdout — `docker compose logs` shows nothing)

## Key known issues / constraints

- `mosquitto/config/mosquitto.conf: Permission denied` warning on `git status` on sietchtabr — pre-existing filesystem permission issue, harmless
- CCU3/RedMatic publishes zero values for all sensors on startup (RISK-012)
- `config.json` previously tracked with credentials in git history (RISK-002, TBD-004)
- BIOS auto-restart after power loss not configured on sietchtabr (OI-001)
- attic/thermostat_humidity was silent >25 h on 2026-05-09 — resolved itself; monitor if it recurs

## SE constitution

`.specify/memory/constitution.md` — read before invoking any SE skill.

## Branching

Feature branches → `develop` → `main`. Current feature branch: `002-mqttlogger-baseline-ip001`.
