# Quant Bet Labs — Claude Instructions

## What This Project Is

Quant Bet Labs is a sports betting subscription web app. The Python backend already finds +EV picks using a custom devig model and posts them to Discord. The current task is to expose that output through a Supabase-backed Next.js frontend — without rewriting any of the model logic.

**This is a data-flow refactor, not a model rewrite.**

---

## Repository Structure

```
Project2/
├── Original_Code/              # All Python backend files
│   ├── odds_engine.py          # v1 — original engine (UNTOUCHED — do not edit)
│   ├── odds_engine_v2.py       # v2 — per-book EV expansion (active engine)
│   ├── run_edge_board.py       # v1 — original board orchestrator (UNTOUCHED)
│   ├── run_edge_board_v2.py    # v2 — wired to odds_engine_v2 (active orchestrator)
│   ├── bet_scheduler7.py       # Long-running scheduler (wired to v2, run_once() extracted)
│   ├── settle_ledger.py        # Daily settlement: bets.csv → ledger.csv + W/L
│   ├── live_lag_filler.py      # Adds historical lag columns to the board
│   └── settings.env            # Sport config, poll cadence (non-secret)
├── mappings/                   # JSON devig curve coefficients per sport/market
├── models/                     # Serialized ML models (.pkl) and metadata (.json)
├── Homepage/                   # Static landing page (pre-Next.js)
│   ├── index.html
│   └── styles.css
├── _test_v2_pipeline.py        # Test suite for v2 pipeline (run from Project2/)
├── CLAUDE.md                   # This file
├── SPEC.md                     # Product and technical specification
├── IMPLEMENTATION_PLAN.md      # Phased build plan
└── PROJECT_STATUS.md           # Current project state
```

**Future additions (not yet created):**
```
├── app/                    # Next.js application (App Router)
├── supabase_writer.py      # Thin Python → Supabase write wrapper
```

---

## The Python Data Pipeline

### v1 (UNTOUCHED — do not edit these files)
```
odds_engine.py → run_edge_board.py
  Output: one row per outcome (best soft book chosen)
  Column: best_book (single best book name)
```

### v2 (ACTIVE — what bet_scheduler7.py uses)
```
odds_engine_v2.py
  └─ All devig/weighting logic IDENTICAL to v1
  └─ expand_per_book() replaces pick_best_soft_price() + add_ev_metrics()
  └─ Output: one row per (outcome × soft book)
  └─ New columns: book, book_ip, book_odds  (instead of best_book, best_ip)
  └─ EV/Kelly/Sharpe computed identically, but against each book's price

run_edge_board_v2.py
  └─ run_edge_board() — identical to v1 except uses odds_engine_v2
  └─ build_edge_output(board)
       └─ Loads sigma + CLV models from models/
       └─ Applies threshold filters (kelly ≥ 0.25%, EV ≤ 0.3, CLV ≥ 0.6, etc.)
       └─ Bins CLV probability into 1–5 star rating
       └─ Returns latest_output — 14 columns (see schema below)

bet_scheduler7.py  [imports from run_edge_board_v2]
  └─ run_once(bets) → dict  [extracted for testability]
       └─ Calls run_edge_board() → latest_board
       └─ Calls build_edge_output() → latest_output
       └─ Snapshots board to snapshots/ as Parquet
       └─ Dedup-merges on (game_id, team, market, point) before any board merge
       └─ Appends new picks to bets_df, updates closing lines + CLV
       └─ Returns: latest_board, latest_output, bets, new_rows, to_send
  └─ main() loop: calls run_once(), posts Discord, writes bets.csv, sleeps

settle_ledger.py  [untouched]
  └─ Moves past bets from bets.csv to ledger.csv
  └─ Fetches scores from The Odds API /scores
  └─ Grades W/L/P per market type
```

---

## Output Schema: latest_output (14 columns)

These columns come out of `build_edge_output()` in `run_edge_board_v2.py` and flow into Supabase `current_picks`:

| Column | Type | Notes |
|--------|------|-------|
| `sport` | str | e.g. `baseball_mlb` |
| `game_id` | str | Odds API game ID |
| `commence_time` | timestamp | UTC |
| `team` | str | Team/side name |
| `market` | str | `h2h`, `spreads`, `totals` |
| `point` | float | Spread/total value, NaN for h2h |
| `book` | str | Bookmaker slug (e.g. `fanduel`) |
| `odds_from_best_book` | float | Decimal odds at this book |
| `sharp_odds` | float | Model's fair value (decimal) |
| `ev` | float | Expected value (e.g. 0.05 = 5%) |
| `kelly` | float | Half-Kelly size, clipped at 3% |
| `clv_prob_med` | float | CLV probability from bagged logistic |
| `stars` | int | 1–5 (binned from clv_prob_med) |
| `outcome_threshold` | float | Risk-adjusted EV floor |

**Key change from v1:** column `best_book` → `book`. All other columns and formulas identical.

---

