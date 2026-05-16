# Concept of Operations

**System:** mqttlogger
**Feature:** 008-grafana-dashboard (last updated)
**Date:** 2026-05-16
**Status:** DRAFT
**Last Updated By:** se-conops skill

---

## 1. System Overview

mqttlogger is a continuous, unattended data capture service that records every environmental sensor reading published on a home network into a persistent database. Sensor devices throughout the home — measuring temperature, humidity, and other environmental conditions — publish their readings to a central message broker. Without mqttlogger, those readings exist only momentarily and are permanently lost when the next reading arrives. mqttlogger's sole purpose is to intercept every reading the moment it is published and write it to durable storage, building a historical record that grows continuously over time.

The primary motivation for this record is energy optimisation. The household operator wants to understand how the home behaves across seasons, how specific rooms respond to renovations or temporary interventions, and whether measures taken to improve comfort or reduce energy consumption are actually working. Because cause and effect in a home environment play out over weeks and months, the value of each individual reading is not immediately apparent — it is realised later, when patterns emerge from the accumulated data. A reading that was never captured cannot be reconstructed.

mqttlogger operates in the background without any user interface. It does not display information, produce reports, or control any devices. Its output is a database table, updated continuously, from which all analysis and decision-making flows.

Feature 008 adds a Grafana dashboard as a companion service in the same Docker Compose stack. The dashboard provides a browser-accessible view of the historical sensor data stored in MariaDB. It does not capture data, control devices, or alter the database in any way — it is a read-only window into the record that mqttlogger builds. The dashboard enables the operator to answer questions such as "how hot was the attic last Tuesday afternoon" in under a minute, without writing SQL queries directly against the database.

---

## 2. Operational Environment

**Deployment Context:** mqttlogger runs as a Docker Compose stack (logger service, MQTT broker, MariaDB database) on a dedicated headless x86 mini PC on the home network. This host runs continuously and also provides DNS-level ad blocking (PiHole) and network management (UniFi Controller). It is consumer-grade hardware — not enterprise-grade — and is connected to a standard residential power supply with no UPS or redundant power.

**Normal Operating Conditions:** Continuous, 24/7 unattended operation. The system receives no human interaction during normal operation. No scheduled jobs, no polling, no manual triggering. Readings arrive whenever sensors publish, which occurs on sensor-defined intervals independent of the logger.

**Abnormal / Degraded Conditions:**

| Condition | Description | Current System Response | Data Impact |
|-----------|-------------|------------------------|-------------|
| Power outage | Host loses power; all services go down simultaneously | No automatic recovery — host must be manually powered on after outage; Docker Compose then restarts all containers automatically | All readings during outage window permanently lost |
| Logger container crash | Unexpected process death not caught by a stop signal | Docker Compose restart policy recovers the container; a data gap exists for the crash-to-restart interval | Gap size depends on restart time; gap has no visible marker in the record |
| Broker temporarily unavailable | Broker connection lost during operation | Logger reconnects indefinitely without operator intervention | Readings published during outage are lost; no MQTT message persistence across broker restarts |
| Database temporarily unavailable | DB write fails | Message is logged and discarded; operation continues | Readings during DB outage are permanently lost; this is accepted behaviour |
| HomeMatic/CCU3 restart | RedMatic publishes zero values for all readings on startup | Logger captures and stores all values including spurious zeros | Spurious records in the dataset; physically impossible values (e.g. 0% humidity) appear as legitimate entries |

### External Dependencies (Inputs)

| System | Role | Notes |
|--------|------|-------|
| HomeMatic IP sensors | Physical measurement devices | Measure and transmit temperature, humidity, and other environmental readings; independently operated |
| CCU3 running RedMatic | MQTT bridge | Translates HomeMatic IP readings into MQTT messages and publishes them to the broker; known to publish startup zeros on restart |
| Eclipse Mosquitto broker | Message transport | Receives sensor readings from RedMatic and delivers them to mqttlogger; co-hosted on the same mini PC |

### External Dependents (Outputs)

