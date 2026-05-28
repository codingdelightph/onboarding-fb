import hashlib
import hmac
import json
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse
import uvicorn

from config import Config
import flow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI()


def _verify_signature(body: bytes, signature_header: str) -> bool:
    """Return True if X-Hub-Signature-256 matches HMAC-SHA256 of body."""
    if not Config.APP_SECRET:
        logger.error("APP_SECRET is not set — rejecting all webhook requests to prevent forged-request bypass")
        return False
    if not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(
        Config.APP_SECRET.encode(), body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature_header)


@app.get("/webhook")
async def verify_webhook(request: Request) -> PlainTextResponse:
    if not Config.VERIFY_TOKEN:
        logger.error("VERIFY_TOKEN is not set — rejecting all webhook verification requests")
        return PlainTextResponse("Forbidden", status_code=403)
    token = request.query_params.get("hub.verify_token", "")
    challenge = request.query_params.get("hub.challenge", "")
    if token == Config.VERIFY_TOKEN:
        return PlainTextResponse(challenge)
    logger.warning("Webhook verify_token mismatch")
    return PlainTextResponse("Forbidden", status_code=403)


@app.post("/webhook")
async def webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not _verify_signature(body, signature):
        logger.warning("Invalid webhook signature")
        return JSONResponse({"status": "forbidden"}, status_code=403)

    try:
        data = json.loads(body)
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
                        logger.warning(
                            "Unexpected pass_thread_control from app_id=%s for psid=%s",
                            prev_app, psid,
                        )
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


# Health check at root so Railway's health probe and quick browser tests succeed
@app.get("/")
async def root():
    return {"status": "ok", "service": "onboarding-fb"}


# Serve the privacy policy at a clean public URL
@app.get("/privacy-policy.html")
async def privacy_policy():
    return FileResponse("privacy-policy.html", media_type="text/html")


@app.get("/privacy-policy")
async def privacy_policy_alias():
    return FileResponse("privacy-policy.html", media_type="text/html")


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)