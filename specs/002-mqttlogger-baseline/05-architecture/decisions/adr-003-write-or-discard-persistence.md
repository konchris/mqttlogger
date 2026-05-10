# ADR-003: Write-or-Discard Persistence — No Message Buffer

**Date:** 2026-05-10
**Status:** Accepted
**Deciders:** Chris
**Feature:** 002-mqttlogger-baseline

---

## Context

When a database write fails (MODE-005), the system must decide what to do with the unwritten message. Two options exist: discard it (accept the data loss) or buffer it (retry later).

The ConOps explicitly documents that "readings published during DB outage are permanently lost; this is accepted behaviour." The system has no secondary storage: no local file, no message queue, no in-memory ring buffer.

The operational context makes buffering less valuable than it appears:
- The database is co-hosted on the same host as the logger. A DB outage severe enough to cause write failures likely affects the host itself.
- MQTT messages that the logger fails to write are published by the sensor only once. They are not retransmitted by the broker (no MQTT persistence enabled). So a message that arrives during a DB outage is lost regardless of whether the logger tries to buffer it — the broker cannot re-deliver it after the outage clears.
- The primary data loss vector is not DB write failure but broker-side gaps (MODE-004: broker unavailable, readings never reach the logger at all). Buffering DB write failures does not address this larger risk.

## Decision

When a database write fails, the message payload is logged at ERROR level with the exception and discarded. The `on_message` callback returns; the paho-mqtt loop continues processing subsequent messages. No retry, no buffer, no queue.

## Consequences

### Positive
- Code is simple: no buffer to manage, no retry logic, no backpressure handling
- The logger never blocks indefinitely on a DB outage — subsequent messages continue to be received from the broker (they will also fail to write, but the MQTT connection stays healthy)
- Disk and memory usage are bounded: no accumulation of undelivered messages

### Negative
- Any message that arrives during a DB write failure is permanently lost
- There is no retry window: even a transient 1-second DB hiccup during a write causes that message to be discarded
- An operator cannot recover lost messages post-hoc; there is no dead-letter queue

### Neutral
- The OPT-B companion monitor detects extended DB outages indirectly: if the DB is down long enough that no sensor readings arrive within the gap window, companion_monitor fires a silence alert. This is a weak form of indirect notification, not a recovery mechanism.

## Alternatives Considered

### Alternative 1: In-memory ring buffer with retry

**Description:** Failed messages are placed in an in-memory ring buffer. A retry thread attempts to re-write them when the DB recovers. If the buffer fills, oldest entries are dropped.

**Rejected because:** The DB is co-hosted — a DB outage that persists long enough for buffering to matter likely also affects the host. A ring buffer that survives a host restart would need to be persisted to disk, adding significant complexity. The MQTT broker does not re-deliver messages to a reconnected subscriber, so the buffer can only help for the narrow window of a transient DB failure while the MQTT connection remains alive. This narrow benefit does not justify the added complexity (Constitution Principle VII).

### Alternative 2: Local SQLite fallback

**Description:** If the MariaDB write fails, write the record to a local SQLite file instead. A reconciliation job later merges SQLite records into MariaDB.

**Rejected because:** Introduces a second database, a reconciliation process, and the risk of duplicate records if both the MariaDB write partially succeeds and the SQLite write also succeeds. The system has no schema migration path for SQLite. Complexity far exceeds the operational benefit for a co-hosted deployment.

### Alternative 3: Persistent MQTT (QoS 1/2 + broker persistence)

**Description:** Enable MQTT QoS 1 or 2 between CCU3/RedMatic and the broker. Enable broker persistence so messages are stored until the logger acknowledges them.

**Rejected because:** RedMatic's MQTT publish settings are out of scope (hard constraint from explore-summary — no changes to HomeMatic/CCU3/RedMatic). Even if enabled, broker persistence only helps when the broker is running and the logger has reconnected; it does not help during a host-level outage.

## Related

- Supersedes: None
- Related requirements: FR-003, FR-005
- Related NFRs: NFR-PERF-001, NFR-REL-001
- Related explore option: None
