# Feature Plan

**System:** mqttlogger
**Feature:** 007-python312-upgrade — Python 3.10 → 3.12 runtime upgrade
**Date:** 2026-05-16
**Status:** DRAFT
**Last Updated By:** se-plan skill

---

## 1. Technical Approach

### System Decomposition

This feature has no new runtime behaviour. All changes are build and CI artefacts. Three components change; the running system is unaffected.

---

**Main App Container Image**
- Purpose: provides the Python 3.12 runtime for `mqtt_logger` and installs all application dependencies
- Files changed: `Dockerfile` (FROM line), `requirements.txt` (three pin bumps)
- Primary requirements: FR-023, FR-026
- NFRs: NFR-PORT-001 (deployable on Linux amd64/arm64 via Docker Compose)

**Companion Monitor Container Image**
- Purpose: provides the Python 3.12 runtime for `companion-monitor/monitor.py`
- Files changed: `companion-monitor/Dockerfile` (FROM line only; companion monitor has no pinned requirements file)
- Primary requirements: FR-024
- NFRs: NFR-PORT-001

**CI Pipeline**
- Purpose: validates lint, test, and coverage using the same Python version as the deployed containers
- Files changed: `.github/workflows/ci.yml` (both `python-version` entries)
- Primary requirements: FR-025
- NFRs: NFR-MAIN-001 (≥80% coverage gate must continue to pass)

---

### Key Interactions

There are no runtime interaction changes. The only build-time dependency ordering is:

`requirements.txt` (FR-026) → `Dockerfile` build (FR-023) → CI test run (FR-025)

`requirements.txt` must be updated before the main app image can be built and tested against Python 3.12. The companion monitor Dockerfile (FR-024) and CI yaml (FR-025) are independent of each other and of FR-026, but all ship in the same branch and PR.

---

### NFR-Driven Design Decisions

| NFR ID | Attribute | Mechanism |
| ------ | --------- | --------- |
| NFR-PORT-001 | Portability — Docker Compose on Linux amd64/arm64 | Use `python:3.12-slim` as base image; this is the official multi-arch Docker Hub image and is supported on both amd64 and arm64. The existing apt package install block (libmariadb-dev, python3-dev, build-essential) is unchanged — these packages are available on the Debian slim base regardless of Python version. |
| NFR-MAIN-001 | Test coverage ≥ 80% line coverage | Update `python-version` in `setup-python@v5` to `"3.12"`. The existing test suite, coverage configuration, and 80% gate in `pyproject.toml` are unchanged. |

---

### Technology Constraints

| Constraint | Technology / Version | Source |
| ---------- | -------------------- | ------ |
| Container base image | `python:3.12-slim` (Docker Hub official) | Feature decision (RISK-003 mitigation) |
| Python runtime | 3.12.x (latest 3.12 patch at build time) | Feature decision |
| ORM | SQLAlchemy 1.4.x (minimum 1.4.50) | Existing system constraint — 2.x API migration is out of scope |
| DB connector | mysqlclient ≥ 2.2.0 | Minimum version with Python 3.12 wheel support |
| Greenlet | ≥ 3.0.0 | Minimum version with Python 3.12 support |
| MQTT client | paho-mqtt 1.6.1 — unchanged | Compatible with 3.12; no upgrade needed |
| CI platform | GitHub Actions, `setup-python@v5` | Existing; already supports Python 3.12 |
| Deployment | Docker Compose, Linux amd64 (sietchtabr) | Constitution Principle III |

---

## 2. Open Technical Questions

| ID | Question | Affects | Options | Resolution Method |
| -- | -------- | ------- | ------- | ----------------- |
| OTQ-001 | The `greenlet==1.1.3` entry in `requirements.txt` uses complex auto-generated platform markers. Do these markers need to change for `greenlet>=3.0.0`? | FR-026 | (a) Remove the markers entirely — greenlet 3.0.0 has wheels for all supported platforms; (b) keep existing markers | Run CI; if install fails due to marker mismatch, simplify to `greenlet>=3.0.0` with no platform marker |
| OTQ-002 | Does upgrading SQLAlchemy 1.4.41 → 1.4.50 introduce any behaviour change that breaks the existing test suite? | FR-025, FR-026 | Not expected — patch series is conservative; changelog confirms no API changes | CI pass/fail is the definitive check; no spike required |

