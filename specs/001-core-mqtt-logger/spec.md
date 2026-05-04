# Feature Specification: Core MQTT Sensor Logging Service

**Feature Branch**: `001-core-mqtt-logger`
**Created**: 2026-05-04
**Status**: Draft
**Input**: Existing codebase — mqttlogger

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Automatic Sensor Data Capture (Priority: P1)

A home resident wants every sensor reading published by devices in and around the home to be
automatically captured and stored without manual intervention, so that historical environmental
data is available for later review and analysis.

**Why this priority**: This is the entire purpose of the system. Without reliable capture, no
other function has value. Every other story depends on data being stored.

**Independent Test**: Deploy the service with a connected broker. Publish a sensor reading to
the broker. Confirm a corresponding record exists in the data store within 5 seconds, containing
the correct timestamp, device identifier, and value.

**Acceptance Scenarios**:

1. **Given** a sensor device publishes a numeric temperature reading to the broker, **When** the
   logging service receives it, **Then** a new record is written to persistent storage containing
   the exact value, the device's full topic address, and the timestamp at time of receipt.

2. **Given** a sensor device publishes a boolean state (e.g., fan on/off), **When** the logging
   service receives it, **Then** the boolean is stored as an equivalent numeric value (1 or 0)
   with the correct device identifier and timestamp.

3. **Given** multiple sensors in different rooms publish readings within the same second, **When**
   the logging service receives them, **Then** all readings are stored as separate records, each
   carrying its own device identifier, so location-level querying is unambiguous.

---

### User Story 2 — Service Continuity Across Restarts (Priority: P1)

A system operator wants the logging service to start automatically when the host machine powers
on and to recover from transient network or broker outages without manual intervention, so that
data collection is not interrupted by routine infrastructure events.

**Why this priority**: A logging service that requires human restarts after every power cycle or
network blip fails its core promise of continuous, unattended data capture.

**Independent Test**: Start the full stack (broker, logger, database). Restart the broker
container. Confirm the logger reconnects and continues storing new readings without the operator
taking any action.

**Acceptance Scenarios**:

1. **Given** the logging service and all dependencies are running, **When** the host machine is
   rebooted, **Then** all services restart automatically and resume data capture without operator
   intervention.

2. **Given** the logging service is running and the broker temporarily becomes unavailable,
   **When** the broker comes back online, **Then** the logger reconnects and resumes capturing
   readings; no operator action is required.

---

### User Story 3 — Graceful Service Shutdown (Priority: P2)

A system operator wants to stop the logging service without leaving stale broker connections or
losing in-flight message data, so that planned maintenance does not corrupt the data store or
cause resource leaks on the broker.

**Why this priority**: Unclean shutdowns accumulate phantom broker connections and may leave
partially-written records in the database, both of which require manual cleanup.

**Independent Test**: With the service running and actively receiving messages, send a stop
signal to the service process. Confirm the service exits within 10 seconds, and that no
in-flight message records are missing and no orphaned connections remain on the broker.

**Acceptance Scenarios**:

1. **Given** the logging service is running and actively receiving messages, **When** a stop
   signal is sent to the service, **Then** the service finishes processing any in-flight message,
   stops subscribing, disconnects from the broker cleanly, and exits with a success status within
   10 seconds.

2. **Given** a clean shutdown has completed, **When** the broker connection list is inspected,
   **Then** no stale connections attributable to the logger are present.

---

### User Story 4 — Operational Diagnostics via Logs (Priority: P2)

A system operator wants to inspect the service's activity through durable, bounded log files so
that connection failures, data write errors, and subscription events can be diagnosed without
stopping the service or requiring interactive access to the running process.

**Why this priority**: As a headless, long-running daemon with no UI, logs are the only
operational instrument for diagnosing failures after the fact.

**Independent Test**: With the service running, produce a connection failure (e.g., point
the service at an unreachable broker). Read the log file and confirm the failure event,
timestamp, and affected component are recorded. Confirm the log file does not grow unboundedly
over extended operation.

**Acceptance Scenarios**:

1. **Given** the logging service is running, **When** it successfully connects and subscribes to
   the broker, **Then** the log file contains a timestamped record of the connection and each
   topic subscription.

2. **Given** a database write fails, **When** the error occurs, **Then** the log file contains a
   timestamped entry identifying the failure cause so an operator can diagnose and resolve it.

3. **Given** the service has been running for an extended period, **When** the log file is
   inspected, **Then** the total size of all log files is bounded (older entries have been
   rotated out) and the log directory has not consumed unbounded disk space.

4. **Given** an operator needs verbose diagnostic output, **When** the service is started with
   the debug flag enabled, **Then** the log output includes message-level detail (topic, payload,
   parsed value) without requiring a code change or service rebuild.

---

### User Story 5 — Zero-Code Deployment Configuration (Priority: P3)

A system operator wants to deploy the logging service to a new host by modifying only a
configuration file — without touching application code — so that the service can be relocated or
reconfigured without a development cycle.

