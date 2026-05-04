# Data Model: Core MQTT Sensor Logging Service

**Branch**: `001-core-mqtt-logger` | **Date**: 2026-05-04

---

## Entity: SensorReading

The sole persistent entity in the system. Represents a single measurement captured from one
sensor device at one point in time.

### Attributes

| Attribute      | Type     | Constraints              | Description |
|----------------|----------|--------------------------|-------------|
| `id`           | Integer  | Primary key, auto-increment, NOT NULL | Surrogate key; uniquely identifies each record |
| `currentdate`  | Date     | NOT NULL                 | Calendar date at time of message receipt (YYYY-MM-DD) |
| `currenttime`  | Time     | NOT NULL                 | Wall-clock time at time of message receipt (HH:MM:SS) |
| `device`       | Text     | NOT NULL                 | Full MQTT topic string used as device address (see Device Address below) |
| `reading`      | Float    | NOT NULL                 | Numeric measurement value; boolean payloads stored as 1.0 (true) or 0.0 (false) |

### Notes

- **Timestamp split**: The capture timestamp is stored as two separate columns (`currentdate` +
  `currenttime`) rather than a single `DATETIME` or `TIMESTAMP` column. This is the existing
  convention; it allows independent date-range and time-of-day filtering without datetime
  arithmetic.

- **device column type**: `Text` (unbounded string) rather than `VARCHAR(N)` accommodates any
  topic path length without schema changes when new sensor locations are added.

- **No unique constraint on (device, currentdate, currenttime)**: Multiple readings from the
  same device at the same second are permitted and stored as separate rows. The `id` surrogate
  key is the only uniqueness guarantee.

- **No foreign keys**: The table is self-contained. Device addresses are denormalized into each
  row as a plain string, avoiding the need for a separate `devices` lookup table at the cost of
  storage redundancy.

### Table Name

`sensorreadings`

### Canonical Naming

The entity is referred to as **Sensor Reading** throughout all specification documents. The
column `device` stores the **Device Address** (full MQTT topic path). The terms "device
identifier" and "device address" are synonymous in this codebase; "device address" is the
canonical term.

---

## Entity: Device Address (Value Object)

Not a stored table — a structured string value embedded in `SensorReading.device`. Documented
here to make the address schema explicit and testable.

### Structure

```
{concern}/{location_level_1}/{location_level_2}/{reading_type}
```

| Segment           | Values                                               |
|-------------------|------------------------------------------------------|
| `concern`         | `environment`                                        |
| `location_level_1`| `indoor`, `outdoor`                                  |
| `location_level_2`| `cellar_front`, `cellar_back`, `bedroom`, `living_room`, `office`, `max_room`, `ben_room`, `kitchen`, `bathroom` (indoor); `patio` (outdoor) |
| `reading_type`    | `temperature`, `humidity`, `fan_state`, `floor_actuator`, `window_state`, `door_state` |

### Examples

```
environment/indoor/cellar_front/temperature
environment/indoor/kitchen/humidity
environment/outdoor/patio/temperature
environment/indoor/bedroom/fan_state
```

### Notes

- The service subscribes to `environment/#` and stores **all** matching topic strings as-is.
  New locations or reading types are captured automatically without schema changes.
- Reading types that represent boolean states (`fan_state`, `floor_actuator`, `window_state`,
  `door_state`) have payloads of `"true"` or `"false"` and are stored as `1.0` or `0.0`.
- Reading types that represent physical measurements (`temperature`, `humidity`) have numeric
  float payloads stored directly.

---

## Entity: Configuration (External Input)

Not stored in the database — read from `config.json` at startup. Documented here for
completeness and to make configuration validation requirements explicit.

### Schema

| Key               | Type   | Required | Description |
|-------------------|--------|----------|-------------|
| `mqtt_server_ip`  | String | Yes      | Hostname or IP address of the MQTT broker |
| `mqtt_server_port`| Integer| Yes      | MQTT broker listener port (typically 1883) |
| `db_ip`           | String | Yes      | Hostname or IP address of the MariaDB server |
| `db_port`         | String | Yes      | MariaDB port (typically 3306) |
| `db_user`         | String | Yes      | Database username |
| `db_password`     | String | Yes      | Database password |
| `db_database`     | String | Yes      | Database name |

### Validation Rules (FR-016)

- If the file does not exist at the expected path, the service MUST exit immediately with a
  non-zero status and a human-readable error identifying the missing file path.
- If any required key is absent or the file is not valid JSON, the service MUST exit immediately
  with a non-zero status and a human-readable error identifying the specific problem.
- No default values are substituted for missing keys.
