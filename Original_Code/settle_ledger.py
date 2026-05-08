#!/usr/bin/env python3
"""
Settle Ledger Script (No argparse) — The Odds API v4 /scores
------------------------------------------------------------
CHANGES REQUESTED:
- Do NOT add a 'commence_time_utc' column to ledger/unsettled.
- After moving bets from bets.csv to ledger, delete those moved bets from bets.csv.

What it does:
- Define your API key, bets/ledger paths, and options below.
- Appends past bets -> ledger (de-dup).
- Removes those moved bets from bets.csv.
- Polls /scores only for unsettled games in ledger (by sport, using eventIds).
- Uses daysFrom (auto up to 3) so completed scores are included.
- Settles W/L/P for h2h, spreads, totals, and soccer 3-way (Draw).

CREDIT COST:
- With daysFrom: 2 credits per /scores call (per sport, regardless of eventIds count).
- Without daysFrom: 1 credit (but no completed scores). We use daysFrom when needed.
"""

import math
import os
from datetime import datetime, timezone
from typing import Optional, Iterable, Dict, Any, List, Tuple

import numpy as np
import pandas as pd
import requests

# Load secrets.env so SUPABASE_* vars are available when run standalone
import pathlib as _pathlib
def _load_env(path: str) -> None:
    p = _pathlib.Path(path)
    if not p.exists():
        return
    for raw in p.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
_load_env("secrets.env")

import supabase_writer as sb  # noqa: E402

# ----------------- USER SETTINGS -----------------
API_KEY: str = os.getenv("ODDS_API_KEY", "")
BETS_PATH: str = "bets.csv"
LEDGER_PATH: str = "ledger.csv"

# Write ledger back to CSV when done?
WRITE_BACK: bool = True

# Also write bets.csv after REMOVING bets that were moved to ledger
DELETE_MOVED_BETS: bool = True

# Force a specific daysFrom (1..3)? Set to None to auto-compute from data.
MAX_DAYS_FROM: Optional[int] = None
# -------------------------------------------------

ODDS_API_BASE = "https://api.the-odds-api.com/v4"

def to_utc_ts(x):
    if pd.isna(x):
        return None
    try:
        return pd.to_datetime(x, utc=True, errors="coerce")
    except Exception:
        return None

def build_row_key(df: pd.DataFrame) -> pd.Series:
    cols = ["game_id", "sport", "market", "team", "point", "book", "odds_from_best_book"]
    present = [c for c in cols if c in df.columns]
    if not present:
        return pd.Series([""], index=df.index, dtype=str)
    return df[present].astype(str).agg("|".join, axis=1)

def select_past_bets(bets: pd.DataFrame, now_utc: pd.Timestamp) -> pd.DataFrame:
    if "commence_time" not in bets.columns:
        raise ValueError("bets.csv must include 'commence_time'")
    # Compute as a temporary series instead of creating a column
    ct_utc = bets["commence_time"].apply(to_utc_ts)
    eligible = bets[~ct_utc.isna() & (ct_utc <= now_utc)].copy()
    return eligible

def append_past_bets_to_ledger(
    bets: pd.DataFrame,
    ledger: pd.DataFrame,
    now_utc: pd.Timestamp
) -> Tuple[pd.DataFrame, pd.Index]:
    """
    Returns: (updated_ledger, moved_bet_index)
    moved_bet_index are the index labels from 'bets' that were appended to ledger.
    """
    eligible = select_past_bets(bets, now_utc)

    bets_key = build_row_key(eligible)
    ledger_key = build_row_key(ledger) if len(ledger) else pd.Series(dtype=str)

    new_mask = ~bets_key.isin(set(ledger_key.values))
    to_append = eligible.loc[new_mask].copy()
    moved_idx = to_append.index  # remember which rows to remove from bets

    if "W/L" not in ledger.columns:
        ledger["W/L"] = ""

    # Ensure ledger has any new columns so concat aligns
    missing_cols = [c for c in to_append.columns if c not in ledger.columns]
    for c in missing_cols:
        ledger[c] = np.nan

    # Align order to ledger columns
    aligned_cols = list(ledger.columns)
    updated_ledger = pd.concat([ledger, to_append.reindex(columns=aligned_cols)], ignore_index=True)
    return updated_ledger, moved_idx

