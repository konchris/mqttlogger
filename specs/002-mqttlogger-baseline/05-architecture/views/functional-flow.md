# View: Functional Flow

**Viewtype:** Component-and-Connector — behaviour over time
**Answers:** How do functions activate and interact for each key operational scenario?
**Audience:** Systems engineers, testers
**Related scenarios:** SCN-001, SCN-003 (with monitoring), SCN-005

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
    Logger->>Logger: parse payload → SensorReading<br/>device=topic, value=14.3,<br/>currentdate=today, currenttime=now
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

## Flow 5 — Graceful Shutdown (MODE-003)

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
