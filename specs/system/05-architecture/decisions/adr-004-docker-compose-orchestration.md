# ADR-004: Docker Compose as Sole Orchestration Mechanism

**Date:** 2026-05-10
**Status:** Accepted
**Deciders:** Chris
**Feature:** 002-mqttlogger-baseline

---

## Context

The system must be deployed on a single consumer-grade Linux mini PC on a private home network, operated by a solo developer who may not interact with the system for months at a time. NFR-PORT-001 mandates Docker Compose on Linux (amd64/arm64). The system consists of six containers that must start in a defined order (mariadb healthcheck before mqtt_logger), restart automatically after failures, and be operable by a returning developer without re-learning the deployment model.

Constitution Principle III (Container-First Deployment) mandates that all runtime components be orchestrable via Docker Compose and that the local development topology mirror the production topology.

## Decision

Docker Compose (`docker-compose.yml`) is the sole orchestration mechanism. All six containers are defined in a single Compose file. Container restart is handled by the `restart: unless-stopped` policy on every service. Start ordering is handled by `depends_on: condition: service_healthy` for mqtt_logger and companion_monitor (both wait for MariaDB healthcheck). No external orchestrator (Kubernetes, Nomad, Swarm) is involved.

## Consequences

### Positive
- A single `docker compose up -d` starts the full stack; a single `docker compose down` stops it
- `restart: unless-stopped` provides automatic recovery from container crashes without operator intervention (NFR-REL-001)
- The Compose file is a complete, readable description of the deployment — a returning developer can understand the full topology from one file (SC-CONOPS-007)
- Zero infrastructure cost; runs on existing hardware with no cloud dependency

### Negative
- Single-host deployment: no redundancy at the host level; a host failure stops all services simultaneously
- Docker Compose restart latency contributes to the overall recovery time; must be within NFR-REL-002 (≤60 s) accounting for mariadb healthcheck time
- No rolling updates: changing a container requires a `docker compose up -d --build` which involves a brief restart window

### Neutral
- Log rotation (`logging: driver: json-file, max-size: 10m, max-file: 3`) is configured at the Compose level rather than inside containers, consistent with the Compose-as-orchestrator approach

## Alternatives Considered

### Alternative 1: Kubernetes (k3s/k3d)

**Description:** Run a single-node k3s cluster on the mini PC; define containers as Kubernetes Deployments and Services.

**Rejected because:** Kubernetes adds significant operational overhead (kubeconfig management, kubectl familiarity, resource consumption) for a single-node deployment. The solo maintainer (STK-002) returning after months away would face a steeper re-orientation burden than with Docker Compose. k3s alone consumes ~500 MB RAM on an idle system. Not aligned with Constitution Principle VII (Minimal Surface Area).

### Alternative 2: systemd service units

**Description:** Run each service directly on the host under systemd, without Docker containers.

**Rejected because:** Violates Constitution Principle III (Container-First Deployment). Bare-metal Python installation path is explicitly not supported. Removes the environment isolation guarantees that ensure the tested artifact is the deployed artifact.

### Alternative 3: Docker Swarm

**Description:** Use Docker Swarm for multi-replica or multi-host deployment.

**Rejected because:** Single-host deployment is an explicit constraint; Swarm's value is horizontal scaling and multi-host redundancy, neither of which applies here. Adds complexity without operational benefit.

## Related

- Supersedes: None
- Related requirements: FR-009, FR-010
- Related NFRs: NFR-PORT-001, NFR-REL-001, NFR-REL-002
- Related explore option: None
