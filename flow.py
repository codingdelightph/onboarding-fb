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
    # NOTE: "done" is intentionally omitted — any new message from a user in
    # the "done" step falls back to the default handle_start, restarting the flow.
    "handoff": handle_handoff,
    "paused": handle_paused,
})
