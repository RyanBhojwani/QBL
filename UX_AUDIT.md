# Quant Bet Labs — UX/UI Audit

**Prepared by:** UX Review  
**Date:** 2026-06-10  
**Scope:** Full product audit — public site, dashboard, and conversion funnel  

---

## Executive Summary

Quant Bet Labs has a solid technical foundation and a coherent design system. The dark theme, cyan accent, and data-dense layout are appropriate for the target audience — analytically-minded sports bettors who are comfortable with financial terminology. However, the product currently reads more like a working prototype than a finished SaaS. The gaps are not design flaws; they are missing layers: orientation, trust, and confidence. Fix those and the product is ready to charge real money.

**The three biggest opportunities in priority order:**

1. **New subscribers have no idea what to do first.** There is no onboarding.
2. **The picks table has zero in-context help.** Columns like CLV, Kelly, and EV are undefined. Users who don't already know these terms will be confused from their first session.
3. **The public site undersells the product.** The performance page is mostly locked, the landing page stats are hardcoded placeholders, and the pricing page doesn't clearly explain what each tier gets you in concrete terms.

Everything below is actionable and scoped — no redesigns, no new pages required unless noted.

---

## Section 1 — New User Onboarding

### 1.1 The problem: zero orientation after signup

A user pays $25–$100/month, completes Stripe checkout, lands on `/dashboard/picks?success=1`, sees the SuccessBanner for 5 seconds, dismisses it, and is immediately staring at a raw data table. There is no explanation of what they're looking at, what order to do things in, or what success looks like. This is the highest-churn moment in any SaaS product.

**Fix:** Add a dismissible first-session modal that fires once — triggered by a `first_visit` flag stored in localStorage after the `?success=1` param is consumed. Keep it to 3 slides maximum:

- **Slide 1:** "Here's what you're looking at" — label the picks table columns with a visual callout. Stars = confidence. Book = where to bet. Odds = what you're getting. Bet Size = suggested unit size.
- **Slide 2:** "How to place a bet" — check pick → open sportsbook → find the line → bet the suggested size. One sentence each.
- **Slide 3:** "Set up Discord" — fastest alerts come through Discord. Link directly to the Discord invite. One button: "Join Discord."

This modal should take under 60 seconds to click through. Do not auto-advance. Let users move at their own pace.

### 1.2 The SuccessBanner is doing too much work

The current banner tries to orient the user, confirm the tier, explain Discord, and link to the How To Use guide — all in one small dismissible bar. Users dismiss banners before reading them.

**Fix:** The banner should only confirm the purchase: "You're subscribed — VIP access is active." Nothing else. The onboarding modal (above) handles orientation. Remove the Discord CTA and How To Use link from the banner.

### 1.3 Default filter state is wrong for new users

