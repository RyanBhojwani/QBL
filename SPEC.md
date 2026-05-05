# Quant Bet Labs — Product & Technical Specification

## Product Summary

Quant Bet Labs surfaces profitable +EV sports betting picks using a custom devig model with sport-specific book weighting. The Python engine already runs — it finds edges, tracks picks, and sends alerts to Discord. This spec defines the web app layer on top of that engine.

**Users pay for tiered access to live picks.** The model runs continuously. Users see the output through a web dashboard instead of (or in addition to) Discord.

---

## User Tiers

| Tier | Access | Price (TBD) |
|------|--------|-------------|
| Free / Unauthed | Landing page only | $0 |
| Basic | All picks (1–5 stars) | $ |
| Premium | Picks rated 3+ stars | $$ |
| VIP | Picks rated 5 stars only | $$$ |

Star rating is binned from CLV probability produced by the bagged logistic model in `run_edge_board.py`. **The tier mapping is fixed — do not change which picks fall in which tier.**

Tier is stored in Clerk `publicMetadata.tier`. Values: `"basic"`, `"premium"`, `"vip"`. Unauthenticated users see the landing page and a signup CTA.

---

## Core User Flows

### 1. Visitor → Subscriber
1. Lands on marketing page (`/`)
2. Views feature overview, sample picks, and pricing
3. Clicks "Get Started" → Clerk sign-up
4. Chooses a plan → Stripe checkout
5. On payment success: Clerk `publicMetadata.tier` is set server-side via Clerk API
6. Redirected to `/picks` board

### 2. Subscriber → Live Picks
1. Signs in → redirected to `/picks`
2. Sees current +EV picks filtered by their tier (read from `current_picks` Supabase table)
3. Table updates in real-time via Supabase Realtime (no page reload)
4. Can filter by sport, market type, stars, time to game
5. Each row shows: team, market, best book, odds, sharp odds, EV%, Kelly%, stars, game time

### 3. Python Worker → Supabase
1. `bet_scheduler7.py` polls on its day/night cadence (15 min / 60 min)
2. Calls `run_edge_board()` → `build_edge_output()` → `latest_output`
3. Upserts `latest_output` rows into `current_picks` (replace strategy)
4. Upserts active bets into `tracked_picks`
5. Discord webhooks fire as normal (unchanged)

### 4. Settlement
1. At 4 AM ET daily, `settle_ledger.main()` runs
2. Moves past bets from `bets.csv` → `ledger.csv` and grades W/L/P
3. Upserts results into `settled_picks` Supabase table
4. `/results` page displays historical performance

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
One row per outcome (best-EV book selected — see Open Questions in PROJECT_STATUS.md).

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
| `book` | text | bookmaker slug (renamed from `best_book` in v2) |
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

---

## Frontend Pages

| Route | Auth | Description |
|-------|------|-------------|
| `/` | Public | Marketing landing page (rebuilt from Homepage/index.html) |
| `/picks` | Required | Live +EV pick board (main product page) |
| `/results` | Required | Historical settled picks with performance metrics |
| `/account` | Required | Subscription status, tier, billing management |
| `/pricing` | Public | Plan comparison and Stripe checkout entry |
| `/sign-in` | Public | Clerk sign-in |
| `/sign-up` | Public | Clerk sign-up |

### `/picks` page requirements
- Server-rendered initial load (SSR via Supabase server client)
- Supabase Realtime subscription for live updates (client component)
- Filter controls: sport, market, stars (min), max time to game
- Sort: by EV (default), stars, commence_time
- Columns shown: Stars, Team, Market (with point), Best Book, Odds, EV%, Kelly%, Game Time
- Odds displayed in American format (convert from decimal: `(D-1)*100` if D≥2, else `-100/(D-1)`)
- Rows filtered server-side by user's tier (via Clerk middleware reading publicMetadata.tier)
- Empty state if no picks currently pass filters

### `/results` page requirements
- Summary stats at top: overall record (W-L-P), ROI%, win rate, total picks tracked
- Table of settled picks (paginated, newest first)
- Filter by sport, market, date range, result
- Each row shows: date, team, market, odds, EV%, result (W/L/P), CLV

---

## Tech Stack

### Python Worker (Railway)
- Long-running worker service (not cron — the scheduler manages its own cadence)
- Existing `bet_scheduler7.py` is the entrypoint (minimal modification)
- New `supabase_writer.py` module handles all Supabase writes
- All secrets injected via Railway environment variables
- `models/` and `mappings/` directories bundled in repo/image
- `snapshots/` Parquet data written to Railway volume or local (non-critical path)

### Database (Supabase)
- PostgreSQL with Row Level Security
- Realtime enabled on `current_picks` table
- Service role key used by Python worker (full write access)
- Anon key used by Next.js frontend (read-only, filtered by RLS)
- RLS policy on `current_picks`: authenticated users read rows where `stars >= tier_min_stars(auth.jwt())`

### Auth (Clerk)
- Next.js middleware protects `/picks`, `/results`, `/account`
- `publicMetadata.tier` set server-side via Clerk API after Stripe payment
- Clerk user ID stored in Supabase `users` table (if needed for per-user features later)

### Billing (Stripe)
- Stripe Checkout for plan selection
- Webhook handler: `checkout.session.completed` → set Clerk metadata tier
- Webhook handler: `customer.subscription.deleted` → downgrade tier to `null` or `"basic"`
- Price IDs mapped to tier strings in env vars

### Frontend (Next.js + Vercel)
- App Router (Next.js 14+)
- Tailwind CSS (utility-first styling)
- shadcn/ui (component library)
- `@supabase/ssr` for server/client Supabase access
- `@clerk/nextjs` for auth
- `@stripe/stripe-js` for client-side Stripe
- Deployed to Vercel (main branch auto-deploy)

---

## Discord Integration (Preserved)

Discord is NOT being removed. It remains the primary real-time notification channel.

- `bet_scheduler7.py` continues posting to tier-specific webhooks
- Tier routing: stars 5 → VIP, stars 3–4 → Premium, stars 1–2 → Basic
- Sport-specific guards (NCAAF spread limits, time-to-game cutoffs) stay unchanged
- The web app is an additional output, not a replacement

---

## Supabase Realtime Strategy

- Python worker writes to `current_picks` on each cycle (~every 15 min)
- Next.js client subscribes to `current_picks` with `on('postgres_changes', ...)`
- Frontend updates the table in-place without page reload
- No websocket connection needed in Python — standard Supabase REST upserts trigger Realtime

---

## Performance & Cost Considerations

- The Odds API: credits consumed by Python worker only (no change from current)
- Supabase: free tier supports Realtime + ~500MB DB — more than sufficient for v1
- Vercel: free tier for frontend
- Railway: hobby plan sufficient for single long-running worker
- Clerk: free tier for <10k MAU
- Stripe: 2.9% + 30¢ per transaction (standard)
