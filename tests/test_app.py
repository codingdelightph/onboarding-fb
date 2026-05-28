import hashlib
import hmac
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


@pytest.fixture
def client():
    from app import app
    return TestClient(app)


@pytest.fixture
def bypass_sig(mocker):
    """Patch _verify_signature to True for tests that aren't testing signature logic."""
    mocker.patch("app._verify_signature", return_value=True)


def test_webhook_verify_missing_token_returns_403(client):
    params = {"hub.mode": "subscribe", "hub.verify_token": "", "hub.challenge": "abc123"}
    with patch("app.Config.VERIFY_TOKEN", ""):
        response = client.get("/webhook", params=params)
    assert response.status_code == 403


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


def test_webhook_post_text_message_calls_dispatch(client, mocker, bypass_sig):
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


def test_webhook_post_postback_calls_dispatch(client, mocker, bypass_sig):
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


def test_webhook_post_agent_resume_calls_dispatch(client, mocker, bypass_sig):
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


def test_webhook_post_non_page_object_ignored(client, mocker, bypass_sig):
    mock_dispatch = mocker.patch("app.flow.dispatch")
    payload = {"object": "user", "entry": []}
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    mock_dispatch.assert_not_called()


def test_webhook_post_wrong_app_id_does_not_dispatch(client, mocker, bypass_sig):
    mock_dispatch = mocker.patch("app.flow.dispatch")
    payload = {
        "object": "page",
        "entry": [{"messaging": [{
            "sender": {"id": "psid_000"},
            "pass_thread_control": {"previous_owner_app_id": "9999999999"},
        }]}]
    }
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    mock_dispatch.assert_not_called()


def test_webhook_post_message_without_text_does_not_dispatch(client, mocker, bypass_sig):
    mock_dispatch = mocker.patch("app.flow.dispatch")
    payload = {
        "object": "page",
        "entry": [{"messaging": [{
            "sender": {"id": "psid_111"},
            "message": {"attachments": [{"type": "image"}]},
        }]}]
    }
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    mock_dispatch.assert_not_called()


def test_webhook_post_bad_json_returns_400(client, bypass_sig):
    response = client.post("/webhook", content=b"not json", headers={"Content-Type": "application/json"})
    assert response.status_code == 400


def test_webhook_post_valid_signature_accepted(client, mocker):
    mocker.patch("app.flow.dispatch")
    secret = "test_secret"
    body = json.dumps({
        "object": "page",
        "entry": [{"messaging": [{"sender": {"id": "p1"}, "message": {"text": "hi"}}]}],
    }).encode()
    sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    with patch("app.Config.APP_SECRET", secret):
        response = client.post(
            "/webhook",
            content=body,
            headers={"Content-Type": "application/json", "X-Hub-Signature-256": sig},
        )
    assert response.status_code == 200


def test_webhook_post_invalid_signature_returns_403(client):
    secret = "test_secret"
    body = json.dumps({"object": "page", "entry": []}).encode()
    with patch("app.Config.APP_SECRET", secret):
        response = client.post(
            "/webhook",
            content=body,
            headers={"Content-Type": "application/json", "X-Hub-Signature-256": "sha256=bad"},
        )
    assert response.status_code == 403
