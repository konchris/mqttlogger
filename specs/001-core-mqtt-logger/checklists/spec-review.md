# Requirements Review Checklist: Core MQTT Sensor Logging Service

**Purpose**: Full-spectrum requirements quality audit — validates completeness, clarity,
consistency, measurability, and coverage of spec.md against contracts/ and data-model.md.
Intended for PR reviewer gate before implementation begins.
**Created**: 2026-05-04
**Feature**: [spec.md](../spec.md)
**Depth**: Standard (~25 items) | **Audience**: PR reviewer | **Scope**: Spec ↔ contracts ↔ data-model cross-check

---

## Requirement Completeness

- [ ] CHK001 - Are log severity levels (ERROR, WARNING, INFO, DEBUG) specified for each
  event category listed in FR-005 (connect, subscribe, receive, write, disconnect, error)?
  [Completeness, Spec §FR-005]

- [ ] CHK002 - Does FR-006 specify where log rotation parameters (file size limit, file
  count) are configured — in source code, configuration file, or environment variable?
  [Completeness, Spec §FR-006]

- [ ] CHK003 - Does FR-007 define a maximum wait time for in-flight write completion during
  shutdown — i.e., how long does the service wait before abandoning a pending DB write on
  receiving a stop signal? [Gap, Spec §FR-007]

- [ ] CHK004 - Does the spec define the timezone convention for `currentdate` and
  `currenttime` (UTC, local system time, or host timezone)? [Gap, Spec §FR-002]

- [ ] CHK005 - Are requirements defined for the startup scenario where the broker is
  reachable but the database is not yet available and the healthcheck dependency gate
  (FR-012) has not triggered? [Gap, Spec §FR-012]

---

## Requirement Clarity

- [ ] CHK006 - Is "numeric equivalent" in FR-003 defined as integer (1/0) or
  floating-point (1.0/0.0)? FR-003 uses "1 for true, 0 for false" while
  contracts/mqtt-topic-schema.md and data-model.md use floats — is this consistent?
  [Clarity, Spec §FR-003, contracts/mqtt-topic-schema.md]

- [ ] CHK007 - Is the measurement point for SC-001's "5 seconds" specified — is latency
  measured from broker publication time or from client receipt time? These diverge when
  network or broker queuing delay is non-trivial. [Clarity, Spec §SC-001]

- [ ] CHK008 - Is "configured size limit" in FR-006 defined with the configuration
  mechanism (e.g., which file or constant controls this value)? Without this, the
  requirement cannot be independently verified. [Clarity, Spec §FR-006]

- [ ] CHK009 - Is "any error condition" in FR-005 bounded — does it mean all Python
  exceptions, only I/O exceptions, or a specific enumerated set of error classes?
  [Clarity, Spec §FR-005]

---

## Requirement Consistency

- [ ] CHK010 - Are FR-003 ("1 for true, 0 for false") and contracts/mqtt-topic-schema.md
  ("1.0 / 0.0") consistent in specifying integer vs. float representation for boolean
  payloads? The data-model.md `reading` column is typed as Float — which is authoritative?
  [Consistency, Spec §FR-003, contracts/mqtt-topic-schema.md, data-model.md]

- [ ] CHK011 - Does the "data loss during database outages is accepted" policy in the Edge
  Cases section conflict with US3's acceptance scenario that "no in-flight message records
  are missing" after a clean shutdown? Which takes precedence when a DB write fails during
  the shutdown window? [Consistency, Spec §US3, §Edge Cases]

- [ ] CHK012 - Are "device identifier" (FR-004) and "device address" (FR-013, FR-014,
  data-model.md) formally established as synonyms — or do they refer to different concepts?
  Data-model.md declares "device address" canonical but the spec uses both interchangeably.
  [Consistency, Spec §FR-004, §FR-013, data-model.md]

- [ ] CHK013 - Does the Assumptions section's claim that "all sensor payloads are numeric
  or boolean" contradict the existence of FR-013 (malformed payload handling)? If the
  assumption holds, FR-013 is unreachable; if FR-013 is needed, the assumption should be
  softened. [Consistency, Spec §Assumptions, §FR-013]

---

