# live_lags.py
from __future__ import annotations
from pathlib import Path
from typing import Tuple
import numpy as np
import pandas as pd

try:
    import pyarrow.dataset as ds
    HAVE_ARROW = True
except Exception:
    HAVE_ARROW = False

SNAP_DIR = Path("snapshots")
KEY = ["game_id", "team", "market", "point"]
FIRST_KEY = ["game_id", "team", "market"]  # <- new (ignores point)
MAX_LAGS = 25
TIME_COL = "snapshot_time"



FIRSTS_PATH = Path("opening_lines/firsts.parquet")

FIRST_PK = ["game_id", "team", "market"]  # persist *without* point

def _load_firsts() -> pd.DataFrame:
    if FIRSTS_PATH.exists():
        df = pd.read_parquet(FIRSTS_PATH)
        # enforce dtypes we rely on
        df["time_of_first_line"] = pd.to_datetime(df["time_of_first_line"], utc=True, errors="coerce")
        return df
    cols = FIRST_PK + ["first_line", "first_point", "time_of_first_line"]
    df = pd.DataFrame(columns=cols)
    df["time_of_first_line"] = pd.to_datetime(df["time_of_first_line"], utc=True, errors="coerce")
    return df

def _save_firsts(df: pd.DataFrame) -> None:
    FIRSTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    # de-dup by PK (keep earliest)
    if not df.empty:
        df = (df.sort_values("time_of_first_line")
                .drop_duplicates(subset=FIRST_PK, keep="first"))
    df.to_parquet(FIRSTS_PATH, index=False)

def _upsert_firsts_from_board(board: pd.DataFrame, firsts: pd.DataFrame) -> pd.DataFrame:
    """Insert brand-new (game_id,team,market) anchors with current sharp_odds/point/snapshot_time.
       Never overwrite existing anchors."""
    if board.empty:
        return firsts
    have = set(map(tuple, firsts[FIRST_PK].to_numpy())) if not firsts.empty else set()
    add = []
    now = pd.Timestamp.now(tz="UTC")
    cols = FIRST_PK + ["sharp_odds", "point", "snapshot_time"]
    for _, r in board.loc[board["sharp_odds"].notna(), cols].iterrows():
        key = (r["game_id"], r["team"], r["market"])
        if key in have:
            continue
        t0 = r.get("snapshot_time")
        add.append({
            "game_id": key[0],
            "team": key[1],
            "market": key[2],
            "first_line": float(r["sharp_odds"]),
            "first_point": float(r["point"]) if pd.notna(r["point"]) else np.nan,
            "time_of_first_line": pd.to_datetime(t0, utc=True, errors="coerce") if pd.notna(t0) else now,
        })
        have.add(key)
    if add:
        firsts = pd.concat([firsts, pd.DataFrame(add)], ignore_index=True)
    return firsts

def _purge_firsts(firsts: pd.DataFrame, board: pd.DataFrame) -> pd.DataFrame:
    """Drop anchors for games no longer present and clearly in the past (housekeeping)."""
    if firsts.empty:
        return firsts
    if board.empty:
        return firsts
    # keep anchors for game_ids still on the live board OR who commence in future
    keep_game_ids = set(board["game_id"].astype(str))
    mask_keep = firsts["game_id"].astype(str).isin(keep_game_ids)
    return firsts.loc[mask_keep].copy()

