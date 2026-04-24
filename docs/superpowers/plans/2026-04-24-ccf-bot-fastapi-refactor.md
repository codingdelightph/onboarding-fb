# CCF Imus D-Group Onboarding Bot — FastAPI Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Rasa + TensorFlow bot with a minimal FastAPI app using a step-handler state machine, keeping the exact same Facebook Messenger conversation flow.

**Architecture:** FastAPI webhook receives FB messages/postbacks and calls `flow.dispatch()`. Each conversation step is a small isolated handler function stored in a `HANDLERS` dict. Per-user state is an in-memory dict keyed by Facebook PSID. All outbound FB API calls go through `facebook.py`.

**Tech Stack:** Python 3.11, FastAPI, Uvicorn, pandas (CSV reads), requests (FB Graph API), python-dotenv, pytest, pytest-mock, httpx (TestClient)

---

## File Map

| File | Status | Responsibility |
|---|---|---|
| `requirements.txt` | Modify | Add pytest, pytest-mock, httpx |
| `.env.example` | Create | Document required env vars |
| `pytest.ini` | Create | Test configuration |
| `tests/__init__.py` | Create | Test package marker |
| `tests/conftest.py` | Create | Clear state between tests |
| `config.py` | Rewrite | All settings from `.env`, absolute data paths |
| `state.py` | Rewrite | `get()`, `update()`, `reset()`, `_default_state()` |
| `schedule.py` | Create (replaces `utils/schedule.py`) | CSV load + `find_schedule()` |
| `facebook.py` | Modify | Add `fetch_user_name()`, keep existing sends |
| `flow.py` | Create | `HANDLERS` dict + all step handler functions + `dispatch()` |
| `app.py` | Rewrite | Webhook GET verify + POST parse + call `flow.dispatch()` |
| `utils/` | Delete | Replaced by `schedule.py` at root |

---

## Task 1: Project Setup

**Files:**
- Modify: `requirements.txt`
- Create: `.env.example`
- Create: `pytest.ini`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Update requirements.txt**

```
fastapi
uvicorn[standard]
python-dotenv
pandas
requests
python-multipart
pytest
pytest-mock
httpx
```

- [ ] **Step 2: Create `.env.example`**

```
PAGE_ACCESS_TOKEN=your_fb_page_access_token_here
VERIFY_TOKEN=your_chosen_verify_token_here
CCF_SATELLITE=Imus
```

- [ ] **Step 3: Create `pytest.ini`**

```ini
[pytest]
testpaths = tests
```

- [ ] **Step 4: Create `tests/__init__.py`**

Empty file — marks `tests/` as a Python package.

- [ ] **Step 5: Create `tests/conftest.py`**

```python
import pytest
import state

@pytest.fixture(autouse=True)
def clear_state():
    state._states.clear()
    yield
    state._states.clear()
```

- [ ] **Step 6: Install dependencies and verify**

```bash
cd /Users/dennisnunez/workspace/claudework/cb-onboarding-refactored
pip install -r requirements.txt
pytest --collect-only
```

