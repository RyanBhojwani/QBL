import FaqAccordion from "@/components/FaqAccordion";
import { DISCORD_INVITE_URL } from "@/lib/constants";
import DiscordCTA from "@/components/DiscordCTA";

const faqs = [
  {
    q: "When do new picks appear?",
    a: "The model runs every 15 minutes during peak hours and every 2 hours overnight. Picks appear on this dashboard in real time via Supabase Realtime — you don't need to refresh. Discord alerts fire the moment a pick is found, which is typically a few seconds faster than the dashboard update.",
  },
  {
    q: "Why do picks sometimes disappear?",
    a: "The picks table shows the current run's output. If a line moves unfavorably before the next run, that pick will no longer appear — the edge is gone. This is by design. Only bets that still have +EV at the time of each run are shown.",
  },
  {
    q: "What does my star rating filter mean?",
    a: "Stars reflect CLV probability — how likely a pick is to beat the closing line. Basic sees 1–2★. Premium sees 1–4★. VIP sees all picks including 5★ plays. Higher tiers surface higher-confidence plays with less noise.",
  },
  {
    q: "How do I know which book to bet at?",
    a: "The Book column shows the specific sportsbook offering the best price for that pick. Go directly to that book, find the game and market, and confirm the odds match before betting. Lines can move quickly.",
  },
  {
    q: "The odds on my sportsbook don't match what's shown. What do I do?",
    a: "Lines move between the model run and when you check. If the displayed odds are gone, the pick may no longer be +EV. Don't bet at worse odds hoping the edge is still there — only bet when the odds match or are better.",
  },
  {
    q: "How does settlement work?",
    a: "Settlement runs daily at 4:00 AM ET. The system fetches official scores from The Odds API and grades each tracked bet as Win, Loss, or Push. Graded results appear in the Performance tab within 24 hours of a game ending.",
  },
  {
    q: "Can I upgrade or downgrade my plan?",
    a: "Yes. Go to the Account page and click \"Manage Subscription\" to upgrade, downgrade, or cancel through the Stripe customer portal. Changes take effect immediately.",
  },
  {
    q: "I'm getting limited by sportsbooks. Is this normal?",
    a: "Yes — consistently winning at retail sportsbooks can trigger account limits. This happens to sharp bettors and is a sign your process is working. Use multiple books to diversify, and see the Education page for tips on extending account longevity.",
  },
];

export default function DashboardFaqPage() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="font-display text-2xl font-bold text-text-primary mb-1">
          FAQ
        </h1>
        <p className="text-text-secondary text-sm">
          Common questions from members.
        </p>
      </div>

      <div className="max-w-[860px]">
        <FaqAccordion items={faqs} />

        <div className="mt-8">
          <DiscordCTA
            variant="compact"
            heading="Didn't find your answer?"
            subtext="Ask in Discord — the community and team respond quickly."
            href={DISCORD_INVITE_URL}
          />
        </div>
      </div>
    </div>
  );
}
