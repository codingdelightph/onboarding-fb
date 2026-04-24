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
