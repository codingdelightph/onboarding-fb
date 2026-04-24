from typing import Any

_states: dict[str, dict[str, Any]] = {}


def _default_state() -> dict[str, Any]:
    return {
        "step": "start",
        "first_name": "",
        "last_name": "",
        "age_group": "",
        "life_stage": "",
        "marital_status": "",
        "gender": "",
        "availability_day": "",
        "preferred_time": "",
        "mobile_number": "",
    }


def get(psid: str) -> dict[str, Any]:
    if psid not in _states:
        _states[psid] = _default_state()
    return _states[psid]


def update(psid: str, **kwargs: Any) -> None:
    get(psid).update(kwargs)


def reset(psid: str) -> None:
    _states[psid] = _default_state()
