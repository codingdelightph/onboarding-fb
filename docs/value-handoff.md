# onboarding-fb (cb-onboarding) — Value Handoff

> **Purpose:** Living progress tracker for the CCF Imus D-Group onboarding FB Messenger bot.
> Upload to the commercial tracker chat. Two lenses below: **Commercial Value** (what it
> earns / saves / de-risks for the business) and **Tech Value** (what's built and how solid it is).
>
> **Last updated:** 2026-05-29

---

## Release & Ship Status

Three distinct lifecycle states — do not conflate them. "Done in code" is not "shipped."

| State | Definition | How to verify | Current |
|---|---|---|---|
| **Built** | Code merged on `main`, tests passing. Not deployed. | `git log` on `main`, tests green | ✅ **Yes** — full flow on `main`, pytest suite (mocked FB calls) green |
| **Released (pipeline)** | A `v*` tag pushed → CI ran → deployed to host. Health endpoint responds. | CI green + `GET /` returns `{"service":"onboarding-fb"}` on Railway | ✅ **Yes** — `v0.1.0` cut; tag-triggered GitHub Actions → Railway deploy |
| **Shipped** | Released **and** a real consumer ingesting it (FB Page Live, real users reach it). | Non-tester messages the Page + gets a reply; events in Railway logs | ✅ **Yes** — live CCF Imus FB Page connected, real users going through the flow |

**Plain-language status today:** *Shipped.* Live on Railway with a real CCF Imus Facebook Page wired to the webhook; real visitors are completing the onboarding flow.

**Path to shipped:** ✅ already shipped. Next frontier is turning the proven engine into a **paid, multi-tenant** product for SMBs (see below).

---

## 1. Commercial Value

*What this delivers for the business — leads, time saved, risk reduced.*

### Value delivered so far
- **Auto-qualifies and routes inbound 24/7.** Profiles each visitor (age group, life stage, availability) and matches them to the right D-Group schedule, then hands warm cases to a human facilitator — no staff needed for the happy path. Live now.
- **No lost inquiries.** Button-driven flow + human handoff with auto-resume means Messenger inquiries get an instant, structured response instead of going cold.
- **Compliant data capture.** Privacy-policy gate before any personal data, with PH mobile validation.
- **Zero marginal cost per conversation** — single Railway service, Facebook Graph API free tier; scales at effectively flat cost.

### Value pending (next to unlock)
- [ ] **Multi-tenant productization.** Repackage the flow engine as a configurable lead-qualifier so paying SMBs can run their own page + flow. This is the path from "internal ministry tool" to revenue. *(Owner action: product decision + build.)*
- [ ] **Durable lead storage.** In-memory state is lost on redeploy — persist leads so none vanish mid-flow.
- [ ] **Lead reporting** — a "how many inquiries, for what, this week" view to prove ROI.

### Open commercial decisions
- First paying vertical for the SMB version — sellers, clinics, schools, real estate?
- Where leads should land — Page Inbox only, or CRM/spreadsheet export?
- Pricing — per page/month, per lead, or managed-service?

---

## 2. Tech Value

*What's actually built, how solid it is, and what's owed.*

### Built and working
- **Production conversation engine** (`flow.py`) — step handlers behind a single `dispatch()` router; full demographic + availability onboarding flow.
- **Schedule matching** — CSV-driven lookup mapping user profile → D-Group schedule.
- **Human handoff + agent-resume** (`facebook.py`) — FB pass-thread-control; bot auto-resumes after a human finishes.
- **Webhook security** — HMAC-SHA256 signature verification; forged/blank-secret requests rejected with 403.
- **Health endpoint** — `GET /` for Railway's probe.
- **CI/CD** — tag-triggered GitHub Actions (ancestry check + changelog + GitHub Release) → `railway up`. `v0.1.0` released.
- **Tests** — pytest suite with mocked Facebook API calls (no live network).

### Known tech debt / risks
- **In-memory per-user state** (`state.py`) — wiped on every Railway redeploy/scale-to-zero. *Fix: swap backing store to Redis/SQLite; interface stays identical.* Highest-priority pre-scale item.
- **`PAGE_ACCESS_TOKEN` expiry** needs manual rotation (FB invalidates it; surfaces as `OAuthException 190`).
- **Single satellite/flow** hardcoded via CSV — not yet multi-tenant or self-serve configurable.

### Tech next steps
- [ ] Durable state store (Redis/SQLite).
- [ ] Per-tenant config/flows (multi-tenancy).
- [ ] Admin/reporting dashboard for captured leads.

---

## Change Log

*Append a dated line each time this file is updated.*

- **2026-05-29** — Converted from root `VALUE_HANDOFF.md` to new 3-state format. Status: **Shipped** — live on Railway (`v0.1.0`, tag-triggered CI/CD) with a real CCF Imus FB Page and real users in the flow. Reusable flow/handoff/deploy assets already being mined for other bots. Biggest gap to a paid product: multi-tenancy + durable state.
