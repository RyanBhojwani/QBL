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
| 3 | Railway Deployment | Python worker running on Railway | ⬜ Not started |
| 4 | Next.js Scaffold | App exists, reads picks from Supabase | ⬜ Not started |
| 5 | Auth & Tiers | Clerk auth, tier-gated picks page | ⬜ Not started |
| 6 | Billing | Stripe checkout sets Clerk tier | ⬜ Not started |
| 7 | Results Page | Ledger/performance display | ⬜ Not started |
| 8 | Landing Page | Static HTML migrated to Next.js route | ⬜ Not started |

---

## Phase 1 — Supabase Schema ✅ COMPLETE

**What was built:**
- All 4 tables live in Supabase: `model_runs`, `current_picks`, `tracked_picks`, `settled_picks`
- All indexes and functional unique indexes created
- `upsert_tracked_picks_batch` PostgreSQL RPC function deployed (handles `COALESCE(point, -9999.0)` conflict key that PostgREST can't express directly)
- 2 migrations in history: `initial_schema`, `upsert_tracked_picks_fn`
- MCP configured in `.mcp.json`

**Key design decisions locked in:**
- `current_picks` lifecycle: delete-all + insert on each successful run (brief empty window acceptable for MVP)
- `tracked_picks` unique key: `(game_id, team, market, COALESCE(point, -9999.0))` — uses functional index, conflict handled via RPC
- `settled_picks` dedup key: `(game_id, market, team)` — standard columns, supports standard upsert

---

## Phase 2 — Python Write Layer ✅ COMPLETE

**What was built:**

`Original_Code/supabase_writer.py` — all 6 functions implemented and tested:
- `start_model_run()` — inserts `model_runs` row at cycle start
- `fail_model_run()` — marks cycle as error with exception string
- `finish_model_run()` — marks cycle success + writes `current_picks`
- `write_current_picks()` — delete-all then batch insert from `latest_output`
- `upsert_tracked_picks()` — calls `upsert_tracked_picks_batch` RPC in 500-row batches
- `upsert_settled_picks()` — renames `W/L`→`result`, filters to graded rows, standard upsert

**Wired into:**
- `bet_scheduler7.py` `main()`: start → fail/finish → upsert_tracked_picks
- `settle_ledger.py` `main()`: upsert_settled_picks after CSV write

**All functions**: gated by `SUPABASE_ENABLED=1`, non-fatal on failure (warn + continue).

**Verified**: `_test_supabase.py` — 35/35 passing, covering inserts, updates, upsert idempotency, conflict resolution, and cleanup.

**Python dependency note**: `supabase==2.18.1` required. Newer versions (2.19+) pull in `storage3>=2.x` → `pyiceberg` → MSVC build tools needed on Windows/Python 3.14. Pin at 2.18.1 until this is resolved upstream or a prebuilt wheel becomes available.

---

## Phase 3 — Railway Deployment 🔶 WORKER PREPARED — PENDING SERVICE CREATION

**What was built (2026-05-05):**
- `requirements.txt` — all deps, `supabase==2.18.1` + `storage3==0.12.1` pinned, `tzdata` for Linux
- `railway.toml` — `startCommand = "cd Original_Code && python -u bet_scheduler7.py"`, restart on failure
- `bet_scheduler7.py` changes (6 surgical edits, no logic touched):
  - `logging.basicConfig()` setup — structured logs readable in Railway log stream
  - `DATA_DIR` / `BETS_PATH` / `SNAP_DIR` env-var-configurable paths
  - Bot thread guarded: only starts if `DISCORD_TOKEN` is set
  - `raise` replaced with `log + sleep(60) + continue` — one bad API call no longer kills the worker
  - Jupyter `clear_output`/`display` removed — replaced with `logger.info("cycle complete | ...")`

**Remaining manual steps (in Railway dashboard):**
- [ ] Push repo to GitHub
- [ ] Create Railway service → Deploy from GitHub repo
- [ ] Add Railway Volume → mount at `/data` → set `DATA_DIR=/data`
- [ ] Set all env vars (full list in PROJECT_STATUS.md)
- [ ] Verify in logs: `Worker starting —` + `cycle complete |` every 15 min
- [ ] Confirm Discord alerts fire and Supabase `current_picks` updates each cycle

**Local test command** (from `Original_Code/` with `secrets.env` + `settings.env` present):
```bash
python -u bet_scheduler7.py
```

**Railway start command** (auto-used from `railway.toml`):
```bash
cd Original_Code && python -u bet_scheduler7.py
```

**Done when**: Scheduler runs on Railway for 24 hours without crashing. Discord alerts appear. Supabase `current_picks` updates on schedule.

**Dependencies**: Phase 2 ✅

---

## Phase 4 — Next.js Scaffold + Picks Page

**Goal**: Next.js app exists. A `/picks` page renders real picks from Supabase `current_picks`. No auth yet — all picks visible.

**Files to create:**
```
app/
  package.json
  app/
    layout.tsx
    picks/
      page.tsx          # server component — fetches current_picks
      PicksTable.tsx    # client component — Realtime subscription
  lib/
    supabase/
      server.ts         # server-side Supabase client
      client.ts         # client-side Supabase client
```

**Init commands:**
```bash
npx create-next-app@latest app --typescript --tailwind --app --no-src-dir
cd app
npm install @supabase/supabase-js @supabase/ssr
npx shadcn@latest init
```

**Picks page minimum requirements:**
- Server component: `supabase.from('current_picks').select('*').order('ev', { ascending: false })`
- `<PicksTable />` client component subscribes to Realtime for live updates
- Columns: Stars, Team, Market, Book, Odds (American format), EV%, Game Time
- Filter bar: sport dropdown, market dropdown, min-stars selector
- Empty state: "No picks currently available"

**Env vars (Vercel):**
```
NEXT_PUBLIC_SUPABASE_URL=https://xktzdsyfsvtwxfixhsgy.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_...
```

**Enable Realtime**: Supabase dashboard → Table Editor → `current_picks` → Realtime toggle ON.

**Done when**: `localhost:3000/picks` shows real picks from Supabase. Update a row in Supabase dashboard — table refreshes without page reload.

**Dependencies**: Phase 1 ✅ (tables exist). Phase 2 helpful but not required — can seed test data manually.

---

## Phase 5 — Auth & Tier Access

**Goal**: Users must sign in. Their Clerk tier determines which picks rows they see.

**Files to create/modify:**
- `app/middleware.ts` — Clerk middleware protecting `/picks`, `/results`, `/account`
- `app/app/layout.tsx` — wrap in `<ClerkProvider>`
- `app/app/sign-in/[[...sign-in]]/page.tsx`
- `app/app/sign-up/[[...sign-up]]/page.tsx`
- `app/app/picks/page.tsx` — read tier from Clerk metadata, pass min-stars to query

**Tier filtering (server-side only):**
```typescript
const tier = user?.publicMetadata?.tier ?? 'basic'
const minStars = tier === 'vip' ? 5 : tier === 'premium' ? 3 : 1
const { data } = await supabase
  .from('current_picks')
  .select('*')
  .gte('stars', minStars)
  .order('ev', { ascending: false })
```

**Supabase RLS (add in this phase):**
```sql
CREATE POLICY "authenticated_read" ON current_picks
  FOR SELECT TO authenticated USING (true);
```
Tier filtering stays in Next.js server code, not RLS.

**Done when**: Unauthenticated → redirected to sign-in. Basic → all picks. Premium → 3+ stars. VIP → 5 stars only.

**Dependencies**: Phase 4 ✅

---

## Phase 6 — Billing (Stripe)

**Goal**: User purchases a plan → Stripe webhook sets Clerk tier → picks access granted.

**Files to create:**
- `app/app/pricing/page.tsx` — plan comparison + checkout buttons
- `app/app/api/stripe/checkout/route.ts` — creates Stripe Checkout Session
- `app/app/api/stripe/webhook/route.ts` — handles `checkout.session.completed` and `customer.subscription.deleted`

**Webhook logic:**
```typescript
// On checkout.session.completed:
await clerkClient.users.updateUserMetadata(clerkUserId, {
  publicMetadata: { tier }  // 'basic' | 'premium' | 'vip'
})

// On customer.subscription.deleted:
await clerkClient.users.updateUserMetadata(clerkUserId, {
  publicMetadata: { tier: null }
})
```

**Env vars needed:**
```
STRIPE_SECRET_KEY
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY
STRIPE_WEBHOOK_SECRET
STRIPE_PRICE_BASIC
STRIPE_PRICE_PREMIUM
STRIPE_PRICE_VIP
```

**Done when**: Test purchase with Stripe test card → Clerk metadata updates → `/picks` shows tier-filtered picks.

**Dependencies**: Phase 5 ✅

---

## Phase 7 — Results Page

**Goal**: `/results` shows historical settled picks with win/loss record and ROI stats.

**Files to create:**
- `app/app/results/page.tsx` — server component, queries `settled_picks`
- `app/app/results/ResultsTable.tsx` — client component with filters

**Stats to compute from `settled_picks`:**
- Record: W / L / P counts
- Win rate: W / (W + L) %
- ROI: `sum((odds - 1) * kelly * W_indicator) / sum(kelly)`
- Breakdown by sport and market type

**Done when**: `/results` shows real historical picks with accurate W/L record.

**Dependencies**: Phase 3 ✅ (settler writing to Supabase on Railway)

---

## Phase 8 — Landing Page Migration

**Goal**: `Homepage/index.html` rebuilt as the Next.js root route (`/`). Same design, same copy, same dark theme — in JSX + Tailwind.

**Files to create:**
- `app/app/page.tsx` — root route
- `app/components/landing/` — Hero, Features, Stats, CTA section components

**Design reference**: `Homepage/index.html` + `Homepage/styles.css`

**Color palette:**
- Background: `#0a0e17`
- Teal accent: `#00d4aa`
- Amber accent: `#f59e0b`
- Discord purple: `#5865F2`

**Typography**: Space Grotesk (headers), Inter (body) — add via `next/font`

**Done when**: `localhost:3000` is visually identical to the static `Homepage/index.html`.

**Dependencies**: Phase 4 ✅

---

## Dependency Graph

```
Phase 1 (Schema) ✅
    └─► Phase 2 (Python Writes) ✅
            └─► Phase 3 (Railway)
                    └─► Phase 7 (Results)

Phase 1 (Schema) ✅
    └─► Phase 4 (Next.js Scaffold)
            └─► Phase 5 (Auth)
                    └─► Phase 6 (Billing)

Phase 4 (Next.js Scaffold)
    └─► Phase 8 (Landing Page)
```

Phases 3 and 4 can run in parallel — both are unblocked right now.
