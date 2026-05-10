from unittest.mock import MagicMock, patch

import pytest

from mqttlogger.data_model import SensorReading
from mqttlogger.mqtt_client import insert, on_message


def _make_message(topic, payload):
    msg = MagicMock()
    msg.topic = topic
    msg.payload = payload
    return msg


# --- on_message ---------------------------------------------------------------


def test_on_message_float_creates_correct_reading():
    client = MagicMock()
    msg = _make_message("environment/indoor/kitchen/temperature", b"21.5")
    on_message(client, None, msg)
    client.insert.assert_called_once()
    reading = client.insert.call_args[0][0]
    assert isinstance(reading, SensorReading)
    assert reading.device == "environment/indoor/kitchen/temperature"
    assert reading.reading == 21.5


def test_on_message_true_payload_becomes_one():
    client = MagicMock()
    msg = _make_message("environment/indoor/kitchen/door_state", b"true")
    on_message(client, None, msg)
    reading = client.insert.call_args[0][0]
    assert reading.reading == 1.0


def test_on_message_false_payload_becomes_zero():
    client = MagicMock()
    msg = _make_message("environment/indoor/kitchen/door_state", b"false")
    on_message(client, None, msg)
    reading = client.insert.call_args[0][0]
    assert reading.reading == 0.0


def test_on_message_bad_payload_does_not_call_insert():
    client = MagicMock()
    msg = _make_message("environment/indoor/kitchen/temperature", b"not-a-number")
    on_message(client, None, msg)
    client.insert.assert_not_called()


def test_on_message_empty_payload_does_not_call_insert():
    client = MagicMock()
    msg = _make_message("environment/indoor/kitchen/temperature", b"")
    on_message(client, None, msg)
    client.insert.assert_not_called()


# --- insert -------------------------------------------------------------------


def _mock_session():
    session = MagicMock()
    factory = MagicMock(return_value=session)
    return session, factory


def test_insert_adds_and_commits():
    reading = SensorReading(device="test/sensor", reading=1.0)
    session, factory = _mock_session()
    with (
        patch("mqttlogger.mqtt_client.create_connection_string", return_value="x"),
        patch("mqttlogger.mqtt_client.create_engine"),
        patch("mqttlogger.mqtt_client.sessionmaker", return_value=factory),
    ):
        insert(reading)
    session.add.assert_called_once_with(reading)
    session.commit.assert_called_once()


def test_insert_db_error_does_not_raise():
    reading = SensorReading(device="test/sensor", reading=1.0)
    session, factory = _mock_session()
    session.commit.side_effect = Exception("connection refused")
    with (
        patch("mqttlogger.mqtt_client.create_connection_string", return_value="x"),
        patch("mqttlogger.mqtt_client.create_engine"),
        patch("mqttlogger.mqtt_client.sessionmaker", return_value=factory),
    ):
        insert(reading)  # must not raise
