import { fPct, fWinPct, pctColor, type ModelResult } from "@/lib/performance";

export type CardDef = {
  label: string;
  value: string;
  /** Raw numeric value used to determine color. Omit or pass undefined for neutral. */
  colorValue?: number | null;
  /** If true, always renders in text-primary (no green/red). */
  neutral?: boolean;
};

export function TimeWindowRow({
  label,
  cards,
}: {
  label: string;
  cards: CardDef[];
}) {
  return (
    <div>
      <p className="font-display text-xs font-semibold text-text-muted uppercase tracking-[0.1em] mb-3">
        {label}
      </p>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {cards.map((c) => {
          const color = c.neutral
            ? "text-text-primary"
            : c.colorValue == null
            ? "text-text-muted"
            : c.colorValue >= 0
            ? "text-accent"
            : "text-red-400";
          return (
            <div
              key={c.label}
              className="bg-bg-surface border border-qbl-border rounded-[12px] p-5 text-center"
            >
              <span
                className={`block font-display text-[1.75rem] font-bold leading-none mb-1.5 ${color}`}
              >
                {c.value}
              </span>
              <span className="block text-text-primary text-xs font-display font-semibold uppercase tracking-[0.08em]">
                {c.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function BreakdownTable({
  nameHeader,
  rows,
  className = "",
}: {
  nameHeader: string;
  rows: { label: string; data: ModelResult | undefined }[];
  className?: string;
}) {
  return (
    <div className={`rounded-[12px] border border-qbl-border overflow-hidden ${className}`}>
      <div className="overflow-x-auto">
        <div className="min-w-[580px]">
          {/* Header */}
          <div className="grid grid-cols-[1fr_88px_88px_110px_88px] px-6 py-3 bg-bg-surface border-b border-qbl-border text-[0.7rem] font-display font-semibold text-text-muted uppercase tracking-[0.08em]">
            <span>{nameHeader}</span>
            <span className="text-right">Real ROI</span>
            <span className="text-right">Exp. ROI</span>
            <span className="text-right">Ann. Return</span>
            <span className="text-right">Win Rate</span>
          </div>
          {/* Body */}
          {rows.length === 0 ? (
            <div className="px-6 py-8 text-center text-text-muted text-sm">No data yet.</div>
          ) : (
            rows.map(({ label, data }) => (
              <div
                key={label}
                className="grid grid-cols-[1fr_88px_88px_110px_88px] px-6 py-4 bg-bg-primary border-b border-qbl-border last:border-0 items-center"
              >
                <span className="text-text-secondary text-sm font-display font-medium whitespace-nowrap pr-4">
                  {label}
                </span>
                <span
                  className={`text-sm text-right font-display font-semibold ${pctColor(data?.roi)}`}
                >
                  {fPct(data?.roi)}
                </span>
                <span
                  className={`text-sm text-right font-display font-semibold ${pctColor(data?.clv_roi)}`}
                >
                  {fPct(data?.clv_roi)}
                </span>
                <span
                  className={`text-sm text-right font-display font-semibold ${pctColor(data?.cagr)}`}
                >
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
  );
}
