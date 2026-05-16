# Operational Scenarios

**System:** mqttlogger
**Feature:** 008-grafana-dashboard (last updated)
**Date:** 2026-05-16
**Status:** DRAFT
**Last Updated By:** se-conops skill

---

## Scenario Index

| ID | Name | Type | Primary Stakeholder | Priority |
|----|------|------|---------------------|----------|
| SCN-001 | Continuous sensor data capture | Normal Success | STK-001 | High |
| SCN-002 | Recovery after power outage | Alternative Success | STK-001 | High |
| SCN-003 | Silent logger crash and restart | System Failure | STK-001 | High |
| SCN-004 | Misconfigured startup | Operator Error | STK-001 | Medium |
| SCN-005 | Broker temporarily unavailable | Degraded Operation | STK-001 | High |
| SCN-006 | HomeMatic/CCU3 restart — spurious zero flood | Degraded Operation | STK-001 | Medium |
| SCN-007 | Planned maintenance update | Maintenance | STK-001 / STK-002 | Medium |
| SCN-008 | Browse historical sensor data | Normal Success | STK-001 | High |
| SCN-009 | Dashboard recovery after power outage | Alternative Success | STK-001 | High |
| SCN-010 | Time range returns no data | Operator Error | STK-001 | Medium |
| SCN-011 | Grafana cannot connect to database | System Failure | STK-001 | High |
| SCN-012 | Database temporarily unavailable mid-session | Degraded Operation | STK-001 | Medium |

---

## Scenarios

### SCN-001 — Continuous Sensor Data Capture

**Type:** Normal Success
**Primary Stakeholder:** STK-001
**Precondition:** All services are running (broker, database, logger); HomeMatic sensors are publishing readings; configuration is valid.

**Scenario Steps:**

1. A HomeMatic IP sensor measures an environmental value (e.g. cellar temperature: 14.3°C).
2. The sensor transmits the reading to the CCU3.
3. RedMatic on the CCU3 translates the reading into an MQTT message and publishes it to the Mosquitto broker on the topic `environment/indoor/cellar_front/temperature`.
4. mqttlogger, subscribed to all topics under `environment/#`, receives the message.
5. The reading is parsed, timestamped, and written to the database as a discrete record containing the capture date, time, full topic path, and value.
6. A log entry is written confirming the successful write.
7. Steps 1–6 repeat for every sensor in the home, continuously, without operator intervention.

**Successful Outcome:** The database grows continuously with a complete, timestamped record of every sensor reading. The operator can query any sensor, any room, any time period and find the data there.

**Failure Modes Within This Scenario:**
- Step 4: Logger has silently crashed — message is published to broker but never received; no record is written; no notification occurs (see SCN-003).
- Step 5: Payload is malformed — logger logs the error and discards the message; operation continues.
- Step 5: Database is unavailable — logger logs the error and discards the message; data is permanently lost (MODE-005).

**Consequences of Failure:** Individual readings are lost permanently. If the failure persists undetected, a gap grows in the historical record that cannot be reconstructed retroactively.

**Notes:** Relates to NEED-STK-001-001. The operator currently has no passive confirmation that this scenario is executing correctly on any given day.

---

### SCN-002 — Recovery After Power Outage

**Type:** Alternative Success
**Primary Stakeholder:** STK-001
**Precondition:** All services are running; a power outage occurs affecting the mini PC host.

**Scenario Steps:**

1. A power outage cuts power to the mini PC. All services — broker, database, logger, PiHole, UniFi Controller — go down simultaneously.
2. Sensor readings published during the outage reach the broker (which is also offline) and are permanently lost.
3. Power is restored to the home.
4. The mini PC does not automatically restart — the BIOS is not configured for power-loss recovery.
5. The operator notices the host is offline (e.g. DNS stops working because PiHole is down, or UniFi management becomes unavailable).
6. The operator physically or remotely powers on the mini PC.
7. The host boots; Docker Compose starts the container stack automatically.
8. The database readiness check passes; the logger connects to the broker and resumes normal capture.
9. Normal operation (MODE-001) resumes. The data gap from the outage period is permanent.

