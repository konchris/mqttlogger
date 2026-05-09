# Solution Exploration Summary

**System:** mqttlogger
**Feature:** 002-mqttlogger-baseline
**Date:** 2026-05-09
**Status:** ACTIVE — options under exploration
**Last Updated By:** se-explore skill

---

## Problem Statement

The system cannot currently tell the operator when something has silently gone wrong. Three distinct failure modes are undetected:

- **RISK-013 (level 16):** Upstream sensor topology changes silently — topic renamed, sensor stops publishing, new sensor added — and the record becomes silently incomplete.
- **RISK-014 (level 16):** No mechanism exists to verify the historical record is complete for any given time period.
- **RISK-016 (level 16):** A container crash leaves no visible marker in the record; the gap is discoverable only by actively inspecting the database.

This exploration focuses on passive observability — the system notifies the operator when something is wrong, rather than requiring the operator to go looking.

---

## Solution Set Boundaries

### Hard Constraints (Immediate Disqualifiers)

- **No cloud-dependent services** — solution must run entirely on the local home network
- **No paid services or subscriptions** — zero additional cost
- **No changes to HomeMatic/CCU3/RedMatic** — upstream sensor publishing infrastructure is out of scope
- **No always-on internet connection required** — solution must function on a fully local, internet-disconnected network
- **Open source, self-hosted tooling only**

### Soft Constraints (Differentiators)

- Minimal Surface Area (Constitution Principle VII) — prefer solutions that don't accumulate scope in the core logger
- NFR-MAIN-001 — additional codebases increase maintenance burden; solo developer with irregular availability
- Low operational complexity — solution must be operable after months away without re-learning

### Known Failed Approaches

| Approach | Evidence of Failure | Source |
|----------|---------------------|--------|
| MQTT heartbeat published to phone MQTT client | EasyMQTT does not support silence-based alerting (cannot notify when messages stop arriving); no remote network access (no VPN, no exposed broker) — passive notification requirement unmet | Session elicitation, 2026-05-09 |

---

## Active Options

| Option ID | Name | Core Approach | Status | Eliminated At |
|-----------|------|---------------|--------|---------------|
| OPT-A | Heartbeat + Uptime Kuma | mqttlogger emits periodic HTTP heartbeat; Uptime Kuma monitors and alerts on silence | Active | — |
| OPT-B | Companion Database Monitor | Separate process queries MariaDB for gaps and sensor silences; reports via self-hosted push notification | Active | — |

## Eliminated Options

| Option ID | Name | Eliminated At | Reason |
|-----------|------|---------------|--------|
| OPT-C | In-Process Enhanced Monitoring | Pre-IP-001 (architectural analysis) | Structural disqualifier: in-process monitoring cannot detect its own process crash. Cannot address RISK-016 by design. In-process concepts may be incorporated as implementation details within OPT-A or OPT-B. |
| — | MQTT heartbeat to phone | Pre-option (analysis) | See Known Failed Approaches above. |

---

## Integration Points

| IP ID | Milestone | Question to Answer | Evidence Threshold | Status |
|-------|-----------|--------------------|--------------------|--------|
| IP-001 | Prototype complete (target: within ~2 weeks of 2026-05-09) | **OPT-A:** Does Uptime Kuma running locally receive an mqttlogger heartbeat and fire an alert — with no internet dependency and no false positives — when the container is deliberately killed? **OPT-B:** Does the companion monitor correctly detect a known sensor gap via fault injection, and does dual-direction sensor config checking work in practice? | Working prototype on live system; fault injection test passed; 24h clean-run with no false positives | Pending |
| IP-002 | Before summer experiment window (target: before 2026-06-15) | Which option better satisfies all three risks (RISK-013, RISK-014, RISK-016) with the lowest solo-developer maintenance burden? | At least one option has passed IP-001; evidence from prototype operation is sufficient to distinguish options on maintenance burden and coverage | Pending |

---

## Convergence Target

**Final Integration Point:** IP-002 — before summer seasonal experiment window begins.
**Convergence Criterion:** One option demonstrably satisfies RISK-016 (passive crash notification) with acceptable false-positive rate and solo-developer maintenance burden. Progress on RISK-013 and RISK-014 is desirable but not required for convergence — these remain open for a later iteration.
**Quality over speed:** The summer deadline is a soft outer boundary. Both options should be given sufficient exploration time to generate reliable evidence.

---

## Current Status

**Options Active:** 2 (OPT-A, OPT-B)
**Options Eliminated:** 1 formal (OPT-C) + 1 pre-option (MQTT-to-phone)
**Next Integration Point:** IP-001 — prototype viability
