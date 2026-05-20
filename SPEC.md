# Quant Bet Labs — Product & Technical Specification

_Last updated: 2026-05-19_

## Product Summary

Quant Bet Labs surfaces profitable +EV sports betting picks using a custom devig model with sport-specific book weighting. The Python engine already runs — it finds edges, tracks picks, and sends alerts to Discord. This spec defines the web app layer on top of that engine.

**Users pay for tiered access to live picks.** The model runs continuously. Users see the output through a web dashboard instead of (or in addition to) Discord.

---

## User Tiers

| Tier | Stars visible | Price | Extras |
|------|--------------|-------|--------|
| None (no subscription) | — | $0 | Landing page only |
| Basic | 1–2★ | $25/mo | Discord alerts, all sports & markets |
| Premium | 1–4★ | $50/mo | Discord alerts, all sports & markets, educational content |
| VIP | 1–5★ (all picks) | $100/mo | Discord alerts, all sports & markets, educational content |

Star rating is binned from CLV probability produced by the bagged logistic model in `run_edge_board_v2.py`. **The tier mapping is fixed — do not change which picks fall in which tier.**

Tier is stored in Clerk `publicMetadata.tier`. Values: `"basic"`, `"premium"`, `"vip"`, or `null`/absent for no subscription. Unauthenticated users are redirected to sign-in by `middleware.ts` when accessing any `/dashboard/*` route.

---

## Core User Flows

### 1. Visitor → Subscriber
1. Lands on marketing page (`/`)
2. Views feature overview, example picks, and pricing
3. Clicks "Get Started" → Clerk sign-up
4. Redirected to `/pricing` → chooses a plan → Stripe checkout
5. On payment success: Clerk `publicMetadata.tier` is set server-side via webhook → Clerk API
6. Redirected to `/dashboard/picks`

### 2. Subscriber → Live Picks
1. Signs in → redirected to `/dashboard/picks`
2. Sees current +EV picks filtered by their tier (read from `current_picks` Supabase table)
3. Table updates in real-time via Supabase Realtime (no page reload)
4. Can filter by sport, book, and star range; preferences are saved per user
5. Each row shows: Stars, Team, Market (with point), Book, Odds (American), Bet Size (units), Game Time

### 3. Python Worker → Supabase
1. `bet_scheduler7.py` polls on its day/night cadence (15 min / 120 min)
2. Calls `run_edge_board()` → `build_edge_output()` → `latest_output`
3. Upserts `latest_output` rows into `current_picks` (replace strategy)
4. Upserts active bets into `tracked_picks`
5. Discord webhooks fire as normal (unchanged)

### 4. Settlement
1. At 4 AM ET daily, `settle_ledger.main()` runs
2. Moves past bets from `bets.csv` → `ledger.csv` and grades W/L/P
3. Upserts results into `settled_picks` Supabase table
4. At 4:30 AM ET, `results_calculator.py` runs and recomputes all `model_results`
5. `/dashboard/performance` and `/performance` reflect updated data that day

---

## Data Model

### `current_picks` table
The live +EV output. Replaced (upserted) on every poll cycle. This is what the frontend displays.
One row per **(outcome × book)** — all books shown for each game.

| Column | Type | Source |
|--------|------|--------|
| `id` | uuid | auto |
| `sport` | text | `latest_output.sport` |
| `game_id` | text | `latest_output.game_id` |
| `commence_time` | timestamptz | `latest_output.commence_time` |
| `team` | text | `latest_output.team` |
| `market` | text | `latest_output.market` (`h2h`, `spreads`, `totals`) |
| `point` | float | `latest_output.point` |
| `book` | text | `latest_output.book` (bookmaker slug, e.g. `fanduel`) |
| `odds_from_best_book` | float | `latest_output.odds_from_best_book` (decimal odds at this book) |
| `sharp_odds` | float | `latest_output.sharp_odds` |
| `ev` | float | `latest_output.ev` (e.g., 0.05 = 5%) |
| `kelly` | float | `latest_output.kelly` |
| `clv_prob_med` | float | `latest_output.clv_prob_med` |
| `stars` | int | `latest_output.stars` (1–5) |
| `outcome_threshold` | float | `latest_output.outcome_threshold` |
| `last_updated` | timestamptz | set by `supabase_writer.py` on each write |