## Acceptance Criteria Quality

- [ ] CHK014 - Is SC-002 ("30 or more days without manual intervention") testable before
  deployment — or is it an operational SLO measurable only post-production? If
  pre-deployment verification is expected, is the test method specified?
  [Measurability, Spec §SC-002]

- [ ] CHK015 - Is SC-004 ("no orphaned connections on the broker") measurable with
  available tooling — is the observation mechanism (broker admin interface, log parsing,
  other) specified in the spec? [Measurability, Spec §SC-004]

- [ ] CHK016 - Is SC-007 ("bounded amount of disk space") quantified with an absolute
  maximum value — or does it defer to FR-006's "configured" parameter that is itself
  unspecified? A success criterion that references an undefined constant cannot be
  objectively verified. [Measurability, Spec §SC-007, §FR-006]

---

## Scenario Coverage

- [ ] CHK017 - Are requirements defined for SIGINT (interactive Ctrl+C) shutdown — or does
  the spec treat SIGINT and SIGTERM as equivalent? FR-007 names only "a process stop
  signal" without distinguishing signal types. [Coverage, Gap, Spec §FR-007]

- [ ] CHK018 - Are requirements defined for the scenario where the `logs/` directory cannot
  be created at startup (e.g., due to filesystem permissions) — and whether this is treated
  as a fatal error or a degraded mode? [Coverage, Gap]

- [ ] CHK019 - Is the callback threading model specified — is `on_message` guaranteed to be
  invoked sequentially, or can concurrent invocations result in simultaneous `insert()`
  calls, and if so, are thread-safety requirements defined? [Coverage, Gap]

---

## Edge Case Coverage

- [ ] CHK020 - Is the retained message flood edge case (noted as deferred in research.md)
  explicitly documented in the spec as an accepted risk with a rationale, rather than an
  unresolved gap? [Edge Case, Spec §Edge Cases]

- [ ] CHK021 - Are requirements defined for network timeout during a database write — as
  distinct from the database being entirely unreachable — given that a partial-write
  scenario may leave the session in an ambiguous state? [Edge Case, Gap, Spec §FR-014]

---

## Non-Functional Requirements

- [ ] CHK022 - Are memory consumption requirements specified (e.g., maximum resident memory
  under sustained load) to guard against unbounded growth from per-message engine creation
  or log buffer accumulation? [Non-Functional, Gap]

- [ ] CHK023 - Is a startup readiness time requirement defined — i.e., the maximum elapsed
  time from process start to first successful message receipt — to support automated
  container health probing? [Non-Functional, Gap]

---

## Contract / Data-Model Cross-Check

- [ ] CHK024 - Does the `sensorreadings` DB schema (contracts/db-schema.md) align with
  FR-002's requirement that all four fields MUST be persisted, given that `currentdate`,
  `currenttime`, `device`, and `reading` are marked nullable in the DDL? Is the absence
  of NOT NULL constraints on these columns an intentional design decision or a gap?
  [Consistency, Spec §FR-002, contracts/db-schema.md]

- [ ] CHK025 - Does the 4-segment Device Address structure defined in data-model.md apply
  to all messages received via the `environment/#` subscription — or does FR-001
  intentionally capture non-conforming topic structures (e.g., 2-segment or 5-segment
  paths) and store them as-is? [Clarity, Spec §FR-001, data-model.md]

- [ ] CHK026 - Are sensors with location values outside the enumerated set in
  contracts/mqtt-topic-schema.md (e.g., a new `garage` room added in future) captured and
  stored correctly under FR-001 — and is this future-extensibility behavior explicitly
  stated rather than implied? [Coverage, Spec §FR-001, contracts/mqtt-topic-schema.md]

---

## Notes

- Items marked [Gap] identify requirements that appear to be missing from the spec entirely.
- Items marked [Consistency] identify potential conflicts between two spec sections or
  between the spec and a contract/data-model artifact.
- Items marked [Ambiguity] or [Clarity] identify requirements that exist but are not
  specific enough to be independently verified.
- Resolve all [Gap] items before proceeding to `/speckit-implement`; [Clarity] and
  [Consistency] items may be resolved inline in the relevant spec section.