def compute_days_from_for_subset(commence_series: pd.Series, now_utc: pd.Timestamp) -> Optional[int]:
    """
    Compute minimal daysFrom (1..3) based on a commence_time series (UTC parsed),
    without adding temporary columns to the DataFrame.
    """
    times = commence_series.apply(to_utc_ts)
    past = times[~times.isna() & (times <= now_utc)]
    if past.empty:
        return None
    max_age_days = (now_utc - past.min()).total_seconds() / 86400.0
    needed = math.ceil(max_age_days)
    return max(1, min(3, needed))

def fetch_scores(api_key: str, sport: str, event_ids: Iterable[str], days_from: Optional[int], date_format: str = "iso", timeout: int = 20):
    params = {"apiKey": api_key, "dateFormat": date_format}
    ev_ids = list(dict.fromkeys(str(e) for e in event_ids))  # unique & preserve order
    if ev_ids:
        params["eventIds"] = ",".join(ev_ids)
    if days_from is not None:
        params["daysFrom"] = int(days_from)

    url = f"{ODDS_API_BASE}/sports/{sport}/scores"
    r = requests.get(url, params=params, timeout=timeout)
    quota = {
        "remaining": r.headers.get("x-requests-remaining"),
        "used": r.headers.get("x-requests-used"),
        "last": r.headers.get("x-requests-last"),
    }
    r.raise_for_status()
    return r.json(), quota

