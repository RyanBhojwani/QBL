"use client";

import { useEffect, useState, useRef, useCallback, type ReactNode } from "react";
import { createClient } from "@/lib/supabase/client";

// ── Types ──────────────────────────────────────────────────────────────────

type Pick = {
  id: string; sport: string; game_id: string; commence_time: string;
  team: string; market: string; point: number | null; book: string;
  odds_from_best_book: number; kelly: number; stars: number;
};

// ── Sport / Book config ────────────────────────────────────────────────────

const SPORTS = [
  { key: "americanfootball_nfl",   label: "NFL"    },
  { key: "americanfootball_ncaaf", label: "NCAAF"  },
  { key: "baseball_mlb",           label: "MLB"    },
  { key: "basketball_nba",         label: "NBA"    },
  { key: "basketball_ncaab",       label: "NCAAB"  },
  { key: "icehockey_nhl",          label: "NHL"    },
  { key: "mma_mixed_martial_arts", label: "MMA"    },
  { key: "boxing_boxing",          label: "Boxing" },
  { key: "tennis",                 label: "Tennis" },
  { key: "soccer",                 label: "Soccer" },
];

const BOOKS_CONFIG = [
  { key: "betmgm",      label: "BetMGM"        },
  { key: "betrivers",   label: "BetRivers"     },
  { key: "caesars",     label: "Caesars"       },
  { key: "draftkings",  label: "DraftKings"    },
  { key: "fanatics",    label: "Fanatics"      },
  { key: "fanduel",     label: "FanDuel"       },
  { key: "ballybet",    label: "Bally Bet"     },
  { key: "thescorebet", label: "theScore Bet"  },
  { key: "hardrockbet", label: "Hard Rock Bet" },
  { key: "kalshi",      label: "Kalshi"        },
  { key: "polymarket",  label: "Polymarket"    },
];

function sportMatchesPick(sportKey: string, pickSport: string): boolean {
  if (sportKey === "soccer")       return pickSport.startsWith("soccer");
  if (sportKey === "tennis")       return pickSport.startsWith("tennis");
  if (sportKey === "baseball_mlb") return pickSport.startsWith("baseball");
  return pickSport === sportKey;
}

function bookMatchesPick(bookKey: string, pickBook: string): boolean {
  if (bookKey === "caesars") return pickBook === "caesars" || pickBook === "williamhill_us";
  return pickBook === bookKey;
}

function pickPassesSportFilter(pick: Pick, selected: Set<string>): boolean {
  if (selected.size === SPORTS.length) return true;
  return SPORTS.some(s => selected.has(s.key) && sportMatchesPick(s.key, pick.sport));
}

function pickPassesBookFilter(pick: Pick, selected: Set<string>): boolean {
  if (selected.size === BOOKS_CONFIG.length) return true;
  const isKnown = BOOKS_CONFIG.some(b => bookMatchesPick(b.key, pick.book));
  if (!isKnown) return true; // unknown book always shown
  return BOOKS_CONFIG.some(b => selected.has(b.key) && bookMatchesPick(b.key, pick.book));
}

// ── Helpers ────────────────────────────────────────────────────────────────

function decimalToAmerican(d: number): string {
  if (d >= 2.0) return `+${Math.round((d - 1) * 100)}`;
  return `${Math.round(-100 / (d - 1))}`;
}

function formatMarket(market: string, point: number | null): string {
  if (market === "h2h") return "Moneyline";
  if (market === "spreads") {
    if (point == null) return "Spread";
    return `Spread ${point > 0 ? "+" : ""}${point}`;
  }
  if (market === "totals") return point != null ? `Total ${point}` : "Total";
  return market;
}

const BOOK_NAMES: Record<string, string> = {
  fanduel: "FanDuel", draftkings: "DraftKings", betmgm: "BetMGM",
  caesars: "Caesars", williamhill_us: "Caesars", betrivers: "BetRivers",
  ballybet: "Bally Bet", hardrockbet: "Hard Rock Bet", fanatics: "Fanatics",
  thescorebet: "theScore Bet", kalshi: "Kalshi", polymarket: "Polymarket",
};

function formatBook(slug: string): string {
  return BOOK_NAMES[slug] ?? slug.charAt(0).toUpperCase() + slug.slice(1).replace(/_/g, " ");
}

function formatGameTime(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    month: "short", day: "numeric", hour: "numeric", minute: "2-digit",
    timeZone: "America/New_York",
  }) + " ET";
}

