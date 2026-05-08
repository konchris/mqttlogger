<!--
SYNC IMPACT REPORT
==================
Version change: (unversioned template) → 1.0.0
Bump type: MINOR — initial ratification; all principles and sections newly defined.

Modified principles: N/A (first ratification)
Added sections: Core Principles (I–VII), Deployment Constraints, Development Workflow, Governance
Removed sections: N/A

Templates reviewed:
  ✅ .specify/templates/plan-template.md — Constitution Check section is generic; no principle-specific
     gates needed beyond what the template already handles.
  ✅ .specify/templates/spec-template.md — Functional/non-functional structure aligns with principles.
  ✅ .specify/templates/tasks-template.md — Phase structure aligns with integration-preferred testing
     and incremental delivery principles.
  ✅ .specify/templates/checklist-template.md — Generic; no changes required.

Deferred TODOs: None.
-->

# mqttlogger Constitution

## Core Principles

### I. Single-Purpose Service

mqttlogger MUST do exactly one thing: subscribe to MQTT topics and persist received readings to
persistent storage. Business logic, data transformation beyond type coercion, analytics, alerting,
and visualization MUST NOT be added to this service. Any such capability belongs in a separate tool
(e.g., a Jupyter notebook, a dedicated analytics service, or an external dashboard).

**Rationale**: Scope creep turns a simple, reliable daemon into a fragile monolith. The service's
value is its reliability and simplicity; both erode when responsibilities accumulate.

### II. Configuration Over Code

All environment-specific values — database credentials, broker address, ports, topic subscriptions —
MUST be supplied via `config.json` or environment variables. Hardcoded connection strings, IP
addresses, or credentials in source code are prohibited. The application MUST start and connect
solely from its configuration inputs without code changes between environments.

**Rationale**: Enables deploy-time reconfiguration across development, staging, and production
without touching source code and avoids accidental credential leakage into version control.

### III. Container-First Deployment

The application MUST be deployable as a Docker container. All runtime components (MQTT broker,
logger service, database) MUST be orchestrable via Docker Compose. The local development topology
MUST mirror the production topology. The Dockerfile MUST use a non-root user and minimize image
size by not retaining build-time dependencies at runtime.

**Rationale**: Reproducible, environment-agnostic deployment reduces "works on my machine"
failures and ensures the tested artifact is the deployed artifact.

### IV. Observability by Default

The service MUST emit structured, timestamped log entries for every significant lifecycle event
(connect, subscribe, message received, DB commit, disconnect, error). Log output MUST use rotating
file handlers with bounded size to prevent disk exhaustion. A `--debug` flag MUST enable verbose
output without requiring code changes or restarts. Logs MUST include module name, function, and
line number for rapid diagnosis.

**Rationale**: A long-running daemon with no external UI is only debuggable through its logs.
Rich, bounded logs are the primary operational instrument.

### V. Graceful Lifecycle Management

The service MUST handle OS signals cleanly. On receipt of SIGTERM or SIGINT, the service MUST
stop the MQTT loop, disconnect from the broker, and exit with code 0 before the process is
killed. In-flight message writes MUST be completed or safely abandoned before exit. Silent,
unclean exits that leave the broker connection dangling or lose committed data are not acceptable.

**Rationale**: Docker Compose and process supervisors issue SIGTERM on stop/restart. Unclean
exits cause broker-side connection backlogs and potential data loss at the DB boundary.

### VI. Integration-Preferred Testing

Tests MUST exercise real protocol behavior wherever feasible. Mocking the paho-mqtt library
internals or the SQLAlchemy database driver is explicitly discouraged. Integration tests MUST use
a real MQTT broker (e.g., test.mosquitto.org for public CI, or a local Mosquitto container for
offline runs) and a real database instance. Unit tests are appropriate only for pure functions
with no I/O dependencies.

**Rationale**: The MQTT client library had a history of behavior changes across minor versions;
mock-based tests missed these regressions. The prior incident (stub tests with `assert False`)
demonstrates the cost of untested I/O paths.

### VII. Minimal Surface Area

