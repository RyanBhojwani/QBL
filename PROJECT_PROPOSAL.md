# Project Proposal: Quant Bet Labs

## One-Line Description
A data-driven +EV sports betting platform that uses custom devig models and sport-specific book weighting to surface profitable picks for sports bettors.

## The Problem
Sports betting is exploding, but most bettors lose money because they rely on gut instinct rather than math. The tools that *do* exist to find +EV (positive expected value) bets — like OddsJam ($27/mo) or Trademate ($49-400/mo) — are expensive, have steep learning curves, and use generic one-size-fits-all models. There's an opportunity for a sharper, more transparent tool: one that uses sport-specific book weighting, refined devig methods, and a statistical threshold model to surface only the picks that actually matter. This matters to me because I love both sports and markets — this project sits at the intersection of probability, data science, and something I'd actually use every day.

## Target User
Sports bettors who are past the "just picking favorites" stage and want a data-driven edge — but don't want to pay $50+/month or build their own models. Think: the bettor who already checks multiple sportsbooks for the best line but doesn't have the tools or time to systematically identify +EV opportunities across every market and sport.

## Core Features (v1)
1. **Live +EV Pick Board** — A filterable, sortable table of current +EV opportunities across sports, bet types, and sportsbooks. Each pick shows the book, odds, consensus fair odds, edge %, and expected value.
2. **Custom EV Model** — Python-powered analysis using sport-specific book weighting, multiple devig methods, and a statistical threshold model that filters out marginal picks and only surfaces high-confidence opportunities.
3. **Outcome Tracking & Analytics** — Automatic result tracking: after games complete, the system verifies whether picks hit and displays historical performance metrics (hit rate, ROI, record by sport/bet type).
4. **Dynamic Sport/Schedule Configuration** — Admin controls to adjust which sports are actively scanned and how frequently the model runs, allowing the system to adapt to the daily sports calendar.
5. **User Accounts** — Authentication via Clerk so users can save preferences, track their own picks, and access personalized dashboards.

## Tech Stack
- **Frontend**: Next.js (App Router) — course standard, great for SSR/ISR which helps with SEO and fast page loads for the pick board
- **Styling**: Tailwind CSS — utility-first, fast to iterate on, pairs well with component libraries like shadcn/ui for a polished data-heavy UI
- **Database**: Supabase (PostgreSQL) — stores odds snapshots, computed picks, game results, user data, and model configuration. Real-time subscriptions can power live pick updates without polling.
- **Auth**: Clerk — course standard, handles user accounts and session management
- **APIs**: 
  - The Odds API — primary data source for odds across 70+ sports and 40+ bookmakers, plus scores for outcome tracking
- **Model/Backend**: Python — runs the custom +EV model (devig calculations, book weighting, threshold filtering). Executes on a configurable schedule, reads config from Supabase, writes computed picks back to Supabase.
- **Deployment**: Vercel (Next.js frontend), Python model hosted as a scheduled job (options: Railway, Render, AWS Lambda, or a cron-based deployment)
- **MCP Servers**: 
  - Supabase MCP — for database schema management and queries during development
  - Playwright MCP — for testing the UI and potentially scraping supplementary data

## Stretch Goals
- **Push/SMS Alerts** — Notify users in real-time when high-value +EV opportunities appear (via web push notifications, email, or Twilio SMS)
- **Player Props Coverage** — Extend the model to analyze player prop markets (The Odds API supports props for NFL, NBA, MLB, NHL, and major soccer leagues)
- **Bet Tracker** — Let users log which picks they actually placed and track their personal P&L over time
- **Line Movement Visualization** — Show how odds have moved over time for a given event, helping users spot steam moves and CLV (closing line value)
- **Bankroll Management Tools** — Kelly criterion calculator, unit sizing recommendations based on edge and bankroll
- **Mobile-Optimized PWA** — Progressive web app for a native-like experience on phones, since most bettors are on mobile
- **Public Performance Dashboard** — A transparent, always-visible page showing the model's historical track record to build trust

## Biggest Risk
Two main risks:

1. **Data freshness vs. API budget** — The Odds API charges by credits (not requests), and the free tier is only 500 credits/month. For a tool that needs to poll frequently across multiple sports, this adds up fast. The challenge is designing a smart caching and polling strategy that keeps picks fresh enough to be actionable while staying within budget. Stale +EV picks are worse than no picks — if the odds have already moved by the time a user sees it, the edge is gone.

2. **Model accuracy and credibility** — If the custom model doesn't consistently identify truly +EV picks, the entire product loses its reason to exist. The outcome tracking feature is a double-edged sword: it proves the model works *or* it exposes that it doesn't. Getting the devig methods, book weighting, and threshold calibration right is the intellectual core of the project — and the hardest part to get right.

## Week 5 Goal
By the end of Week 5, demo a working end-to-end pipeline: the Python model pulls live odds from The Odds API, runs the custom +EV analysis (devig, book weighting, threshold filtering), writes picks to Supabase, and a basic but functional Next.js frontend displays those picks in a filterable table. The UI doesn't need to be polished — but it needs to show real, current +EV picks powered by real data. This proves the core value proposition: the model works, the pipeline works, and there's something real on screen.
