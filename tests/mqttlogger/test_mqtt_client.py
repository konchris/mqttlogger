from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch


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


# --- FR-031, FR-032, FR-033: new field population ----------------------------


def test_on_message_sets_captured_at_to_utc_now():
    """FR-031: captured_at set to datetime.now(timezone.utc) at message receipt."""
    client = MagicMock()
    msg = _make_message("environment/indoor/attic/temperature", b"21.5")
    before = datetime.now(timezone.utc)
    on_message(client, None, msg)
    after = datetime.now(timezone.utc)
    reading = client.insert.call_args[0][0]
    assert reading.captured_at is not None
    # captured_at must be timezone-aware and within the before/after window
    assert reading.captured_at.tzinfo is not None
    assert before - timedelta(seconds=1) <= reading.captured_at <= after + timedelta(seconds=1)


def test_on_message_sets_location_from_topic_segments():
    """FR-032: location derived from topic segments 2+3 (joined by '/')."""
    client = MagicMock()
    msg = _make_message("environment/indoor/attic/temperature", b"21.5")
    on_message(client, None, msg)
    reading = client.insert.call_args[0][0]
    assert reading.location == "indoor/attic"


def test_on_message_sets_measurement_type_from_final_segment():
    """FR-033: measurement_type is the final slash-delimited topic segment."""
    client = MagicMock()
    msg = _make_message("environment/indoor/attic/temperature", b"21.5")
    on_message(client, None, msg)
    reading = client.insert.call_args[0][0]
    assert reading.measurement_type == "temperature"


def test_on_message_location_and_type_for_outdoor_humidity():
    """FR-032 + FR-033: different topic path derives correctly."""
    client = MagicMock()
    msg = _make_message("environment/outdoor/patio/humidity", b"65.0")
    on_message(client, None, msg)
    reading = client.insert.call_args[0][0]
    assert reading.location == "outdoor/patio"
    assert reading.measurement_type == "humidity"
