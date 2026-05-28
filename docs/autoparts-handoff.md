# Autoparts Trading Bot — Handoff from onboarding-fb

This document maps reusable components from the CCF onboarding bot to an Autoparts Trading FB Messenger bot. The goal is to avoid rebuilding proven infrastructure and focus effort on domain-specific logic.

---

## What to Copy Verbatim

These files are completely domain-agnostic — copy them into the new repo unchanged.

| File | What it provides |
|---|---|
| `app.py` | FastAPI webhook GET/POST, HMAC-SHA256 signature verification, health check at `/`, privacy policy route pattern |
| `facebook.py` | `send_message`, `send_buttons`, `send_carousel`, `fetch_user_name`, `handoff_to_human` — all Graph API calls |
| `config.py` | Env var loading via `Config` class |
| `state.py` | In-memory per-user state store (`get` / `update` / `reset`) |
| `procfile` | Railway startup command |
| `.github/workflows/deploy.yml` | Tag-triggered CI/CD pipeline → GitHub Release → Railway deploy |
| `.env.example` | Env var documentation template |
| `pytest.ini` | Test config |
| `requirements.txt` | Base deps (FastAPI, uvicorn, requests, pytest, httpx, pandas, python-dotenv) |

---

## What to Refactor (Keep the Pattern, Replace the Content)

### 1. `flow.py` — Conversation Engine

**Keep:**
- `dispatch()` + `HANDLERS` dict pattern — this is the entire routing engine, works for any flow
- `_normalize()` — strips `/` prefix and lowercases payloads
- `handle_handoff()` + `handle_paused()` — human handoff and agent resume, copy exactly
- Privacy policy gate (`handle_start` + `handle_privacy`) — replace the URL and copy text only
- Wind-down pattern (`_show_wind_down` + `handle_wind_down`) — replace button labels and copy
- Mobile number collection + PH validation (`_MOBILE_RE`, `handle_collect_mobile`, `handle_mobile_prompt`) — customer contact capture, reuse as-is

**Replace:**
- All CCF-specific handlers: `handle_membership`, `handle_invite`, `handle_age_group`, `handle_life_stage_*`, `handle_gender`, `handle_generation_old`, `handle_availability_*`, `handle_preferred_time`
- State fields: swap out `age_group`, `marital_status`, `life_stage`, `availability_day`, `preferred_time` for autoparts-specific fields (see below)

### 2. `state.py` — User State Fields

Replace `_default_state()` fields with autoparts equivalents:

```python
def _default_state() -> dict[str, Any]:
    return {
        "step": "start",
        "first_name": "",
        "last_name": "",
        "mobile_number": "",
        "inquiry_type": "",       # parts / labor / both
        "vehicle_make": "",       # Toyota, Honda, Mitsubishi, etc.
        "vehicle_model": "",      # Vios, Civic, etc.
        "vehicle_year": "",       # 2018, 2019, etc.
        "part_category": "",      # engine, brakes, suspension, electrical, body
        "part_description": "",   # free-text or specific part name
        "branch": "",             # if multi-branch
    }
```

### 3. `schedule.py` → `catalog.py` or `inventory.py`

The CSV lookup pattern (`load_schedule` → `find_schedule`) maps directly to parts catalog lookup. Refactor to:

```python
def find_parts(
    vehicle_make: str,
    vehicle_model: str,
    vehicle_year: str,
    part_category: str,
) -> str:
    """Return matching parts from catalog CSV, or empty string if not found."""
```

CSV columns would be: `make, model, year_from, year_to, category, part_name, part_number, price, availability`

---

## New Flows to Build

These have no equivalent in the CCF bot and need to be written from scratch.

| Flow | Steps |
|---|---|
| **Vehicle profiling** | Make → Model → Year (cascading button menus, ~3 steps) |
| **Inquiry type** | Parts only / Labor / Both → branches into different paths |
| **Part category** | Engine / Brakes / Suspension / Electrical / Body / Other |
| **Parts lookup result** | Show matched parts with price + availability; offer "Add to inquiry" or "Talk to staff" |
| **Branch selection** | If multi-location: show branch buttons before wind-down |
| **Quick quote vs full order** | Quick quote (just price info, no contact) vs full inquiry (captures mobile, hands off to staff) |

---

## Suggested New Conversation Flow

```
GET_STARTED
    └─► Privacy policy
            └─► Inquiry type (Parts / Labor / Both)
                    └─► Vehicle make
                            └─► Vehicle model
                                    └─► Vehicle year
                                            └─► Part category
                                                    └─► Parts lookup result
                                                            ├─► Get a quote → mobile number → wind-down → handoff
                                                            ├─► Need help choosing → handoff to staff
                                                            └─► Just browsing → done
```

---

## Infrastructure Reuse

The CI/CD pipeline, Railway deploy, and GitHub Actions setup are **fully reusable**. For the new repo:

1. Create new Railway project and service
2. Add the same GitHub secrets/variables (`RAILWAY_TOKEN`, `RAILWAY_SERVICE`, `RAILWAY_ENVIRONMENT`)
3. Copy `.github/workflows/deploy.yml` — no changes needed
4. Cut a `v0.1.0` tag to trigger the first deploy

---

## Estimated Build Effort

| Area | Effort |
|---|---|
| Infrastructure setup (copy verbatim) | 1–2 hours |
| Vehicle profiling flow (make/model/year) | 1 day |
| Parts catalog CSV + lookup logic | 1–2 days |
| Parts result + quote flow | 1 day |
| Mobile capture + handoff (reuse) | 2 hours |
| Tests | 1 day |
| **Total** | **~5–6 days** |