**Why this priority**: Hardcoded connection details couple the deployment environment to the
source code, making any infrastructure change unnecessarily risky and time-consuming.

**Independent Test**: Starting from a fresh host with no prior installation, modify only the
configuration file to point at the correct broker and database. Start the service. Confirm it
connects and begins storing readings successfully.

**Acceptance Scenarios**:

1. **Given** a fresh host with the service container image available, **When** an operator
   supplies a configuration file with the correct broker address and database credentials and
   starts the service, **Then** the service connects and begins capturing data with no code
   changes.

2. **Given** the service is configured for one broker, **When** the configuration file is updated
   to point at a different broker and the service is restarted, **Then** the service connects to
   the new broker without any code modification.

---

### Edge Cases

- What happens when a message payload cannot be parsed as a number or boolean? (malformed payload)
- What happens if the database is unavailable when a message arrives?
- How does the service behave if the configuration file is missing or malformed on startup?
- What happens if the broker sends a retained message flood on (re)connect?
- What happens if disk space is exhausted and a new log file cannot be created?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST subscribe to all topics under the `environment/` address space
  upon connecting to the broker.
- **FR-002**: The system MUST persist each received message as a discrete record containing:
  capture date, capture time, full device address (topic), and measurement value.
- **FR-003**: The system MUST convert boolean message payloads to a numeric equivalent (1 for
  true, 0 for false) before storage.
- **FR-004**: The system MUST use the full MQTT topic string as the device identifier in every
  stored record, preserving the complete location and reading-type hierarchy.
- **FR-005**: The system MUST emit a timestamped log entry for each of the following events:
  broker connection, topic subscription, message receipt, storage write, disconnection, and
  any error condition.
- **FR-006**: The system MUST rotate log files when they reach a configured size limit and
  retain a bounded number of historical log files.
- **FR-007**: The system MUST handle a process stop signal by completing any in-flight storage
  write, stopping message receipt, disconnecting from the broker, and exiting with a success
  status.
- **FR-008**: The system MUST read all connection parameters (broker address and port, database
  host, port, name, and credentials) from an external configuration source; none of these values
  may be hard-coded in the application.
- **FR-009**: The system MUST run as a non-privileged (non-root) operating system user.
- **FR-010**: The system MUST be deployable alongside its broker and database dependencies via
  a single container orchestration command.
- **FR-011**: The system MUST expose a debug logging mode that can be activated at start time
  without modifying application code or rebuilding the service.
- **FR-012**: The database MUST be considered ready before the logging service attempts its
  first connection, to prevent startup failures due to initialization race conditions.

### Key Entities

- **Sensor Reading**: A single captured measurement from one sensor device at one point in time.
  Attributes: unique identifier, capture date, capture time, device address (full topic path),
  measurement value (numeric).

- **Device Address**: The full hierarchical MQTT topic path identifying a sensor's physical
  location and the type of measurement it reports. Structured as:
  `{concern}/{indoor-or-outdoor}/{room}/{reading-type}`. Examples:
  `environment/indoor/cellar_front/temperature`,
  `environment/outdoor/patio/humidity`.

- **Configuration**: An external input supplying all environment-specific parameters needed to
  connect to the broker and the database. Must be modifiable without touching application code.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every sensor message published to the broker is stored as a complete record within
  5 seconds of publication under normal operating conditions.
- **SC-002**: The service runs continuously for 30 or more days without requiring manual
  intervention under normal household network conditions.
- **SC-003**: All stored records can be filtered by device location and reading type using only
  the device address field, with no ambiguity between sensors.
- **SC-004**: When a stop signal is sent, the service exits within 10 seconds and leaves no
  orphaned connections on the broker.
- **SC-005**: An operator can determine the cause of any connection or storage failure by
  reading log files alone, without access to the running process.
- **SC-006**: The service is deployable to a fresh host by modifying only the configuration
  file, with no changes to any other file in the package.
- **SC-007**: Log files never consume more than a fixed, bounded amount of disk space regardless
  of how long the service has been running.

## Assumptions

- Sensor devices (publishers) are out of scope; they are independently operated and publish to
  the broker without coordination from the logging service.
- The MQTT broker is provided and managed separately; the logging service connects to it as a
  client and does not configure or administer the broker.
- All sensor payloads are either numeric values (floats) or boolean strings (`true`/`false`);
  no other payload formats are expected.
- Readings are captured at the moment of receipt, not the moment of sensor measurement;
  clock drift between sensors and the logging host is not compensated for.
- Data access for analysis (querying, visualization) is out of scope; a separate tool handles
  this concern.
- The service is single-instance; concurrent or distributed deployment is not required.
- Record retention is indefinite; no automated expiry or archival policy is in scope.
- Network connectivity between broker, logger, and database is reliable within the local network;
  wide-area network reliability is not a design requirement.
- The service operates within a private home network; no public-facing security hardening beyond
  non-root execution is required for v1.
