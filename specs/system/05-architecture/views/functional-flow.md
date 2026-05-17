# View: Functional Flow

**Viewtype:** Component-and-Connector — behaviour over time
**Answers:** How do functions activate and interact for each key operational scenario?
**Audience:** Systems engineers, testers
**Related scenarios:** SCN-001, SCN-003 (with monitoring), SCN-005, SCN-008 (live schema migration)
**Last Updated:** 2026-05-17 (feature 009 — updated SCN-001 field names; added SCN-008 migration flow)

---

## Flow 1 — Normal Message Capture (SCN-001, MODE-001)

Shows the end-to-end path from sensor measurement to committed database record during steady-state operation.

```mermaid
sequenceDiagram
    participant Sensor as HomeMatic Sensor
    participant CCU3 as CCU3 / RedMatic
    participant Broker as eclipse-mosquitto
    participant Logger as mqtt_logger<br/>(on_message)
    participant DB as MariaDB

    Sensor->>CCU3: value change (proprietary protocol)
    CCU3->>Broker: MQTT PUBLISH<br/>topic: environment/indoor/cellar/temperature<br/>payload: {"val": 14.3}
    Broker->>Logger: MQTT message delivered<br/>(subscription: environment/#)
    Logger->>Logger: parse payload → SensorReading<br/>device=topic, reading=14.3,<br/>captured_at=now(UTC), location=indoor/cellar,<br/>measurement_type=temperature
    Logger->>DB: SQLAlchemy INSERT<br/>BEGIN … COMMIT
    DB-->>Logger: commit OK
    Logger->>Logger: log INFO "stored reading"
    Note over Logger,DB: If commit fails: log ERROR, discard message,<br/>continue (MODE-005 — DB unavailable)
```

---

## Flow 2 — Crash Detection and Notification (SCN-003 + OPT-A)

Shows how a silent container crash is detected and the operator is notified. Two sub-flows: the heartbeat path during normal operation, and the alert path after a crash.

```mermaid
sequenceDiagram
    participant Logger as mqtt_logger<br/>(heartbeat thread)
    participant UK as uptime_kuma
    participant NTFY as ntfy
    participant iPhone as Operator iPhone

    loop Every 60 seconds (normal operation)
        Logger->>UK: HTTP POST /api/push/token<br/>?status=up&msg=OK
        UK-->>Logger: 200 OK
        UK->>UK: reset watchdog timer
    end

    Note over Logger: Container killed (crash / docker kill)
    Note over Logger: Heartbeat thread stops — no more pushes

    UK->>UK: watchdog timer expires<br/>(after ~60s with no push)
    UK->>UK: monitor transitions DOWN
    UK->>NTFY: HTTP POST /mqttlogger-alerts<br/>Title: "mqttlogger: DOWN"
    NTFY->>iPhone: push notification<br/>(home LAN — device must be on Wi-Fi)
    Note over iPhone: Operator sees alert<br/>typically within 93–120s of crash
```

---

## Flow 3 — Sensor Gap Detection and Notification (OPT-B, FR-MON-002)

Shows the companion monitor poll cycle detecting a sensor that has gone silent.

```mermaid
sequenceDiagram
    participant CM as companion_monitor<br/>(run_check)
    participant DB as MariaDB
    participant NTFY as ntfy
    participant iPhone as Operator iPhone

    loop Every 5 minutes
        CM->>DB: SELECT DISTINCT device<br/>WHERE ts >= NOW() - 600min
        DB-->>CM: {set of active devices}
        CM->>CM: expected_set - active = now_missing
        CM->>CM: now_missing - alerted_missing = new_alerts

        alt new_alerts is not empty (state transition: normal → silent)
            CM->>NTFY: HTTP POST /mqttlogger-alerts<br/>"Sensor silent (>600min): attic/temp"
            NTFY->>iPhone: push notification
            CM->>CM: alerted_missing.add(sensor)
        else no change
            CM->>CM: log DEBUG "no change"
        end

        CM->>CM: alerted_missing - now_missing = recovered
        alt recovered is not empty (state transition: silent → active)
            CM->>NTFY: HTTP POST /mqttlogger-alerts<br/>"Sensor resumed: attic/temp"
            NTFY->>iPhone: push notification
            CM->>CM: alerted_missing.remove(sensor)
        end
    end
```

---

## Flow 4 — Startup and Connection Sequence (MODE-002)

Shows the orchestrated startup, including the mariadb healthcheck dependency and the LWT registration sequence.