**Successful Outcome:** The service resumes capturing data without further operator intervention after the host is powered on. The gap in the record is bounded by the outage duration plus the time until the operator noticed and powered on the host.

**Failure Modes Within This Scenario:**
- Step 4/6: Operator does not notice the host is offline — gap grows unboundedly until noticed (the absence of PiHole DNS is the most likely indicator).
- Step 7–8: A service fails to start cleanly — operator must diagnose and resolve before capture resumes.

**Consequences of Failure:** An unnoticed outage results in a gap in the historical record proportional to the time until discovery. During an active experiment period (e.g. summer cooling trial), this gap may invalidate the experiment's dataset.

**Notes:** OI-001 — BIOS auto-restart configuration is an infrastructure action that would eliminate step 4–6 and reduce recovery time. Relates to NEED-STK-001-004.

---

### SCN-003 — Silent Logger Crash and Restart

**Type:** System Failure
**Primary Stakeholder:** STK-001
**Precondition:** All services are running normally; the logger container dies unexpectedly (process crash, OOM kill, or unhandled exception).

**Scenario Steps:**

1. The logger container dies unexpectedly. No SIGTERM is issued; no graceful shutdown occurs; no final log entry is written.
2. Docker Compose detects the container has exited and, per the configured restart policy, restarts it automatically.
3. The logger container restarts; configuration is loaded; connections are re-established; normal capture resumes.
4. A gap exists in the database record for the interval between crash and restart. The gap has no marker — it appears as an absence of readings rather than an explicit error record.
5. The operator has no notification that a crash occurred. The system appears healthy from the outside.
6. The gap is discovered only when the operator actively inspects the database — by querying for a time range and noticing the absence of expected readings — or never.

**Successful Outcome (partial):** The service recovers automatically. The data gap is bounded by the crash-to-restart interval (likely seconds to minutes). Normal capture resumes without operator action.

**Failure Modes Within This Scenario:**
- The restart policy is not configured or fails — container does not restart; gap grows indefinitely; system silently stops capturing (see RISK-016).
- The crash recurs repeatedly — Docker Compose may enter a restart loop; eventually data capture may cease entirely.
- The gap is never discovered — analyses conducted over the affected period produce incorrect results without the operator knowing.

**Consequences of Failure:** An undetected data gap in the historical record. If the gap occurs during an active experiment, the experiment's conclusions may be invalid. The operator cannot distinguish "no readings were published" from "readings were published but not captured."

**Notes:** This is the highest-priority failure scenario from the stakeholder analysis ("a system that fails invisibly is worse than one that fails loudly"). Relates to NEED-STK-001-002, NEED-STK-001-003, RISK-016.

---

### SCN-004 — Misconfigured Startup

**Type:** Operator Error
**Primary Stakeholder:** STK-001
**Precondition:** The operator is deploying the service to a new host or after a configuration change; the configuration file is missing, malformed, or contains incorrect connection details.

**Scenario Steps:**

1. The operator starts the Docker Compose stack.
2. The logger container starts and attempts to load the configuration file.
3a. (Missing or malformed config) The configuration file is absent or cannot be parsed. The logger exits immediately with a non-zero status code and a human-readable error message identifying the problem.
3b. (Wrong connection details) The configuration file loads successfully but contains an incorrect broker address, database host, or credentials.
4b. The logger attempts to connect and fails. Connection errors are logged; reconnection attempts begin.
5b. The operator inspects the logs, identifies the incorrect values, corrects the configuration file, and restarts the container.

**Successful Outcome:** The operator receives a clear, actionable error message that identifies the configuration problem, corrects it, and the service starts successfully.

**Failure Modes Within This Scenario:**
- The error message is unclear or does not identify which parameter is wrong — the operator must guess or trial-and-error through the configuration.
- The wrong-credentials case causes indefinite reconnection attempts with no clear terminal failure — the operator may not realise the service is not capturing.

