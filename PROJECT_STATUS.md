# Quant Bet Labs — Project Status

_Last updated: 2026-05-05_

---

## Current State: Phase 4 Complete with Live Supabase Realtime — Current Picks Page is Live

The Python pipeline, Supabase schema, and full write layer are complete. The Railway worker is running — Discord alerts firing and `current_picks` updating every 15 minutes. The Next.js app reads picks from Supabase and subscribes to Realtime so the table refreshes automatically when the worker runs. Auth (Phase 5) is next.

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
| 5 — Auth & Tiers | ⬜ Not started | — |
| 6 — Billing | ⬜ Not started | — |
| 7 — Results Page | ⬜ Not started | — |
| 8 — Landing Page | ✅ Merged into Phase 4 | 2026-05-05 |

---

## What Exists

### Python Engine

| Component | File | Status |
|-----------|------|--------|
| Odds fetching, devig, EV/Kelly (v1) | `Original_Code/odds_engine.py` | ✅ Untouched reference |
| Per-book EV expansion (v2) | `Original_Code/odds_engine_v2.py` | ✅ Active engine |
| Board assembly + ML filtering (v1) | `Original_Code/run_edge_board.py` | ✅ Untouched reference |
| Board assembly wired to v2 engine | `Original_Code/run_edge_board_v2.py` | ✅ Active orchestrator |
| Long-running scheduler (v2, run_once, Option A dedup) | `Original_Code/bet_scheduler7.py` | ✅ All Supabase injection points wired |
| Daily settlement | `Original_Code/settle_ledger.py` | ✅ Supabase write wired; `book` column fix applied |
| Live lag feature augmentation | `Original_Code/live_lag_filler.py` | ✅ Unchanged |
| Supabase write adapter | `Original_Code/supabase_writer.py` | ✅ All 6 functions implemented |
| Devig curve coefficients | `mappings/` | ✅ Present |
| Serialized ML models | `models/` | ✅ Present |
| Sport/league config | `Original_Code/settings.env` | ✅ Drives cadence + active sports |
| Secret env vars | `Original_Code/secrets.env` | ✅ All values populated (do not commit) |

### Supabase

| Component | Status | Notes |
|-----------|--------|-------|
| `model_runs` table | ✅ Live | Tracks every scheduler cycle |
| `current_picks` table | ✅ Live | Replaced each successful run |
| `tracked_picks` table | ✅ Live | Mirrors bets.csv — one row per outcome |
| `settled_picks` table | ✅ Live | Append-only graded results |
| `upsert_tracked_picks_batch` RPC | ✅ Live | PostgreSQL function handling functional conflict key |
| MCP server config | ✅ Configured | `.mcp.json` — HTTP transport + auth header |
| Migration history | ✅ 2 migrations applied | `initial_schema`, `upsert_tracked_picks_fn` |

### Test Suites

| Suite | File | Result |
|-------|------|--------|
| v2 pipeline (schema, columns, filters, dedup) | `_test_v2_pipeline.py` | ✅ 19/19 passing |
| Supabase write layer (all 4 tables, upserts, idempotency) | `_test_supabase.py` | ✅ 35/35 passing |

### Frontend

| Component | Location | Status |
|-----------|----------|--------|
| Static landing page (reference) | `Homepage/index.html` | ✅ Design reference — preserved |
| Landing page styles (reference) | `Homepage/styles.css` | ✅ Color palette reference — preserved |
| Next.js app root | `app/` | ✅ Next.js 16 + Tailwind v4, App Router |
| Root layout + fonts | `app/app/layout.tsx` | ✅ Space Grotesk + Inter via next/font |
| Global styles + design tokens | `app/app/globals.css` | ✅ QBL palette, hero bg, pulse animation |
| Landing page | `app/app/page.tsx` | ✅ Full port of Homepage/index.html — `/` |
| Pricing page | `app/app/pricing/page.tsx` | ✅ 3-tier cards placeholder — `/pricing` |
| Dashboard layout | `app/app/dashboard/layout.tsx` | ✅ Top nav with picks/results/account tabs |
| Current Picks page | `app/app/dashboard/picks/page.tsx` | ✅ Live data + Realtime — `/dashboard/picks` |
| PicksTable component | `app/app/dashboard/picks/PicksTable.tsx` | ✅ Fetch + Realtime subscription + debounced refetch |
| Supabase browser client | `app/lib/supabase/client.ts` | ✅ Singleton client for Realtime |
| Results page | `app/app/dashboard/results/page.tsx` | ✅ Placeholder stats + table — `/dashboard/results` |
| Account page | `app/app/dashboard/account/page.tsx` | ✅ Profile + subscription placeholder — `/dashboard/account` |

