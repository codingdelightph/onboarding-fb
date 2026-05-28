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
    assert user["age_group"] == "Baby Boomer"
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


# ── preferred_time ───────────────────────────────────────────────────────────

def test_afternoon_shows_schedule_and_asks_mobile(mocker):
    mocker.patch("flow.schedule.find_schedule", return_value="Group on Monday led by John.")
    mocker.patch("flow.facebook.send_message")
    mocker.patch("flow.facebook.send_buttons")
    state.update(
        PSID,
        step="preferred_time",
        age_group="Gen Z",
        marital_status="Young Adult",
        availability_day="Monday",
    )
    flow.dispatch(PSID, "/afternoon")
    assert state.get(PSID)["preferred_time"] == "afternoon"
    assert state.get(PSID)["step"] == "mobile_prompt"
    flow.facebook.send_message.assert_called_with(PSID, "Group on Monday led by John.")


def test_no_schedule_found_sends_sorry_message(mocker):
    mocker.patch("flow.schedule.find_schedule", return_value="")
    mocker.patch("flow.facebook.send_message")
    mocker.patch("flow.facebook.send_buttons")
    state.update(
        PSID,
        step="preferred_time",
        age_group="Gen Z",
        marital_status="Widowed",
        availability_day="Monday",
    )
    flow.dispatch(PSID, "/evening")
    flow.facebook.send_message.assert_called_with(
        PSID,
        "Sorry, I couldn't find a schedule matching your profile. "
        "A team member will follow up with you.",
    )


# ── mobile_prompt ─────────────────────────────────────────────────────────────

def test_provide_mobile_asks_for_number(mocker):
    mocker.patch("flow.facebook.send_message")
    state.update(PSID, step="mobile_prompt")
    flow.dispatch(PSID, "/provide_mobile")
    assert state.get(PSID)["step"] == "collect_mobile"
    flow.facebook.send_message.assert_called_once()


def test_not_ready_goes_to_wind_down(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="mobile_prompt")
    flow.dispatch(PSID, "/not_ready_to_share")
    assert state.get(PSID)["step"] == "wind_down"


# ── collect_mobile ────────────────────────────────────────────────────────────

def test_valid_mobile_stores_number_and_shows_summary(mocker):
    mocker.patch("flow.facebook.send_message")
    mocker.patch("flow.facebook.send_buttons")
    state.update(
        PSID,
        step="collect_mobile",
        first_name="Juan",
        last_name="Cruz",
        age_group="Gen Z",
        availability_day="Monday",
        preferred_time="afternoon",
        marital_status="Young Adult",
    )
    flow.dispatch(PSID, "09171234567")
    assert state.get(PSID)["mobile_number"] == "09171234567"
    assert state.get(PSID)["step"] == "wind_down"
    flow.facebook.send_message.assert_called_once()


def test_valid_international_mobile_stored(mocker):
    mocker.patch("flow.facebook.send_message")
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="collect_mobile", first_name="M", last_name="S",
                 age_group="Gen Z", availability_day="Monday",
                 preferred_time="afternoon", marital_status="Young Adult")
    flow.dispatch(PSID, "+639171234567")
    assert state.get(PSID)["mobile_number"] == "+639171234567"


def test_invalid_mobile_sends_error_and_stays(mocker):
    mocker.patch("flow.facebook.send_message")
    state.update(PSID, step="collect_mobile")
    flow.dispatch(PSID, "not-a-number")
    assert state.get(PSID)["step"] == "collect_mobile"
    flow.facebook.send_message.assert_called_with(
        PSID,
        "Please send a valid PH mobile number (e.g. 09171234567).",
    )


# ── wind_down ─────────────────────────────────────────────────────────────────

def test_wind_down_get_started_confirms_and_hands_off(mocker):
    mocker.patch("flow.facebook.send_message")
    mocker.patch("flow.facebook.handoff_to_human")
    state.update(PSID, step="wind_down", first_name="Juan", mobile_number="09171234567")
    flow.dispatch(PSID, "/get_started")
    user = state.get(PSID)
    assert user["step"] == "paused"


def test_wind_down_im_good_sends_farewell(mocker):
    mocker.patch("flow.facebook.send_message")
    state.update(PSID, step="wind_down")
    flow.dispatch(PSID, "/wind_down")
    assert state.get(PSID)["step"] == "done"
    flow.facebook.send_message.assert_called_once()


def test_wind_down_revert_seeker_sends_followup(mocker):
    mocker.patch("flow.facebook.send_message")
    state.update(PSID, step="wind_down")
    flow.dispatch(PSID, "/revert_seeker")
    assert state.get(PSID)["step"] == "done"
    flow.facebook.send_message.assert_called_once()


def test_paused_agent_resume_resumes_to_membership(mocker):
    mocker.patch("flow.facebook.send_message")
    state.update(PSID, step="paused")
    flow.dispatch(PSID, "agent_resume")
    assert state.get(PSID)["step"] == "membership"


def test_paused_user_message_sends_wait_notice(mocker):
    mocker.patch("flow.facebook.send_message")
    state.update(PSID, step="paused")
    flow.dispatch(PSID, "hello")
    assert state.get(PSID)["step"] == "paused"
    flow.facebook.send_message.assert_called_once_with(
        PSID, "Please wait — a team member will be with you shortly."
    )


def test_invalid_preferred_time_resends_time_buttons(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="preferred_time")
    flow.dispatch(PSID, "/nonsense")
    assert state.get(PSID)["step"] == "preferred_time"


def test_invalid_mobile_prompt_resends_buttons(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="mobile_prompt")
    flow.dispatch(PSID, "/nonsense")
    assert state.get(PSID)["step"] == "mobile_prompt"
