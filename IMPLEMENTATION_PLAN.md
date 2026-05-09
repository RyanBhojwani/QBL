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

---

## Phases 1–8 — COMPLETE

All phases through the results dashboard are fully implemented and live. See `PROJECT_STATUS.md` for the full breakdown of what was built.

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

**Frontend — `/performance`** (public page, updated):
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

## Phase 8 — Discord Links

**Goal**: Replace all 8 `href="#"` Discord CTA placeholders with real invite URL.

**Approach**: Define `DISCORD_INVITE_URL` constant in `lib/constants.ts`, import everywhere — one change updates all 8 locations.

**Files to edit:** `app/page.tsx` (×2), `app/faq/page.tsx`, `app/pricing/page.tsx`, `app/how-it-works/page.tsx`, `app/dashboard/faq/page.tsx`, `app/dashboard/account/page.tsx`, `app/dashboard/picks/page.tsx`

**Done when:** All Discord buttons navigate to the real server.

---

## Phase 9 — Admin Config Panel

**Goal**: Change active sports and poll intervals from a web UI instead of the Railway dashboard.

**Architecture:**
1. **Supabase `worker_config` table** — key/value store seeded with `day_poll_minutes`, `night_poll_minutes`, `active_sports`
2. **Worker change** — `fetch_remote_config()` in `bet_scheduler7.py` reads from this table each cycle, falls back to env vars
3. **`/dashboard/admin` page** — admin-gated (email check), shows toggles + inputs, saves via `/api/admin/config`
4. **`/api/admin/config` route** — verifies admin email, writes to `worker_config` via service key

**Done when:** Toggling a sport off in the UI takes effect on the next poll cycle.

---

## Phase 10 — Picks Table Filtering & User Preferences

**Goal**: Let users filter the picks table by sport, market, book, and minimum stars. Reach goal: persist those filters per user so their preferred settings load automatically every time they open the dashboard.

**Core filters (all users):**
- **Sport** — dropdown of distinct sports present in `current_picks` (e.g. MLB, NHL, NBA)
- **Market** — dropdown: All / Moneyline / Spreads / Totals
- **Book** — dropdown of distinct books present in `current_picks` (FanDuel, DraftKings, etc.)
- **Min stars** — 1–5 selector (respects their tier cap — can't filter above their tier max)

**Implementation approach:**
- Filters are client-side state in `PicksTable.tsx` — fetch all eligible picks once, filter in memory
- Distinct sport/book values derived from the fetched data (no extra query)
- Active filter count badge on each dropdown so users can see what's applied at a glance

**Persistent preferences (reach goal):**

Option: **Supabase `user_preferences` table** (keyed by Clerk user ID)
```sql
CREATE TABLE user_preferences (
  clerk_user_id  text PRIMARY KEY,
  picks_filters  jsonb DEFAULT '{}',
  updated_at     timestamptz DEFAULT now()
);
```
- `picks_filters` stores: `{ sports: ["baseball_mlb"], markets: ["h2h"], books: ["fanduel"], min_stars: 2 }`
- On dashboard load: fetch preferences → pre-populate filter state
- On filter change: debounced upsert back to `user_preferences` (500ms after last change)
- RLS: users can only read/write their own row (`clerk_user_id = requesting_user_id` — enforced via service key on API route)

**Files to create/modify:**
- `app/app/dashboard/picks/PicksTable.tsx` — add filter bar UI + filter logic + preference load/save
- `app/api/preferences/route.ts` — GET/POST endpoint for `user_preferences` (reads Clerk user ID from `auth()`)
- Supabase migration: `user_preferences` table + RLS policy

**Done when:** Filter dropdowns work, picks update instantly on selection. On revisit, last-used filters are pre-selected.

---

## Phase 11 — Snapshot Pipeline (previously Phase 10)

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

**Note:** Retraining script is a separate workstream. Phase 12 establishes the deployment pathway.

**Done when:** Updated `.pkl` files pushed to GitHub, Railway redeploys, new model behavior confirmed.

---

## Phase 13 — Content Pass (previously Phase 12)

**Goal**: Replace all placeholder copy with real marketing content.

**Pages:** `/` (stats accuracy), `/how-it-works`, `/performance`, `/pricing`, `/faq`, `/rules`

**Approach:** Collaborative — you provide copy direction, implementation is mechanical text replacement.

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
- Supabase RLS: only `current_picks` anon read should be open; all other tables require service key or auth
- All `/api/*` routes must call `auth()` before any logic
- Webhook handler: `constructEvent()` must be first call (raw body, no prior JSON parse)
- `proxy.ts` middleware covers all `/dashboard/*` and sensitive `/api/*` routes
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
Phase 13 (Content pass)              ← collaborative, anytime
Phase 10 (Picks filtering)           ← unblocked, frontend work
Phase 9  (Admin config UI)           ← after Phase 7
Phase 11 (Snapshot pipeline)         ← unblocked, Python-side
Phase 12 (Model retraining)          ← after Phase 11
Phase 15 (Security audit)            ← before Phase 14
Phase 16 (Mobile QA)                 ← before Phase 14
Phase 14 (Stripe live mode)          ← needs Stripe account activation
Phase 17 (Deployment docs)           ← last
```

---

## Dependency Graph (updated)

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
                    └─► Phase 10 (Picks Filtering)
                    └─► Phase 15 (Security) → Phase 14 (Stripe Live)
                    └─► Phase 16 (Mobile QA) → Phase 14

Phase 7 → Phase 9 (Admin UI)
Phase 8, 13, 17 — independent
```
