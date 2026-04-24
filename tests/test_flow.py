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


# ── invite ───────────────────────────────────────────────────────────────────

def test_will_join_sends_age_group_buttons(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="invite")
    flow.dispatch(PSID, "/will_join")
    assert state.get(PSID)["step"] == "age_group"


def test_not_joining_sends_farewell_and_done(mocker):
    mocker.patch("flow.facebook.send_message")
    state.update(PSID, step="invite")
    flow.dispatch(PSID, "/not_joining")
    assert state.get(PSID)["step"] == "done"


def test_invite_request_handoff_triggers_handoff(mocker):
    mocker.patch("flow.facebook.send_message")
    mocker.patch("flow.facebook.handoff_to_human")
    state.update(PSID, step="invite")
    flow.dispatch(PSID, "/request_handoff")
    assert state.get(PSID)["step"] == "paused"


# ── age_group ────────────────────────────────────────────────────────────────

def test_younger_group_sends_life_stage_young_buttons(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="age_group")
    flow.dispatch(PSID, "/younger_group")
    assert state.get(PSID)["step"] == "life_stage_young"


def test_older_group_sends_generation_buttons(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="age_group")
    flow.dispatch(PSID, "/older_group")
    assert state.get(PSID)["step"] == "generation_old"


# ── life_stage_young ─────────────────────────────────────────────────────────

def test_elevate_b1g_sends_sub_buttons(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="life_stage_young")
    flow.dispatch(PSID, "/elevate_B1G")
    assert state.get(PSID)["step"] == "elevate_b1g"


def test_younger_married_sets_millennials_married_and_asks_day(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="life_stage_young")
    flow.dispatch(PSID, "/married")
    user = state.get(PSID)
    assert user["age_group"] == "Millennials"
    assert user["marital_status"] == "Married"
    assert user["step"] == "availability_group"


def test_solo_parent_sets_state_and_asks_gender(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="life_stage_young")
    flow.dispatch(PSID, "/solo_parent")
    user = state.get(PSID)
    assert user["marital_status"] == "Solo Parent"
    assert user["age_group"] == "Gen X"
    assert user["step"] == "gender"


# ── elevate_b1g ──────────────────────────────────────────────────────────────

def test_elevate_sets_gen_z_young_adult_and_asks_gender(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="elevate_b1g")
    flow.dispatch(PSID, "/elevate")
    user = state.get(PSID)
    assert user["age_group"] == "Gen Z"
    assert user["marital_status"] == "Young Adult"
    assert user["step"] == "gender"


def test_young_professionals_sets_millennials_and_asks_gender(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="elevate_b1g")
    flow.dispatch(PSID, "/young_professionals")
    user = state.get(PSID)
    assert user["age_group"] == "Millennials"
    assert user["marital_status"] == "Young Adult"
    assert user["step"] == "gender"


# ── gender ───────────────────────────────────────────────────────────────────

def test_gender_male_stores_and_asks_availability(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="gender")
    flow.dispatch(PSID, "/male")
    assert state.get(PSID)["gender"] == "male"
    assert state.get(PSID)["step"] == "availability_group"


def test_gender_female_stores_and_asks_availability(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="gender")
    flow.dispatch(PSID, "/female")
    assert state.get(PSID)["gender"] == "female"
    assert state.get(PSID)["step"] == "availability_group"


def test_unknown_gender_resends_gender_buttons(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="gender")
    flow.dispatch(PSID, "/something")
    assert state.get(PSID)["step"] == "gender"


# ── generation_old ───────────────────────────────────────────────────────────

def test_gen_x_sets_age_group_and_asks_life_stage(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="generation_old")
    flow.dispatch(PSID, "/gen_x")
    user = state.get(PSID)
    assert user["age_group"] == "Gen X"
    assert user["step"] == "life_stage_old"


def test_baby_boomers_sets_age_group_and_asks_life_stage(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="generation_old")
    flow.dispatch(PSID, "/baby_boomers")
    user = state.get(PSID)
    assert user["age_group"] == "Baby Boomers"
    assert user["step"] == "life_stage_old"


# ── life_stage_old ───────────────────────────────────────────────────────────

def test_older_married_sets_marital_and_asks_day(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="life_stage_old", age_group="Gen X")
    flow.dispatch(PSID, "/married")
    user = state.get(PSID)
    assert user["marital_status"] == "Married"
    assert user["step"] == "availability_group"


def test_older_single_sets_marital_and_asks_day(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="life_stage_old", age_group="Baby Boomers")
    flow.dispatch(PSID, "/single")
    user = state.get(PSID)
    assert user["marital_status"] == "Single"
    assert user["step"] == "availability_group"


def test_older_widowed_sets_marital_and_asks_day(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="life_stage_old", age_group="Gen X")
    flow.dispatch(PSID, "/widowed")
    user = state.get(PSID)
    assert user["marital_status"] == "Widowed"
    assert user["step"] == "availability_group"


# ── availability_group ───────────────────────────────────────────────────────

def test_mwf_sends_mwf_day_buttons(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="availability_group")
    flow.dispatch(PSID, "/mwf")
    assert state.get(PSID)["step"] == "availability_mwf"


def test_tth_sends_tth_day_buttons(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="availability_group")
    flow.dispatch(PSID, "/tth")
    assert state.get(PSID)["step"] == "availability_tth"


def test_weekend_sends_weekend_day_buttons(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="availability_group")
    flow.dispatch(PSID, "/weekend")
    assert state.get(PSID)["step"] == "availability_weekend"


# ── availability_mwf / tth / weekend ────────────────────────────────────────

def test_monday_sets_day_and_asks_time(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="availability_mwf")
    flow.dispatch(PSID, "/monday")
    user = state.get(PSID)
    assert user["availability_day"] == "Monday"
    assert user["step"] == "preferred_time"


def test_thursday_sets_day_and_asks_time(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="availability_tth")
    flow.dispatch(PSID, "/thursday")
    user = state.get(PSID)
    assert user["availability_day"] == "Thursday"
    assert user["step"] == "preferred_time"


def test_saturday_sets_day_and_asks_time(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="availability_weekend")
    flow.dispatch(PSID, "/saturday")
    user = state.get(PSID)
    assert user["availability_day"] == "Saturday"
    assert user["step"] == "preferred_time"


# ── invalid payload fallbacks for Task 7 handlers ────────────────────────────

def test_invalid_generation_old_resends_buttons(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="generation_old")
    flow.dispatch(PSID, "/nonsense")
    assert state.get(PSID)["step"] == "generation_old"


def test_invalid_life_stage_old_resends_buttons(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="life_stage_old")
    flow.dispatch(PSID, "/nonsense")
    assert state.get(PSID)["step"] == "life_stage_old"


def test_invalid_availability_group_resends_buttons(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="availability_group")
    flow.dispatch(PSID, "/nonsense")
    assert state.get(PSID)["step"] == "availability_group"


def test_invalid_availability_mwf_resends_buttons(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="availability_mwf")
    flow.dispatch(PSID, "/nonsense")
    assert state.get(PSID)["step"] == "availability_mwf"


def test_invalid_availability_tth_resends_buttons(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="availability_tth")
    flow.dispatch(PSID, "/nonsense")
    assert state.get(PSID)["step"] == "availability_tth"


def test_invalid_availability_weekend_resends_buttons(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="availability_weekend")
    flow.dispatch(PSID, "/nonsense")
    assert state.get(PSID)["step"] == "availability_weekend"
