#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Module/Script docstring

"""

__author__ = 'Christopher Espy'

import logging
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from constants import ROOT_DIR
from mqttlogger.data_model import SensorReading
from mqttlogger.db_connection import create_connection_string

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

    # Publish online status to the LWT topic so monitoring tools see a clear transition.
    status_topic = getattr(client, 'status_topic', None)
    if status_topic:
        client.publish(status_topic, "online", qos=1, retain=True)
        module_logger.info("Published online status to %s", status_topic)

    topic_filter = getattr(client, 'topic_filter', "environment/#")
    client.subscribe(topic_filter)
    module_logger.info("Successfully subscribed to topic %s" % topic_filter)


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
    module_logger.info("Received message for topic: %s" % message.topic)

    module_logger.debug("Message payload: %s" % message.payload)

    # Convert the payload
    try:
        if message.payload == b'true':
            message_payload = True
        elif message.payload == b'false':
            message_payload = False
        else:
            message_payload = float(message.payload)
    except (ValueError, TypeError):
        module_logger.error(
            "Malformed payload for topic %s: %r" % (message.topic, message.payload)
        )
        return

    module_logger.debug("The converted message payload is: %s" % message_payload)

    new_reading = SensorReading(
        captured_at=datetime.now(timezone.utc),
        location='/'.join(message.topic.split('/')[1:3]),
        measurement_type=message.topic.split('/')[-1],
        device=message.topic,
        reading=float(message_payload),
    )
    try:
        client.insert(new_reading)
    except Exception as exc:
        module_logger.error(
            "DB write failed for device=%s value=%s: %s" % (
                message.topic, new_reading.reading, exc
            )
        )


def insert(sensor_reading):
    """Insert the new sensor reading into the database

    Parameters
    ----------
    sensor_reading : ?
        The SQLAlchemy data model for the sensor reading

    """
    module_logger.debug(f"Adding new record to DB: {sensor_reading}")

    db_conn_str = create_connection_string(ROOT_DIR / "config.json")

    engine = create_engine(db_conn_str)
    module_logger.debug(f"Successfully created engine: {engine.url}")

    Session = sessionmaker()
    Session.configure(bind=engine)

    session = Session()

    module_logger.debug("Adding sensor reading")
    try:
        session.add(sensor_reading)
        session.commit()
        module_logger.info("Successfully committed to the db.")
    except Exception as exc:
        module_logger.error(
            "DB write failed for device=%s value=%s: %s" % (
                sensor_reading.device, sensor_reading.reading, exc
            )
        )