| System | Role | Notes |
|--------|------|-------|
| MariaDB database | Persistence target | Receives and stores every captured reading; co-hosted on the same mini PC |
| Jupyter notebooks | Ad-hoc analysis | Reads from MariaDB for exploratory data analysis; not a real-time consumer |
| Grafana dashboard | Visualisation consumer | Reads from MariaDB via a read-only datasource connection; co-hosted on the same mini PC; browser-accessible on the home LAN; feature 008 |
| Operator notification device (iPhone) | Alert recipient | Receives push notifications from the self-hosted ntfy server via the home LAN; the ntfy app connects directly to the LAN IP of the ntfy container — **notification delivery requires the device to be on the home network**. Off-network delivery (operator away from home) is not currently supported. See RISK-023. |

### Operational Constraints

- **No formal maintenance windows.** Downtime can occur at operator discretion, but every minute offline is a minute of sensor data permanently lost.
- **Loss-cost is roughly uniform** across time, with peaks during active experiments (e.g. summer cooling trials when the attic and bedroom temperature data is being actively used to evaluate interventions).
- **Host auto-restart is not configured.** The mini PC BIOS is not set to restore power after an outage; all power-loss recovery requires manual host power-on before any services can restart.
- **Notification delivery requires home network presence.** The ntfy push notification server is LAN-only; the operator's iPhone receives monitoring alerts only when connected to the home Wi-Fi network. A crash or sensor silence that occurs while the operator is away from home will not be notified until the operator returns and the device reconnects to the LAN. Off-network notification requires a VPN, Tailscale, or ntfy cloud relay — none of which are currently configured (see RISK-023).

---

## 3. Stakeholders and Roles

Full profiles are in `specs/002-mqttlogger-baseline/00-stakeholders/`. Summary operational roles:

| Stakeholder | Operational Role |
|-------------|-----------------|
| STK-001 — Developer/Operator/Owner/Data Consumer | Deploys and maintains the system; the sole person who interacts with it; the sole beneficiary of its output. All roles are held by one person. |
| STK-002 — Future Maintainer | The same person returning after an extended absence; needs reliable re-orientation artefacts and an unambiguous view of the deployed system state. |

---

## 4. Modes of Operation

| Mode ID | Mode Name | Entry Trigger | Description | Exit Trigger | Safety Notes |
|---------|-----------|---------------|-------------|--------------|--------------|
| MODE-001 | Normal Operation | Startup complete; broker and database connections established | Continuous capture of sensor readings; every published message is received, parsed, and written to the database; lifecycle events are logged | SIGTERM / SIGINT received, or unrecoverable failure | None |
| MODE-002 | Startup / Initialisation | Container starts | Configuration is loaded and validated; broker and database connections are attempted; database readiness is confirmed before the first connection attempt | All connections established; MODE-001 entered | None — fails fast and exits if configuration is missing or invalid |
| MODE-003 | Graceful Shutdown | SIGTERM / SIGINT received | Message receipt stops; any in-flight database write is completed; broker connection is closed cleanly; process exits with success status | Process exits | None |
| MODE-004 | Degraded — Broker Unavailable | Broker connection lost during MODE-001 | Reconnection attempts continue indefinitely using built-in retry; no messages are received during this interval; all readings published during this interval are permanently lost | Broker reconnected; MODE-001 resumes | None |
| MODE-005 | Degraded — Database Unavailable | Database write fails during MODE-001 | The failed message is logged and discarded; operation continues; subsequent messages are processed normally; no buffering occurs | Database write succeeds on next attempt; MODE-001 continues | None — data loss during DB outage is accepted by design |
| MODE-006 | Degraded — Upstream Noise | CCU3/RedMatic restarts and floods broker with startup zeros | Logger continues normal operation; all messages including physically impossible zero values are captured and stored; spurious records enter the dataset | Startup zero flood ceases; normal sensor readings resume | None — spurious data is a known upstream behaviour; mitigation is on the HomeMatic side |
| MODE-007 | Maintenance | Operator initiates deliberate downtime | Operator stops the Docker Compose stack, applies changes (code update, configuration change, dependency upgrade, image rebuild), and restarts the stack | Stack restarted and MODE-002 entered | None — all readings during maintenance window are permanently lost |
| MODE-008 | Dashboard Startup | sietchtabr boots or Docker Compose stack starts | Grafana container initialises; datasource connection to MariaDB is established; dashboards become available in the browser | Grafana HTTP endpoint responds and datasource is healthy | None |
| MODE-009 | Dashboard Normal Operation | MODE-008 complete | Operator browses sensor data via browser; time-range filtering, panel inspection, and ad-hoc queries are all available; no writes to the database | Stack shutdown or loss of MariaDB connection | None |
| MODE-010 | Dashboard Degraded — Database Unavailable | MariaDB connection lost while Grafana is running | Grafana is reachable in the browser but panels display a datasource error; no historical data is shown; Grafana recovers automatically when MariaDB becomes available again | MariaDB connection re-established; panels resume showing data without operator intervention | None |

