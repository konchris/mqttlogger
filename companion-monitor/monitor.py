#!/usr/bin/env python3
"""Companion DB Monitor — OPT-B IP-001 prototype.

Polls MariaDB on a configurable interval, checks two directions:
  1. Config sensors absent from DB in the last gap window → crash / sensor silent alert
  2. DB sensors absent from config → new/unknown sensor notification

State is maintained in-memory so alerts fire on transition (missing → seen, seen → missing)
rather than every poll cycle.

Configuration via environment variables:
  DB_HOST              MariaDB host          (default: mariadb)
  DB_PORT              MariaDB port          (default: 3306)
  DB_USER              MariaDB user
  DB_PASSWORD          MariaDB password
  DB_NAME              MariaDB database name
  NTFY_URL             ntfy push URL         (e.g. http://ntfy:80/mqttlogger-alerts)
  SENSORS_FILE         Path to sensors.yml   (default: /app/sensors.yml)
  POLLING_INTERVAL_SECONDS  How often to poll (default: 300)
  GAP_WINDOW_MINUTES        Silence window    (default: 10)
"""

import logging
import os
import time
import urllib.request
import urllib.error
from typing import Optional

import pymysql
import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("companion-monitor")

# --- Configuration -----------------------------------------------------------

DB_HOST = os.environ.get("DB_HOST", "mariadb")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_USER = os.environ.get("DB_USER", "")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "")
NTFY_URL = os.environ.get("NTFY_URL", "")
SENSORS_FILE = os.environ.get("SENSORS_FILE", "/app/sensors.yml")
POLLING_INTERVAL = int(os.environ.get("POLLING_INTERVAL_SECONDS", "300"))
GAP_WINDOW = int(os.environ.get("GAP_WINDOW_MINUTES", "10"))


# --- Helpers -----------------------------------------------------------------

def load_sensor_config(path: str) -> tuple[list[str], set[str]]:
    """Return (monitored, excluded) sensor sets from sensors.yml.

    monitored  — gap-checked; alert if silent for > GAP_WINDOW minutes
    excluded   — known event-driven sensors; suppressed from both gap and unknown alerts
    """
    with open(path) as f:
        data = yaml.safe_load(f)
    sensors = data.get("sensors", [])
    if not sensors:
        raise ValueError(f"No sensors defined in {path}")
    excluded = set(str(s) for s in data.get("excluded", []))
    logger.info("Loaded %d monitored + %d excluded sensors from %s", len(sensors), len(excluded), path)
    return [str(s) for s in sensors], excluded


def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        connect_timeout=10,
    )


def query_active_sensors(window_minutes: int) -> set[str]:
    """Return the set of device topics that have published within the last *window_minutes*."""
    sql = """
        SELECT DISTINCT device
        FROM sensorreadings
        WHERE TIMESTAMP(currentdate, currenttime) >= DATE_SUB(NOW(), INTERVAL %s MINUTE)
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (window_minutes,))
            return {row[0] for row in cur.fetchall()}
    finally:
        conn.close()


def push_notification(message: str, title: str = "mqttlogger alert") -> None:
    if not NTFY_URL:
        logger.warning("NTFY_URL not set — notification suppressed: %s", message)
        return
    try:
        req = urllib.request.Request(
            NTFY_URL,
            data=message.encode(),
            headers={"Title": title},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            logger.debug("Notification sent status=%s", resp.status)
    except Exception as exc:
        logger.error("Failed to send notification: %s", exc)


# --- Main loop ---------------------------------------------------------------

def run_check(expected: list[str], excluded: set[str], alerted_missing: set, alerted_unknown: set) -> None:
    try:
        active = query_active_sensors(GAP_WINDOW)
    except Exception as exc:
        logger.error("DB query failed: %s", exc)
        return

    expected_set = set(expected)

    # Direction 1: expected sensors absent from DB
    now_missing = expected_set - active
    now_recovered = alerted_missing - now_missing

    for sensor in sorted(now_missing - alerted_missing):
        logger.warning("ALERT: sensor silent — %s", sensor)
        push_notification(
            f"Sensor silent (>{GAP_WINDOW}min): {sensor}",
            title="mqttlogger: sensor gap",
        )
    alerted_missing.update(now_missing - alerted_missing)

    for sensor in sorted(now_recovered):
        logger.info("RECOVERY: sensor resumed — %s", sensor)
        push_notification(
            f"Sensor resumed: {sensor}",
            title="mqttlogger: sensor recovery",
        )
    alerted_missing -= now_recovered

    # Direction 2: DB sensors absent from config (unknown / new sensor).
    # Excluded sensors are known event-driven devices — suppress their unknown alerts.
    now_unknown = active - expected_set - excluded
    new_unknowns = now_unknown - alerted_unknown
    gone_unknowns = alerted_unknown - now_unknown

    for sensor in sorted(new_unknowns):
        logger.warning("UNKNOWN sensor in DB (not in config): %s", sensor)
        push_notification(
            f"Unknown sensor publishing: {sensor}",
            title="mqttlogger: unknown sensor",
        )
    alerted_unknown.update(new_unknowns)
    alerted_unknown -= gone_unknowns

    logger.info(
        "Check complete — active=%d missing=%d unknown=%d",
        len(active), len(alerted_missing), len(alerted_unknown),
    )


def main() -> None:
    logger.info("Companion monitor starting up")
    logger.info("DB=%s:%s/%s  gap=%dmin  poll=%ds", DB_HOST, DB_PORT, DB_NAME, GAP_WINDOW, POLLING_INTERVAL)

    expected, excluded = load_sensor_config(SENSORS_FILE)

    alerted_missing: set[str] = set()
    alerted_unknown: set[str] = set()

    while True:
        run_check(expected, excluded, alerted_missing, alerted_unknown)
        time.sleep(POLLING_INTERVAL)


if __name__ == "__main__":
    main()
