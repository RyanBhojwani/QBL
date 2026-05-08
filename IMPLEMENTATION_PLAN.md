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
| 7 | Results Page | Ledger/performance display | ⬜ Not started |

---

## Phases 1–6 — COMPLETE

All phases through billing are fully implemented and live. See `PROJECT_STATUS.md` for the full breakdown of what was built.

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

## Phase 7 — Results Page

**Goal**: `/dashboard/performance` shows historical settled picks with win/loss record and ROI stats.

**Files to create/modify:**
- `app/app/dashboard/performance/page.tsx` — server component querying `settled_picks`
- `app/app/dashboard/performance/ResultsTable.tsx` — client component with filters

**Stats to compute from `settled_picks`:**
- Record: W / L / P counts
- Win rate: `W / (W + L) %`
- ROI: `sum((odds - 1) * kelly * W_indicator) / sum(kelly)`
- Breakdown by sport, market type, and star rating
- Rolling ROI chart (optional)

**Data source**: `settled_picks` table in Supabase — populated by `settle_ledger.py` running on Railway after games complete.

**Gating**: Accessible to all subscription tiers. Show full history regardless of current tier.

**Done when**: `/dashboard/performance` shows real historical picks with accurate W/L record and ROI pulling from live `settled_picks` data.

**Dependencies**: Railway worker + `settle_ledger.py` must have run enough cycles to accumulate meaningful data.

---

## Phase 7 — Settlement Verification & Results Page

**Goal**: Confirm settlement is writing to Supabase correctly, then build the Performance dashboard page with real W/L/ROI data from `settled_picks`.

**Settlement architecture (no changes needed):**
- Already running: daemon thread in `bet_scheduler7.py` fires `settle_ledger.main()` at 4 AM ET
- Already writes to: `settled_picks` table via `sb.upsert_settled_picks(graded_rows)`
- Still reads from: `bets.csv` + `ledger.csv` on Railway volume (acceptable for MVP)
- Future migration: replace CSV reads with `tracked_picks` Supabase queries — defer until stable

**Verification step**: Query `settled_picks` in Supabase dashboard. If empty, check Railway logs around 4 AM ET.

**Files to build:**
- `app/app/dashboard/performance/page.tsx` — server component, queries `settled_picks`, computes stats
- `app/app/dashboard/performance/ResultsTable.tsx` — client component (follow `PicksTable.tsx` pattern)

**Stats to compute (server-side):**
- Record: W / L / P counts
- Win rate: `W / (W + L) * 100`
- ROI: `sum((odds_from_best_book - 1) * kelly * [result=W]) / sum(kelly) * 100`
- Breakdown by sport, market type, and star tier

**Table columns:** Stars, Team, Market, Sport, Book, Odds, Result (W/L/P), Game Time

**Done when:** `/dashboard/performance` shows real W/L record and ROI from live `settled_picks` data.

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
Phase 7  (Results page)              ← unblocked now
Phase 8  (Discord links)             ← unblocked, quick task
Phase 9  (Admin config UI)           ← after Phase 7
Phase 10 (Picks filtering)           ← unblocked, frontend work
Phase 11 (Snapshot pipeline)         ← unblocked, Python-side
Phase 12 (Model retraining)          ← after Phase 11
Phase 13 (Content pass)              ← collaborative, anytime
Phase 14 (Stripe live mode)          ← needs Stripe account activation
Phase 15 (Security audit)            ← before Phase 14
Phase 16 (Mobile QA)                 ← before Phase 14
Phase 17 (Deployment docs)           ← last
```

---

## Dependency Graph (updated)

```
Phase 1 (Schema) ✅
    └─► Phase 2 (Python Writes) ✅
            └─► Phase 3 (Railway) ✅
                    └─► Phase 7 (Results)
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