**Consequences of Failure:** Delayed startup; readings lost during the diagnosis and correction interval. If the misconfiguration is not immediately noticed (e.g. it happens during a remote reconfiguration), the service may appear to be running while capturing nothing.

**Notes:** FR-016 covers the missing/malformed case. The wrong-credentials case is less explicitly handled in current requirements. Relates to NEED-STK-001-002.

---

### SCN-005 — Broker Temporarily Unavailable

**Type:** Degraded Operation
**Primary Stakeholder:** STK-001
**Precondition:** The service is running normally; the Mosquitto broker becomes unavailable (container crash, deliberate restart, or broker-level fault).

**Scenario Steps:**

1. The Mosquitto broker becomes unavailable.
2. The logger loses its broker connection. An error is logged.
3. The logger enters MODE-004 (Degraded — Broker Unavailable) and begins reconnecting indefinitely.
4. Sensor readings published during this interval reach the broker (which is also offline or restarting) and are permanently lost.
5. The broker comes back online.
6. The logger reconnects automatically. A log entry confirms reconnection.
7. Normal capture resumes (MODE-001). The data gap from the outage period is permanent.

**Successful Outcome:** The service recovers from broker unavailability without operator intervention. The operator can find the outage window in the log file if needed.

**Failure Modes Within This Scenario:**
- The broker does not recover — the logger remains in reconnecting state indefinitely; capture does not resume.
- The broker restart triggers a HomeMatic/CCU3 startup zero flood (see SCN-006).

**Consequences of Failure:** Data loss proportional to broker outage duration. Since broker and logger are co-hosted, broker instability is expected to be rare.

**Notes:** FR-015 covers the reconnection behaviour. Since broker and logger share a host, broker restarts are rare except during deliberate maintenance. Relates to NEED-STK-001-004.

---

### SCN-006 — HomeMatic/CCU3 Restart — Spurious Zero Flood

**Type:** Degraded Operation
**Primary Stakeholder:** STK-001
**Precondition:** The service is running normally; the CCU3 is restarted (for any reason, including RedMatic update, HomeMatic maintenance, or power interruption to the CCU3 specifically).

**Scenario Steps:**

1. The CCU3 restarts and RedMatic initialises.
2. RedMatic publishes zero values for every registered sensor topic simultaneously — including physically impossible values such as 0°C and 0% humidity for sensors that should be reporting ambient conditions.
3. mqttlogger receives all zero-value messages and stores them as legitimate readings in the database.
4. The zero flood ceases as RedMatic completes initialisation and begins publishing real sensor values.
5. The database now contains spurious records timestamped at the CCU3 restart time.

**Successful Outcome (partial):** The logger continues operating normally. Real readings resume after the startup flood. The spurious records are present in the database and must be accounted for in any analysis.

**Failure Modes Within This Scenario:**
- Spurious zeros are indistinguishable from legitimate zero readings for sensors where zero is a physically valid value (e.g. CO₂ sensors, contact sensors reporting closed state).
- The spurious records are not identified or excluded in analysis, leading to incorrect conclusions (e.g. apparent 0°C temperature spikes in the cellar dataset).

**Consequences of Failure:** Data quality degradation. Analyses that do not account for startup zeros will produce incorrect results. The severity depends on how often the CCU3 restarts and which sensors are affected.

**Notes:** Known upstream behaviour. Potential mitigation: disable "publish cached values on start" in RedMatic (OI-004). Relates to NEED-STK-001-005, RISK-012. If RedMatic mitigation is not fully reliable, a flagging strategy within mqttlogger may be required.

---

### SCN-007 — Planned Maintenance Update

**Type:** Maintenance
**Primary Stakeholder:** STK-001 / STK-002
**Precondition:** The operator decides to update the service — new code, dependency change, configuration update, or image rebuild.

**Scenario Steps:**

