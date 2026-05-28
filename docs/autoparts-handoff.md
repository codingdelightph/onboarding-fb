# Autoparts Trading Bot — Handoff from onboarding-fb

Reviewed by Claude Opus 4.7. This document maps reusable components from the CCF onboarding bot
to an Autoparts Trading FB Messenger bot, with accurate classifications and known gotchas.

---

## Read This First — Two Blockers That Affect the Design

### 1. FB Messenger hard-caps button templates at 3 buttons per message

`facebook.py` only implements `send_buttons` (3-button cap) and `send_carousel` (10 elements × 3 buttons).
The Philippine auto market has 15+ common makes and 10–20+ models per make. Button menus **cannot**
cover vehicle selection. You need one or more of:

- **Quick Replies** — up to 13 chip-style buttons, disappear after tap. Best for make/model pickers.
  **Not in `facebook.py` — you must add `send_quick_replies()`.**
- **Carousel with pagination** — 10 elements max per message; add a "More →" element to chain.
- **Free-text input** — accept make/model as typed text, normalize with a lookup dict.

Plan this before writing a single flow handler. The suggested flow at the bottom of this doc reflects
these constraints.

### 2. In-memory state is wiped on every Railway redeploy

`state.py` stores all user sessions in a plain module-level dict (`_states`). Every deploy, container
restart, or Railway scale-to-zero event silently loses all in-progress conversations.

For a church onboarding bot, a dropped session is a minor inconvenience. For a sales/inquiry bot
capturing phone numbers and part requests, it is a lost lead.

**Recommendation:** Replace `state.py`'s backing store with Redis or SQLite before launch.
The `get`/`update`/`reset` interface stays the same — only the storage changes.

---

## What to Copy (With Noted Exceptions)

### Copy with small edits

