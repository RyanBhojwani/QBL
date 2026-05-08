import { createClient } from "@supabase/supabase-js";

export type DailyCurvePoint = {
  date: string;
  bankroll_real: number;
  bankroll_exp: number;
};

export type ModelResult = {
  time_window: string;
  segment_type: string;
  segment_val: string;
  // Counts
  n_picks: number | null;
  n_wins: number | null;
  n_losses: number | null;
  n_pushes: number | null;
  // Win / odds
  win_pct: number | null;
  avg_odds: number | null;
  // Real ROI
  roi: number | null;
  total_profit_units: number | null;
  // CLV
  clv_n_picks: number | null;
  clv_win_pct: number | null;
  clv_roi: number | null;
  clv_profit_units: number | null;
  // EV
  ev_roi: number | null;
  ev_profit_units: number | null;
  // Financial
  cagr: number | null;
  bankroll_return: number | null;
  log_return: number | null;
  max_drawdown: number | null;
  volatility: number | null;
  sharpe: number | null;
  sortino: number | null;
  // Chart
  daily_curve: DailyCurvePoint[] | null;
};

export async function fetchModelResults(): Promise<ModelResult[]> {
  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
  const { data } = await supabase.from("model_results").select(`
    time_window, segment_type, segment_val,
    n_picks, n_wins, n_losses, n_pushes,
    win_pct, avg_odds,
    roi, total_profit_units,
    clv_n_picks, clv_win_pct, clv_roi, clv_profit_units,
    ev_roi, ev_profit_units,
    cagr, bankroll_return, log_return,
    max_drawdown, volatility, sharpe, sortino,
    daily_curve
  `);
  return (data ?? []) as ModelResult[];
}

export function getResult(
  rows: ModelResult[],
  timeWindow: string,
  segmentType: string,
  segmentVal: string
): ModelResult | undefined {
  return rows.find(
    (r) =>
      r.time_window === timeWindow &&
      r.segment_type === segmentType &&
      r.segment_val === segmentVal
  );
}

/** Signed percentage: 0.049 -> "+4.9%" */
export function fPct(v: number | null | undefined, decimals = 1): string {
  if (v == null) return "-";
  return (v >= 0 ? "+" : "") + (v * 100).toFixed(decimals) + "%";
}

/** Win rate (no sign): 0.531 -> "53.1%" */
export function fWinPct(v: number | null | undefined): string {
  if (v == null) return "-";
  return (v * 100).toFixed(1) + "%";
}

/** Signed ratio for Sharpe / Sortino: 6.89 -> "+6.89" */
export function fRatio(v: number | null | undefined): string {
  if (v == null) return "-";
  return (v >= 0 ? "+" : "") + v.toFixed(2);
}

/** Drawdown: always negative display */
export function fDrawdown(v: number | null | undefined): string {
  if (v == null) return "-";
  return "-" + (v * 100).toFixed(1) + "%";
}

/** Betting units with sign: 0.921 -> "+0.921u" */
export function fUnits(v: number | null | undefined): string {
  if (v == null) return "-";
  return (v >= 0 ? "+" : "") + v.toFixed(3) + "u";
}

/** Decimal odds: 1.910 */
export function fOdds(v: number | null | undefined): string {
  if (v == null) return "-";
  return v.toFixed(3);
}

/** Break-even win rate implied by decimal odds */
export function fBreakEven(avgOdds: number | null | undefined): string {
  if (!avgOdds || avgOdds <= 0) return "-";
  return (100 / avgOdds).toFixed(1) + "%";
}

/** Tailwind text color based on sign */
export function pctColor(v: number | null | undefined): string {
  if (v == null) return "text-text-muted";
  return v >= 0 ? "text-accent" : "text-red-400";
}

const SPORT_LABELS: Record<string, string> = {
  baseball: "Baseball",
  soccer: "Soccer",
  basketball_nba: "NBA",
  icehockey_nhl: "NHL",
  americanfootball_nfl: "NFL",
  americanfootball_ncaaf: "College Football",
  boxing_boxing: "Boxing",
  mma_mixed_martial_arts: "MMA",
  tennis: "Tennis",
};

const MARKET_LABELS: Record<string, string> = {
  h2h: "Moneyline",
  spreads: "Spread",
  totals: "Total",
};

export function sportLabel(s: string): string {
  return (
    SPORT_LABELS[s] ??
    s.split("_").map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")
  );
}

export function marketLabel(m: string): string {
  return MARKET_LABELS[m] ?? m;
}

export function sportMarketLabel(v: string): string {
  const idx = v.indexOf("|");
  if (idx === -1) return v;
  return `${sportLabel(v.slice(0, idx))} - ${marketLabel(v.slice(idx + 1))}`;
}
