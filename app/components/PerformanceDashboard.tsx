"use client";

import { useState } from "react";
import {
  ModelResult,
  getResult,
  fPct,
  fWinPct,
  pctColor,
  sportLabel,
  sportMarketLabel,
} from "@/lib/performance";
import { TimeWindowRow, type CardDef } from "@/components/PerformanceComponents";
import PerformanceModal from "@/components/PerformanceModal";

type TimeWindow = "all_time" | "30d";

function card(
  label: string,
  value: string,
  colorValue?: number | null,
  neutral?: boolean
): CardDef {
  return { label, value, colorValue, neutral };
}

function nBets(v: number | null | undefined): string {
  return v != null ? String(v) : "-";
}

// ── Window toggle ─────────────────────────────────────────────────────────────

function WindowToggle({
  selected,
  onChange,
}: {
  selected: TimeWindow;
  onChange: (w: TimeWindow) => void;
}) {
  return (
    <div className="flex rounded-[8px] border border-qbl-border overflow-hidden text-[0.7rem]">
      {(["all_time", "30d"] as TimeWindow[]).map((w) => (
        <button
          key={w}
          onClick={() => onChange(w)}
          className={`px-3 py-1.5 font-display font-semibold transition-colors ${
            w !== "all_time" ? "border-l border-qbl-border" : ""
          } ${
            selected === w
              ? "bg-[rgba(0,212,170,0.15)] text-accent"
              : "text-text-muted hover:text-text-primary hover:bg-[rgba(255,255,255,0.04)]"
          }`}
        >
          {w === "all_time" ? "All-Time" : "Past 30 Days"}
        </button>
      ))}
    </div>
  );
}

// ── Clickable breakdown table ─────────────────────────────────────────────────

