import urllib.request
from unittest.mock import patch, MagicMock

import pytest

import monitor

VALID_YAML = """
sensors:
  - environment/indoor/kitchen/temperature
  - environment/indoor/bedroom/humidity
excluded:
  - environment/indoor/kitchen/door_state
"""


@pytest.fixture
def sensors_file(tmp_path):
    p = tmp_path / "sensors.yml"
    p.write_text(VALID_YAML)
    return str(p)


# --- load_sensor_config -------------------------------------------------------


def test_load_sensor_config_returns_monitored_and_excluded(sensors_file):
    monitored, excluded = monitor.load_sensor_config(sensors_file)
    assert "environment/indoor/kitchen/temperature" in monitored
    assert "environment/indoor/bedroom/humidity" in monitored
    assert "environment/indoor/kitchen/door_state" in excluded


def test_load_sensor_config_excluded_not_in_monitored(sensors_file):
    monitored, excluded = monitor.load_sensor_config(sensors_file)
    for sensor in excluded:
        assert sensor not in monitored


def test_load_sensor_config_missing_file():
    with pytest.raises(FileNotFoundError):
        monitor.load_sensor_config("/nonexistent/sensors.yml")


def test_load_sensor_config_empty_sensors_raises(tmp_path):
    p = tmp_path / "sensors.yml"
    p.write_text("sensors: []\nexcluded: []\n")
    with pytest.raises(ValueError):
        monitor.load_sensor_config(str(p))


# --- run_check: missing sensor detection --------------------------------------


def test_run_check_missing_sensor_fires_alert():
    expected = ["sensor/a", "sensor/b"]
    excluded = set()
    alerted_missing: set = set()
    alerted_unknown: set = set()

    with patch.object(monitor, "query_active_sensors", return_value={"sensor/b"}), \
         patch.object(monitor, "push_notification") as mock_push:
        monitor.run_check(expected, excluded, alerted_missing, alerted_unknown)

    assert "sensor/a" in alerted_missing
    assert "sensor/b" not in alerted_missing
    mock_push.assert_called_once()
    assert "sensor/a" in mock_push.call_args[0][0]


def test_run_check_alert_fires_once_not_on_every_cycle():
    expected = ["sensor/a"]
    excluded = set()
    alerted_missing: set = set()
    alerted_unknown: set = set()

    with patch.object(monitor, "query_active_sensors", return_value=set()), \
         patch.object(monitor, "push_notification") as mock_push:
        monitor.run_check(expected, excluded, alerted_missing, alerted_unknown)
        assert mock_push.call_count == 1
        monitor.run_check(expected, excluded, alerted_missing, alerted_unknown)
        assert mock_push.call_count == 1  # no second alert on second cycle


def test_run_check_recovery_clears_state_and_notifies():
    expected = ["sensor/a"]
    excluded = set()
    alerted_missing: set = {"sensor/a"}
    alerted_unknown: set = set()

    with patch.object(monitor, "query_active_sensors", return_value={"sensor/a"}), \
         patch.object(monitor, "push_notification") as mock_push:
        monitor.run_check(expected, excluded, alerted_missing, alerted_unknown)

    assert "sensor/a" not in alerted_missing
    mock_push.assert_called_once()
    assert "resumed" in mock_push.call_args[0][0].lower()


# --- run_check: unknown sensor detection --------------------------------------


def test_run_check_unknown_sensor_fires_alert():
    expected = ["sensor/known"]
    excluded = set()
    alerted_missing: set = set()
    alerted_unknown: set = set()

    with patch.object(monitor, "query_active_sensors", return_value={"sensor/known", "sensor/new"}), \
         patch.object(monitor, "push_notification") as mock_push:
        monitor.run_check(expected, excluded, alerted_missing, alerted_unknown)

    assert "sensor/new" in alerted_unknown
    mock_push.assert_called_once()
    assert "sensor/new" in mock_push.call_args[0][0]


def test_run_check_excluded_sensor_not_alerted():
    expected = ["sensor/known"]
    excluded = {"sensor/event_driven"}
    alerted_missing: set = set()
    alerted_unknown: set = set()

    with patch.object(monitor, "query_active_sensors", return_value={"sensor/known", "sensor/event_driven"}), \
         patch.object(monitor, "push_notification") as mock_push:
        monitor.run_check(expected, excluded, alerted_missing, alerted_unknown)

    assert "sensor/event_driven" not in alerted_unknown
    mock_push.assert_not_called()


def test_run_check_unknown_alert_fires_once():
    expected = ["sensor/known"]
    excluded = set()
    alerted_missing: set = set()
    alerted_unknown: set = set()

    active = {"sensor/known", "sensor/new"}
    with patch.object(monitor, "query_active_sensors", return_value=active), \
         patch.object(monitor, "push_notification") as mock_push:
        monitor.run_check(expected, excluded, alerted_missing, alerted_unknown)
        assert mock_push.call_count == 1
        monitor.run_check(expected, excluded, alerted_missing, alerted_unknown)
        assert mock_push.call_count == 1


# --- run_check: DB failure ----------------------------------------------------


def test_run_check_db_error_does_not_crash():
    expected = ["sensor/a"]
    excluded = set()
    alerted_missing: set = set()
    alerted_unknown: set = set()

    with patch.object(monitor, "query_active_sensors", side_effect=Exception("connection refused")):
        monitor.run_check(expected, excluded, alerted_missing, alerted_unknown)  # must not raise


# --- push_notification --------------------------------------------------------


def test_push_notification_skipped_when_no_url():
    original = monitor.NTFY_URL
    monitor.NTFY_URL = ""
    try:
        with patch("urllib.request.urlopen") as mock_open:
            monitor.push_notification("test message")
        mock_open.assert_not_called()
    finally:
        monitor.NTFY_URL = original


def test_push_notification_sends_post():
    original = monitor.NTFY_URL
    monitor.NTFY_URL = "http://ntfy/test"
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=MagicMock(status=200))
    ctx.__exit__ = MagicMock(return_value=False)
    try:
        with patch("urllib.request.urlopen", return_value=ctx) as mock_open:
            monitor.push_notification("alert: sensor gone silent")
        mock_open.assert_called_once()
        req = mock_open.call_args[0][0]
        assert isinstance(req, urllib.request.Request)
        assert req.get_method() == "POST"
        assert b"sensor gone silent" in req.data
    finally:
        monitor.NTFY_URL = original


def test_push_notification_network_error_does_not_raise():
    original = monitor.NTFY_URL
    monitor.NTFY_URL = "http://ntfy/test"
    try:
        with patch("urllib.request.urlopen", side_effect=OSError("unreachable")):
            monitor.push_notification("test")  # must not raise
    finally:
        monitor.NTFY_URL = original
