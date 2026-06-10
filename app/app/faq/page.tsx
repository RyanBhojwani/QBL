import PublicLayout from "@/components/PublicLayout";
import { DISCORD_INVITE_URL } from "@/lib/constants";
import FaqAccordion from "@/components/FaqAccordion";
import DiscordCTA from "@/components/DiscordCTA";

const faqs = [
  {
    q: "What is expected value (EV) betting?",
    a: "EV betting means placing bets where the probability of winning is higher than what the sportsbook's odds imply. If our model estimates the true probability of an outcome at 60% but the book is offering odds that imply only 52%, you have a +EV edge. Over a large sample of +EV bets, the math works in your favor — though individual outcomes will vary and no result is guaranteed.",
  },
  {
    q: "How does the model find edge?",
    a: "We use sharp sportsbook prices (from highly efficient market makers) to derive the true probability of each outcome via a multiplicative devig process. We then compare that true probability against prices at retail sportsbooks. When a retail book offers better-than-true odds, we have positive expected value.",
  },
  {
    q: "What does the star rating (1–5★) mean?",
    a: "Stars reflect the model's confidence based on CLV (Closing Line Value) probability — the likelihood the pick's odds will be better than the final pre-game price. This is estimated by a bagged logistic regression model trained on historical line movement. 5★ picks are the highest confidence. Basic tier sees 1–2★ picks. Premium sees 1–4★. VIP sees all picks including every 5★ play.",
  },
  {
    q: "What is CLV and why does it matter?",
    a: "CLV measures how much your odds beat the closing line — the final price the market settles at before a game starts. The closing line is the most efficient estimate of true probability. Consistently beating it confirms your selection process has real edge, not just short-term variance.",
  },
  {
    q: "Are these guaranteed to win?",
    a: "No. +EV betting is a long-term strategy. Individual picks will lose. Variance is real — even a 65% true-probability bet loses 35% of the time. The math works in your favor over a large sample, but no outcome is guaranteed. You need proper bankroll management (we recommend half-Kelly sizing) and patience to play long-term. See our Rules & Disclaimer page for more.",
  },
  {
    q: "How often does the model run?",
    a: "Our Python worker runs every 15 minutes during peak hours and every 2 hours overnight. Picks update in real time on the dashboard via Supabase Realtime. Discord alerts fire the moment new picks are found.",
  },
  {
    q: "What sports and leagues are covered?",
    a: "Currently: MLB, NHL, NBA, EPL (English Premier League soccer), MMA/UFC, and Boxing. We add leagues seasonally — NFL coverage is added in September each year.",
  },
  {
    q: "What sportsbooks do you cover?",
    a: "We pull prices from all major US retail sportsbooks: FanDuel, DraftKings, BetMGM, Caesars, BetRivers, Hard Rock Bet, Fanatics, Bally Bet, theScore Bet, and more. The book with the best price for each pick is shown on the dashboard.",
  },
  {
    q: "How is this different from touts and tip services?",
    a: "We don't pick winners based on gut feelings, trends, or team analysis. Every pick comes from a mathematical edge vs. the true market price. We track everything and publish our full record. No cherry-picking, no \"units\" games, no fake screenshots.",
  },
  {
    q: "Can I cancel anytime?",
    a: "Yes. All plans are month-to-month. You can cancel at any time from the Account page. Billing is managed via Stripe — no commitments, no hassle.",
  },
];

export default function FaqPage() {
  return (
    <PublicLayout>
      {/* Header */}
      <div className="relative pt-[72px] py-16 overflow-hidden">
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              "radial-gradient(ellipse at 50% 0%, rgba(0,212,170,0.06) 0%, transparent 60%)",
          }}
        />
        <div className="relative max-w-[1140px] mx-auto px-6">
          <h1 className="font-display text-[clamp(1.8rem,4vw,3rem)] font-bold tracking-[-0.02em] mb-3">
            Frequently Asked Questions
          </h1>
          <p className="text-text-secondary text-[1.05rem] max-w-[520px] leading-[1.7]">
            Everything you need to know before you subscribe.
          </p>
        </div>
      </div>

      <div className="max-w-[860px] mx-auto px-6 pb-20">
        <FaqAccordion items={faqs} />

        <div className="mt-12">
          <DiscordCTA
            variant="compact"
            heading="Still have questions?"
            subtext="Reach out in our Discord — the community and team respond fast."
            href={DISCORD_INVITE_URL}
          />
        </div>
      </div>
    </PublicLayout>
  );
}