## Data Mapping: Python → Supabase

| Python | Supabase table | Upsert key | Notes |
|--------|----------------|------------|-------|
| `latest_output` | `current_picks` | `(game_id, team, market, point, book)` | One row per book per outcome; all books shown |
| `bets_df` (bets.csv) | `tracked_picks` | `(game_id, team, market, point)` | One row per outcome (best-book dedup needed — see OPEN QUESTIONS) |
| `ledger.csv` | `settled_picks` | `(game_id, team, market)` | Append-only; settled W/L |

---

## Absolute Rules

### Never touch these:
- Any logic in `odds_engine.py` (v1 — preserved as reference)
- Devig logic, book weighting, EV formulas (identical in v2 — do not change)
- Threshold/filter logic in `run_edge_board_v2.py`
- Model loading or ML prediction logic in `run_edge_board_v2.py`
- Discord posting logic in `bet_scheduler7.py`
- Settlement math in `settle_ledger.py`

### Always preserve:
- CSV behavior (`bets.csv`, `ledger.csv`) until Supabase replacement is confirmed working
- Discord output — it is not being removed, only supplemented
- The landing page visual style (`Homepage/styles.css` is the design reference)
- Parquet snapshot system in `bet_scheduler7.py`
- v1 files (`odds_engine.py`, `run_edge_board.py`) — kept intact as reference

### Never commit:
- `secrets.env` or any `.env` file containing API keys
- `ODDS_API_KEY`, `DISCORD_WEBHOOK_*`, `SUPABASE_KEY`, `STRIPE_SECRET_KEY`, or `CLERK_SECRET_KEY`
- `.pkl` model files should not be regenerated or replaced without explicit instruction

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Python worker | Railway (long-running worker service) |
| Database | Supabase (PostgreSQL + Realtime) |
| Auth | Clerk |
| Billing | Stripe |
| Frontend | Next.js (App Router), Tailwind CSS, shadcn/ui |
| Hosting | Vercel |
| Odds data | The Odds API v4 |
| Alerts | Discord webhooks (preserved) |

---

## Environment Variables

**Python worker (Railway):**
- `ODDS_API_KEY` — The Odds API v4
- `DISCORD_WEBHOOK_BASIC`, `DISCORD_WEBHOOK_PREMIUM`, `DISCORD_WEBHOOK_VIP`, `DISCORD_WEBHOOK_TEST`
- `DISCORD_TOKEN`, `DISCORD_CH_*`
- `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`
- `DAY_POLL_MINUTES`, `NIGHT_POLL_MINUTES` (default 15, 60)
- `ACTIVE_SPORTS` (e.g., `BASEBALL,HOCKEY,NBA,SOCCER`)
- `LEAGUES_<SPORT>` (optional overrides)

**Next.js app (Vercel):**
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
- `CLERK_SECRET_KEY`
- `STRIPE_SECRET_KEY`
- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`
- `STRIPE_WEBHOOK_SECRET`

---

## User Tiers

Tiers are stored in Clerk `publicMetadata.tier`. Values: `"basic"`, `"premium"`, `"vip"`.

| Tier | Price | Stars visible | Maps to Discord |
|------|-------|---------------|-----------------|
| basic | $25/mo | 1★ only | `#basic` channel |
| premium | $50/mo | 1–3 stars + educational content | `#premium` channel |
| vip | $100/mo | 1–5 stars (all picks) | `#vip` channel |

---

## Open Questions (must resolve before Supabase Phase 2)

### 1. Per-book bets tracking
`latest_output` now has one row per (outcome × book). The `run_once()` loop appends new rows to `bets_df` using key `["game_id", "market", "stars"]`, which does NOT include `book`. On a fresh run this would add ALL book rows for every outcome — meaning 4 Discord alerts and 4 `tracked_picks` rows for one game.

**Decision needed:** Should `tracked_picks` track one row per outcome (best-EV book) or one row per (outcome × book)?
- **Option A (recommended):** Dedup `new_rows` by `(game_id, team, market, point)` keeping max-EV book before appending to bets. Keeps Discord and tracking clean. One row per opportunity.
- **Option B:** Track all books in bets; post only one Discord alert per outcome (best book). More data but more complex dedup in Discord logic.

### 2. settle_ledger.py column name
`settle_ledger.py:57` uses `best_book` in the composite row key for dedup. With v2 bets, the column is now `book`. This is currently safe (the function skips missing columns) but `book` is not included in the dedup key, which could cause ledger duplicates in edge cases. Fix: add `book` to the key list in `build_row_key()`.

---

## Key Constraints for Development

- `build_edge_output()` is a black box — its return value is the source of truth for what picks exist
- Do not change which rows pass filters; only change what happens to those rows after they are generated
- The Python worker and the Next.js app communicate exclusively through Supabase — no direct HTTP calls between them
- Supabase RLS enforces tier access at the database level for production
- Run tests with: `python _test_v2_pipeline.py` from `Project2/`