On first visit, filters are blank (or loaded from preferences that don't exist yet). A new Basic subscriber sees a table that potentially shows 0 picks if their preferences are misconfigured, which reads like the product is broken.

**Fix:** On first session (no stored preferences), default to: all sports, all books, stars = 1 to tier-max (e.g., 1–2 for Basic). Never show 0 picks to a brand new user unless there are genuinely 0 picks in the system.

---

## Section 2 — Picks Table (Core Feature)

### 2.1 Column headers are undefined

The seven columns — Stars, Team, Market, Book, Odds, Bet Size, Game Time — include at least three that will confuse non-expert users: Stars (what is a 5-star pick?), Bet Size (units? what is a unit?), and Market (what does "Spread +5.5" mean vs "Total 6.0"?). There is no inline explanation anywhere on the page.

**Fix:** Add a small `ⓘ` icon next to each column header that triggers a tooltip on hover (or tap on mobile). One sentence each:

| Column | Tooltip text |
|--------|--------------|
| Stars | Model confidence rating (1–5). Higher = stronger CLV signal. Your tier determines the maximum star level you can see. |
| Market | Bet type: Moneyline (who wins), Spread (margin of victory), Total (combined score over/under). |
| Book | Which sportsbook has the best price. Open your account there and find this line before placing. |
| Odds | American odds at this book. Positive = underdog, negative = favorite. |
| Bet Size | Suggested wager in units using half-Kelly sizing, capped at 3 units. Size your unit based on your bankroll (e.g., 1u = 1% of bankroll). |
| EV | Expected value — the mathematical edge on this bet as a percentage of your wager. |
| CLV | Closing Line Value probability — likelihood this line moves in your favor before game time. |

### 2.2 No context for the live indicator

The pulsing "Live" dot in the top right of the filter bar is the only signal that the data is real-time. But users don't know what "Live" means here — are these live game odds? Is the model running live?

**Fix:** Change the label from "Live" to "Auto-refreshing" and add a subtle subtitle beneath the filter bar: "Model runs every 15 minutes. Table updates automatically." This sets correct expectations and reduces "why did the table just change?" confusion.

### 2.3 The empty state for filtered results needs a nudge

When filters return 0 picks, the current message is "No picks match your filters" with a suggestion to adjust. This is fine but passive.

**Fix:** Add a single "Reset Filters" button inline in the empty state — not just the small text link at the top of the filter bar which users may not see. Make the recovery action obvious.

### 2.4 No indication of when the model last ran

Users don't know if the picks are 2 minutes old or 14 minutes old. This creates anxiety — "is this stale?"

**Fix:** Add a "Last updated X minutes ago" timestamp below the filter bar, next to the Live indicator. Update it client-side using the `updated_at` column from Supabase or a client-side timer. This is one line of code and significantly improves perceived reliability.

### 2.5 Mobile layout is too dense

On mobile the 7-column table collapses to 2 columns, which is good, but the stacked card format loses the book and bet size which are the two most actionable columns. A user on mobile opening the app to actually place a bet needs book and bet size immediately.

**Fix:** On mobile, show: Stars, Team/Market, Book, Odds, Bet Size. Drop Game Time to a secondary row within the card. The game time is low-priority information at bet placement time.

---

## Section 3 — Public Site & Conversion Funnel

### 3.1 Landing page stats are placeholders

"500+ Alerts Sent" and "16 Leagues Covered" are hardcoded. If real numbers are higher (and after months of operation they likely are), this actively undersells the product. If they're lower, it's misleading.

**Fix:** Pull alerts sent from `COUNT(*)` on `settled_picks` + `current_picks`, compute leagues from `DISTINCT sport` in `settled_picks`, and display real numbers. If the numbers are good, let them speak. If they're not impressive yet, replace these stats with something that is — e.g., average EV per pick, win rate, total units profit.

### 3.2 ">100% Annual ROI" needs a footnote

This is the most prominent claim on the site. Without a methodology note it reads like a marketing fabrication. This is also a potential FTC/legal issue (addressed separately in Phase 12.7).

**Fix:** Add a superscript `¹` after the claim with a footnote at the bottom of the section: *"Based on $1,000 starting bankroll, half-Kelly sizing, picks since [launch date]. Past performance does not guarantee future results."* This makes the claim credible rather than suspicious.

### 3.3 The pricing page doesn't answer the key question

The pricing page shows what each tier costs and lists feature checkmarks, but doesn't answer the question every prospective subscriber actually has: **"What does a 4-star pick look like vs a 2-star pick?"**

**Fix:** Add a row to the pricing comparison showing example pick quality or a one-line description of the signal strength difference. Example: "Basic (1–2★): Solid +EV edge, consistent volume" vs "Premium (1–4★): Higher confidence plays, fewer but stronger signals" vs "VIP (1–5★): All picks including highest-conviction plays."

Also add the subscription billing terms inline on the pricing page — "Billed monthly. Cancel anytime. Access continues until end of billing period." This removes friction for users who are on the fence about commitment.

### 3.4 The public performance page locks too much

The public `/performance` page shows summary stats but immediately locks the breakdown tables behind a subscribe overlay. For a product selling on data and transparency, locking all the detail upfront creates distrust rather than urgency.

**Fix:** Show the By Star Rating table publicly (read-only, no modal drill-down). This is the single most convincing table for a prospective subscriber — it shows that higher star picks outperform lower star picks, which validates the tier pricing model. Lock the modal detail behind a subscribe CTA. This turns a "trust me" into a "here's proof."

### 3.5 How It Works and How To Use are not linked well enough

The site has excellent educational content — the How It Works methodology page and the How To Use guide are both thorough. But the conversion funnel doesn't route users through them. A confused visitor lands on the homepage, sees jargon, and leaves.

**Fix:** On the landing page hero section, add a secondary text link below the two CTA buttons: "Not sure if this is for you? See how the model works →" linking to `/how-it-works`. This intercepts skeptical visitors before they bounce.

---

## Section 4 — Dashboard Navigation & Information Architecture

### 4.1 "Results" and "Performance" are confusing as separate items

From a user's mental model, "Results" (settled bets) and "Performance" (ROI metrics) are the same thing — "how did my picks do?" The current separation requires users to understand the difference between raw settlement data and computed analytics, which is an internal distinction, not a user one.

**Fix (short term):** Rename "Results" to "Settled Picks" in the nav so the distinction is immediately clear — one is the pick-by-pick record, one is the aggregate analytics. Long term, consider merging them into a single "Track Record" page with tabs.

### 4.2 Education is buried and undersold

The Education section is Premium/VIP-only content and a meaningful part of the value proposition at those tiers. But it's just another nav item — nothing on the picks page, the pricing page, or the onboarding flow draws attention to it.

**Fix:** On the pricing page, add "Educational content" to the Premium and VIP feature lists with a brief description: "Core concepts, glossary, and strategy guides for serious bettors." This makes the tier upgrade more concrete.

### 4.3 Account page is missing subscription details

The Account page shows "VIP — Active" and a "Manage Subscription" button, but no renewal date, no next billing amount, and no description of what happens at cancellation. Users cancel because they're uncertain — "when does my access end? will I be charged again?"

**Fix:** Display renewal date (available from Stripe via the webhook events already being processed), price, and a one-line cancellation note: "If you cancel, access continues until [date]. You will not be charged again."

### 4.4 The nav is visually identical in authenticated vs unauthenticated state

The same PublicNav renders for both states, which is good for consistency, but the "Home" link in the authenticated nav goes to `/` (the public landing page) rather than the dashboard. This is subtly wrong — a logged-in user who clicks "Home" expects to go to their picks, not the marketing site.

**Fix:** Change the "Home" link in the authenticated nav to point to `/dashboard/picks`. The public landing page is not the "home" for a paying subscriber.

---

## Section 5 — Visual Design & Polish

### 5.1 No loading skeleton on the picks table

The picks table shows a spinner while loading. On a fast connection this is fine; on a slow connection or during Supabase cold start, users stare at a spinner with no idea how long to wait or whether anything is coming.

**Fix:** Replace the spinner with 5–8 skeleton rows — gray placeholder blocks in the shape of table cells. This signals "data is loading" much more clearly than a spinner and reduces perceived wait time.

### 5.2 The performance modal is information overload

The modal packs 6 summary cards, a bankroll chart, 3 stat sections (Win/Loss Record, Returns and Profit, Financial Statistics), and 14+ individual data points into a single scrollable overlay. Most users will see the first two cards, glance at the chart, and close. The financial statistics (Sharpe, Sortino, CAGR, Max Drawdown, Volatility) are investment-grade metrics that mean nothing to the average sports bettor.

**Fix (option A):** Collapse the Financial Statistics section behind a "For advanced users" toggle — expanded by default for returning users, collapsed for first-time viewers.

**Fix (option B):** Move the financial stats to the Education page as a "reading your performance" guide. The modal becomes leaner and faster to parse.

Either way, add a one-sentence tooltip to each financial metric: Sharpe, Sortino, Max Drawdown, and CAGR are all undefined inline and will confuse users without finance backgrounds.

### 5.3 Positive/negative coloring is inconsistent

On the performance stats cards, Real ROI is cyan when positive and red when negative. Win Rate is always black regardless of value. This inconsistency makes it harder to scan the cards quickly.

**Fix:** Apply the same color logic to all numeric metrics: cyan/green when above a "good" threshold, red when below, neutral (white) when flat or near zero. Win rate: green above ~52% (rough break-even for average odds), red below.

### 5.4 The upgrade wall doesn't tell users what they'd see

When a Basic subscriber hits the upgrade wall on the Education or How To Use pages, they see "This is a Premium feature. Upgrade to access." There's no preview of what's behind the wall.

**Fix:** Show the section headers (blurred or grayed out) behind the upgrade overlay, the same way the public performance page shows blurred breakdown table rows. Users upgrade when they can see what they're missing, not when they're told it exists.

### 5.5 Footer is missing legal links

The footer has logo, nav links, and copyright. It does not have Terms of Service or Privacy Policy links. These are legally required for any subscription product collecting payments. This is a Phase 12.7 item but worth noting here since it's also a trust signal — users look for ToS/Privacy links before entering payment info.

---

## Section 6 — Mobile-Specific Issues

### 6.1 Filter dropdowns on mobile are full-width but not full-height

On small screens the Sport and Book filter dropdowns render as full-width panels. With 10 sports and 11 sportsbooks listed with checkboxes, these panels are tall and require significant scrolling inside a scrollable page. This creates a scroll-within-scroll problem.

**Fix:** On mobile, render the filter dropdowns as bottom sheets (slide up from the bottom of the viewport) rather than dropdown panels. Bottom sheets are the native mobile pattern for multi-select filter UIs.

### 6.2 The star range slider is unusable on mobile

Dual-handle range sliders have notoriously bad touch targets on mobile. The handles are small and close together for 1–5 star range, making accurate selection difficult.

**Fix:** On mobile (screen width < 640px), replace the range slider with two simple +/– step controls: "Min Stars: [1] [+] [–]" and "Max Stars: [5] [+] [–]". These are easy to tap and match the user's mental model.

### 6.3 The performance modal is difficult to navigate on mobile

A scrollable modal inside a scrollable page creates the same double-scroll problem as the filters. On mobile, the modal with its chart and three stat sections is nearly impossible to read comfortably.

**Fix:** On mobile, instead of a centered overlay modal, use a full-screen slide-in panel that replaces the current view. This is the standard native mobile pattern for detail views and eliminates the scroll conflict entirely.

---

## Section 7 — Error & Edge Case Handling

### 7.1 Supabase fetch failure is silent

If the Supabase fetch on the picks page fails (network error, timeout, Supabase outage), the error state shows a red border and a "Retry" button. This is correct. However there is no indication of whether the issue is on the user's end or the system's end.

**Fix:** On fetch failure, add: "This may be a temporary issue — try again in a moment. If the problem persists, check our [Discord] for status updates." This prevents users from assuming the product is broken and gives them a recovery path.

### 7.2 The results/settled picks page is a visible placeholder

`/dashboard/results` currently shows a table header, disabled filter buttons, and an empty state icon. A paying subscriber who finds this page will think either the product is broken or their bets aren't being tracked. There is no explanation that this page is intentionally pending.

**Fix:** Until the results page is populated, either (a) hide it from the nav entirely, or (b) replace the empty state with: "Settlement runs daily at 4 AM ET. Your first settled picks will appear here after tomorrow morning. View your current open picks →" This turns a confusing blank page into a reassuring status update.

### 7.3 No feedback when picks update in real-time

When Supabase Realtime fires and the picks table refreshes, the table just silently changes. If picks disappear (line moved, no longer +EV) the user has no idea what happened.

**Fix:** Add a brief non-intrusive toast notification at the bottom of the screen: "Picks updated" with a timestamp. Disappears after 3 seconds. This closes the loop on the "why did my table change?" question without interrupting the user.

---

## Priority Summary

| Priority | Issue | Effort | Impact |
|----------|-------|--------|--------|
| 1 | First-session onboarding modal | Medium | Very High |
| 2 | Column header tooltips on picks table | Low | High |
| 3 | "Last updated X minutes ago" timestamp | Low | High |
| 4 | Default filter state for new users | Low | High |
| 5 | Show star rating breakdown table publicly | Low | High |
| 6 | Landing page stats pulled from real data | Medium | High |
| 7 | Rename "Results" → "Settled Picks" in nav | Low | Medium |
| 8 | Account page renewal date + cancellation note | Medium | Medium |
| 9 | Picks table skeleton loading state | Low | Medium |
| 10 | Authenticated "Home" nav → `/dashboard/picks` | Low | Medium |
| 11 | SuccessBanner simplified to confirmation only | Low | Medium |
| 12 | Upgrade wall shows blurred preview content | Medium | Medium |
| 13 | Financial metric tooltips in performance modal | Low | Medium |
| 14 | Settled picks page — hide or explain | Low | Medium |
| 15 | Real-time update toast notification | Low | Low |
| 16 | Performance modal collapse financial stats | Medium | Low |
| 17 | Mobile: replace star slider with step controls | Medium | Low |
| 18 | Mobile: filter dropdowns as bottom sheets | High | Low |
| 19 | ">100% ROI" footnote | Low | Medium (legal) |
| 20 | Footer legal links (ToS, Privacy) | Low | High (legal) |
