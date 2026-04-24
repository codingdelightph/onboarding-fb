import pytest
from unittest.mock import patch, MagicMock
import facebook


PSID = "user_123"


def test_send_message_posts_correct_payload(mocker):
    mock_post = mocker.patch("facebook.requests.post")
    facebook.send_message(PSID, "Hello!")
    mock_post.assert_called_once()
    _, kwargs = mock_post.call_args
    body = kwargs["json"]
    assert body["recipient"]["id"] == PSID
    assert body["message"]["text"] == "Hello!"


def test_send_buttons_uses_button_template(mocker):
    mock_post = mocker.patch("facebook.requests.post")
    buttons = [{"type": "postback", "title": "Yes", "payload": "/yes"}]
    facebook.send_buttons(PSID, "Choose:", buttons)
    _, kwargs = mock_post.call_args
    body = kwargs["json"]
    template = body["message"]["attachment"]["payload"]
    assert template["template_type"] == "button"
    assert template["text"] == "Choose:"
    assert template["buttons"] == buttons


def test_fetch_user_name_returns_names(mocker):
    mock_get = mocker.patch("facebook.requests.get")
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "first_name": "Maria",
        "last_name": "Santos",
    }
    first, last = facebook.fetch_user_name(PSID)
    assert first == "Maria"
    assert last == "Santos"


def test_fetch_user_name_returns_empty_on_error(mocker):
    mock_get = mocker.patch("facebook.requests.get")
    mock_get.return_value.status_code = 400
    mock_get.return_value.json.return_value = {"error": "invalid token"}
    first, last = facebook.fetch_user_name(PSID)
    assert first == ""
    assert last == ""


def test_handoff_to_human_calls_pass_thread_control(mocker):
    mock_post = mocker.patch("facebook.requests.post")
    facebook.handoff_to_human(PSID)
    mock_post.assert_called_once()
    _, kwargs = mock_post.call_args
    body = kwargs["json"]
    assert body["recipient"]["id"] == PSID
    assert body["target_app_id"] == "3374491019519787"
