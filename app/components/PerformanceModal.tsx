"use client";

import { useEffect, useRef } from "react";
import dynamic from "next/dynamic";
import {
  ModelResult,
  fPct,
  fWinPct,
  fRatio,
  fDrawdown,
  fUnits,
  fOdds,
  fBreakEven,
  pctColor,
} from "@/lib/performance";

// Skip SSR entirely — Recharts uses window/ResizeObserver which crash on the server
const BankrollChart = dynamic(() => import("./BankrollChart"), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-[260px] rounded-[12px] border border-qbl-border bg-bg-surface text-text-muted text-sm">
      Loading chart...
    </div>
  ),
});

// ── Internal layout components ────────────────────────────────────────────────

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="font-display text-[0.7rem] font-bold text-text-muted uppercase tracking-[0.12em] mb-3 mt-8">
      {children}
    </h3>
  );
}

function Stat({
  label,
  value,
  valueClass = "text-text-primary",
  sub,
}: {
  label: string;
  value: string;
  valueClass?: string;
  sub?: string;
}) {
  return (
    <div className="bg-bg-surface border border-qbl-border rounded-[10px] px-4 py-3">
      <p className="text-[0.65rem] font-display font-semibold text-text-muted uppercase tracking-[0.08em] mb-1.5 leading-tight">
        {label}
      </p>
      <p className={`font-display text-[1.05rem] font-bold leading-none ${valueClass}`}>{value}</p>
      {sub && <p className="text-[0.65rem] text-text-muted mt-1">{sub}</p>}
    </div>
  );
}

// ── Modal ─────────────────────────────────────────────────────────────────────

