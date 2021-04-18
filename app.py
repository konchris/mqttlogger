#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Christopher Espy"

# Built-In Libraries
import logging
import argparse

# Third-party libraries
import paho.mqtt.client as mqtt
# from flask import Flask, render_template
# from flask_sqlalchemy import SQLAlchemy

# Local libraries
# from mqttlogger.data_model import SensorReading
from mqttlogger.mqtt_client import on_connect, on_message, insert

logging.basicConfig(
    filename="mqttlogger.log",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"

)

LOG = logging.getLogger("mqttlogger")


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
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    LOG.setLevel(log_level)
    LOG.debug("LOG_LEVEL is DEBUG")

    LOG.debug("Creating MQTT Client")
    mqttc = mqtt.Client()
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    mqttc.insert = insert
    mqttc.connect("localhost", 1883, 60)
    LOG.debug("Client created")
    mqttc.loop_forever()

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main(sys.argv[1:]))

