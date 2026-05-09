# Assumptions: Option A

**Date:** 2026-05-09

---

## Assumptions Register

| ID | Assumption | If False, Then | Validation Approach | Status |
|----|------------|----------------|---------------------|--------|
| ASM-A-001 | Uptime Kuma can be added to the existing Docker Compose stack without meaningful resource contention on the mini PC host | Host resource constraints prevent running Uptime Kuma alongside existing services | Measure CPU and memory usage before and after adding Uptime Kuma container; compare to existing headroom (~14% memory, ~1% disk) | Unvalidated |
| ASM-A-002 | Uptime Kuma push monitor type operates without any internet access | Uptime Kuma requires outbound internet connectivity for push monitors; local-only deployment is broken | Deploy Uptime Kuma on isolated local network; configure push monitor; verify alert fires without internet access | Unvalidated |
| ASM-A-003 | A timer-based HTTP ping from within mqttlogger does not interfere with the paho-mqtt event loop or introduce meaningful latency to message processing | Heartbeat emission blocks or delays the MQTT receive path, causing message drops | Prototype heartbeat in a background thread; verify no impact on message throughput at peak estimated load | Unvalidated |
| ASM-A-004 | A missed heartbeat is a reliable proxy for "the service has stopped capturing" at IP-001 scope | The process is alive (heartbeats continue) but capture has silently stopped — the heartbeat gives false assurance | Accepted limitation at IP-001 scope; noted as a known gap to be addressed in a future iteration with a DB-write-confirming heartbeat | Accepted limitation |
| ASM-A-005 | A heartbeat interval exists (e.g. 60 seconds) that provides timely crash detection with acceptable false-positive rate under normal network conditions | False positives (spurious missed pings causing false alerts) are too frequent to be operationally useful | Test with 60-second interval over 24+ hours of normal operation; count false positive events | Unvalidated |

---

## Assumption Risk Summary

| Assumption | Risk if False | Must Resolve By |
|------------|---------------|-----------------|
| ASM-A-002 | High — if push monitors require internet, entire option is disqualified | IP-001 |
| ASM-A-003 | Medium — heartbeat interference with MQTT loop could violate NFR-PERF-001 | IP-001 |
| ASM-A-005 | Medium — excessive false positives make the tool unusable in practice | IP-001 |
| ASM-A-001 | Low — host has significant headroom; unlikely to be an issue | IP-001 |
| ASM-A-004 | Accepted — known scope limitation, not a disqualifier for this option | Future iteration |