Expected: `no tests ran` (no test files yet — that's fine)

- [ ] **Step 7: Commit**

```bash
git init  # if not already a git repo
git add requirements.txt .env.example pytest.ini tests/
git commit -m "chore: project setup for FastAPI refactor"
```

---

## Task 2: config.py and state.py

**Files:**
- Rewrite: `config.py`
- Create: `tests/test_state.py`
- Rewrite: `state.py`

- [ ] **Step 1: Write failing tests for state**

Create `tests/test_state.py`:

```python
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
```

- [ ] **Step 2: Run tests — expect failure**

```bash
pytest tests/test_state.py -v
```

Expected: `ImportError` or `AttributeError` — state.py is not yet correct.

- [ ] **Step 3: Rewrite `config.py`**

```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

_BASE = Path(__file__).parent


class Config:
    PAGE_ACCESS_TOKEN: str = os.getenv("PAGE_ACCESS_TOKEN", "")
    VERIFY_TOKEN: str = os.getenv("VERIFY_TOKEN", "")
    CCF_SATELLITE: str = os.getenv("CCF_SATELLITE", "Imus")
    PAGE_INBOX_APP_ID: str = "3374491019519787"

    DGROUP_SCHEDULE: str = str(_BASE / "data" / "imus_dgroup_schedule.csv")
    LIFESTAGE: str = str(_BASE / "data" / "imus_lifestage.csv")
    SCHEDULE_OPTIONS: str = str(_BASE / "data" / "schedule_options.csv")
```

- [ ] **Step 4: Rewrite `state.py`**

```python
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
```

- [ ] **Step 5: Run tests — expect pass**

```bash
pytest tests/test_state.py -v
```

Expected:
```
test_state.py::test_new_psid_returns_default_state PASSED
test_state.py::test_update_sets_fields PASSED
test_state.py::test_update_preserves_other_fields PASSED
test_state.py::test_reset_clears_all_fields PASSED
test_state.py::test_get_returns_same_object PASSED
5 passed
```

- [ ] **Step 6: Commit**

```bash
git add config.py state.py tests/test_state.py
git commit -m "feat: config and state management"
```

---

## Task 3: schedule.py

**Files:**
- Create: `schedule.py`
- Create: `tests/test_schedule.py`
- Delete: `utils/schedule.py` and `utils/` directory

- [ ] **Step 1: Write failing tests**

Create `tests/test_schedule.py`:

```python
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
```

- [ ] **Step 2: Run tests — expect failure**

```bash
pytest tests/test_schedule.py -v
```

Expected: `ModuleNotFoundError: No module named 'schedule'`

- [ ] **Step 3: Create `schedule.py`**

```python
import pandas as pd
from config import Config


def load_schedule() -> pd.DataFrame:
    return pd.read_csv(Config.DGROUP_SCHEDULE)


def find_schedule(
    age_group: str,
    marital_status: str,
    day: str,
    preferred_time: str,
) -> str:
    """Return a schedule description string, or empty string if not found."""
    df = load_schedule()
    df = df[df["satellite"].str.lower() == Config.CCF_SATELLITE.lower()]
    df = df[df["day"].str.lower() == day.lower()]
    df = df[df["age_group"].str.lower() == age_group.lower()]
    df = df[df["marital_status"].str.lower() == marital_status.lower()]

    if df.empty:
        return ""

    row = df.iloc[0]
    return (
        f"The group on {row['day']} for {row['age_group']} ({row['marital_status']}) "
        f"is led by {row['leader']} and runs from {row['start_time']} to {row['end_time']}."
    )
```

- [ ] **Step 4: Run tests — expect pass**

```bash
pytest tests/test_schedule.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Delete the old utils directory**

```bash
rm -rf utils/
```

- [ ] **Step 6: Commit**

```bash
git add schedule.py tests/test_schedule.py
git rm -r utils/
git commit -m "feat: schedule CSV lookup, remove utils/"
```

---

## Task 4: facebook.py

**Files:**
- Modify: `facebook.py`
- Create: `tests/test_facebook.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_facebook.py`:

```python
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
```

- [ ] **Step 2: Run tests — expect failure**

```bash
pytest tests/test_facebook.py -v
```

Expected: Several failures — `fetch_user_name` does not exist yet.

- [ ] **Step 3: Rewrite `facebook.py`**

```python
import requests
from config import Config

_BASE_URL = f"https://graph.facebook.com/v21.0"


def _messages_url() -> str:
    return f"{_BASE_URL}/me/messages?access_token={Config.PAGE_ACCESS_TOKEN}"


def send_message(psid: str, text: str) -> None:
    requests.post(_messages_url(), json={
        "recipient": {"id": psid},
        "message": {"text": text},
    })


def send_buttons(psid: str, text: str, buttons: list) -> None:
    requests.post(_messages_url(), json={
        "recipient": {"id": psid},
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "button",
                    "text": text,
                    "buttons": buttons,
                },
            }
        },
    })


def send_carousel(psid: str, elements: list) -> None:
    requests.post(_messages_url(), json={
        "recipient": {"id": psid},
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": elements,
                },
            }
        },
    })


def fetch_user_name(psid: str) -> tuple[str, str]:
    url = (
        f"{_BASE_URL}/{psid}"
        f"?fields=first_name,last_name"
        f"&access_token={Config.PAGE_ACCESS_TOKEN}"
    )
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get("first_name", ""), data.get("last_name", "")
    return "", ""


def handoff_to_human(psid: str) -> None:
    url = f"{_BASE_URL}/me/pass_thread_control?access_token={Config.PAGE_ACCESS_TOKEN}"
    requests.post(url, json={
        "recipient": {"id": psid},
        "target_app_id": Config.PAGE_INBOX_APP_ID,
        "metadata": "Handoff to human agent",
    })
```

- [ ] **Step 4: Run tests — expect pass**

```bash
pytest tests/test_facebook.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add facebook.py tests/test_facebook.py
git commit -m "feat: facebook API helpers with fetch_user_name"
```

---

## Task 5: flow.py — Dispatcher + start / privacy / membership

**Files:**
- Create: `flow.py`
- Create: `tests/test_flow.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_flow.py`:

```python
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
```

- [ ] **Step 2: Run tests — expect failure**

```bash
pytest tests/test_flow.py -v
```

Expected: `ModuleNotFoundError: No module named 'flow'`

- [ ] **Step 3: Create `flow.py` with dispatcher, helpers, and first three handlers**

```python
from typing import Callable
import facebook
import state
from config import Config


# ── helpers ─────────────────────────────────────────────────────────────────

def _normalize(payload: str) -> str:
    """Strip leading slash and lowercase for consistent matching."""
    return payload.lstrip("/").lower()


