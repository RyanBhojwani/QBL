const placeholderStats = [
  { label: "Record", value: "—" },
  { label: "Win Rate", value: "—" },
  { label: "ROI", value: "—" },
  { label: "Total Picks", value: "—" },
];

export default function ResultsPage() {
  return (
    <div>
      {/* Page header */}
      <div className="mb-8">
        <h1 className="font-display text-2xl font-bold text-text-primary mb-1">Results</h1>
        <p className="text-text-secondary text-sm">
          Historical settled picks with verified win/loss record and ROI.
        </p>
      </div>

      {/* Summary stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {placeholderStats.map((s) => (
          <div
            key={s.label}
            className="bg-bg-surface border border-qbl-border rounded-[12px] p-6 text-center"
          >
            <span className="block font-display text-3xl font-bold text-accent mb-1">{s.value}</span>
            <span className="block text-text-secondary text-xs uppercase tracking-[0.08em] font-display font-semibold">
              {s.label}
            </span>
          </div>
        ))}
      </div>

      {/* Filter bar */}
      <div className="flex gap-3 mb-6 flex-wrap">
        {["All Sports ▾", "All Markets ▾", "Date Range ▾"].map((label) => (
          <button
            key={label}
            className="font-display text-sm px-4 py-2 rounded-[8px] bg-bg-surface border border-qbl-border text-text-secondary opacity-60 cursor-not-allowed transition-all"
            disabled
          >
            {label}
          </button>
        ))}
      </div>

      {/* Results table */}
      <div className="rounded-[12px] border border-qbl-border overflow-hidden">
        <div className="hidden md:grid grid-cols-[80px_1fr_100px_100px_80px_80px_90px] gap-4 px-6 py-3 bg-bg-surface border-b border-qbl-border text-[0.75rem] font-display font-semibold text-text-muted uppercase tracking-[0.08em]">
          <span>Stars</span>
          <span>Team / Market</span>
          <span>Sport</span>
          <span>Book</span>
          <span>Odds</span>
          <span>Result</span>
          <span>Settled</span>
        </div>

        {/* Empty state */}
        <div className="py-20 text-center bg-bg-primary">
          <div className="text-4xl text-accent mb-4 opacity-60">📊</div>
          <h3 className="font-display text-xl font-semibold text-text-primary mb-2">
            No settled picks yet
          </h3>
          <p className="text-text-secondary text-sm max-w-[360px] mx-auto leading-[1.6]">
            Results will appear here once picks have been graded. Settlement runs daily at 4:00 AM ET.
          </p>
        </div>
      </div>
    </div>
  );
}
