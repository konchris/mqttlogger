# ADR-002: Two-Layer Out-of-Process Monitoring

**Date:** 2026-05-10
**Status:** Accepted
**Deciders:** Chris
**Feature:** 002-mqttlogger-baseline

---

## Context

Three level-16 risks were identified in the baseline analysis:
- RISK-013: sensor topology changes silently (sensor renamed, stopped, or added)
- RISK-016: logger container crash leaves no visible marker; gap goes undetected

SC-CONOPS-003 ("any failure is visible without active inspection") was unmet. Two candidate approaches were explored in parallel (Set-Based Design, see `03-explore/`):

- **OPT-A**: Heartbeat push from mqtt_logger to Uptime Kuma. Uptime Kuma detects heartbeat silence and fires an alert.
- **OPT-B**: Companion monitor container polls MariaDB for sensor gaps and unknown sensor appearances.
- **OPT-C (eliminated pre-IP-001)**: In-process monitoring — a watchdog thread or health check running inside mqtt_logger that reports its own health.

OPT-C was eliminated before prototyping because of a structural impossibility: a monitor running inside the logger process cannot detect that the logger process has crashed. If the process dies, the in-process monitor dies with it. This elimination is evidence-based (logical impossibility), not a preference.

Both OPT-A and OPT-B passed 24-hour false-positive baselines with zero spurious alerts (IP-001 evidence). The convergence decision (IP-002) showed they are not substitutes — they cover different failure modes at different system layers.

## Decision

Deploy both OPT-A and OPT-B as complementary monitoring layers:

- **OPT-A (process layer):** mqtt_logger emits an HTTP liveness heartbeat to Uptime Kuma every 60 seconds. If Uptime Kuma receives no push for >120 seconds, it fires a DOWN alert via ntfy. Detects: process crash, container OOM kill, unhandled exception death. Latency: ≤120 seconds (validated: mean 93 s, max 120 s, 3/3 fault injection runs).

- **OPT-B (sensor layer):** companion_monitor polls MariaDB every 5 minutes with a 600-minute gap window. Detects: individual sensor silence (periodic sensors only), new/unknown sensor appearances. Latency: ≤600 minutes (constrained by the slowest periodic sensor's publish interval).

Both layers report via the self-hosted ntfy push server.

## Consequences

### Positive
- RISK-016 (crash detection) mitigated: ≤120 s latency with zero false positives
- RISK-013 (topology changes) mitigated: unknown sensors surface within one poll cycle; silent sensors detected within 600 min
- OPT-A and OPT-B are structurally independent — OPT-B operates even when mqtt_logger is down (the crash-detection scenario)
- Self-healing unknown sensor alerts: new devices announce themselves automatically, reducing manual `sensors.yml` maintenance burden
- Both options are LAN-only: no internet dependency (FR-MON-006, hard constraint from explore-summary)

### Negative
- Two additional containers (uptime_kuma, ntfy) and one additional Python codebase (companion_monitor) increase the deployment surface
- companion_monitor has no automated test suite (Constitution Principle VI gap — documented in plan.md)
- 600-minute crash detection ceiling via OPT-B means a crash that coincides with OPT-A being disabled could go undetected for up to 10 hours
- Off-network notification gap: ntfy is LAN-only; alerts are lost if operator's iPhone is not on home Wi-Fi (RISK-023)

### Neutral
- The "select one" convergence criterion was revised: evidence showed the options are complementary, not redundant

## Alternatives Considered

### Alternative 1: OPT-C — In-Process Monitoring

**Description:** A watchdog thread or health-check endpoint inside mqtt_logger that reports process health.

**Rejected because:** Structural impossibility — the monitor cannot outlive the process it monitors. If the logger process crashes, all in-process monitoring ceases simultaneously. See `03-explore/elimination-record.md`.

### Alternative 2: OPT-A only (no OPT-B)

**Description:** Deploy only the heartbeat + Uptime Kuma layer; skip companion_monitor.

**Rejected because:** OPT-A detects process crashes (RISK-016) but cannot detect individual sensor silence (RISK-013). A sensor that stops publishing while the logger is running would be undetectable. RISK-013 remains level 16 without OPT-B.

### Alternative 3: OPT-B only (no OPT-A)

**Description:** Deploy only the companion monitor; skip Uptime Kuma and heartbeat.

**Rejected because:** OPT-B's crash detection latency ceiling is 600 minutes (10 hours) — the gap window must cover the slowest periodic sensor (thermostat set points, ~288 min). This violates the operator's expectation of timely crash notification. FR-MON-001 (≤120 s) cannot be satisfied by OPT-B alone.

## Related

- Supersedes: None
- Related requirements: FR-MON-001, FR-MON-002, FR-MON-003, FR-MON-004, FR-MON-005, FR-MON-006
- Related NFRs: NFR-REL-001, NFR-REL-002
- Related explore option: OPT-A, OPT-B (both selected), OPT-C (eliminated)
