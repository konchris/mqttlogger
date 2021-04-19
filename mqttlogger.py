#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Christopher Espy"

# Built-In Libraries
import argparse
import logging
import logging.handlers
import os

# Third-party libraries
import paho.mqtt.client as mqtt

# Local libraries
from mqttlogger.mqtt_client import on_connect, on_message, insert

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Create Logger
logger = logging.getLogger("mqttlogger")
logger.setLevel(logging.INFO)

# file handler
LOG_FOLDER = os.path.join(ROOT_DIR, "logs")
LOG_FILENAME = os.path.join(LOG_FOLDER, "mqttlogger.log")

if not os.path.exists(LOG_FOLDER):
    os.mkdir(os.path.dirname(LOG_FILENAME))

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
    mqttc.connect("localhost", 1883, 60)
    logger.debug("Client created")
    mqttc.loop_forever()

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main(sys.argv[1:]))
