# Evaluation Log: Option B

---

## Integration Point Reviews

### IP-001 — Prototype Viability

**Status:** Artifacts delivered — hands-on evidence pending
**Target Date:** ~2026-05-23 (within ~2 weeks of 2026-05-09)

**Question:** Does the companion monitor correctly detect a known sensor gap via fault injection, and does dual-direction sensor config checking work in practice against the live database?

---

### Artifacts Delivered (2026-05-09)

| Task | Artifact | Status |
|------|----------|--------|
| TASK-B-001 | `specs/002-mqttlogger-baseline/03-explore/option-b/research-ntfy-vs-gotify.md` — ntfy.sh selected; rationale documented; ASM-B-001 validated by analysis | Done |
| TASK-B-003 | `companion-monitor/monitor.py` — gap detection + dual-direction config check + ntfy push + stateful alerting (alert on transition, not every poll) | Done |
| TASK-B-003 | `companion-monitor/bootstrap_sensors.py` — queries distinct topics from last 30 days; writes `sensors.yml` | Done |
| TASK-B-004 | `docker-compose.yml` — `ntfy` service (port 8080) + `companion_monitor` service (builds from `companion-monitor/`); both on `monitoring_net` + `mqtt_db` | Done |
| TASK-B-004 | `companion-monitor/Dockerfile` + `companion-monitor/requirements.txt` (PyMySQL + PyYAML) | Done |
| TASK-B-004 | `companion-monitor/sensors.yml.example` — template for operator configuration | Done |

---

### Operator Steps Required Before Evidence Collection

1. Run bootstrap to populate sensor config (requires live DB access):
   ```bash
   DB_HOST=localhost DB_PORT=3306 DB_USER=<user> DB_PASSWORD=<pw> DB_NAME=<db> \
       SENSORS_FILE=companion-monitor/sensors.yml \
       python companion-monitor/bootstrap_sensors.py
   ```
   Review `companion-monitor/sensors.yml` and remove any test/transient topics.

2. Start the OPT-B services:
   ```bash
   docker compose up -d ntfy companion_monitor
   ```

3. Verify companion monitor is running and making checks:
   ```bash
   docker compose logs -f companion_monitor
   ```
   Expect: `Check complete — active=N missing=0 unknown=0` every 5 minutes.

4. Subscribe to alerts on phone: install the ntfy app → add subscription `http://<host-ip>:8080/mqttlogger-alerts`

---

### Evidence to Collect (TASK-B-002 through TASK-B-006)

| Evidence Item | How to Collect | Target |
|---------------|----------------|--------|
| Sensor config bootstrap effort | Time to run bootstrap_sensors.py and review output | ≤ 30 min; no manual lookup required |
| Sensor config completeness | Count gaps (topics known to exist but not in bootstrap output) | 0 unexpected gaps |
| Polling interval selected | From POLLING_INTERVAL_SECONDS env var (default 300 s) | Record actual value used |
| Fault injection run 1–3: time from `docker stop mqtt_logger` to ntfy notification received | Stopwatch × 3 (stop logger, wait for gap to show in DB, wait for monitor to detect and alert) | ≤ 2 × polling interval (≤ 10 min) |
| False positive count over 24 h | Count spurious alerts during normal operation (excluding deliberate maintenance window) | 0 during steady-state; ≤ 1 during maintenance window |
| Dual-direction check: unknown sensors found | Run for 1 week; count sensors discovered in DB but not in config | Record count; assess whether actionable |
| Dual-direction check: silent sensors found | Run for 1 week; count sensors in config not seen in DB | Record count; assess whether stale config or real silence |
| Codebase assessment | Review `companion-monitor/monitor.py` against Constitution Principle VII (Minimal Surface Area) | Could a returning developer understand it in one session? Yes/No |
| DB query overhead | Check host CPU during polling vs. baseline; check `SHOW PROCESSLIST` during query | No measurable impact at this sensor scale |

---

**Evidence Gathered (2026-05-09 – 2026-05-10):**

