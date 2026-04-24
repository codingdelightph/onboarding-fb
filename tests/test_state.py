import state


def test_new_psid_returns_default_state():
    user = state.get("psid_1")
    assert user["step"] == "start"
    assert user["first_name"] == ""
    assert user["mobile_number"] == ""


def test_update_sets_fields():
    state.update("psid_2", step="privacy", first_name="Juan")
    user = state.get("psid_2")
    assert user["step"] == "privacy"
    assert user["first_name"] == "Juan"


def test_update_preserves_other_fields():
    state.update("psid_3", first_name="Maria")
    state.update("psid_3", step="membership")
    user = state.get("psid_3")
    assert user["first_name"] == "Maria"
    assert user["step"] == "membership"


def test_reset_clears_all_fields():
    state.update("psid_4", step="membership", first_name="Pedro", mobile_number="09171234567")
    state.reset("psid_4")
    user = state.get("psid_4")
    assert user["step"] == "start"
    assert user["first_name"] == ""
    assert user["mobile_number"] == ""


def test_get_returns_same_object():
    user1 = state.get("psid_5")
    user2 = state.get("psid_5")
    assert user1 is user2
