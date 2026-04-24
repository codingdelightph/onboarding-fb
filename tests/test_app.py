import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import state


@pytest.fixture
def client():
    from app import app
    return TestClient(app)


def test_webhook_verify_returns_challenge(client):
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "test_token",
        "hub.challenge": "abc123",
    }
    with patch("app.Config.VERIFY_TOKEN", "test_token"):
        response = client.get("/webhook", params=params)
    assert response.status_code == 200
    assert response.text == "abc123"


def test_webhook_verify_wrong_token_returns_403(client):
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "wrong_token",
        "hub.challenge": "abc123",
    }
    with patch("app.Config.VERIFY_TOKEN", "test_token"):
        response = client.get("/webhook", params=params)
    assert response.status_code == 403


def test_webhook_post_text_message_calls_dispatch(client, mocker):
    mock_dispatch = mocker.patch("app.flow.dispatch")
    payload = {
        "object": "page",
        "entry": [{
            "messaging": [{
                "sender": {"id": "psid_123"},
                "message": {"text": "hello"},
            }]
        }]
    }
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    mock_dispatch.assert_called_once_with("psid_123", "hello")


def test_webhook_post_postback_calls_dispatch(client, mocker):
    mock_dispatch = mocker.patch("app.flow.dispatch")
    payload = {
        "object": "page",
        "entry": [{
            "messaging": [{
                "sender": {"id": "psid_456"},
                "postback": {"payload": "/accept_privacy_policy"},
            }]
        }]
    }
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    mock_dispatch.assert_called_once_with("psid_456", "/accept_privacy_policy")


def test_webhook_post_agent_resume_calls_dispatch(client, mocker):
    mock_dispatch = mocker.patch("app.flow.dispatch")
    payload = {
        "object": "page",
        "entry": [{
            "messaging": [{
                "sender": {"id": "psid_789"},
                "pass_thread_control": {
                    "previous_owner_app_id": "3374491019519787",
                },
            }]
        }]
    }
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    mock_dispatch.assert_called_once_with("psid_789", "agent_resume")


def test_webhook_post_non_page_object_ignored(client, mocker):
    mock_dispatch = mocker.patch("app.flow.dispatch")
    payload = {"object": "user", "entry": []}
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    mock_dispatch.assert_not_called()
