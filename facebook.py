import logging
import requests
from config import Config

logger = logging.getLogger(__name__)
_BASE_URL = "https://graph.facebook.com/v21.0"


def _messages_url() -> str:
    return f"{_BASE_URL}/me/messages?access_token={Config.PAGE_ACCESS_TOKEN}"


def _log_response_error(action: str, response: requests.Response) -> None:
    if not response.ok:
        logger.error("%s failed: %s %s", action, response.status_code, response.text)


def send_message(psid: str, text: str) -> None:
    r = requests.post(_messages_url(), json={
        "recipient": {"id": psid},
        "message": {"text": text},
    })
    _log_response_error("send_message", r)


def send_buttons(psid: str, text: str, buttons: list) -> None:
    r = requests.post(_messages_url(), json={
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
    _log_response_error("send_buttons", r)


def send_carousel(psid: str, elements: list) -> None:
    r = requests.post(_messages_url(), json={
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
    _log_response_error("send_carousel", r)


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
    logger.error("fetch_user_name failed for psid=%s: %s", psid, response.status_code)
    return "", ""


def handoff_to_human(psid: str) -> None:
    url = f"{_BASE_URL}/me/pass_thread_control?access_token={Config.PAGE_ACCESS_TOKEN}"
    r = requests.post(url, json={
        "recipient": {"id": psid},
        "target_app_id": Config.PAGE_INBOX_APP_ID,
        "metadata": "Handoff to human agent",
    })
    _log_response_error("handoff_to_human", r)