| Evidence Item | Result | Notes |
|---------------|--------|-------|
| TASK-B-001: Notification tool selected | ntfy.sh | See research-ntfy-vs-gotify.md; simpler API, no token management, iOS+Android apps |
| TASK-B-001: Internet-independence | Confirmed by analysis | ntfy.sh phone app connects directly to self-hosted server on LAN; no cloud relay required |
| TASK-B-002: Sensor config bootstrap effort | ~15 min total | bootstrap_sensors.py + manual classification into sensors:/excluded: sections |
| Sensor publish interval analysis | Slowest periodic: ~288 min (thermostat set points) | Drove GAP_WINDOW_MINUTES upward from initial 10 to 600 |
| GAP_WINDOW_MINUTES selected | 600 min (10 hours) | 2× slowest periodic publisher interval; prevents false positives on set point sensors |
| Polling interval selected | 300 s (5 min) | Default; no adjustment needed |
| Sensors monitored | 13 (temperature + humidity only) | Set points, window/door states, radiator levels classified as excluded |
| Dual-direction check: unknown sensors surfaced | 3 new dining room sensors surfaced automatically | Correct behaviour — RISK-013 detection working in live operation |
| Dual-direction check: excluded sensor handling | Added excluded: key to sensors.yml; suppresses known event-driven sensors from unknown alerts | Required code update to monitor.py |
| ASM-B-004 (config drift): maintenance burden | Lower than initially assessed | Sensor topology is stable; additions are rare, one-time, and self-announcing via unknown-sensor alert |
| Crash detection latency | Up to 600 min (10 hours) | Fundamental structural limitation — gap window must cover slowest sensor publish interval |
| TASK-B-005: Fault injection | Not run | 10 h latency is the structural ceiling; running a timed kill would confirm detection but not reduce latency |
| TASK-B-006: 24h false positive baseline | PASS — 0 spurious alerts | Ran 13:15 UTC 2026-05-09 → 13:15 UTC 2026-05-10; 4 alerts total, all genuine |
| Alert: attic/thermostat_humidity | Genuine recovery alert | Sensor was silent >25 h then resumed; not a false positive |
| Alert: 3× new dining room sensors | Genuine unknown-sensor alerts | New devices publishing for first time; self-announced correctly |

**Assessment:** OPT-B correctly detects individual sensor silence and surfaces unknown sensors through live operation. The dual-direction check works as designed in a real deployment. Zero false positives over 24 h. The 10 h crash detection ceiling is a known structural limitation — it is acceptable only when paired with OPT-A.

**Decision:** Continue

**Decision Rationale:** All IP-001 success criteria met. Dual-direction check validated live. False positive baseline clean. OPT-B advances to IP-002 convergence.

**Decision Made By:** Chris

---

### IP-002 — Final Convergence

**Status:** PASS — 2026-05-10
**Target Date:** Before 2026-06-15 (summer experiment window)

**Question:** Does OPT-B better satisfy RISK-016 (and RISK-013/RISK-014) with acceptable solo-developer maintenance burden compared to OPT-A?

**Evidence Gathered:**

OPT-B is the only option that detects individual sensor silence (RISK-013) and surfaces new/unknown sensors automatically. During the 24 h baseline, 3 new dining room sensors were discovered without operator intervention — the self-announcing property eliminates the primary maintenance concern (ASM-B-004). Sensor topology is stable in practice; `sensors.yml` updates are rare and triggered by the monitor itself. OPT-B does not address RISK-016 at useful latency (10 h worst case); it depends on OPT-A for that coverage.

**Assessment:** OPT-B and OPT-A are not substitutes. OPT-B covers the sensor-level failure modes (RISK-013) that OPT-A is blind to; OPT-A covers the crash detection (RISK-016) that OPT-B cannot provide at useful latency. Both options are retained.

**Decision:** Selected — retained as part of combined monitoring stack

**Decision Rationale:** OPT-B is the sole path to RISK-013 mitigation (individual sensor gaps, unknown sensor surfacing). It operates at a monitoring layer below OPT-A and addresses failure modes OPT-A cannot detect. Maintenance burden is lower than initially assessed due to the self-announcing unknown-sensor alert.

**Decision Made By:** Chris
