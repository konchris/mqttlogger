# Contract: MQTT Topic Schema

**Service**: mqttlogger (subscriber)
**Broker**: Eclipse Mosquitto
**Date**: 2026-05-04

---

## Overview

mqttlogger subscribes to the `environment/#` wildcard and expects all messages published under
that prefix to conform to this schema. Messages that do not conform result in a logged error and
are discarded (FR-013).

---

## Topic Address Format

```
environment/{location_level_1}/{location_level_2}/{reading_type}
```

All four segments are required. Topics with fewer or more segments are outside this contract;
if received, they will be stored as-is but may not be queryable by the standard location
hierarchy.

---

## Segment Definitions

### `environment` (fixed)

Always the literal string `environment`. This is the top-level namespace for all environmental
sensor data. Other top-level namespaces (e.g., `brewing`) are out of scope for this service.

### `location_level_1`

| Value     | Meaning |
|-----------|---------|
| `indoor`  | Sensor located inside the building |
| `outdoor` | Sensor located outside the building |

### `location_level_2`

| Value          | Location            | `location_level_1` |
|----------------|---------------------|---------------------|
| `cellar_front` | Front of the cellar | `indoor`            |
| `cellar_back`  | Rear of the cellar  | `indoor`            |
| `bedroom`      | Bedroom             | `indoor`            |
| `living_room`  | Living room         | `indoor`            |
| `office`       | Office              | `indoor`            |
| `max_room`     | Max's room          | `indoor`            |
| `ben_room`     | Ben's room          | `indoor`            |
| `kitchen`      | Kitchen             | `indoor`            |
| `bathroom`     | Bathroom            | `indoor`            |
| `patio`        | Patio               | `outdoor`           |

New locations can be added by sensor publishers without changes to the logging service.

### `reading_type`

| Value             | Payload Format | Stored As | Description |
|-------------------|----------------|-----------|-------------|
| `temperature`     | Float string   | Float     | Degrees Celsius |
| `humidity`        | Float string   | Float     | Relative humidity percentage |
| `fan_state`       | `true`/`false` | 1.0 / 0.0 | Fan running or not |
| `floor_actuator`  | `true`/`false` | 1.0 / 0.0 | Floor heating actuator open or closed |
| `window_state`    | `true`/`false` | 1.0 / 0.0 | Window open or closed |
| `door_state`      | `true`/`false` | 1.0 / 0.0 | Door open or closed |

---

## Payload Format

### Numeric readings

A UTF-8 encoded string representing a decimal number parseable by `float()`.

```
23.4
18.75
100.0
```

### Boolean state readings

The exact UTF-8 strings `true` or `false` (lowercase only).

```
true
false
```

**Important**: The values `True`, `TRUE`, `1`, `0`, `yes`, `no` are **not** part of this
contract and will be treated as malformed payloads (discarded with a logged error).

---

## QoS Level

QoS 0 (at most once). Message delivery is best-effort; duplicate or lost messages are
acceptable at household sensor publishing rates. The broker is configured with
`allow_anonymous true` on port 1883.

---

## Example Messages

| Topic | Payload | Stored reading |
|-------|---------|---------------|
| `environment/indoor/cellar_front/temperature` | `18.3` | 18.3 |
| `environment/indoor/kitchen/humidity` | `62.5` | 62.5 |
| `environment/indoor/bedroom/fan_state` | `true` | 1.0 |
| `environment/outdoor/patio/temperature` | `9.1` | 9.1 |
