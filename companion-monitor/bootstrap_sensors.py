#!/usr/bin/env python3
"""Bootstrap sensor config from live DB history.

Queries MariaDB for all distinct device topics seen in the last 30 days
and writes them to sensors.yml. Run this once to initialise the config,
then review the output and remove any topics that should not be monitored.

Usage (from repo root):
    DB_HOST=localhost DB_PORT=3306 DB_USER=... DB_PASSWORD=... DB_NAME=... \\
        python companion-monitor/bootstrap_sensors.py

Or via Docker Compose (once DB is running):
    docker compose run --rm companion_monitor python bootstrap_sensors.py

Output is written to /app/sensors.yml inside the container, or to
./companion-monitor/sensors.yml when run directly.
"""

import os
import sys
from datetime import date, timedelta

import pymysql
import yaml

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_USER = os.environ.get("DB_USER", "")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "")
OUTPUT_FILE = os.environ.get("SENSORS_FILE", "/app/sensors.yml")
LOOKBACK_DAYS = int(os.environ.get("LOOKBACK_DAYS", "30"))

SQL = """
    SELECT DISTINCT device
    FROM sensorreadings
    WHERE DATE(captured_at) >= %s
    ORDER BY device
"""


def main():
    cutoff = (date.today() - timedelta(days=LOOKBACK_DAYS)).isoformat()
    print(f"Querying {DB_HOST}:{DB_PORT}/{DB_NAME} for sensors seen since {cutoff}...")

    try:
        conn = pymysql.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER,
            password=DB_PASSWORD, database=DB_NAME, connect_timeout=10,
        )
    except Exception as exc:
        print(f"ERROR: Could not connect to DB: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        with conn.cursor() as cur:
            cur.execute(SQL, (cutoff,))
            sensors = [row[0] for row in cur.fetchall()]
    finally:
        conn.close()

    if not sensors:
        print("WARNING: No sensors found in the last %d days." % LOOKBACK_DAYS)
        sys.exit(0)

    print(f"Found {len(sensors)} distinct sensors:")
    for s in sensors:
        print(f"  {s}")

    output = {
        "sensors": sensors,
        "_meta": {
            "generated": date.today().isoformat(),
            "source": f"{DB_HOST}/{DB_NAME}",
            "lookback_days": LOOKBACK_DAYS,
        },
    }

    with open(OUTPUT_FILE, "w") as f:
        yaml.dump(output, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"\nWritten to {OUTPUT_FILE}")
    print("Review the list and remove any sensors that should not be monitored.")


if __name__ == "__main__":
    main()