The service MUST NOT accumulate helper scripts, management commands, or operational tooling
beyond what is required to run and log. Exploratory data analysis MUST live in `notebooks/`.
Schema migrations, if needed, MUST be handled via an explicit migration tool, not ad-hoc scripts
committed to the project root. The `persist.sh` script and any other one-off operational scripts
MUST be documented or removed; undocumented scripts at the repo root are prohibited.

**Rationale**: Undocumented scripts rot silently and create maintenance confusion. Keeping the
repo root clean signals intent and reduces cognitive overhead for contributors.

## Deployment Constraints

- The application targets Python 3.10+ running on Linux (amd64/arm64).
- The MQTT broker MUST be Eclipse Mosquitto. No other broker is officially supported.
- The database MUST be MariaDB (MySQL-compatible). SQLAlchemy is the only sanctioned ORM.
- `config.json` MUST NOT be committed with production credentials. Use `.env` and Docker
  Compose environment variable injection for secrets.
- The `mariadb` service MUST define a `healthcheck` in `docker-compose.yml` so that
  `mqtt_logger` does not attempt connections before the database is ready.

## Development Workflow

1. All changes MUST be made on a feature branch; direct commits to `main` or `develop` are
   prohibited except for hotfixes with explicit justification.
2. Integration tests MUST pass before any PR is merged to `develop`.
3. A PR MUST include a description of what was changed and why; template prose ("see commits")
   is not acceptable.
4. The `Dockerfile` and `docker-compose.yml` MUST be updated in the same PR as any change to
   dependencies or runtime configuration that affects the container image.
5. Any new dependency added to `requirements.txt` MUST have a pinned version.

## Governance

This constitution supersedes all prior informal practices for the mqttlogger project. Amendments
require:

1. A written rationale explaining why the current principle is insufficient.
2. An update to this document with a version bump following the semantic versioning policy below.
3. Propagation of any impacted changes to templates under `.specify/templates/`.
4. A commit message of the form: `docs: amend constitution to vX.Y.Z (<summary>)`.

**Versioning policy**:
- MAJOR: A principle is removed, fundamentally redefined, or made incompatible with prior rules.
- MINOR: A new principle or section is added, or existing guidance is materially expanded.
- PATCH: Clarifications, rewording, typo fixes, or non-semantic refinements.

All PRs and code reviews MUST verify compliance with the active principles. Complexity that
violates a principle MUST be explicitly justified in the Complexity Tracking section of the
relevant `plan.md`.

**Version**: 1.0.0 | **Ratified**: 2026-05-04 | **Last Amended**: 2026-05-04

---

# SE Project Constitution (INCOSE SE Pack)

## System Identity

**System Name:** mqttlogger
**Version:** 0.1
**Last Updated:** 2026-05-08
**Status:** DRAFT

### Problem Statement

Home-network smart-home sensor devices publish environmental readings (temperature, humidity, etc.) to an MQTT broker. There is no persistent record of those readings unless something captures and stores them. mqttlogger solves that by running as a continuous, unattended daemon that captures every received reading and writes it to a MariaDB database for long-term retention. The primary motivation is energy optimisation: tracking how seasonal conditions, renovations, and temporary measures affect comfort and energy usage across rooms (bedrooms, attic, etc.), with the goal of minimising energy consumption over time. Analyses are not yet defined — data is being collected now so that future analyses are possible. All raw readings are retained indefinitely; no expiry policy is defined.

### System of Interest

mqttlogger is the data-capture daemon and its supporting container stack (broker + database). It is NOT: sensor firmware, MQTT broker administration, data analysis tooling, dashboards, alerting systems, or any actuator control logic. The system boundary begins at the MQTT broker client connection and ends at a committed database row. The transport mechanism (currently MQTT) is an implementation constraint, not a fixed architectural commitment; future ingestion paths are explicitly in scope for later versions.

### Primary Users and Operational Environment

**Developer/Operator/End-User:** A single person who deploys, maintains, and benefits from the system. No other users currently exist; no one else has the technical capability to interact with the system.

**Operational Environment:** Private home network; Linux host (amd64 or arm64); containerised via Docker Compose; no public internet exposure; continuous unattended 24/7 operation. Current actuators on the monitored system: heat registers only. The service does not control any actuators.

---

## Domain and Regulatory Context

