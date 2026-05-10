import time
from unittest.mock import MagicMock, patch

from mqttlogger.heartbeat import start_heartbeat


def _ctx_mock(status=200):
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=MagicMock(status=status))
    ctx.__exit__ = MagicMock(return_value=False)
    return ctx


def test_returns_daemon_thread():
    with patch("urllib.request.urlopen", return_value=_ctx_mock()):
        t = start_heartbeat("http://example.com/ping", interval=3600)
    assert t.daemon is True
    assert t.name == "heartbeat"
    assert t.is_alive()


def test_first_push_fires_immediately():
    with patch("urllib.request.urlopen", return_value=_ctx_mock()) as mock_open:
        start_heartbeat("http://example.com/ping", interval=3600)
        time.sleep(0.15)
    mock_open.assert_called()
    call_url = mock_open.call_args[0][0]
    assert "example.com" in call_url


def test_failed_push_does_not_kill_thread():
    with patch("urllib.request.urlopen", side_effect=OSError("unreachable")):
        t = start_heartbeat("http://example.com/ping", interval=3600)
        time.sleep(0.15)
    assert t.is_alive()
