# onboarding-fb

A Facebook Messenger chatbot that guides new visitors through a D-Group onboarding flow for **CCF (Christ's Commission Fellowship)**. The bot asks a series of smart button-driven questions, matches the user to an appropriate D-Group schedule, and optionally hands the conversation to a human facilitator.

---

## Features

- Button-driven conversation — no free-text parsing required for the happy path
- Privacy policy acceptance gate before collecting any personal data
- Demographic profiling: age group, generation, life stage, marital status, gender
- Availability matching: day-of-week + time preference → D-Group schedule lookup from CSV
- Optional mobile number collection with PH number validation
- Human handoff via Facebook Inbox (pass-thread-control protocol)
- Agent resume — bot automatically picks up after a human finishes
- Webhook signature verification (HMAC-SHA256) to reject forged requests

---

## Tech Stack

| Layer | Choice |
|---|---|
| Language | Python 3.11 |
| Web framework | FastAPI |
| ASGI server | Uvicorn |
| Config | python-dotenv |
| Schedule data | CSV via pandas |
| Messenger API | Facebook Graph API v18+ |
| Hosting | Railway |
| Tests | pytest + pytest-mock + httpx |

---

## Project Structure

```
onboarding-fb/
├── app.py              # FastAPI app, webhook GET/POST handlers, signature verification
├── flow.py             # All conversation step handlers and the dispatch() router
├── state.py            # In-memory per-user state store (keyed by PSID)
├── facebook.py         # Facebook Graph API calls (send_message, send_buttons, handoff)
├── schedule.py         # CSV lookup: matches user profile to a D-Group schedule
├── config.py           # Env var loading via Config class
├── data/
│   ├── imus_dgroup_schedule.csv
│   ├── imus_lifestage.csv
│   └── schedule_options.csv
├── tests/
│   ├── test_app.py
│   ├── test_flow.py
│   └── test_schedule.py
├── .env.example
├── procfile
└── requirements.txt
```

---

## Conversation Flow

```
GET_STARTED / any message
    └─► Privacy policy acceptance
            └─► Member or Not-yet-member?
                    ├─► Member → done
                    └─► Not member
                            ├─► Want to join? → Age group
                            │       ├─► Younger (<44)
                            │       │       ├─► Elevate (students) → gender → day → time
                            │       │       ├─► B1G (young professional) → gender → day → time
                            │       │       ├─► Married (couple) → day → time
                            │       │       └─► Solo Parent → gender → day → time
                            │       └─► Seasoned (44+) → Gen X or Baby Boomer
                            │               └─► life stage (Single/Married/Widowed) → day → time
                            ├─► Need more time → done
                            └─► Talk to a person → human handoff (paused)

day → time → schedule lookup → mobile number prompt → wind-down
    wind-down options:
        Place me now  → human handoff + confirmation message
        Get back soon → done
        I'm good      → done
```

---

## Local Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/codingdelightph/onboarding-fb.git
cd onboarding-fb
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in real values:

```dotenv
PAGE_ACCESS_TOKEN=your_fb_page_access_token_here
VERIFY_TOKEN=your_chosen_verify_token_here
APP_SECRET=your_fb_app_secret_here
CCF_SATELLITE=Imus
PAGE_INBOX_APP_ID=3374491019519787
```

| Variable | Where to get it |
|---|---|
| `PAGE_ACCESS_TOKEN` | Meta for Developers → App → Messenger → Settings → Generate Token |
| `VERIFY_TOKEN` | Any string you choose; must match what you enter in the webhook config on Meta |
| `APP_SECRET` | Meta for Developers → App → Settings → Basic → App Secret |
| `CCF_SATELLITE` | The branch name shown to users (e.g. `Imus`) |
| `PAGE_INBOX_APP_ID` | The app ID of Facebook's native Page Inbox (default works for most pages) |

> **Security note:** `APP_SECRET` is required. The app will reject all incoming webhooks with HTTP 403 if this variable is missing or blank.

### 3. Run the server

```bash
uvicorn app:app --reload --port 8000
```

The server starts at `http://localhost:8000`. Use [ngrok](https://ngrok.com/) or similar to expose it for local Facebook webhook testing:

```bash
ngrok http 8000
```

Copy the `https://` ngrok URL and set it as your webhook URL in the Meta dashboard.

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `PAGE_ACCESS_TOKEN` | Yes | — | Facebook Page token for sending messages |
| `VERIFY_TOKEN` | Yes | — | Shared secret for webhook verification |
| `APP_SECRET` | Yes | — | Used to verify HMAC-SHA256 webhook signatures |
| `CCF_SATELLITE` | No | `Imus` | Branch name displayed in welcome messages |
| `PAGE_INBOX_APP_ID` | No | `3374491019519787` | App ID that owns the inbox handoff target |

---

## Running Tests

```bash
pytest
```

Run with verbose output:

```bash
pytest -v
```

Run a specific test file:

```bash
pytest tests/test_flow.py -v
```

All tests use mocked Facebook API calls — no real network requests are made.

---

## Deploying to Railway

1. Push your code to GitHub.
2. Create a new Railway project and link the repository.
3. Add all environment variables under **Variables** in the Railway dashboard (do not commit `.env`).
4. Railway uses the `procfile` to start the server:
   ```
   web: uvicorn app:app --host 0.0.0.0 --port $PORT
   ```
5. Once deployed, copy the Railway public URL and set it as your Facebook webhook:
   - **Callback URL:** `https://<your-app>.up.railway.app/webhook`
   - **Verify Token:** the value you set for `VERIFY_TOKEN`
   - **Subscriptions:** `messages`, `messaging_postbacks`, `messaging_handovers`

---

## Facebook App Setup Checklist

- [ ] Create a Meta App at [developers.facebook.com](https://developers.facebook.com)
- [ ] Add the **Messenger** product
- [ ] Generate a Page Access Token and add it to Railway env vars
- [ ] Subscribe the app to your Facebook Page
- [ ] Configure the webhook URL and verify token
- [ ] Enable subscriptions: `messages`, `messaging_postbacks`, `messaging_handovers`
- [ ] Set a **Get Started** button payload (recommended: `GET_STARTED`) via the Messenger Profile API
- [ ] Configure **Handover Protocol** — set your bot as the Primary Receiver and Page Inbox as the Secondary Receiver

---

## Adding a New Conversation Step

1. Write a handler function in `flow.py`:
   ```python
   def handle_my_step(psid: str, payload: str) -> None:
       if payload == "my_option":
           state.update(psid, some_field="value", step="next_step")
       else:
           # re-send the prompt on unexpected input
           facebook.send_buttons(psid, "Pick one:", [...])
   ```
2. Add the step key to `HANDLERS` at the bottom of `flow.py`:
   ```python
   HANDLERS["my_step"] = handle_my_step
   ```
3. Point an existing handler to the new step by calling `state.update(psid, step="my_step")`.
4. Add tests in `tests/test_flow.py`.

---

## Health Check

`GET /` returns `{"status": "ok", "service": "onboarding-fb"}` — used by Railway's health probe.

---

## License

Internal use — CCF Imus Onboarding Team.
