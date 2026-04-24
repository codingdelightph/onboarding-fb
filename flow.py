from typing import Callable
import facebook
import schedule
import state
from config import Config
import re


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


# ── HANDLERS dict ────────────────────────────────────────────────────────────

HANDLERS: dict[str, Callable[[str, str], None]] = {}


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
