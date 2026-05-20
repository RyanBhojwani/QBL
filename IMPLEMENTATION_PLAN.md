# Quant Bet Labs — Implementation Plan

## Guiding Principle

This is a data-flow refactor. The Python model is a black box. We add outputs to the existing pipeline; we do not modify what the pipeline produces.

**Rule**: If a change touches `odds_engine.py`, the devig logic, or the filter thresholds in `run_edge_board.py` — stop and reconsider. That is out of scope.

---

## Phase Overview

| Phase | Name | Goal | Status |
|-------|------|------|--------|
| 0 | Docs | Planning documents complete | ✅ Done |
| 0.5 | v2 Engine | Per-book pipeline built and tested | ✅ Done |
| 1 | Supabase Schema | Tables created, RPC deployed | ✅ Done |
| 2 | Python Write Layer | Scheduler writes to Supabase alongside CSV | ✅ Done |
| 3 | Railway Deployment | Python worker running on Railway | ✅ Done |
| 4 | Next.js Scaffold | App exists, reads picks from Supabase | ✅ Done |
| 5 | Auth & Tiers | Clerk auth, tier-gated picks page | ✅ Done |
| 6 | Billing | Stripe checkout sets Clerk tier | ✅ Done (test mode) |
| 7 | Results Page | Ledger/performance display | ✅ Done |
| 8 | Discord Links | All CTA buttons wired to real invite URL | ✅ Done |
| 9 | Admin Config Panel | /dashboard/admin — poll cadence + sport/league toggles, Railway reads dynamically | ✅ Done |
| 10 | Picks Filtering | Sport/book/stars dropdowns + persistent user preferences | ✅ Done |
| 11 | Snapshot Pipeline | Daily snapshots auto-upload to Supabase Storage + nightly local download | ⬜ Not started |
| 12 | ML Retraining | Workflow for retraining models on accumulated data and deploying to Railway | ⬜ Not started |
| 13 | Content Pass | Replace placeholder copy with real marketing content and accurate stats | ⬜ Not started |
| 14 | Stripe Live Mode | Switch from test payments to real payments | ⬜ Not started |
| 15 | Security Audit | Harden all routes and inputs before public launch | ⬜ Not started |
| 16 | Mobile QA | All pages verified on iOS Safari and Android Chrome | ⬜ Not started |
| 17 | Deployment Docs | Comprehensive RUNBOOK.md | ⬜ Not started |

---

## Phases 0–10 — COMPLETE

All phases through picks filtering and admin config are fully implemented and live. See `PROJECT_STATUS.md` for the full breakdown of what was built, including all bug fixes applied on 2026-05-19.

---

## ⚠️ Pre-Launch Requirement: Stripe Live Mode

Stripe is currently in **test mode**. Before accepting real payments:

1. Activate Stripe account (business info + bank account)
2. Re-create Basic/Premium/VIP products in live mode
3. Swap all Stripe env vars on Vercel to live keys
4. Register new webhook endpoint in Stripe live mode
5. Update `STRIPE_WEBHOOK_SECRET` on Vercel
6. Test one real purchase end-to-end

---

## Phase 7 — Results Page ✅ COMPLETE

**What was built:**

**Backend — `Original_Code/results_calculator.py`** (new file):
- Loads all `settled_picks` from Supabase, deduplicates on `(game_id, market, team)` keeping earliest `found_at`
- Normalizes sports: `soccer_*` → `soccer`, `baseball_*` → `baseball`, `mma` → `mma_mixed_martial_arts`
- Computes metrics across 3 time windows (`all_time`, `30d`, `1d`) × 5 segment types (`overall`, `star`, `sport`, `market`, `sport_market`) = ~66 rows
- Metrics per row: n_picks/wins/losses/pushes, win_pct, avg_odds (kelly-weighted), ROI, total_profit_units, CLV metrics, EV metrics, bankroll compounding metrics (CAGR, Sharpe, Sortino, max drawdown, volatility), daily_curve JSONB array
- Upserts all rows to `model_results` table; table stays at ~66 rows forever
- Fires at 4:30 AM ET via daemon thread added to `bet_scheduler7.py`

**Supabase — `model_results` table** (new):
- ~66 rows, upserted nightly; anon read RLS policy applied
- `daily_curve` stored as native JSONB array (not string-encoded)