---

## 5. Success Criteria

| Criterion ID | Description | Measurable Threshold | Stakeholder |
|--------------|-------------|----------------------|-------------|
| SC-CONOPS-001 | Every sensor reading published to the broker is captured and stored | 100% of readings stored within 5 seconds of publication under normal operating conditions | STK-001 |
| SC-CONOPS-002 | The service operates without manual intervention for extended periods | Continuous operation for 30 or more days without operator action under normal home network conditions | STK-001 |
| SC-CONOPS-003 | Any failure that prevents data capture is visible without active inspection | TBD — no passive notification mechanism currently exists; this criterion is unmet by the current implementation | STK-001 |
| SC-CONOPS-004 | The completeness of the historical record can be verified for any given time period | Operator can confirm the record is complete for a specified period without manual cross-referencing | STK-001 |
| SC-CONOPS-005 | The service recovers from broker outage without operator intervention | Reconnection achieved automatically; no operator action required | STK-001 |
| SC-CONOPS-006 | The service exits cleanly when stopped | Exit within 10 seconds of stop signal; no orphaned broker connections; no partial database writes | STK-001 |
| SC-CONOPS-007 | A returning developer can re-orient to current system state within one work session | Developer can identify deployed version, understand current state, and resume productive work within one session after months-long absence | STK-002 |
| SC-CONOPS-008 | The dashboard shows recent sensor data when opened | At least one reading from within the last hour is visible in any time range that includes the present | STK-001 |
| SC-CONOPS-009 | The operator can answer a specific historical question without writing SQL | Operator can filter by sensor/room and time range and read a result in under one minute | STK-001 |
| SC-CONOPS-010 | The dashboard recovers automatically after sietchtabr restarts | Grafana panels show data without any manual operator action after a power-cycle and restart | STK-001 |
| SC-CONOPS-011 | The dashboard does not require manual refresh to show current data | No operator-initiated action is needed to see the latest readings within the normal polling cadence | STK-001 |

---

## 6. Open Issues

| ID | Issue | Owner | Target Resolution |
|----|-------|-------|-------------------|
| OI-001 | Host BIOS not configured for auto-restart after power loss — all power outage recovery requires manual host power-on | Chris | Before next Phase gate — BIOS setting change is a one-time infrastructure action |
| OI-002 | No passive notification mechanism exists for container crash or data capture failure — SC-CONOPS-003 is unmet by current implementation | Chris | Architecture / NFR phase |
| OI-003 | No data completeness verification mechanism — SC-CONOPS-004 is unmet by current implementation | Chris | Architecture / NFR phase |
| OI-004 | CCU3/RedMatic "publish cached values on start" setting not yet evaluated or changed — spurious startup zeros continue to pollute the dataset | Chris | Before next active experiment window |
| OI-005 | ~~Future dashboard identified as downstream consumer but not yet designed~~ **CLOSED** — Grafana dashboard is now being designed as feature 008 | Chris | **Closed 2026-05-16** |

---

*This document describes the operational concept only. Architecture, design, and implementation decisions are out of scope for this document.*
