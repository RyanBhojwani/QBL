# Quant Bet Labs — How the Product Works (Human Perspective)

This document describes the product from the perspective of an expert user. It exists so that
when building UX improvements, we have an accurate mental model of the actual workflow — not
just what the code does, but how a real person uses this day to day.

**Update this document whenever something is wrong or incomplete.**

---

## Who is the user?

A Quant Bet Labs subscriber is a sports bettor who wants a mathematical edge. They are not
a casual bettor picking games based on gut feel. They understand (or are learning) concepts
like expected value, line shopping, and bankroll management. They have accounts at multiple
US sportsbooks and are comfortable placing bets quickly when a good line appears. They are
willing to treat betting like a long-term investment — accepting short-term losing streaks
in exchange for a positive expected outcome over hundreds of bets.

---

## The core daily workflow

### Morning / throughout the day
1. Open the dashboard (or get a Discord notification)
2. Check the Current Picks tab — this shows every live +EV opportunity the model has found
3. For each pick: note the book, the odds, and the bet size
4. Open that sportsbook app or website
5. Find the specific line (team, spread/total/moneyline, exact point value)
6. Confirm the odds match (or are better than) what the pick shows
7. Place the bet at the suggested unit size
8. Return to the dashboard — new picks may appear as lines move

### What "a pick" actually is
A single row in the picks table represents one specific bet opportunity:
- A specific team or side
- At a specific book (e.g. FanDuel)
- On a specific market (e.g. Spread -3.5, or Total Over 6.5, or Moneyline)
- At odds that the model has identified as better than fair value

The same game may appear as multiple rows — different books offering different prices,
or different markets (spread AND total) both being +EV at the same time.

### What to do when a pick disappears
Picks disappear when the line moves enough that the edge is gone. This is normal and
expected — it means the market is moving toward the model's fair value (which is CLV).
If a pick disappears before you bet it, do not chase it. Move on to the next opportunity.

---

## The star rating system

Stars (1–5) represent the model's confidence in the pick, specifically the CLV probability —
how likely this line is to close better than the current price.

- **1–2 stars**: Solid +EV edge. Consistent volume. The model finds a mathematical edge but
  the CLV signal is moderate. Good for building sample size.
- **3–4 stars**: Higher confidence plays. The model is more confident this line will close
  in your favor. Fewer but stronger signals.
- **5 stars**: Highest conviction plays. Rarest. The model's strongest signal on both EV
  and CLV probability.

**Tier access:**
- Basic ($25/mo): 1–2★ picks only
- Premium ($50/mo): 1–4★ picks
- VIP ($100/mo): all picks 1–5★

Higher tier does not mean the lower stars are bad — it means you get access to the
additional high-confidence layer on top.

---

## Bet sizing

The "Bet Size" column shows a suggested wager in **units**, using half-Kelly sizing capped at 3 units.

A **unit** is a percentage of your betting bankroll that you define yourself. Common convention:
1 unit = 1% of total bankroll. So if you have a $1,000 bankroll, 1 unit = $10.

Example: A pick showing "2.3u" means bet 2.3% of your bankroll (or $23 on a $1,000 bankroll).

The model caps bet size at 3 units to prevent overexposure on any single bet even when
Kelly suggests a larger size.

**Important:** You do not have to follow the exact unit size. It is a suggestion based on
the mathematical edge. Some users scale up or down based on their own bankroll rules.

---

## The books

The "Book" column shows which sportsbook has the best price on this pick. The user needs
to have an account at that book and available balance to place the bet.

Common books shown: FanDuel, DraftKings, BetMGM, Caesars, BetRivers, Fanatics, and others.

**Line shopping is part of the workflow.** The model finds the best price across all covered
books. If you don't have an account at the listed book, you may be able to find an acceptable
price at a different book — but the identified edge may be smaller or gone.

---

## Discord

Discord is the ONLY way to get real-time alerts for new picks. There is no push notification,
email alert, or in-app notification system. The workflow is:

1. User joins Discord and enables mobile notifications
2. When the model finds a new pick, it posts to the appropriate tier channel instantly
3. User gets a Discord ping on their phone
4. User opens the dashboard (or reads the pick directly in Discord) and places the bet

Without Discord, a user would have to manually refresh the dashboard every 15 minutes to
catch new picks. Discord is therefore not optional — it is the primary delivery mechanism
for the service. Joining Discord should be treated as a required setup step for new subscribers,
not a nice-to-have.

Tier-specific channels:
- #basic: 1–2★ picks
- #premium: 1–4★ picks
- #vip: all picks 1–5★

---

## Settlement and results

Every day at 4:00 AM ET, the system automatically:
1. Fetches final scores from The Odds API
2. Grades every tracked pick as Win, Loss, or Push
3. Moves graded picks from "active" to "settled"

Results appear in the Settled Picks tab after 4 AM. Performance metrics (ROI, win rate, etc.)
are recalculated at 4:30 AM and reflected in the Performance tab.

**Push:** When a spread or total lands exactly on the line (e.g., spread is -3 and game
lands exactly 3 points apart), the bet is a push — the wager is returned, no win or loss.

---

## Performance metrics — what they mean

- **ROI (Real)**: Actual return on investment across all settled picks. Dollars won divided
  by dollars wagered.
- **Expected ROI (CLV)**: What the ROI should be based on closing line value — how the lines
  moved after the model found them. A proxy for long-term edge independent of short-term variance.
- **Win Rate**: Percentage of bets graded as wins (not counting pushes).
- **CLV Win Rate**: Percentage of picks where the line moved in the predicted direction
  (closed better than the model's pick price). A high CLV win rate means the model is
  consistently finding real edges, even if short-term results are mixed.
- **Kelly / Bet Size**: Already covered above.
- **Sharpe Ratio**: Risk-adjusted return. Borrowed from finance — measures return per unit
  of volatility. Higher is better.
- **Max Drawdown**: Largest peak-to-trough decline in the bankroll curve. Tells you the worst
  losing streak the model has experienced.

---

## What the model is NOT

- It is not a guarantee. Every bet has variance. Even +EV bets lose.
- It is not a hot-take service. It does not pick based on injuries, weather, matchups, or
  "feels." It picks based purely on math.
- It is not a parlay builder. The picks are individual bets, each with its own independent edge.
  Parlaying +EV picks destroys the edge because the books set parlay payouts below fair value.
- It is not for everyone. Users who need to win every week, or who bet money they cannot
  afford to lose, will have a bad experience regardless of the model's edge.

---

## Open questions / things to verify with the user

- [ ] Is the unit sizing convention (1u = 1% bankroll) explicitly communicated anywhere,
      or is it assumed knowledge?
- [ ] Do users typically have accounts at all covered books, or do they line-shop manually
      across 2–3 books?
- [ ] Is there a recommended minimum bankroll to use the service effectively?
- [ ] Do VIP users get any additional features beyond pick access (e.g., direct support,
      early access)?
- [ ] How are pushes currently displayed in the Settled Picks tab?
- [ ] Does the Discord bot post picks in real-time as they are found, or in batches?
