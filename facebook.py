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
