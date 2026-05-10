# ADR-005: ntfy as the Self-Hosted Push Notification Server

**Date:** 2026-05-10
**Status:** Accepted
**Deciders:** Chris
**Feature:** 002-mqttlogger-baseline

---

## Context

Both monitoring options (OPT-A and OPT-B) require a mechanism to deliver push notifications to the operator's iPhone without internet dependency (hard constraint from explore-summary: "no cloud-dependent services"). The notification server must:
- Run self-hosted on the same Docker Compose stack
- Support iOS push notifications via a native app
- Accept HTTP POST payloads from other containers (Uptime Kuma and companion_monitor)
- Require no account registration, API keys, or cloud relay for LAN-only delivery

A dedicated research document was produced before selection: `03-explore/option-b/research-ntfy-vs-gotify.md`.

## Decision

Deploy `binwiederhier/ntfy` as a self-hosted push notification server on port 8080. Both Uptime Kuma (OPT-A alert routing) and companion_monitor (OPT-B direct push) send HTTP POST requests to `http://ntfy:80/mqttlogger-alerts`. The ntfy iOS app subscribes to this topic directly via the home LAN IP.

## Consequences

### Positive
- No account, no API key, no cloud relay required for LAN delivery
- The iOS/Android app connects directly to the self-hosted server — no cloud intermediary for LAN-only operation
- Simple HTTP API: `curl -d "message" http://ntfy:80/topic` — trivially callable from Python and Uptime Kuma
- No per-message or per-device cost; self-hosted means unlimited use
- ntfy server log level set to `warn` (docker-compose.yml) suppressing per-minute INFO stats that dominated log volume

### Negative
- **LAN-only by default:** The ntfy iOS app on the operator's iPhone connects to the server's LAN IP. If the iPhone is not on the home Wi-Fi, notifications are not delivered (RISK-023). Off-network delivery requires either ntfy cloud relay or exposing the ntfy server externally (e.g. via Tailscale), neither of which is currently configured.
- The ntfy server accumulates message history on disk (`ntfy-data` Docker volume); no TTL or size limit configured — volume can grow over time
- ntfy server has no authentication in the current deployment; any device on the home LAN can read or publish to any topic

### Neutral
- Uptime Kuma is configured to send alerts to ntfy as a notification provider; this is configuration in the Uptime Kuma UI, not in code

## Alternatives Considered

### Alternative 1: Gotify

**Description:** Self-hosted push notification server; well-established Go project.

**Rejected because:** The research document (`research-ntfy-vs-gotify.md`) found that Gotify requires token management (per-app tokens for sending, per-client tokens for receiving) which adds operational friction for a solo-maintained system. The ntfy API is token-free for simple deployments. Both support iOS via a native app; ntfy's app connects directly to self-hosted without a cloud relay for LAN use. Gotify's iOS app required a cloud relay for push delivery at the time of research.

### Alternative 2: Telegram bot

**Description:** Send alert messages via a Telegram bot to the operator's Telegram account.

**Rejected because:** Requires internet access (Telegram API is cloud-based). Violates the hard constraint: "no cloud-dependent services." The system must function on an isolated home network.

### Alternative 3: Email (SMTP)

**Description:** Send alert emails via a local or external SMTP server.

**Rejected because:** A local SMTP server adds significant operational complexity (mail queue, bounce handling, spam filters). An external SMTP relay (e.g. Gmail SMTP) requires internet access. Email is also a lower-urgency channel than push notification for time-sensitive alerts.

### Alternative 4: Uptime Kuma's native notification providers (Telegram, Slack, etc.)

**Description:** Use Uptime Kuma's built-in notification providers that work over the internet.

**Rejected because:** All useful Uptime Kuma providers (Telegram, Slack, PagerDuty, email) require internet access. The "internet-independence" constraint rules them out. ntfy self-hosted is the only provider Uptime Kuma supports that works LAN-only.

## Related

- Supersedes: None
- Related requirements: FR-MON-006
- Related NFRs: None directly; satisfies the no-cloud-dependency constraint from explore-summary
- Related explore option: OPT-A, OPT-B (both use ntfy for delivery)