**Upsert key**: `(game_id, team, market, point, book)`
**Cleanup**: rows where `last_updated < current cycle timestamp` are deleted after each upsert

### `tracked_picks` table
Active bets awaiting settlement. Mirrors `bets.csv`. Updated on each scheduler cycle.
One row per outcome (best-EV book selected).

| Column | Type | Source |
|--------|------|--------|
| `id` | uuid | auto |
| `found_at` | timestamptz | `bets.csv.found_at` |
| `sport` | text | |
| `game_id` | text | |
| `commence_time` | timestamptz | |
| `team` | text | |
| `market` | text | |
| `point` | float | |
| `book` | text | bookmaker slug |
| `odds_from_best_book` | float | decimal odds at time of pick |
| `sharp_odds` | float | |
| `ev` | float | |
| `kelly` | float | |
| `clv_prob_med` | float | |
| `stars` | int | |
| `closing_line` | float | nullable, filled as game approaches |
| `clv` | float | nullable, filled at closing |
| `posted` | bool | whether Discord alert was sent |
| `tier` | text | `basic`/`premium`/`vip` |

**Upsert key**: `(game_id, team, market, point)` — one row per outcome

### `settled_picks` table
Historical settled bets with grades. Append-only (never deleted). Mirrors `ledger.csv`.

| Column | Type | Source |
|--------|------|--------|
| `id` | uuid | auto |
| `found_at` | timestamptz | |
| `sport` | text | |
| `game_id` | text | |
| `commence_time` | timestamptz | |
| `team` | text | |
| `market` | text | |
| `point` | float | |
| `best_book` | text | |
| `odds_from_best_book` | float | |
| `sharp_odds` | float | |
| `ev` | float | |
| `kelly` | float | |
| `stars` | int | |
| `closing_line` | float | |
| `clv` | float | |
| `result` | text | `W`, `L`, `P`, or empty if ungradeable |
| `settled_at` | timestamptz | set by `supabase_writer.py` |

**Insert key**: `(game_id, market, team)` — de-duplicated before insert

### `model_results` table
Pre-computed performance metrics. ~66 rows, upserted nightly at 4:30 AM ET.

| Key columns | Notes |
|-------------|-------|
| `time_window` | `all_time`, `30d`, `1d` |
| `segment_type` | `overall`, `star`, `sport`, `market`, `sport_market` |
| `segment_val` | e.g. `"5"`, `"baseball"`, `"baseball\|h2h"` |
| `n_picks`, `n_wins`, `n_losses`, `n_pushes` | counts |
| `win_pct`, `avg_odds` | kelly-weighted average odds |
| `roi`, `total_profit_units` | real return |
| `clv_roi`, `clv_profit_units` | CLV-based return |
| `ev_roi`, `ev_profit_units` | model EV at time of bet |
| `cagr`, `bankroll_return`, `sharpe`, `sortino`, `max_drawdown`, `volatility` | financial metrics |
| `daily_curve` | JSONB array of `{date, bankroll_real, bankroll_exp}` |

### `user_preferences` table
Per-user filter preferences for the picks dashboard.

| Column | Type |
|--------|------|
| `clerk_user_id` | text (PK) |
| `sports` | text[] |
| `books` | text[] |
| `min_stars` | int (1–5) |
| `max_stars` | int (1–5) |
| `updated_at` | timestamptz |

### `worker_config` table
Key/value config read by Railway worker each poll cycle.

| Key | Example value |
|-----|---------------|
| `day_poll_minutes` | `"15"` |
| `night_poll_minutes` | `"120"` |
| `active_sports` | `"BASEBALL,HOCKEY,SOCCER,FIGHTS"` |
| `leagues_soccer` | `"soccer_epl,soccer_usa_mls"` |
| `leagues_fights` | `"mma_mixed_martial_arts,boxing_boxing"` |

---

## Frontend Pages

### Public pages

| Route | Description |
|-------|-------------|
| `/` | Marketing landing page — hero, how it works, features, performance teaser |
| `/performance` | Public performance overview — real data, modals; breakdown tables locked behind subscribe CTA |
| `/how-it-works` | Full methodology walkthrough — 7 steps + glossary |
| `/pricing` | Plan comparison + Stripe checkout entry |
| `/faq` | Frequently asked questions |
| `/rules` | Rules & disclaimer |

