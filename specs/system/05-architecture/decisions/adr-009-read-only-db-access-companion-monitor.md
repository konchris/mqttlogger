# ADR-009: Read-Only Database Access for Companion Monitor

**Date:** 2026-05-17
**Status:** Accepted
**Deciders:** Chris (sole operator)
**Feature:** 009-schema-evolution

---

## Context

The `companion_monitor` service queries MariaDB to detect sensor gaps and unknown sensors.
Its queries are exclusively read operations (`SELECT DISTINCT device`). However, at the time
of feature 009, the companion monitor is configured in `docker-compose.yml` to connect using
the same credentials as `mqtt_logger` — the write-capable `MYSQL_USER`/`MYSQL_PASSWORD` pair.

This violates NFR-INT-002: *Non-logger consumers shall connect to the database with
`SELECT`-only privileges*. The violation creates two risks:

1. A bug or future code change in `companion_monitor` could corrupt the `sensorreadings`
   table — the logger's primary data store — because the credentials permit `INSERT`,
   `UPDATE`, and `DELETE`.
2. The architecture provides no enforced separation between the write path (mqtt_logger)
   and the read path (companion_monitor). Constitution Principle I (Single-Purpose Service)
   requires each service to have only the access it needs.

Feature 009 is the right time to close this gap because the schema migration requires
restarting the full stack anyway. Creating the read-only user can be done in the same
maintenance window with no additional downtime.

---

## Decision

Create a dedicated MariaDB user `monitor_ro` with `SELECT`-only privileges on the
`mqttlogger` database's `sensorreadings` table. Configure the `companion_monitor` service
in `docker-compose.yml` to use `MONITOR_DB_USER` / `MONITOR_DB_PASSWORD` environment
variables, sourced from `.env`, rather than the logger's `MYSQL_USER` / `MYSQL_PASSWORD`.

MariaDB provisioning (applied inside the running `mariadb` container during deployment):

```sql
CREATE USER 'monitor_ro'@'%' IDENTIFIED BY '<password>';
GRANT SELECT ON mqttlogger.sensorreadings TO 'monitor_ro'@'%';
FLUSH PRIVILEGES;
```

`docker-compose.yml` `companion_monitor` service environment:

```yaml
environment:
  DB_USER: ${MONITOR_DB_USER}
  DB_PASSWORD: ${MONITOR_DB_PASSWORD}
  DB_HOST: mariadb
  DB_NAME: ${MYSQL_DATABASE}
```

This is a principle-of-least-privilege enforcement — the companion monitor is structurally
prevented from writing to the database regardless of any future code change.

---

## Consequences

### Positive

- NFR-INT-002 satisfied: SHOW GRANTS confirms SELECT-only access for the companion monitor
  user at any time — verifiable by inspection
- A future bug or rogue code change in companion_monitor cannot corrupt the primary data store
- The read and write credentials are independently rotatable — rotating the logger's DB
  password does not require updating the companion monitor's configuration and vice versa
- Consistent with Constitution Principle I (Single-Purpose Service): each service has only
  the database access its function requires

### Negative

- One additional secret (`MONITOR_DB_PASSWORD`) must be managed in `.env` on sietchtabr
- The MariaDB user creation step is a manual operational procedure (cannot be version-controlled
  as SQL that runs automatically) — must be documented and executed during deployment

### Neutral

- The `MONITOR_DB_USER` and `MONITOR_DB_PASSWORD` variables in `.env` are parallel to the
  existing `MYSQL_USER` / `MYSQL_PASSWORD` variables — same pattern, different values

---

## Alternatives Considered

### Alternative 1: Keep using logger credentials (current state)

**Description:** Leave the companion monitor using `MYSQL_USER` / `MYSQL_PASSWORD`. The
monitor only executes SELECT queries in practice; the risk is theoretical.

**Rejected because:** NFR-INT-002 is a Must Have requirement. "The risk is theoretical"
is not an acceptable disposition for a must-have architectural property. The fix is low-cost
and the maintenance window is already required for the schema migration.

### Alternative 2: MariaDB row-level security

**Description:** Rather than a user-level privilege restriction, use MariaDB row-level
security to restrict what data the companion monitor can access.

**Rejected because:** MariaDB does not have row-level security in the PostgreSQL/Oracle
sense. User-level GRANT restrictions are the correct mechanism. Row-level restrictions are
not applicable here — the companion monitor needs access to all rows, just not write access.

---

## Related

- Supersedes: None
- Related requirements: FR-036
- Related NFRs: NFR-INT-002
- Related risks: RISK-028
- Related ADRs: ADR-002 (two-layer monitoring — companion_monitor purpose)