def _ask_availability_group(psid: str) -> None:
    facebook.send_buttons(
        psid,
        "Which day works for you?",
        [
            {"type": "postback", "title": "📅 M-W-F", "payload": "/mwf"},
            {"type": "postback", "title": "📅 T-Th", "payload": "/tth"},
            {"type": "postback", "title": "🌅 Weekend", "payload": "/weekend"},
        ],
    )
    state.update(psid, step="availability_group")


def _ask_gender(psid: str) -> None:
    facebook.send_buttons(
        psid,
        "To match you with the right group, could you let me know your gender?",
        [
            {"type": "postback", "title": "👨 Male", "payload": "/male"},
            {"type": "postback", "title": "👩 Female", "payload": "/female"},
        ],
    )
    state.update(psid, step="gender")


def _ask_preferred_time(psid: str) -> None:
    facebook.send_buttons(
        psid,
        "Do you prefer afternoon or evening sessions?",
        [
            {"type": "postback", "title": "Afternoon", "payload": "/afternoon"},
            {"type": "postback", "title": "Evening", "payload": "/evening"},
            {"type": "postback", "title": "Specific Hours", "payload": "/specific_hours"},
        ],
    )
    state.update(psid, step="preferred_time")


def _show_wind_down(psid: str) -> None:
    facebook.send_buttons(
        psid,
        "Anything else?",
        [
            {"type": "postback", "title": "Place me now", "payload": "/get_started"},
            {"type": "postback", "title": "Get back soon", "payload": "/revert_seeker"},
            {"type": "postback", "title": "I'm good", "payload": "/wind_down"},
        ],
    )
    state.update(psid, step="wind_down")


# ── handlers ────────────────────────────────────────────────────────────────

def handle_start(psid: str, payload: str) -> None:
    facebook.send_buttons(
        psid,
        "Tap Accept if you agree to our privacy policy and the terms stated in the link below.",
        [
            {"type": "postback", "title": "✅ Accept", "payload": "/accept_privacy_policy"},
            {
                "type": "web_url",
                "title": "📄 Privacy Policy",
                "url": "https://www.nxtaigen.com/cb-onboarding-policy.html",
            },
        ],
    )
    state.update(psid, step="privacy")


def handle_privacy(psid: str, payload: str) -> None:
    if payload != "accept_privacy_policy":
        handle_start(psid, payload)
        return
    first_name, last_name = facebook.fetch_user_name(psid)
    state.update(psid, first_name=first_name, last_name=last_name)
    facebook.send_message(psid, "Thank you for accepting our privacy policy! Let's get started.")
    facebook.send_buttons(
        psid,
        f"Welcome {first_name} to CCF {Config.CCF_SATELLITE}! Are you a member of a D-Group?",
        [
            {"type": "postback", "title": "Member", "payload": "/member"},
            {"type": "postback", "title": "Not yet a member", "payload": "/not_member"},
        ],
    )
    state.update(psid, step="membership")


def handle_membership(psid: str, payload: str) -> None:
    if payload == "member":
        facebook.send_message(psid, "That's great! How can I assist you further with your D-Group?")
        state.update(psid, step="done")
    elif payload == "not_member":
        user = state.get(psid)
        facebook.send_buttons(
            psid,
            (
                f"Welcome {user['first_name']} {user['last_name']} to CCF {Config.CCF_SATELLITE}! "
                "It seems you're not part of a D-Group yet. Would you like to join one?"
            ),
            [
                {"type": "postback", "title": "✅ I want to join", "payload": "/will_join"},
                {"type": "postback", "title": "⏳ I need more time", "payload": "/not_joining"},
                {"type": "postback", "title": "📞 Talk to a person", "payload": "/request_handoff"},
            ],
        )
        state.update(psid, step="invite")
    else:
        handle_privacy(psid, "accept_privacy_policy")


def handle_done(psid: str, payload: str) -> None:
    # Not registered in HANDLERS — any new message after "done" falls back to
    # the default handle_start, restarting the conversation from scratch.
    pass


def handle_handoff(psid: str, payload: str) -> None:
    facebook.send_message(psid, "Please wait while we connect you to someone who can help.")
    facebook.handoff_to_human(psid)
    state.update(psid, step="paused")


def handle_paused(psid: str, payload: str) -> None:
    if payload == "agent_resume":
        facebook.send_message(psid, "Welcome back! Let's continue where we left off.")
        state.update(psid, step="membership")


# ── HANDLERS dict (populated after all functions defined) ───────────────────

HANDLERS: dict[str, Callable[[str, str], None]] = {}  # filled at bottom of file


def dispatch(psid: str, raw_payload: str) -> None:
    payload = _normalize(raw_payload)

    # Global: handoff is always available
    if payload == "request_handoff":
        handle_handoff(psid, payload)
        return

    user = state.get(psid)
    step = user["step"]
    handler = HANDLERS.get(step, handle_start)
    handler(psid, payload)


