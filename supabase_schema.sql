-- Quant Bet Labs — Initial Supabase Schema
-- Run this in the Supabase SQL Editor (or via `supabase db push` once CLI is configured).
-- All tables use service-role writes from supabase_writer.py; RLS added in Phase 5.

-- ─────────────────────────────────────────
-- 1. model_runs
-- Tracks every run_once() execution in bet_scheduler7.py.
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS model_runs (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  started_at           timestamptz NOT NULL DEFAULT now(),
  finished_at          timestamptz,
  status               text NOT NULL DEFAULT 'running', -- 'running' | 'success' | 'error'
  active_sports        text,         -- e.g. 'BASEBALL,HOCKEY'
  latest_board_count   integer,      -- row count from run_edge_board()
  latest_output_count  integer,      -- row count from build_edge_output() after filters
  new_rows_count       integer,      -- new picks appended to bets_df this cycle
  to_send_count        integer,      -- Discord alerts queued this cycle
  error_message        text          -- NULL on success; exception string on error
);

CREATE INDEX IF NOT EXISTS model_runs_status_finished
  ON model_runs (status, finished_at DESC);


-- ─────────────────────────────────────────
-- 2. current_picks
-- Mirrors latest_output from build_edge_output().
-- Replaced each successful run: upsert all rows, then delete stale rows.
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS current_picks (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id              uuid REFERENCES model_runs(id),

  -- Exact latest_output columns (names match Python output exactly)
  sport               text NOT NULL,
  game_id             text NOT NULL,
  commence_time       timestamptz NOT NULL,
  team                text NOT NULL,
  market              text NOT NULL,           -- 'h2h' | 'spreads' | 'totals'
  point               double precision,        -- NULL for h2h markets
  book                text NOT NULL,           -- bookmaker slug e.g. 'fanduel'
  odds_from_best_book double precision NOT NULL,
  sharp_odds          double precision NOT NULL,
  ev                  double precision NOT NULL,
  kelly               double precision NOT NULL,
  clv_prob_med        double precision NOT NULL,
  stars               integer NOT NULL CHECK (stars BETWEEN 1 AND 5),
  outcome_threshold   double precision NOT NULL,

  -- Added by supabase_writer.py; used to identify and delete stale rows
  last_updated        timestamptz NOT NULL DEFAULT now()
);

-- Functional unique index handles NULL point (h2h rows) correctly.
-- COALESCE maps NaN/NULL → -9999.0 so two h2h rows with the same key
-- are treated as duplicates.  -9999.0 is outside any real spread/total range.
CREATE UNIQUE INDEX IF NOT EXISTS current_picks_upsert_key
  ON current_picks (game_id, team, market, COALESCE(point, -9999.0), book);

CREATE INDEX IF NOT EXISTS current_picks_stars        ON current_picks (stars);
CREATE INDEX IF NOT EXISTS current_picks_sport        ON current_picks (sport);
CREATE INDEX IF NOT EXISTS current_picks_commence     ON current_picks (commence_time);
CREATE INDEX IF NOT EXISTS current_picks_last_updated ON current_picks (last_updated);


-- ─────────────────────────────────────────
-- 3. tracked_picks
-- Mirrors bets.csv / bets_df.  One row per outcome (Option A dedup).
-- Upserted on each run; rows migrate to settled_picks when graded.
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tracked_picks (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Lifecycle columns
  found_at            timestamptz NOT NULL,
  posted              boolean NOT NULL DEFAULT false,
  tier                text,                    -- 'basic' | 'premium' | 'vip' | NULL

  -- Pick identity (from latest_output via bets_df)
  sport               text NOT NULL,
  game_id             text NOT NULL,
  commence_time       timestamptz NOT NULL,
  team                text NOT NULL,
  market              text NOT NULL,
  point               double precision,        -- NULL for h2h
  book                text NOT NULL,           -- best-EV book (Option A)
  odds_from_best_book double precision NOT NULL,
  sharp_odds          double precision NOT NULL,
  ev                  double precision NOT NULL,
  kelly               double precision NOT NULL,
  clv_prob_med        double precision NOT NULL,
  stars               integer NOT NULL CHECK (stars BETWEEN 1 AND 5),
  outcome_threshold   double precision NOT NULL,

  -- Filled by update_closing_lines() in bet_scheduler7.py
  closing_line        double precision,        -- NULL until game closes
  clv                 double precision         -- NULL until game closes
);

CREATE UNIQUE INDEX IF NOT EXISTS tracked_picks_upsert_key
  ON tracked_picks (game_id, team, market, COALESCE(point, -9999.0));

CREATE INDEX IF NOT EXISTS tracked_picks_game_id  ON tracked_picks (game_id);
CREATE INDEX IF NOT EXISTS tracked_picks_found_at ON tracked_picks (found_at);
CREATE INDEX IF NOT EXISTS tracked_picks_stars    ON tracked_picks (stars);


-- ─────────────────────────────────────────
-- 4. settled_picks
-- Mirrors ledger.csv.  Append-only; never deleted.
-- Rows migrate here from tracked_picks when settle_ledger.py runs.
-- Python column "W/L" is renamed to "result" (slash invalid in SQL identifiers).
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS settled_picks (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Lifecycle columns
  found_at            timestamptz NOT NULL,
  settled_at          timestamptz NOT NULL DEFAULT now(),
  posted              boolean NOT NULL DEFAULT false,
  tier                text,

  -- Pick identity (same columns as tracked_picks)
  sport               text NOT NULL,
  game_id             text NOT NULL,
  commence_time       timestamptz NOT NULL,
  team                text NOT NULL,
  market              text NOT NULL,
  point               double precision,
  book                text NOT NULL,
  odds_from_best_book double precision NOT NULL,
  sharp_odds          double precision NOT NULL,
  ev                  double precision NOT NULL,
  kelly               double precision NOT NULL,
  clv_prob_med        double precision NOT NULL,
  stars               integer NOT NULL CHECK (stars BETWEEN 1 AND 5),
  outcome_threshold   double precision NOT NULL,

  -- Closing / CLV (always filled by settlement time)
  closing_line        double precision,
  clv                 double precision,

  -- Settlement grade — Python's "W/L" column renamed here
  result              text CHECK (result IN ('W', 'L', 'P', ''))
                      -- 'W'=win, 'L'=loss, 'P'=push, ''=ungradeable
);

-- Dedup key matches settle_ledger.py build_row_key() logic
CREATE UNIQUE INDEX IF NOT EXISTS settled_picks_dedup
  ON settled_picks (game_id, market, team);

CREATE INDEX IF NOT EXISTS settled_picks_sport      ON settled_picks (sport);
CREATE INDEX IF NOT EXISTS settled_picks_settled_at ON settled_picks (settled_at);
CREATE INDEX IF NOT EXISTS settled_picks_stars      ON settled_picks (stars);
CREATE INDEX IF NOT EXISTS settled_picks_result     ON settled_picks (result);
