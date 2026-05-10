# TASK-B-001: ntfy.sh vs Gotify — Notification Tool Research

**Date:** 2026-05-09
**Task ID:** TASK-B-001
**Output:** Recommendation with rationale

---

## Candidates Evaluated

### ntfy.sh

| Property | Detail |
|----------|--------|
| Project | Open source (Apache 2.0), maintained by Philipp C. Heckel |
| Docker image | `binwiederhier/ntfy` (official, actively maintained) |
| Protocol | Plain HTTP POST to a topic URL — no auth required for simple local use |
| Push API | `POST http://ntfy-host/topic-name` with body = message text; optional headers for title, priority, tags |
| Phone app | Official ntfy app (Android + iOS); subscribes to any topic URL by hostname |
| Local-only operation | Yes — the Android app polls or uses WebSocket to the self-hosted server; no cloud relay required if the phone is on the same WiFi |
| Config complexity | Minimal — zero config required for basic use; optional `server.yml` for auth, attachment limits |
| Resource footprint | ~30 MB RAM; Go binary; tiny Docker image |

### Gotify

| Property | Detail |
|----------|--------|
| Project | Open source (MIT), maintained by Gotify team |
| Docker image | `gotify/server` (official) |
| Protocol | REST API + WebSocket; requires creating an "application" and obtaining a push token |
| Push API | `POST http://gotify-host/message?token=<app_token>` with JSON body |
| Phone app | Gotify Android app; maintains a persistent WebSocket connection to the server |
| Local-only operation | Yes — phone app connects directly to the local server |
| Config complexity | Medium — must create an application in the web UI, copy the token, and pass it to every producer |
| Resource footprint | ~50 MB RAM; similar Go binary |

---

## Comparison

| Criterion | ntfy.sh | Gotify | Winner |
|-----------|---------|--------|--------|
| Initial setup complexity | Low — start container, subscribe to topic URL | Medium — create application, copy token | **ntfy.sh** |
| Push API simplicity | Minimal — `curl -d "message" http://ntfy/topic` | Requires token in every push | **ntfy.sh** |
| Internet independence | Yes | Yes | Tie |
| Phone app quality | Good; official iOS + Android | Good; Android only | **ntfy.sh** |
| Auth support | Optional (config flag) | Built-in | Gotify |
| WebSocket delivery | Yes (app uses it automatically) | Yes | Tie |
| Production maturity | Rapidly growing, widely deployed | Established, stable | Tie |

---

## Recommendation

**ntfy.sh** — for this use case (local-only, solo operator, single producer).

Rationale:
- Zero-config to get first notification working: `docker compose up ntfy`, then `curl -d "test" http://localhost:8080/mqttlogger-alerts`
- No token management for the companion monitor — the NTFY_URL env var is the full push URL, self-describing
- Official iOS and Android apps support self-hosted servers with no account required
- Lower barrier validates ASM-B-001 (local push notification) faster

Gotify would be preferable if multi-user access or fine-grained per-application auth is needed. Neither is a requirement here.

---

## Validation of ASM-B-001

> ASM-B-001: ntfy.sh or Gotify can be deployed locally with no internet dependency and zero cost, and can deliver push notifications to the operator's phone.

ntfy.sh satisfies this assumption:
- Deployed as a Docker service in the existing Compose stack (no internet required)
- Push API is a plain HTTP POST (companion monitor uses `urllib.request` from stdlib)
- Phone app connects to `http://<host-ip>:8080` on the local network — no cloud relay
- Cost: zero (open source)

ASM-B-001 is **validated by analysis** pending live phone delivery confirmation (TASK-B-001 live test).
