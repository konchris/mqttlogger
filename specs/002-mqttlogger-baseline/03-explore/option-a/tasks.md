# Exploration Tasks: Option A

**Target Integration Point:** IP-001
**Date:** 2026-05-09

---

## Tasks

| Task ID | Description | Type | Owner | Effort | Target IP | Output |
|---------|-------------|------|-------|--------|-----------|--------|
| TASK-A-001 | Add Uptime Kuma to the Docker Compose stack; confirm it starts, serves its UI, and operates with no internet access | Research + Prototype | Chris | ~1h | IP-001 | Uptime Kuma running locally; internet-independence confirmed |
| TASK-A-002 | Configure a push monitor in Uptime Kuma with 60-second heartbeat interval; configure a notification channel (push notification via Uptime Kuma mobile app or alternative) | Prototype | Chris | ~1h | IP-001 | Push monitor active; test notification received on phone |
| TASK-A-003 | Add heartbeat emission to mqttlogger — a background timer that sends an HTTP ping to the Uptime Kuma push endpoint at the configured interval | Prototype | Chris | ~2h | IP-001 | mqttlogger emits heartbeat; Uptime Kuma shows service as UP |
| TASK-A-004 | Evaluate LWT integration — register an LWT on mqttlogger's broker connection; configure Uptime Kuma or a separate subscriber to observe the LWT topic | Research + Prototype | Chris | ~1h | IP-001 | LWT fires on unclean disconnect; observable in broker or Uptime Kuma |
| TASK-A-005 | Fault injection test — deliberately kill the mqttlogger container; measure time from kill to alert received; repeat 3 times for consistency | Test | Chris | ~1h | IP-001 | Alert fires within 2× heartbeat interval on all 3 runs; no false negatives |
| TASK-A-006 | False positive baseline — run the full stack for 24+ hours under normal conditions; count spurious alerts | Test | Chris | ~24h elapsed (passive) | IP-001 | Zero false positives in 24h normal operation |

---

## Evidence Collection

At IP-001, the following evidence must be recorded in `evaluation-log.md`:

1. **Internet-independence confirmed:** Yes/No — Uptime Kuma push monitor operates with network interface set to local-only
2. **Heartbeat interval selected:** N seconds — chosen based on alert latency vs. false positive trade-off
3. **Fault injection results:** Time from container kill to alert received, across 3 runs (mean, max)
4. **False positive count:** Number of spurious alerts in 24h baseline period
5. **Resource impact:** Memory and CPU delta on host after adding Uptime Kuma
6. **MQTT event loop impact:** Any observed message drops or latency increase during heartbeat emission
7. **Go / No-go assessment:** Does OPT-A satisfy the IP-001 question?
