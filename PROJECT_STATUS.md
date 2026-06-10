# Quant Bet Labs — Project Status

_Last updated: 2026-06-10_

---

## Current State: Phases 0–10 Complete — Full Stack Live on Vercel + Railway

The entire core product is built and deployed. The Python worker runs on Railway every 15 minutes, finds +EV picks, posts to Discord, and writes to Supabase. A nightly 4:30 AM job computes performance metrics and stores them in `model_results`. The Next.js frontend is live on Vercel at **https://quantbetlabs.vercel.app**. Clerk handles auth with tier gating and proper route protection. Stripe handles billing and automatically sets user tiers in Clerk on payment. Everything is currently in **Stripe test mode** — must be switched to live mode before taking real payments.

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
| 7 — Results Page | ✅ Complete | 2026-05-08 |
| 8 — Discord Links | ✅ Complete | 2026-05-08 |
| 9 — Admin Config Panel | ✅ Complete | 2026-05-08 |
| 10 — Picks Filtering & Preferences | ✅ Complete | 2026-05-08 |
| 10.5 — Bug Fixes & Navigation Audit | ✅ Complete | 2026-06-09 |
| 11 — Snapshot Pipeline | ✅ Complete | 2026-06-10 |
| 12 — ML Retraining | ⬜ Not started | — |
| 12.5 — UX Audit & Improvements | ⬜ Not started | — |
| 12.7 — Legal & Compliance | ⬜ Not started | — |
| 13 — Content Pass | ⬜ Not started | — |
| 13.5 — Marketing & SEO | ⬜ Not started | — |
| 14 — Stripe Live Mode | ⬜ Not started | — |
| 14.5 — Discord Role Sync | ⬜ Not started | — |
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
| Long-running scheduler | `Original_Code/bet_scheduler7.py` | ✅ Running on Railway; fires results calc at 4:30 AM ET |
| Daily settlement | `Original_Code/settle_ledger.py` | ✅ Supabase write wired |
| Nightly results calculator | `Original_Code/results_calculator.py` | ✅ Computes all metrics, upserts to `model_results` |
| Supabase write adapter | `Original_Code/supabase_writer.py` | ✅ Includes `load_settled_picks()` + `write_model_results()` |
| Devig curve coefficients | `mappings/` | ✅ Present |
| Serialized ML models | `models/` | ✅ Present |

### Supabase

| Component | Status |
|-----------|--------|
| `model_runs` table | ✅ Live |
| `current_picks` table | ✅ Live — updated every 15 min by Railway |
| `tracked_picks` table | ✅ Live |
| `settled_picks` table | ✅ Live — 6,400+ rows |
| `model_results` table | ✅ Live — ~66 rows, upserted nightly at 4:30 AM ET |
| `upsert_tracked_picks_batch` RPC | ✅ Live |
| Realtime publication on `current_picks` | ✅ Enabled |
| Anon read RLS on `current_picks` | ✅ Applied |
| Anon read RLS on `model_results` | ✅ Applied |
| `user_preferences` table | ✅ Live — keyed by Clerk user ID, RLS enabled, service key access only |
| `worker_config` table | ✅ Live — key/value config read by Railway worker each poll cycle; RLS enabled |

### Frontend (Vercel — https://quantbetlabs.vercel.app)

**Public pages:**

| Page | Route | Status |
|------|-------|--------|
| Landing page | `/` | ✅ Live |
| Pricing page | `/pricing` | ✅ Live — Stripe checkout wired |
| Performance | `/performance` | ✅ Live — real data; All-Time/30d/Yesterday overview + modal; breakdown tables locked behind subscribe CTA |
| How It Works | `/how-it-works` | ✅ Live |
| FAQ | `/faq` | ✅ Live |
| Rules | `/rules` | ✅ Live |

**Dashboard pages (auth-gated):**

| Page | Route | Status |
|------|-------|--------|
| Picks | `/dashboard/picks` | ✅ Live — real-time picks, tier-filtered, sport/book/stars filters with persistent user preferences |
| Performance | `/dashboard/performance` | ✅ Live — full performance dashboard with all data |
| Education | `/dashboard/education` | ✅ Live — premium/vip only; upgrade wall distinguishes unsubscribed from basic |
| How To Use | `/dashboard/how-to-use` | ✅ Live — premium/vip only; upgrade wall distinguishes unsubscribed from basic |
| FAQ | `/dashboard/faq` | ✅ Live |
| Account | `/dashboard/account` | ✅ Live — tier display + Manage Subscription; Sign Out correctly ends Clerk session |
| Admin | `/dashboard/admin` | ✅ Live — poll cadence, sport/league toggles; visible only to ADMIN_EMAIL |

