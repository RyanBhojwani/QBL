import { fetchModelResults } from "@/lib/performance";
import PublicPerformanceOverview from "@/components/PublicPerformanceOverview";
import Link from "next/link";
import PublicLayout from "@/components/PublicLayout";

export const revalidate = 3600;

export default async function PerformancePage() {
  const results = await fetchModelResults();

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
        {/* ── Time window overview + modals ─────────────────────────────────── */}
        <PublicPerformanceOverview results={results} />

        {/* ── Locked breakdown section ───────────────────────────────────────── */}
        <div className="relative rounded-[16px] overflow-hidden border border-qbl-border">
          {/* Blurred placeholder content */}
          <div
            className="blur-sm pointer-events-none select-none opacity-50 p-6"
            aria-hidden="true"
          >
            <h2 className="font-display text-lg font-semibold text-text-primary mb-4">
              By Star Rating
            </h2>
            <div className="rounded-[12px] border border-qbl-border overflow-hidden mb-8">
              {["5 Stars", "4 Stars", "3 Stars", "2 Stars", "1 Star"].map((s) => (
                <div
                  key={s}
                  className="grid grid-cols-5 gap-4 px-6 py-4 bg-bg-primary border-b border-qbl-border last:border-0"
                >
                  <span className="text-text-secondary text-sm">{s}</span>
                  <span className="text-accent text-sm text-right">+9.4%</span>
                  <span className="text-accent text-sm text-right">+7.2%</span>
                  <span className="text-accent text-sm text-right">+310%</span>
                  <span className="text-text-secondary text-sm text-right">56.1%</span>
                </div>
              ))}
            </div>
            <h2 className="font-display text-lg font-semibold text-text-primary mb-4">
              By Sport
            </h2>
            <div className="rounded-[12px] border border-qbl-border overflow-hidden mb-2">
              {["NHL", "Baseball", "NBA", "Soccer", "NFL"].map((s) => (
                <div
                  key={s}
                  className="grid grid-cols-5 gap-4 px-6 py-4 bg-bg-primary border-b border-qbl-border last:border-0"
                >
                  <span className="text-text-secondary text-sm">{s}</span>
                  <span className="text-accent text-sm text-right">+10.3%</span>
                  <span className="text-accent text-sm text-right">+8.5%</span>
                  <span className="text-accent text-sm text-right">+266%</span>
                  <span className="text-text-secondary text-sm text-right">61.0%</span>
                </div>
              ))}
            </div>
          </div>

          {/* Lock overlay */}
          <div
            className="absolute inset-0 flex items-center justify-center"
            style={{
              background:
                "linear-gradient(to bottom, rgba(10,14,23,0.1) 0%, rgba(10,14,23,0.82) 45%, rgba(10,14,23,0.97) 100%)",
            }}
          >
            <div className="text-center px-6 py-8 max-w-[420px]">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-[rgba(0,212,170,0.08)] border border-[rgba(0,212,170,0.2)] mb-5">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="text-accent"
                >
                  <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
              </div>
              <h3 className="font-display text-xl font-semibold text-text-primary mb-2">
                More in-depth data for subscribers
              </h3>
              <p className="text-text-secondary text-sm leading-[1.7] mb-6">
                Breakdowns by star rating, sport, and market type are available to members. See
                exactly where edge is coming from.
              </p>
              <Link
                href="/pricing"
                className="inline-block font-display font-semibold text-sm px-6 py-3 rounded-[8px] bg-accent text-bg-primary border-2 border-accent hover:bg-accent-hover hover:border-accent-hover transition-all hover:-translate-y-[1px]"
              >
                View Plans
              </Link>
            </div>
          </div>
        </div>
      </div>
    </PublicLayout>
  );
}