1. The operator SSHes into the host.
2. The operator pulls the latest code from the repository (`git pull`).
3. If dependencies or the Dockerfile have changed, the operator rebuilds the container image (`docker compose build`).
4. The operator stops the running stack (`docker compose down`). All services — logger, broker, database — stop. Readings published during this window are permanently lost.
5. The operator starts the updated stack (`docker compose up -d`).
6. The database readiness check passes; the logger connects to the broker and resumes capture.
7. The operator verifies the service is running (`docker compose ps`) and optionally inspects the log output.
8. The operator confirms a new reading has appeared in the database.

**Successful Outcome:** The updated service is running. The maintenance window is bounded and the operator has confirmed capture has resumed. The data gap is limited to the stack downtime.

**Failure Modes Within This Scenario:**
- The updated image fails to build — the operator must diagnose the build error before restarting; gap extends.
- The updated service fails to start (configuration mismatch, schema change) — operator must diagnose; gap extends.
- The operator forgets to verify capture has resumed — the maintenance appears successful but the service is silently not capturing (see SCN-003).

**Consequences of Failure:** Extended data gap; or a silent non-capture state post-maintenance that goes undetected.

**Notes:** STK-002 perspective: after a long absence, step 2 must be preceded by re-orientation (reading quick-start doc, identifying deployed version, checking backlog). Without these artefacts, the maintenance session begins with context reconstruction rather than productive action. Relates to NEED-STK-002-001, NEED-STK-002-002.

---

### SCN-008 — Browse Historical Sensor Data

**Type:** Normal Success
**Primary Stakeholder:** STK-001
**Precondition:** All services are running (logger, database, Grafana); sensor readings are present in the database.

**Scenario Steps:**

1. The operator opens a browser on any device connected to the home LAN and navigates to the Grafana URL (e.g. `http://sietchtabr:3000`).
2. The Grafana home dashboard loads, showing available panels.
3. The operator selects a time range of interest (e.g. last 7 days, or a specific date range).
4. The operator navigates to a panel or dashboard showing a specific sensor or room (e.g. attic temperature).
5. The panel queries MariaDB and renders the historical readings as a time-series graph.
6. The operator reads the data and draws a conclusion (e.g. "the attic reached 38°C on three afternoons last week").

**Successful Outcome:** The operator answers a specific question about historical sensor data in under one minute without writing any SQL.

**Failure Modes Within This Scenario:**
- Step 5: Panel loads but shows no data for the selected range — operator may not realise the time range predates available data (see SCN-010).
- Step 5: Panel shows data that appears incorrect — data quality issue in the underlying record (spurious zeros from CCU3 restart; see SCN-006).

**Consequences of Failure:** Operator cannot answer the question; falls back to direct SQL query. No data loss — the dashboard is read-only.

**Notes:** Directly satisfies NEED-STK-001-010 and SC-CONOPS-009. Relates to OI-005 (now closed).

---

### SCN-009 — Dashboard Recovery After Power Outage

**Type:** Alternative Success
**Primary Stakeholder:** STK-001
**Precondition:** sietchtabr has lost power and been manually powered back on; Docker Compose has restarted all containers.

**Scenario Steps:**

1. Power is restored; the operator powers on sietchtabr.
2. Docker Compose starts all containers: MariaDB, Mosquitto, mqtt_logger, Grafana.
3. Grafana starts and attempts to connect to MariaDB. MariaDB may still be initialising.
4. Grafana retries the datasource connection until MariaDB is ready.
5. Once MariaDB is healthy, Grafana datasource becomes active.
6. The operator opens a browser and navigates to the Grafana URL.
7. Panels load and show historical data up to the point before the outage. No operator action beyond opening the browser is required.

**Successful Outcome:** The dashboard is accessible and shows historical data without any manual configuration or restart steps after the host comes back online.

**Failure Modes Within This Scenario:**
- MariaDB takes longer than Grafana's connection timeout to initialise — Grafana marks datasource as failed and does not retry automatically; operator must restart the Grafana container.
- The operator opens the browser before MariaDB is ready and sees a datasource error — refreshing the browser after a short wait resolves it.

