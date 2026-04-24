import schedule


def test_find_matching_schedule_monday_gen_z():
    result = schedule.find_schedule(
        age_group="Gen Z",
        marital_status="Young Adult",
        day="Monday",
        preferred_time="afternoon",
    )
    assert "John Doe" in result
    assert "Monday" in result
    assert "2:00 PM" in result


def test_find_matching_schedule_monday_millennials_married():
    result = schedule.find_schedule(
        age_group="Millennials",
        marital_status="Married",
        day="Monday",
        preferred_time="afternoon",
    )
    assert "Juan Sicat" in result


def test_find_matching_schedule_evening():
    result = schedule.find_schedule(
        age_group="Baby Boomer",
        marital_status="Married",
        day="Monday",
        preferred_time="evening",
    )
    assert "Pedro Dy" in result
    assert "6:30 PM" in result


def test_find_no_match_returns_empty_string():
    result = schedule.find_schedule(
        age_group="Gen Z",
        marital_status="Married",
        day="Monday",
        preferred_time="afternoon",
    )
    assert result == ""


def test_find_case_insensitive():
    result = schedule.find_schedule(
        age_group="gen z",
        marital_status="young adult",
        day="monday",
        preferred_time="afternoon",
    )
    assert "John Doe" in result
