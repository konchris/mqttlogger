#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Module/Script docstring

"""

__author__ = 'Christopher Espy'

import logging
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mqttlogger.data_model import SensorReading

module_logger = logging.getLogger("mqttlogger.mqtt_client")


def on_connect(client, userdata, flags, rc):
    """Function that is called when the broker responds to our connection request.

    The broker here mosquitto running on testingpi (192.168.1.14).

    This callback will subscribe to the "environment" topic and all subtopics. The topic levels are the following:
    1. top level: concern - {environment, -brewing-}
    2. second level: location 01 - {indoor, outdoor}
    3. third level: location 02 - {{cellar front,
                                    cellar back,
                                    bedroom,
                                    living_room,
                                    office,
                                    max_room,
                                    ben_room,
                                    kitchen,
                                    bathroom},
                                  {patio}}
    4. fourth level: reading type - {temperature, humidity, fan_state, floor_actuator, window_state, door_state}

    Parameters
    ----------
    client : paho.mqtt.client
        the client instance for this callback
    userdata : ?
        the private user data as set in Client() or user_data_set()
    flags : dict
        response flags sent by the broker
    rc : ?
        the connection result

    """
    module_logger.debug("Connected with result code %s" % str(rc))
    topics = ["environment/#"]
    for topic in topics:
        client.subscribe(topic)
        module_logger.info("Successfully subscribed to topic %s" % topic)


def on_message(client, userdata, message):
    """

    Parameters
    ----------
    client : paho.mqtt.client
        the client instance for this callback
    userdata : ?
        the private user data as set in Client() or user_data_set()
    message :
        an instance of MQTT Message. This is a class with members topic, payload, qos, retain

    """
    module_logger.debug("Received message for topic: %s" % message.topic)

    module_logger.debug("Message payload: %s" % message.payload)

    # Convert the payload
    if message.payload == b'true':
        message_payload = True
    elif message.payload == b'false':
        message_payload = False
    else:
        message_payload = float(message.payload)

    module_logger.debug("The converted message payload is: %s" % message_payload)
    #
    new_reading = SensorReading(currentdate=datetime.now().strftime("%Y-%m-%d"),
                                currenttime=datetime.now().strftime("%H:%M:%S"),
                                device=message.topic,
                                reading=float(message_payload))
    client.insert(new_reading)


def insert(sensor_reading):
    """Insert the new sensor reading into the database

    Parameters
    ----------
    sensor_reading : ?
        The SQLAlchemy data model for the sensor reading

    """
    module_logger.debug(f"Adding new record to DB: {sensor_reading}")
    engine = create_engine("mysql+mysqldb://mqttlogger:REDACTED_DB_PASS@192.168.1.14:3306/sensorreadings")
    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()
    session.add(sensor_reading)
    session.commit()