def parse_scores_into_frame(scores_data: List[Dict[str, Any]]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for ev in scores_data:
        home = ev.get("home_team")
        away = ev.get("away_team")
        scores = ev.get("scores") or []
        name_to_score: Dict[str, int] = {}
        for s in scores:
            try:
                name_to_score[s["name"]] = int(s["score"])
            except Exception:
                pass
        home_score = name_to_score.get(home)
        away_score = name_to_score.get(away)

        margin = None
        total_points = None
        if home_score is not None and away_score is not None:
            margin = home_score - away_score
            total_points = home_score + away_score

        rows.append({
            "id": ev.get("id"),
            "sport_key": ev.get("sport_key"),
            "home_team": home,
            "away_team": away,
            "completed": bool(ev.get("completed")),
            "home_score": home_score,
            "away_score": away_score,
            "margin": margin,
            "total_points": total_points,
            "last_update": ev.get("last_update"),
        })
    return pd.DataFrame(rows)

def is_soccer_three_way(sport_key: str) -> bool:
    return isinstance(sport_key, str) and sport_key.lower().startswith("soccer_")

def settle_row(row: pd.Series, ev_map: Dict[str, Dict[str, Any]]) -> str:
    wl = str(row.get("W/L", "") or "").strip()
    if wl in {"W", "L", "P"}:
        return wl

    game_id = row.get("game_id")
    sport   = row.get("sport")
    market  = str(row.get("market", "")).strip().lower()
    team    = str(row.get("team", ""))
    point   = row.get("point")

    ev = ev_map.get(game_id)
    if ev is None:
        return ""

    if not bool(ev.get("completed")):
        return ""

    home = ev.get("home_team")
    away = ev.get("away_team")
    home_score = ev.get("home_score")
    away_score = ev.get("away_score")
    margin = ev.get("margin")
    total_points = ev.get("total_points")

    def norm(s):
        return "" if s is None else str(s).strip().lower()

    team_norm = norm(team)
    is_over  = team_norm.startswith("over")
    is_under = team_norm.startswith("under")
    is_draw  = team_norm.startswith("draw")

    def eq(a, b): return norm(a) == norm(b)

    if market == "h2h":
        if home_score is None or away_score is None:
            return ""
        if is_soccer_three_way(sport):
            if is_draw:
                return "W" if home_score == away_score else "L"
            if home_score == away_score:
                return "L"
            winner_team = home if home_score > away_score else away
            return "W" if eq(team, winner_team) else "L"
        else:
            if home_score == away_score:
                return "P"
            winner_team = home if home_score > away_score else away
            return "W" if eq(team, winner_team) else "L"

    elif market == "spreads":
        if margin is None or pd.isna(point):
            return ""
        if eq(team, home):
            team_margin = margin
        elif eq(team, away):
            team_margin = -margin
        else:
            return ""
        net = float(team_margin) + float(point)
        if abs(net) < 1e-9:
            return "P"
        return "W" if net > 0 else "L"

    elif market == "totals":
        if total_points is None or pd.isna(point):
            return ""
        if not (is_over or is_under):
            return ""
        diff = float(total_points) - float(point)
        if abs(diff) < 1e-9:
            return "P"
        if is_over:
            return "W" if diff > 0 else "L"
        else:
            return "W" if diff < 0 else "L"

    else:
        return ""

def main():
    if not API_KEY:
        raise RuntimeError("Missing ODDS_API_KEY")

    now_utc = pd.Timestamp.now(tz="UTC")

    # ── Primary path: read unsettled picks from Supabase tracked_picks ──────
    # Returns None when SUPABASE_ENABLED=0 → fall back to CSVs.
    # Returns empty DataFrame when enabled but no picks to settle.
    sb_rows = sb.load_unsettled_picks(now_utc)

    if sb_rows is not None:
        if sb_rows.empty:
            print("No unsettled picks in tracked_picks. Nothing to settle.")
            return
        ledger_updated = sb_rows.copy()
        unsettled_mask = ~ledger_updated["W/L"].astype(str).isin(["W", "L", "P"])
        unsettled = ledger_updated.loc[unsettled_mask].copy()

    else:
        # ── CSV fallback (SUPABASE_ENABLED=0) ───────────────────────────────
        bets   = pd.read_csv(BETS_PATH)
        ledger = pd.read_csv(LEDGER_PATH)

        if "W/L" not in ledger.columns:
            ledger["W/L"] = ""

        ledger_updated, moved_idx = append_past_bets_to_ledger(bets, ledger, now_utc)

        if DELETE_MOVED_BETS and len(moved_idx) > 0:
            bets.drop(index=moved_idx).to_csv(BETS_PATH, index=False)
            print(f"Removed {len(moved_idx)} moved bet(s) from bets.csv.")

        unsettled_mask = ~ledger_updated["W/L"].astype(str).isin(["W", "L", "P"])
        unsettled = ledger_updated.loc[unsettled_mask].copy()

    # ── Shared: within-3-day window + score polling ──────────────────────────
    unsettled_times = unsettled["commence_time"].apply(to_utc_ts)
    within_3_mask   = (~unsettled_times.isna()) & ((now_utc - unsettled_times).dt.total_seconds() <= 3 * 86400)
    within_3_days   = unsettled.loc[within_3_mask].copy()

    if within_3_days.empty:
        print("No unsettled games within the last 3 days. Nothing to poll via /scores.")
        if sb_rows is None and WRITE_BACK:
            ledger_updated.to_csv(LEDGER_PATH, index=False)
        return

    if MAX_DAYS_FROM is not None:
        days_from = max(1, min(3, int(MAX_DAYS_FROM)))
    else:
        days_from = compute_days_from_for_subset(within_3_days["commence_time"], now_utc)

    ev_frames  = []
    credit_cost = 0
    quotas     = []

    for sport_key, grp in within_3_days.groupby("sport"):
        ev_ids = grp["game_id"].dropna().astype(str).unique().tolist()
        if not ev_ids:
            continue
        data, quota = fetch_scores(API_KEY, sport_key, ev_ids, days_from=days_from)
        ev_frames.append(parse_scores_into_frame(data))
        quotas.append((sport_key, quota))
        credit_cost += 2

    ev_all = pd.concat(ev_frames, ignore_index=True) if ev_frames else pd.DataFrame(
        columns=["id","sport_key","home_team","away_team","completed",
                 "home_score","away_score","margin","total_points","last_update"]
    )
    ev_map = {row["id"]: row for row in ev_all.to_dict(orient="records")}

    # ── Settle ───────────────────────────────────────────────────────────────
    ledger_updated.loc[unsettled_mask, "W/L"] = (
        ledger_updated.loc[unsettled_mask].apply(lambda r: settle_row(r, ev_map), axis=1)
    )

    graded_mask = ledger_updated["W/L"].isin(["W", "L", "P"])
    graded_rows = ledger_updated.loc[graded_mask]

    # ── Write results ────────────────────────────────────────────────────────
    if sb_rows is not None:
        sb.update_tracked_picks_results(graded_rows)   # W/L → tracked_picks.result
        sb.upsert_settled_picks(graded_rows)            # append to settled_picks
    else:
        if WRITE_BACK:
            ledger_updated.to_csv(LEDGER_PATH, index=False)
        sb.upsert_settled_picks(graded_rows)

    print(f"Polled {len(quotas)} sport(s) with daysFrom={days_from}. Estimated credits: {credit_cost}.")
    for sport_key, quota in quotas:
        print(f"[{sport_key}] headers: remaining={quota['remaining']} used={quota['used']} last={quota['last']}")

if __name__ == "__main__":
    main()
