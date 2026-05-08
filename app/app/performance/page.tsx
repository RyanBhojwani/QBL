import Link from "next/link";
import PublicLayout from "@/components/PublicLayout";

const statCards = [
  { label: "Win Rate", value: "—", sub: "W–L record" },
  { label: "ROI", value: "—", sub: "all settled picks" },
  { label: "Total Picks", value: "—", sub: "since launch" },
  { label: "Avg. EV", value: "—", sub: "per pick" },
];

const byTier = [
  { tier: "Basic (1–5★)", picks: "—", winRate: "—", roi: "—" },
  { tier: "Premium (3–5★)", picks: "—", winRate: "—", roi: "—" },
  { tier: "VIP (5★ only)", picks: "—", winRate: "—", roi: "—" },
];

export default function PerformancePage() {
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
            Performance
          </h1>
          <p className="text-text-secondary text-[1.05rem] max-w-[520px] leading-[1.7]">
            Verified win/loss record and ROI across all picks since launch. Updated daily after
            settlement.
          </p>
        </div>
      </div>

      <div className="max-w-[1140px] mx-auto px-6 pb-20">
        {/* Hero ROI stat */}
        <div className="mb-10 flex justify-center sm:justify-start">
          <div className="relative overflow-hidden text-center px-12 py-10 bg-bg-surface border border-[rgba(0,212,170,0.3)] rounded-2xl w-full max-w-[360px]">
            <div
              className="absolute inset-0 pointer-events-none"
              style={{
                background:
                  "radial-gradient(ellipse at center, rgba(0,212,170,0.06) 0%, transparent 70%)",
              }}
            />
            <span className="stat-hero-glow relative block font-display text-[clamp(3rem,8vw,5rem)] font-bold text-accent tracking-[-0.03em] leading-none">
              —
            </span>
            <span className="relative block font-display text-base font-semibold text-text-primary mt-2 uppercase tracking-[0.1em]">
              All-Time ROI
            </span>
            <span className="relative block text-[0.8rem] text-text-muted mt-1">
              Updated after daily settlement
            </span>
          </div>
        </div>

        {/* Summary stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
          {statCards.map((s) => (
            <div
              key={s.label}
              className="bg-bg-surface border border-qbl-border rounded-[12px] p-6 text-center"
            >
              <span className="block font-display text-3xl font-bold text-accent mb-1">
                {s.value}
              </span>
              <span className="block text-text-primary text-xs font-display font-semibold uppercase tracking-[0.08em] mb-0.5">
                {s.label}
              </span>
              <span className="block text-text-muted text-[0.7rem]">{s.sub}</span>
            </div>
          ))}
        </div>

        {/* By tier */}
        <h2 className="font-display text-lg font-semibold text-text-primary mb-4">
          Results by Tier
        </h2>
        <div className="rounded-[12px] border border-qbl-border overflow-hidden mb-12">
          <div className="grid grid-cols-[1fr_80px_80px_80px] gap-4 px-6 py-3 bg-bg-surface border-b border-qbl-border text-[0.7rem] font-display font-semibold text-text-muted uppercase tracking-[0.08em]">
            <span>Tier</span>
            <span className="text-right">Picks</span>
            <span className="text-right">Win Rate</span>
            <span className="text-right">ROI</span>
          </div>
          {byTier.map((row) => (
            <div
              key={row.tier}
              className="grid grid-cols-[1fr_80px_80px_80px] gap-4 px-6 py-4 bg-bg-primary border-b border-qbl-border last:border-0 items-center"
            >
              <span className="text-text-secondary text-sm">{row.tier}</span>
              <span className="text-text-muted text-sm text-right">{row.picks}</span>
              <span className="text-text-muted text-sm text-right">{row.winRate}</span>
              <span className="text-text-muted text-sm text-right">{row.roi}</span>
            </div>
          ))}
        </div>

        {/* Coming soon notice */}
        <div className="rounded-[12px] border border-qbl-border bg-bg-surface px-6 py-8 text-center">
          <div className="text-3xl text-accent mb-3 opacity-50">📊</div>
          <h3 className="font-display text-lg font-semibold text-text-primary mb-2">
            Full results coming soon
          </h3>
          <p className="text-text-secondary text-sm max-w-[400px] mx-auto leading-[1.6]">
            The worker has been live since May 2026. As picks settle, results will populate here and
            in the member dashboard automatically.
          </p>
          <Link
            href="/dashboard/picks"
            className="inline-block mt-6 font-display font-semibold text-sm px-6 py-2.5 rounded-[8px] bg-accent text-bg-primary border-2 border-accent hover:bg-accent-hover hover:border-accent-hover transition-all hover:-translate-y-[1px]"
          >
            View Current Picks
          </Link>
        </div>
      </div>
    </PublicLayout>
  );
}
