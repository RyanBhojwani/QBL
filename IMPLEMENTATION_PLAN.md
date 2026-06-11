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
| 10.5 | Bug Fixes & Navigation Audit | Stripe redirect fix, inter-page nav, admin auto-sport, success state, 404 page | ⬜ Not started |
| 11 | Snapshot Pipeline | Daily snapshots auto-upload to Supabase Storage + nightly local download | ✅ Done |
| 12 | ML Retraining | Workflow for retraining models on accumulated data and deploying to Railway | ✅ Done |
| 12.5 | UX Audit & Improvements | Onboarding, tooltips, empty/error/loading states, picks table clarity, account detail | ✅ Done |
| 12.7 | Legal & Compliance | ToS, Privacy Policy, disclaimers, 18+ notice, geo-disclaimer, FTC compliance | ✅ Done |
| 12.8 | Raw Model Output Pipeline | Write all pre-threshold model output to Supabase on every worker run | ✅ Done |
| 12.9 | Explore Tab | Team Search + Sportsbook Explorer using raw model output | ✅ Done |
| 12.95 | Intelligent Schedule Automation | Auto-configure active sports and poll cadence based on real-time game schedules | ✅ Done |
| 13 | Content Pass | Replace placeholder copy with real marketing content and accurate stats | ⬜ Not started |
| 13.5 | Marketing & SEO | Meta tags, OG images, analytics, sitemap, social proof, CTA audit | ⬜ Not started |
| 14 | Stripe Live Mode | Switch from test payments to real payments | ⬜ Not started |
| 14.5 | Discord Role Sync | Stripe/Clerk → Discord role assignment, replacing Whop | ⬜ Not started |
| 15 | Security Audit | Harden all routes and inputs before public launch | ⬜ Not started |
| 16 | Mobile QA | All pages verified on iOS Safari and Android Chrome | ⬜ Not started |
| 17 | Deployment Docs | Comprehensive RUNBOOK.md | ⬜ Not started |
| 18 | Total Line Normalization | Convert totals/spreads across books to a common line for proper EV comparison | ⬜ Not started |

---

## Phases 0–10 — COMPLETE

All phases through picks filtering and admin config are fully implemented and live. See `PROJECT_STATUS.md` for the full breakdown of what was built, including all bug fixes applied on 2026-05-19.

---

## Phase 10.5 — Bug Fixes & Navigation Audit

**Goal**: Fix known bugs and ensure every inter-page path on the site is intentional and correct before any further build work.

**Bug fixes:**

1. **Stripe redirect fix** — `NEXT_PUBLIC_APP_URL` is set to `localhost:3000` on Vercel. Update to `https://quantbetlabs.vercel.app`. The code in `/api/checkout` is already correct; this is a Vercel env var change only.
2. **Post-purchase success state** ✅ — `SuccessBanner` component created (`components/SuccessBanner.tsx`). Reads `?success=1` from searchParams on the picks page, shows dismissible banner with tier confirmation, picks explainer, Discord CTA, and link to the How To Use guide.
3. **Custom 404 page** ✅ — `app/not-found.tsx` created. Branded with QUANTBETLABS style, large faded 404, links back to Home and Dashboard.

**Navigation audit — every inter-page path to verify and fix:**

