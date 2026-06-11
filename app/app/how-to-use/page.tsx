import Link from "next/link";
import PublicLayout from "@/components/PublicLayout";
import { DISCORD_INVITE_URL } from "@/lib/constants";

const steps = [
  {
    n: "1",
    title: "Check the Picks tab",
    body: "The Picks page shows all current +EV opportunities sorted by confidence. New picks appear automatically — the table updates in real time via Supabase Realtime when the model runs.",
    tip: "Don't wait for a refresh. If the page is open, it updates itself.",
  },
  {
    n: "2",
    title: "Read the star rating",
    body: "Stars (1–5) indicate the model's confidence that this pick will beat the closing line. Your tier determines which stars are visible to you.",
    tip: "Basic: 1★ · Premium: 1–3★ · VIP: 1–5★",
  },
  {
    n: "3",
    title: "Note the book and odds",
    body: "The pick shows which sportsbook has the best price. Go directly to that book and confirm the line is still available before betting. Always verify current odds before placing a bet.",
    tip: "Lines move fast. Verify the odds at the book before placing.",
  },
  {
    n: "4",
    title: "Use the bet size",
    body: "The Bet Size column shows half-Kelly sizing in units (1 unit = 1% of bankroll), capped at 3u. Never exceed the suggested size. Underbetting is fine — overbetting is how bankrolls bust.",
    tip: "Half-Kelly is already conservative. Stick to it.",
  },
  {
    n: "5",
    title: "Set up Discord for real-time alerts",
    body: "Discord alerts fire the moment a pick is found — often before you check the dashboard. Join your tier channel and enable mobile push notifications for the fastest possible response.",
    tip: "Enable mobile push notifications in Discord for the picks channel.",
  },
  {
    n: "6",
    title: "Track your results",
    body: "The Performance tab shows your verified W/L record and ROI as picks settle. Settlement runs daily at 4:00 AM ET using official scores.",
    tip: "It can take 12–24 hours after a game ends for settlement to run.",
  },
];

const dos = [
  "Check picks early — lines are freshest when first posted",
  "Use the suggested bet size or less",
  "Spread action across multiple sportsbooks",
  "Think in terms of hundreds of picks, not individual results",
  "Keep a separate betting bankroll from personal funds",
];

const donts = [
  "Chase losses by increasing bet size after a cold streak",
  "Parlay multiple +EV picks together",
  "Bet picks where the line has already moved significantly",
  "Bet money you can't afford to lose",
  "Ignore the star rating — higher stars = higher confidence",
];

export default function HowToUsePage() {
  return (
    <PublicLayout>
      <section className="pt-[72px] max-w-[860px] mx-auto px-6 py-16">
        <div className="mb-10">
          <h1 className="font-display text-[clamp(1.8rem,4vw,2.6rem)] font-bold text-text-primary mb-3">
            How To Use
          </h1>
          <p className="text-text-secondary text-[1rem] leading-[1.7]">
            Step-by-step guide to getting the most out of your subscription.
          </p>
        </div>

        <div className="space-y-4 mb-12">
          {steps.map((s) => (
            <div key={s.n} className="bg-bg-surface border border-qbl-border rounded-[12px] p-6 flex gap-5">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[rgba(0,212,170,0.1)] border border-[rgba(0,212,170,0.2)] flex items-center justify-center">
                <span className="font-display font-bold text-accent text-sm">{s.n}</span>
              </div>
              <div className="flex-1">
                <h3 className="font-display font-semibold text-sm text-text-primary mb-2">{s.title}</h3>
                <p className="text-text-secondary text-sm leading-[1.7] mb-2">{s.body}</p>
                <p className="text-text-muted text-xs bg-[rgba(0,212,170,0.04)] border border-[rgba(0,212,170,0.1)] rounded-[6px] px-3 py-1.5 inline-block">
                  {s.tip}
                </p>
              </div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
          <div className="bg-bg-surface border border-[rgba(0,212,170,0.2)] rounded-[12px] p-6">
            <h2 className="font-display font-semibold text-sm text-accent mb-4 uppercase tracking-[0.06em]">✓ Do</h2>
            <ul className="space-y-2.5">
              {dos.map((d) => (
                <li key={d} className="flex items-start gap-2.5 text-sm text-text-secondary">
                  <span className="text-accent font-bold mt-0.5 shrink-0">✓</span>
                  {d}
                </li>
              ))}
            </ul>
          </div>
          <div className="bg-bg-surface border border-[rgba(239,68,68,0.15)] rounded-[12px] p-6">
            <h2 className="font-display font-semibold text-sm text-red-400 mb-4 uppercase tracking-[0.06em]">✗ Don&apos;t</h2>
            <ul className="space-y-2.5">
              {donts.map((d) => (
                <li key={d} className="flex items-start gap-2.5 text-sm text-text-secondary">
                  <span className="text-red-400 font-bold mt-0.5 shrink-0">✗</span>
                  {d}
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          <Link
            href="/pricing"
            className="font-display font-semibold text-sm px-5 py-2.5 rounded-[8px] bg-accent text-bg-primary border-2 border-accent hover:bg-accent-hover hover:border-accent-hover transition-all hover:-translate-y-[1px]"
          >
            View Plans
          </Link>
          <a
            href={DISCORD_INVITE_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="font-display font-semibold text-sm px-5 py-2.5 rounded-[8px] border border-qbl-border text-text-secondary hover:text-text-primary hover:border-[rgba(0,212,170,0.3)] transition-all"
          >
            Join Discord
          </a>
          <Link
            href="/rules"
            className="font-display font-semibold text-sm px-5 py-2.5 rounded-[8px] border border-qbl-border text-text-secondary hover:text-text-primary hover:border-[rgba(0,212,170,0.3)] transition-all"
          >
            Rules &amp; Disclaimer
          </Link>
        </div>
      </section>
    </PublicLayout>
  );
}
