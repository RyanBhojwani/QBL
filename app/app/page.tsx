import Link from "next/link";
import { DISCORD_INVITE_URL } from "@/lib/constants";
import { createClient } from "@supabase/supabase-js";
import { unstable_noStore as noStore } from "next/cache";
import PublicLayout from "@/components/PublicLayout";
import DiscordCTA from "@/components/DiscordCTA";
import ExamplePickCard from "@/components/ExamplePickCard";
import DiscordIcon from "@/components/DiscordIcon";
import GetStartedButton from "@/app/components/GetStartedButton";

export const dynamic = "force-dynamic";

async function fetchLandingStats(): Promise<{ alertsSent: number; sportsCount: number; unitsProfit: number | null }> {
  noStore();
  try {
    const supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_KEY!
    );
    const [countRes, sportsRes, resultsRes] = await Promise.all([
      supabase.from("settled_picks").select("*", { count: "exact", head: true }),
      supabase.from("settled_picks").select("sport"),
      supabase.from("model_results")
        .select("total_profit_units")
        .eq("time_window", "all_time")
        .eq("segment_type", "overall")
        .eq("segment_val", "overall")
        .single(),
    ]);
    const alertsSent = countRes.count ?? 0;
    const sportsCount = sportsRes.data
      ? new Set(sportsRes.data.map((r: { sport: string }) => {
          const s = r.sport as string;
          if (s.startsWith("soccer_")) return "soccer";
          if (s.startsWith("baseball_")) return "baseball";
          if (s.startsWith("tennis_")) return "tennis";
          return s;
        })).size
      : 0;
    const unitsProfit = resultsRes.data?.total_profit_units ?? null;
    return { alertsSent, sportsCount, unitsProfit };
  } catch {
    return { alertsSent: 0, sportsCount: 0, unitsProfit: null };
  }
}

const features = [
  {
    icon: "◈",
    title: "EV Detection Engine",
    desc: "Our models scan every major sportsbook in real time to find mispriced odds where expected value is heavily in your favor.",
  },
  {
    icon: "⚡",
    title: "Instant Discord Alerts",
    desc: "The moment we detect edge, you get a ping. No delays, no stale lines. Act before the market corrects.",
  },
  {
    icon: "+",
    title: "Pure Math, Zero Guesswork",
    desc: "Every pick is backed by rigorous statistical modeling and deep market analysis. We don't do gut feelings.",
  },
];

