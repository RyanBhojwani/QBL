import Link from "next/link";
import { currentUser } from "@clerk/nextjs/server";

const glossary = [
  {
    term: "EV (Expected Value)",
    def: "+EV means the bet returns more than it costs on average over many trials. If a coin flip pays +$110 when you win and you lose -$100, and the true probability is 50%, your EV is +$5 per $100 bet.",
  },
  {
    term: "Devig",
    def: "Sportsbooks bake in a margin (the \"juice\" or \"vig\"). Devigging strips that out to reveal the true implied probability. We use multiplicative devigging across multiple sharp books.",
  },
  {
    term: "Sharp vs. Soft books",
    def: "Sharp books (e.g., Pinnacle) accept high-limit action and move lines efficiently based on sharp money. Soft books (e.g., FanDuel, DraftKings) lag behind — that lag is your edge window.",
  },
  {
    term: "CLV (Closing Line Value)",
    def: "If you bet -110 and the game closes at -130, you beat the close by 20 cents. Consistently beating the close proves your process has edge. Our model's CLV probability predicts which picks are most likely to do this.",
  },
  {
    term: "Star Rating",
    def: "1–5 stars based on the model's CLV probability output. Higher stars = higher confidence the pick has genuine edge vs. the closing line. Basic sees 1★, Premium sees 1–3★, VIP sees all five stars.",
  },
  {
    term: "Kelly Criterion",
    def: "A formula for optimal bet sizing: f = edge / odds. We use half-Kelly to reduce variance, capped at 3 units of bankroll. Over-betting is how bankrolls blow up even with real edge.",
  },
  {
    term: "Line movement",
    def: "Odds shift as money comes in and the market becomes more efficient. Sharp money moves lines faster than recreational money. Our picks target the early window before sharp action closes the gap.",
  },
  {
    term: "Market efficiency",
    def: "Efficient markets price outcomes correctly. The closing line is the most efficient price. Our edge window is the period between when soft books post early lines and when sharp money moves them to efficiency.",
  },
];

const concepts = [
  {
    title: "Why +EV betting works long-term",
    body: "Sportsbooks make money because most bettors place -EV bets (bet underdogs at inflated prices, chase losses, bet with their hearts). The small minority of bettors who consistently find +EV edges — and bet them with discipline — tend to profit over a large enough sample. It's the same principle as profitable poker: making decisions with a mathematical edge, repeatedly, over time.",
  },
  {
    title: "Variance is your biggest enemy",
    body: "Even a bet with 60% true probability loses 40% of the time. A string of losses doesn't mean your edge is gone — it means variance is normal. With proper bankroll management (2–3% per bet), you can weather a 20-bet losing streak without busting. This is why bet sizing discipline matters as much as pick quality.",
  },
  {
    title: "Why you shouldn't parlay these picks",
    body: "Parlays multiply your edge — but they also multiply variance exponentially. A 2-leg parlay of two 55% picks only wins 30% of the time. Single-game bets let you systematically capture edge. Parlays are a sportsbook's most profitable product for a reason.",
  },
  {
    title: "Account longevity",
    body: "Consistently winning at retail sportsbooks can trigger account limits — this is a known aspect of +EV betting. Diversifying across multiple books is standard practice: it gives you access to the best price on each game and reduces dependence on any single book. Having accounts at several sportsbooks also means more opportunities to act when a pick is found.",
  },
];

function UpgradeWall({ hasSubscription }: { hasSubscription: boolean }) {
  return (
    <div className="rounded-[12px] border border-qbl-border bg-bg-surface px-8 py-14 text-center max-w-[520px] mx-auto mt-20">
      <div className="text-3xl mb-4 opacity-60">🔒</div>
      <h2 className="font-display text-xl font-semibold text-text-primary mb-2">
        Educational content is a Premium feature
      </h2>
      <p className="text-text-secondary text-sm leading-[1.7] mb-6">
        {hasSubscription
          ? "Your current plan doesn't include the education library. Upgrade to Premium or VIP to access concepts, glossary, and strategy guides for +EV betting."
          : "Subscribe to Premium or VIP to access the full education library — concepts, glossary, and strategy guides for +EV betting."}
      </p>
      <Link
        href="/pricing"
        className="inline-block font-display font-semibold text-sm px-6 py-3 rounded-[8px] bg-accent text-bg-primary border-2 border-accent hover:bg-accent-hover hover:border-accent-hover transition-all hover:-translate-y-[1px]"
      >
        {hasSubscription ? "Upgrade to Premium" : "View Plans"}
      </Link>
    </div>
  );
}

export default async function EducationPage() {
  const user = await currentUser();
  const tier = user?.publicMetadata?.tier as string | undefined;

  if (!tier || tier === "basic") return (
    <div>
      <div className="mb-8">
        <h1 className="font-display text-2xl font-bold text-text-primary mb-1">Education</h1>
        <p className="text-text-secondary text-sm">Core concepts behind +EV betting.</p>
      </div>
      <UpgradeWall hasSubscription={tier === "basic"} />
    </div>
  );

  return (
    <div>
      <div className="mb-8">
        <h1 className="font-display text-2xl font-bold text-text-primary mb-1">Education</h1>
        <p className="text-text-secondary text-sm">
          Core concepts behind +EV betting and how to use this service effectively.
        </p>
      </div>

      <h2 className="font-display text-base font-semibold text-text-primary mb-4">Core Concepts</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-10">
        {concepts.map((c) => (
          <div key={c.title} className="bg-bg-surface border border-qbl-border rounded-[12px] p-6">
            <h3 className="font-display font-semibold text-sm text-accent mb-2">{c.title}</h3>
            <p className="text-text-secondary text-sm leading-[1.75]">{c.body}</p>
          </div>
        ))}
      </div>

      <h2 className="font-display text-base font-semibold text-text-primary mb-4">Glossary</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-10">
        {glossary.map((g) => (
          <div key={g.term} className="bg-bg-surface border border-qbl-border rounded-[10px] p-5">
            <p className="font-display font-semibold text-sm text-text-primary mb-1.5">{g.term}</p>
            <p className="text-text-secondary text-sm leading-[1.65]">{g.def}</p>
          </div>
        ))}
      </div>

      <div className="rounded-[12px] border border-qbl-border bg-bg-surface px-6 py-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <p className="font-display font-semibold text-text-primary text-sm mb-1">Want more detail?</p>
          <p className="text-text-muted text-xs">See the full methodology breakdown on the public site.</p>
        </div>
        <div className="flex gap-3 flex-wrap shrink-0">
          <Link href="/how-it-works" className="font-display font-semibold text-sm px-4 py-2 rounded-[8px] border border-qbl-border text-text-secondary hover:text-text-primary hover:border-[rgba(0,212,170,0.3)] transition-all">
            How It Works
          </Link>
          <Link href="/faq" className="font-display font-semibold text-sm px-4 py-2 rounded-[8px] border border-qbl-border text-text-secondary hover:text-text-primary hover:border-[rgba(0,212,170,0.3)] transition-all">
            FAQ
          </Link>
        </div>
      </div>
    </div>
  );
}
