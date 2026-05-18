# Solution Exploration Summary

**System:** mqttlogger
**Feature:** 009-schema-evolution
**Date:** 2026-05-17
**Status:** CONVERGED — single option active; pre-exploration convergence rationale documented
**Last Updated By:** se-explore skill

---

## Pre-Exploration Convergence Note

The solution space for this feature converged before the branch was opened. The W-003 scope
(add `captured_at`, `location`, `measurement_type`; retain `device`; drop `currentdate` and
`currenttime`) was established through explicit operator decision during project planning,
informed by:

- Operational need to eliminate the `TIMESTAMP(currentdate, currenttime)` workaround in
  every downstream query (NFR-INT-003)
- Operational need for filtered time-range query acceleration (NFR-PERF-003)
- Explicit decision to retain `device` as the canonical MQTT topic — a single location can
  have multiple devices with the same measurement type (e.g. thermostat + radiators both
  reporting temperature)

One alternative (view-based schema exposure) was considered and eliminated pre-exploration
on the basis that it cannot satisfy NFR-INT-003 or NFR-PERF-003. See elimination record.

This is an accepted deviation from the standard Set-Based Design workflow. The convergence
is justified because: (a) the operational need is well-understood and unambiguous; (b) the
solution is a constrained migration of a single database table; (c) the eliminated alternative
fails hard constraints, not soft preferences.

---

## Solution Set Boundaries

### Hard Constraints (Immediate Disqualifiers)

- Must preserve all existing data — no row may be deleted or its `reading` or `device` value
  altered by the migration
- Must not require any internet connectivity or external services
- Must be executable as a single maintenance operation on `sietchtabr` within a short stack
  downtime window (target: under 5 minutes)
- Must satisfy NFR-INT-003: `captured_at` must be a native `DATETIME NOT NULL` column on
  the base table, not a computed expression in a view
- Must satisfy NFR-PERF-003: the composite index `(location, measurement_type, captured_at)`
  must be on the base table
- The logger (`data_model.py`, `mqtt_client.py`) and companion monitor (`monitor.py`,
  `bootstrap_sensors.py`) must function correctly immediately after migration — no
  degraded-mode operation is acceptable post-deployment

### Soft Constraints (Differentiators)

- Migration downtime should be minimised (soft target: under 5 minutes total)
- Migration script should be readable and reviewable by a returning developer (STK-002)
- Backfill derivation should be verifiable by a pre-migration dry-run SELECT

### Known Failed Approaches

| Approach | Evidence of Failure | Source |
| -------- | ------------------- | ------ |
| View-based schema exposure (OPT-B) | Cannot satisfy NFR-INT-003 (base table retains old columns; computed expressions still required at the storage layer) or NFR-PERF-003 (MariaDB does not support indexes on view columns) | Architecture analysis, 2026-05-17 |

---

## Active Options

| Option ID | Name | Core Approach | Status | Eliminated At |
| --------- | ---- | ------------- | ------ | ------------- |
| OPT-A | Direct Column Migration | ALTER TABLE to add new columns; UPDATE to backfill; DROP old columns; add composite index | Active | — |

---

## Integration Points

| IP ID | Milestone | Question to Answer | Evidence Threshold | Status |
| ----- | --------- | ------------------ | ------------------ | ------ |
| IP-001 | Before production deployment | Does the migration SQL produce correct `captured_at`, `location`, and `measurement_type` values for all existing topic patterns, and do the updated companion monitor queries work against the new schema? | (1) Dry-run SELECT confirms correct derivation for a representative sample of device topics; (2) updated companion monitor SQL executes without error against the new column names on a local schema copy | Pending |

---

## Convergence Target

**Final Integration Point:** IP-001 — pre-deployment dry-run verification
**Convergence Criterion:** IP-001 evidence confirms correct backfill derivation and companion
monitor compatibility. No further option comparison is needed — OPT-A proceeds to deployment.

---

## Current Status

**Options Active:** 1
**Options Eliminated:** 1 (pre-exploration)
**Next Integration Point:** IP-001 — pending dry-run tasks