# Populate HANDLERS after all functions are defined
HANDLERS.update({
    "start": handle_start,
    "privacy": handle_privacy,
    "membership": handle_membership,
    # NOTE: "done" is intentionally omitted — any new message from a user in
    # the "done" step falls back to the default handle_start, restarting the flow.
    "handoff": handle_handoff,
    "paused": handle_paused,
})
```

- [ ] **Step 4: Run tests — expect pass**

```bash
pytest tests/test_flow.py -v
```

Expected: `8 passed`

- [ ] **Step 5: Commit**

```bash
git add flow.py tests/test_flow.py
git commit -m "feat: flow dispatcher + start/privacy/membership handlers"
```

---

## Task 6: flow.py — invite / age_group / younger path handlers

**Files:**
- Modify: `flow.py`
- Modify: `tests/test_flow.py`

- [ ] **Step 1: Add failing tests to `tests/test_flow.py`**

Append to the end of `tests/test_flow.py`:

```python
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
```

- [ ] **Step 2: Run tests — expect failure**

```bash
pytest tests/test_flow.py -v
```

Expected: many failures for the new tests.

- [ ] **Step 3: Add handlers to `flow.py`**

Add these functions before the `HANDLERS.update(...)` call at the bottom of `flow.py`:

```python
def handle_invite(psid: str, payload: str) -> None:
    if payload == "will_join":
        facebook.send_buttons(
            psid,
            "Which age group best describes you?",
            [
                {"type": "postback", "title": "🧒 Younger (below 44)", "payload": "/younger_group"},
                {"type": "postback", "title": "👴 Seasoned (44+)", "payload": "/older_group"},
            ],
        )
        state.update(psid, step="age_group")
    elif payload == "not_joining":
        facebook.send_message(
            psid,
            "No problem! Take your time. Let me know if you change your mind or have any other questions.",
        )
        state.update(psid, step="done")
    elif payload == "request_handoff":
        handle_handoff(psid, payload)
    else:
        facebook.send_buttons(
            psid,
            "Would you like to join a D-Group?",
            [
                {"type": "postback", "title": "✅ I want to join", "payload": "/will_join"},
                {"type": "postback", "title": "⏳ I need more time", "payload": "/not_joining"},
                {"type": "postback", "title": "📞 Talk to a person", "payload": "/request_handoff"},
            ],
        )


def handle_age_group(psid: str, payload: str) -> None:
    if payload == "younger_group":
        facebook.send_buttons(
            psid,
            "Please select your life stage:",
            [
                {"type": "postback", "title": "👩‍💻 Elevate or B1G", "payload": "/elevate_B1G"},
                {"type": "postback", "title": "💍 Couple", "payload": "/married"},
                {"type": "postback", "title": "🧑‍🍼 Solo Parent", "payload": "/solo_parent"},
            ],
        )
        state.update(psid, step="life_stage_young")
    elif payload == "older_group":
        facebook.send_buttons(
            psid,
            "Are you a Gen X (1965–1980) or Baby Boomer (1946–1964)?",
            [
                {"type": "postback", "title": "🧓 Gen X", "payload": "/gen_x"},
                {"type": "postback", "title": "👴 Baby Boomers", "payload": "/baby_boomers"},
            ],
        )
        state.update(psid, step="generation_old")
    else:
        facebook.send_buttons(
            psid,
            "Which age group best describes you?",
            [
                {"type": "postback", "title": "🧒 Younger (below 44)", "payload": "/younger_group"},
                {"type": "postback", "title": "👴 Seasoned (44+)", "payload": "/older_group"},
            ],
        )


def handle_life_stage_young(psid: str, payload: str) -> None:
    if payload == "elevate_b1g":
        facebook.send_buttons(
            psid,
            "Elevate or B1G — which one?",
            [
                {"type": "postback", "title": "👩‍💻 Elevate — Students", "payload": "/elevate"},
                {"type": "postback", "title": "👩‍💻 B1G — Young Professional", "payload": "/young_professionals"},
            ],
        )
        state.update(psid, step="elevate_b1g")
    elif payload == "married":
        state.update(psid, life_stage="married", marital_status="Married", age_group="Millennials")
        _ask_availability_group(psid)
    elif payload == "solo_parent":
        state.update(psid, life_stage="solo_parent", marital_status="Solo Parent", age_group="Gen X")
        _ask_gender(psid)
    else:
        facebook.send_buttons(
            psid,
            "Please select your life stage:",
            [
                {"type": "postback", "title": "👩‍💻 Elevate or B1G", "payload": "/elevate_B1G"},
                {"type": "postback", "title": "💍 Couple", "payload": "/married"},
                {"type": "postback", "title": "🧑‍🍼 Solo Parent", "payload": "/solo_parent"},
            ],
        )


