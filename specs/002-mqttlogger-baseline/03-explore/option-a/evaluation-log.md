# Evaluation Log: Option A

---

## Integration Point Reviews

### IP-001 — Prototype Viability

**Status:** Artifacts delivered — hands-on evidence pending
**Target Date:** ~2026-05-23 (within ~2 weeks of 2026-05-09)

**Question:** Does Uptime Kuma running locally receive an mqttlogger heartbeat and fire an alert — with no internet dependency and no false positives — when the container is deliberately killed?

---

### Artifacts Delivered (2026-05-09)

| Task | Artifact | Status |
|------|----------|--------|
| TASK-A-001 | `docker-compose.yml` — `uptime_kuma` service added with persistent volume, port 3001, `monitoring_net` | Done |
| TASK-A-003 | `mqttlogger/heartbeat.py` — background daemon thread; HTTP push to `heartbeat_url` every `heartbeat_interval_seconds` | Done |
| TASK-A-003 | `app.py` — heartbeat started after connect if `heartbeat_url` present in `config.json`; optional, backward-compatible | Done |
| TASK-A-004 | `app.py` — LWT registered (`mqttlogger/status` → `"offline"`, QoS 1, retain) before `connect()` | Done |
| TASK-A-004 | `mqttlogger/mqtt_client.py` — publishes `"online"` to `mqttlogger/status` in `on_connect` | Done |

---

### Operator Steps Required Before Evidence Collection

1. `docker compose up -d uptime_kuma` — start Uptime Kuma
2. Open `http://localhost:3001` → create a **Push** monitor
   - Heartbeat interval: **60 seconds**
   - Retries before alert: **1** (alert fires after one missed push = 60–120 s from crash)
3. Copy the push URL from the monitor settings (e.g. `http://uptime-kuma:3001/api/push/<token>?status=up&msg=OK&ping=`)
4. Add to `config.json`:
   ```json
   "heartbeat_url": "http://uptime-kuma:3001/api/push/<your-token>?status=up&msg=OK&ping=",
   "heartbeat_interval_seconds": 60
   ```
5. Configure a notification channel (Uptime Kuma → Notifications → add push/email/Telegram)
6. `docker compose up -d --build mqtt_logger` — rebuild with heartbeat code
7. Confirm Uptime Kuma shows `mqtt_logger` as **UP** within 60 s

---

### Evidence to Collect (TASK-A-005 and TASK-A-006)

| Evidence Item | How to Collect | Target |
|---------------|----------------|--------|
| Fault injection run 1–3: time from `docker kill mqtt_logger` to notification received | Stopwatch × 3 | ≤ 120 s (≤ 2 × heartbeat interval) |
| False positive count over 24 h normal operation | Count alerts that fired without a deliberate kill | 0 |
| Resource delta: host RAM before/after adding Uptime Kuma | `free -h` before and after `docker compose up uptime_kuma` | Acceptable (note actual MB) |
| Internet-independence: Uptime Kuma UI and push reachable without internet | Block outbound internet; confirm UI loads and push endpoint responds | Yes |
| LWT observable: watch `mosquitto_sub -t 'mqttlogger/status'` during kill and reconnect | Terminal during fault injection | `offline` on kill; `online` on reconnect |

---

**Evidence Gathered (2026-05-09 – 2026-05-10):**

| Evidence Item | Result | Notes |
|---------------|--------|-------|
| TASK-A-005: Fault injection run 1 | 120 s | Full Pending → Down cycle observed |
| TASK-A-005: Fault injection run 2 | 50 s | Kill near end of heartbeat window |
| TASK-A-005: Fault injection run 3 | 108 s | Pending → Down sequence confirmed |
| TASK-A-005: Mean / Max | 93 s / 120 s | All runs within 2× heartbeat interval ✓ |
| TASK-A-005: False negative count | 0 | All 3 runs detected and notified |
| Notification delivery | ntfy (self-hosted) | Uptime Kuma → ntfy → web UI confirmed |
| TASK-A-006: 24h false positive baseline | PASS — 0 spurious alerts | Ran 15:07 UTC 2026-05-09 → 15:07 UTC 2026-05-10; zero false positives |

**Assessment:** OPT-A reliably detects mqttlogger container crashes within 2× the heartbeat interval (max 120 s). The Uptime Kuma → ntfy notification chain works end-to-end. Zero false positives over 24 h of normal operation. This directly addresses RISK-016 with response latency no other option can match.

**Decision:** Continue

**Decision Rationale:** All IP-001 success criteria met. Fault injection 3/3 detected; false positive baseline clean. OPT-A advances to IP-002 convergence.

**Decision Made By:** Chris

---

### IP-002 — Final Convergence

**Status:** PASS — 2026-05-10
**Target Date:** Before 2026-06-15 (summer experiment window)

**Question:** Does OPT-A better satisfy RISK-016 with lower solo-developer maintenance burden than OPT-B?

**Evidence Gathered:**

OPT-A is the only option that detects a complete mqttlogger process crash within an operationally useful latency (≤120 s). OPT-B's crash detection ceiling is 600 min by design — the gap window must cover the slowest periodic sensor, making rapid crash notification structurally impossible from OPT-B alone. OPT-A's maintenance surface is minimal: one background thread in `heartbeat.py`, one Uptime Kuma push monitor, and one config key (`heartbeat_url`). Both options passed their 24 h false-positive baselines.

**Assessment:** OPT-A and OPT-B are not substitutes — they monitor at different layers. OPT-A answers "is the logger process alive?" OPT-B answers "are all individual sensors still publishing?" The convergence criterion ("select one") was based on an assumption of redundancy that the prototype evidence disproved. Both options are retained.

**Decision:** Selected — retained as part of combined monitoring stack

**Decision Rationale:** OPT-A is the sole path to RISK-016 mitigation with acceptable latency. It is lightweight, validated, and operationally simple. Dropping it in favour of OPT-B would leave crash detection at 10 h worst case.

**Decision Made By:** Chris
