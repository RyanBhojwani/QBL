import Link from "next/link";

const statCards = [
  { label: "Record", value: "—", sub: "W–L–P" },
  { label: "Win Rate", value: "—", sub: "graded picks" },
  { label: "ROI", value: "—", sub: "all settled" },
  { label: "Total Picks", value: "—", sub: "tracked" },
];

const byTier = [
  { tier: "Basic (1–5★)", picks: "—", winRate: "—", roi: "—" },
  { tier: "Premium (3–5★)", picks: "—", winRate: "—", roi: "—" },
  { tier: "VIP (5★ only)", picks: "—", winRate: "—", roi: "—" },
];

const bySport = [
  { sport: "MLB", picks: "—", winRate: "—", roi: "—" },
  { sport: "NBA", picks: "—", winRate: "—", roi: "—" },
  { sport: "NHL", picks: "—", winRate: "—", roi: "—" },
  { sport: "Soccer", picks: "—", winRate: "—", roi: "—" },
  { sport: "MMA / Boxing", picks: "—", winRate: "—", roi: "—" },
];

export default function DashboardPerformancePage() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="font-display text-2xl font-bold text-text-primary mb-1">Performance</h1>
        <p className="text-text-secondary text-sm">
          Verified win/loss record across all tracked picks. Updates daily after settlement.
        </p>
      </div>

      {/* Summary stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
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
      <h2 className="font-display text-base font-semibold text-text-primary mb-3">By Tier</h2>
      <div className="rounded-[12px] border border-qbl-border overflow-hidden mb-8">
        <div className="grid grid-cols-[1fr_80px_80px_80px] gap-4 px-6 py-3 bg-bg-surface border-b border-qbl-border text-[0.7rem] font-display font-semibold text-text-muted uppercase tracking-[0.08em]">
          <span>Tier</span>
          <span className="text-right">Picks</span>
          <span className="text-right">Win %</span>
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

      {/* By sport */}
      <h2 className="font-display text-base font-semibold text-text-primary mb-3">By Sport</h2>
      <div className="rounded-[12px] border border-qbl-border overflow-hidden mb-10">
        <div className="grid grid-cols-[1fr_80px_80px_80px] gap-4 px-6 py-3 bg-bg-surface border-b border-qbl-border text-[0.7rem] font-display font-semibold text-text-muted uppercase tracking-[0.08em]">
          <span>Sport</span>
          <span className="text-right">Picks</span>
          <span className="text-right">Win %</span>
          <span className="text-right">ROI</span>
        </div>
        {bySport.map((row) => (
          <div
            key={row.sport}
            className="grid grid-cols-[1fr_80px_80px_80px] gap-4 px-6 py-4 bg-bg-primary border-b border-qbl-border last:border-0 items-center"
          >
            <span className="text-text-secondary text-sm">{row.sport}</span>
            <span className="text-text-muted text-sm text-right">{row.picks}</span>
            <span className="text-text-muted text-sm text-right">{row.winRate}</span>
            <span className="text-text-muted text-sm text-right">{row.roi}</span>
          </div>
        ))}
      </div>

      {/* Coming soon notice */}
      <div className="rounded-[12px] border border-qbl-border bg-bg-surface px-6 py-8 text-center">
        <div className="text-3xl text-accent mb-3 opacity-50">📊</div>
        <h3 className="font-display text-base font-semibold text-text-primary mb-2">
          Results populate as picks settle
        </h3>
        <p className="text-text-secondary text-sm max-w-[400px] mx-auto leading-[1.6]">
          Settlement runs daily at 4:00 AM ET. Picks are graded W/L/P using official scores from
          The Odds API.
        </p>
        <Link
          href="/dashboard/picks"
          className="inline-block mt-5 font-display font-semibold text-sm px-5 py-2.5 rounded-[8px] border border-qbl-border text-text-secondary hover:text-text-primary hover:border-[rgba(0,212,170,0.3)] transition-all"
        >
          View Current Picks
        </Link>
      </div>
    </div>
  );
}