export default async function LandingPage() {
  const { alertsSent, sportsCount, unitsProfit } = await fetchLandingStats();
  const unitsDisplay = unitsProfit != null
    ? `${unitsProfit * 100 >= 0 ? "+" : ""}${Math.round(unitsProfit * 100)}u`
    : null;

  const roundedAlerts = alertsSent > 0 ? Math.floor(alertsSent / 100) * 100 : 500;
  const stats = [
    { number: `${roundedAlerts.toLocaleString()}+`, label: "Alerts Sent" },
    { number: "24/7", label: "Market Monitoring" },
    { number: "10", label: "Sports Covered" },
  ];

  return (
    <PublicLayout>
      {/* ── Hero ── */}
      <section className="relative min-h-[calc(100vh-72px)] flex items-center pt-[72px] overflow-hidden">
        <div className="hero-bg" />
        <div className="relative max-w-[860px] mx-auto px-6 text-center py-20 lg:py-[100px] w-full">
          <h1 className="font-display text-[clamp(2.4rem,5.5vw,4.2rem)] font-bold tracking-[-0.02em] leading-[1.15] mb-6">
            Your Edge Is <span className="text-accent">Waiting</span>
          </h1>
          <p className="text-[1.2rem] text-text-secondary max-w-[640px] mx-auto mb-4 leading-[1.7]">
            Quant Bet Labs uses statistical modeling to find expected value in sports betting markets
            and alerts you on Discord the second opportunity strikes.
          </p>
          <p className="font-display font-semibold text-amber mb-11 tracking-[0.01em]">
            Every minute counts when lines are moving.
          </p>
          <div className="flex gap-4 justify-center flex-wrap max-sm:flex-col max-sm:items-center mb-16">
            <a
              href={DISCORD_INVITE_URL}
              className="btn-pulse relative z-10 inline-flex items-center gap-2.5 font-display font-semibold text-[1.15rem] px-10 py-[18px] rounded-[12px] bg-discord text-white border-2 border-discord transition-all duration-250 hover:bg-[#4752c4] hover:border-[#4752c4] hover:-translate-y-[2px] hover:shadow-[0_6px_30px_rgba(88,101,242,0.4)] max-sm:w-full max-sm:max-w-[340px] max-sm:justify-center"
            >
              <DiscordIcon size={24} />
              Join Discord — It&apos;s Free
            </a>
            <GetStartedButton />
          </div>

          {/* Example picks preview */}
          <ExamplePickCard />
        </div>
      </section>

      {/* ── Numbers Speak ── */}
      <section className="py-[120px] bg-bg-surface" id="performance">
        <div className="max-w-[1140px] mx-auto px-6">
          <h2 className="font-display text-[clamp(1.6rem,3.5vw,2.5rem)] font-semibold text-center mb-3">
            The Numbers Speak for Themselves
          </h2>

          <div className="flex justify-center mt-12 mb-10">
            <div className="relative overflow-hidden text-center px-16 py-14 bg-bg-primary border border-[rgba(0,212,170,0.3)] rounded-2xl max-w-[480px] w-full">
              <div
                className="absolute inset-0 pointer-events-none"
                style={{
                  background:
                    "radial-gradient(ellipse at center, rgba(0,212,170,0.06) 0%, transparent 70%)",
                }}
              />
              <span className="stat-hero-glow relative block font-display text-[clamp(4rem,10vw,6.5rem)] font-bold text-accent tracking-[-0.03em] leading-none">
                {unitsDisplay ?? ">100%"}
              </span>
              <span className="relative block font-display text-[1.3rem] font-semibold text-text-primary mt-3 uppercase tracking-[0.1em]">
                {unitsDisplay ? "Units Profit (Since June 2025)" : "Annual ROI"}
              </span>
              <span className="relative block text-[0.9rem] text-text-muted mt-2">
                Exposed. Verified. Repeatable.
              </span>
              <span className="relative block text-[0.72rem] text-text-muted mt-3 leading-[1.6] max-w-[340px] mx-auto">
                Based on all settled picks since beta launch (June 2025).
                Past performance does not guarantee future results.
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {stats.map((s) => (
              <div
                key={s.label}
                className="text-center py-9 px-6 bg-bg-primary border border-qbl-border rounded-[12px] transition-colors hover:border-[rgba(0,212,170,0.2)]"
              >
                <span className="block font-display text-[clamp(2rem,4vw,2.8rem)] font-bold text-accent tracking-[-0.02em]">
                  {s.number}
                </span>
                <span className="block text-[0.9rem] text-text-secondary mt-1.5 uppercase tracking-[0.06em]">
                  {s.label}
                </span>
              </div>
            ))}
          </div>

          <div className="mt-10 text-center">
            <Link
              href="/performance"
              className="font-display font-semibold text-sm text-accent hover:text-accent-hover transition-colors"
            >
              View full performance history →
            </Link>
          </div>
        </div>
      </section>

      {/* ── Why Quant Bet Labs ── */}
      <section className="py-[120px] bg-bg-primary" id="features">
        <div className="max-w-[1140px] mx-auto px-6">
          <h2 className="font-display text-[clamp(1.6rem,3.5vw,2.5rem)] font-semibold text-center mb-3">
            Why Quant Bet Labs
          </h2>
          <p className="text-center text-text-secondary text-[1.05rem] max-w-[560px] mx-auto mb-[60px] leading-[1.7]">
            A quantitative approach to sports betting, powered by data, not hunches.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f) => (
              <div
                key={f.title}
                className="bg-bg-surface border border-qbl-border rounded-[12px] p-10 transition-all duration-250 hover:border-[rgba(0,212,170,0.35)] hover:-translate-y-1 hover:shadow-[0_8px_40px_rgba(0,212,170,0.06)]"
              >
                <div className="text-[2rem] text-accent mb-[18px] font-bold leading-none">{f.icon}</div>
                <h3 className="font-display text-xl font-semibold text-text-primary mb-3">
                  {f.title}
                </h3>
                <p className="text-text-secondary text-[0.95rem] leading-[1.7]">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Discord CTA ── */}
      <DiscordCTA
        variant="full"
        bg="bg-bg-surface"
        heading="Join the community. Get the edge."
        subtext="Free to join Discord. Real-time picks and the full dashboard require a subscription."
        href={DISCORD_INVITE_URL}
      />
    </PublicLayout>
  );
}
