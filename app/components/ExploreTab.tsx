"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";

// ── Types ──────────────────────────────────────────────────────────────────

type RawRow = {
  id: number;
  sport: string;
  game_id: string;
  commence_time: string;
  home_team: string | null;
  away_team: string | null;
  team: string;
  market: string;
  point: number | null;
  book: string;
  odds_from_best_book: number;
  sharp_odds: number;
  ev: number;
  kelly: number;
  clv_prob_med: number;
  stars: number;
  last_updated: string;
};

type TeamEntry = {
  team: string;
  game_id: string;
  commence_time: string;
  sport: string;
};

// ── Constants ──────────────────────────────────────────────────────────────

const BOOKS_CONFIG = [
  { key: "betmgm",      label: "BetMGM"        },
  { key: "betrivers",   label: "BetRivers"     },
  { key: "caesars",     label: "Caesars"       },
  { key: "draftkings",  label: "DraftKings"    },
  { key: "fanduel",     label: "FanDuel"       },
  { key: "hardrockbet", label: "Hard Rock Bet" },
  { key: "ballybet",    label: "Bally Bet"     },
  { key: "fanatics",    label: "Fanatics"      },
  { key: "thescorebet", label: "theScore Bet"  },
];

const SPORT_LABELS: Record<string, string> = {
  americanfootball_nfl:   "NFL",
  americanfootball_ncaaf: "NCAAF",
  baseball_mlb:           "MLB",
  basketball_nba:         "NBA",
  basketball_ncaab:       "NCAAB",
  icehockey_nhl:          "NHL",
  mma_mixed_martial_arts: "MMA",
  boxing_boxing:          "Boxing",
  tennis:                 "Tennis",
};

// ── Helpers ────────────────────────────────────────────────────────────────

function sportLabel(sport: string): string {
  if (sport.startsWith("soccer_")) return "Soccer";
  if (sport.startsWith("tennis_") || sport === "tennis") return "Tennis";
  return SPORT_LABELS[sport] ?? sport;
}

function toAmerican(decimal: number): string {
  if (!decimal || decimal <= 1) return "—";
  if (decimal >= 2) return `+${Math.round((decimal - 1) * 100)}`;
  return `${Math.round(-100 / (decimal - 1))}`;
}

function fmtEV(ev: number): string {
  if (ev <= 0) return "—";
  return `+${(ev * 100).toFixed(1)}%`;
}

function fmtGameTime(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    weekday: "short", month: "short", day: "numeric",
    hour: "numeric", minute: "2-digit", timeZoneName: "short",
  });
}

function minutesAgo(iso: string): string {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 60000);
  if (diff < 1) return "just now";
  if (diff === 1) return "1 min ago";
  return `${diff} min ago`;
}

function formatSide(row: RawRow): string {
  const { team, market, point } = row;
  if (market === "spreads" && point !== null)
    return `${team} ${point > 0 ? "+" : ""}${point}`;
  if (market === "totals" && point !== null)
    return `${team} ${point}`;
  return team;
}

function bookLabel(book: string): string {
  const found = BOOKS_CONFIG.find(
    (b) => b.key === book || (b.key === "caesars" && book === "williamhill_us")
  );
  return found?.label ?? book.replace(/_/g, " ");
}

// Returns db book slugs for a set of UI book keys (handles caesars alias)
function dbBooks(keys: Set<string>): string[] {
  return Array.from(keys).flatMap((k) =>
    k === "caesars" ? ["caesars", "williamhill_us"] : [k]
  );
}

// Among rows for one outcome, pick best book: highest EV if any >0, else highest odds
function getBestRow(rows: RawRow[], selectedBooks: Set<string>): RawRow | null {
  const filtered = rows.filter((r) => {
    const normalized = r.book === "williamhill_us" ? "caesars" : r.book;
    return selectedBooks.has(normalized) || selectedBooks.has(r.book);
  });
  if (filtered.length === 0) return null;
  const pos = filtered.filter((r) => r.ev > 0);
  if (pos.length > 0) return pos.reduce((a, b) => (a.ev > b.ev ? a : b));
  return filtered.reduce((a, b) =>
    a.odds_from_best_book > b.odds_from_best_book ? a : b
  );
}

