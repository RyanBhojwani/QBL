# Quant Bet Labs — Legal Audit & Risk Assessment

**Prepared as:** Pre-launch legal review, sports betting & consumer protection lens  
**Date:** 2026-06-10  
**Scope:** All public-facing content, subscription terms, disclaimers, performance claims, and structural legal gaps

---

## Executive Summary

Quant Bet Labs operates as a **sports betting information service** — not a sportsbook, not a financial adviser. This distinction is your entire legal foundation. Everything you publish must reinforce it consistently and never blur it.

The current site has a reasonable disclaimer page and reasonable FAQ language, but it has four structural gaps that need to be resolved before you take real money from real users:

1. **No Terms of Service** — you have no limitation of liability, no arbitration clause, no governing law, no class action waiver. One unhappy subscriber who loses money could file suit and you have nothing protecting you.
2. **No Privacy Policy** — legally required under California law (CCPA), applicable to any subscriber in the EU (GDPR), and now required under a growing number of US state privacy laws.
3. **Performance claims without methodology** — the ">100% Annual ROI" claim on the landing page is an FTC liability as written.
4. **No responsible gambling resources** — multiple states require gambling-adjacent services to post the NCPG hotline. Even where not legally required, omitting it is a reputational and liability risk.

The remaining issues below are real but smaller — language fixes rather than structural gaps.

---

## Issue 1 — No Terms of Service (Critical)

**Risk level: High**

