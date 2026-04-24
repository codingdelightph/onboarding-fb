# CCF Imus D-Group Onboarding Bot — FastAPI Refactor Design

**Date:** 2026-04-24  
**Author:** Dennis Nunez  
**Status:** Approved — ready for implementation

---

## Overview

Refactor the existing Rasa + TensorFlow Facebook Messenger onboarding bot into a minimal FastAPI app. The new bot is purely rule-based (no NLU, no ML, no Rasa), uses a step-based state machine keyed by Facebook PSID, and is easy to own and maintain solo.

**Platform:** Facebook Messenger (Facebook Graph API v21.0)  
**Language:** Python 3.11  
**Framework:** FastAPI + Uvicorn  
**Deploy target:** Railway or Render

---

## Goals

- Remove all Rasa, TensorFlow, and training complexity
- Keep the exact same conversation flow, button text, and payloads
- Keep the same CSV data files — no data changes
- In-memory state per PSID (Redis-ready interface for later)
- Small focused files, type hints, readable code

---

## Folder Structure

```
cb-onboarding-refactored/
├── app.py              # FastAPI webhook + dispatcher
├── config.py           # Config class from .env
├── state.py            # In-memory user state keyed by PSID
├── facebook.py         # All FB Graph API calls
├── flow.py             # HANDLERS dict + all step handler functions
├── schedule.py         # CSV loading + schedule lookup
├── .env                # Secrets (not committed)
├── requirements.txt
└── data/
    ├── imus_dgroup_schedule.csv
    ├── imus_lifestage.csv
    └── schedule_options.csv
```

### File responsibilities

| File | Owns |
|---|---|
| `app.py` | HTTP only — webhook verify (GET) + parse POST + call `dispatch()` |
| `flow.py` | All conversation logic — `HANDLERS` dict, one function per step |
| `state.py` | Read/write user state by PSID (swap to Redis by changing only this file) |
| `facebook.py` | All outbound FB API calls, zero business logic |
| `schedule.py` | CSV loading + lookup by day / age_group / marital_status |
| `config.py` | All secrets and constants from `.env` |

---

## State Fields (per PSID)

```python
{
    "step": str,              # current state machine step name
    "first_name": str,
    "last_name": str,
    "age_group": str,         # "Gen Z" | "Millennials" | "Gen X" | "Baby Boomers"
    "life_stage": str,        # "elevate" | "young_professionals" | "married" | "solo_parent"
                              # "single" | "widowed"
    "marital_status": str,    # "Young Adult" | "Married" | "Solo Parent" | "Single" | "Widowed"
    "gender": str,            # "male" | "female"
    "availability_day": str,  # "Monday" … "Sunday"
    "preferred_time": str,    # "afternoon" | "evening" | "specific_hours"
    "mobile_number": str,
}
```

---

## State Machine — All Steps & Transitions

| Step | Trigger payload(s) | Bot sends | Next step |
|---|---|---|---|
| `start` | any first message / Get Started | Privacy policy buttons | `privacy` |
| `privacy` | `/accept_privacy_policy` | Greet by FB name + D-Group membership buttons | `membership` |
| `membership` | `/member` | "That's great! How can I assist you?" | `done` |
| `membership` | `/not_member` | Invite to join buttons | `invite` |
| `invite` | `/will_join` | Age group buttons | `age_group` |
| `invite` | `/not_joining` | "No problem, take your time." | `done` |
| `invite` | `/request_handoff` | "Connecting you…" + handoff | `handoff` |
| `age_group` | `/younger_group` | Younger life stage buttons | `life_stage_young` |
| `age_group` | `/older_group` | Older generation buttons | `generation_old` |
| `life_stage_young` | `/elevate_B1G` | Elevate / B1G sub-buttons | `elevate_b1g` |
| `life_stage_young` | `/married` | (stores marital=Married) | `availability_group` |
| `life_stage_young` | `/solo_parent` | Gender buttons | `gender` |
| `elevate_b1g` | `/elevate` | Gender buttons | `gender` |
| `elevate_b1g` | `/young_professionals` | Gender buttons | `gender` |
| `gender` | `/male` `/female` | (stores gender) | `availability_group` |
| `generation_old` | `/gen_x` `/baby_boomers` | Older life stage buttons | `life_stage_old` |
| `life_stage_old` | `/single` `/married` `/widowed` | (stores marital_status) | `availability_group` |
| `availability_group` | `/mwf` | Mon / Wed / Fri buttons | `availability_mwf` |
| `availability_group` | `/tth` | Tue / Thu buttons | `availability_tth` |
| `availability_group` | `/weekend` | Sat / Sun buttons | `availability_weekend` |
| `availability_mwf` | `/monday` `/wednesday` `/friday` | (stores day) | `preferred_time` |
| `availability_tth` | `/tuesday` `/thursday` | (stores day) | `preferred_time` |
| `availability_weekend` | `/saturday` `/sunday` | (stores day) | `preferred_time` |
| `preferred_time` | `/afternoon` `/evening` `/specific_hours` | Schedule text from CSV + mobile prompt buttons | `mobile_prompt` |
| `mobile_prompt` | `/provide_mobile` | "Please type your mobile number" | `collect_mobile` |
| `mobile_prompt` | `/not_ready_to_share` | Wind-down buttons | `wind_down` |
| `mobile_prompt` | `/request_handoff` | Handoff | `handoff` |
| `collect_mobile` | free text matching `09\d{9}` or `\+639\d{9}` | Summary + wind-down buttons | `wind_down` |
| `collect_mobile` | free text NOT matching mobile regex | "Please send a valid PH mobile number (e.g. 09171234567)" | `collect_mobile` (stay) |
| `wind_down` | `/get_started` | Reset ALL state fields + restart | `start` |
| `wind_down` | `/wind_down` / any | "Thanks, God bless!" | `done` |
| `handoff` | (internal) | `pass_thread_control` to Page Inbox | `paused` |
| `paused` | FB `pass_thread_control` webhook event with `previous_owner_app_id = 3374491019519787` | Resume greeting | `membership` |

