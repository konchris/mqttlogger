# -*- coding: utf-8 -*-

import pytest
from paho.mqtt import client
import random
import string

from mqttlogger.mqtt_client import on_connect, on_message, insert


@pytest.fixture()
def test_mqtt_server():
    """For integration testing use an already running mosquitto server

    This of course assumes one has internet access and this address is not blocked.
    """
    yield "test.mosquitto.org"


@pytest.fixture()
def test_mqtt_topic():
    """Because integration testing is happening on a public server, create a unique topic name"""
    base = "espy_test"
    random_part = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(7))
    yield "_".join((base, random_part))


@pytest.fixture()
def test_client(test_mqtt_server, test_mqtt_topic):
    """Persistent client using custom functions on_connect, on_message, insert for testing

    Returns
    -------
    my_client : paho.mqtt.client.Client

    """
    my_client = client.Client()
    my_client.on_connect = on_connect
    my_client.on_message = on_message
    my_client.insert = insert
    my_client.connect(test_mqtt_server, 1883, 60)
    my_client.unsubscribe("environment/#")
    my_client.subscribe(test_mqtt_topic)
    my_client.loop_start()
    yield my_client
    my_client.loop_stop()


@pytest.fixture()
def dummy_sender(test_mqtt_server):
    """Sender for

    Returns
    -------

    """
    dummy_client = client.Client()
    dummy_client.connect(test_mqtt_server, 1883, 60)
    dummy_client.loop_start()
    yield dummy_client
    dummy_client.loop_stop()