---

## `supabase_writer.py` — Complete

**Location**: `Original_Code/supabase_writer.py`

All functions implemented and tested end-to-end:

| Function | Table | Called from |
|----------|-------|-------------|
| `start_model_run(active_sports)` | `model_runs` | `bet_scheduler7.py` — before `run_once()` |
| `fail_model_run(run_id, error)` | `model_runs` | `bet_scheduler7.py` — if `run_once()` raises |
| `finish_model_run(run_id, result, latest_output)` | `model_runs` + `current_picks` | `bet_scheduler7.py` — after `bets.to_csv()` |
| `write_current_picks(latest_output, run_id)` | `current_picks` | Called inside `finish_model_run()` |
| `upsert_tracked_picks(bets_df)` | `tracked_picks` | `bet_scheduler7.py` — after `finish_model_run()` |
| `upsert_settled_picks(settled_rows)` | `settled_picks` | `settle_ledger.py` — after ledger CSV write |

All functions are gated by `SUPABASE_ENABLED=1` and non-fatal (warn + continue on failure).

---

## Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Scheduler host | Railway (long-running worker) | Supports persistent process, easy env var management |
| `current_picks` lifecycle | Delete-all + insert on each run | `latest_output` exists before table is cleared; brief empty window is MVP-acceptable |
| `tracked_picks` dedup | Option A — max-EV book per `(game_id, team, market, point)` | One bet per opportunity; keeps Discord clean |
| `tracked_picks` upsert strategy | PostgreSQL RPC (`upsert_tracked_picks_batch`) | PostgREST can't express functional conflict key `COALESCE(point, -9999.0)`; RPC bypasses this |
| `settled_picks` upsert strategy | Standard supabase-py upsert | Conflict key `(game_id, market, team)` is column-only — no functional index needed |
| User tier storage | Clerk `publicMetadata.tier` | No extra DB table, server-readable, set via Clerk API after Stripe |
| Tier enforcement | Next.js server-side query filter | Simple, keeps RLS minimal |
| Tier structure | Basic $25 (1–2★), Premium $50 (1–4★ + education), VIP $100 (1–5★ all picks) | Flipped from original spec — VIP unlocks 5★, not Basic |
| Supabase write failure | Non-fatal (warn + continue) | Discord and CSV are the live system; Supabase is additive |
| Serialization | `json.loads(df.to_json(orient="records", date_format="iso"))` | Handles Timestamp→ISO, NaN→None, numpy scalars in one call |
| Discord | Preserved permanently | Real-time alert channel; Supabase supplements it |
| CSV files | Preserved alongside Supabase | Removed from critical path only once Supabase is verified in production |
| supabase-py version | Pinned to 2.18.1 | v2.9.1 had JWT regex validator rejecting new `sb_secret_...` key format; 2.18.1+ removed that check; 2.19+ requires `storage3>=2.x` which pulls in `pyiceberg` needing MSVC on Windows/Python 3.14 |

---

## Supabase Project Details

| Item | Value |
|------|-------|
| Project ref | `xktzdsyfsvtwxfixhsgy` |
| Project URL | `https://xktzdsyfsvtwxfixhsgy.supabase.co` |
| MCP URL | `https://mcp.supabase.com/mcp?project_ref=xktzdsyfsvtwxfixhsgy` |
| MCP config file | `.mcp.json` (project root) |
| Key format | New Supabase format (`sb_publishable_...` / `sb_secret_...`) — not legacy JWT |

