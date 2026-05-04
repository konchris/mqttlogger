# Contract: Database Schema

**Database**: MariaDB (MySQL-compatible)
**Date**: 2026-05-04

---

## Overview

mqttlogger writes to a single table, `sensorreadings`, in the configured database. The table
is created automatically by `data_model.py` if it does not exist. All reads (analysis,
reporting) are performed by external tools (e.g., Jupyter notebooks) and are outside the scope
of this service.

---

## Table: `sensorreadings`

```sql
CREATE TABLE sensorreadings (
    id          INTEGER     NOT NULL AUTO_INCREMENT,
    currentdate DATE,
    currenttime TIME,
    device      TEXT,
    reading     FLOAT,
    PRIMARY KEY (id)
);
```

### Column Reference

| Column        | Type    | Nullable | Description |
|---------------|---------|----------|-------------|
| `id`          | INTEGER | No       | Surrogate primary key, auto-incremented |
| `currentdate` | DATE    | Yes*     | Calendar date at time of message receipt (YYYY-MM-DD) |
| `currenttime` | TIME    | Yes*     | Wall-clock time at time of message receipt (HH:MM:SS) |
| `device`      | TEXT    | Yes*     | Full MQTT topic string (Device Address) |
| `reading`     | FLOAT   | Yes*     | Numeric measurement value |

\* The ORM model does not declare explicit `NOT NULL` constraints on `currentdate`,
`currenttime`, `device`, or `reading`, so MariaDB permits NULL values at the column level.
The application always supplies values for all columns; NULL values in these columns indicate
a data integrity issue rather than expected behavior.

---

## Querying by Device Address

Because `device` stores the full topic path, standard SQL pattern matching applies:

```sql
-- All cellar readings
SELECT * FROM sensorreadings WHERE device LIKE 'environment/indoor/cellar%';

-- All temperature readings across all locations
SELECT * FROM sensorreadings WHERE device LIKE '%/temperature';

-- Specific sensor on a specific date
SELECT * FROM sensorreadings
WHERE device = 'environment/indoor/cellar_front/temperature'
  AND currentdate = '2026-05-04';
```

---

## Database User Permissions

The `mqttlogger` database user requires only `INSERT` and `SELECT` privileges on the
`sensorreadings` table, plus `CREATE` privilege on the database if automatic table creation
via `data_model.create()` is used.

---

## Notes

- The table uses no indexes beyond the primary key. For analytical queries over large date
  ranges, a compound index on `(device, currentdate)` would improve performance but is outside
  the scope of the logging service itself.
- The `id` column is the only guarantee of uniqueness. Two readings from the same device at
  the same second are valid and will have different `id` values.
- Records are never deleted by the logging service. Retention management is out of scope.