function Stars({ count }: { count: number }) {
  const filled = Math.min(Math.max(count, 0), 5);
  return (
    <span className="text-xl font-bold tracking-tight leading-none">
      <span className="text-amber">{"★".repeat(filled)}</span>
      <span className="text-text-muted opacity-20">{"★".repeat(5 - filled)}</span>
    </span>
  );
}

function SportBadge({ sport }: { sport: string }) {
  const label =
    sport === "baseball_mlb"           ? "MLB"    :
    sport === "basketball_nba"         ? "NBA"    :
    sport === "icehockey_nhl"          ? "NHL"    :
    sport === "americanfootball_nfl"   ? "NFL"    :
    sport === "americanfootball_ncaaf" ? "NCAAF"  :
    sport === "mma_mixed_martial_arts" ? "MMA"    :
    sport === "boxing_boxing"          ? "Boxing" :
    sport.startsWith("soccer_")        ? "Soccer" :
    sport.startsWith("tennis_")        ? "Tennis" :
    sport.split("_").pop()?.toUpperCase() ?? sport.toUpperCase();
  return (
    <span className="inline-block text-[0.65rem] font-display font-semibold tracking-[0.07em] px-1.5 py-0.5 rounded bg-[rgba(0,212,170,0.08)] text-accent border border-[rgba(0,212,170,0.18)]">
      {label}
    </span>
  );
}

// ── CheckboxItem ───────────────────────────────────────────────────────────

function CheckboxItem({ checked, onChange, label }: {
  checked: boolean; onChange: () => void; label: string;
}) {
  return (
    <label className="flex items-center gap-2.5 cursor-pointer group select-none">
      <div className={`w-4 h-4 rounded border flex items-center justify-center transition-all flex-shrink-0 ${
        checked
          ? "bg-accent border-accent"
          : "border-[rgba(255,255,255,0.2)] bg-transparent group-hover:border-[rgba(0,212,170,0.4)]"
      }`}>
        {checked && (
          <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
            <path d="M1 4L3.5 6.5L9 1" stroke="#060912" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        )}
      </div>
      <span className="text-sm text-text-secondary group-hover:text-text-primary transition-colors">{label}</span>
    </label>
  );
}

// ── FilterDropdown (generic pill button + dropdown shell) ──────────────────