**Consequences of Failure:** Dashboard temporarily unavailable post-restart; operator must manually intervene to restore it. No data loss — dashboard is read-only.

**Notes:** Relates to SC-CONOPS-010. Container startup ordering in Docker Compose should use a health check dependency on MariaDB to prevent the primary failure mode above.

---

### SCN-010 — Time Range Returns No Data

**Type:** Operator Error
**Primary Stakeholder:** STK-001
**Precondition:** Dashboard is running normally; operator selects a time range.

**Scenario Steps:**

1. The operator sets a time range in Grafana (e.g. "last 30 days" — but the logger was only deployed 10 days ago, or the operator accidentally selects a future date range).
2. The panel query returns zero rows from MariaDB.
3. Grafana displays empty panels or a "No data" message.
4. The operator realises the selected time range contains no readings and adjusts it.

**Successful Outcome:** The operator adjusts the time range and data appears as expected.

**Failure Modes Within This Scenario:**
- The operator interprets empty panels as a system failure rather than an empty time range — unnecessary investigation is triggered.
- The time range covers a genuine gap in the record (e.g. a logger outage period) — the operator cannot distinguish "no data was captured" from "wrong time range selected."

**Consequences of Failure:** Wasted investigation time. No data loss or system harm.

**Notes:** Clear "No data" messaging in panels reduces confusion. A visible panel annotation for known outage periods would mitigate the gap-vs-range ambiguity, but is not in scope for feature 008.

---

### SCN-011 — Grafana Cannot Connect to Database

**Type:** System Failure
**Primary Stakeholder:** STK-001
**Precondition:** Grafana is running; MariaDB is unavailable or the datasource credentials are incorrect.

**Scenario Steps:**

1. The operator opens the browser and navigates to the Grafana URL.
2. Grafana loads the dashboard UI but panels fail to render data.
3. Panels display a datasource error (e.g. "Error: failed to query data" or a connection refused message).
4. The operator inspects the Grafana datasource settings or container logs to identify the cause.
5a. (Credentials wrong) Operator corrects the datasource configuration and panels recover.
5b. (MariaDB unavailable) Operator investigates MariaDB container status and resolves the underlying fault.

**Successful Outcome:** The operator identifies the cause from the error message, resolves it, and panels return to showing data.

**Failure Modes Within This Scenario:**
- The error message is not actionable — operator cannot determine whether the fault is credentials, network, or MariaDB being down.
- The operator does not notice the error (e.g. checking a panel on a mobile device where the error is not prominently displayed).

**Consequences of Failure:** Dashboard is unavailable for data access. No data loss — dashboard is read-only. Underlying mqttlogger capture may or may not be affected depending on whether the MariaDB fault is the cause.

**Notes:** Relates to SC-CONOPS-008. Grafana datasource configuration must use a dedicated read-only database user, not the mqttlogger write user, to limit blast radius of credential exposure (see RISK-027).

---

### SCN-012 — Database Temporarily Unavailable Mid-Session

**Type:** Degraded Operation
**Primary Stakeholder:** STK-001
**Precondition:** The operator is actively browsing the dashboard; MariaDB becomes temporarily unavailable (e.g. during a Docker Compose restart of MariaDB only).

**Scenario Steps:**

1. The operator is viewing panels in the browser.
2. MariaDB becomes unavailable mid-session.
3. Subsequent panel refreshes or time-range changes return datasource errors.
4. The operator notices the error state.
5. MariaDB recovers (automatically, e.g. after a container restart completes).
6. Grafana datasource reconnects automatically.
7. The operator refreshes the browser; panels return to showing data.

**Successful Outcome:** Grafana recovers automatically once MariaDB is back, requiring only a browser refresh from the operator.

**Failure Modes Within This Scenario:**
- Grafana does not recover automatically — operator must manually restart the Grafana container.

**Consequences of Failure:** Brief dashboard unavailability. No data loss.

**Notes:** Relates to MODE-010 (Dashboard Degraded). Automatic recovery on datasource reconnect is standard Grafana behaviour and is not expected to require configuration.