- Landing page → Pricing (is there a clear CTA that goes directly to pricing, not just Discord?)
- Landing page → Performance (the "View full performance history →" link exists — confirm it works)
- Public `/performance` → Pricing (locked breakdown tables show a subscribe CTA — confirm it links to `/pricing`)
- `/how-it-works` → Pricing (confirm there's a CTA at the bottom)
- `/faq` → Pricing or Discord (confirm CTAs exist)
- `/rules` → Pricing or Discord (confirm CTAs exist)
- `/pricing` → `/` (confirm nav and logo link back to landing)
- After sign-in → `/dashboard/picks` (confirm Clerk redirect is set correctly)
- After sign-up → `/pricing` (confirm Clerk redirect is set correctly)
- After sign-out → `/` (confirm)
- Dashboard nav → all dashboard pages (verify all links work)
- Dashboard → public pages (is there any way to get back to the public site from the dashboard?)
- `/dashboard/picks` upgrade wall → `/pricing` (confirm link)
- `/dashboard/education` upgrade wall → `/pricing` (confirm link)
- `/dashboard/how-to-use` upgrade wall → `/pricing` (confirm link)

**Admin auto-sport detection:**

- Current behavior: admin must manually toggle sports on/off in the config panel.
- New behavior: on page load, the admin panel queries `current_picks` for distinct `sport` values, pre-checks sports that currently have active picks, and shows any sports in `worker_config` that are toggled on but have no current picks (flagging them as "no active picks").
- Rationale: reduces manual admin overhead and prevents the worker from scanning dead sports.

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

## Phase 12.5 — UX Audit & Improvements

**Goal**: Audit and fix the user experience end-to-end before writing final copy or going live. UX decisions made here will inform what content is needed in Phase 13.

**New subscriber onboarding:**
- After first successful purchase, the picks page currently provides zero orientation. Add a dismissible onboarding banner or modal that explains: what the stars mean, how to read the picks table, and that Discord alerts accompany each pick.
- On first visit to the dashboard (new user, no prior preferences), default filters to "all sports, all books, tier-appropriate star range" rather than showing an empty result.

**Jargon / tooltips on the picks table:**
- Add inline tooltip icons (ⓘ) to all technical column headers: EV, Kelly, CLV, Stars, Devig, Sharp Odds.
- Each tooltip should show a one-sentence plain-English explanation. Users paying $25–$100/mo should not need to Google what the columns mean.

**Empty states:**
- Picks page: when the model has found zero picks that pass filters (or zero picks match the current filter selection), show a friendly message with the last-updated timestamp and the next expected poll time.
- Performance tables: if a segment has zero bets (e.g., a star tier with no history), show "No data yet" instead of dashes or zeros.

**Loading & error states:**
- Picks page: show skeleton rows while Supabase fetches, not a blank page.
- Performance page: show a loading state while model results are fetched.
- Both pages: if the fetch fails, show a user-facing error message with a retry button rather than a silent failure.

**Performance page accessibility:**
- Add a plain-English summary section above the stat cards aimed at a layperson sports bettor. E.g., "Since launch, the model has gone X-Y-Z on picks, returning X% on investment from a $1,000 starting bankroll."
- Consider adding tooltips to financial metrics (Sharpe, Sortino, CAGR, Max Drawdown) — these are opaque to most users.

**Account page improvements:**
- Show subscription renewal date and price alongside tier name.
- Clarify what happens at cancellation (access continues until end of billing period, then tier clears).

**Upgrade wall improvements:**
- Walls should clearly list the specific features unlocked by upgrading to the next tier, not just say "upgrade to access."
- Include a direct link to the specific pricing tier, not just `/pricing`.

**Cancellation UX:**
- After a user cancels via the Stripe portal, they return to the app. Is there a confirmation message? Is the tier immediately shown as changing or is it clear access continues until end of period? Audit and fix.

**Done when:** All states above are handled, tooltips exist on all picks table columns, onboarding banner fires on first post-purchase visit.

---

## Phase 12.7 — Legal & Compliance

**Goal**: Ensure the site is legally defensible as a gambling-adjacent subscription service before going live. This phase informs what copy is allowed in Phase 13.

**New pages to create:**

- `/terms` — Terms of Service
  - Subscription terms: what you get, billing cadence, cancellation policy (access until end of period), no refunds policy or refund window if applicable
  - Limitation of liability: company is not liable for betting losses incurred based on picks
  - No gambling advice: service is informational only; users bet at their own risk
  - Acceptable use: must be 18+, must be in a jurisdiction where sports betting is legal
  - Account termination terms

- `/privacy` — Privacy Policy
  - What data is collected: name, email address (Clerk), payment info (Stripe, not stored directly), filter preferences (Supabase), usage data (analytics if added in Phase 13.5)
  - How data is stored and with which third parties (Clerk, Stripe, Supabase, Vercel)
  - Data retention and deletion: how users can request account deletion
  - GDPR/CCPA: rights of EU and California residents (access, deletion, portability)

**Disclaimer language — required on these pages:**
- All pages displaying picks or performance data must include: *"For informational and entertainment purposes only. Past performance does not guarantee future results. This is not financial, gambling, or investment advice. Always bet responsibly and within the laws of your jurisdiction."*
- Landing page: the ">100% Annual ROI" claim must be accompanied by a methodology footnote or link to the performance page showing the underlying data, time period, and sample size. The FTC requires advertised performance figures to be truthful and not misleading.

**18+ and geo-disclaimer:**
- Add a visible 18+ notice to the footer sitewide.
- Add a statement that the service is intended for users in jurisdictions where sports betting is legal. Users are responsible for knowing and complying with their local laws.
- Decision needed: implement IP-based geo-blocking for clearly illegal jurisdictions, or rely on disclaimer? For launch, disclaimer is the minimum viable approach.

**Footer links:**
- Terms of Service, Privacy Policy, and the informational disclaimer must be linked from the footer on every page (public and dashboard).

**Pricing page subscription terms:**
- Clearly state billing cadence (monthly), what happens at cancellation (access until period end), and link to Terms of Service.

**Done when:** `/terms` and `/privacy` pages exist, disclaimer appears on all pick/performance pages, footer links are live sitewide, pricing page subscription terms are clear.

---

## Phase 12.8 — Raw Model Output Pipeline

**Goal**: Write all pre-threshold model output to Supabase on every worker run, enabling the Explore tab features in Phase 12.9. This is a backend-only phase with no frontend changes.

**New Supabase table: `raw_model_output`**

Same 16 columns as `current_picks` plus `home_team` and `away_team` (both already present on the board from the Odds API response). EV, Kelly, and CLV values can be any value including negative — no threshold filtering applied. The table is fully wiped and rewritten on every worker run (~15 min cadence).

| Column | Type | Notes |
|--------|------|-------|
| `sport` | text | |
| `game_id` | text | |
| `commence_time` | timestamptz | |
| `home_team` | text | from Odds API |
| `away_team` | text | from Odds API |
| `team` | text | side name |
| `market` | text | h2h, spreads, totals |
| `point` | float | spread/total value, null for h2h |
| `book` | text | bookmaker slug |
| `book_odds` | float | decimal odds at this book |
| `sharp_odds` | float | model fair value |
| `ev` | float | can be negative |
| `kelly` | float | can be negative |
| `clv_prob_med` | float | |
| `stars` | int | computed from clv_prob_med binning regardless of threshold |
| `outcome_threshold` | float | |

**RLS:** Authenticated users only — no anon read. Tier enforcement is handled in the application layer.

**Python changes (all additive — no existing functions modified):**

- `Original_Code/run_edge_board_v2.py`: add `build_full_output(board)` — identical logic to `build_edge_output()` (same ML model loading, same EV/Kelly/CLV/stars computation) but with the threshold filter lines removed. Returns the complete dataframe. Does not replace or modify `build_edge_output()`.
- `Original_Code/supabase_writer.py`: add `write_raw_output(df)` — executes `DELETE` on the full table, then bulk-inserts the new frame. Same pattern as other write functions.
- `Original_Code/bet_scheduler7.py`: after the existing `build_edge_output()` call in `run_once()`, add a call to `build_full_output()` and `write_raw_output()`. Two additional lines in `run_once()`.

**Done when:** `raw_model_output` table exists in Supabase, is populated after each worker run, and is verifiably wiped and rewritten (not appended to) on subsequent runs.

---

## Phase 12.9 — Explore Tab

**Goal**: Give premium and VIP subscribers a self-serve way to look up any team or sportsbook and see what the model says, without those results being gated by pick thresholds. This is a research tool, not a picks feed.

**Access:** Premium and VIP only. Basic subscribers and unauthenticated users see an upgrade wall.

**Route:** `/dashboard/explore`

**Nav:** "Explore" added to the dashboard navigation alongside Picks, Performance, Education, etc.

**Layout:** Pill toggle at the top of the page switches between two modes: **Team Search** and **Sportsbook Explorer**. Default mode is Team Search on first visit.

---

### Mode 1 — Team Search

**Step 1 — Team dropdown**
A searchable dropdown populated with distinct `team` values from `raw_model_output` where `commence_time` is in the future (or within 3 hours past, to catch in-progress games). User types a team name or scrolls and clicks. No logos for now — clean text dropdown.

**Step 2 — Book filter**
After a team is selected, a row of multi-select book chips appears (FanDuel, DraftKings, BetMGM, Caesars, etc.) populated from distinct `book` values in the table. Default: all books selected.

**Step 3 — Results**
The page finds the `game_id` for the selected team and pulls all rows for that game across all markets. Results are organized into three sections:

**Game header:** "New York Knicks vs Indiana Pacers · Tonight 7:30 PM ET"

```
MONEYLINE
Knicks    +110  FanDuel   EV: 3.2%
Pacers    -130  DraftKings  EV: —

SPREAD
Knicks -3.5   -108  FanDuel   EV: 5.1%
Pacers +3.5   -112  BetMGM    EV: —

TOTAL
Over  224.5   -112  Caesars   EV: 1.8%
Under 224.5   -108  FanDuel   EV: —
```

For each outcome, the displayed line is the **best book among the user's selected books**: highest EV if any selected book has EV > 0, otherwise highest odds. EV shown as a percentage when positive, "—" when ≤ 0. No star ratings displayed anywhere on this page.

**No game found state:** If the selected team has no rows in `raw_model_output`, show: *"No game found for [Team] in current model data. Check back closer to game time."*

---

### Mode 2 — Sportsbook Explorer

**Step 1 — Book selection**
Multi-select chips for all available books (same set as team search). User selects one or more books. OR logic: show me all EV > 0 lines available on any of these books.

**Step 2 — Results table**
All rows from `raw_model_output` where `book` is in the selected set and `ev > 0`, sorted highest EV to lowest. Columns:

| Game | Market | Side | Book | Odds | EV |
|------|--------|------|------|------|----|
| Knicks vs Pacers | Spread | Knicks -3.5 | FanDuel | -108 | 5.1% |

No star ratings. EV displayed as a percentage. If no results after book selection: *"No positive EV lines found on selected books right now. Check back after the next model run."*

**Freshness:** Both modes show the same "Last updated X minutes ago" timestamp as the picks page. Data refreshes every ~15 minutes with the worker.

---

**Done when:** `/dashboard/explore` is live, both modes work against real `raw_model_output` data, premium/VIP gate is enforced, and freshness timestamp is accurate.

---

## Phase 12.95 — Intelligent Schedule Automation

**Goal**: Replace the manual admin panel sport/time configuration with an automated system that determines which sports to run and when, based on real-time game schedules. Zero human intervention required for a normal day.

**Problem with the current approach**: The admin panel lets you toggle sports on/off and set poll cadence, but someone still has to remember to do it. If NHL playoffs are running but `ACTIVE_SPORTS` still includes NBA (no games), the worker wastes API quota polling dead leagues. Conversely, if a new sport season starts, it won't be picked up until manually toggled on.

**Architecture:**

1. **Schedule resolver (new function in `bet_scheduler7.py` or a standalone `schedule_resolver.py`)**
   - Runs once at worker startup and once at midnight ET each day
   - Calls The Odds API `/sports` endpoint (already authenticated) to get all currently-in-season leagues
   - Filters to the leagues the worker knows about (the `LEAGUES_*` config)
   - For each active league, calls `/events` or checks the board for upcoming game times that day
   - Returns: `active_sports` (list of leagues with games today or tomorrow), `next_game_time` (UTC timestamp of nearest game start), `last_game_time` (UTC timestamp of latest game start)

2. **Poll cadence auto-calculation**
   - If `next_game_time` is more than 4 hours away: sleep until 90 minutes before (no polling needed yet)
   - From 90 minutes before first game until 30 minutes after last game: use `DAY_POLL_MINUTES` (default 15)
   - Outside active window: use `NIGHT_POLL_MINUTES` (default 60), but auto-skip sports with no games
   - Override: `worker_config` manual settings still take precedence when explicitly set by admin

3. **Supabase `worker_config` integration**
   - Add a `schedule_auto` key (default `true`) — when true, auto-resolver runs; when false, falls back to manual config
   - Auto-resolver writes its computed `active_sports` back to `worker_config` each cycle so the admin panel reflects what's actually running
   - Admin panel gains a read-only "Today's Schedule" display showing what the resolver computed and why

4. **Season-awareness**
   - NHL: October–June (playoffs extend to ~June 20)
   - MLB: April–October
   - NBA: October–June
   - NFL: September–February
   - Soccer: depends on league — resolver checks The Odds API's `active` flag per league
   - MMA/Boxing: event-driven — resolver checks for upcoming events in next 7 days

5. **Failure handling**
   - If The Odds API `/sports` call fails, fall back to last known `active_sports` from `worker_config`
   - Log the fallback with a warning so it's visible in Railway logs

**Done when:** Worker auto-detects which sports have games today, sets poll cadence accordingly, and the admin panel reflects the computed schedule without requiring manual input.

**What was built:**

- **`Original_Code/schedule_resolver.py`** (new) — standalone module, ~320 lines
  - `LEAGUE_THRESHOLDS` dict: 27 league keys (MLB, NHL, NBA, NCAAB, NFL, NCAAF, MMA, Boxing, 8 Grand Slam tennis keys, 10 soccer leagues) each with `sport_group`, `threshold`, `horizon_h`
  - `SPORT_GROUP_CREDITS`: BASEBALL/HOCKEY/NBA/NCAAB/NFL/NCAAF = 3, SOCCER/FIGHTS/TENNIS = 1 (h2h only)
  - `_fetch_events()`: calls `/v4/sports/{league}/events` with commenceTimeFrom/To — free endpoint, no quota cost; retries on 429/5xx; returns 404 as empty list (league off-season)
  - `_days_until_reset()`: parses `x-requests-reset` as Unix timestamp or ISO string; falls back to days remaining in calendar month
  - `run_daily()`: fetches all leagues, threshold-checks each independently, groups by sport, computes credits per poll, reads `x-requests-remaining`, calculates `day_poll_minutes = round(900 / (daytime_budget / credits_per_poll))`, writes `active_sports` + `day_poll_minutes` + `leagues_*` keys to Supabase `worker_config`; respects `SCHEDULE_AUTO=false` for dry-run mode
- **`Original_Code/supabase_writer.py`**: added `upsert_worker_config(key, value)` using `on_conflict="key"`
- **`Original_Code/bet_scheduler7.py`**: added `_daily_schedule_worker()` thread — runs `run_daily()` immediately on startup, then sleeps until 5 AM ET and loops daily
- **`Original_Code/run_edge_board_v2.py`**: added World Cup, Women's WC, UCL, Europa League to both `SOCCER_CFG` sport_key list and `SOCCER_LEAGUE_GROUP` dict (Group A); these were silently falling back to Group E (wrong sigma model)
- **`app/app/dashboard/admin/AdminPanel.tsx`**: added Schedule Automation section at top — toggle for `schedule_auto`, amber warning banner when manual mode is on; `schedule_auto` saved with the rest of the config

---

## Phase 13 — Content Pass

**Goal**: Replace placeholder/hardcoded content with accurate, real marketing copy. This phase runs after UX (12.5) and Legal (12.7) so copy is written to the correct structure and within legal constraints.

**Known items:**
- Landing page stats (Alerts Sent, Leagues Covered) are hardcoded — replace with real numbers pulled from the DB or manually verified and updated
- ">100% Annual ROI" claim on landing page needs methodology footnote per Phase 12.7 legal requirement
- All public page copy should be reviewed for accuracy, tone, and consistency with the brand voice
- Pricing page: subscription terms must match what was finalized in Phase 12.7
- Disclaimer language from Phase 12.7 must be incorporated on all relevant pages

**Pages to review:** `/`, `/how-it-works`, `/performance`, `/pricing`, `/faq`, `/rules`, `/terms`, `/privacy`

---

## Phase 13.5 — Marketing & SEO

**Goal**: Ensure the site is discoverable, shareable, and instrumented to measure conversion before going live. This phase runs after content is finalized so we're optimizing real copy, not placeholders.

**SEO — meta and crawlability:**
- Add unique `<title>` and `<meta name="description">` to every public page. Currently generic or missing.
- `sitemap.xml` — Next.js can auto-generate this. All public pages should be included; dashboard routes excluded.
- `robots.txt` — explicitly disallow `/dashboard/*` and `/api/*`; allow all public routes.

**Social sharing:**
- Open Graph (`og:title`, `og:description`, `og:image`) tags for all public pages. When the site is shared on Discord, Twitter, or iMessage it currently shows a blank preview.
- Twitter card tags (`twitter:card`, `twitter:title`, `twitter:image`).
- OG image: create a single branded default image (1200×630) showing the Quant Bet Labs name and key stat. Can be a static file.

**Analytics & conversion tracking:**
- Add Vercel Analytics (zero-config, privacy-friendly, no cookie consent required) for pageview data.
- Define and instrument key conversion events: "clicked Get Early Access," "landed on /pricing," "initiated checkout," "completed checkout." These fire to analytics and let you see where users drop off in the funnel.
- If GA4 is preferred over Vercel Analytics, implement that instead — but decide before Phase 14 so data is collecting from day one.

**Landing page social proof & CTA audit:**
- Replace hardcoded "500+ Alerts Sent" and "16 Leagues Covered" with real numbers from the database or a manually updated constant that is accurate at launch.
- Review the CTA hierarchy: the primary CTA is a free Discord join, the secondary is "Get Early Access" (paid). Decide: is the goal to grow free Discord members or paid subscribers? If paid, the hierarchy may need to flip.
- Consider adding real Discord member count (via Discord widget or manual update) as social proof.
- Consider adding a small testimonials or results section if any early users/testers have feedback to share.

**Pre-launch mechanism (optional):**
- If the site is not opening to the general public on day one, add an email capture ("Join the waitlist") on the landing page so you can build a list before opening billing. Remove once live.

**Done when:** All public pages have unique meta titles/descriptions, OG tags are in place, sitemap.xml and robots.txt exist, analytics is collecting data, social proof numbers are accurate.

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

## Phase 14.5 — Discord Role Sync (Stripe/Clerk → Discord)

**Goal**: Replace Whop as the Discord permissions layer. Users who subscribe via Stripe should automatically receive the correct Discord role for their tier, and lose it when they cancel. Discord becomes the real-time alert channel; role access must mirror the Stripe subscription state exactly.

**Background**: Previously Discord permissions were managed through Whop. Whop is no longer in the stack — subscriptions are now handled entirely through Stripe + Clerk. Discord channel access is currently ungated (anyone with the invite link can join any channel), which means paying subscribers get no exclusive access and the Discord value proposition is broken.

**Architecture:**

Discord role sync should be event-driven, triggered by the same Stripe webhook events already being handled in `/api/webhooks/stripe`. No polling, no scheduled jobs.

1. **Supabase table: `discord_connections`**
   - Columns: `clerk_user_id` (PK), `discord_user_id`, `discord_username`, `connected_at`
   - Stores the mapping between a Clerk user and their Discord account after OAuth
   - RLS: service key only

2. **Discord OAuth flow (new API route: `/api/discord/connect`)**
   - User clicks "Connect Discord" on the Account page
   - Redirects to Discord OAuth (`identify` + `guilds.join` scopes)
   - Callback route (`/api/discord/callback`) exchanges code for token, fetches Discord user ID and username, stores in `discord_connections`, then uses the bot token to add the user to the guild and assign the correct role based on their current Clerk tier
   - On success, redirects back to Account page with a `?discord=connected` param

3. **Role assignment on webhook events**
   - In `/api/webhooks/stripe`, after updating Clerk tier on `checkout.session.completed`, `customer.subscription.updated`, and `customer.subscription.deleted`:
     - Look up `discord_connections` by `clerk_user_id`
     - If a Discord connection exists, call Discord API to assign/remove the appropriate role
   - Tier → Discord role mapping (roles must be created in the Discord server):
     - `basic` → Basic role
     - `premium` → Premium role
     - `vip` → VIP role
     - cancelled / null → remove all tier roles

4. **Discord server setup (manual, one-time)**
   - Create three roles in the Discord server: Basic, Premium, VIP
   - Set channel permissions so each tier's alert channel is only visible to that role (and higher tiers)
   - Create a bot application in the Discord Developer Portal, add it to the server with `bot` and `applications.commands` scopes, `Manage Roles` permission
   - Store bot token as `DISCORD_BOT_TOKEN` env var on Vercel and Railway
   - Store guild ID as `DISCORD_GUILD_ID` env var
   - Store role IDs as `DISCORD_ROLE_BASIC`, `DISCORD_ROLE_PREMIUM`, `DISCORD_ROLE_VIP` env vars

5. **Account page UI**
   - If Discord is not connected: show "Connect Discord for real-time alerts" button that initiates the OAuth flow
   - If Discord is connected: show Discord username and tier role, with a "Disconnect" option
   - Connection status fetched server-side from `discord_connections`

6. **Edge cases**
   - User changes tier (upgrade/downgrade): old role removed, new role assigned in the same webhook event
   - User cancels: all tier roles removed; they remain in the server as a free member (they keep access to the free/public channels)
   - User reconnects a different Discord account: old mapping replaced
   - Discord account not connected when subscription changes: no action; the webhook logs a warning but does not fail

**New env vars (Vercel + Railway):**
- `DISCORD_BOT_TOKEN` — bot token from Discord Developer Portal
- `DISCORD_GUILD_ID` — server ID
- `DISCORD_ROLE_BASIC` — role ID for Basic tier
- `DISCORD_ROLE_PREMIUM` — role ID for Premium tier
- `DISCORD_ROLE_VIP` — role ID for VIP tier
- `DISCORD_CLIENT_ID` — OAuth app client ID (for OAuth flow)
- `DISCORD_CLIENT_SECRET` — OAuth app client secret (for OAuth flow)
- `NEXT_PUBLIC_DISCORD_CLIENT_ID` — same client ID, exposed to client for the OAuth redirect URL

**Done when:** A user subscribes via Stripe, connects their Discord account from the Account page, and immediately appears in the correct tier channel on Discord. A cancelled user loses role access within seconds of the Stripe webhook firing.

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

## Phase 18 — Total Line Normalization

**Goal**: Convert totals and spreads from different line values to a common reference line so EV across books can be compared apples-to-apples. Currently, FanDuel offering Over 5.5 and DraftKings offering Over 6.0 in the same NHL game are stored as separate rows — the Explore tab shows blanks when a user's book only has the non-consensus line.

**The problem in detail:**
`mainTotalPoint()` in `ExploreTab.tsx` picks the most common total line across books (e.g., 6.0). If a user's only sportsbook has Over 5.5, the row is filtered out and they see dashes. Over 5.5 and Over 6.0 are genuinely different bets — you can't directly compare their odds without knowing `P(exactly 6 goals)`. The same problem applies to spreads where books shade off different key numbers.

**Conversion mathematics:**
For any sport, moving the total by 0.5 from line L to line L+0.5 requires `P(total = L+0.5 rounded to next integer)`:
```
P(Over L) = P(Over L+0.5) + P(total = ceil(L+0.5))
odds_at_L = prob_to_decimal(P(Over L))
```
This requires a scoring distribution model per sport.

**Sport-specific distributions:**
| Sport | Distribution | Parameters |
|-------|-------------|------------|
| NHL | Poisson | λ = devigged total from sharp books |
| MLB | Poisson | λ = devigged total from sharp books |
| NBA | Normal | μ = devigged total, σ ≈ 11 (empirical) |
| NFL | Normal + hook mass | μ = devigged total, σ ≈ 14; extra mass at key numbers 3, 7, 10, 14 |
| Soccer | Poisson (goals) | λ = devigged total |

NFL/NBA distributions already implemented by user for existing model — port those here.

**Implementation plan:**
1. New function `normalize_total_line(rows, target_line, sport)` in `odds_engine_v2.py` or a new `line_converter.py`
   - Takes all book rows for one Over/Under outcome
   - Computes fair probability at each book's actual line using the sport's distribution
   - Converts to implied odds at `target_line` (the sharp consensus line)
   - Returns a new set of rows all priced at `target_line`, preserving book identity
2. Call this in `build_full_output()` before storing to `raw_model_output` — all totals normalized to the sharp consensus line
3. Same normalization for spreads at key numbers (NFL primarily)
4. Explore tab drops the `mainTotalPoint()` gymnastics — all rows are already at the same line

**Done when:** Over/Under rows in `raw_model_output` are normalized to the sharp consensus line per game; Explore tab shows populated totals rows for all books regardless of which line they originally priced.

---

## Implementation Order

```
Phase 7    (Results page)              ← ✅ DONE
Phase 8    (Discord links)             ← ✅ DONE
Phase 9    (Admin config UI)           ← ✅ DONE
Phase 10   (Picks filtering)           ← ✅ DONE
Phase 10.5 (Bug fixes & navigation)    ← ✅ DONE
Phase 11   (Snapshot pipeline)         ← ✅ DONE
Phase 12   (Model retraining)          ← ✅ DONE
Phase 12.5 (UX audit)                  ← ✅ DONE
Phase 12.7 (Legal & compliance)        ← ✅ DONE
Phase 12.8 (Raw output pipeline)       ← ✅ DONE
Phase 12.9 (Explore tab)               ← ✅ DONE
Phase 12.95 (Schedule automation)      ← ✅ DONE
Phase 13   (Content pass)              ← next up; collaborative
Phase 13.5 (Marketing & SEO)           ← after Phase 13; content must be final
Phase 14   (Stripe live mode)          ← needs Stripe account activation
Phase 14.5 (Discord role sync)         ← after live mode; requires real Stripe + real Clerk tiers
Phase 15   (Security audit)            ← after Discord sync; covers new OAuth routes
Phase 16   (Mobile QA)                 ← before final launch
Phase 17   (Deployment docs)           ← second-to-last
Phase 18   (Total line normalization)  ← post-launch; improves Explore tab totals accuracy
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
                            └─► Phase 10.5 (Bug Fixes & Nav)
                                    └─► Phase 12.5 (UX Audit)
                                            └─► Phase 12.7 (Legal)
                                                    └─► Phase 12.8 (Raw Output Pipeline)
                                                            └─► Phase 12.9 (Explore Tab)
                                                                    └─► Phase 12.95 (Schedule Automation)
                                                                            └─► Phase 13 (Content)
                                                            └─► Phase 13.5 (Marketing & SEO)
                                                                    └─► Phase 14 (Stripe Live)

Phase 14 (Stripe Live)
    └─► Phase 14.5 (Discord Role Sync)
Phase 15 (Security audit) → final launch gate
Phase 16 (Mobile QA) → final launch gate
Phase 9 (Admin UI) ✅
Phase 17 (Deployment docs) — second-to-last
Phase 18 (Total Line Normalization) — post-launch improvement
```
