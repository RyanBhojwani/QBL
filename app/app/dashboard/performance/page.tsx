import {
  fetchModelResults,
  getResult,
  fPct,
  fWinPct,
  sportLabel,
  sportMarketLabel,
  type ModelResult,
} from "@/lib/performance";
import {
  TimeWindowRow,
  BreakdownTable,
  type CardDef,
} from "@/components/PerformanceComponents";

export const revalidate = 3600;

function card(
  label: string,
  value: string,
  colorValue?: number | null,
  neutral?: boolean
): CardDef {
  return { label, value, colorValue, neutral };
}

export default async function DashboardPerformancePage() {
  const results = await fetchModelResults();

  const at = getResult(results, "all_time", "overall", "overall");
  const td = getResult(results, "30d", "overall", "overall");
  const yd = getResult(results, "1d", "overall", "overall");

  const starRows = [1, 2, 3, 4, 5].map((s) => ({
    label: s === 1 ? "1 Star" : `${s} Stars`,
    data: getResult(results, "all_time", "star", String(s)),
  }));

  const sportRows: { label: string; data: ModelResult }[] = results
    .filter((r) => r.time_window === "all_time" && r.segment_type === "sport")
    .sort((a, b) => (b.roi ?? -Infinity) - (a.roi ?? -Infinity))
    .map((r) => ({ label: sportLabel(r.segment_val), data: r }));

  const sportMarketRows: { label: string; data: ModelResult }[] = results
    .filter((r) => r.time_window === "all_time" && r.segment_type === "sport_market")
    .sort((a, b) => (b.roi ?? -Infinity) - (a.roi ?? -Infinity))
    .map((r) => ({ label: sportMarketLabel(r.segment_val), data: r }));

  return (
    <div>
      <div className="mb-8">
        <h1 className="font-display text-2xl font-bold text-text-primary mb-1">Performance</h1>
        <p className="text-text-secondary text-sm">
          Verified win/loss record across all tracked picks. Updates daily after settlement.
        </p>
      </div>

      {/* ── Time window overview ─────────────────────────────────────────────── */}
      <div className="space-y-8 mb-12">
        <TimeWindowRow
          label="All-Time"
          cards={[
            card("Real ROI", fPct(at?.roi), at?.roi),
            card("Expected ROI", fPct(at?.clv_roi), at?.clv_roi),
            card("Win Rate", fWinPct(at?.win_pct), undefined, true),
            card("Annualized Return", fPct(at?.cagr), at?.cagr),
          ]}
        />
        <TimeWindowRow
          label="Past 30 Days"
          cards={[
            card("Real ROI", fPct(td?.roi), td?.roi),
            card("Expected ROI", fPct(td?.clv_roi), td?.clv_roi),
            card("Win Rate", fWinPct(td?.win_pct), undefined, true),
            card("Annualized Return", fPct(td?.cagr), td?.cagr),
          ]}
        />
        <TimeWindowRow
          label="Yesterday"
          cards={[
            card("Real ROI", fPct(yd?.roi), yd?.roi),
            card("Expected ROI", fPct(yd?.clv_roi), yd?.clv_roi),
            card("Win Rate", fWinPct(yd?.win_pct), undefined, true),
            card(
              "Number of Bets",
              yd?.n_picks != null ? String(yd.n_picks) : "-",
              undefined,
              true
            ),
          ]}
        />
      </div>

      {/* ── By Star Rating ───────────────────────────────────────────────────── */}
      <h2 className="font-display text-base font-semibold text-text-primary mb-3">
        By Star Rating
      </h2>
      <BreakdownTable nameHeader="Rating" rows={starRows} className="mb-8" />

      {/* ── By Sport ────────────────────────────────────────────────────────── */}
      <h2 className="font-display text-base font-semibold text-text-primary mb-3">By Sport</h2>
      <BreakdownTable nameHeader="Sport" rows={sportRows} className="mb-8" />

      {/* ── By Sport and Market ──────────────────────────────────────────────── */}
      <h2 className="font-display text-base font-semibold text-text-primary mb-3">
        By Sport and Market
      </h2>
      <BreakdownTable nameHeader="Sport / Market" rows={sportMarketRows} />
    </div>
  );
}