def handle_elevate_b1g(psid: str, payload: str) -> None:
    if payload == "elevate":
        state.update(psid, life_stage="elevate", marital_status="Young Adult", age_group="Gen Z")
        _ask_gender(psid)
    elif payload == "young_professionals":
        state.update(
            psid,
            life_stage="young_professionals",
            marital_status="Young Adult",
            age_group="Millennials",
        )
        _ask_gender(psid)
    else:
        facebook.send_buttons(
            psid,
            "Elevate or B1G — which one?",
            [
                {"type": "postback", "title": "👩‍💻 Elevate — Students", "payload": "/elevate"},
                {"type": "postback", "title": "👩‍💻 B1G — Young Professional", "payload": "/young_professionals"},
            ],
        )


def handle_gender(psid: str, payload: str) -> None:
    if payload in ("male", "female"):
        state.update(psid, gender=payload)
        _ask_availability_group(psid)
    else:
        _ask_gender(psid)
```

Then update the `HANDLERS.update(...)` call:

```python
HANDLERS.update({
    "start": handle_start,
    "privacy": handle_privacy,
    "membership": handle_membership,
    "invite": handle_invite,
    "age_group": handle_age_group,
    "life_stage_young": handle_life_stage_young,
    "elevate_b1g": handle_elevate_b1g,
    "gender": handle_gender,
    # NOTE: "done" is intentionally omitted — any new message from a user in
    # the "done" step falls back to the default handle_start, restarting the flow.
    "handoff": handle_handoff,
    "paused": handle_paused,
})
```

- [ ] **Step 4: Run tests — expect pass**

```bash
pytest tests/test_flow.py -v
```

Expected: all tests pass (previously passing + new ones)

- [ ] **Step 5: Commit**

```bash
git add flow.py tests/test_flow.py
git commit -m "feat: invite/age_group/younger-path handlers"
```

---

## Task 7: flow.py — Older path + all availability handlers

**Files:**
- Modify: `flow.py`
- Modify: `tests/test_flow.py`

- [ ] **Step 1: Add failing tests**

Append to `tests/test_flow.py`:

```python
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
```

- [ ] **Step 2: Run tests — expect failure**

```bash
pytest tests/test_flow.py -v
```

Expected: new tests fail with `KeyError` or handler-not-found.

- [ ] **Step 3: Add handlers to `flow.py`**

Add these functions before `HANDLERS.update(...)`:

```python
def handle_generation_old(psid: str, payload: str) -> None:
    if payload == "gen_x":
        state.update(psid, age_group="Gen X")
    elif payload == "baby_boomers":
        state.update(psid, age_group="Baby Boomers")
    else:
        facebook.send_buttons(
            psid,
            "Are you a Gen X (1965–1980) or Baby Boomer (1946–1964)?",
            [
                {"type": "postback", "title": "🧓 Gen X", "payload": "/gen_x"},
                {"type": "postback", "title": "👴 Baby Boomers", "payload": "/baby_boomers"},
            ],
        )
        return
    facebook.send_buttons(
        psid,
        "Which life stage best describes your current situation?",
        [
            {"type": "postback", "title": "👤 Single", "payload": "/single"},
            {"type": "postback", "title": "💍 Married", "payload": "/married"},
            {"type": "postback", "title": "🕊️ Widowed", "payload": "/widowed"},
        ],
    )
    state.update(psid, step="life_stage_old")


def handle_life_stage_old(psid: str, payload: str) -> None:
    mapping = {"single": "Single", "married": "Married", "widowed": "Widowed"}
    if payload in mapping:
        state.update(psid, marital_status=mapping[payload])
        _ask_availability_group(psid)
    else:
        facebook.send_buttons(
            psid,
            "Which life stage best describes your current situation?",
            [
                {"type": "postback", "title": "👤 Single", "payload": "/single"},
                {"type": "postback", "title": "💍 Married", "payload": "/married"},
                {"type": "postback", "title": "🕊️ Widowed", "payload": "/widowed"},
            ],
        )


def handle_availability_group(psid: str, payload: str) -> None:
    if payload == "mwf":
        facebook.send_buttons(
            psid,
            "Which day works for you between M-W-F?",
            [
                {"type": "postback", "title": "📅 Monday", "payload": "/monday"},
                {"type": "postback", "title": "📅 Wednesday", "payload": "/wednesday"},
                {"type": "postback", "title": "📅 Friday", "payload": "/friday"},
            ],
        )
        state.update(psid, step="availability_mwf")
    elif payload == "tth":
        facebook.send_buttons(
            psid,
            "Which day works for you between Tuesday or Thursday?",
            [
                {"type": "postback", "title": "📅 Tuesday", "payload": "/tuesday"},
                {"type": "postback", "title": "📅 Thursday", "payload": "/thursday"},
            ],
        )
        state.update(psid, step="availability_tth")
    elif payload == "weekend":
        facebook.send_buttons(
            psid,
            "Which day works for you on the weekend?",
            [
                {"type": "postback", "title": "🌅 Saturday", "payload": "/saturday"},
                {"type": "postback", "title": "⛪ Sunday", "payload": "/sunday"},
            ],
        )
        state.update(psid, step="availability_weekend")
    else:
        _ask_availability_group(psid)