**Python worker env vars** (in `Original_Code/secrets.env` and Railway):
```
SUPABASE_ENABLED=1
SUPABASE_URL=https://xktzdsyfsvtwxfixhsgy.supabase.co
SUPABASE_SERVICE_KEY=sb_secret_...   # in secrets.env — do not commit
```

**Next.js env vars** (Phase 4 — Vercel):
```
NEXT_PUBLIC_SUPABASE_URL=https://xktzdsyfsvtwxfixhsgy.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_...
```

---

## Railway Deployment — What Was Done

**Files created/modified for Railway (2026-05-05):**

| File | Change |
|------|--------|
| `requirements.txt` | Created — all deps pinned; `supabase==2.18.1`, `storage3==0.12.1`, `tzdata` for Linux |
| `railway.toml` | Created — `startCommand = "cd Original_Code && python -u bet_scheduler7.py"` |
| `Original_Code/bet_scheduler7.py` | 6 surgical changes (no logic touched) — see below |

**Changes to `bet_scheduler7.py`:**
1. Added `import logging` + `logging.basicConfig()` — structured logs for Railway
2. Added `DATA_DIR` + `BETS_PATH` constants (read from `DATA_DIR` env var, default `.`)
3. `SNAP_DIR` updated to `DATA_DIR / "snapshots"`
4. All `bets.csv` path references updated to `BETS_PATH`
5. Bot thread guarded with `if DISCORD_TOKEN:` — webhook-only mode works without bot token
6. `raise` in except block replaced with `log + sleep(60) + continue` — worker survives API failures
7. Removed `clear_output(wait=True)` + `display(bets)` (Jupyter-only) → `logger.info("cycle complete | ...")`

## Immediate Next Steps

**Phase 3 — Create the Railway service (manual steps):**
1. Push this repo to GitHub (required for Railway to pull from)
2. Go to railway.app → New Project → Deploy from GitHub repo
3. Add a **Volume** in Railway → mount at `/data` → set `DATA_DIR=/data` env var
4. Set all env vars in Railway dashboard (see table below)
5. Railway will auto-detect `railway.toml` and run the start command
6. Verify in Railway logs: `Worker starting —` appears, then `cycle complete |` every 15 min

**Required Railway environment variables:**

| Variable | Source | Notes |
|----------|--------|-------|
| `ODDS_API_KEY` | `secrets.env` | The Odds API v4 key |
| `DISCORD_WEBHOOK_BASIC` | `secrets.env` | Webhook URL |
| `DISCORD_WEBHOOK_PREMIUM` | `secrets.env` | Webhook URL |
| `DISCORD_WEBHOOK_VIP` | `secrets.env` | Webhook URL |
| `DISCORD_TOKEN` | `secrets.env` | Optional — only needed for bot startup ping |
| `DISCORD_CH_TEST` | `secrets.env` | Optional — only used if bot token is set |
| `SUPABASE_ENABLED` | — | Set to `1` |
| `SUPABASE_URL` | — | `https://xktzdsyfsvtwxfixhsgy.supabase.co` |
| `SUPABASE_SERVICE_KEY` | `secrets.env` | `sb_secret_...` key |
| `DATA_DIR` | — | Set to `/data` (Railway volume mount path) |
| `ACTIVE_SPORTS` | `settings.env` | e.g. `BASEBALL,HOCKEY,NBA,SOCCER,FIGHTS` |
| `DAY_POLL_MINUTES` | `settings.env` | Default `15` |
| `NIGHT_POLL_MINUTES` | `settings.env` | Default `120` |
| `LEAGUES_BASEBALL` | `settings.env` | `baseball_mlb` |
| `LEAGUES_HOCKEY` | `settings.env` | `icehockey_nhl` |
| `LEAGUES_NBA` | `settings.env` | `basketball_nba` |
| `LEAGUES_SOCCER` | `settings.env` | `soccer_epl` |
| `LEAGUES_FIGHTS` | `settings.env` | `mma_mixed_martial_arts,boxing_boxing` |

