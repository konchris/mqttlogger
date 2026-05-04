#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import time
import pytest
from unittest.mock import MagicMock, patch


@pytest.mark.integration
def test_send_floats(test_client, dummy_sender, test_mqtt_topic):
    received = []
    test_client.insert = lambda sr: received.append(sr)

    dummy_sender.publish(test_mqtt_topic, "18.3")
    time.sleep(2)

    assert len(received) == 1
    assert received[0].reading == pytest.approx(18.3)
    assert received[0].device == test_mqtt_topic


@pytest.mark.integration
def test_send_boolean_true(test_client, dummy_sender, test_mqtt_topic):
    received = []
    test_client.insert = lambda sr: received.append(sr)

    dummy_sender.publish(test_mqtt_topic, b'true')
    time.sleep(2)

    assert len(received) == 1
    assert received[0].reading == 1.0


@pytest.mark.integration
def test_send_boolean_false(test_client, dummy_sender, test_mqtt_topic):
    received = []
    test_client.insert = lambda sr: received.append(sr)

    dummy_sender.publish(test_mqtt_topic, b'false')
    time.sleep(2)

    assert len(received) == 1
    assert received[0].reading == 0.0


@pytest.mark.integration
def test_malformed_payload_discarded(test_client, dummy_sender, test_mqtt_topic):
    received = []
    test_client.insert = lambda sr: received.append(sr)

    dummy_sender.publish(test_mqtt_topic, b'not-a-number')
    time.sleep(2)

    assert len(received) == 0, "malformed payload must not produce a DB record"

    # Service must continue processing subsequent valid messages
    dummy_sender.publish(test_mqtt_topic, "22.5")
    time.sleep(2)

    assert len(received) == 1
    assert received[0].reading == pytest.approx(22.5)


def test_debug_flag_enables_verbose_logging(caplog):
    import app as app_module

    mock_mqttc = MagicMock()
    mock_mqttc.loop_forever.return_value = None

    with patch("app.mqtt.Client", return_value=mock_mqttc):
        with caplog.at_level(logging.DEBUG, logger="mqttlogger"):
            app_module.main(["--debug"])

    debug_records = [r for r in caplog.records if r.levelno == logging.DEBUG]
    assert len(debug_records) > 0, "no DEBUG records emitted with --debug flag"


@pytest.mark.integration
def test_clean_disconnect(test_client, test_mqtt_topic):
    assert test_client.is_connected()
    test_client.loop_stop()
    test_client.disconnect()
    assert not test_client.is_connected()


@pytest.mark.integration
def test_reconnect_after_disconnect(test_client, dummy_sender, test_mqtt_topic):
    received = []
    test_client.insert = lambda sr: received.append(sr)

    # Confirm messages flow before disconnect
    dummy_sender.publish(test_mqtt_topic, "1.0")
    time.sleep(2)
    assert len(received) == 1

    # Override on_connect so reconnect re-subscribes to the test topic
    def on_reconnect(client, userdata, flags, rc):
        client.subscribe(test_mqtt_topic)

    test_client.on_connect = on_reconnect
    test_client.disconnect()
    # loop_stop() waits for the thread to exit and clears _thread so loop_start() can restart
    test_client.loop_stop()
    test_client.reconnect()
    test_client.loop_start()
    time.sleep(2)

    # Messages published after reconnect must still be received
    dummy_sender.publish(test_mqtt_topic, "2.0")
    time.sleep(2)

    assert len(received) == 2
    assert received[1].reading == pytest.approx(2.0)


@pytest.mark.integration
def test_db_write_failure_continues(test_client, dummy_sender, test_mqtt_topic):
    """FR-014: a DB write error must not stop subsequent messages from being processed."""
    # Raise on first call, succeed on second
    mock_insert = MagicMock(side_effect=[Exception("simulated DB failure"), None])
    test_client.insert = mock_insert

    dummy_sender.publish(test_mqtt_topic, "10.0")
    time.sleep(2)
    dummy_sender.publish(test_mqtt_topic, "20.0")
    time.sleep(2)

    assert mock_insert.call_count == 2