// Most common point value among rows for a given team+market
function mainPoint(rows: RawRow[], team: string, market: string): number | null {
  const rel = rows.filter((r) => r.market === market && r.team === team && r.point !== null);
  if (rel.length === 0) return null;
  const counts: Record<number, number> = {};
  for (const r of rel) counts[r.point!] = (counts[r.point!] ?? 0) + 1;
  return parseFloat(Object.entries(counts).sort((a, b) => b[1] - a[1])[0][0]);
}

// Most common total value across all total rows
function mainTotalPoint(rows: RawRow[]): number | null {
  const rel = rows.filter((r) => r.market === "totals" && r.point !== null);
  if (rel.length === 0) return null;
  const counts: Record<number, number> = {};
  for (const r of rel) counts[r.point!] = (counts[r.point!] ?? 0) + 1;
  return parseFloat(Object.entries(counts).sort((a, b) => b[1] - a[1])[0][0]);
}

// ── Sub-components ─────────────────────────────────────────────────────────

function BookChips({
  selected, onToggle, onAll, onClear,
}: {
  selected: Set<string>;
  onToggle: (key: string) => void;
  onAll: () => void;
  onClear: () => void;
}) {
  const allSelected = selected.size === BOOKS_CONFIG.length;
  return (
    <div className="flex flex-wrap gap-2 items-center">
      <button
        onClick={allSelected ? onClear : onAll}
        className="text-xs font-display font-semibold px-3 py-1.5 rounded-full border border-qbl-border text-text-secondary hover:text-text-primary hover:border-[rgba(255,255,255,0.2)] transition-all"
      >
        {allSelected ? "Clear all" : "Select all"}
      </button>
      {BOOKS_CONFIG.map((b) => (
        <button
          key={b.key}
          onClick={() => onToggle(b.key)}
          className={`text-xs font-display font-semibold px-3 py-1.5 rounded-full border transition-all ${
            selected.has(b.key)
              ? "bg-[rgba(0,212,170,0.1)] text-text-primary border-[rgba(0,212,170,0.35)]"
              : "bg-transparent text-text-secondary border-qbl-border hover:border-[rgba(255,255,255,0.2)] hover:text-text-primary"
          }`}
        >
          {b.label}
        </button>
      ))}
    </div>
  );
}

function OutcomeRow({
  label, row,
}: {
  label: string;
  row: RawRow | null;
}) {
  const hasEV = row !== null && row.ev > 0;
  const negEV = row !== null && row.ev <= 0;
  const evClass = hasEV ? "text-accent" : negEV ? "text-red-400" : "text-text-secondary";
  return (
    <div className="grid grid-cols-[1fr_auto_auto_auto] items-center gap-4 py-3 border-b border-qbl-border last:border-0">
      <span className="text-text-primary text-sm font-medium">{label}</span>
      <span className="text-text-secondary text-sm text-right">
        {row ? bookLabel(row.book) : "—"}
      </span>
      <span className="font-display font-semibold text-sm text-text-primary w-16 text-right">
        {row ? toAmerican(row.odds_from_best_book) : "—"}
      </span>
      <span className={`font-display font-semibold text-sm w-16 text-right ${evClass}`}>
        {row ? fmtEV(row.ev) : "—"}
      </span>
    </div>
  );
}

function SectionHeader({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-3 mb-1">
      <span className="font-display text-xs font-semibold uppercase tracking-[0.12em] text-text-secondary">
        {label}
      </span>
      <div className="flex-1 h-px bg-qbl-border" />
    </div>
  );
}

// ── Team Search ────────────────────────────────────────────────────────────