**Industry Domain:** Consumer IoT / Home Automation
**Safety Classification:** Non-safety
**Configuration Control Required:** No — git history + PR review is the full change record.

### Applicable Standards and Frameworks

- No regulatory obligations identified at this time.
- INCOSE SE Pack workflow applied voluntarily to improve artifact quality and traceability.
- IEEE 29148 requirements quality attributes applied voluntarily to all functional requirements.

### Regulatory Obligations

No regulatory obligations identified at this time.

---

## Quality Principles

### Priority Quality Attributes

1. **Reliability** — The service operates unattended 24/7; a missed reading is permanently lost with no recovery mechanism.
2. **Maintainability** — Solo developer, long lifecycle; the system must remain comprehensible and modifiable months or years after initial development.
3. **Data Integrity** — Retained indefinitely with no recovery mechanism; a corrupt or missing record cannot be reconstructed.

### Known Constraints

- **Python 3.10+ / Linux (amd64, arm64)** — Current runtime target; affects all phases. Python 3.11+ is a candidate upgrade but not yet actioned (TBD-005).
- **Eclipse Mosquitto** — Only supported MQTT broker; affects architecture and integration test configuration.
- **MariaDB + SQLAlchemy** — Only supported database stack; affects data model and all phases.
- **Docker / Docker Compose** — Mandated deployment mechanism; affects all phases.
- **Single-instance deployment** — Concurrent or distributed deployment is not in scope; affects architecture phase.
- **config.json for connection parameters** — Current configuration mechanism; may be superseded by `.env` / environment variable injection in a future version (TBD-006).
- **Single developer** — All work is self-reviewed; affects quality assurance strategy and review obligations.

### Engineering and Design Principles

The following principles are defined in the Spec Kit constitution above and are binding on all SE work:

1. **Single-Purpose Service** — Subscribe and persist only; no analytics, alerting, or control logic.
2. **Configuration Over Code** — All environment-specific values via `config.json` or environment variables; no hardcoding.
3. **Container-First Deployment** — Docker Compose; non-root user; production topology mirrored in development.
4. **Observability by Default** — Structured, timestamped, rotating log files; `--debug` flag; module/function/line in every log entry.
5. **Graceful Lifecycle Management** — SIGTERM/SIGINT handled cleanly; in-flight writes completed before exit.
6. **Integration-Preferred Testing** — Real broker and real database in tests; mock-only tests discouraged.
7. **Minimal Surface Area** — No accumulation of helper scripts or undocumented artefacts.
8. **Data Immutability** — Stored readings are never modified or deleted after capture; the store is append-only.

Additionally, the following SE-standard obligations apply:

- Requirements shall be verifiable before being baselined.
- Every design decision shall have documented rationale (ADR).
- No requirement shall be implemented without a corresponding V&V plan entry.
- Architecture shall be documented in multiple views (C4 model).
- All SE artefacts shall be version-controlled as code.

### Development Standards

**Language and Compiler:**
Python 3.10+ (Linux, amd64/arm64). No compiler qualification required (non-safety-critical). Python 3.11+ is a candidate upgrade; not yet actioned (TBD-005).

**Coding Style and Linting:**
Target: `ruff` (replaces flake8, isort, partial black). Configuration file location: TBD — to be added to `pyproject.toml` or `ruff.toml` (TBD-001). Current practice: informal PEP 8 enforced by developer discipline in PyCharm Pro.

**Test Coverage Threshold:**
80% line coverage minimum (target; not yet enforced — TBD-002). Current gate: "tests must pass." Framework: `pytest` with `pytest-cov`. Enforcement to be added when CI/CD pipeline is established. Integration tests require a real MQTT broker and MariaDB instance per the Integration-Preferred Testing principle.

**CI/CD Pipeline:**
No pipeline currently exists (TBD-003). Target platform: GitHub Actions (free tier) on a new GitHub repository. Migration from Bitbucket planned; repository history may be dropped due to credential hygiene (TBD-004). Planned mandatory stages: lint (ruff) → unit test → integration test → coverage check (80% gate) on every push and pull request.

**Branching Strategy:**
Feature branches + PR to `develop`; no direct commits to `main` or `develop` except hotfixes with explicit justification. `develop` merges to `main` for releases. Self-review is current practice (solo project); no required external reviewers. No automated branch protection rules currently configured.

