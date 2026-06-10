"use client";

import { useState } from "react";
import { ModelResult, getResult, fPct, fWinPct, fUnits } from "@/lib/performance";
import { TimeWindowRow, type CardDef } from "@/components/PerformanceComponents";
import PerformanceModal from "@/components/PerformanceModal";

function card(
  label: string,
  value: string,
  colorValue?: number | null,
  neutral?: boolean
): CardDef {
  return { label, value, colorValue, neutral };
}

export default function PublicPerformanceOverview({ results }: { results: ModelResult[] }) {
  const [modal, setModal] = useState<{ title: string; data: ModelResult } | null>(null);

  const at = getResult(results, "all_time", "overall", "overall");
  const td = getResult(results, "30d",      "overall", "overall");
  const yd = getResult(results, "1d",       "overall", "overall");

  function open(title: string, data: ModelResult | undefined) {
    if (data) setModal({ title, data });
  }

  const moreStatsBtn =
    "mt-4 w-full font-display text-sm font-semibold text-text-secondary hover:text-accent border border-qbl-border hover:border-[rgba(0,212,170,0.35)] rounded-[10px] py-2.5 transition-all hover:bg-[rgba(0,212,170,0.04)]";

  return (
    <>
      <div className="space-y-8 mb-12">
        {/* All-Time */}
        <div>
          <TimeWindowRow
            label="All-Time"
            cards={[
              card("Number of Bets", at?.n_picks != null ? String(at.n_picks) : "-", undefined, true),
              card("Real ROI", fPct(at?.roi), at?.roi),
              card("Expected ROI", fPct(at?.clv_roi), at?.clv_roi),
              card("Win Rate", fWinPct(at?.win_pct), undefined, true),
              card("Units Profit", fUnits(at?.total_profit_units), at?.total_profit_units),
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
              card("Number of Bets", td?.n_picks != null ? String(td.n_picks) : "-", undefined, true),
              card("Real ROI", fPct(td?.roi), td?.roi),
              card("Expected ROI", fPct(td?.clv_roi), td?.clv_roi),
              card("Win Rate", fWinPct(td?.win_pct), undefined, true),
              card("Units Profit", fUnits(td?.total_profit_units), td?.total_profit_units),
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
            card("Number of Bets", yd?.n_picks != null ? String(yd.n_picks) : "-", undefined, true),
            card("Real ROI", fPct(yd?.roi), yd?.roi),
            card("Expected ROI", fPct(yd?.clv_roi), yd?.clv_roi),
            card("Win Rate", fWinPct(yd?.win_pct), undefined, true),
            card("Units Profit", fUnits(yd?.total_profit_units), yd?.total_profit_units),
            card("Annualized Return", fPct(yd?.cagr), yd?.cagr),
          ]}
        />
      </div>

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
