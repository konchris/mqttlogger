# Option A: Heartbeat + Uptime Kuma

**Status:** Active
**Date Created:** 2026-05-09
**Last Updated:** 2026-05-09

---

## Core Approach

mqttlogger is extended to emit a periodic HTTP "push" ping to a locally hosted instance of Uptime Kuma, a self-hosted monitoring and alerting tool. Uptime Kuma's push monitor type expects a ping at a configured interval; if the ping is missed, Uptime Kuma fires an alert via the operator's chosen notification channel (e.g. push notification to phone via the Uptime Kuma mobile app, which supports active alerting unlike a raw MQTT client).

As a secondary signal, mqttlogger may register a Last Will and Testament (LWT) message with the Mosquitto broker at connection time. If mqttlogger disconnects uncleanly (process crash), Mosquitto automatically publishes the LWT to a designated topic. Uptime Kuma can subscribe to this topic as a supplementary crash signal, providing faster detection than waiting for the next missed heartbeat interval.

This option makes a minimal change to the mqttlogger codebase (a timer-based HTTP call) and introduces one new tool to the Docker Compose stack (Uptime Kuma). The core capture logic is untouched.

## Key Characteristics

- Minimal code change to mqttlogger — heartbeat emission is a small, isolated addition
- Uptime Kuma is a widely used, actively maintained, self-hosted monitoring tool with no cloud dependency in its push monitor configuration
- Heartbeat proves *process liveness*, not *capture activity* — a hung thread could continue emitting heartbeats while writing nothing to the database
- Crash detection latency equals the heartbeat interval (e.g. 60-second interval → alert fires within 60–120 seconds of crash)
- Does not directly address RISK-013 (silent drift) or RISK-014 (completeness verification) — these remain open for a future iteration
- LWT provides a complementary, near-instant crash signal through the existing broker

## NFR Satisfaction Assessment

| NFR ID | Priority | Assessment | Confidence |
|--------|----------|------------|------------|
| NFR-PERF-001 | Must Have | Satisfied — heartbeat addition does not affect the capture path | High |
| NFR-PERF-002 | Must Have | Satisfied — heartbeat addition does not affect timestamping | High |
| NFR-REL-001 | Must Have | Satisfied — heartbeat emission failure does not affect service recovery | High |
| NFR-REL-002 | Must Have | Satisfied — heartbeat addition does not affect restart time | High |
| NFR-SEC-001 | Must Have | Satisfied — no new credentials required | High |
| NFR-USE-001 | Must Have | Satisfied — unaffected | High |
| NFR-USE-002 | Must Have | Satisfied — heartbeat events logged per standard | High |
| NFR-MAIN-001 | Should Have | Low risk — small isolated addition; existing test suite extended | Medium |
| NFR-PORT-001 | Must Have | Satisfied — Uptime Kuma added to existing Docker Compose stack | High |
| NFR-INT-001 | Must Have | Satisfied — no database schema changes | High |

## Potential Advantages

- No new codebase to maintain — Uptime Kuma is a third-party tool with its own maintenance lifecycle
- Lowest code change of the three options — minimal regression risk
- Uptime Kuma provides a web dashboard for historical uptime visibility as a free secondary benefit
- LWT integration uses a native MQTT feature with no additional code
- Notification channel is configurable in Uptime Kuma (push, email, Slack, etc.) — future flexibility

## Potential Weaknesses

- Heartbeat proves liveness, not capture activity — does not detect a scenario where the process is alive but writes are failing silently
- Does not address RISK-013 (drift) or RISK-014 (completeness) — requires a future complementary mechanism for full observability coverage
- Alert latency equals heartbeat interval — a 60-second interval means up to 120 seconds before alert fires
- Uptime Kuma is an additional tool to learn, configure, and keep updated
