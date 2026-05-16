# Option B: Metabase

**Status:** Active
**Date Created:** 2026-05-16
**Last Updated:** 2026-05-16

---

## Core Approach

Metabase is an open-source business intelligence tool that runs as a Docker container. It auto-discovers the `sensorreadings` table schema on first connection and allows the operator to build questions (queries) and dashboards via a point-and-click interface without writing SQL. It connects to MariaDB via the MySQL driver using a read-only database user.

Metabase stores all its state — saved questions, dashboards, user settings, and schema metadata — in an internal database (H2 by default, or an external MySQL/PostgreSQL database). This state does not load from files at container startup: there is no native file-based provisioning equivalent to Grafana's datasource YAML + dashboard JSON approach. Dashboard export/import is available via the API, but restoration after a volume wipe requires manual steps or custom scripting.

## Key Characteristics

- Auto-discovers database schema on first connection — no SQL required to build the first visualization
- Point-and-click question builder lowers the barrier to ad-hoc exploration
- Suitable for a range of chart types including time-series, but optimised more for BI/aggregation than continuous sensor time-series
- Internal metadata database (H2 or external) stores all configuration state
- Limited native provisioning-as-code: no file-based datasource or dashboard loading on container startup

## NFR Satisfaction Assessment

| NFR ID | Priority | Assessment | Confidence |
| ------ | -------- | ---------- | ---------- |
| NFR-PERF-003 | Must Have | Likely satisfied — direct SQL under the hood; render time similar to Grafana for equivalent queries | Medium — needs TASK-B-002 to confirm |
| NFR-REL-003 | Must Have | At risk — Metabase startup is slower than Grafana (JVM-based); may exceed 2-minute availability target | Low — needs TASK-B-001 to measure |
| NFR-SEC-002 | Must Have | Satisfied — datasource uses read-only user; credentials supplied via environment variables | High |
| NFR-USE-003 | Must Have | At risk — no native file-based provisioning; restoring after volume wipe requires manual steps or API scripting | Low — this is the primary elimination risk for OPT-B |
| NFR-INT-002 | Must Have | Satisfied — read-only user has SELECT on sensorreadings only | High |

## Potential Advantages

- Fastest path to a first working visualization — auto-discovery means no SQL authoring for initial exploration
- Point-and-click interface is more accessible for ad-hoc questions that don't fit pre-built panels
- Good at aggregation queries (averages, min/max by room) that complement time-series panels

## Potential Weaknesses

- NFR-USE-003 is the critical weakness: dashboard state lives in the internal H2 database, not in version-controlled files; volume loss requires manual restore or API scripting
- NFR-REL-003 risk: JVM startup time may push availability beyond 2 minutes after host restart
- Less suited to continuous time-series sensor data than Grafana's native time series panel type
