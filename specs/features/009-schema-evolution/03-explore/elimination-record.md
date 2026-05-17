# Option Elimination Record

**System:** mqttlogger
**Feature:** 009-schema-evolution

---

*This document records all options that were eliminated during exploration, and the evidence
that justified elimination. Eliminated options are never deleted — they are preserved here
so that future engineers understand why the road not taken was abandoned.*

---

## Eliminated Options

| Option ID | Name | Eliminated At | Evidence Summary | Decision By |
| --------- | ---- | ------------- | ---------------- | ----------- |
| OPT-B | View-Based Schema Exposure | Pre-exploration (architecture analysis) | Cannot satisfy NFR-INT-003 (base table retains old columns; `TIMESTAMP()` workaround moves from application queries into the view definition, not eliminated) or NFR-PERF-003 (MariaDB does not support indexes on view columns — index must be on the base table) | Chris, 2026-05-17 |

---

## Detail Records

### OPT-B — View-Based Schema Exposure

**Eliminated At:** Pre-exploration, 2026-05-17
**Eliminated By:** Chris

**Description:**
Rather than migrating the base table, create a MariaDB VIEW named `sensorreadings_v2` (or
replace the base table name via a rename) that exposes `TIMESTAMP(currentdate, currenttime)
AS captured_at`, `SUBSTRING_INDEX(device, '/', -2) AS location`, and
`SUBSTRING_INDEX(device, '/', -1) AS measurement_type` as computed columns derived from the
existing `currentdate`, `currenttime`, and `device` base columns. The base table schema
remains unchanged; no data migration is required; downtime is zero.

**Evidence of Elimination:**

1. **Fails NFR-INT-003**: The requirement states that `captured_at` must be a native
   `DATETIME NOT NULL` column on the base table, directly usable without computed
   expressions. A view does not satisfy this — the computation is merely moved from the
   application query into the view definition. The base table still stores `currentdate`
   and `currenttime` separately, and any consumer that reads the base table directly (e.g.
   a future tool that bypasses the view) must still use `TIMESTAMP()`. NFR-INT-003 is a
   hard constraint; this option cannot satisfy it.

2. **Fails NFR-PERF-003**: MariaDB does not support indexes on view columns. The composite
   index `(location, measurement_type, captured_at)` required by NFR-PERF-003 must be
   created on the base table. A view over computed columns cannot have its own index;
   queries through the view that filter on `location`, `measurement_type`, or `captured_at`
   will resolve to a full base-table scan. NFR-PERF-003 is a hard constraint; this option
   cannot satisfy it.

**Conditions for Reconsideration:**
This option is not eligible for reconsideration within feature 009. It may be revisited
only if: (a) NFR-INT-003 and NFR-PERF-003 are formally downgraded from Must Have, and
(b) a specific operational constraint prevents any table-level migration (e.g. the table
grows to a scale where ALTER TABLE is prohibitively slow). Neither condition is currently
anticipated.
