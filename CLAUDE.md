# mqttlogger — Claude Context

## Project overview

Home automation sensor logger. HomeMatic IP sensors publish via CCU3/RedMatic over MQTT. mqttlogger subscribes and persists readings to MariaDB. Stack runs on `sietchtabr` (mini PC, not Raspberry Pi) via Docker Compose.

## Current SE feature

**`002-mqttlogger-baseline`** — INCOSE SE baseline analysis of the existing system.

- Phase 0 (Problem Space): **PASS**
- Phase 1 (Solution Space): **PASS** — gate report at `specs/002-mqttlogger-baseline/gate-reports/gate-1-pass.md`
- Phase 2+: not yet started

Active branch: **`002-mqttlogger-baseline-ip001`** (IP-001 exploration prototypes)

### IP-001 exploration status (as of 2026-05-10)

Two options under parallel evaluation:

**OPT-A — Uptime Kuma heartbeat push**
- Heartbeat emitted from `mqttlogger/heartbeat.py` every 60 s to Uptime Kuma push endpoint
- Uptime Kuma notifies via self-hosted ntfy (`http://ntfy:80/mqttlogger-alerts`)
- Fault injection (TASK-A-005): 3/3 runs detected, mean 93 s, max 120 s ✓
- 24h false positive baseline (TASK-A-006): **PASS** — zero spurious alerts

**OPT-B — Companion DB monitor**
- `companion-monitor/monitor.py` polls MariaDB every 5 min, 600-min gap window
- Dual-direction check: missing periodic sensors → alert; new unknown sensors → alert
- 13 periodic sensors monitored (temp/humidity); 15 event-driven sensors excluded
- 24h false positive baseline (TASK-B-006): **PASS** — zero spurious alerts; all 4 alerts were genuine (attic humidity recovery + 3 new dining room sensors surfaced automatically)
- Key finding: crash detection latency up to 10 hours (gap window constraint) vs OPT-A's 120 s max

**Next step:** IP-002 convergence — compare options and select one. Then `/se-architecture` (Phase 3).

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
