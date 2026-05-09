# Exploration Tasks: Option B

**Target Integration Point:** IP-001
**Date:** 2026-05-09

---

## Tasks

| Task ID | Description | Type | Owner | Effort | Target IP | Output |
|---------|-------------|------|-------|--------|-----------|--------|
| TASK-B-001 | Evaluate ntfy.sh vs Gotify for local push notification — deploy each, send a test notification to phone without internet access, assess setup complexity and UX | Research + Prototype | Chris | ~2h | IP-001 | One tool selected; local delivery confirmed; internet-independence confirmed |
| TASK-B-002 | Bootstrap initial sensor config — query MariaDB for all distinct sensor topics seen in the last 30 days; review list for completeness; create `sensors.yml` or equivalent | Research | Chris | ~1h | IP-001 | `sensors.yml` with complete list of known sensors; gaps identified |
| TASK-B-003 | Write companion monitor script — queries DB for sensors in config not seen within polling window; queries DB for sensors seen but not in config; emits push notification on any anomaly | Prototype | Chris | ~3h | IP-001 | Working script producing correct output against live database |
| TASK-B-004 | Deploy companion monitor — as a Docker Compose service with scheduled polling or as a host cron job; decide which deployment model fits better | Prototype | Chris | ~1h | IP-001 | Companion monitor running on schedule; logs confirming execution |
| TASK-B-005 | Fault injection test — stop mqttlogger for a defined period (e.g. 10 minutes); verify companion monitor detects the gap and sends a notification; repeat 3 times | Test | Chris | ~1h | IP-001 | Notification received within 2× polling interval on all 3 runs; gap correctly identified in report |
| TASK-B-006 | False positive baseline — run companion monitor for 24+ hours under normal conditions including one planned maintenance window; count spurious alerts | Test | Chris | ~24h elapsed (passive) | IP-001 | Alert count during normal operation = 0 (excluding maintenance window); maintenance window handling assessed |

---

## Evidence Collection

At IP-001, the following evidence must be recorded in `evaluation-log.md`:

1. **Notification tool selected:** ntfy.sh or Gotify — with rationale
2. **Internet-independence confirmed:** Yes/No — local push notification works without internet
3. **Sensor config bootstrap effort:** Time taken to derive initial `sensors.yml` from DB history; gaps found
4. **Polling interval selected:** N minutes — chosen based on detection latency vs. false positive trade-off
5. **Fault injection results:** Time from logger stop to notification received, across 3 runs (mean, max)
6. **False positive count:** Number of spurious alerts in 24h baseline period (excluding maintenance window)
7. **Codebase assessment:** Is the companion monitor simple enough to understand and maintain after months away?
8. **Dual-direction check results:** Any sensors discovered in DB not in config (new sensors found)? Any config sensors not in DB (silent sensors found)?
9. **Go / No-go assessment:** Does OPT-B satisfy the IP-001 question?
