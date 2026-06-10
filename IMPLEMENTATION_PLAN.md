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
| 12.5 | UX Audit & Improvements | Onboarding, tooltips, empty/error/loading states, picks table clarity, account detail | ⬜ Not started |
| 12.7 | Legal & Compliance | ToS, Privacy Policy, disclaimers, 18+ notice, geo-disclaimer, FTC compliance | ⬜ Not started |
| 13 | Content Pass | Replace placeholder copy with real marketing content and accurate stats | ⬜ Not started |
| 13.5 | Marketing & SEO | Meta tags, OG images, analytics, sitemap, social proof, CTA audit | ⬜ Not started |
| 14 | Stripe Live Mode | Switch from test payments to real payments | ⬜ Not started |
| 14.5 | Discord Role Sync | Stripe/Clerk → Discord role assignment, replacing Whop | ⬜ Not started |
| 15 | Security Audit | Harden all routes and inputs before public launch | ⬜ Not started |
| 16 | Mobile QA | All pages verified on iOS Safari and Android Chrome | ⬜ Not started |
| 17 | Deployment Docs | Comprehensive RUNBOOK.md | ⬜ Not started |

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

## Implementation Order

```
Phase 7    (Results page)              ← ✅ DONE
Phase 8    (Discord links)             ← ✅ DONE
Phase 9    (Admin config UI)           ← ✅ DONE
Phase 10   (Picks filtering)           ← ✅ DONE
Phase 10.5 (Bug fixes & navigation)    ← next up; unblocked
Phase 11   (Snapshot pipeline)         ← unblocked, Python-side
Phase 12   (Model retraining)          ← after Phase 11
Phase 12.5 (UX audit)                  ← after Phase 12; informs content
Phase 12.7 (Legal & compliance)        ← after Phase 12.5; informs content
Phase 13   (Content pass)              ← after 12.5 and 12.7; collaborative
Phase 13.5 (Marketing & SEO)           ← after Phase 13; content must be final
Phase 14   (Stripe live mode)          ← needs Stripe account activation
Phase 14.5 (Discord role sync)         ← after live mode; requires real Stripe + real Clerk tiers
Phase 15   (Security audit)            ← after Discord sync; covers new OAuth routes
Phase 16   (Mobile QA)                 ← before final launch
Phase 17   (Deployment docs)           ← last
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
                                                    └─► Phase 13 (Content)
                                                            └─► Phase 13.5 (Marketing & SEO)
                                                                    └─► Phase 14 (Stripe Live)

Phase 14 (Stripe Live)
    └─► Phase 14.5 (Discord Role Sync)
Phase 15 (Security audit) → final launch gate
Phase 16 (Mobile QA) → final launch gate
Phase 9 (Admin UI) ✅
Phase 17 — last
```
