#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Christopher Espy"

# Built-In Libraries
import argparse
import logging
import logging.handlers
import signal
import sys

# Third-party libraries
import paho.mqtt.client as mqtt

# Local libraries
from constants import ROOT_DIR
from mqttlogger.db_connection import load_config_file
from mqttlogger.mqtt_client import on_connect, on_message, insert

# Create Logger
logger = logging.getLogger("mqttlogger")
logger.setLevel(logging.INFO)

# file handler
LOG_FOLDER = ROOT_DIR / "logs"
LOG_FILENAME = LOG_FOLDER / "mqttlogger.log"

if not LOG_FOLDER.exists():
    LOG_FOLDER.mkdir()

fh = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=2000000, backupCount=5)

# console handler
ch = logging.StreamHandler()

# formatter
formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)s | %(message)s")
ch.setFormatter(formatter)
fh.setFormatter(formatter)

# add handlers to logger
logger.addHandler(fh)


def parse_arguments(args):
    """The argument parser
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', help='set logging trace level to debug', action='store_true')
    return parser.parse_args(args)


def main(argv=None):
    """The main function"""
    arguments = parse_arguments(argv)

    if arguments.debug:
        logger.addHandler(ch)
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logger.setLevel(log_level)
    logger.debug("LOG_LEVEL is DEBUG")

    logger.debug("Creating MQTT Client")
    mqttc = mqtt.Client()
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    mqttc.insert = insert

    config = load_config_file(ROOT_DIR / "config.json")

    mqttc.connect(config["mqtt_server_ip"], config["mqtt_server_port"], 60)
    logger.debug("Client created")

    # Handle SIGTERM gracefully
    def handle_sigterm(signum, frame):
        logger.info("Received SIGTERM, disconnecting MQTT client...")
        mqttc.loop_stop()
        mqttc.disconnect()
        sys.exti(0)

    signal.signal(signal.SIGTERM, handle_sigterm)

    logger.debug("Starting MQTT loop_forever")
    mqttc.loop_forever()
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main(sys.argv[1:]))