function TeamSearch({ selectedBooks }: { selectedBooks: Set<string> }) {
  const [teams, setTeams] = useState<TeamEntry[]>([]);
  const [teamsLoading, setTeamsLoading] = useState(true);
  const [selectedTeam, setSelectedTeam] = useState<TeamEntry | null>(null);
  const [gameRows, setGameRows] = useState<RawRow[]>([]);
  const [gameLoading, setGameLoading] = useState(false);
  const [query, setQuery] = useState("");
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const supabase = createClient();

  // Close dropdown on outside click
  useEffect(() => {
    function handleOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node))
        setDropdownOpen(false);
    }
    document.addEventListener("mousedown", handleOutside);
    return () => document.removeEventListener("mousedown", handleOutside);
  }, []);

  // Fetch available teams on mount
  useEffect(() => {
    const threeHoursAgo = new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString();
    supabase
      .from("raw_model_output")
      .select("team, game_id, commence_time, sport")
      .eq("market", "h2h")
      .gt("commence_time", threeHoursAgo)
      .order("commence_time", { ascending: true })
      .then(({ data }) => {
        if (data) {
          const seen = new Set<string>();
          const unique: TeamEntry[] = [];
          for (const row of data as TeamEntry[]) {
            if (!seen.has(row.team)) {
              seen.add(row.team);
              unique.push(row);
            }
          }
          setTeams(unique);
        }
        setTeamsLoading(false);
      });
  }, []);

  // Fetch game rows when a team is selected
  useEffect(() => {
    if (!selectedTeam) return;
    setGameLoading(true);
    supabase
      .from("raw_model_output")
      .select("*")
      .eq("game_id", selectedTeam.game_id)
      .then(({ data }) => {
        setGameRows(data ?? []);
        setGameLoading(false);
      });
  }, [selectedTeam?.game_id]);

  const filteredTeams = teams.filter((t) =>
    t.team.toLowerCase().includes(query.toLowerCase())
  );

  // Derive game structure from fetched rows
  const h2hRows     = gameRows.filter((r) => r.market === "h2h");
  const spreadRows  = gameRows.filter((r) => r.market === "spreads");
  const totalRows   = gameRows.filter((r) => r.market === "totals");

  // All unique outcome names from h2h rows (includes "Draw" for soccer 3-way markets)
  const teamNames   = [...new Set(h2hRows.map((r) => r.team))];
  // Actual competing teams only (excludes "Draw") — used for game header and spread/total logic
  const actualTeams = teamNames.filter((t) => t !== "Draw");
  const teamA       = actualTeams[0] ?? selectedTeam?.team ?? "";
  const teamB       = actualTeams[1] ?? "";

  const hasSpread   = spreadRows.length > 0;
  const hasTotal    = totalRows.length > 0;

  const mainSpreadA  = mainPoint(spreadRows, teamA, "spreads");
  const mainSpreadB  = mainPoint(spreadRows, teamB, "spreads");
  const mainTotalVal = mainTotalPoint(totalRows);

  const bestSpread_A = mainSpreadA !== null
    ? getBestRow(spreadRows.filter((r) => r.team === teamA && r.point === mainSpreadA), selectedBooks)
    : null;
  const bestSpread_B = mainSpreadB !== null
    ? getBestRow(spreadRows.filter((r) => r.team === teamB && r.point === mainSpreadB), selectedBooks)
    : null;

  const bestOver  = mainTotalVal !== null
    ? getBestRow(totalRows.filter((r) => r.team.startsWith("Over")  && r.point === mainTotalVal), selectedBooks)
    : null;
  const bestUnder = mainTotalVal !== null
    ? getBestRow(totalRows.filter((r) => r.team.startsWith("Under") && r.point === mainTotalVal), selectedBooks)
    : null;

  // Column header row for results
  const colHeader = (
    <div className="grid grid-cols-[1fr_auto_auto_auto] gap-4 pb-2 mb-1 border-b border-qbl-border">
      <span className="text-xs uppercase tracking-widest text-text-secondary">Side</span>
      <span className="text-xs uppercase tracking-widest text-text-secondary text-right">Book</span>
      <span className="text-xs uppercase tracking-widest text-text-secondary w-16 text-right">Odds</span>
      <span className="text-xs uppercase tracking-widest text-text-secondary w-16 text-right">EV</span>
    </div>
  );

  return (
    <div className="space-y-4">
      {/* Search input */}
      <div ref={dropdownRef} className="relative max-w-[480px]">
        <input
          type="text"
          value={query}
          onChange={(e) => { setQuery(e.target.value); setDropdownOpen(true); }}
          onFocus={() => setDropdownOpen(true)}
          placeholder={teamsLoading ? "Loading teams…" : teams.length === 0 ? "No games in current data" : "Search a team…"}
          disabled={teamsLoading || teams.length === 0}
          className="w-full bg-bg-surface border border-qbl-border rounded-[10px] px-4 py-3 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-[rgba(0,212,170,0.5)] transition-colors disabled:opacity-50"
        />
        {dropdownOpen && !teamsLoading && filteredTeams.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-bg-surface border border-qbl-border rounded-[10px] shadow-2xl z-50 max-h-[280px] overflow-y-auto">
            {filteredTeams.map((t) => (
              <button
                key={`${t.game_id}-${t.team}`}
                onClick={() => {
                  setSelectedTeam(t);
                  setQuery(t.team);
                  setDropdownOpen(false);
                }}
                className="w-full text-left px-4 py-3 text-sm transition-colors border-b border-qbl-border last:border-0 hover:bg-[rgba(0,212,170,0.05)]"
              >
                <span className="text-text-primary font-medium">{t.team}</span>
                <span className="text-text-muted text-xs ml-2">
                  · {sportLabel(t.sport)} · {fmtGameTime(t.commence_time)}
                </span>
              </button>
            ))}
          </div>
        )}
        {dropdownOpen && !teamsLoading && filteredTeams.length === 0 && query.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-bg-surface border border-qbl-border rounded-[10px] shadow-2xl z-50 px-4 py-3 text-sm text-text-muted">
            No teams matching &ldquo;{query}&rdquo;
          </div>
        )}
      </div>

      {/* Results */}
      {selectedTeam && (
        <div className="bg-bg-surface border border-qbl-border rounded-[12px] overflow-hidden">
          {/* Game header */}
          <div className="px-6 py-4 border-b border-qbl-border bg-[rgba(0,212,170,0.03)]">
            <p className="font-display font-semibold text-text-primary">
              {teamA || selectedTeam.team}
              {teamB ? <span className="text-text-muted font-normal"> vs </span> : ""}
              {teamB}
            </p>
            <p className="text-text-secondary text-xs mt-0.5">
              {sportLabel(selectedTeam.sport)} · {fmtGameTime(selectedTeam.commence_time)}
            </p>
          </div>

          {gameLoading ? (
            <div className="px-6 py-10 text-center text-text-muted text-sm">Loading…</div>
          ) : gameRows.length === 0 ? (
            <div className="px-6 py-10 text-center text-text-muted text-sm">
              No data found for this game.
            </div>
          ) : (
            <div className="px-6 py-4 space-y-4">
              {colHeader}

              {/* Moneyline — maps over all outcomes so 3-way soccer markets show all 3 sides */}
              <div>
                <SectionHeader label="Moneyline" />
                {teamNames.map((name) => (
                  <OutcomeRow
                    key={name}
                    label={name}
                    row={getBestRow(h2hRows.filter((r) => r.team === name), selectedBooks)}
                  />
                ))}
              </div>

              {/* Spread */}
              {hasSpread && (
                <div>
                  <SectionHeader label="Spread" />
                  <OutcomeRow
                    label={mainSpreadA !== null ? `${teamA} ${mainSpreadA > 0 ? "+" : ""}${mainSpreadA}` : teamA}
                    row={bestSpread_A}
                  />
                  {teamB && (
                    <OutcomeRow
                      label={mainSpreadB !== null ? `${teamB} ${mainSpreadB > 0 ? "+" : ""}${mainSpreadB}` : teamB}
                      row={bestSpread_B}
                    />
                  )}
                </div>
              )}

              {/* Total */}
              {hasTotal && mainTotalVal !== null && (
                <div>
                  <SectionHeader label={`Total ${mainTotalVal}`} />
                  <OutcomeRow label="Over" row={bestOver} />
                  <OutcomeRow label="Under" row={bestUnder} />
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {!selectedTeam && !teamsLoading && teams.length === 0 && (
        <p className="text-text-muted text-sm">
          No games in current model data. Check back closer to game time.
        </p>
      )}
    </div>
  );
}

// ── Sportsbook Explorer ────────────────────────────────────────────────────

function SportsbookExplorer({ selectedBooks }: { selectedBooks: Set<string> }) {
  const [rows, setRows] = useState<RawRow[]>([]);
  const [loading, setLoading] = useState(false);
  const supabase = createClient();

  const fetchRows = useCallback(() => {
    if (selectedBooks.size === 0) { setRows([]); return; }
    setLoading(true);
    supabase
      .from("raw_model_output")
      .select("*")
      .in("book", dbBooks(selectedBooks))
      .gt("ev", 0)
      .order("ev", { ascending: false })
      .then(({ data }) => {
        setRows(data ?? []);
        setLoading(false);
      });
  }, [selectedBooks]);

  useEffect(() => { fetchRows(); }, [fetchRows]);

  if (selectedBooks.size === 0) {
    return (
      <p className="text-text-muted text-sm">Select at least one sportsbook above.</p>
    );
  }

  if (loading) {
    return (
      <div className="text-text-muted text-sm py-6">Loading…</div>
    );
  }

  if (rows.length === 0) {
    return (
      <p className="text-text-muted text-sm">
        No positive EV lines on selected books right now. Check back after the next model run.
      </p>
    );
  }

  return (
    <div className="bg-bg-surface border border-qbl-border rounded-[12px] overflow-hidden">
      {/* Table header */}
      <div className="grid grid-cols-[1fr_auto_auto_auto_auto] gap-4 px-5 py-3 border-b border-qbl-border">
        <span className="text-xs uppercase tracking-widest text-text-secondary">Side</span>
        <span className="text-xs uppercase tracking-widest text-text-secondary">Sport</span>
        <span className="text-xs uppercase tracking-widest text-text-secondary text-right">Book</span>
        <span className="text-xs uppercase tracking-widest text-text-secondary w-16 text-right">Odds</span>
        <span className="text-xs uppercase tracking-widest text-text-secondary w-16 text-right">EV</span>
      </div>

      {/* Rows */}
      <div className="divide-y divide-qbl-border">
        {rows.map((r) => (
          <div
            key={r.id}
            className="grid grid-cols-[1fr_auto_auto_auto_auto] gap-4 px-5 py-3.5 items-center hover:bg-[rgba(0,212,170,0.03)] transition-colors"
          >
            <div>
              <span className="text-text-primary text-sm font-medium">{formatSide(r)}</span>
            </div>
            <span className="text-text-secondary text-sm">{sportLabel(r.sport)}</span>
            <span className="text-text-secondary text-sm text-right">{bookLabel(r.book)}</span>
            <span className="font-display font-semibold text-sm text-text-primary w-16 text-right">
              {toAmerican(r.odds_from_best_book)}
            </span>
            <span className="font-display font-semibold text-sm text-accent w-16 text-right">
              {fmtEV(r.ev)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────

export default function ExploreTab() {
  const [mode, setMode] = useState<"team" | "sportsbook">("team");
  const [selectedBooks, setSelectedBooks] = useState<Set<string>>(
    new Set(BOOKS_CONFIG.map((b) => b.key))
  );
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [, setTick] = useState(0);
  const supabase = createClient();

  const fetchTimestamp = useCallback(() => {
    supabase
      .from("raw_model_output")
      .select("last_updated")
      .order("last_updated", { ascending: false })
      .limit(1)
      .single()
      .then(({ data }) => {
        if (data) setLastUpdated((data as { last_updated: string }).last_updated);
      });
  }, []);

  // Fetch timestamp on mount + subscribe to Realtime so new worker writes are caught
  useEffect(() => {
    fetchTimestamp();

    const channel = supabase
      .channel("raw_model_output_ts")
      .on("postgres_changes", { event: "INSERT", schema: "public", table: "raw_model_output" },
        () => fetchTimestamp()
      )
      .subscribe();

    // Tick every 60s so minutesAgo() stays accurate even without new data
    const timer = setInterval(() => setTick((t) => t + 1), 60_000);

    return () => {
      supabase.removeChannel(channel);
      clearInterval(timer);
    };
  }, [fetchTimestamp]);

  function toggleBook(key: string) {
    setSelectedBooks((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  }

  return (
    <div className="space-y-5">
      {/* Book chips */}
      <div className="bg-bg-surface border border-qbl-border rounded-[12px] px-5 py-4">
        <p className="text-xs font-display font-semibold uppercase tracking-[0.1em] text-text-secondary mb-3">
          My Sportsbooks
        </p>
        <BookChips
          selected={selectedBooks}
          onToggle={toggleBook}
          onAll={() => setSelectedBooks(new Set(BOOKS_CONFIG.map((b) => b.key)))}
          onClear={() => setSelectedBooks(new Set())}
        />
      </div>

      {/* Mode toggle */}
      <div className="flex items-center justify-between">
        <div className="flex bg-bg-surface border border-qbl-border rounded-[10px] p-1 gap-1">
          {(["team", "sportsbook"] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`font-display font-semibold text-base px-7 py-2.5 rounded-[7px] transition-all ${
                mode === m
                  ? "bg-accent text-bg-primary"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              {m === "team" ? "Team Search" : "Sportsbook Explorer"}
            </button>
          ))}
        </div>
        {lastUpdated && (
          <span className="text-[0.72rem] text-text-muted">
            Updated {minutesAgo(lastUpdated)}
          </span>
        )}
      </div>

      {/* Mode content */}
      {mode === "team"
        ? <TeamSearch selectedBooks={selectedBooks} />
        : <SportsbookExplorer selectedBooks={selectedBooks} />
      }
    </div>
  );
}
