"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";

type Pick = {
  id: string;
  sport: string;
  game_id: string;
  commence_time: string;
  team: string;
  market: string;
  point: number | null;
  book: string;
  odds_from_best_book: number;
  kelly: number;
  stars: number;
};

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
  if (market === "totals") {
    return point != null ? `Total ${point}` : "Total";
  }
  return market;
}

const BOOK_NAMES: Record<string, string> = {
  fanduel: "FanDuel",
  draftkings: "DraftKings",
  betmgm: "BetMGM",
  caesars: "Caesars",
  williamhill_us: "Caesars",
  betrivers: "BetRivers",
  unibet: "Unibet",
  ballybet: "Bally Bet",
  hardrockbet: "Hard Rock",
  espnbet: "ESPN Bet",
  betonlineag: "BetOnline",
  mybookieag: "MyBookie",
  bovada: "Bovada",
};

function formatBook(slug: string): string {
  return (
    BOOK_NAMES[slug] ??
    slug.charAt(0).toUpperCase() + slug.slice(1).replace(/_/g, " ")
  );
}

function formatGameTime(iso: string): string {
  return (
    new Date(iso).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
      timeZone: "America/New_York",
    }) + " ET"
  );
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
    sport === "baseball_mlb" ? "MLB" :
    sport === "basketball_nba" ? "NBA" :
    sport === "icehockey_nhl" ? "NHL" :
    sport === "americanfootball_nfl" ? "NFL" :
    sport === "soccer_epl" ? "EPL" :
    sport === "mma_mixed_martial_arts" ? "MMA" :
    sport === "boxing_boxing" ? "Boxing" :
    sport.split("_").pop()?.toUpperCase() ?? sport.toUpperCase();

  return (
    <span className="inline-block text-[0.65rem] font-display font-semibold tracking-[0.07em] px-1.5 py-0.5 rounded bg-[rgba(0,212,170,0.08)] text-accent border border-[rgba(0,212,170,0.18)]">
      {label}
    </span>
  );
}

// ── Component ───────────────────────────────────────────────────────────────