**API routes:**

| Route | Purpose | Status |
|-------|---------|--------|
| `POST /api/checkout` | Creates Stripe Checkout Session | ✅ Live — validates priceId against known prices before calling Stripe |
| `POST /api/webhooks/stripe` | Handles Stripe events → updates Clerk tier | ✅ Live |
| `POST /api/portal` | Opens Stripe Customer Portal | ✅ Live |
| `GET /api/preferences` | Load user filter preferences | ✅ Live |
| `POST /api/preferences` | Save user filter preferences | ✅ Live — star values clamped to 1–5 |
| `GET /api/admin/config` | Load worker config (admin only) | ✅ Live |
| `POST /api/admin/config` | Save worker config (admin only) | ✅ Live |

### Middleware & Auth

| Component | File | Status |
|-----------|------|--------|
| Clerk route protection | `app/middleware.ts` | ✅ Live — protects all `/dashboard/*` routes; unauthenticated users are redirected to sign-in |

### Performance Dashboard (Phase 7 detail)

Both `/dashboard/performance` and `/performance` are powered by pre-computed data in `model_results`. No live computation on the frontend.

**Time window overview (all three pages):**
- All-Time, Past 30 Days, Yesterday rows — each showing: Number of Bets, Real ROI, Expected ROI, Win Rate, Annualized Return
- "View Detailed Statistics" button under All-Time and Past 30 Days opens a full modal

**Detail modal:**
- 5 summary cards in 3+2 centered layout
- Bankroll curve chart (Recharts, SSR-safe via `next/dynamic`) — starts Y-axis above $0, solid white $1,000 break-even line
- Win/Loss Record section: Record W-L-P, Win Rate, Avg Odds, Break-Even Win Rate, Picks with CLV, CLV Win Rate
- Returns and Profit section: Real ROI + Profit, CLV ROI + Profit, EV ROI + Profit (profit displayed as units ×100)
- Financial Statistics section: CAGR, Bankroll Return, Max Drawdown, Volatility, Sharpe Ratio, Sortino Ratio

**Breakdown tables (dashboard only):**
- By Star Rating, By Sport, By Sport and Market
- Each table has an independent All-Time / Past 30 Days toggle
- Clicking any row opens the detail modal for that segment + window
- Columns: Name, # Bets, Real ROI, Exp. ROI, Ann. Return, Win Rate

**Data pipeline:**
- `results_calculator.py` runs at 4:30 AM ET daily (after 4 AM settlement)
- Deduplicates `settled_picks` on `(game_id, market, team)` — keeps earliest `found_at`
- Computes metrics across 3 time windows × 5 segment types = ~66 rows
- Sport normalization: all `soccer_*` → `soccer`, all `baseball_*` → `baseball`, `mma` → `mma_mixed_martial_arts`
- Bankroll metrics use daily compounding from $1,000 starting bankroll at half-Kelly sizing
- `daily_curve` stored as native JSONB array (not double-encoded string)

### Auth (Clerk)

- Clerk v7 integrated throughout
- `middleware.ts` protects all `/dashboard/*` routes — unauthenticated users are redirected to sign-in (not just shown an upgrade wall)
- Tier stored in `publicMetadata.tier`: `"basic"` | `"premium"` | `"vip"` | `null`
- Tier enforcement: server-side query filter (`.lte("stars", maxStars)`)
- After sign-in → `/dashboard/picks`
- After sign-up → `/pricing`
- After sign-out → `/` (Clerk `signOut()` called — session is properly terminated)
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