def handle_availability_mwf(psid: str, payload: str) -> None:
    day_map = {"monday": "Monday", "wednesday": "Wednesday", "friday": "Friday"}
    if payload in day_map:
        state.update(psid, availability_day=day_map[payload])
        _ask_preferred_time(psid)
    else:
        facebook.send_buttons(
            psid,
            "Which day works for you between M-W-F?",
            [
                {"type": "postback", "title": "📅 Monday", "payload": "/monday"},
                {"type": "postback", "title": "📅 Wednesday", "payload": "/wednesday"},
                {"type": "postback", "title": "📅 Friday", "payload": "/friday"},
            ],
        )


def handle_availability_tth(psid: str, payload: str) -> None:
    day_map = {"tuesday": "Tuesday", "thursday": "Thursday"}
    if payload in day_map:
        state.update(psid, availability_day=day_map[payload])
        _ask_preferred_time(psid)
    else:
        facebook.send_buttons(
            psid,
            "Which day works for you between Tuesday or Thursday?",
            [
                {"type": "postback", "title": "📅 Tuesday", "payload": "/tuesday"},
                {"type": "postback", "title": "📅 Thursday", "payload": "/thursday"},
            ],
        )


def handle_availability_weekend(psid: str, payload: str) -> None:
    day_map = {"saturday": "Saturday", "sunday": "Sunday"}
    if payload in day_map:
        state.update(psid, availability_day=day_map[payload])
        _ask_preferred_time(psid)
    else:
        facebook.send_buttons(
            psid,
            "Which day works for you on the weekend?",
            [
                {"type": "postback", "title": "🌅 Saturday", "payload": "/saturday"},
                {"type": "postback", "title": "⛪ Sunday", "payload": "/sunday"},
            ],
        )
```

Update `HANDLERS.update(...)` to include the new handlers:

```python
HANDLERS.update({
    "start": handle_start,
    "privacy": handle_privacy,
    "membership": handle_membership,
    "invite": handle_invite,
    "age_group": handle_age_group,
    "life_stage_young": handle_life_stage_young,
    "elevate_b1g": handle_elevate_b1g,
    "gender": handle_gender,
    "generation_old": handle_generation_old,
    "life_stage_old": handle_life_stage_old,
    "availability_group": handle_availability_group,
    "availability_mwf": handle_availability_mwf,
    "availability_tth": handle_availability_tth,
    "availability_weekend": handle_availability_weekend,
    # NOTE: "done" is intentionally omitted — any new message from a user in
    # the "done" step falls back to the default handle_start, restarting the flow.
    "handoff": handle_handoff,
    "paused": handle_paused,
})
```

- [ ] **Step 4: Run tests — expect pass**

```bash
pytest tests/test_flow.py -v
```

Expected: all tests pass

- [ ] **Step 5: Commit**

```bash
git add flow.py tests/test_flow.py
git commit -m "feat: older path + availability handlers"
```

---

## Task 8: flow.py — preferred_time / mobile / wind_down

**Files:**
- Modify: `flow.py`
- Modify: `tests/test_flow.py`

- [ ] **Step 1: Add failing tests**

Append to `tests/test_flow.py`:

```python
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

def test_wind_down_get_started_resets_and_sends_privacy(mocker):
    mocker.patch("flow.facebook.send_buttons")
    state.update(PSID, step="wind_down", first_name="Juan", mobile_number="09171234567")
    flow.dispatch(PSID, "/get_started")
    user = state.get(PSID)
    assert user["step"] == "privacy"   # after reset + handle_start, step is "privacy"
    assert user["first_name"] == ""    # reset clears the name


def test_wind_down_im_good_sends_farewell(mocker):
    mocker.patch("flow.facebook.send_message")
    state.update(PSID, step="wind_down")
    flow.dispatch(PSID, "/wind_down")
    assert state.get(PSID)["step"] == "done"
    flow.facebook.send_message.assert_called_once()
```

- [ ] **Step 2: Run tests — expect failure**

```bash
pytest tests/test_flow.py -v
```

Expected: new tests fail.

- [ ] **Step 3: Add handlers to `flow.py`**

Add the `import re` and `import schedule` at the top of `flow.py`:

```python
import re
import facebook
import schedule
import state
from config import Config
```

Then add these handler functions before `HANDLERS.update(...)`:

```python
_MOBILE_RE = re.compile(r"^(\+63|0)9\d{9}$")


