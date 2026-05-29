# onboarding-fb (cb-onboarding) — Value Handoff

**Status:** 🟢 Shipped  (Idea → Prototype → Built (local) → Deployed → Shipped)
**One-liner:** A Facebook Messenger chatbot that onboards new visitors into the right CCF Imus D-Group through a button-driven flow, with seamless handoff to a human facilitator.
**Last updated:** 2026-05-29

> Status ladder:
> - ⚪ Idea — concept only
> - 🔵 Prototype — partial, throwaway
> - 🟡 Built (local) — works, runs on dev machine only
> - 🟠 Deployed — live on a host, no real consumer yet
> - 🟢 Shipped — deployed AND a real consumer ingesting the backend (e.g. FB Page webhook)

## 💰 Commercial Value
- **Problem & who has it:** Organizations that get inbound interest via their Facebook Page can't respond to and qualify every visitor by hand. CCF Imus has this problem for D-Group onboarding — and it's live, solving it now.
- **Who pays / willingness to pay:** Current deployment is for a ministry (internal use, non-commercial). The commercial value is the proven, reusable engine: PH SMBs that sell/recruit through FB Messenger would pay for the same "auto-qualify and route leads" capability.
- **Market (PH / SEA SMB angle):** Strong fit. FB Messenger is the default storefront/inbox for PH small businesses (Marketplace, online selling). A button-driven qualify-then-handoff bot maps directly to lead capture for sellers, clinics, schools, real estate, etc.
- **Differentiation:** Button-driven happy path (no fragile free-text parsing), privacy-gate before data collection, PH mobile validation, and proper human handoff via Facebook's handover protocol with auto-resume. It's a real, shipped flow — not a demo.
- **Path to revenue & current commercial status:** Live for one non-paying org (CCF Imus). Nearest revenue step: repackage the flow engine as a configurable lead-qualifier for paying SMBs (multi-page, multi-flow). The shipped deployment is strong proof it works in production.
- **Cost to run (margin signal):** Low — single Railway service + Facebook Graph API (free tier covers messaging). Cheap to run per page; healthy margin if sold as a managed service.

## 🛠 Tech Value
- **What's built:** Production FastAPI Messenger bot — full demographic + availability onboarding flow, CSV-driven D-Group schedule matching, HMAC-SHA256 webhook signature verification, human handoff via pass-thread-control with bot auto-resume, and a health endpoint. pytest suite with mocked FB calls.
- **Deployment & consumer:** 🟢 Live. Hosted on **Railway**; a real **CCF Imus Facebook Page** is wired to the `/webhook` endpoint and real visitors are going through the flow. Tag-triggered CI/CD (`v*` tag → GitHub Release → Railway deploy); `v0.1.0` released.
- **Reusable assets / technical moat:** The conversation-flow engine (step handlers + dispatch router + per-user state), FB Graph API wrapper, signature verification, and the tag-triggered Railway deploy pipeline are all reusable — already being mined for other bots (e.g. an autoparts trading bot handoff). Moat is execution speed + a working FB integration, not IP.
- **Risks & what's NOT done:** In-memory per-user state (lost on restart/redeploy) — fine for short flows, a risk at scale. `PAGE_ACCESS_TOKEN` expiry needs manual rotation. Single satellite/flow hardcoded via CSV; not yet multi-tenant or self-serve configurable.
- **Scale readiness:** One page, one flow today. To serve paying SMBs needs persistent state (DB), per-tenant config/flows, and a dashboard. Deploy pipeline and FB integration are already production-grade — the gap is multi-tenancy, not infra.

## 📈 Progress Log
- **2026-05-29** — First value handoff created. Status: Shipped — live on Railway with a real CCF Imus FB Page and real users going through the onboarding flow. CI/CD via tag-triggered Railway deploy (`v0.1.0` released). Reusable flow engine + FB integration + deploy pipeline already being reused for other bots. Biggest gap to a paid SMB product: multi-tenancy and persistent state.
