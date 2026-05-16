# Option A: Grafana OSS

**Status:** Active
**Date Created:** 2026-05-16
**Last Updated:** 2026-05-16

---

## Core Approach

Grafana OSS is an open-source time-series visualization platform with a native MySQL/MariaDB datasource plugin. It runs as a Docker container and connects directly to the `sensorreadings` table using a read-only database user. Panels are defined as SQL queries against the table; time-range filtering, sensor selection, and multi-panel layouts are all supported out of the box.

Grafana supports full configuration-as-code via its provisioning system: datasource definitions (YAML) and dashboard definitions (JSON) are mounted into the container at startup and loaded automatically — no UI interaction required to restore a complete dashboard after a volume wipe.

## Key Characteristics

- Purpose-built for time-series sensor data — the primary use case maps directly onto Grafana's native panel types
- Native MariaDB/MySQL datasource: no additional plugins or adapters required
- Dashboard provisioning is a first-class feature: datasource YAML + dashboard JSON committed to the repo are sufficient to fully restore after a clean volume
- Zero custom code required — all configuration is declarative
- Wide community support; extensive documentation for home automation use cases

## NFR Satisfaction Assessment

| NFR ID | Priority | Assessment | Confidence |
| ------ | -------- | ---------- | ---------- |
| NFR-PERF-003 | Must Have | Likely satisfied — direct SQL queries against sensorreadings; render time depends on row count and indexing | Medium — needs TASK-A-002 to confirm |
| NFR-REL-003 | Must Have | Likely satisfied — lightweight container; depends_on health check handles startup ordering | Medium — needs TASK-A-001 to confirm |
| NFR-SEC-002 | Must Have | Satisfied — datasource YAML references .env-supplied credentials; read-only user configured at DB level | High |
| NFR-USE-003 | Must Have | Satisfied — native provisioning via mounted YAML/JSON files; volume wipe + restart is the standard recovery path | High |
| NFR-INT-002 | Must Have | Satisfied — datasource user has SELECT on sensorreadings only; panel queries are version-controlled | High |

## Potential Advantages

- NFR-USE-003 (provisioning as code) is natively and robustly supported — strongest differentiator over OPT-B
- Time-series chart types (time series, stat, gauge, heatmap) directly match the sensor data use case
- Alerting and annotation support available for future features (e.g. RISK-020 write-activity heartbeat)
- No internal metadata database to manage — Grafana can run with a SQLite volume or be made fully stateless via provisioning

## Potential Weaknesses

- Initial dashboard JSON authoring is manual — first panel must be built via UI and exported, or written by hand
- Grafana's query model is SQL-in-panels, which may feel less intuitive than Metabase's point-and-click question builder for ad-hoc exploration