You are charging $25–$100/month and have no Terms of Service. This means:
- No limitation of your liability if a user loses money following picks
- No arbitration clause — you're fully exposed to class action lawsuits
- No governing law — a plaintiff could sue you under whatever state law is most favorable to them
- No warranty disclaimer — you have not legally disclaimed any implied warranties
- No description of what the subscription entitles users to (and what it doesn't)
- No dispute resolution process
- No termination rights (your right to terminate abusive accounts)

**What to create:** A `/terms` page with the following sections:

**1. Nature of Service**  
State clearly and prominently: Quant Bet Labs is a sports betting *information* service. We provide statistical analysis of publicly available odds data. We do not place bets, accept wagers, operate as a sportsbook, or act as a financial or investment adviser. Nothing on this platform constitutes gambling advice, financial advice, investment advice, or legal advice.

**2. Eligibility**  
Users must be 18 years of age or older (or the minimum legal age in their jurisdiction, whichever is higher). Users must be located in a jurisdiction where accessing sports betting information is legal. By subscribing, users represent that they meet these requirements.

**3. Subscription Terms**  
- Billing is monthly, charged on the same day each month
- Cancellation can be done at any time through the Account page
- Upon cancellation, access continues until the end of the current billing period; no partial refunds are issued for unused days
- Refunds are not issued for subscription fees already charged, except where required by applicable law
- We reserve the right to change pricing with 30 days written notice

**4. Limitation of Liability** *(most important section)*  
To the maximum extent permitted by applicable law, Quant Bet Labs, its owners, officers, employees, and affiliates shall not be liable for:
- Any betting losses incurred by users who act on picks or information from this service
- Any indirect, consequential, incidental, special, or punitive damages
- Any loss of profits, revenue, data, or business opportunity

In no event shall our total liability to any user exceed the amount paid by that user in the twelve (12) months preceding the claim.

**5. Disclaimer of Warranties**  
The service is provided "as is" and "as available" without warranties of any kind, express or implied. We do not warrant that picks will be profitable, that the model will continue to perform at historical levels, or that the service will be error-free.

**6. Governing Law & Dispute Resolution**  
This Agreement is governed by the laws of [your state — Delaware is preferable as a formation state]. Any disputes must be resolved through binding individual arbitration under AAA Commercial Rules. Users waive the right to participate in class action lawsuits.

**7. Termination**  
We reserve the right to terminate or suspend accounts for violations of these terms, abuse of the service, or at our sole discretion with reasonable notice.

---

## Issue 2 — No Privacy Policy (Critical)

**Risk level: High**

California's CCPA applies to any business with California users. GDPR applies to any EU user. Virginia, Colorado, Texas, and a dozen other states now have similar laws. A privacy policy is not optional.

**What to create:** A `/privacy` page covering:

- **Data collected:** Email address and name (via Clerk), payment information (processed by Stripe — not stored by QBL), filter preferences (stored in Supabase), usage data (if analytics are added)
- **Third-party processors:** Clerk (auth), Stripe (payments), Supabase (database), Vercel (hosting). Include links to each processor's privacy policy.
- **Data use:** To provide the service, process payments, send transactional communications
- **Data sale:** We do not sell personal data to third parties
- **Retention:** Account data retained until account deletion; payment records retained as required by law
- **User rights:** Right to access, correct, delete, and export their data. Contact email for requests.
- **Contact:** privacy@quantbetlabs.com (or support@)

---

## Issue 3 — Performance Claims (FTC Liability)

**Risk level: High**

The landing page displays `>100%` or a real units figure as "Annual ROI" or "Units Profit (All-Time)" in a large hero display with no context. The FTC Act Section 5 prohibits deceptive advertising. A performance claim without:
- The time period it covers
- The starting bankroll assumption
- The bet sizing methodology
- A typical results disclosure

...is a deceptive claim under FTC guidelines, regardless of whether the number is real.

This is not theoretical. The FTC has taken action against sports pick services and financial information services for unsubstantiated performance claims.

**What to fix:**

The hero stat needs a footnote, inline or immediately beneath. It does not need to be lengthy:

> *"Based on all picks since [launch date], using half-Kelly bet sizing on a $1,000 starting bankroll. [X] total picks settled. Past performance does not guarantee future results."*

Additionally, the landing page copy currently includes:

> *"Every minute you're not in, you're leaving money on the table."*

This implies a near-certain financial loss from non-subscription. It should be softened to avoid false urgency claims:

> *"Every minute counts when lines are moving."*

---

## Issue 4 — Responsible Gambling Resources Missing (Moderate–High)

**Risk level: Moderate–High**

Several states (New Jersey, Michigan, Pennsylvania, Colorado, among others) require operators in the gambling ecosystem to include responsible gambling messaging and the NCPG crisis line. QBL is not a licensed sportsbook, so direct regulatory requirements may not apply to you — but:

1. The absence of any responsible gambling resource is a reputational liability
2. If a user with a gambling problem suffers harm and sues, the absence of any responsible gambling messaging strengthens their negligence claim
3. App stores and payment processors (Stripe) increasingly require this for gambling-adjacent products

**What to add:**

On the Rules & Disclaimer page, add a section:

> **Responsible Gambling**  
> Sports betting carries real financial risk. If you or someone you know may have a gambling problem, free and confidential help is available 24/7. Call or text **1-800-GAMBLER** (1-800-426-2537), or visit **ncpgambling.org**.

Also add this to the **footer sitewide** — a single line is sufficient:

> Gambling problem? Call 1-800-GAMBLER

---

## Issue 5 — Age Requirement Stated Incorrectly

**Risk level: Moderate**

The Rules page states:
> *"Sports betting is only legal in certain jurisdictions and for individuals who meet the minimum legal age requirement (typically 21+ in the United States)."*

This is factually wrong and creates a false impression. The minimum age for sports betting in most US states is **18**, not 21. States requiring 21+ are a minority (Connecticut, New Jersey, Washington DC, West Virginia, Montana, Wyoming — rules vary). Stating "typically 21+" either (a) discourages legal-age users or (b) misleads 18–20 year olds into thinking they're covered when they may not be in their state.

**Fix:**
> *"Sports betting is only legal in certain jurisdictions and for individuals who meet the minimum legal age in their state (18 or 21 depending on jurisdiction). Always confirm the minimum age requirement in your specific location before using this service."*

---

## Issue 6 — "You Will Profit" Language in FAQ (Moderate)

**Risk level: Moderate**

The public FAQ states:
> *"Over a large sample of +EV bets, you will profit — regardless of individual outcomes."*

"**You will profit**" stated as fact is a guarantee. Guarantees in pick services are a well-documented FTC red flag and a common basis for fraud claims when users lose money.

**Fix:**
> *"Over a large sample of +EV bets, the math works in your favor — though individual results vary and no outcome is guaranteed. Variance is real, and even a statistically positive strategy can experience extended losing streaks."*

---

## Issue 7 — Education Page "Card Counting" Analogy (Low–Moderate)

**Risk level: Low–Moderate**

The Education page states:
> *"It's the same math as poker or blackjack card counting."*

Card counting is legal but is widely associated with being banned from casinos and is a charged term. More importantly, this analogy draws a direct line between your service and beating the house by stealth — which is exactly the framing that makes sportsbooks limit accounts. Stating it openly on your platform creates a record that you are knowingly helping users circumvent sportsbook security.

**Fix:** Drop the card counting reference. The poker analogy alone is fine and less charged:
> *"It's the same principle as profitable poker — making decisions with a mathematical edge over time."*

---

## Issue 8 — "Account Longevity" Advice (Low–Moderate)

**Risk level: Low–Moderate**

The Education page advises:
> *"To extend account life: bet round numbers, vary your timing, use multiple books, and don't hammer one book."*

This is explicit advice on how to evade sportsbook risk management systems. Sportsbook terms of service prohibit using software or systems to gain an unfair advantage, and some sportsbooks argue that detection-evasion tactics violate their terms. While this advice is widely circulated in the +EV community, publishing it on your platform as a tutorial creates a record that your service knowingly facilitates TOS circumvention at retail sportsbooks. This could expose you to a tortious interference claim from a sportsbook, or be used against you in a user lawsuit arguing you enabled deceptive conduct.

**Fix:** Reframe as general best practice rather than evasion tactics:
> *"Diversifying across multiple sportsbooks is standard practice for any serious bettor — it gives you access to the best line on each game and reduces dependence on any single book's pricing."*

Remove the specific "bet round numbers, vary your timing" framing — these are evasion tactics.

---

## Issue 9 — Subscription Terms Disclosure Too Thin on Pricing Page (Moderate)

**Risk level: Moderate**

The pricing page shows the price and "Cancel anytime." but does not disclose:
- When the first charge occurs
- What happens to access when you cancel
- That there are no partial refunds
- Whether there is a free trial

California's Automatic Renewal Law (Business & Professions Code § 17600) requires that auto-renewing subscription terms be disclosed "clearly and conspicuously" before purchase, in visual proximity to the purchase button. Several other states have similar laws.

**Fix:** Add beneath the pricing cards:

> *Billed monthly. Charged immediately upon signup. Cancel anytime — access continues until the end of your current billing period. No partial refunds. No free trial. By subscribing you agree to our [Terms of Service] and [Privacy Policy].*

---

## Issue 10 — Footer Has No Legal Links (Moderate)

**Risk level: Moderate**

The footer currently has no links to Terms of Service, Privacy Policy, or the disclaimer. This is:
- A legal requirement in many jurisdictions
- Required by Stripe's terms for subscription merchants
- Required to give users constructive notice of your terms (necessary for the arbitration clause in ToS to be enforceable)

**Fix:** Add to the footer on every page:
- Terms of Service → `/terms`
- Privacy Policy → `/privacy`
- Rules & Disclaimer → `/rules`
- 18+ | Gambling problem? 1-800-GAMBLER

---

## Issue 11 — Refund Policy is Undefined (Low–Moderate)

**Risk level: Low–Moderate**

The Rules page states:
> *"Refunds are evaluated on a case-by-case basis."*

This is legally ambiguous. "Case-by-case" means nothing enforceable. In a chargeback dispute with Stripe, a vague refund policy is interpreted against the merchant. Several states (including California) give consumers the right to cancel and receive a refund within a specific window regardless of your stated policy.

**Fix in ToS:** State a clear policy:
> *"All subscription fees are non-refundable except where required by applicable law. If you believe you were charged in error, contact support@quantbetlabs.com within 7 days of the charge."*

---

## Issue 12 — No Representation About Geo-Restrictions (Low)

**Risk level: Low**

The site is accessible globally but sports betting information services can face regulatory scrutiny in certain jurisdictions (UK, Australia, some EU countries) where pick services may be regulated differently. The current disclaimer places all responsibility on the user but doesn't explicitly limit service availability.

**Fix in ToS eligibility section:**
> *"This service is intended for users in the United States and other jurisdictions where accessing sports betting information is lawful. We make no representation that the service is appropriate or available for use in locations where it would be unlawful."*

---

## Priority Order for Implementation

| Priority | Issue | Action Required |
|----------|-------|----------------|
| 1 | No Terms of Service | Create `/terms` page |
| 2 | No Privacy Policy | Create `/privacy` page |
| 3 | Performance claim without methodology | Add footnote to hero stat on landing page |
| 4 | No responsible gambling resources | Add to Rules page + footer |
| 5 | Subscription terms not disclosed pre-purchase | Add disclosure beneath pricing cards |
| 6 | Footer has no legal links | Add ToS, Privacy, Rules, 1-800-GAMBLER to footer |
| 7 | "You will profit" language in FAQ | Soften to "may" / "the math works in your favor" |
| 8 | Age requirement stated as "typically 21+" | Fix to "18 or 21 depending on jurisdiction" |
| 9 | Card counting analogy in Education | Replace with poker analogy |
| 10 | Account longevity evasion advice | Reframe as book diversification |
| 11 | Undefined refund policy | Define clearly in ToS |
| 12 | No geo-restriction representation | Add to ToS eligibility section |

---

## What QBL Is Not Doing Wrong

For context — these are common concerns in this space that **do not apply** to QBL:

- **Wire Act**: Doesn't apply — QBL doesn't transmit bets or wagers across state lines
- **UIGEA**: Doesn't apply — QBL doesn't process gambling transactions
- **Investment adviser registration**: Doesn't apply — sports betting is not a "security" under federal law
- **Sports bribery laws**: Doesn't apply — QBL analyzes publicly available market data, not inside information
- **Tout service registration**: Most states don't require registration for information services of this type; the few that have attempted regulation have faced preemption challenges

The core business model — sell access to statistical analysis of publicly available odds data — is legally sound. The risk is in how it's presented, not what it does.

---

*This document is an internal legal risk assessment, not a substitute for licensed legal counsel. Before launch, have a licensed attorney in your state review the Terms of Service and Privacy Policy drafts.*