export default function PicksTable({ maxStars }: { maxStars: number }) {
  const [picks, setPicks] = useState<Pick[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRefetching, setIsRefetching] = useState(false);

  const supabase = useRef(createClient());
  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchPicks = useCallback(async (background = false) => {
    if (background) setIsRefetching(true);
    try {
      const { data, error: err } = await supabase.current
        .from("current_picks")
        .select(
          "id, sport, game_id, commence_time, team, market, point, book, odds_from_best_book, kelly, stars"
        )
        .lte("stars", maxStars)
        .order("stars", { ascending: false })
        .order("kelly", { ascending: false });

      if (err) throw err;
      setPicks(data ?? []);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load picks");
    } finally {
      setLoading(false);
      setIsRefetching(false);
    }
  }, [maxStars]);

  useEffect(() => {
    // Initial load
    fetchPicks();

    // Realtime subscription — listen for any INSERT / UPDATE / DELETE on current_picks.
    //
    // The Python worker does DELETE-ALL then batch INSERT. Reacting to each event
    // individually would flash an empty table between the two operations.
    // Debouncing 500ms after the LAST event means we wait until the full batch of
    // INSERTs has landed, then fetch once and swap atomically — no visible flicker.
    const channel = supabase.current
      .channel("current_picks_realtime")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "current_picks" },
        () => {
          if (debounceTimer.current) clearTimeout(debounceTimer.current);
          debounceTimer.current = setTimeout(() => fetchPicks(true), 500);
        }
      )
      .subscribe();

    return () => {
      if (debounceTimer.current) clearTimeout(debounceTimer.current);
      supabase.current.removeChannel(channel);
    };
  }, [fetchPicks]);

  // ── Loading ──────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="rounded-[12px] border border-qbl-border bg-bg-primary py-20 text-center">
        <div className="inline-block w-5 h-5 border-2 border-accent border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-text-muted text-sm">Loading picks…</p>
      </div>
    );
  }

  // ── Error ────────────────────────────────────────────────────────────────

  if (error) {
    return (
      <div className="rounded-[12px] border border-[rgba(239,68,68,0.3)] bg-bg-primary py-16 text-center">
        <p className="text-red-400 font-display font-semibold text-sm mb-2">
          Failed to load picks
        </p>
        <p className="text-text-muted text-xs max-w-[320px] mx-auto mb-5">{error}</p>
        <button
          onClick={() => {
            setLoading(true);
            fetchPicks();
          }}
          className="font-display font-semibold text-sm px-5 py-2 rounded-[8px] border border-qbl-border text-text-secondary hover:text-text-primary hover:border-[rgba(0,212,170,0.3)] transition-all"
        >
          Retry
        </button>
      </div>
    );
  }

  // ── Table ────────────────────────────────────────────────────────────────

  return (
    <div>
      {/* Live / updating indicator */}
      <div className="flex items-center justify-end mb-2 h-5">
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

      <div className="rounded-[12px] border border-qbl-border overflow-hidden">
        {/* Column header */}
        <div className="hidden md:grid grid-cols-[110px_1fr_136px_120px_88px_88px_1fr] gap-4 px-6 py-3 bg-bg-surface border-b border-qbl-border text-[0.7rem] font-display font-semibold text-text-muted uppercase tracking-[0.08em]">
          <span>Stars</span>
          <span>Team</span>
          <span>Market</span>
          <span>Book</span>
          <span>Odds</span>
          <span>Bet Size</span>
          <span>Game Time</span>
        </div>

        {picks.length === 0 ? (
          /* Empty state */
          <div className="py-20 text-center bg-bg-primary">
            <div className="text-4xl text-accent mb-4 opacity-50">◈</div>
            <h3 className="font-display text-xl font-semibold text-text-primary mb-2">
              No picks currently available
            </h3>
            <p className="text-text-secondary text-sm max-w-[340px] mx-auto leading-[1.6]">
              The model runs every 15 minutes. Check back soon — or join Discord for
              real-time alerts.
            </p>
          </div>
        ) : (
          /* Pick rows */
          <div className="divide-y divide-qbl-border bg-bg-primary">
            {picks.map((pick) => (
              <div
                key={pick.id}
                className="grid grid-cols-1 md:grid-cols-[110px_1fr_136px_120px_88px_88px_1fr] gap-y-1 gap-x-4 px-6 py-4 hover:bg-bg-surface transition-colors duration-150"
              >
                {/* Stars + sport badge (mobile: same row) */}
                <div className="flex items-center gap-2">
                  <Stars count={pick.stars} />
                  <span className="md:hidden">
                    <SportBadge sport={pick.sport} />
                  </span>
                </div>

                {/* Team + sport badge (desktop: badge next to team) */}
                <div className="flex items-center gap-2">
                  <span className="text-text-primary font-medium text-sm leading-snug">
                    {pick.team}
                  </span>
                  <span className="hidden md:inline">
                    <SportBadge sport={pick.sport} />
                  </span>
                </div>

                {/* Market */}
                <div className="flex items-center text-text-secondary text-sm">
                  {formatMarket(pick.market, pick.point)}
                </div>

                {/* Book */}
                <div className="flex items-center text-text-secondary text-sm">
                  {formatBook(pick.book)}
                </div>

                {/* Odds */}
                <div className="flex items-center font-display font-semibold text-sm text-text-primary">
                  {decimalToAmerican(pick.odds_from_best_book)}
                </div>

                {/* Bet Size */}
                <div className="flex items-center font-display font-semibold text-sm text-text-primary">
                  {(pick.kelly * 100).toFixed(1)}u
                </div>

                {/* Game time */}
                <div className="flex items-center text-text-muted text-xs">
                  {formatGameTime(pick.commence_time)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {picks.length > 0 && (
        <p className="text-text-muted text-[0.7rem] mt-3 text-center">
          {picks.length} pick{picks.length !== 1 ? "s" : ""} · Updates automatically when the model runs.
        </p>
      )}
    </div>
  );
}
