# ADR-006: Heartbeat Implemented as Daemon Thread Inside mqtt_logger

**Date:** 2026-05-10
**Status:** Accepted
**Deciders:** Chris
**Feature:** 002-mqttlogger-baseline

---

## Context

OPT-A (ADR-002) requires that the mqttlogger process emit a liveness signal at regular intervals so that Uptime Kuma can detect when the process has stopped. The liveness signal must originate from inside the mqttlogger process — otherwise it cannot prove the logger process specifically is alive.

Constitution Principle I states: "Business logic, data transformation beyond type coercion, analytics, alerting, and visualization MUST NOT be added to this service." The heartbeat is not alerting (it does not evaluate conditions or decide to notify); it is a passive liveness signal analogous to a health check ping. However, it is additional code inside the core service, which creates tension with Principle I.

## Decision

Implement the heartbeat as a Python `threading.Thread` (daemon=True) started inside the `app.py` entry point, defined in `mqttlogger/heartbeat.py`. The thread sleeps for `heartbeat_interval_seconds` (default 60), wakes, sends `HTTP POST heartbeat_url`, and repeats. As a daemon thread, it exits automatically when the main process exits — no explicit shutdown logic required. The heartbeat is activated only when `heartbeat_url` is present in `config.json`; if absent, the thread is not started (backward-compatible, no configuration required for existing deployments).

The Constitution Principle I tension is accepted and documented in `07-plan/plan.md` (Constitution Check section) with the rationale: the heartbeat is a liveness signal, not business logic or alerting. The alerting decision (trigger a notification) is made by Uptime Kuma, not by the logger.

## Consequences

### Positive
- The heartbeat thread definitively proves process liveness — if the HTTP push arrives, the Python interpreter and the thread scheduler are running inside the correct process
- Daemon thread exits automatically with the process; no shutdown coordination needed (Constitution Principle V satisfied)
- Optional: existing deployments without `heartbeat_url` are unaffected
- Adds fewer than 20 lines of code to the codebase

### Negative
- Adds code to the core logger in tension with Constitution Principle I (documented violation in plan.md)
- RISK-020: the heartbeat proves liveness, not capture activity — a deadlocked `on_message` callback that is alive but not processing messages would continue sending heartbeats, providing false assurance about capture health
- The heartbeat thread shares the Python process with the MQTT loop; a GIL-heavy MQTT processing spike could theoretically delay heartbeat execution, though at observed message rates this is negligible

### Neutral
- The heartbeat interval (60 s default) and the Uptime Kuma monitor configuration (2× interval = 120 s alert threshold) are operational parameters, not architectural ones

## Alternatives Considered

### Alternative 1: Sidecar container that probes the logger

**Description:** A separate container periodically checks whether the mqtt_logger process or container is alive (e.g. via Docker API, health check endpoint, or `docker inspect`).

**Rejected because:** A sidecar that uses the Docker API to check container status only confirms the container is running, not that the Python process inside is alive and responsive. An unresponsive process (deadlocked, in an infinite loop) would appear healthy to a container-level check. The heartbeat thread inside the process is the only mechanism that confirms the Python runtime is executing.

### Alternative 2: MQTT-based heartbeat (publish to a topic)

**Description:** The logger periodically publishes a heartbeat message to an MQTT topic. A separate subscriber detects silence on that topic.

**Rejected because:** The subscriber cannot detect broker-level silence vs. logger-level silence. If the broker is unavailable, the heartbeat topic goes silent even though the logger is healthy. An HTTP push to Uptime Kuma is unambiguous: it only fires if the logger process itself issues the HTTP request.

### Alternative 3: Expose an HTTP health endpoint inside mqtt_logger

**Description:** Add an HTTP server endpoint (e.g. `/health`) to mqtt_logger that Uptime Kuma polls.

**Rejected because:** Adds an HTTP server to the logger, which is more invasive than a thread (more code, a listening socket, a new dependency). Uptime Kuma would then be polling the logger (pull model), which means Uptime Kuma checks must be configured to account for the logger's restart timing. The push model (logger pushes to Uptime Kuma) means Uptime Kuma's timer is reset on each push — simpler and more reliable for detecting absence of heartbeats.

## Related

- Supersedes: None
- Related requirements: FR-013, FR-014, FR-MON-001
- Related NFRs: NFR-REL-001
- Related explore option: OPT-A