### Dashboard pages (require auth via `middleware.ts`)

| Route | Tier required | Description |
|-------|--------------|-------------|
| `/dashboard/picks` | Any (subscription) | Live +EV picks — real-time, tier-filtered, sport/book/stars filters |
| `/dashboard/performance` | Any (subscription) | Full performance dashboard — all breakdown tables and modals |
| `/dashboard/education` | Premium / VIP | Glossary + core concepts for +EV betting |
| `/dashboard/how-to-use` | Premium / VIP | Step-by-step guide + Do/Don't list |
| `/dashboard/faq` | Any (subscription) | Member FAQ |
| `/dashboard/account` | Any (subscription) | Tier display, Manage Subscription (Stripe portal), Sign Out |
| `/dashboard/admin` | Admin email only | Worker config — poll cadence, sport/league toggles |

### API routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/checkout` | POST | Create Stripe Checkout Session — validates priceId before calling Stripe |
| `/api/webhooks/stripe` | POST | Handle Stripe events → update Clerk tier |
| `/api/portal` | POST | Open Stripe Customer Portal |
| `/api/preferences` | GET / POST | Load / save user filter preferences — star values clamped to 1–5 |
| `/api/admin/config` | GET / POST | Load / save worker_config — admin-gated |

---

## Tech Stack

### Python Worker (Railway)
- Long-running worker service (not cron — the scheduler manages its own cadence)
- `bet_scheduler7.py` is the entrypoint
- `supabase_writer.py` module handles all Supabase writes
- All secrets injected via Railway environment variables
- `models/` and `mappings/` directories bundled in repo/image

### Database (Supabase)
- PostgreSQL with Row Level Security
- Realtime enabled on `current_picks` table
- Service role key used by Python worker (full write access)
- Anon key used by Next.js frontend (read-only, filtered by RLS)
- Anon read open on: `current_picks`, `model_results`
- All other tables require service key or authenticated session

### Auth (Clerk)
- `middleware.ts` at Next.js project root protects all `/dashboard/*` routes
- Unauthenticated users are redirected to sign-in (not shown upgrade walls)
- `publicMetadata.tier` set server-side via Clerk API after Stripe payment
- Sign-out calls Clerk `signOut()` — session is properly terminated

### Billing (Stripe)
- Stripe Checkout for plan selection
- `priceId` validated against known prices server-side before Stripe call
- Webhook handler: `checkout.session.completed` → set Clerk metadata tier
- Webhook handler: `customer.subscription.updated` → update tier on plan change
- Webhook handler: `customer.subscription.deleted` → set tier to `null`
- Stripe Customer Portal for self-serve upgrade/downgrade/cancel

### Frontend (Next.js + Vercel)
- App Router (Next.js 15+)
- Tailwind CSS
- Recharts for bankroll curve chart (loaded via `next/dynamic` for SSR safety)
- `@supabase/supabase-js` for database access
- `@clerk/nextjs` for auth
- Deployed to Vercel — auto-deploys on push to `master`

---

## Discord Integration (Preserved)

Discord is NOT being removed. It remains the primary real-time notification channel.

- `bet_scheduler7.py` continues posting to tier-specific webhooks
- Tier routing: stars 1–2 → Basic channel, stars 1–4 → Premium channel, stars 1–5 → VIP channel
- Sport-specific guards (NCAAF spread limits, time-to-game cutoffs) stay unchanged
- The web app is an additional output, not a replacement

---

## Supabase Realtime Strategy

- Python worker writes to `current_picks` on each cycle (~every 15 min)
- Next.js client subscribes to `current_picks` with `on('postgres_changes', ...)`
- Frontend updates the table in-place without page reload; debounced 500ms to avoid thrashing
- Live indicator in filter bar pulses amber while a background update is in flight

---

## Performance & Cost Considerations

- The Odds API: credits consumed by Python worker only (no change from current)
- Supabase: free tier supports Realtime + ~500MB DB — more than sufficient for v1
- Vercel: free tier for frontend
- Railway: hobby plan sufficient for single long-running worker
- Clerk: free tier for <10k MAU
- Stripe: 2.9% + 30¢ per transaction (standard)
