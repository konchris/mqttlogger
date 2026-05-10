# Implementation Plan: 002-mqttlogger-baseline

**Branch:** `002-mqttlogger-baseline-ip001`
**Date:** 2026-05-10
**Spec Artifacts:** `specs/002-mqttlogger-baseline/`
**Status:** POST-EXPLORATION — monitoring stack implemented and validated; proceeding to architecture documentation

---

## Summary

mqttlogger is an existing home-automation sensor capture daemon. This SE feature (002) performs a full INCOSE SE baseline analysis of the system, surfaces three level-16 risks (RISK-013, RISK-014, RISK-016), and designs and validates a passive monitoring stack to mitigate RISK-013 and RISK-016.

The converged solution consists of two complementary monitoring layers:
- **OPT-A** — Uptime Kuma heartbeat push: mqttlogger emits an HTTP liveness heartbeat every 60 s; Uptime Kuma alerts via ntfy if the heartbeat stops. Crash detection ≤ 120 s.
- **OPT-B** — Companion DB monitor: a separate Python container polls MariaDB every 5 min with a 600-min gap window; alerts on sensor silence and unknown sensor appearances. Addresses RISK-013.

Both options passed 24 h false-positive baselines with zero spurious alerts. Both are deployed in the current `docker-compose.yml`.

---

## Technical Context

**Language/Version:** Python 3.10+ (Linux amd64/arm64)
**Primary Dependencies:**
- Core logger: `paho-mqtt`, `SQLAlchemy`, `pymysql`
- Companion monitor: `pymysql`, `pyyaml`
- Notification: `ntfy` (self-hosted, binwiederhier/ntfy Docker image)
- Heartbeat monitor: `Uptime Kuma` (louislam/uptime-kuma Docker image)

**Storage:** MariaDB (lscr.io/linuxserver/mariadb), co-hosted on `sietchtabr`

**Testing:** `pytest` — unit tests exist but are not comprehensive for the monitoring components. No CI/CD pipeline (TBD-003). Current gate: "tests must pass."

**Target Platform:** Linux x86 mini PC (`sietchtabr`), Docker Compose, private home network, no internet dependency

**Project Type:** Long-running capture daemon + companion monitoring services

**Performance Goals:** Message completeness (no drops); crash detection ≤ 120 s (OPT-A); sensor silence detection ≤ 600 min (OPT-B)

**Constraints:**
- No cloud services or internet dependency — fully local network only
- No changes to HomeMatic / CCU3 / RedMatic
- Solo developer; maintenance windows are irregular
- OPT-B gap window (600 min) is constrained by slowest periodic sensor (thermostat set points, ~288 min); cannot be reduced below ~2× slowest without generating false positives

**Scale/Scope:** ~13 periodic sensors monitored; ~15 event-driven sensors excluded; ~50 devices total publishing to the broker

---

## Constitution Check

*Assessed against mqttlogger Constitution v1.0.0*

| Principle | Assessment | Justification / Violation Action |
|-----------|------------|----------------------------------|
| I. Single-Purpose Service | **Borderline** | The heartbeat thread (`mqttlogger/heartbeat.py`) runs inside the core logger process. The constitution states alerting MUST be in a separate tool. However, the heartbeat only emits a liveness signal — it does not perform alerting. Alerting is performed by Uptime Kuma (external service). Accepted as within scope; the heartbeat is analogous to a health check, not business logic. |
| II. Configuration Over Code | ✓ Pass | All env-specific values in `config.json` or environment variables; no hardcoded values |
| III. Container-First Deployment | ✓ Pass | Full stack deployable via `docker compose up -d`; Dockerfile uses non-root user |
| IV. Observability by Default | ✓ Pass | Structured rotating logs; companion monitor suppresses "check complete" when state unchanged (reduces noise without losing signal) |
| V. Graceful Lifecycle Management | ✓ Pass | SIGTERM/SIGINT handled in app.py; heartbeat thread is daemon (exits with process) |
| VI. Integration-Preferred Testing | ⚠ Gap | Companion monitor has no automated tests. This is accepted for the exploration phase; tests should be added before the next SE gate closes. |
| VII. Minimal Surface Area | **Justified Violation** | OPT-B adds a second codebase (`companion-monitor/`). Justified: an in-process monitor cannot detect its own process crash (RISK-016 proof). The companion is a structurally distinct concern — process crash vs. sensor gap — and cannot be merged into the core without violating its own purpose. See `03-explore/elimination-record.md` (OPT-C eliminated on this basis). |