export default function PerformanceModal({
  title,
  data,
  onClose,
}: {
  title: string;
  data: ModelResult;
  onClose: () => void;
}) {
  const overlayRef = useRef<HTMLDivElement>(null);

  // daily_curve may arrive as a JSON string (legacy) or a parsed array
  const curve: DailyCurvePoint[] = (() => {
    const raw = data.daily_curve;
    if (!raw) return [];
    if (Array.isArray(raw)) return raw as DailyCurvePoint[];
    if (typeof raw === "string") {
      try { return JSON.parse(raw) as DailyCurvePoint[]; } catch { return []; }
    }
    return [];
  })();

  // Close on Escape
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  // Lock body scroll
  useEffect(() => {
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = ""; };
  }, []);

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(6,9,18,0.88)", backdropFilter: "blur(10px)" }}
      onClick={(e) => { if (e.target === overlayRef.current) onClose(); }}
    >
      <div className="relative w-full max-w-[880px] max-h-[90vh] overflow-y-auto bg-bg-primary rounded-[16px] border border-qbl-border shadow-2xl">
        {/* Sticky header */}
        <div className="sticky top-0 z-10 flex items-center justify-between px-6 py-4 border-b border-qbl-border bg-bg-primary">
          <h2 className="font-display text-lg font-bold text-text-primary">{title}</h2>
          <button
            onClick={onClose}
            className="text-text-muted hover:text-text-primary transition-colors p-1.5 rounded-[6px] hover:bg-[rgba(255,255,255,0.06)]"
            aria-label="Close"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="px-6 pb-8">
          {/* Summary cards — parse daily_curve defensively (may arrive as string or array) */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 pt-6 mb-2">
            {[
              {
                label: "Number of Bets",
                value: data.n_picks != null ? String(data.n_picks) : "-",
                neutral: true,
              },
              { label: "Real ROI", value: fPct(data.roi), colorValue: data.roi },
              { label: "Expected ROI", value: fPct(data.clv_roi), colorValue: data.clv_roi },
              { label: "Win Rate", value: fWinPct(data.win_pct), neutral: true },
              { label: "Ann. Return", value: fPct(data.cagr), colorValue: data.cagr },
            ].map((c) => {
              const color =
                "neutral" in c && c.neutral
                  ? "text-text-primary"
                  : "colorValue" in c && c.colorValue == null
                  ? "text-text-muted"
                  : "colorValue" in c && (c.colorValue ?? 0) >= 0
                  ? "text-accent"
                  : "text-red-400";
              return (
                <div
                  key={c.label}
                  className="bg-bg-surface border border-qbl-border rounded-[12px] p-4 text-center"
                >
                  <span className={`block font-display text-[1.5rem] font-bold leading-none mb-1.5 ${color}`}>
                    {c.value}
                  </span>
                  <span className="block text-[0.65rem] font-display font-semibold text-text-muted uppercase tracking-[0.08em]">
                    {c.label}
                  </span>
                </div>
              );
            })}
          </div>

          {/* ── Bankroll Chart ────────────────────────────────────────── */}
          <SectionHeading>Bankroll Curve</SectionHeading>
          <BankrollChart data={curve} />

          {/* ── Win / Loss Record ─────────────────────────────────────── */}
          <SectionHeading>Win / Loss Record</SectionHeading>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <Stat
              label="Record"
              value={`${data.n_wins ?? 0}W - ${data.n_losses ?? 0}L - ${data.n_pushes ?? 0}P`}
            />
            <Stat label="Win Rate" value={fWinPct(data.win_pct)} />
            <Stat label="Avg Odds" value={fOdds(data.avg_odds)} />
            <Stat
              label="Break-Even Win Rate"
              value={fBreakEven(data.avg_odds)}
              sub="Win rate needed to break even at these odds"
            />
            <Stat label="CLV Win Rate" value={fWinPct(data.clv_win_pct)} sub="% of bets that beat closing line" />
            <Stat label="Picks with CLV" value={data.clv_n_picks != null ? String(data.clv_n_picks) : "-"} />
          </div>

          {/* ── Returns and Profit ────────────────────────────────────── */}
          <SectionHeading>Returns and Profit</SectionHeading>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <Stat
              label="Real ROI"
              value={fPct(data.roi)}
              valueClass={pctColor(data.roi)}
              sub="Actual return per unit wagered"
            />
            <Stat
              label="Real Profit"
              value={fUnits(data.total_profit_units)}
              valueClass={pctColor(data.total_profit_units)}
              sub="Total units at half-Kelly sizing"
            />
            <Stat
              label="Expected ROI (CLV)"
              value={fPct(data.clv_roi)}
              valueClass={pctColor(data.clv_roi)}
              sub="Edge captured vs closing line"
            />
            <Stat
              label="CLV Profit"
              value={fUnits(data.clv_profit_units)}
              valueClass={pctColor(data.clv_profit_units)}
            />
            <Stat
              label="Model ROI (EV)"
              value={fPct(data.ev_roi)}
              valueClass={pctColor(data.ev_roi)}
              sub="Predicted edge at time of bet"
            />
            <Stat
              label="EV Profit"
              value={fUnits(data.ev_profit_units)}
              valueClass={pctColor(data.ev_profit_units)}
            />
          </div>

          {/* ── Financial Statistics ──────────────────────────────────── */}
          <SectionHeading>Financial Statistics</SectionHeading>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <Stat
              label="Annualized Return (CAGR)"
              value={fPct(data.cagr)}
              valueClass={pctColor(data.cagr)}
              sub="Compounded annual growth rate"
            />
            <Stat
              label="Bankroll Return"
              value={fPct(data.bankroll_return)}
              valueClass={pctColor(data.bankroll_return)}
              sub="Simple return on $1,000 starting bankroll"
            />
            <Stat
              label="Log Return"
              value={
                data.log_return != null
                  ? (data.log_return >= 0 ? "+" : "") + data.log_return.toFixed(3)
                  : "-"
              }
              valueClass={pctColor(data.log_return)}
              sub="Continuously compounded return"
            />
            <Stat
              label="Max Drawdown"
              value={fDrawdown(data.max_drawdown)}
              valueClass="text-red-400"
              sub="Worst peak-to-trough decline"
            />
            <Stat
              label="Volatility"
              value={fPct(data.volatility)}
              sub="Annualized std dev of daily returns"
            />
            <Stat
              label="Sharpe Ratio"
              value={fRatio(data.sharpe)}
              valueClass={pctColor(data.sharpe)}
              sub="Risk-adjusted return (3.96% risk-free)"
            />
            <Stat
              label="Sortino Ratio"
              value={fRatio(data.sortino)}
              valueClass={pctColor(data.sortino)}
              sub="Downside-risk adjusted return"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
