import pytest
import state
import flow


PSID = "psid_flow_test"


# ── start ──────────────────────────────────────────────────────────────────

def test_dispatch_any_message_at_start_sends_privacy_buttons(mocker):
    mocker.patch("flow.facebook.send_buttons")
    flow.dispatch(PSID, "hello")
    flow.facebook.send_buttons.assert_called_once()
    text_arg = flow.facebook.send_buttons.call_args[0][1]
    assert "privacy policy" in text_arg.lower()
    assert state.get(PSID)["step"] == "privacy"


def test_dispatch_get_started_at_start_sends_privacy_buttons(mocker):
    mocker.patch("flow.facebook.send_buttons")
    flow.dispatch(PSID, "GET_STARTED")
    flow.facebook.send_buttons.assert_called_once()
    assert state.get(PSID)["step"] == "privacy"


# ── privacy ─────────────────────────────────────────────────────────────────

def test_accept_privacy_policy_greets_and_asks_membership(mocker):
    mocker.patch("flow.facebook.fetch_user_name", return_value=("Juan", "dela Cruz"))
    mocker.patch("flow.facebook.send_message")
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="privacy")
    flow.dispatch(PSID, "/accept_privacy_policy")
    assert state.get(PSID)["first_name"] == "Juan"
    assert state.get(PSID)["last_name"] == "dela Cruz"
    assert state.get(PSID)["step"] == "membership"
    flow.facebook.send_message.assert_called_once()


def test_wrong_payload_at_privacy_resends_privacy_buttons(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="privacy")
    flow.dispatch(PSID, "/something_else")
    assert state.get(PSID)["step"] == "privacy"


# ── membership ──────────────────────────────────────────────────────────────

def test_member_sends_confirmation_and_done(mocker):
    mocker.patch("flow.facebook.send_message")
    state.update(PSID, step="membership", first_name="Juan", last_name="Cruz")
    flow.dispatch(PSID, "/member")
    assert state.get(PSID)["step"] == "done"
    flow.facebook.send_message.assert_called_once()


def test_not_member_sends_invite_buttons(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="membership", first_name="Juan", last_name="Cruz")
    flow.dispatch(PSID, "/not_member")
    assert state.get(PSID)["step"] == "invite"
    flow.facebook.send_buttons.assert_called_once()
