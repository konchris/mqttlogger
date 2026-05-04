#!/usr/bin/env bash
# Legacy bare-metal launcher — pre-dates Docker Compose deployment.
# Use `docker compose up -d` instead. Kept for reference only.

sudo nohup python3 app.py >> nohup.log 2>&1 &
