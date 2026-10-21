"""Offline regressions for framework failures found during review."""

import importlib.util
import json
import logging
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests

from src.base.api_base import APIBase
from src.base.web_base import WebBase
from src.utils.logger import get_logger

spec = importlib.util.spec_from_file_location(
    "project_fixtures", Path(__file__).resolve().parents[2] / "conftest.py"
)
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)

pytestmark = pytest.mark.unit


@pytest.fixture
def client():
    instance = APIBase(
        {
            "base_api_url": "https://example.invalid",
            "api_auth_endpoint": "/auth",
            "credentials": {"api_user": {"username": "admin", "password": "secret"}},
        }
    )
    yield instance
    instance.session.close()


def test_failed_authentication_blocks_protected_request(client, monkeypatch):
    response = requests.Response()
    response.status_code = 200
    response._content = b'{"reason":"Bad credentials"}'
    monkeypatch.setattr(client.session, "post", lambda *args, **kwargs: response)

    def unexpected_request(*args, **kwargs):
        pytest.fail("Protected request was sent after failed authentication")

    monkeypatch.setattr(client.session, "request", unexpected_request)
    with pytest.raises(requests.exceptions.RequestException, match="Authentication failed"):
        client.delete("/booking/1")


def test_failed_reauthentication_discards_old_token(client, monkeypatch):
    client.auth_token = "old-token"

    def timeout(*args, **kwargs):
        raise requests.Timeout("server unavailable")

    monkeypatch.setattr(client.session, "post", timeout)
    assert client.authenticate() is False
    assert client.auth_token is None


@pytest.mark.parametrize("body", [b"[]", b"null", b'{"token":123}', b'{"token":""}'])
def test_malformed_authentication_response_is_rejected(client, monkeypatch, body):
    response = requests.Response()
    response.status_code = 200
    response._content = body
    monkeypatch.setattr(client.session, "post", lambda *args, **kwargs: response)
    assert client.authenticate() is False
    assert client.auth_token is None


def test_typing_does_not_log_password(monkeypatch):
    messages = []
    monkeypatch.setattr("src.base.web_base.logger.info", lambda message: messages.append(message))
    page = WebBase(Mock(), {})
    monkeypatch.setattr(page, "_find_element", lambda *args: Mock())
    page._type(("id", "password"), "private-password")
    assert "private-password" not in "\n".join(messages)


def test_invalid_log_level_falls_back_to_info():
    logger = get_logger("unit.invalid-level", level="NOT_A_LEVEL")
    assert logger.level == logging.INFO
    assert logger.handlers[0].level == logging.INFO


def test_driver_is_closed_when_window_setup_fails(monkeypatch):
    driver = Mock()
    driver.maximize_window.side_effect = RuntimeError("window setup failed")
    monkeypatch.setattr(fixtures.DriverFactory, "get_driver", lambda *args: driver)
    fixture = fixtures.web_driver.__wrapped__({})
    with pytest.raises(Exception, match="window setup failed"):
        next(fixture)
    driver.quit.assert_called_once()


def test_config_loads_from_repository_when_working_directory_changes(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TEST_ENV", "dev")
    assert fixtures.config.__wrapped__()["base_api_url"] == "https://restful-booker.herokuapp.com"


def test_invalid_config_is_not_silently_ignored(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{invalid", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        fixtures.load_config_file(path)