def handle_preferred_time(psid: str, payload: str) -> None:
    if payload not in ("afternoon", "evening", "specific_hours"):
        _ask_preferred_time(psid)
        return
    state.update(psid, preferred_time=payload)
    user = state.get(psid)
    result = schedule.find_schedule(
        age_group=user["age_group"],
        marital_status=user["marital_status"],
        day=user["availability_day"],
        preferred_time=payload,
    )
    if result:
        facebook.send_message(psid, result)
    else:
        facebook.send_message(
            psid,
            "Sorry, I couldn't find a schedule matching your profile. "
            "A team member will follow up with you.",
        )
    facebook.send_buttons(
        psid,
        "Happy to share your mobile number?",
        [
            {"type": "postback", "title": "📱 Take my number!", "payload": "/provide_mobile"},
            {"type": "postback", "title": "🙅 I'm not ready to share", "payload": "/not_ready_to_share"},
            {"type": "postback", "title": "📞 Talk to a person", "payload": "/request_handoff"},
        ],
    )
    state.update(psid, step="mobile_prompt")


def handle_mobile_prompt(psid: str, payload: str) -> None:
    if payload == "provide_mobile":
        facebook.send_message(psid, "Could you please share your mobile number?")
        state.update(psid, step="collect_mobile")
    elif payload == "not_ready_to_share":
        _show_wind_down(psid)
    elif payload == "request_handoff":
        handle_handoff(psid, payload)
    else:
        facebook.send_buttons(
            psid,
            "Happy to share your mobile number?",
            [
                {"type": "postback", "title": "📱 Take my number!", "payload": "/provide_mobile"},
                {"type": "postback", "title": "🙅 I'm not ready to share", "payload": "/not_ready_to_share"},
                {"type": "postback", "title": "📞 Talk to a person", "payload": "/request_handoff"},
            ],
        )


def handle_collect_mobile(psid: str, payload: str) -> None:
    if _MOBILE_RE.match(payload.strip()):
        state.update(psid, mobile_number=payload.strip())
        user = state.get(psid)
        summary = (
            f"Wonderful! {user['first_name']} {user['last_name']}\n"
            f"You belong to {user['age_group']}!\n"
            f"You are free on {user['availability_day']}.\n"
            f"Your preferred time is {user['preferred_time']}.\n"
            f"You'll probably fit right in with the {user['marital_status']} group.\n"
            f"Your mobile number: {user['mobile_number']}. "
            "You can ask us to remove your mobile number from our records anytime."
        )
        facebook.send_message(psid, summary)
        _show_wind_down(psid)
    else:
        facebook.send_message(psid, "Please send a valid PH mobile number (e.g. 09171234567).")


def handle_wind_down(psid: str, payload: str) -> None:
    if payload == "get_started":
        state.reset(psid)
        handle_start(psid, payload)
    else:
        facebook.send_message(psid, "Thank you! God bless! 🙏")
        state.update(psid, step="done")
```

Update the final `HANDLERS.update(...)` to include all handlers:

```python
HANDLERS.update({
    "start": handle_start,
    "privacy": handle_privacy,
    "membership": handle_membership,
    "invite": handle_invite,
    "age_group": handle_age_group,
    "life_stage_young": handle_life_stage_young,
    "elevate_b1g": handle_elevate_b1g,
    "gender": handle_gender,
    "generation_old": handle_generation_old,
    "life_stage_old": handle_life_stage_old,
    "availability_group": handle_availability_group,
    "availability_mwf": handle_availability_mwf,
    "availability_tth": handle_availability_tth,
    "availability_weekend": handle_availability_weekend,
    "preferred_time": handle_preferred_time,
    "mobile_prompt": handle_mobile_prompt,
    "collect_mobile": handle_collect_mobile,
    "wind_down": handle_wind_down,
    # NOTE: "done" is intentionally omitted — any new message from a user in
    # the "done" step falls back to the default handle_start, restarting the flow.
    "handoff": handle_handoff,
    "paused": handle_paused,
})
```

- [ ] **Step 4: Run tests — expect pass**

```bash
pytest tests/test_flow.py -v
```

Expected: all tests pass

- [ ] **Step 5: Run full test suite**

```bash
pytest -v
```

Expected: all tests across all files pass.

- [ ] **Step 6: Commit**

```bash
git add flow.py tests/test_flow.py
git commit -m "feat: complete flow — schedule display, mobile, wind-down"
```

---

## Task 9: app.py

**Files:**
- Rewrite: `app.py`
- Create: `tests/test_app.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_app.py`:

```python
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
```

- [ ] **Step 2: Run tests — expect failure**

```bash
pytest tests/test_app.py -v
```

Expected: failures — `app.py` still has the old implementation.

- [ ] **Step 3: Rewrite `app.py`**

```python
import logging
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import uvicorn
from config import Config
import flow

logger = logging.getLogger(__name__)
app = FastAPI()


@app.get("/webhook")
async def verify_webhook(request: Request) -> PlainTextResponse:
    token = request.query_params.get("hub.verify_token", "")
    challenge = request.query_params.get("hub.challenge", "")
    if token == Config.VERIFY_TOKEN:
        return PlainTextResponse(challenge)
    return PlainTextResponse("Forbidden", status_code=403)