**Gate Result:** PASS with two documented justifications (Principle I borderline, Principle VI gap noted for future).

---

## Complexity Tracking

| Item | Why Needed | Simpler Alternative Rejected Because |
|------|------------|-------------------------------------|
| `mqttlogger/heartbeat.py` as background thread inside core logger | OPT-A requires the liveness signal to originate from the logger process itself; an external poller cannot confirm the logger process is alive | Moving the heartbeat to a separate sidecar would require the sidecar to confirm logger liveness via something other than its own heartbeat, creating circular dependency |
| `companion-monitor/` second codebase | An in-process monitor cannot detect its own crash (RISK-016); requires structural separation | In-process monitoring was eliminated as OPT-C — see `03-explore/elimination-record.md` |
| 600-minute gap window (OPT-B) | Slowest periodic sensor (thermostat set points) publishes approximately every 288 min; 2× provides a false-positive-free margin | Shorter windows (10 min originally attempted) generated false positives against the slowest sensors; the 600-min value was calibrated against live data |

---

## Project Structure

### SE Documentation

```text
specs/002-mqttlogger-baseline/
├── 00-stakeholders/
│   ├── stakeholder-register.md
│   ├── needs-register.md
│   ├── personas/
│   └── empathy-maps/
├── 01-conops/
│   ├── conops.md
│   └── operational-scenarios.md
├── 02-nfr/
│   └── quality-attributes.md
├── 03-explore/
│   ├── explore-summary.md            # CONVERGED 2026-05-10 — both OPT-A + OPT-B selected
│   ├── elimination-record.md
│   ├── option-a/
│   │   ├── description.md
│   │   ├── assumptions.md
│   │   ├── evaluation-log.md         # IP-001 PASS + IP-002 Selected
│   │   └── tasks.md
│   └── option-b/
│       ├── description.md
│       ├── assumptions.md
│       ├── evaluation-log.md         # IP-001 PASS + IP-002 Selected
│       ├── research-ntfy-vs-gotify.md
│       └── tasks.md
├── 04-requirements/
│   └── requirements-register.md     # FR-001..FR-014 + FR-MON-001..FR-MON-007
├── 05-architecture/                  # TO BE CREATED by /se-architecture
├── 07-plan/
│   └── plan.md                       # This file
├── 09-vv/
│   └── vv-plan.md                    # NFR entries populated; FR entries pending
├── 10-risk/
│   └── risk-register.md             # RISK-001..RISK-022
└── gate-reports/
    └── gate-1-pass.md
```

### Source Code Layout

```text
app.py                                # Core logger entry point (MQTT connect, heartbeat start, LWT)
mqttlogger/
├── mqtt_client.py                    # on_connect, on_message, insert to DB
├── heartbeat.py                      # OPT-A: background HTTP push thread (60 s default)
├── db_connection.py                  # load_config_file, create_connection_string
└── data_model.py                     # SensorReading SQLAlchemy model (table: sensorreadings)
companion-monitor/
├── monitor.py                        # OPT-B: gap detection + dual-direction config check + ntfy push
├── bootstrap_sensors.py              # One-shot: query DB for distinct topics → sensors.yml
├── sensors.yml.example               # Template (sensors.yml is gitignored)
├── Dockerfile
└── requirements.txt                  # pymysql, pyyaml
config.json.example                   # Template (config.json is gitignored)
docker-compose.yml                    # mqtt, mqtt_logger, mariadb, uptime_kuma, ntfy, companion_monitor
mosquitto/                            # Mosquitto broker config
```

### Deployed Services (`sietchtabr`)

| Service | Purpose | Monitoring Layer |
|---------|---------|-----------------|
| `mqtt` | MQTT broker | — |
| `mqtt_logger` | Core capture daemon | Emits heartbeat (OPT-A) |
| `mariadb` | Persistence | — |
| `uptime_kuma` | Heartbeat monitor (OPT-A) | Process layer |
| `ntfy` | Push notification server | Both layers |
| `companion_monitor` | Gap and topology monitor (OPT-B) | Sensor layer |