| Tier | Price | Dashboard access | Education / How To Use |
|------|-------|-----------------|------------------------|
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
ADMIN_EMAIL
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
| 1 | 10.5 | ✅ Complete — Stripe redirect fixed, custom 404 wired, post-purchase success banner wired, nav unified (single auth-aware nav, More dropdown, How To Use public at /how-to-use) |
| 2 | 12 | ML retraining workflow — document + automate deployment of updated models |
| 3 | 12 | ML retraining workflow — document + automate deployment of updated models |
| 4 | 12.5 | UX audit — onboarding, picks table tooltips, empty/error/loading states, account detail, upgrade wall clarity |
| 5 | 12.7 | Legal & compliance — ToS page, Privacy Policy page, disclaimers, 18+ notice, geo-disclaimer, FTC compliance on performance claims |
| 6 | 13 | Content pass — real copy and accurate stats on all public pages (informed by UX + legal) |
| 7 | 13.5 | Marketing & SEO — meta tags, OG images, sitemap, analytics, social proof audit |
| 8 | 14 | Stripe live mode — after security + mobile sign-off |
| 9 | 14.5 | Discord role sync — replace Whop; wire Stripe/Clerk tiers to Discord roles via bot + OAuth |
| 10 | 15 | Security audit — covers all routes including new Discord OAuth endpoints |
| 11 | 16 | Mobile QA — before going live |
| 12 | 17 | Deployment docs / runbook |

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
| 2026-05-08 | Phase 7 complete: `results_calculator.py`, `model_results` table, full performance dashboard |
| 2026-05-08 | Performance modal: bankroll chart, win/loss record, returns/profit, financial statistics |
| 2026-05-08 | Breakdown tables with per-table All-Time/30d toggle; public `/performance` page with modal |
| 2026-05-08 | Fixed: NCAAB rows deleted, sport normalization, JSONB double-encoding, MMA dedup, RLS policy |
| 2026-05-08 | Phase 8 complete: all Discord CTA buttons wired to real invite URL via `lib/constants.ts` |
| 2026-05-08 | Phase 9 complete: `/dashboard/admin` config panel — poll cadence, sport/league toggles |
| 2026-05-08 | Phase 10 complete: picks filter bar (Sport/Book/Stars dropdowns), persistent user preferences |
| 2026-05-19 | Fixed: `proxy.ts` renamed to `middleware.ts` — Clerk route protection now actually runs |
| 2026-05-19 | Fixed: Sign Out on Account page and mobile nav now calls Clerk `signOut()` properly |
| 2026-05-19 | Fixed: Tier descriptions were reversed on 4 pages (Basic/Premium/VIP star ranges) |
| 2026-05-19 | Fixed: Stale placeholder copy removed from dashboard FAQ ("coming in Phase 6") |
| 2026-05-19 | Fixed: ESPN Bet (shut down 2025) removed from FAQ sportsbook list |
| 2026-05-19 | Fixed: Education and How To Use upgrade walls now distinguish no-subscription from basic |
| 2026-05-19 | Fixed: `/api/checkout` now validates `priceId` against known Stripe prices before calling Stripe |
| 2026-05-19 | Fixed: `/api/preferences` now clamps `min_stars`/`max_stars` to valid 1–5 range |
| 2026-05-19 | Fixed: Star Rating glossary in Education correctly describes all three tier access levels |
| 2026-06-02 | Added phases 10.5 (Bug Fixes & Nav), 12.5 (UX Audit), 12.7 (Legal & Compliance), 13.5 (Marketing & SEO) to plan |
| 2026-06-02 | Phase 10.5 partial: custom 404 page (`app/not-found.tsx`), post-purchase success banner (`components/SuccessBanner.tsx`) |
| 2026-06-02 | Added Phase 14.5 (Discord Role Sync) — replaces Whop; Stripe/Clerk tiers drive Discord role assignment via bot + OAuth |
| 2026-06-09 | Fixed: Stripe success_url/cancel_url now falls back to `new URL(req.url).origin` if `NEXT_PUBLIC_APP_URL` is unset on Vercel |
| 2026-06-09 | Confirmed: `not-found.tsx` and `SuccessBanner.tsx` are correctly wired — 404 auto-renders via App Router, banner shows on `?success=1` after checkout |
| 2026-06-10 | Phase 11 complete: R2 snapshot pipeline fully verified — Railway uploads YYYYMMDD.parquet to R2 at 4:15 AM ET; Windows Task Scheduler pulls to `./snapshots/` at 9 AM and clears R2; historical backfill uploaded via `RUN_SNAPSHOT_BACKFILL` env var trigger |
| 2026-06-10 | Fixed Railway crash: cross-platform pkl load shim in `bet_scheduler7.py` (Windows `_loss` → `sklearn._loss._loss` on Linux) |
| 2026-06-09 | Unified nav: `PublicNav.tsx` now handles both logged-out (Home/Performance/How to Use/Pricing/FAQ/Rules + Sign In/Get Started) and logged-in (Home/Current Picks/Performance/How to Use/Education/Pricing/More▾ + Account/UserButton) states; `DashboardLayout` simplified to use shared nav |
| 2026-06-09 | How To Use moved to public route `/how-to-use` (no auth required); `/dashboard/how-to-use` redirects there; `/how-it-works` no longer linked |