Note: `secrets.env` and `settings.env` are NOT deployed to Railway — all values must be set as Railway env vars directly.

**Phase 4 — Next.js scaffold (can run in parallel):**
1. `npx create-next-app@latest app --typescript --tailwind --app --no-src-dir`
2. Install Supabase client: `npm install @supabase/supabase-js @supabase/ssr`
3. Create `/picks` page — server component reading from `current_picks`
4. Add Realtime subscription for live updates
5. Enable Realtime on `current_picks` in Supabase dashboard

---

## Changelog

| Date | Change | File |
|------|--------|------|
| 2026-04-30 | Created planning docs | `CLAUDE.md`, `SPEC.md`, `IMPLEMENTATION_PLAN.md`, `PROJECT_STATUS.md` |
| 2026-04-30 | Extracted `run_once()` from `main()` loop | `Original_Code/bet_scheduler7.py` |
| 2026-04-30 | Created per-book EV engine | `Original_Code/odds_engine_v2.py` |
| 2026-05-01 | Created v2 board orchestrator | `Original_Code/run_edge_board_v2.py` |
| 2026-05-01 | Wired scheduler to v2; dedup fixes; CSV migration | `Original_Code/bet_scheduler7.py` |
| 2026-05-01 | Installed pyarrow, discord.py, IPython | pip |
| 2026-05-01 | Created v2 test suite (19/19 passing) | `_test_v2_pipeline.py` |
| 2026-05-01 | Option A dedup: max-EV book per outcome | `Original_Code/bet_scheduler7.py` |
| 2026-05-01 | Fixed `build_row_key()`: `best_book` → `book` | `Original_Code/settle_ledger.py` |
| 2026-05-05 | Designed schema (4 tables + indexes) | `supabase_schema.sql` |
| 2026-05-05 | Applied `initial_schema` migration — all 4 tables live | Supabase |
| 2026-05-05 | Applied `upsert_tracked_picks_fn` migration — RPC live | Supabase |
| 2026-05-05 | Implemented all 6 writer functions | `Original_Code/supabase_writer.py` |
| 2026-05-05 | Wired all Supabase injection points in scheduler | `Original_Code/bet_scheduler7.py` |
| 2026-05-05 | Wired Supabase write in settlement script | `Original_Code/settle_ledger.py` |
| 2026-05-05 | Created + populated secrets file | `Original_Code/secrets.env` |
| 2026-05-05 | Installed supabase-py 2.18.1 (new key format support) | pip |
| 2026-05-05 | Created Supabase test suite (35/35 passing) | `_test_supabase.py` |
| 2026-05-05 | Railway prep: logging, DATA_DIR, graceful error handling, bot guard | `Original_Code/bet_scheduler7.py` |
| 2026-05-05 | Created Railway start command config | `railway.toml` |
| 2026-05-05 | Created Python dependency manifest | `requirements.txt` |
| 2026-05-05 | Fixed Railway CWD bug: run from repo root with PYTHONPATH | `railway.toml` |
| 2026-05-05 | Railway worker deployed and verified — cycle complete, Supabase + Discord live | Railway |
| 2026-05-05 | Scaffolded Next.js 16 app (Tailwind v4, App Router) | `app/` |
| 2026-05-05 | Ported landing page to Next.js (full design match) | `app/app/page.tsx` |
| 2026-05-05 | Created pricing page with tier cards | `app/app/pricing/page.tsx` |
| 2026-05-05 | Created dashboard layout with picks/results/account tabs | `app/app/dashboard/layout.tsx` |
| 2026-05-05 | Created picks, results, account placeholder pages | `app/app/dashboard/` |
| 2026-05-05 | Added anon read RLS policy + Realtime publication on current_picks | Supabase |
| 2026-05-05 | Built PicksTable with Supabase fetch + Realtime + debounced refetch | `app/app/dashboard/picks/PicksTable.tsx` |
| 2026-05-05 | Created singleton Supabase browser client | `app/lib/supabase/client.ts` |