**Mandated or Prohibited Tools:**
No SAST tools currently configured (noted as future improvement). No dependency scanner currently configured (noted as future improvement). No GPL licence restriction — GPL dependencies are permitted.

**Documentation Standards:**
Aspirational (not yet enforced):
- Google-style docstrings required on all public functions and classes.
- `CHANGELOG.md` to be maintained per release.
- No architecture diagram review obligation at this time.

---

## Stakeholder Context

**Key Stakeholders:**

| Stakeholder | Role | Interest |
|-------------|------|----------|
| Developer/Operator | System builder and sole maintainer | Correct, reliable data capture; low maintenance burden |
| Home resident (same person) | End beneficiary | Long-term energy optimisation data availability |

**System Lifecycle:** Long-term maintained product — data is retained indefinitely; the system is expected to run continuously for years.

### External System Interfaces (Known)

| Interface | Direction | Description |
|-----------|-----------|-------------|
| Eclipse Mosquitto MQTT broker | Inbound | Message source; mqttlogger subscribes as a client |
| MariaDB database | Outbound | Persistence target; all readings written here |
| Smart-home sensor devices | Upstream (out of scope) | Publishers to the broker; independently operated |
| Jupyter notebooks (`notebooks/`) | Downstream (out of scope) | Reads from MariaDB for ad-hoc analysis |

---

## SE Workflow Obligations

This project follows the INCOSE SE Pack workflow. The following obligations apply to every skill invocation:

### Threaded Artifact Update Obligations

| Artifact | Initiated | Every skill must |
|----------|-----------|-----------------|
| `risk-register.md` | Phase 0 | Add entries for any new assumptions, unknowns, or external dependencies introduced |
| `vv-plan.md` | Phase 1 | Add an entry for every new NFR or requirement |
| `rtm.md` | Phase 2 | Update allocations when design, tasks, or implementation changes |

### Phase Gate Obligations

No phase is complete until `/se-gate {N}` passes. Gates check threaded artifact currency, not just sequenced artifact existence.

### Requirements Quality Obligations

Every requirement must satisfy all eight IEEE 29148 quality attributes before Phase 2 closes:
Necessary · Unambiguous · Verifiable · Consistent · Complete · Singular · Feasible · Traceable

A requirement without a verification method is **incomplete by definition**. The V&V plan entry must exist before the requirement is baselined.

### Architecture Documentation Obligations

All architecture views shall be produced as Mermaid diagrams embedded in Markdown files. Minimum required views:
- C4 Level 1: System Context
- C4 Level 2: Container
- Functional Flow
- Deployment/Allocation

Architecture Decision Records (ADRs) shall be written for every significant design decision using the format:
Context → Decision → Consequences → Alternatives Considered

### Set-Based Design Obligation

Until Phase 3 gate passes, no solution option shall be eliminated without documented evidence. Opinion is not evidence. All eliminated options shall have an entry in `elimination-record.md` stating what evidence caused elimination.

---

## Open Issues and TBDs

| ID | Item | Owner | Target Phase |
|----|------|-------|-------------|
| TBD-001 | Ruff linting configuration not yet added to repo | Chris | Phase 1 |
| TBD-002 | 80% coverage enforcement not yet active (pending CI/CD) | Chris | Phase 1 |
| TBD-003 | GitHub Actions CI/CD pipeline not yet created | Chris | Phase 1 |
| TBD-004 | Bitbucket → GitHub migration pending; credential hygiene check required | Chris | Phase 0 |
| TBD-005 | Python 3.11+ upgrade candidate not yet actioned | Chris | Phase 2 |
| TBD-006 | config.json → .env / environment variable migration planned but not scoped | Chris | Phase 2 |
| TBD-007 | CHANGELOG.md and Google-style docstring standards aspirational only | Chris | Phase 1 |
| TBD-008 | Future ingestion paths beyond MQTT not yet designed | Chris | Phase 3+ |
| TBD-009 | Analyses / use cases for retained data not yet defined | Chris | Phase 3+ |
| TBD-010 | Indefinite retention strategy — no archival or size-management policy defined | Chris | Phase 3+ |