**`Original_Code/supabase_writer.py`** (modified):
- Added `load_settled_picks()` — paginated read of all settled_picks rows
- Added `write_model_results()` — upsert on `(time_window, segment_type, segment_val)`

**Frontend — `/dashboard/performance`** (full rebuild):
- Server page fetches all 66 `model_results` rows, passes to `PerformanceDashboard` client component
- Three time-window rows (All-Time, 30d, Yesterday): Number of Bets, Real ROI, Expected ROI, Win Rate, Annualized Return
- "View Detailed Statistics" button under All-Time and 30d opens detail modal
- Three breakdown tables (By Star Rating, By Sport, By Sport and Market) — each has independent All-Time/30d toggle; clicking any row opens detail modal for that segment
- Detail modal: 5 summary cards (3+2 layout), bankroll chart with $1k reference line, Win/Loss Record section, Returns and Profit section, Financial Statistics section

**Frontend — `/performance`** (public page):
- Same time-window overview with "View Detailed Statistics" modals
- Breakdown tables remain locked behind subscribe upsell overlay

**Key files:**
- `Original_Code/results_calculator.py` — nightly computation entry point
- `app/lib/performance.ts` — `ModelResult` type, `fetchModelResults()`, all formatters
- `app/components/PerformanceDashboard.tsx` — main dashboard client component
- `app/components/PerformanceModal.tsx` — detail modal with chart and all stat sections
- `app/components/BankrollChart.tsx` — Recharts line chart (SSR-safe via next/dynamic)
- `app/components/PublicPerformanceOverview.tsx` — public page client wrapper for modals

---

## Phase 8 — Discord Links ✅ COMPLETE

`DISCORD_INVITE_URL` constant defined in `lib/constants.ts` and imported across all pages. All Discord CTA buttons navigate to the real server.

---

## Phase 9 — Admin Config Panel ✅ COMPLETE

**Architecture:**
1. **Supabase `worker_config` table** — key/value store seeded with `day_poll_minutes`, `night_poll_minutes`, `active_sports`, `leagues_*`
2. **Worker change** — `fetch_remote_config()` in `bet_scheduler7.py` reads from this table each cycle, falls back to env vars
3. **`/dashboard/admin` page** — admin-gated (email check against `ADMIN_EMAIL` env var), shows toggles + inputs, saves via `/api/admin/config`
4. **`/api/admin/config` route** — verifies admin email server-side, writes to `worker_config` via service key

---

## Phase 10 — Picks Table Filtering & User Preferences ✅ COMPLETE

**Implemented:**
- Sport, Book, and Star Range filter dropdowns in `PicksTable.tsx`
- All filtering is client-side — picks fetched once, filtered in memory
- `user_preferences` table in Supabase keyed by Clerk user ID
- Preferences loaded on mount, saved via debounced POST to `/api/preferences` (600ms)
- Star values clamped and validated server-side (1–5)

---

## Phase 11 — Snapshot Pipeline

**Goal**: Daily Railway snapshots auto-upload to Supabase Storage and auto-download to your local machine — fully hands-off.

**Architecture:**
1. **Supabase Storage `snapshots` bucket** — private, service key only
2. **`upload_daily_snapshot(snap_dir)` in `supabase_writer.py`** — uploads yesterday's consolidated Parquet after 4 AM settlement; auto-deletes files older than 7 days from bucket
3. **`download_snapshots.py`** (repo root, runs locally) — lists bucket, downloads new files to `./snapshots/YYYYMMDD.parquet`, deletes from Supabase after download, logs to `./snapshots/download.log`
4. **Windows Task Scheduler** — runs `download_snapshots.py` nightly at 6:00 AM; one-time setup, fully automated thereafter

**Storage budget:** ~5–20 MB/day × 7 days = 35–140 MB max in Supabase at any time. Local accumulation is unbounded (intended for retraining).

**Done when:** Task Scheduler fires at 6 AM, snapshot appears locally, disappears from Supabase.

---

## Phase 12 — ML Model Retraining & Redeployment

**Goal**: Establish the workflow for retraining models on accumulated snapshot data and deploying updated files to Railway.

**Workflow:**
1. Snapshots accumulate locally via Phase 11
2. Run retraining script (to be written separately) against `./snapshots/`
3. Updated `.pkl` and `.json` files written to `models/`
4. `git add models/ && git commit && git push` → Railway auto-redeploys
5. New models active on next poll cycle

