# Assumptions: Option B

**Date:** 2026-05-09

---

## Assumptions Register

| ID | Assumption | If False, Then | Validation Approach | Status |
|----|------------|----------------|---------------------|--------|
| ASM-B-001 | ntfy.sh or Gotify can be deployed locally with no internet dependency and zero cost, and can deliver push notifications to the operator's phone | Neither tool works on a local-only network without cloud relay; push notifications require internet | Deploy ntfy.sh locally; configure phone client; send test notification without internet access; verify delivery | Unvalidated |
| ASM-B-002 | Periodic MariaDB queries at the chosen polling interval do not meaningfully impact database or host performance at the current scale (~50 sensors, low message rate) | DB query load causes observable performance degradation or affects mqttlogger's write throughput | Measure DB query latency and host CPU during companion monitor runs; compare to baseline | Unvalidated |
| ASM-B-003 | A hardcoded sensor config file is a viable starting point — the initial list of expected sensors can be derived from DB history without extensive manual effort | Deriving the initial sensor list from DB history is impractical; the config cannot be bootstrapped quickly | Query the DB for distinct sensor topics seen in the last 30 days; review completeness of resulting list | Unvalidated |
| ASM-B-004 | Dual-direction checking (config sensors absent from DB + DB sensors absent from config) provides sufficient coverage to keep the sensor config current over time without manual maintenance | Config drift still accumulates despite dual-direction checking; the config becomes stale faster than it is updated | Operate the dual-direction check for 1 week on the live database; count discovered discrepancies and assess whether they were actionable | Unvalidated |
| ASM-B-005 | A polling interval exists (e.g. 5 minutes) that provides crash detection within an acceptable window while keeping false positive rate near zero | Either detection is too slow to be useful, or false positives (transient DB gaps during maintenance) are too frequent | Test with 5-minute interval over 24+ hours including a deliberate maintenance window; count false positives | Unvalidated |
| ASM-B-006 | The companion monitor is simple enough to be understood and maintained by a solo developer returning after months away | Companion codebase accretes complexity and becomes as opaque as the problem it was designed to surface | Review companion codebase against Constitution Principle VII (Minimal Surface Area) before IP-001; assess whether a returning developer could understand it in one session | Unvalidated |

---

## Assumption Risk Summary

| Assumption | Risk if False | Must Resolve By |
|------------|---------------|-----------------|
| ASM-B-001 | High — if local push notification is not achievable, the alerting mechanism fails; option is disqualified | IP-001 |
| ASM-B-005 | High — if no polling interval achieves both timely detection and low false positives, the option is operationally unusable | IP-001 |
| ASM-B-003 | Medium — if bootstrapping the sensor list is impractical, initial setup cost is prohibitive | IP-001 |
| ASM-B-004 | Medium — if dual-direction checking doesn't keep config current, the option degrades to a manually maintained list | IP-001 |
| ASM-B-002 | Low — host has significant headroom; query load at this scale is unlikely to matter | IP-001 |
| ASM-B-006 | Medium — codebase clarity is a maintenance concern; assess before IP-001 | IP-001 |