function FilterDropdown({ label, active, open, onToggle, children }: {
  label: string; active: boolean; open: boolean; onToggle: () => void; children: ReactNode;
}) {
  return (
    <div className="relative">
      <button
        onClick={onToggle}
        className={`flex items-center gap-1.5 font-display text-sm px-4 py-2 rounded-[8px] border transition-all ${
          active
            ? "bg-[rgba(0,212,170,0.1)] border-accent text-accent"
            : "bg-bg-surface border-qbl-border text-text-secondary hover:text-text-primary hover:border-[rgba(255,255,255,0.2)]"
        }`}
      >
        {label}
        <svg
          width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
          className={`transition-transform duration-150 ${open ? "rotate-180" : ""}`}
        >
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>
      {open && (
        <div className="absolute left-0 top-[calc(100%+6px)] z-50 bg-bg-surface border border-qbl-border rounded-[12px] shadow-xl p-4 min-w-[220px]">
          {children}
        </div>
      )}
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────

export default function PicksTable({ maxStars: tierMax }: { maxStars: number }) {
  const [picks, setPicks]           = useState<Pick[]>([]);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState<string | null>(null);
  const [isRefetching, setIsRefetching] = useState(false);

  // Filter state
  const [openDropdown, setOpenDropdown] = useState<"sports" | "books" | "stars" | null>(null);
  const [selectedSports, setSelectedSports] = useState<Set<string>>(new Set(SPORTS.map(s => s.key)));
  const [selectedBooks,  setSelectedBooks]  = useState<Set<string>>(new Set(BOOKS_CONFIG.map(b => b.key)));
  const [starsLo, setStarsLo] = useState(1);
  const [starsHi, setStarsHi] = useState(tierMax);
  const filterBarRef = useRef<HTMLDivElement>(null);

  const supabase      = useRef(createClient());
  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const saveTimer     = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Close dropdowns when clicking outside the filter bar
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (filterBarRef.current && !filterBarRef.current.contains(e.target as Node)) {
        setOpenDropdown(null);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  // ── Load preferences on mount ─────────────────────────────────────────────

  useEffect(() => {
    fetch("/api/preferences")
      .then(r => r.ok ? r.json() : {})
      .then((prefs: Record<string, unknown>) => {
        if (Array.isArray(prefs.sports) && prefs.sports.length > 0)
          setSelectedSports(new Set(prefs.sports as string[]));
        if (Array.isArray(prefs.books) && prefs.books.length > 0)
          setSelectedBooks(new Set(prefs.books as string[]));
        if (typeof prefs.min_stars === "number") setStarsLo(prefs.min_stars);
        if (typeof prefs.max_stars === "number") setStarsHi(Math.min(prefs.max_stars as number, tierMax));
      })
      .catch(() => {});
  }, [tierMax]);

  // ── Save preferences (debounced 600ms) ───────────────────────────────────

  const savePreferences = useCallback((
    sports: Set<string>, books: Set<string>, lo: number, hi: number
  ) => {
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      fetch("/api/preferences", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sports:    sports.size === SPORTS.length       ? [] : [...sports],
          books:     books.size  === BOOKS_CONFIG.length ? [] : [...books],
          min_stars: lo,
          max_stars: hi,
        }),
      }).catch(() => {});
    }, 600);
  }, []);

  // ── Filter actions ────────────────────────────────────────────────────────

  function toggleSport(key: string) {
    setSelectedSports(prev => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      savePreferences(next, selectedBooks, starsLo, starsHi);
      return next;
    });
  }

  function toggleBook(key: string) {
    setSelectedBooks(prev => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      savePreferences(selectedSports, next, starsLo, starsHi);
      return next;
    });
  }

  function toggleAllSports() {
    const next = selectedSports.size === SPORTS.length
      ? new Set<string>()
      : new Set(SPORTS.map(s => s.key));
    setSelectedSports(next);
    savePreferences(next, selectedBooks, starsLo, starsHi);
  }

  function toggleAllBooks() {
    const next = selectedBooks.size === BOOKS_CONFIG.length
      ? new Set<string>()
      : new Set(BOOKS_CONFIG.map(b => b.key));
    setSelectedBooks(next);
    savePreferences(selectedSports, next, starsLo, starsHi);
  }

  function changeStars(lo: number, hi: number) {
    setStarsLo(lo);
    setStarsHi(hi);
    savePreferences(selectedSports, selectedBooks, lo, hi);
  }

  function resetFilters() {
    const sports = new Set(SPORTS.map(s => s.key));
    const books  = new Set(BOOKS_CONFIG.map(b => b.key));
    setSelectedSports(sports);
    setSelectedBooks(books);
    setStarsLo(1);
    setStarsHi(tierMax);
    savePreferences(sports, books, 1, tierMax);
  }

  // ── Active filter flags ───────────────────────────────────────────────────

  const sportFiltered = selectedSports.size < SPORTS.length;
  const bookFiltered  = selectedBooks.size  < BOOKS_CONFIG.length;
  const starsFiltered = starsLo > 1 || starsHi < tierMax;
  const anyFiltered   = sportFiltered || bookFiltered || starsFiltered;

  // ── Star slider helpers ───────────────────────────────────────────────────

  const trackPct = (v: number) =>
    tierMax === 1 ? 100 : ((v - 1) / (tierMax - 1)) * 100;

  // ── Fetch picks ───────────────────────────────────────────────────────────

  const fetchPicks = useCallback(async (background = false) => {
    if (background) setIsRefetching(true);
    try {
      const { data, error: err } = await supabase.current
        .from("current_picks")
        .select("id, sport, game_id, commence_time, team, market, point, book, odds_from_best_book, kelly, stars")
        .lte("stars", tierMax)
        .order("stars",  { ascending: false })
        .order("kelly",  { ascending: false });
      if (err) throw err;
      setPicks(data ?? []);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load picks");
    } finally {
      setLoading(false);
      setIsRefetching(false);
    }
  }, [tierMax]);

  useEffect(() => {
    fetchPicks();
    const channel = supabase.current
      .channel("current_picks_realtime")
      .on("postgres_changes", { event: "*", schema: "public", table: "current_picks" }, () => {
        if (debounceTimer.current) clearTimeout(debounceTimer.current);
        debounceTimer.current = setTimeout(() => fetchPicks(true), 500);
      })
      .subscribe();
    return () => {
      if (debounceTimer.current) clearTimeout(debounceTimer.current);
      supabase.current.removeChannel(channel);
    };
  }, [fetchPicks]);

  // ── Apply client-side filters ─────────────────────────────────────────────

  const filteredPicks = picks.filter(p =>
    p.stars >= starsLo &&
    p.stars <= starsHi &&
    pickPassesSportFilter(p, selectedSports) &&
    pickPassesBookFilter(p, selectedBooks)
  );

  // ── Loading ───────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="rounded-[12px] border border-qbl-border bg-bg-primary py-20 text-center">
        <div className="inline-block w-5 h-5 border-2 border-accent border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-text-muted text-sm">Loading picks…</p>
      </div>
    );
  }

  // ── Error ─────────────────────────────────────────────────────────────────

  if (error) {
    return (
      <div className="rounded-[12px] border border-[rgba(239,68,68,0.3)] bg-bg-primary py-16 text-center">
        <p className="text-red-400 font-display font-semibold text-sm mb-2">Failed to load picks</p>
        <p className="text-text-muted text-xs max-w-[320px] mx-auto mb-5">{error}</p>
        <button
          onClick={() => { setLoading(true); fetchPicks(); }}
          className="font-display font-semibold text-sm px-5 py-2 rounded-[8px] border border-qbl-border text-text-secondary hover:text-text-primary hover:border-[rgba(0,212,170,0.3)] transition-all"
        >
          Retry
        </button>
      </div>
    );
  }

  // ── Table ─────────────────────────────────────────────────────────────────

  return (
    <div>
      {/* Filter bar */}
      <div ref={filterBarRef} className="flex items-center gap-2 flex-wrap mb-4">

        {/* Sports dropdown */}
        <FilterDropdown
          label={sportFiltered ? `Sport (${selectedSports.size})` : "All Sports"}
          active={sportFiltered}
          open={openDropdown === "sports"}
          onToggle={() => setOpenDropdown(o => o === "sports" ? null : "sports")}
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-[0.65rem] font-display font-semibold text-text-muted uppercase tracking-[0.08em]">Sport</span>
            <button onClick={toggleAllSports} className="text-xs font-display text-text-muted hover:text-accent transition-colors">
              {selectedSports.size === SPORTS.length ? "Deselect All" : "Select All"}
            </button>
          </div>
          <div className="grid grid-cols-2 gap-y-2 gap-x-4">
            {SPORTS.map(s => (
              <CheckboxItem key={s.key} checked={selectedSports.has(s.key)} onChange={() => toggleSport(s.key)} label={s.label} />
            ))}
          </div>
        </FilterDropdown>

        {/* Books dropdown */}
        <FilterDropdown
          label={bookFiltered ? `Book (${selectedBooks.size})` : "All Books"}
          active={bookFiltered}
          open={openDropdown === "books"}
          onToggle={() => setOpenDropdown(o => o === "books" ? null : "books")}
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-[0.65rem] font-display font-semibold text-text-muted uppercase tracking-[0.08em]">Book</span>
            <button onClick={toggleAllBooks} className="text-xs font-display text-text-muted hover:text-accent transition-colors">
              {selectedBooks.size === BOOKS_CONFIG.length ? "Deselect All" : "Select All"}
            </button>
          </div>
          <div className="grid grid-cols-2 gap-y-2 gap-x-4">
            {BOOKS_CONFIG.map(b => (
              <CheckboxItem key={b.key} checked={selectedBooks.has(b.key)} onChange={() => toggleBook(b.key)} label={b.label} />
            ))}
          </div>
        </FilterDropdown>

        {/* Stars dropdown */}
        <FilterDropdown
          label={starsFiltered ? `Stars (${starsLo}★–${starsHi}★)` : "All Stars"}
          active={starsFiltered}
          open={openDropdown === "stars"}
          onToggle={() => setOpenDropdown(o => o === "stars" ? null : "stars")}
        >
          <div className="mb-2 flex items-center justify-between">
            <span className="text-[0.65rem] font-display font-semibold text-text-muted uppercase tracking-[0.08em]">Star Range</span>
            <span className="text-xs font-display font-semibold text-accent">
              {starsLo === starsHi ? `${starsLo}★` : `${starsLo}★ – ${starsHi}★`}
            </span>
          </div>
          <div className="space-y-2.5 mb-3">
            <div className="flex items-center gap-3">
              <span className="text-xs text-text-muted w-8 shrink-0">Min</span>
              <input
                type="range" min={1} max={tierMax} step={1} value={starsLo}
                onChange={e => changeStars(Math.min(Number(e.target.value), starsHi), starsHi)}
                className="flex-1 h-1.5 rounded-full appearance-none cursor-pointer accent-[#00d4aa]"
                style={{ background: `linear-gradient(to right, #00d4aa 0% ${trackPct(starsLo)}%, rgba(255,255,255,0.12) ${trackPct(starsLo)}% 100%)` }}
              />
              <span className="text-xs font-display font-semibold text-accent w-4 text-right shrink-0">{starsLo}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-text-muted w-8 shrink-0">Max</span>
              <input
                type="range" min={1} max={tierMax} step={1} value={starsHi}
                onChange={e => changeStars(starsLo, Math.max(Number(e.target.value), starsLo))}
                className="flex-1 h-1.5 rounded-full appearance-none cursor-pointer accent-[#00d4aa]"
                style={{ background: `linear-gradient(to right, #00d4aa 0% ${trackPct(starsHi)}%, rgba(255,255,255,0.12) ${trackPct(starsHi)}% 100%)` }}
              />
              <span className="text-xs font-display font-semibold text-accent w-4 text-right shrink-0">{starsHi}</span>
            </div>
          </div>
          <div className="flex gap-1 px-11">
            {Array.from({ length: tierMax }, (_, i) => i + 1).map(star => (
              <div key={star} className={`flex-1 h-1 rounded-full transition-colors ${star >= starsLo && star <= starsHi ? "bg-accent" : "bg-[rgba(255,255,255,0.1)]"}`} />
            ))}
          </div>
        </FilterDropdown>

        {/* Reset — only shown when any filter is active */}
        {anyFiltered && (
          <button
            onClick={resetFilters}
            className="font-display text-xs text-text-muted hover:text-accent transition-colors px-2 py-2"
          >
            Reset
          </button>
        )}

        {/* Live indicator pushed to the right */}
        <div className="ml-auto h-5 flex items-center">
          {isRefetching ? (
            <span className="flex items-center gap-1.5 text-[0.7rem] text-text-muted">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-amber animate-pulse" />
              Updating…
            </span>
          ) : (
            <span className="flex items-center gap-1.5 text-[0.7rem] text-text-muted">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-accent" />
              Live
            </span>
          )}
        </div>
      </div>

      {/* Picks table */}
      <div className="rounded-[12px] border border-qbl-border overflow-hidden">
        <div className="hidden md:grid grid-cols-[110px_1fr_136px_120px_88px_88px_1fr] gap-4 px-6 py-3 bg-bg-surface border-b border-qbl-border text-[0.7rem] font-display font-semibold text-text-muted uppercase tracking-[0.08em]">
          <span>Stars</span>
          <span>Team</span>
          <span>Market</span>
          <span>Book</span>
          <span>Odds</span>
          <span>Bet Size</span>
          <span>Game Time</span>
        </div>

        {filteredPicks.length === 0 ? (
          <div className="py-20 text-center bg-bg-primary">
            <div className="text-4xl text-accent mb-4 opacity-50">◈</div>
            <h3 className="font-display text-xl font-semibold text-text-primary mb-2">
              {picks.length === 0 ? "No picks currently available" : "No picks match your filters"}
            </h3>
            <p className="text-text-secondary text-sm max-w-[340px] mx-auto leading-[1.6]">
              {picks.length === 0
                ? "The model runs every 15 minutes. Check back soon — or join Discord for real-time alerts."
                : "Try adjusting your sport, book, or star filters."}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-qbl-border bg-bg-primary">
            {filteredPicks.map((pick) => (
              <div
                key={pick.id}
                className="grid grid-cols-1 md:grid-cols-[110px_1fr_136px_120px_88px_88px_1fr] gap-y-1 gap-x-4 px-6 py-4 hover:bg-bg-surface transition-colors duration-150"
              >
                <div className="flex items-center gap-2">
                  <Stars count={pick.stars} />
                  <span className="md:hidden"><SportBadge sport={pick.sport} /></span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-text-primary font-medium text-sm leading-snug">{pick.team}</span>
                  <span className="hidden md:inline"><SportBadge sport={pick.sport} /></span>
                </div>
                <div className="flex items-center text-text-secondary text-sm">
                  {formatMarket(pick.market, pick.point)}
                </div>
                <div className="flex items-center text-text-secondary text-sm">
                  {formatBook(pick.book)}
                </div>
                <div className="flex items-center font-display font-semibold text-sm text-text-primary">
                  {decimalToAmerican(pick.odds_from_best_book)}
                </div>
                <div className="flex items-center font-display font-semibold text-sm text-text-primary">
                  {(pick.kelly * 100).toFixed(1)}u
                </div>
                <div className="flex items-center text-text-muted text-xs">
                  {formatGameTime(pick.commence_time)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <p className="text-text-muted text-[0.7rem] mt-3 text-center">
        {filteredPicks.length} of {picks.length} pick{picks.length !== 1 ? "s" : ""}
        {activeFilterCount > 0 ? " (filtered)" : ""} · Updates automatically when the model runs.
      </p>
    </div>
  );
}