### Dispatch rules

- Payloads arrive as `/intent_name` strings. The dispatcher strips leading `/` and lowercases before matching.
- **Unknown payload at any step:** Bot replies "I didn't get that — please choose one of the options." and re-sends the current step's buttons.
- **Agent resume trigger:** Detected in `app.py` POST handler as a `pass_thread_control` event where `messaging[].pass_thread_control.previous_owner_app_id == "3374491019519787"`. When detected, `dispatch(psid, "agent_resume")` is called, setting step back to `membership`.
- **Full restart:** When `/get_started` is received in `wind_down`, `state.reset(psid)` clears all fields (equivalent to a brand-new user) before transitioning to `start`.
- **`/request_handoff` is valid at any step** — always triggers handoff regardless of current step.

---

## Schedule Lookup (`schedule.py`)

Reads `data/imus_dgroup_schedule.csv` (columns: `satellite, day, age_group, marital_status, leader, start_time, end_time`).

Lookup: filter by `satellite == CCF_SATELLITE` (default "Imus") + `day` + `age_group` + `marital_status`.

- Match found → "The group on {day} for {age_group} ({marital_status}) is led by {leader} and runs from {start_time} to {end_time}."
- No match → "Sorry, I couldn't find a schedule matching your profile." + offer handoff button.

Afternoon filter: `start_time` between 2:00 PM – 6:00 PM.  
Evening filter: `start_time` after 6:00 PM.  
Specific hours: show all matches for that day, no time filter.

---

## Facebook API (`facebook.py`)

All calls use `POST https://graph.facebook.com/v21.0/me/messages?access_token=TOKEN`.

| Function | Purpose |
|---|---|
| `send_message(psid, text)` | Plain text message |
| `send_buttons(psid, text, buttons)` | Button template (max 3 buttons) |
| `send_carousel(psid, elements)` | Generic template (cards) |
| `send_quick_replies(psid, text, replies)` | Quick reply bubbles |
| `fetch_user_name(psid) -> tuple[str,str]` | GET Graph API for first_name, last_name |
| `handoff_to_human(psid)` | `pass_thread_control` to target_app_id 3374491019519787 |

---

## Error Handling

- FB webhook always returns `200 OK` immediately (even on error) to prevent FB retry storms.
- Errors in handlers are caught, logged to stdout, and send a fallback message to the user.
- CSV `FileNotFoundError` → startup exception (fail fast; don't silently serve broken schedules).
- Invalid/missing FB token → log error, send nothing (don't crash the whole server).

---

## Removed From Rasa Version

| Removed | Reason |
|---|---|
| `ActionRecommendDGroup` (TensorFlow) | Mock model; CSV lookup is the real recommendation |
| `ActionPredictDay` (TensorFlow) | Users choose their own day |
| All Rasa YAML (domain, stories, rules, nlu, config, endpoints) | Replaced by `flow.py` |
| `models/` directory | TF SavedModels no longer needed |
| `actions/` directory | All logic moves to `flow.py` |
| `utils/` directory | `schedule.py` replaces `utils/schedule.py` |

---

## Testing Plan

- Unit tests for `schedule.py` — lookup returns correct row, no-match case, time filter cases.
- Unit tests for `flow.py` — each handler called with a mock state returns the expected next step.
- Manual integration test: run locally with `uvicorn app:app --reload`, use ngrok to expose, test full flow in FB Messenger test page.

---

## Running Locally

```bash
cd cb-onboarding-refactored
pip install -r requirements.txt
cp .env.example .env   # fill in PAGE_ACCESS_TOKEN and VERIFY_TOKEN
uvicorn app:app --reload
# then: ngrok http 8000
# set webhook URL in FB App Dashboard to https://<ngrok-url>/webhook
```

## Deploying to Railway / Render

1. Push `cb-onboarding-refactored/` to a GitHub repo.
2. Create a new Railway/Render service pointing to that repo.
3. Set environment variables: `PAGE_ACCESS_TOKEN`, `VERIFY_TOKEN`, `CCF_SATELLITE=Imus`.
4. Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`.
5. Update the Facebook webhook URL to the deployed HTTPS URL.
