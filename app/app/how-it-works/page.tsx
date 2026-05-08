import Link from "next/link";
import PublicLayout from "@/components/PublicLayout";
import DiscordCTA from "@/components/DiscordCTA";

const steps = [
  {
    n: "01",
    title: "Live odds fetched every 15 minutes",
    body: "Our Python worker polls The Odds API v4 for every active market across MLB, NHL, NBA, EPL, MMA, and Boxing. All major US sportsbooks are included — FanDuel, DraftKings, BetMGM, Caesars, and more.",
  },
  {
    n: "02",
    title: "Sharp books set the true price",
    body: "We separate books into \"sharp\" (efficient market makers: Pinnacle, Bookmaker) and \"soft\" (retail books that lag). Sharp odds are aggregated using a weighted average to estimate the true probability of each outcome.",
  },
  {
    n: "03",
    title: "Devig strips the margin",
    body: "Every set of odds has a bookmaker's juice baked in. We use multiplicative devigging to remove that margin and convert sharp odds into true implied probabilities — the most accurate estimate of the real-world likelihood.",
  },
  {
    n: "04",
    title: "EV is calculated vs. soft books",
    body: "For each outcome, we compare the true probability against the price offered at every soft book. When a soft book's odds imply a lower probability than our model's estimate, there's positive expected value. EV = (true_prob × (odds − 1)) − (1 − true_prob).",
  },
  {
    n: "05",
    title: "Threshold filters remove noise",
    body: "Not every positive-EV line is worth playing. We apply Kelly criterion (minimum 0.25%), EV floor, and CLV probability filters to surface only high-quality opportunities. Lines with EV > 30% are excluded as likely data errors.",
  },
  {
    n: "06",
    title: "Star rating signals confidence",
    body: "Each pick gets a 1–5 star rating based on CLV probability — the likelihood the pick beats the closing line. This is derived from a bagged logistic regression model trained on historical closing lines. 5-star picks are the sharpest.",
  },
  {
    n: "07",
    title: "You get alerted instantly",
    body: "New picks fire to your Discord tier channel the moment they're found. Basic members see all 1–5 star picks. Premium sees 3–5 stars. VIP sees 5-star only. The dashboard shows all picks in real time.",
  },
];

const glossary = [
  { term: "EV (Expected Value)", def: "The average profit per unit bet over many wagers. +5% EV means for every $100 bet, you expect +$5 back on average." },
  { term: "Devig", def: "Removing the sportsbook's margin (juice/vig) from their odds to reveal the true implied probability." },
  { term: "CLV (Closing Line Value)", def: "How much your odds beat the final pre-game price. Consistently beating the close is the strongest indicator of long-term edge." },
  { term: "Kelly Criterion", def: "A formula for optimal bet sizing based on edge and odds. We use half-Kelly to reduce variance, capped at 3% of bankroll." },
  { term: "Sharp books", def: "Sportsbooks that accept sharp action and have efficient, well-calibrated lines. Used as our benchmark for true probability." },
  { term: "Soft books", def: "Retail sportsbooks that move lines more slowly and tolerate recreational bettors — where our edge is exploited." },
];

export default function HowItWorksPage() {
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
            How It Works
          </h1>
          <p className="text-text-secondary text-[1.05rem] max-w-[560px] leading-[1.7]">
            A full breakdown of the model — from raw sportsbook odds to a +EV pick in your Discord.
          </p>
        </div>
      </div>

      <div className="max-w-[1140px] mx-auto px-6 pb-20">
        {/* Steps */}
        <div className="space-y-6 mb-20">
          {steps.map((s, i) => (
            <div
              key={s.n}
              className="flex gap-6 bg-bg-surface border border-qbl-border rounded-[12px] p-6 sm:p-8"
            >
              <div className="font-display text-[1.8rem] font-bold text-accent opacity-30 leading-none shrink-0 pt-0.5 w-10">
                {s.n}
              </div>
              <div>
                <h2 className="font-display text-base font-semibold text-text-primary mb-2">
                  {s.title}
                </h2>
                <p className="text-text-secondary text-sm leading-[1.75]">{s.body}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Glossary */}
        <h2 className="font-display text-xl font-semibold text-text-primary mb-6">Glossary</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-16">
          {glossary.map((g) => (
            <div
              key={g.term}
              className="bg-bg-surface border border-qbl-border rounded-[10px] p-5"
            >
              <p className="font-display font-semibold text-sm text-accent mb-1.5">{g.term}</p>
              <p className="text-text-secondary text-sm leading-[1.65]">{g.def}</p>
            </div>
          ))}
        </div>

        {/* CTA */}
        <div className="rounded-[12px] border border-qbl-border bg-bg-surface px-8 py-8 flex flex-col sm:flex-row items-center justify-between gap-5">
          <div>
            <p className="font-display font-semibold text-text-primary mb-1">Ready to get started?</p>
            <p className="text-text-secondary text-sm">
              Join Discord free or subscribe for full dashboard access.
            </p>
          </div>
          <div className="flex gap-3 flex-wrap shrink-0">
            <a
              href="#"
              className="font-display font-semibold text-sm px-5 py-2.5 rounded-[8px] bg-discord text-white hover:bg-[#4752c4] transition-all"
            >
              Join Discord
            </a>
            <Link
              href="/pricing"
              className="font-display font-semibold text-sm px-5 py-2.5 rounded-[8px] bg-accent text-bg-primary border-2 border-accent hover:bg-accent-hover transition-all"
            >
              View Pricing
            </Link>
          </div>
        </div>
      </div>
    </PublicLayout>
  );
}
