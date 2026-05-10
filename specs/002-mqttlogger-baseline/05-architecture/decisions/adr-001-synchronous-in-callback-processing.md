# ADR-001: Synchronous In-Callback Message Processing

**Date:** 2026-05-10
**Status:** Accepted
**Deciders:** Chris
**Feature:** 002-mqttlogger-baseline

---

## Context

mqttlogger must capture every MQTT message received and commit it to MariaDB (NFR-PERF-001: message completeness, no drops due to processing backlog). Two processing models were available: synchronous processing inside the paho-mqtt `on_message` callback, or asynchronous processing via a queue (messages enqueued in the callback, consumed by a separate worker thread).

The system receives approximately 50 sensors publishing on value-change — estimated low tens of messages per minute under normal conditions, with a burst during CCU3/RedMatic restart (all sensors simultaneously). MariaDB is co-hosted on the same mini PC with sub-millisecond local network latency.

The message completeness requirement (NFR-PERF-001) was explicitly defined as completeness over throughput: "a missed reading is permanently lost with no recovery mechanism." The previous 5-second capture-to-storage latency target (SC-001) was retired as analytically unmotivated — no operational requirement drives sub-second storage latency for a trend-analysis system.

## Decision

Process each MQTT message synchronously inside the `on_message` callback: parse the payload, construct a `SensorReading`, open a SQLAlchemy session, INSERT, and COMMIT before returning from the callback. If the commit fails, log and discard — the callback returns without buffering the message.

## Consequences

### Positive
- No queue means no queue overflow; the only way to lose a message is a DB commit failure, which is logged and accepted by design (MODE-005)
- Code is simple: the entire capture path is one linear function — no concurrency, no shared state between message handler and worker
- Easy to reason about: if the callback returns, the message is committed or explicitly discarded

### Negative
- If the DB write blocks (network latency, lock contention, slow disk), the paho-mqtt loop also blocks; MQTT messages that arrive during the block are buffered by paho internally up to its internal queue limit, then dropped
- At pathologically high message rates (not current workload), synchronous writes become a throughput bottleneck
- Restart burst from CCU3 (~50 simultaneous messages) is handled sequentially; in practice this completes in under a second given co-hosted MariaDB

### Neutral
- Timestamp fidelity (NFR-PERF-002) is unaffected: the capture timestamp is set at time-of-receipt, before the DB write, so synchronous write latency does not affect the timestamp value

## Alternatives Considered

### Alternative 1: Async queue with worker thread

**Description:** `on_message` puts received messages onto a `queue.Queue`. A separate daemon thread consumes from the queue and performs DB writes. The MQTT loop is never blocked by DB I/O.

**Rejected because:** Introduces a queue that can overflow or lose messages if the worker is too slow. Also introduces shared-state concurrency that complicates the code significantly (Constitution Principle VII — Minimal Surface Area). At the observed message rate (tens per minute), synchronous processing leaves the MQTT loop idle >99% of the time, so the concurrency benefit is theoretical, not operational. The queue failure mode (silent drop on overflow) is worse for NFR-PERF-001 than the synchronous failure mode (explicit log-and-discard).

### Alternative 2: Async IO (asyncio + aiomqtt)

**Description:** Rewrite the entire application using asyncio with an async MQTT client library, making all I/O non-blocking.

**Rejected because:** Would require replacing paho-mqtt (the supported MQTT library per the constitution) with a third-party async client. Adds significant complexity for a workload that does not require it. Not aligned with Constitution Principle VII or the solo-maintainer constraint (NFR-MAIN-001 — the codebase must be re-learnable after months away).

## Related

- Supersedes: None
- Related requirements: FR-001, FR-002, FR-003, FR-005, NFR-PERF-001
- Related NFRs: NFR-PERF-001, NFR-REL-001
- Related explore option: None (core logger architecture, pre-dates exploration)
