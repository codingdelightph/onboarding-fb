import hmac
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
import uvicorn
from config import Config
import flow

logger = logging.getLogger(__name__)
app = FastAPI()


@app.get("/webhook")
async def verify_webhook(request: Request) -> PlainTextResponse:
    token = request.query_params.get("hub.verify_token", "")
    challenge = request.query_params.get("hub.challenge", "")
    if hmac.compare_digest(token, Config.VERIFY_TOKEN):
        return PlainTextResponse(challenge)
    return PlainTextResponse("Forbidden", status_code=403)


@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"status": "bad_request"}, status_code=400)

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
                    else:
                        logger.warning("Unexpected pass_thread_control from app_id=%s for psid=%s", prev_app, psid)
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
