# Option Elimination Record

**System:** mqttlogger
**Feature:** 002-mqttlogger-baseline

---

*This document records all options that were eliminated during exploration, and the evidence that justified elimination. Eliminated options are never deleted — they are preserved here so that future engineers understand why the road not taken was abandoned.*

---

## Eliminated Options

| Option ID | Name | Eliminated At | Evidence Summary | Decision By |
|-----------|------|---------------|------------------|-------------|
| OPT-C | In-Process Enhanced Monitoring | Pre-IP-001 (architectural analysis, 2026-05-09) | Structural disqualifier — in-process monitoring cannot detect its own process crash. Cannot address RISK-016 by design. | Chris |
| — | MQTT Heartbeat to Phone | Pre-option (elicitation analysis, 2026-05-09) | EasyMQTT does not support silence-based alerting; no remote network access without VPN. Passive notification requirement unmet under current constraints. | Chris |

---

## Detail Records

### OPT-C — In-Process Enhanced Monitoring

**Eliminated At:** Pre-IP-001, 2026-05-09
**Eliminated By:** Chris

**Core Approach (as proposed):** mqttlogger extended with a background monitoring thread that tracks per-sensor last-seen timestamps, message counts, and write success rates. Emits structured log summaries and/or push alerts from within the same process.

**Evidence of Elimination:**
Architectural analysis established that in-process monitoring cannot detect the failure mode it was designed to address: if the mqttlogger process crashes, the monitoring thread crashes with it. No heartbeat is emitted, no alert fires, no gap marker is written. This is a structural property of single-process monitoring, not an implementation detail that can be engineered around.

OPT-C was therefore structurally disqualified as a standalone option for RISK-016 (passive crash notification). To address RISK-016, OPT-C would require an external watchdog — at which point OPT-A or OPT-B is already present and OPT-C adds complexity without adding coverage.

**Preserved Concepts:**
In-process monitoring concepts (per-sensor tracking, write success rate logging, structured periodic summaries) may be incorporated as implementation details within OPT-A or OPT-B during implementation. These are useful enhancements to log quality and capture verification, even if they cannot substitute for an external observer.

**Conditions for Reconsideration:**
OPT-C could be reconsidered as a complement (not a replacement) to OPT-A or OPT-B in a future iteration, specifically to add richer in-process telemetry beyond what a heartbeat or DB poll can provide.

---

### MQTT Heartbeat to Phone (Pre-Option)

**Eliminated At:** Pre-option (elicitation stage), 2026-05-09
**Eliminated By:** Chris

**Core Approach (as proposed):** mqttlogger publishes a periodic heartbeat to a dedicated MQTT topic on the Mosquitto broker. The operator subscribes via a phone MQTT client (EasyMQTT) and monitors for heartbeat presence. A native MQTT Last Will and Testament (LWT) message provides complementary crash detection via the broker.

**Evidence of Elimination:**

1. **No silence-based alerting in EasyMQTT:** The operator's current MQTT phone client (EasyMQTT, free tier) displays the last received value for a topic but does not alert when messages stop arriving. Passive crash notification requires detecting *absence*, not *presence*. Without silence-based alerting, this approach requires the operator to actively check the MQTT client — which is the current behaviour and solves nothing.

2. **No remote network access:** The operator has no VPN and the Mosquitto broker is not exposed to the internet. When away from home, the phone has no connection to the broker. Any notification mechanism dependent on direct MQTT connectivity is therefore unavailable during periods of remote operation.

**Preserved Concepts:**
- LWT (Last Will and Testament) remains a viable mechanism as a secondary signal within OPT-A or as supplementary telemetry in OPT-B. If the broker publishes a death message on mqttlogger disconnect, an external monitor (Uptime Kuma or companion script) can subscribe to that topic for faster crash detection.
- The MQTT heartbeat concept is valid if a future VPN deployment makes the broker remotely accessible and a silence-alerting MQTT client is adopted.

**Conditions for Reconsideration:**
If a VPN is set up providing remote access to the home network, and an MQTT client with silence-based alerting is adopted, this approach becomes viable. Revisit in a future iteration.
