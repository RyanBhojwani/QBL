import { createClient } from "@supabase/supabase-js";

export type ModelResult = {
  time_window: string;
  segment_type: string;
  segment_val: string;
  n_picks: number | null;
  win_pct: number | null;
  roi: number | null;
  clv_roi: number | null;
  cagr: number | null;
};

export async function fetchModelResults(): Promise<ModelResult[]> {
  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
  const { data } = await supabase
    .from("model_results")
    .select("time_window,segment_type,segment_val,n_picks,win_pct,roi,clv_roi,cagr");
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

/** Format a decimal ratio as a signed percentage: 0.049 -> "+4.9%" */
export function fPct(v: number | null | undefined, decimals = 1): string {
  if (v == null) return "-";
  return (v >= 0 ? "+" : "") + (v * 100).toFixed(decimals) + "%";
}

/** Format a win rate (no sign): 0.531 -> "53.1%" */
export function fWinPct(v: number | null | undefined): string {
  if (v == null) return "-";
  return (v * 100).toFixed(1) + "%";
}

/** Tailwind text color class based on sign of value. */
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
  mma: "MMA (legacy)",
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
    s
      .split("_")
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(" ")
  );
}

export function marketLabel(m: string): string {
  return MARKET_LABELS[m] ?? m;
}

/** "baseball|h2h" -> "Baseball - Moneyline" */
export function sportMarketLabel(v: string): string {
  const idx = v.indexOf("|");
  if (idx === -1) return v;
  return `${sportLabel(v.slice(0, idx))} - ${marketLabel(v.slice(idx + 1))}`;
}
