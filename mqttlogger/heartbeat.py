#!/usr/bin/env python3
import logging
import threading
import time
import urllib.request

logger = logging.getLogger("mqttlogger.heartbeat")


def start_heartbeat(url: str, interval: int = 60) -> threading.Thread:
    """Start a background daemon thread that pushes a heartbeat to *url* every *interval* seconds.

    The first push fires immediately so that startup is visible in the monitoring UI.
    If the push fails (network error, service not ready) the error is logged as a
    warning and the loop continues — a failed heartbeat is not fatal to the logger.
    """
    def _push():
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                logger.debug("Heartbeat sent status=%s", resp.status)
        except Exception as exc:
            logger.warning("Heartbeat push failed: %s", exc)

    def _loop():
        logger.info("Heartbeat started url=%s interval=%ds", url, interval)
        while True:
            _push()
            time.sleep(interval)

    t = threading.Thread(target=_loop, daemon=True, name="heartbeat")
    t.start()
    return t
