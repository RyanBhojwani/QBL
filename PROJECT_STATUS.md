# Quant Bet Labs — Project Status

_Last updated: 2026-05-07_

---

## Current State: Phases 0–6 Complete — Full Stack Live on Vercel + Railway

The entire core product is built and deployed. The Python worker runs on Railway every 15 minutes, finds +EV picks, posts to Discord, and writes to Supabase. The Next.js frontend is live on Vercel at **https://quantbetlabs.vercel.app**. Clerk handles auth with tier gating. Stripe handles billing and automatically sets user tiers in Clerk on payment. Everything is currently in **Stripe test mode** — must be switched to live mode before taking real payments.

---

## ⚠️ IMPORTANT: Stripe Test Mode

**Stripe is currently in test mode.** All purchases use fake test cards. No real money is being collected.

**Before launching to real users:**
1. Complete Stripe account activation (business info, bank account, etc.)
2. Re-create the 3 products (Basic/Premium/VIP) in Stripe **live mode**
3. Swap all Stripe env vars on Vercel to live mode keys (`pk_live_`, `sk_live_`)
4. Update `NEXT_PUBLIC_STRIPE_PRICE_BASIC/PREMIUM/VIP` to live mode price IDs
5. Create a new webhook endpoint in Stripe live mode pointing to the same URL
6. Update `STRIPE_WEBHOOK_SECRET` on Vercel to the live mode signing secret
7. Update `.env.local` if testing locally against live mode
8. Verify a real purchase end-to-end before announcing

---

## Phase Status

| Phase | Status | Completed |
|-------|--------|-----------|
| 0 — Docs | ✅ Complete | 2026-04-30 |
| 0.5 — v2 Engine | ✅ Complete | 2026-05-01 |
| 1 — Supabase Schema | ✅ Complete | 2026-05-05 |
| 2 — Python Write Layer | ✅ Complete | 2026-05-05 |
| 3 — Railway Deployment | ✅ Complete | 2026-05-05 |
| 4 — Next.js Scaffold | ✅ Complete | 2026-05-05 |
| 5 — Auth & Tiers | ✅ Complete | 2026-05-07 |
| 6 — Billing | ✅ Complete (test mode) | 2026-05-07 |
| 7 — Results Page | ⬜ Not started | — |
| 8 — Discord Links | ⬜ Not started | — |
| 9 — Admin Config Panel | ⬜ Not started | — |
| 10 — Picks Filtering & Preferences | ⬜ Not started | — |
| 11 — Snapshot Pipeline | ⬜ Not started | — |
| 12 — ML Retraining | ⬜ Not started | — |
| 13 — Content Pass | ⬜ Not started | — |
| 14 — Stripe Live Mode | ⬜ Not started | — |
| 15 — Security Audit | ⬜ Not started | — |
| 16 — Mobile QA | ⬜ Not started | — |
| 17 — Deployment Docs | ⬜ Not started | — |

---

## What Exists

### Python Engine (Railway Worker)

| Component | File | Status |
|-----------|------|--------|
| Odds fetching, devig, EV/Kelly (v1) | `Original_Code/odds_engine.py` | ✅ Untouched reference |
| Per-book EV expansion (v2) | `Original_Code/odds_engine_v2.py` | ✅ Active engine |
| Board assembly + ML filtering (v1) | `Original_Code/run_edge_board.py` | ✅ Untouched reference |
| Board assembly wired to v2 engine | `Original_Code/run_edge_board_v2.py` | ✅ Active orchestrator |
| Long-running scheduler | `Original_Code/bet_scheduler7.py` | ✅ Running on Railway |
| Daily settlement | `Original_Code/settle_ledger.py` | ✅ Supabase write wired |
| Supabase write adapter | `Original_Code/supabase_writer.py` | ✅ Bug fixed: always DELETEs current_picks even when output is empty |
| Devig curve coefficients | `mappings/` | ✅ Present |
| Serialized ML models | `models/` | ✅ Present |

### Supabase

| Component | Status |
|-----------|--------|
| `model_runs` table | ✅ Live |
| `current_picks` table | ✅ Live — updated every 15 min by Railway |
| `tracked_picks` table | ✅ Live |
| `settled_picks` table | ✅ Live |
| `upsert_tracked_picks_batch` RPC | ✅ Live |
| Realtime publication on `current_picks` | ✅ Enabled |
| Anon read RLS policy on `current_picks` | ✅ Applied |

### Frontend (Vercel — https://quantbetlabs.vercel.app)

**Public pages:**

| Page | Route | Status |
|------|-------|--------|
| Landing page | `/` | ✅ Live |
| Pricing page | `/pricing` | ✅ Live — Stripe checkout wired |
| Performance | `/performance` | ✅ Live (placeholder content) |
| How It Works | `/how-it-works` | ✅ Live |
| FAQ | `/faq` | ✅ Live |
| Rules | `/rules` | ✅ Live |

**Dashboard pages (auth-gated):**

| Page | Route | Status |
|------|-------|--------|
| Picks | `/dashboard/picks` | ✅ Live — real-time picks, tier-filtered |
| Performance | `/dashboard/performance` | ✅ Live (placeholder) |
| Education | `/dashboard/education` | ✅ Live — premium/vip only |
| How To Use | `/dashboard/how-to-use` | ✅ Live — premium/vip only |
| FAQ | `/dashboard/faq` | ✅ Live |
| Account | `/dashboard/account` | ✅ Live — tier display + Manage Subscription |