| File | What it provides | What to change |
|---|---|---|
| `app.py` | FastAPI webhook, HMAC-SHA256 signature verification, health check, privacy policy route | Line 101: change `"onboarding-fb"` to new service name. Lines 105–112: replace `privacy-policy.html` with your own file. See gotchas below. |
| `facebook.py` | `send_message`, `send_buttons`, `send_carousel`, `fetch_user_name`, `handoff_to_human` | Add `send_quick_replies()` (needed for vehicle selection). Note `send_carousel` is present but **never called in the CCF flow and has no tests** — test it before relying on it. Graph API pinned to `v21.0` (line 6); check for deprecation at [developers.facebook.com/docs/graph-api/changelog](https://developers.facebook.com/docs/graph-api/changelog) when creating the new app. |
| `config.py` | Env var loading | Rename `CCF_SATELLITE` to something meaningful. Replace the three CSV path constants (lines 17–19) with your catalog path(s). `PAGE_INBOX_APP_ID` default `3374491019519787` is Facebook's native Page Inbox — update if the business uses a third-party inbox (Manychat, Chatwoot, etc.), otherwise agent-resume silently breaks. |
| `state.py` | Per-user session store | Replace the dict fields in `_default_state()` (see below). Swap backing store to Redis/SQLite if session durability matters. |
| `procfile` | Railway startup | No changes needed. Note: filename is lowercase — Railway accepts this. |
| `.env.example` | Env var docs | Replace CCF-specific vars with autoparts equivalents. Add catalog path var. |
| `pytest.ini` | Test config | No changes needed. |

### Copy verbatim

| File | Notes |
|---|---|
| `.github/workflows/deploy.yml` | Fully generic — no project-specific identifiers. **Prerequisites:** create a `production` environment in GitHub repo Settings → Environments, add `RAILWAY_TOKEN` as a **Secret**, add `RAILWAY_SERVICE` and `RAILWAY_ENVIRONMENT` as **Variables** (not secrets). See the setup comments at the top of the file. |
| `requirements.txt` | Full list: `fastapi`, `uvicorn[standard]`, `python-dotenv`, `pandas`, `requests`, `python-multipart`, `pytest`, `pytest-mock`, `httpx`. All needed — `pytest-mock` in particular is used throughout `tests/`. |

---

## What to Refactor

### `flow.py` — Conversation Engine

**Keep exactly as-is:**

- `dispatch()` + `HANDLERS` dict — the routing engine. One important behavior: `HANDLERS.get(step, handle_start)` (line 514) means any unrecognised step silently restarts the flow. This is fine for happy-path design but masks bugs during development — add a logger warning there when building new steps.
- `_normalize()` — strips `/` prefix and lowercases payloads. Copy unchanged.
- Global handoff intercept (lines 507–510):
  ```python
  if payload == "request_handoff":
      handle_handoff(psid, payload)
      return
  ```
  This is what makes "Talk to a person" buttons work from **any step** in the flow. Do not remove it during refactoring.
- `handle_handoff()` + `handle_paused()` — human handoff and agent-resume. Copy exactly.
- Wind-down pattern (`_show_wind_down` + `handle_wind_down`) — replace copy and button labels only.
- Mobile number collection (`_MOBILE_RE`, `handle_collect_mobile`, `handle_mobile_prompt`) — PH number validation is reusable. Copy as-is.

**Replace entirely:**

All CCF-specific handlers: `handle_membership`, `handle_invite`, `handle_age_group`,
`handle_life_stage_young`, `handle_life_stage_old`, `handle_elevate_b1g`, `handle_gender`,
`handle_generation_old`, `handle_availability_*`, `handle_preferred_time`.

**Keep the privacy gate, update the content:**

`handle_start` + `handle_privacy` — keep the pattern. Replace the privacy policy URL (currently
`https://www.nxtaigen.com/cb-onboarding-policy.html`, hardcoded in `flow.py` line 78) with the new
bot's URL. See privacy policy note below.

**`fetch_user_name` edge case:**

`facebook.py` line 59 returns `("", "")` silently on failure. The CCF bot uses `first_name` in
several messages and the summary. If the Graph API call fails or the page lacks profile permission,
all downstream messages will render with empty names (e.g. `"Wonderful!  "`). Add an explicit
fallback string (`"there"` or similar) in `handle_privacy` or wherever names are first used.

---

### `state.py` — User State Fields

Replace all fields in `_default_state()`. The actual current fields are:
`step, first_name, last_name, age_group, life_stage, marital_status, gender, availability_day, preferred_time, mobile_number`.

Autoparts equivalent:

```python
def _default_state() -> dict[str, Any]:
    return {
        "step": "start",
        "first_name": "",
        "last_name": "",
        "mobile_number": "",
        "vehicle_make": "",        # Toyota, Honda, Mitsubishi, etc.
        "vehicle_model": "",       # Vios, Civic, L300, etc.
        "vehicle_year": "",        # 2018, 2019, etc. (free-text or picker)
        "part_category": "",       # engine, brakes, suspension, electrical, body
        "part_subcategory": "",    # brake pads, brake disc, caliper, etc.
        "part_description": "",    # free-text detail from customer
        "inquiry_type": "",        # parts / labor / both
        "branch": "",              # if multi-location
    }
```

---

### `schedule.py` → `catalog.py`

The pattern (`load_csv` → filter → return formatted string) is directly reusable. Refactor signature:

```python
def find_parts(
    vehicle_make: str,
    vehicle_model: str,
    vehicle_year: str,
    part_category: str,
    part_subcategory: str = "",
) -> list[dict]:
    """Return matching parts from catalog. Empty list if no match."""
```

**Important warnings on the CSV approach:**

- Auto parts prices change frequently. A price stored in a CSV committed to git will go stale and
  could constitute misleading advertising. Either omit prices from the lookup result and tell customers
  "contact us for pricing", or load the CSV from an external source that can be updated without a deploy.
- The current `schedule.py` calls `pd.read_csv` on every lookup request (line 13) with no caching.
  Fine for a small CSV, but a real parts catalog with thousands of SKUs should be loaded once at startup
  and cached. Consider `@functools.lru_cache` or loading into a module-level dict on startup.
- CSV columns to design: `make, model, year_from, year_to, category, subcategory, part_name, part_number, availability` (omit price unless you have a refresh strategy).

---

## New Primitives to Add to `facebook.py`

### Quick Replies (required for vehicle selection)

```python
def send_quick_replies(psid: str, text: str, replies: list[dict]) -> None:
    """
    replies format:
    [{"content_type": "text", "title": "Toyota", "payload": "/toyota"}, ...]
    Max 13 replies. Titles max 20 chars.
    """
    r = requests.post(_messages_url(), json={
        "recipient": {"id": psid},
        "message": {
            "text": text,
            "quick_replies": replies,
        },
    })
    _log_response_error("send_quick_replies", r)
```

Quick Replies disappear after the user taps one, so they cannot be re-shown. Design handlers to
re-ask (send again) if the step receives an unexpected payload, same as the button handlers do.

---

## New Flows to Build

| Flow | Implementation notes |
|---|---|
| **Vehicle make** | Quick Replies with top 10–13 PH makes + "Other" fallback to free-text |
| **Vehicle model** | Quick Replies per make (Toyota: Vios/Wigo/Innova/Fortuner/Hilux/Avanza/Rush/Other; etc.) |
| **Vehicle year** | Free-text input — validate as 4-digit year between 1990 and current year + 1 |
| **Part category** | `send_buttons` works (≤3: Engine+Electrical / Brakes+Suspension / Body+Other, with sub-step) or Quick Replies for 6 in one shot |
| **Part subcategory** | Quick Replies per category |
| **Catalog lookup** | Call `catalog.find_parts()`, send result as message or carousel if multiple hits |
| **Quote/inquiry branch** | Get a quote (capture mobile → handoff) / Just browsing (done) / Talk to staff (direct handoff) |
| **Branch selection** | `send_buttons` if ≤3 branches, Quick Replies if more |
| **Image attachment** | `app.py` line 89–92 only handles `message.text` — it silently ignores `message.attachments`. Customers routinely send photos of broken parts on Messenger. Add an `attachments` branch in `app.py`'s webhook handler that sends: "Thanks for the photo! A staff member will review it and get back to you." + handoff. |

---

## Suggested Conversation Flow

Lead with the vehicle — that is how customers think.

```
GET_STARTED / any message
    └─► Privacy policy acceptance
            └─► Vehicle make  (Quick Replies: top makes + Other)
                    └─► Vehicle model  (Quick Replies per make)
                            └─► Vehicle year  (free-text, validated)
                                    └─► Part category  (Quick Replies)
                                            └─► Part subcategory  (Quick Replies)
                                                    └─► Catalog lookup result
                                                            ├─► Get a quote
                                                            │       └─► Mobile number → wind-down → handoff to staff
                                                            ├─► Talk to a person  (direct handoff, available at any step)
                                                            └─► Just browsing → done

Image received at any step → "Thanks for the photo!" → handoff to staff
```

Inquiry type (Parts / Labor / Both) can be asked **after** the vehicle is profiled and the catalog
result is shown — not before. Asking it first adds a question that doesn't help the customer decide.

---

## Pre-launch Checklist

### Facebook App Setup (commonly lost hours)
- [ ] Create Meta App at developers.facebook.com
- [ ] Add Messenger product
- [ ] Generate Page Access Token → Railway `PAGE_ACCESS_TOKEN`
- [ ] Subscribe app to the Facebook Page
- [ ] Configure webhook URL: `https://<railway-domain>/webhook`
- [ ] Set Verify Token → Railway `VERIFY_TOKEN`, must match exactly
- [ ] **Enable subscriptions: `messages`, `messaging_postbacks`, `messaging_handovers`** — all three required; missing `messaging_handovers` silently breaks agent-resume
- [ ] Set Get Started button payload (`GET_STARTED`) via Messenger Profile API
- [ ] Configure Handover Protocol: bot = Primary Receiver, Page Inbox (or CRM) = Secondary Receiver
- [ ] Confirm `PAGE_INBOX_APP_ID` in Railway matches the Secondary Receiver's app ID

### Railway Setup
- [ ] New Railway project + service
- [ ] Add env vars: `PAGE_ACCESS_TOKEN`, `VERIFY_TOKEN`, `APP_SECRET`, catalog path, `PAGE_INBOX_APP_ID` (if not default)
- [ ] GitHub repo secrets/variables: `RAILWAY_TOKEN` (secret), `RAILWAY_SERVICE` (variable), `RAILWAY_ENVIRONMENT` (variable)
- [ ] GitHub repo Settings → Environments → create `production` (add required reviewer for approval gate if wanted)

### Privacy Policy
The existing `privacy-policy.html` is CCF-branded and written for a church onboarding context.
For a commercial bot capturing names and mobile numbers in the Philippines, the **Data Privacy Act
(RA 10173)** requires a privacy policy that covers commercial data use, retention, and disclosure.
This is legal work — do not copy the existing policy and change the logo. Have it reviewed or
drafted for the business before launch.

---

## Infrastructure Reuse — CI/CD

`.github/workflows/deploy.yml` is fully generic. After repo setup:

```bash
git tag -a v0.1.0 -m "release: initial production release"
git push origin v0.1.0
```

This triggers: ancestry check → changelog → GitHub Release → `railway up` deploy.

---

## Realistic Effort Estimate

| Area | Estimate | Notes |
|---|---|---|
| Repo setup + infra copy | 2–4 hours | Copy files, update names, configure Railway + GitHub secrets |
| FB app setup + webhook verification | 0.5–1 day | Meta console, Page subscription, handover protocol |
| Privacy policy (commercial) | 0.5 day | Legal review or draft — do not skip |
| `send_quick_replies()` in `facebook.py` | 2–3 hours | New primitive + tests |
| Vehicle profiling (make → model → year) | 2–3 days | Quick Replies per make, free-text year validation, fallback handling |
| Parts catalog CSV design + lookup logic | 2–3 days | Schema design, data entry, `catalog.py`, caching, no-match handling |
| Catalog result + quote/inquiry flow | 1 day | |
| Image attachment handler | 1 day | `app.py` webhook branch + handoff |
| Mobile capture + wind-down (reuse) | 2–3 hours | |
| Durable state store (Redis/SQLite) | 1–2 days | If session loss is not acceptable |
| Tests | 1–2 days | Reuse test scaffolding from `tests/`; `conftest.py` patterns are directly portable |
| **Total** | **~10–14 days** | 5–6 days only if cutting: no image handling, no durable state, free-text vehicle entry, no real pricing |