**Key files:** `models/sigma_tweedie.pkl`, `models/logit_bag.pkl`, `models/clv_meta.json`, `models/sigma_design.json`

**Done when:** Updated `.pkl` files pushed to GitHub, Railway redeploys, new model behavior confirmed.

---

## Phase 13 — Content Pass

**Goal**: Replace placeholder/hardcoded content with accurate, real marketing copy.

**Known items:**
- Landing page stats (Alerts Sent, Leagues Covered) are hardcoded — should pull real numbers or be manually verified
- All public page copy should be reviewed for accuracy and tone

**Pages:** `/`, `/how-it-works`, `/performance`, `/pricing`, `/faq`, `/rules`

---

## Phase 14 — Stripe Live Mode

**Goal**: Switch from test payments to real payments.

**Checklist** (see also `PROJECT_STATUS.md` ⚠️ section):
1. Activate Stripe account (business info + bank account)
2. Re-create 3 products in Stripe live mode
3. Swap all Stripe env vars on Vercel to `pk_live_` / `sk_live_` keys + new price IDs
4. Register new webhook endpoint in Stripe live mode
5. Update `STRIPE_WEBHOOK_SECRET` on Vercel
6. Test one real purchase end-to-end, then refund

---

## Phase 15 — Security Audit

**Goal**: Harden before public launch.

**Checklist:**
- Supabase RLS: only `current_picks` and `model_results` anon read should be open; all other tables require service key or auth
- All `/api/*` routes call `auth()` before any logic ✅ (already done)
- Webhook handler: `constructEvent()` is first call with raw body ✅ (already done)
- `middleware.ts` covers all `/dashboard/*` routes ✅ (fixed 2026-05-19)
- `/api/checkout` validates `priceId` against known prices ✅ (fixed 2026-05-19)
- `/api/preferences` clamps and validates star values ✅ (fixed 2026-05-19)
- No secret keys in `NEXT_PUBLIC_` vars or client-side code
- Rate limiting on `/api/checkout` and `/api/portal`
- No open CORS headers on API routes

---

## Phase 16 — Mobile Layout QA

**Goal**: All pages render correctly on iOS Safari and Android Chrome.

**Known risk areas:**
- `PicksTable` complex grid — likely needs condensed mobile layout (fewer columns or card-per-row)
- Pricing 3-column grid must stack cleanly on small screens

**Pages to test:** Landing, Pricing, all Dashboard pages, all public pages

---

## Phase 17 — Deployment Docs

**Goal**: Comprehensive `RUNBOOK.md` so the system can be maintained and handed off.

**Sections:** Architecture overview, repo structure, local dev setup, Railway deployment, ML model update workflow, admin config panel usage, snapshot download setup, Stripe live mode switch, monitoring guide, troubleshooting common issues.

---

## Implementation Order

```
Phase 7  (Results page)              ← ✅ DONE
Phase 8  (Discord links)             ← ✅ DONE
Phase 9  (Admin config UI)           ← ✅ DONE
Phase 10 (Picks filtering)           ← ✅ DONE
Phase 13 (Content pass)              ← collaborative, anytime
Phase 11 (Snapshot pipeline)         ← unblocked, Python-side
Phase 12 (Model retraining)          ← after Phase 11
Phase 15 (Security audit)            ← before Phase 14
Phase 16 (Mobile QA)                 ← before Phase 14
Phase 14 (Stripe live mode)          ← needs Stripe account activation
Phase 17 (Deployment docs)           ← last
```

---

## Dependency Graph

```
Phase 1 (Schema) ✅
    └─► Phase 2 (Python Writes) ✅
            └─► Phase 3 (Railway) ✅
                    └─► Phase 7 (Results) ✅
                    └─► Phase 11 (Snapshots)
                            └─► Phase 12 (Retraining)

Phase 4 (Next.js) ✅
    └─► Phase 5 (Auth) ✅
            └─► Phase 6 (Billing) ✅
                    └─► Phase 10 (Picks Filtering) ✅
                    └─► Phase 15 (Security) → Phase 14 (Stripe Live)
                    └─► Phase 16 (Mobile QA) → Phase 14

Phase 9 (Admin UI) ✅
Phase 8, 13, 17 — independent
```