```mermaid
flowchart TD
    START([Container starts]) --> LOADCFG[Load config.json\nvalidate all required fields]
    LOADCFG -->|missing/invalid field| FAIL([Exit — log specific field name and source])
    LOADCFG -->|valid| SETUPLOG[Configure rotating file handler\nset log level]
    SETUPLOG --> DBWAIT{mariadb\nhealthcheck\npassing?}
    DBWAIT -->|no — Docker Compose waits| DBWAIT
    DBWAIT -->|yes| LWT[Register MQTT LWT\ntopic: mqttlogger/status\npayload: 'offline'\nQoS 1, retain]
    LWT --> HEARTBEAT{heartbeat_url\nin config?}
    HEARTBEAT -->|yes| STARTTHREAD[Start heartbeat\ndaemon thread]
    HEARTBEAT -->|no| CONNECT
    STARTTHREAD --> CONNECT[MQTT connect\nto configured broker:port]
    CONNECT -->|fail| RECONNECT[paho-mqtt auto-retry\nlog each attempt]
    RECONNECT --> CONNECT
    CONNECT -->|success| ONCONNECT[on_connect:\nsubscribe environment/#\npublish status = 'online']
    ONCONNECT --> MODE001([MODE-001 — Normal Operation])
```

---

## Flow 5 — Live Schema Migration (SCN-008, Feature 009)

Shows the operator-executed migration procedure that evolves the `sensorreadings` schema
from the legacy two-column timestamp representation to the unified `captured_at` column.
See ADR-008 for the decision rationale.

```mermaid
flowchart TD
    START([Operator initiates maintenance window]) --> DRYRUN[Run IP-001 dry-run tasks\nSELECT DISTINCT device — confirm 4-level pattern\nPreview SELECT — verify backfill derivation\nNULL count check — currentdate/currenttime]
    DRYRUN -->|any task fails| ABORT1([STOP — investigate topic anomalies\nbefore proceeding])
    DRYRUN -->|all tasks pass — ASM-A-001..A-004 resolved| STAGE[Stage migration SQL on sietchtabr\ndb/migration-009-schema-evolution.sql]
    STAGE --> DOWN[docker compose down\nCapture gap begins]
    DOWN --> ADD[ALTER TABLE: ADD captured_at NULL\nADD location NULL\nADD measurement_type NULL]
    ADD --> TXN[START TRANSACTION\nUPDATE SET captured_at = TIMESTAMP\nUPDATE SET location = SUBSTRING_INDEX x2\nUPDATE SET measurement_type = SUBSTRING_INDEX\nCOMMIT]
    TXN --> NULLCHECK{SELECT COUNT WHERE\ncaptured_at IS NULL\nor location IS NULL\nor measurement_type IS NULL}
    NULLCHECK -->|count > 0| ABORT2([STOP — backfill incomplete\nInvestigate NULL rows before DROP])
    NULLCHECK -->|count = 0| MODIFY[ALTER TABLE: MODIFY captured_at NOT NULL\nMODIFY location NOT NULL\nMODIFY measurement_type NOT NULL]
    MODIFY --> INDEX[CREATE INDEX idx_loc_mtype_time\non sensorreadings location, measurement_type, captured_at]
    INDEX --> DROP[ALTER TABLE: DROP COLUMN currentdate\nDROP COLUMN currenttime]
    DROP --> UP[docker compose up -d\nNew image with updated code deployed]
    UP --> VERIFY[Spot-check new row in DB\nverify captured_at, location, measurement_type populated]
    VERIFY -->|values correct| DONE([Migration complete\nCapture gap ends])
    VERIFY -->|values missing or wrong| ROLLBACK([STOP — investigate\nCheck code deployment and image rebuild])
```

**Key properties of this flow:**
- The UPDATE backfill is transactional; if interrupted, all three column updates roll back together
- DDL (ADD/MODIFY/DROP COLUMN) auto-commits in MariaDB/InnoDB — the null-check is the gate between transactional backfill and irreversible schema changes
- The stack-down window encompasses both the migration and the `docker compose up -d` with new code; no intermediate state where old code runs against new schema

---

## Flow 6 — Graceful Shutdown (MODE-003)

```mermaid
flowchart TD
    SIGNAL([SIGTERM or SIGINT received]) --> STOPMQTT[mqtt_loop_stop\nno new messages accepted]
    STOPMQTT --> INFLIGHT{in-flight DB\nwrite in progress?}
    INFLIGHT -->|yes| WAIT[wait for commit\nor rollback]
    INFLIGHT -->|no| DISCONNECT
    WAIT --> DISCONNECT[mqtt.disconnect\nbroker receives clean DISCONNECT\nLWT is NOT sent]
    DISCONNECT --> LOG[log INFO 'shutdown complete']
    LOG --> EXIT([exit 0])
```
