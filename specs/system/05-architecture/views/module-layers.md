# View: Module Layers

**Viewtype:** Module — allowed dependencies
**Answers:** What are the structural layers and what dependency directions are permitted?
**Audience:** Developers, code reviewers
**Related NFRs:** NFR-MAIN-001 (testability), Constitution Principle VII (Minimal Surface Area)

Dependency rule: modules may only depend on modules in the same or lower layer. Upward dependencies (lower → higher) are prohibited.

---

## mqtt_logger Layers

```mermaid
graph TD
    subgraph L1["Layer 1 — Application (Entry Point)"]
        APP["app.py\nOrchestration · Startup · Signal handling"]
    end

    subgraph L2["Layer 2 — Domain (Message Handling)"]
        CLIENT["mqtt_client.py\nMQTT event handling · Message parsing"]
        HEART["heartbeat.py\nLiveness signal emission"]
    end

    subgraph L3["Layer 3 — Data Access"]
        MODEL["data_model.py\nSensorReading model · Schema definition"]
        DBCONN["db_connection.py\nConfig loading · Connection string"]
    end

    subgraph L4["Layer 4 — Infrastructure (External)"]
        PAHOMQTT["paho-mqtt\nMQTT client library"]
        SQLA["SQLAlchemy\nORM + session management"]
        MARIADB["MariaDB\nDatabase"]
        UKHTTP["Uptime Kuma\nHTTP push endpoint"]
        CFGJSON["config.json\nConfiguration file"]
    end

    APP --> CLIENT
    APP --> HEART
    APP --> DBCONN
    CLIENT --> MODEL
    CLIENT --> PAHOMQTT
    MODEL --> SQLA
    SQLA --> MARIADB
    DBCONN --> CFGJSON
    DBCONN --> MODEL
    HEART --> UKHTTP
    APP --> PAHOMQTT
```

### Layer Notes

**Layer 1 (Application):** `app.py` is the only allowed entry point. It imports from Layer 2 and Layer 3 but is itself imported by nothing. This layer is thin by design — it orchestrates but does not contain logic.

**Layer 2 (Domain):** Message handling and liveness emission. `mqtt_client.py` is the hot path. `heartbeat.py` is an independent thread with no dependency on `mqtt_client.py` — they share nothing except the process.

**Layer 3 (Data Access):** The data model and configuration are isolated from MQTT concerns. `data_model.py` knows nothing about MQTT topics — it only knows about `SensorReading` fields. This separation means the DB schema can evolve independently of the MQTT parsing logic.

**Layer 4 (Infrastructure):** Third-party libraries and external systems. No owned code lives here.

---

## companion_monitor Layers

```mermaid
graph TD
    subgraph L1B["Layer 1 — Application"]
        MAINF["main()\nPoll loop · State management\nalerted_missing · alerted_unknown"]
    end

    subgraph L2B["Layer 2 — Domain"]
        LOADSENS["load_sensor_config()\nYAML parsing · Sensor classification"]
        RUNCHECK["run_check()\nGap detection · Set logic · State transitions"]
    end

    subgraph L3B["Layer 3 — Data Access"]
        QUERYDB["query_active_sensors()\nSQL SELECT · Result set to Python set"]
        PUSHNOTI["push_notification()\nHTTP POST construction · Error handling"]
        GETCONN["get_db_connection()\nPyMySQL connection from env vars"]
    end

    subgraph L4B["Layer 4 — Infrastructure (External)"]
        PYMYSQL["PyMySQL\nDB driver"]
        MARIADB2["MariaDB\nDatabase (read-only path)"]
        YAML["PyYAML\nYAML parser"]
        NTFYHTTP["ntfy\nHTTP API"]
        SENSORYML["sensors.yml\nVolume-mounted config"]
    end

    MAINF --> LOADSENS
    MAINF --> RUNCHECK
    RUNCHECK --> QUERYDB
    RUNCHECK --> PUSHNOTI
    QUERYDB --> GETCONN
    GETCONN --> PYMYSQL
    PYMYSQL --> MARIADB2
    LOADSENS --> YAML
    LOADSENS --> SENSORYML
    PUSHNOTI --> NTFYHTTP
```

### Layer Notes

**State isolation:** The `alerted_missing` and `alerted_unknown` sets live in `main()` scope only. `run_check()` receives them as mutable arguments — it does not own state. This design means the detection logic (`run_check`) can be tested in isolation by passing any state combination.

**No persistent DB connection:** `get_db_connection()` opens a new PyMySQL connection on each poll cycle and closes it immediately after the query. This avoids stale connection errors on the 5-minute interval. The overhead (connection setup) is negligible at this frequency.

---

## Cross-Container Dependency Rule

The two Python applications (`mqtt_logger` and `companion_monitor`) share no code, no shared volume, and no direct process communication. Their only shared resource is the MariaDB database, accessed via separate connections. This is intentional: `companion_monitor` must be able to operate even when `mqtt_logger` is down (that is the crash-detection scenario).
