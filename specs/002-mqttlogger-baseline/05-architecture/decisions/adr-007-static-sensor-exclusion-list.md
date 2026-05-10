# ADR-007: Static Sensor Classification via sensors.yml Exclusion List

**Date:** 2026-05-10
**Status:** Accepted
**Deciders:** Chris
**Feature:** 002-mqttlogger-baseline

---

## Context

OPT-B (companion_monitor) checks two directions: (1) sensors in a known configuration that have gone silent, and (2) sensors publishing to the DB that are not in the known configuration. Direction 2 (unknown sensor detection) must distinguish between:
- **Periodic sensors** (temperature, humidity): publish on a regular schedule; silence indicates a problem; must be gap-monitored
- **Event-driven sensors** (door/window contacts, motion): publish only on state change; may be legitimately silent for hours or days; must NOT trigger silence alerts

Without this distinction, the gap-window approach generates false positives for event-driven sensors that happen not to have triggered during the gap window.

The bootstrap process (bootstrap_sensors.py) queries the DB for all sensors that have published recently, but cannot automatically classify them — the distinction between periodic and event-driven is based on physical knowledge of the sensor type, not on publish frequency alone (a thermostat set-point sensor may publish as rarely as every 288 minutes, which is within the range of some legitimate event-driven devices).

## Decision

Use a YAML configuration file (`sensors.yml`) with two explicit lists:
- `sensors:` — periodic sensors subject to gap monitoring
- `excluded:` — event-driven sensors suppressed from both gap alerts and unknown-sensor alerts

The file is populated once using `bootstrap_sensors.py` (queries the DB) followed by manual operator classification. It is mounted as a read-only volume into the companion_monitor container. Changes require a container restart.

The unknown-sensor alert (direction 2) fires when a device publishes to the DB that is neither in `sensors:` nor in `excluded:`. This self-announcing property means new sensors surface automatically — the operator only needs to reclassify them, not discover them.

## Consequences

### Positive
- Simple to understand and audit: the entire sensor topology is visible in one YAML file
- No algorithmic classification risk: a sensor that publishes infrequently for physical reasons (cold room, rarely opened door) is not misclassified
- New sensors self-announce via the unknown-sensor alert — the operator does not need to remember to update `sensors.yml` when a new device is installed; they receive a notification
- Stable in practice: the home sensor topology changes rarely (a new sensor every few months at most)

### Negative
- Manual classification required at bootstrap time (~15 minutes per deployment)
- `sensors.yml` is not version-controlled (gitignored) because it contains deployment-specific sensor names; there is no automated way to verify it is current
- Classification errors (periodic sensor placed in `excluded:`) suppress alerts silently — no warning is generated for an excluded sensor that stops publishing
- Container restart required to pick up changes to `sensors.yml`

### Neutral
- The gap window (600 minutes) was calibrated against the live deployment to avoid false positives from the slowest periodic sensor (thermostat set points, ~288 min publish interval). This tuning must be revisited if slower periodic sensors are added.

## Alternatives Considered

### Alternative 1: Automatic classification by publish frequency

**Description:** Analyse the historical publish interval for each sensor topic. Topics with median intervals below a threshold are classified as periodic; above the threshold as event-driven.

**Rejected because:** The boundary between "slow periodic" and "event-driven" is ambiguous. A thermostat set-point sensor may publish every 288 minutes; a rarely-opened door contact might also go silent for 6 hours. Statistical classification would require a training window and would still mis-classify edge cases. Physical knowledge of the sensor type is the only reliable classifier for these sensors. The manual approach is correct here; the automation would add complexity without improving accuracy.

### Alternative 2: No exclusion list — alert on all unknowns

**Description:** Remove the `excluded:` list entirely; let all unknown sensors generate alerts.

**Rejected because:** 15 event-driven sensors are currently deployed. Each time any one of these triggers (e.g. a door opens), it generates an "unknown sensor" alert for the first occurrence and a "sensor resumed" alert thereafter. This floods the operator with noise. The IP-001 baseline confirmed that kitchen sensors (5 devices) triggered unknown-sensor alerts correctly — an event-driven device should trigger exactly one unknown alert (when first seen), then be classified and excluded. An exclusion list enables this.

### Alternative 3: Dynamic classification stored in the database

**Description:** Store the sensor classification (periodic/excluded) in a MariaDB table instead of a YAML file.

**Rejected because:** Adds schema complexity (new table, migration required) and operational complexity (UI or CLI tool needed to update classifications). The YAML file is simpler, human-readable, and can be edited with any text editor on the host. The classification changes infrequently enough that a file-based approach is operationally superior (Constitution Principle VII — Minimal Surface Area).

## Related

- Supersedes: None
- Related requirements: FR-MON-002, FR-MON-004, FR-MON-005, FR-MON-007
- Related NFRs: None directly
- Related explore option: OPT-B