---

## 3. Implementation Sequence

### Phase Breakdown

**Phase 1 — Dependency Pin Updates**
Update `requirements.txt` to satisfy Python 3.12 compatibility (FR-026).
- Bump `greenlet==1.1.3` → `greenlet>=3.0.0` (resolve OTQ-001 platform marker question)
- Bump `sqlalchemy==1.4.41` → `sqlalchemy>=1.4.50,<2.0`
- Bump `mysqlclient==2.1.1` → `mysqlclient>=2.2.0`
- Keep `paho-mqtt==1.6.1` — no change required

Requirements addressed: FR-026

**Phase 2 — Container Image Updates**
Update both Dockerfiles to use the Python 3.12 base image.
- `Dockerfile`: `FROM python:3.10-slim` → `FROM python:3.12-slim`
- `companion-monitor/Dockerfile`: `FROM python:3.11-slim` → `FROM python:3.12-slim`
- No other changes to either Dockerfile

Requirements addressed: FR-023, FR-024

**Phase 3 — CI Pipeline Update**
Update `.github/workflows/ci.yml`.
- Both `python-version` entries: `"3.10"` → `"3.12"`
- No other changes to the CI workflow

Requirements addressed: FR-025

**Phase 4 — Governance and Documentation**
Close the governance obligations created when RISK-003 was identified.
- `.specify/memory/constitution.md`: update "Python 3.10+" → "Python 3.12+" in Deployment Constraints and Development Standards; close TBD-005
- `CLAUDE.md`: move RISK-003 to closed/resolved; confirm deployed Python version is 3.12

No formal FR — governance obligation from constitution.

---

### Minimum Viable Implementation

All four formal requirements are Must Have. The minimum viable implementation is:

FR-023 + FR-024 + FR-025 + FR-026 — all changes in one PR; CI must be green before merge.

---

### External Dependencies and Schedule Constraints

| Dependency | Type | Affects | Notes |
| ---------- | ---- | ------- | ----- |
| `python:3.12-slim` on Docker Hub | Third-party (Docker Hub) | FR-023, FR-024 | Available; multi-arch amd64/arm64 confirmed |
| `greenlet>=3.0.0` on PyPI | Third-party (PyPI) | FR-026 | Released October 2023; available |
| `SQLAlchemy>=1.4.50` on PyPI | Third-party (PyPI) | FR-026 | Released 2023; available |
| `mysqlclient>=2.2.0` on PyPI | Third-party (PyPI) | FR-026 | Released 2023; available |
| `setup-python@v5` Python 3.12 support | GitHub Actions | FR-025 | Confirmed supported |
| sietchtabr deployment test | Manual (operator) | All | Post-merge: `docker compose build && docker compose up -d`; verify service starts and captures a reading — per branching convention, merge requires deployment verification |

---

## 4. Requirements Coverage Check

| Req ID | Addressed By | Phase | Notes |
| ------ | ------------ | ----- | ----- |
| FR-023 | `Dockerfile` FROM line change | Phase 2 | Single-line change |
| FR-024 | `companion-monitor/Dockerfile` FROM line change | Phase 2 | Single-line change |
| FR-025 | `.github/workflows/ci.yml` python-version change | Phase 3 | Two entries, same value |
| FR-026 | `requirements.txt` pin bumps | Phase 1 | Three package pins; OTQ-001 may affect greenlet marker syntax |

Uncovered requirements: None — all four requirements are addressed.

---

## 5. Risks Introduced by This Plan

| Risk ID | Description | Mitigation in Plan |
| ------- | ----------- | ------------------ |
| OTQ-001 (RISK-025) | greenlet platform markers may need simplification for 3.0.0 | Addressed in Phase 1; CI failure is the detection mechanism; fallback is removing the marker entirely |
| — | SQLAlchemy 1.4.41 → 1.4.50 behaviour delta | OTQ-002; CI pass is the definitive check; no design impact expected |