def _ensure_present(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Add any of `cols` that are missing, filled with NaN (or NaT for timestamps)."""
    if df is None or df.empty:
        return df
    for c in cols:
        if c not in df.columns:
            if c == "time_of_first_line":
                df[c] = pd.NaT
            else:
                df[c] = np.nan
    return df


# ---------- odds mapping (re-uses your odds_engine curves) ----------
from odds_engine import _load_mapping, _make_spreads_curve, _make_totals_curve, _logit, _sigmoid  # type: ignore

MAPPING_IDS = {
    ("americanfootball_nfl",   "spreads"): "NFL_spreads",
    ("americanfootball_nfl",   "totals"):  "NFL_totals",
    ("americanfootball_ncaaf", "spreads"): "NCAAF_spreads",
    ("americanfootball_ncaaf", "totals"):  "NCAAF_totals",
}

def _odds_to_p(odds: np.ndarray) -> np.ndarray:
    odds = np.asarray(odds, float)
    out = np.full_like(odds, np.nan, dtype=float)
    m = np.isfinite(odds) & (odds > 0)
    out[m] = 1.0 / odds[m]
    return out

def _p_to_odds(p: np.ndarray) -> np.ndarray:
    p = np.asarray(p, float)
    out = np.full_like(p, np.nan, dtype=float)
    m = np.isfinite(p) & (p > 0) & (p < 1)
    out[m] = 1.0 / p[m]
    return out

def _build_curves(mappings_dir: str):
    # cacheable dict of z() callables per sport/market family
    curves = {}
    for (sport, market), cid in MAPPING_IDS.items():
        payload = _load_mapping(cid, mappings_dir)
        curves[(sport, market)] = (
            _make_totals_curve(payload) if market == "totals" else _make_spreads_curve(payload)
        )
    return curves

# ---------- IO helpers ----------
LAG_COLS  = [f"sharp_odds_lag{k}" for k in range(1, MAX_LAGS + 1)]
MINS_COLS = [f"mins_ago_lag{k}"   for k in range(1, MAX_LAGS + 1)]
KEEP_BASE = ["snapshot_time","sport","game_id","commence_time","team","market","point","sharp_odds",
             "first_line","first_point","time_of_first_line"] + LAG_COLS + MINS_COLS  # + first_point

def _read_today_latest_snapshot(snap_dir: Path) -> tuple[pd.DataFrame, pd.Timestamp, pd.DataFrame]:
    """
    Read today's part-*.parquet under snapshots/YYYYMMDD/.
    Returns:
      last_df  : rows at the max snapshot_time (latest block)
      last_ts  : that timestamp
      hist_day : ALL rows for today (used for exact prior-time point lookups)
    """
    # Today in UTC (use your folder naming convention)
    utc_today = pd.Timestamp.now(tz="UTC").strftime("%Y%m%d")
    day_dir = snap_dir / utc_today
    if not day_dir.exists():
        # Try local date as a fallback (if your folder is local-day based)
        local_today = pd.Timestamp.now().strftime("%Y%m%d")
        day_dir = snap_dir / local_today
        if not day_dir.exists():
            return pd.DataFrame(), pd.NaT, pd.DataFrame()

    # Find all parquet parts in the day folder
    parts = sorted(day_dir.glob("*.parquet"))
    if not parts:
        # Some writers put them in a subfolder; fallback to recursive
        parts = sorted(day_dir.rglob("*.parquet"))
    if not parts:
        return pd.DataFrame(), pd.NaT, pd.DataFrame()

    # Read only needed columns, tolerate days before first_line existed
    need = [c for c in KEEP_BASE if c != "time_of_first_line"] + ["time_of_first_line"]
    dfs = []
    for p in parts:
        t0 = pd.read_parquet(p)
        cols = [c for c in need if c in t0.columns]
        dfs.append(t0[cols])
    hist_day = pd.concat(dfs, ignore_index=True)

    if hist_day.empty:
        return pd.DataFrame(), pd.NaT, pd.DataFrame()

    # Normalize dtypes we rely on
    hist_day["snapshot_time"] = pd.to_datetime(hist_day["snapshot_time"], utc=True, errors="coerce")
    if "time_of_first_line" in hist_day.columns:
        hist_day["time_of_first_line"] = pd.to_datetime(hist_day["time_of_first_line"], utc=True, errors="coerce")

    last_ts = hist_day["snapshot_time"].max()
    last_df = hist_day.loc[hist_day["snapshot_time"] == last_ts].copy()
    
    _need = ["first_line", "first_point", "time_of_first_line"] + LAG_COLS + MINS_COLS
    hist_day = _ensure_present(hist_day, _need)
    last_df  = _ensure_present(last_df,  _need)

    return last_df, last_ts, hist_day


def _shift_right_from_last(last_df: pd.DataFrame, new_time: pd.Timestamp) -> pd.DataFrame:
    """
    Produce a DataFrame keyed by KEY with shifted lags:
      lag{k}   <- last.lag{k-1}
      mins{k}  <- last.mins{k-1}
      lag1     <- last.sharp_odds
      mins1    <- minutes(new_time - last.snapshot_time)
    Also carry first_line/time_of_first_line.
    """
    _need = ["first_line","first_point","time_of_first_line"] + LAG_COLS + MINS_COLS
    last_df = _ensure_present(last_df, _need)
    out = last_df[KEY + ["sharp_odds","snapshot_time","first_line","first_point","time_of_first_line"] + LAG_COLS + MINS_COLS].copy()
    delta_min = (new_time - out["snapshot_time"]).dt.total_seconds() / 60.0
    
    # shift 2..MAX from prior lags
    for k in range(MAX_LAGS, 1, -1):
        out[f"sharp_odds_lag{k}"] = out.get(f"sharp_odds_lag{k-1}", np.nan)
        prev_m = pd.to_numeric(out.get(f"mins_ago_lag{k-1}", np.nan), errors="coerce")
        out[f"mins_ago_lag{k}"]   = prev_m + delta_min

    # lag1 from prior sharp_odds and delta-minutes
    out["sharp_odds_lag1"] = out["sharp_odds"].astype(float)
    out["mins_ago_lag1"]   = delta_min.astype(float)

    # keep only the columns we’ll merge to the new board
    keep = KEY + ["first_line","first_point","time_of_first_line"] + LAG_COLS + MINS_COLS
    return out[keep].copy()

def _prune_stale_lags(df: pd.DataFrame, max_minutes: int = 600) -> None:
    for k in range(1, MAX_LAGS + 1):
        mc, oc = f"mins_ago_lag{k}", f"sharp_odds_lag{k}"
        stale = pd.to_numeric(df[mc], errors="coerce") > float(max_minutes)
        df.loc[stale, [mc, oc]] = np.nan
        

def _latest_seen_shift(hist_day: pd.DataFrame, now_ts: pd.Timestamp) -> pd.DataFrame:
    """
    For each KEY, take the *latest* row in hist_day, then produce a shifted
    lag view as-of now_ts:
      lag{k}   <- latest.lag{k-1}
      mins{k}  <- latest.mins{k-1} + (now - latest.snapshot_time)
      lag1     <- latest.sharp_odds
      mins1    <- (now - latest.snapshot_time)
    Carries first_line/time_of_first_line through untouched.
    """
    if hist_day.empty:
        return pd.DataFrame(columns=KEY + ["first_line","time_of_first_line"] + LAG_COLS + MINS_COLS)

    # ensure dtypes
    df = hist_day.copy()
    df["snapshot_time"] = pd.to_datetime(df["snapshot_time"], utc=True, errors="coerce")

    # latest row per KEY
    df = df.sort_values("snapshot_time")
    _need = ["first_line","first_point","time_of_first_line"] + LAG_COLS + MINS_COLS
    df = _ensure_present(df, _need)
    last_idx = df.drop_duplicates(subset=KEY, keep="last").index
    latest = df.loc[last_idx, KEY + ["sharp_odds","snapshot_time","first_line","first_point","time_of_first_line"] + LAG_COLS + MINS_COLS].copy()

    delta_min = (now_ts - latest["snapshot_time"]).dt.total_seconds() / 60.0

    # shift minutes forward for every lag and move odds one step right
    for k in range(MAX_LAGS, 1, -1):
        latest[f"sharp_odds_lag{k}"] = latest.get(f"sharp_odds_lag{k-1}", np.nan)
        prev_m = pd.to_numeric(latest.get(f"mins_ago_lag{k-1}", np.nan), errors="coerce")
        latest[f"mins_ago_lag{k}"]   = prev_m + delta_min

    latest["sharp_odds_lag1"] = pd.to_numeric(latest["sharp_odds"], errors="coerce")
    latest["mins_ago_lag1"]   = delta_min.astype(float)

    keep = KEY + ["first_line","first_point","time_of_first_line"] + LAG_COLS + MINS_COLS
    return latest[keep].copy()


def _earliest_firstline(hist_day: pd.DataFrame) -> pd.DataFrame:
    """
    For each (game_id, team, market), return:
      • first_line               (sharp_odds at the earliest time we saw this game/team/market today)
      • first_point              (point at that same earliest time)
      • time_of_first_line       (that earliest snapshot_time)
    """
    if hist_day.empty:
        cols = FIRST_KEY + ["first_line","first_point","time_of_first_line"]
        return pd.DataFrame(columns=cols).set_index(FIRST_KEY)

    df = hist_day.copy()
    df["snapshot_time"] = pd.to_datetime(df["snapshot_time"], utc=True, errors="coerce")
    df = df.sort_values("snapshot_time")

    # take earliest per (gid, team, market) — NOT including point
    first_idx = df.drop_duplicates(subset=FIRST_KEY, keep="first").index
    earliest = (
        df.loc[first_idx, FIRST_KEY + ["sharp_odds","point","snapshot_time"]]
          .rename(columns={"sharp_odds": "first_line", "point": "first_point", "snapshot_time": "time_of_first_line"})
          .set_index(FIRST_KEY)
    )
    return earliest


# --- NEW: fill from same-snapshot siblings on the current board ---
def _fill_from_current_snapshot_siblings(board: pd.DataFrame, mappings_dir: str) -> None:
    """
    For NFL/NCAAF spreads/totals rows with missing lags, try to copy each lag k
    from another row of the SAME (game, team, market) in *this board* (different point),
    then map sibling_point -> target_point using the football curves.
    """
    if board.empty:
        return
    curves = _build_curves(mappings_dir)

    fam = board.copy()
    fam["__row"] = fam.index  # carry original board row labels

    fam["point"] = pd.to_numeric(fam["point"], errors="coerce")
    is_fb = fam["sport"].astype(str).isin(["americanfootball_nfl","americanfootball_ncaaf"])
    is_st = fam["market"].astype(str).isin(["spreads","totals"])
    fam = fam[is_fb & is_st].copy()
    if fam.empty:
        return

    # Build a donor table per (gid,team,market) that *has* any lag entries (sibling point)
    key = ["game_id","team","market"]
    donor_cols = key + ["point"] + LAG_COLS + MINS_COLS + ["sport"]
    donors = fam[donor_cols].copy()

    # Self-join on (gid,team,market), but exclude identical point (we need a different point)
    merged = fam.merge(donors, on=key, how="left", suffixes=("", "__sib"))
    merged = merged[merged["point"] != merged["point__sib"]]
    merged = merged.set_index("__row", drop=True)  # <- crucial


    if merged.empty:
        return

    sport = merged["sport"].astype(str).to_numpy()
    market = merged["market"].astype(str).to_numpy()
    p_to   = pd.to_numeric(merged["point"], errors="coerce").to_numpy()
    p_from = pd.to_numeric(merged["point__sib"], errors="coerce").to_numpy()
    teams  = merged["team"].astype(str).to_numpy()

    is_nfl   = (sport == "americanfootball_nfl")
    is_ncaaf = (sport == "americanfootball_ncaaf")

    for k in range(1, MAX_LAGS+1):
        oc, mc = f"sharp_odds_lag{k}", f"mins_ago_lag{k}"
        need = merged[oc].isna().to_numpy() & merged[f"{oc}__sib"].notna().to_numpy()
        if not need.any():
            continue

        # use sibling's lagk as donor odds & mins
        donor_odds = pd.to_numeric(merged.loc[need, f"{oc}__sib"], errors="coerce").to_numpy()
        donor_mins = pd.to_numeric(merged.loc[need, f"{mc}__sib"], errors="coerce").to_numpy()
        if donor_odds.size == 0:
            continue

        # totals: model Over, flip for Under
        mask_tot = need & (market == "totals") & (is_nfl | is_ncaaf)
        if mask_tot.any():
            z_nfl   = curves[("americanfootball_nfl","totals")]
            z_ncaaf = curves[("americanfootball_ncaaf","totals")]
            ix = np.where(mask_tot)[0]
            odds = pd.to_numeric(merged.loc[mask_tot, f"{oc}__sib"], errors="coerce").to_numpy()
            p    = _odds_to_p(odds)
            over = np.array([str(t).lower().startswith("over") for t in teams[mask_tot]], bool)
            # choose curve by sport row-wise
            mapped = np.empty_like(p)
            for j, row_idx in enumerate(ix):
                z = z_nfl if is_nfl[row_idx] else z_ncaaf
                pt_anchor = float(merged.iloc[row_idx]["point__sib"])
                pt_target = float(merged.iloc[row_idx]["point"])
                p_anchor_over = p[j] if over[j] else (1.0 - p[j])
                z_to = _logit(p_anchor_over) + (z(pt_target) - z(pt_anchor))
                p_over_to = _sigmoid(z_to)
                p_row = p_over_to if over[j] else (1.0 - p_over_to)
                mapped[j] = 1.0 / np.clip(p_row, 1e-9, 1-1e-9)
            # re-pull donor mins aligned to the SAME mask (no cross-slicing)
            board.loc[merged.index[mask_tot], oc] = mapped
            donor_mins_tot = pd.to_numeric(merged.loc[mask_tot, f"{mc}__sib"], errors="coerce").to_numpy()
            board.loc[merged.index[mask_tot], mc] = donor_mins_tot

        # spreads: model underdog at |s|, flip for favorite
        mask_spr = need & (market == "spreads") & (is_nfl | is_ncaaf)
        if mask_spr.any():
            ix = np.where(mask_spr)[0]
            odds = pd.to_numeric(merged.loc[mask_spr, f"{oc}__sib"], errors="coerce").to_numpy()
            p    = _odds_to_p(odds)
            mapped = np.empty_like(p)
            for j, row_idx in enumerate(ix):
                z = curves[("americanfootball_nfl","spreads")] if is_nfl[row_idx] else curves[("americanfootball_ncaaf","spreads")]
                s_anchor  = abs(float(merged.iloc[row_idx]["point__sib"]))
                s_target  = abs(float(merged.iloc[row_idx]["point"]))
                side_sign = np.sign(float(merged.iloc[row_idx]["point"]))  # + underdog, - favorite
                p_und_anchor = p[j] if side_sign >= 0 else (1.0 - p[j])
                z_to = _logit(p_und_anchor) + (z(s_target) - z(s_anchor))
                p_und_to = _sigmoid(z_to)
                p_row = p_und_to if side_sign >= 0 else (1.0 - p_und_to)
                mapped[j] = 1.0 / np.clip(p_row, 1e-9, 1-1e-9)
            board.loc[merged.index[mask_spr], oc] = mapped
            donor_mins_spr = pd.to_numeric(merged.loc[mask_spr, f"{mc}__sib"], errors="coerce").to_numpy()
            board.loc[merged.index[mask_spr], mc] = donor_mins_spr


# --- NEW: exact prior-point mapping from last snapshot for remaining gaps ---
def _fill_from_last_snapshot_exact(
    board: pd.DataFrame,
    last_df: pd.DataFrame,
    last_ts: pd.Timestamp,
    hist_day: pd.DataFrame,           # NEW: full intraday history already loaded
    mappings_dir: str,
    now_ts: pd.Timestamp,
) -> None:
    """
    For still-missing lagk, compute prior_time_k = last_ts − donor_mins_k,
    fetch donor point at that exact time from hist_day, then map donor_point -> target_point.
    """
    if board.empty or last_df.empty or hist_day.empty or pd.isna(last_ts):
        return

    curves = _build_curves(mappings_dir)
    
    delta_min_since_last = float((now_ts - last_ts).total_seconds() / 60.0)

    # Donor mins/odds from last snapshot keyed by (gid,team,market,point)
    donors = last_df[KEY + LAG_COLS + MINS_COLS + ["sport"]].copy()
    
    # before merge:
    left = board.reset_index().rename(columns={"index":"__row"})

    merged = left.merge(donors, on=KEY, how="left", suffixes=("","__don"))
    missing_any = np.column_stack([merged[f"sharp_odds_lag{k}"].isna().to_numpy()
                               for k in range(1, MAX_LAGS+1)]).any(axis=1)
    merged = merged.loc[missing_any]
    if merged.empty:
        return
    
    # Fast exact lookup index from the in-memory intraday history
    ix_cols = ["game_id","team","market","snapshot_time"]
    hist_ix = (hist_day[ix_cols + ["point"]]
               .drop_duplicates(ix_cols)
               .set_index(ix_cols)
               .sort_index())

    # For each lag k, compute the exact prior_time and map using donor_point(prior_time)
    for k in range(1, MAX_LAGS+1):
        oc, mc = f"sharp_odds_lag{k}", f"mins_ago_lag{k}"
        need_k = merged[oc].isna() & merged[f"{mc}__don"].notna()
        if not need_k.any():
            continue

        rows = merged.loc[need_k]
        mins = pd.to_numeric(rows[f"{mc}__don"], errors="coerce")
        prior_ts = last_ts - pd.to_timedelta(mins, unit="m")

        key = pd.MultiIndex.from_arrays([
            rows["game_id"].astype(str),
            rows["team"].astype(str),
            rows["market"].astype(str),
            prior_ts
        ], names=ix_cols)

        donor_point = pd.Series(np.nan, index=rows.index, dtype="float64")
        hit = key.isin(hist_ix.index)
        if hit.any():
            donor_point.loc[rows.index[hit]] = hist_ix.reindex(key[hit])["point"].to_numpy()

        # Only map where we found the exact donor point
        ok = donor_point.notna().to_numpy()
        if not ok.any():
            continue

        idxs_merged = rows.index[ok]                               # labels in MERGED
        idxs_board  = merged.loc[idxs_merged, "__row"].to_numpy()  # map -> BOARD labels

        # pull arrays aligned to the same merged subset
        sport  = merged.loc[idxs_merged, "sport"].astype(str).to_numpy()
        market = merged.loc[idxs_merged, "market"].astype(str).to_numpy()
        pt_to  = pd.to_numeric(merged.loc[idxs_merged, "point"], errors="coerce").to_numpy()
        pt_fr  = donor_point.loc[idxs_merged].to_numpy()
        odds_d = pd.to_numeric(merged.loc[idxs_merged, f"{oc}__don"], errors="coerce").to_numpy()
        mins_d = pd.to_numeric(merged.loc[idxs_merged, f"{mc}__don"], errors="coerce").to_numpy()
        teamlb = merged.loc[idxs_merged, "team"].astype(str).to_numpy()

        # Totals: Over modeled, flip for Under
        mask_tot = (market == "totals") & np.isin(sport, ["americanfootball_nfl","americanfootball_ncaaf"])
        if mask_tot.any():
            mapped = np.empty(mask_tot.sum())
            ii = np.where(mask_tot)[0]
            for j, loc in enumerate(ii):
                z = curves[(sport[loc], "totals")]
                p_from = 1.0 / max(odds_d[loc], 1e-9)
                over = teamlb[loc].lower().startswith("over")
                p_over_from = p_from if over else (1.0 - p_from)
                z_to = _logit(p_over_from) + (z(pt_to[loc]) - z(pt_fr[loc]))
                p_over_to = _sigmoid(z_to)
                p_row = p_over_to if over else (1.0 - p_over_to)
                mapped[j] = 1.0 / np.clip(p_row, 1e-9, 1-1e-9)
            board.loc[idxs_board[mask_tot], oc] = mapped 
            board.loc[idxs_board[mask_tot], mc] = mins_d[mask_tot] + delta_min_since_last

        # Spreads: Underdog modeled, flip for favorite
        mask_spr = (market == "spreads") & np.isin(sport, ["americanfootball_nfl","americanfootball_ncaaf"])
        if mask_spr.any():
            mapped = np.empty(mask_spr.sum())
            ii = np.where(mask_spr)[0]
            for j, loc in enumerate(ii):
                z = curves[(sport[loc], "spreads")]
                s_to = abs(pt_to[loc]); s_fr = abs(pt_fr[loc])
                side_sign = np.sign(pt_to[loc])
                p_from = 1.0 / max(odds_d[loc], 1e-9)
                p_und_from = p_from if side_sign >= 0 else (1.0 - p_from)
                z_to = _logit(p_und_from) + (z(s_to) - z(s_fr))
                p_und_to = _sigmoid(z_to)
                p_row = p_und_to if side_sign >= 0 else (1.0 - p_und_to)
                mapped[j] = 1.0 / np.clip(p_row, 1e-9, 1-1e-9)
            board.loc[idxs_board[mask_spr], oc] = mapped
            board.loc[idxs_board[mask_spr], mc] = mins_d[mask_spr] + delta_min_since_last
          
            
def _map_first_line_to_current(board: pd.DataFrame, mappings_dir: str) -> None:
    """
    For NFL/NCAAF spreads/totals rows with defined first_line & first_point and a current numeric point,
    map the first_line odds (anchored at first_point) onto the current point using your football curves.
    Result goes back into board['first_line'] in-place. Non-football / h2h rows are skipped.
    """
    if board.empty: return
    curves = _build_curves(mappings_dir)

    fam = board.copy()
    fam_idx = fam.index

    sport  = fam["sport"].astype(str)
    market = fam["market"].astype(str)
    team   = fam["team"].astype(str)

    p_cur  = pd.to_numeric(fam["point"], errors="coerce")
    p_first= pd.to_numeric(fam["first_point"], errors="coerce")
    odds0  = pd.to_numeric(fam["first_line"], errors="coerce")

    is_fb  = sport.isin(["americanfootball_nfl","americanfootball_ncaaf"])
    is_st  = market.isin(["spreads","totals"])
    need   = is_fb & is_st & p_cur.notna() & p_first.notna() & odds0.notna() & (p_cur != p_first)

    if not need.any():
        return

    idx = fam_idx[need]
    for i in idx:
        s   = sport.at[i]; m = market.at[i]
        z   = curves[(s, m)]
        pt0 = float(p_first.at[i]); pt1 = float(p_cur.at[i])
        o0  = float(odds0.at[i])
        p0  = 1.0 / max(o0, 1e-9)

        if m == "totals":
            over = team.at[i].lower().startswith("over")
            p_over0 = p0 if over else (1.0 - p0)
            z1 = _logit(p_over0) + (z(pt1) - z(pt0))
            p_over1 = _sigmoid(z1)
            p1 = p_over1 if over else (1.0 - p_over1)
        else:  # spreads
            side_sign = np.sign(float(p_cur.at[i]))
            p_und0 = p0 if side_sign >= 0 else (1.0 - p0)  # model underdog at |s|
            z1 = _logit(p_und0) + (z(abs(pt1)) - z(abs(pt0)))
            p_und1 = _sigmoid(z1)
            p1 = p_und1 if side_sign >= 0 else (1.0 - p_und1)

        fam.at[i, "first_line"] = 1.0 / np.clip(p1, 1e-9, 1 - 1e-9)

    board.loc[idx, "first_line"] = fam.loc[idx, "first_line"].to_numpy()
          
            
def _ensure_cols(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        if c not in out.columns:
            out[c] = pd.NaT if "time_of_first_line" == c else np.nan   # handles first_point as NaN
    if "time_of_first_line" in out.columns:
        out["time_of_first_line"] = pd.to_datetime(out["time_of_first_line"], utc=True, errors="coerce")
    return out


def augment_board_after_run(
    board: pd.DataFrame,
    *,
    snap_dir: str | Path = SNAP_DIR,
    mappings_dir: str = "mappings",
    max_lag_minutes: int = 600,
) -> pd.DataFrame:
    """
    1) read today's latest snapshot (with lags already saved),
    2) shift those lags right + set lag1 from last sharp_odds and minutes since,
    3) merge into the new board on (game_id, team, market, point),
    4) prune >600-min lags,
    5) vector-fill missing lags for NFL/NCAAF spreads/totals via mappings (fast).
    """
    if board.empty:
        return board

    last_df, last_ts, hist_day = _read_today_latest_snapshot(Path(snap_dir))
    now_ts = pd.Timestamp.now(tz="UTC")
    
    
    if last_df.empty or pd.isna(last_ts):
        # Nothing to inherit — just attach empty columns so schema is stable
        out = board.copy()
        out["first_line"] = np.nan
        out["first_point"] = np.nan
        out["time_of_first_line"] = pd.NaT
        for c in LAG_COLS + MINS_COLS:
            out[c] = np.nan
        return out

    # 1) shift-right view from last snapshot
    shifted = _shift_right_from_last(last_df, now_ts)

    # 2) merge onto the new board
    out = board.merge(shifted, on=KEY, how="left")
    # ensure newer columns always exist on the merged board
    _need = ["first_line","first_point","time_of_first_line"] + LAG_COLS + MINS_COLS
    out = _ensure_present(out, _need)
    
    # ── Load persistent firsts and attach them (carry across days)
    firsts = _load_firsts()
    if not firsts.empty:
        out = out.merge(firsts, on=FIRST_PK, how="left")  # adds first_line/first_point/time_of_first_line when known

    # ensure newer columns always exist on the merged board
    _need = ["first_line","first_point","time_of_first_line"] + LAG_COLS + MINS_COLS
    out = _ensure_present(out, _need)
    
    # ── Create anchors only for brand-new (game_id,team,market) we've never seen before
    firsts = _upsert_firsts_from_board(
        board.assign(snapshot_time=now_ts),  # ensure snapshot_time is present
        firsts
    )
    # Save registry immediately (so restarts won’t lose new anchors)
    _save_firsts(firsts)
    
    # --- NEW: fill missing lags from the last time this KEY was seen today ---
    missing_lag_any = np.column_stack([out[f"sharp_odds_lag{k}"].isna().to_numpy() for k in range(1, MAX_LAGS+1)]).any(axis=1)
    if missing_lag_any.any():
        latest_seen = _latest_seen_shift(hist_day, now_ts)
        # suffix so we only fill NaNs
        out2 = out.merge(latest_seen, on=KEY, how="left", suffixes=("", "__late"))
        # fill lags where still NaN
        for k in range(1, MAX_LAGS+1):
            oc, mc = f"sharp_odds_lag{k}", f"mins_ago_lag{k}"
            need = out2[oc].isna() & out2[f"{oc}__late"].notna()
            if need.any():
                out2.loc[need, oc] = out2.loc[need, f"{oc}__late"].to_numpy()
                out2.loc[need, mc] = out2.loc[need, f"{mc}__late"].to_numpy()
        out = out2.drop(columns=[c for c in out2.columns if c.endswith("__late")])

    # --- NEW: backfill first_line/time from earliest occurrence today ---
    # backfill firsts from earliest (by FIRST_KEY)
    #need_first = out["first_line"].isna()
    #if need_first.any():
    #    earliest = _earliest_firstline(hist_day)         # indexed by FIRST_KEY now
    #    sub_key = out.loc[need_first, FIRST_KEY].set_index(FIRST_KEY)
    #    got = earliest.reindex(sub_key.index)

    #    fillmask = got["first_line"].notna().to_numpy()
    #    if fillmask.any():
    #        rows = out.loc[need_first].index[fillmask]
    #        out.loc[rows, "first_line"] = got.loc[fillmask, "first_line"].to_numpy()
    #        out.loc[rows, "first_point"] = got.loc[fillmask, "first_point"].to_numpy()          # NEW
    #        out.loc[rows, "time_of_first_line"] = got.loc[fillmask, "time_of_first_line"].to_numpy()
    
    
    now_ts = pd.Timestamp.now(tz="UTC")
    mask_new = out["first_line"].isna() & out["sharp_odds"].notna()
    out.loc[mask_new, "first_line"] = pd.to_numeric(out.loc[mask_new, "sharp_odds"], errors="coerce")
    out.loc[mask_new, "first_point"] = pd.to_numeric(out.loc[mask_new, "point"], errors="coerce")   # NEW
    out.loc[mask_new, "time_of_first_line"] = now_ts
    
    # 3) prune >600 minutes
    _prune_stale_lags(out, max_minutes=max_lag_minutes)
    _map_first_line_to_current(out, mappings_dir=mappings_dir)

    # 1) same-snapshot sibling (current board) first
    _fill_from_current_snapshot_siblings(out, mappings_dir=mappings_dir)

    # 2) exact prior-time donor point from today’s in-memory history
    _fill_from_last_snapshot_exact(
        out,
        last_df=last_df,
        last_ts=last_ts,
        hist_day=hist_day,              # NEW
        mappings_dir=mappings_dir,
        now_ts=now_ts, 
    )

    # re-prune (mapping may copy donor mins)
    _prune_stale_lags(out, max_minutes=max_lag_minutes)
    return out