function BreakdownSection({
  title,
  nameHeader,
  rows,
  onRowClick,
  selectedWindow,
  onWindowChange,
  className = "",
}: {
  title: string;
  nameHeader: string;
  rows: { label: string; data: ModelResult | undefined }[];
  onRowClick: (label: string, data: ModelResult) => void;
  selectedWindow: TimeWindow;
  onWindowChange: (w: TimeWindow) => void;
  className?: string;
}) {
  return (
    <div className={className}>
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-display text-base font-semibold text-text-primary">{title}</h2>
        <WindowToggle selected={selectedWindow} onChange={onWindowChange} />
      </div>
      <div className="rounded-[12px] border border-qbl-border overflow-hidden">
        <div className="overflow-x-auto">
          <div className="min-w-[640px]">
            <div className="grid grid-cols-[1fr_64px_80px_80px_100px_80px] px-6 py-3 bg-bg-surface border-b border-qbl-border text-[0.7rem] font-display font-semibold text-text-muted uppercase tracking-[0.08em]">
              <span>{nameHeader}</span>
              <span className="text-right"># Bets</span>
              <span className="text-right">Real ROI</span>
              <span className="text-right">Exp. ROI</span>
              <span className="text-right">Ann. Return</span>
              <span className="text-right">Win Rate</span>
            </div>
            {rows.length === 0 ? (
              <div className="px-6 py-8 text-center text-text-muted text-sm">No data yet.</div>
            ) : (
              rows.map(({ label, data }) => (
                <div
                  key={label}
                  role="button"
                  tabIndex={data ? 0 : -1}
                  onClick={() => data && onRowClick(label, data)}
                  onKeyDown={(e) => {
                    if ((e.key === "Enter" || e.key === " ") && data) onRowClick(label, data);
                  }}
                  className={`grid grid-cols-[1fr_64px_80px_80px_100px_80px] px-6 py-4 bg-bg-primary border-b border-qbl-border last:border-0 items-center transition-colors ${
                    data
                      ? "cursor-pointer hover:bg-[rgba(0,212,170,0.04)] group"
                      : "cursor-default"
                  }`}
                >
                  <span className="text-text-secondary text-sm font-display font-medium whitespace-nowrap pr-4 group-hover:text-text-primary transition-colors">
                    {label}
                  </span>
                  <span className="text-sm text-right text-text-secondary">
                    {data?.n_picks != null ? String(data.n_picks) : "-"}
                  </span>
                  <span className={`text-sm text-right font-display font-semibold ${pctColor(data?.roi)}`}>
                    {fPct(data?.roi)}
                  </span>
                  <span className={`text-sm text-right font-display font-semibold ${pctColor(data?.clv_roi)}`}>
                    {fPct(data?.clv_roi)}
                  </span>
                  <span className={`text-sm text-right font-display font-semibold ${pctColor(data?.cagr)}`}>
                    {fPct(data?.cagr)}
                  </span>
                  <span className="text-sm text-right text-text-secondary">
                    {fWinPct(data?.win_pct)}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Main dashboard ────────────────────────────────────────────────────────────

export default function PerformanceDashboard({ results }: { results: ModelResult[] }) {
  const [modal, setModal] = useState<{ title: string; data: ModelResult } | null>(null);

  const [starWindow, setStarWindow]             = useState<TimeWindow>("all_time");
  const [sportWindow, setSportWindow]           = useState<TimeWindow>("all_time");
  const [sportMarketWindow, setSportMarketWindow] = useState<TimeWindow>("all_time");

  const at = getResult(results, "all_time", "overall", "overall");
  const td = getResult(results, "30d",      "overall", "overall");
  const yd = getResult(results, "1d",       "overall", "overall");

  const starRows = [1, 2, 3, 4, 5].map((s) => ({
    label: s === 1 ? "1 Star" : `${s} Stars`,
    data: getResult(results, starWindow, "star", String(s)),
  }));

  const sportRows: { label: string; data: ModelResult }[] = results
    .filter((r) => r.time_window === sportWindow && r.segment_type === "sport")
    .sort((a, b) => (b.roi ?? -Infinity) - (a.roi ?? -Infinity))
    .map((r) => ({ label: sportLabel(r.segment_val), data: r }));

  const sportMarketRows: { label: string; data: ModelResult }[] = results
    .filter((r) => r.time_window === sportMarketWindow && r.segment_type === "sport_market")
    .sort((a, b) => (b.roi ?? -Infinity) - (a.roi ?? -Infinity))
    .map((r) => ({ label: sportMarketLabel(r.segment_val), data: r }));

  const windowSuffix = (w: TimeWindow) => w === "30d" ? " — Past 30 Days" : "";

  function open(title: string, data: ModelResult | undefined) {
    if (data) setModal({ title, data });
  }

  const moreStatsBtn =
    "mt-4 w-full font-display text-sm font-semibold text-text-secondary hover:text-accent border border-qbl-border hover:border-[rgba(0,212,170,0.35)] rounded-[10px] py-2.5 transition-all hover:bg-[rgba(0,212,170,0.04)]";

  return (
    <>
      {/* ── Time window overview ──────────────────────────────────────────── */}
      <div className="space-y-8 mb-12">
        {/* All-Time */}
        <div>
          <TimeWindowRow
            label="All-Time"
            cards={[
              card("Number of Bets", nBets(at?.n_picks), undefined, true),
              card("Real ROI", fPct(at?.roi), at?.roi),
              card("Expected ROI", fPct(at?.clv_roi), at?.clv_roi),
              card("Win Rate", fWinPct(at?.win_pct), undefined, true),
              card("Annualized Return", fPct(at?.cagr), at?.cagr),
            ]}
          />
          <button onClick={() => open("All-Time Detailed Analysis", at)} className={moreStatsBtn}>
            View Detailed Statistics
          </button>
        </div>

        {/* Past 30 Days */}
        <div>
          <TimeWindowRow
            label="Past 30 Days"
            cards={[
              card("Number of Bets", nBets(td?.n_picks), undefined, true),
              card("Real ROI", fPct(td?.roi), td?.roi),
              card("Expected ROI", fPct(td?.clv_roi), td?.clv_roi),
              card("Win Rate", fWinPct(td?.win_pct), undefined, true),
              card("Annualized Return", fPct(td?.cagr), td?.cagr),
            ]}
          />
          <button onClick={() => open("30-Day Detailed Analysis", td)} className={moreStatsBtn}>
            View Detailed Statistics
          </button>
        </div>

        {/* Yesterday */}
        <TimeWindowRow
          label="Yesterday"
          cards={[
            card("Number of Bets", nBets(yd?.n_picks), undefined, true),
            card("Real ROI", fPct(yd?.roi), yd?.roi),
            card("Expected ROI", fPct(yd?.clv_roi), yd?.clv_roi),
            card("Win Rate", fWinPct(yd?.win_pct), undefined, true),
            card("Annualized Return", fPct(yd?.cagr), yd?.cagr),
          ]}
        />
      </div>

      {/* ── Breakdown tables ──────────────────────────────────────────────── */}
      <BreakdownSection
        title="By Star Rating"
        nameHeader="Rating"
        rows={starRows}
        onRowClick={(label, data) => open(label + windowSuffix(starWindow), data)}
        selectedWindow={starWindow}
        onWindowChange={setStarWindow}
        className="mb-8"
      />
      <BreakdownSection
        title="By Sport"
        nameHeader="Sport"
        rows={sportRows}
        onRowClick={(label, data) => open(label + windowSuffix(sportWindow), data)}
        selectedWindow={sportWindow}
        onWindowChange={setSportWindow}
        className="mb-8"
      />
      <BreakdownSection
        title="By Sport and Market"
        nameHeader="Sport / Market"
        rows={sportMarketRows}
        onRowClick={(label, data) => open(label + windowSuffix(sportMarketWindow), data)}
        selectedWindow={sportMarketWindow}
        onWindowChange={setSportMarketWindow}
      />

      {/* ── Modal ─────────────────────────────────────────────────────────── */}
      {modal && (
        <PerformanceModal
          title={modal.title}
          data={modal.data}
          onClose={() => setModal(null)}
        />
      )}
    </>
  );
}
