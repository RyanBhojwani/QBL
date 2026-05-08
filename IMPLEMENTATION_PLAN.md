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

## Remaining Work Beyond Phase 7

| Task | Notes |
|------|-------|
| Content/copy pass | All public pages have placeholder text — needs real marketing copy |
| Discord invite links | All `href="#"` Discord CTAs need real server invite URLs |
| Stripe live mode switch | See pre-launch requirement above |
| Email notifications | Stripe handles receipts automatically; daily summary is future work |
| Mobile QA pass | Test all pages on iOS/Android before wide launch |

---

## Dependency Graph (updated)

```
Phase 1 (Schema) ✅
    └─► Phase 2 (Python Writes) ✅
            └─► Phase 3 (Railway) ✅
                    └─► Phase 7 (Results) ← NEXT

Phase 1 (Schema) ✅
    └─► Phase 4 (Next.js Scaffold) ✅
            └─► Phase 5 (Auth) ✅
                    └─► Phase 6 (Billing) ✅
```
