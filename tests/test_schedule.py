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


def test_baby_boomer_age_group_matches_csv_spelling():
    """Regression: flow.py must store 'Baby Boomer' (singular) to match CSV."""
    result = schedule.find_schedule(
        age_group="Baby Boomer",
        marital_status="Married",
        day="Monday",
        preferred_time="evening",
    )
    assert result != "", "Baby Boomer (singular) must resolve to a schedule"
    # Plural form must NOT match
    result_plural = schedule.find_schedule(
        age_group="Baby Boomers",
        marital_status="Married",
        day="Monday",
        preferred_time="evening",
    )
    assert result_plural == "", "Baby Boomers (plural) should not match any CSV row"
