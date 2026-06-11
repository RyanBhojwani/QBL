function Stars({ count }: { count: number }) {
  return (
    <span className="text-sm font-bold tracking-tight">
      <span className="text-amber">{"★".repeat(count)}</span>
      <span className="text-text-muted opacity-25">{"★".repeat(5 - count)}</span>
    </span>
  );
}

const picks = [
  {
    stars: 5,
    sport: "NBA",
    team: "Boston Celtics",
    market: "Spread -5.5",
    book: "FanDuel",
    odds: "+108",
    units: "0.8u",
    gameTime: "Tonight 7:30 PM ET",
  },
  {
    stars: 4,
    sport: "MLB",
    team: "New York Yankees",
    market: "Moneyline",
    book: "DraftKings",
    odds: "-115",
    units: "0.6u",
    gameTime: "Tonight 8:05 PM ET",
  },
  {
    stars: 3,
    sport: "NHL",
    team: "Over 6.0",
    market: "Total 6.0",
    book: "BetMGM",
    odds: "+102",
    units: "0.4u",
    gameTime: "Tonight 9:00 PM ET",
  },
];

export default function ExamplePickCard() {
  return (
    <div className="rounded-[12px] border border-[rgba(0,212,170,0.2)] overflow-hidden max-w-[600px] mx-auto shadow-[0_8px_40px_rgba(0,212,170,0.06)]">
      {/* Header */}
      <div className="bg-bg-surface border-b border-qbl-border px-5 py-3 flex items-center justify-between">
        <span className="font-display text-xs font-semibold text-text-muted uppercase tracking-[0.1em]">
          Example Picks
        </span>
      </div>

      {/* Column headers */}
      <div className="hidden sm:grid grid-cols-[80px_1fr_100px_80px] gap-4 px-5 py-2.5 bg-bg-surface border-b border-qbl-border text-[0.65rem] font-display font-semibold text-text-muted uppercase tracking-[0.08em]">
        <span>Stars</span>
        <span>Team / Market</span>
        <span>Odds</span>
        <span>Bet Size</span>
      </div>

      {/* Rows */}
      <div className="divide-y divide-qbl-border bg-bg-primary">
        {picks.map((pick, i) => (
          <div
            key={i}
            className="grid grid-cols-[80px_1fr_100px_80px] gap-4 px-5 py-3.5 items-center"
          >
            <div className="flex items-center gap-2">
              <Stars count={pick.stars} />
            </div>
            <div>
              <p className="text-text-primary font-medium text-sm leading-snug">{pick.team}</p>
              <p className="text-text-muted text-xs mt-0.5">
                {pick.market} · {pick.book} · {pick.sport}
              </p>
            </div>
            <div className="font-display font-semibold text-sm text-text-primary">
              {pick.odds}
            </div>
            <div className="font-display font-semibold text-sm text-accent">{pick.units}</div>
          </div>
        ))}
      </div>

      <div className="bg-bg-surface border-t border-qbl-border px-5 py-2.5">
        <p className="text-text-muted text-[0.7rem] text-center">
          example data
        </p>
      </div>
    </div>
  );
}