**API routes:**

| Route | Purpose | Status |
|-------|---------|--------|
| `POST /api/checkout` | Creates Stripe Checkout Session | ✅ Live |
| `POST /api/webhooks/stripe` | Handles Stripe events → updates Clerk tier | ✅ Live |
| `POST /api/portal` | Opens Stripe Customer Portal | ✅ Live |

### Auth (Clerk)

- Clerk v7 integrated throughout
- `proxy.ts` middleware protects all `/dashboard/*` routes
- Tier stored in `publicMetadata.tier`: `"basic"` | `"premium"` | `"vip"` | `null`
- Tier enforcement: server-side query filter (`.lte("stars", maxStars)`)
- After sign-in → `/dashboard/picks`
- After sign-up → `/pricing`
- After sign-out → `/`
- No tier = upgrade wall on picks page with link to `/pricing`

### Billing (Stripe — TEST MODE)

| Item | Value |
|------|-------|
| Mode | **TEST MODE** — no real payments |
| Basic price ID | `price_1TUdZa6hx2fDbpp0SRrKxYs0` |
| Premium price ID | `price_1TUdaQ6hx2fDbpp0RcZy7F5g` |
| VIP price ID | `price_1TUdae6hx2fDbpp0lmwo8IzS` |
| Webhook endpoint | `https://quantbetlabs.vercel.app/api/webhooks/stripe` |
| Webhook events | `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted` |
| Customer portal | Enabled — users can cancel/upgrade from Account page |
| Tier mapping | Basic → `tier: "basic"`, Premium → `tier: "premium"`, VIP → `tier: "vip"` |
| Cancellation | Clears `tier` in Clerk → picks page shows upgrade wall |

---

## Tier Structure

| Tier | Price | Dashboard access | Education |
|------|-------|-----------------|-----------|
| None (no subscription) | — | Upgrade wall | No |
| Basic | $25/mo | 1–2★ picks | No |
| Premium | $50/mo | 1–4★ picks | Yes |
| VIP | $100/mo | 1–5★ picks (all) | Yes |

---

## Environment Variables

### Next.js (Vercel + `.env.local`)

```
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
CLERK_SECRET_KEY
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard/picks
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/pricing
NEXT_PUBLIC_CLERK_AFTER_SIGN_OUT_URL=/
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY        ← test mode key
STRIPE_SECRET_KEY                          ← test mode key
NEXT_PUBLIC_STRIPE_PRICE_BASIC
NEXT_PUBLIC_STRIPE_PRICE_PREMIUM
NEXT_PUBLIC_STRIPE_PRICE_VIP
STRIPE_WEBHOOK_SECRET                      ← test mode whsec_
NEXT_PUBLIC_APP_URL
```

### Python Worker (Railway)

```
ODDS_API_KEY, DISCORD_WEBHOOK_*, DISCORD_TOKEN
SUPABASE_ENABLED=1, SUPABASE_URL, SUPABASE_SERVICE_KEY
DATA_DIR=/data, ACTIVE_SPORTS, DAY_POLL_MINUTES, NIGHT_POLL_MINUTES
LEAGUES_BASEBALL, LEAGUES_HOCKEY, LEAGUES_NBA, LEAGUES_SOCCER, LEAGUES_FIGHTS
```

---

## Immediate Next Steps

| Priority | Phase | Task |
|----------|-------|------|
| 1 | 7 | Build results/performance page using `settled_picks` — first verify table has data |
| 2 | 8 | Discord links — swap all `href="#"` with real invite URL (quick) |
| 3 | 9 | Admin config panel — toggle sports + poll intervals from dashboard UI |
| 4 | 10 | Picks filtering — sport/market/book/stars filters + persistent user preferences |
| 5 | 11 | Snapshot pipeline — auto-upload to Supabase Storage + nightly local download |
| 6 | 12 | ML retraining workflow — document + automate deployment of updated models |
| 7 | 13 | Content pass — real copy on all public pages |
| 8 | 15 | Security audit — before going live |
| 9 | 16 | Mobile QA — before going live |
| 10 | 14 | Stripe live mode — after security + mobile sign-off |
| 11 | 17 | Deployment docs / runbook |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-04-30 | Created planning docs, extracted `run_once()`, created v2 engine |
| 2026-05-01 | v2 board orchestrator, scheduler wired to v2, dedup fixes, test suite (19/19) |
| 2026-05-05 | Supabase schema (4 tables), Python write layer (35/35 tests), Railway deployment |
| 2026-05-05 | Next.js scaffold, landing page, picks page with Realtime, all public + dashboard pages |
| 2026-05-07 | Clerk v7 auth integrated — tier gating, route protection, sign-in/sign-up flow |
| 2026-05-07 | Stripe billing integrated — checkout, webhook, portal, Clerk tier sync (test mode) |
| 2026-05-07 | Deployed to Vercel at https://quantbetlabs.vercel.app |
| 2026-05-07 | Fixed `supabase_writer.py` stale picks bug — DELETE always runs even when output is empty |