@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        return {"status": "bad_request"}

    if data.get("object") != "page":
        return {"status": "ignored"}

    for entry in data.get("entry", []):
        for messaging in entry.get("messaging", []):
            psid: str = messaging.get("sender", {}).get("id", "")
            if not psid:
                continue

            try:
                # Agent resume: human inbox returning control to bot
                if "pass_thread_control" in messaging:
                    prev_app = messaging["pass_thread_control"].get("previous_owner_app_id", "")
                    if prev_app == Config.PAGE_INBOX_APP_ID:
                        flow.dispatch(psid, "agent_resume")
                    continue

                # Postback button tap
                postback = messaging.get("postback", {})
                if postback.get("payload"):
                    flow.dispatch(psid, postback["payload"])
                    continue

                # Regular text message
                message = messaging.get("message", {})
                text = message.get("text", "")
                if text:
                    flow.dispatch(psid, text)

            except Exception as exc:
                logger.exception("Error handling message for psid=%s: %s", psid, exc)

    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
```

- [ ] **Step 4: Run tests — expect pass**

```bash
pytest tests/test_app.py -v
```

Expected: `6 passed`

- [ ] **Step 5: Run full test suite**

```bash
pytest -v
```

Expected: all tests pass across all files.

- [ ] **Step 6: Commit**

```bash
git add app.py tests/test_app.py
git commit -m "feat: FastAPI webhook with dispatch and agent resume"
```

---

## Task 10: Cleanup + Deploy Instructions

**Files:**
- Delete: `cb-onboarding-2026/` (Rasa directory — archive or remove)
- Verify: all tests still pass after cleanup

- [ ] **Step 1: Run the full test suite one last time**

```bash
cd /Users/dennisnunez/workspace/claudework/cb-onboarding-refactored
pytest -v
```

Expected: all tests pass with output similar to:
```
tests/test_app.py::... PASSED
tests/test_facebook.py::... PASSED
tests/test_flow.py::... PASSED
tests/test_schedule.py::... PASSED
tests/test_state.py::... PASSED
XX passed in X.XXs
```

- [ ] **Step 2: Archive the old Rasa directory**

```bash
cd /Users/dennisnunez/workspace/claudework
mv cb-onboarding-2026 cb-onboarding-2026-rasa-archive
```

(Keep it for reference — don't delete immediately in case you need something.)

- [ ] **Step 3: Set up your `.env` file**

```bash
cd cb-onboarding-refactored
cp .env.example .env
# Edit .env and fill in:
#   PAGE_ACCESS_TOKEN=<your real token from Facebook App Dashboard>
#   VERIFY_TOKEN=<any secret string you choose, e.g. "ccf_imus_2026">
#   CCF_SATELLITE=Imus
```

- [ ] **Step 4: Run locally with ngrok**

Terminal 1:
```bash
cd cb-onboarding-refactored
uvicorn app:app --reload --port 8000
```

Terminal 2:
```bash
ngrok http 8000
```

Copy the HTTPS URL from ngrok (e.g. `https://abc123.ngrok.io`).

In Facebook App Dashboard → Webhooks → Edit:
- Callback URL: `https://abc123.ngrok.io/webhook`
- Verify token: (same value as `VERIFY_TOKEN` in `.env`)
- Subscribe to: `messages`, `messaging_postbacks`

Click "Verify and Save". If it returns 200, your bot is connected.

- [ ] **Step 5: Manual end-to-end test in Messenger**

Go to your Facebook Page in Messenger. Test this happy path:

1. Tap "Get Started" → bot sends privacy policy buttons
2. Tap "✅ Accept" → bot greets you by name, asks membership
3. Tap "Not yet a member" → invite to join buttons
4. Tap "✅ I want to join" → age group buttons
5. Tap "Younger (below 44)" → life stage buttons
6. Tap "Elevate or B1G" → sub-buttons
7. Tap "B1G — Young Professional" → gender buttons
8. Tap "Male" → availability day group buttons
9. Tap "M-W-F" → Monday/Wednesday/Friday buttons
10. Tap "Monday" → preferred time buttons
11. Tap "Afternoon" → schedule text + mobile prompt buttons
12. Tap "📱 Take my number!" → "Please share your mobile number"
13. Type `09171234567` → summary message + wind-down buttons
14. Tap "I'm good" → "Thank you! God bless!"

- [ ] **Step 6: Deploy to Railway**

1. Push to GitHub:
   ```bash
   git remote add origin https://github.com/<your-username>/ccf-onboarding-bot.git
   git push -u origin main
   ```

2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub repo.

3. Select the `cb-onboarding-refactored` directory as the root.

4. Add environment variables in Railway dashboard:
   - `PAGE_ACCESS_TOKEN`
   - `VERIFY_TOKEN`
   - `CCF_SATELLITE=Imus`

5. Set the start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`

6. Once deployed, update the FB webhook URL to the Railway HTTPS URL.

- [ ] **Step 7: Final commit**

```bash
git add .
git commit -m "chore: cleanup and deploy instructions"
```
