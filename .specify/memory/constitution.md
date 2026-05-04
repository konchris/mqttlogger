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
