import requests
import pandas as pd
import numpy as np
from typing import Callable, List, Tuple, Dict

###############################################################################
# 1. NETWORK HELPERS
###############################################################################

def build_odds_url(api_key: str, sport: str, markets: str, books: str) -> str:
    """Return a fully‑formed Odds‑API v4 URL."""
    return (
        f"https://api.the-odds-api.com/v4/sports/{sport}/odds?"  # endpoint
        f"apiKey={api_key}&bookmakers={books}&markets={markets}&oddsFormat=decimal"
    )


#def fetch_odds_json(url: str, timeout: int = 10) -> Tuple[List[Dict], Dict[str, str]]:
#    """GET the Odds‑API endpoint and return (json, headers). Raises on non‑200."""
#    resp = requests.get(url, timeout=timeout)
#    resp.raise_for_status()
    
import time, requests
from typing import Tuple, List, Dict
    
def fetch_odds_json(url: str, timeout: int = 12) -> Tuple[List[Dict], Dict[str, str]]:
    """GET the Odds API v4 endpoint. Always returns (json, headers) or raises."""
    backoffs = [0, 1.0, 3.0]  # immediate, then 1s, then 3s
    last_err = None
    for i, sleep_s in enumerate(backoffs):
        if sleep_s:
            time.sleep(sleep_s)
        try:
            resp = requests.get(url, timeout=timeout)
        except Exception as e:
            last_err = e
            continue

        # Rate limit / server errors: retry on 429/5xx
        if resp.status_code in (429, 500, 502, 503, 504):
            last_err = RuntimeError(
                f"HTTP {resp.status_code} from Odds API; "
                f"x-requests-remaining={resp.headers.get('x-requests-remaining')}, "
                f"x-requests-used={resp.headers.get('x-requests-used')}, "
                f"x-requests-reset={resp.headers.get('x-requests-reset')}"
            )
            continue

        # Non-success that we don't retry → raise with context
        if resp.status_code != 200:
            snippet = resp.text[:300].replace("\n", " ")
            raise RuntimeError(
                f"Odds API HTTP {resp.status_code}: {snippet} | "
                f"headers={{'x-requests-remaining': {resp.headers.get('x-requests-remaining')}, "
                f"'x-requests-used': {resp.headers.get('x-requests-used')}, "
                f"'x-requests-reset': {resp.headers.get('x-requests-reset')}}}"
            )

        # 200 OK
        text = (resp.text or "").strip()
        if not text:   # 204-like empty body (some proxies): treat as empty list
            return [], resp.headers
        try:
            return resp.json(), resp.headers  # type: ignore[return-value]
        except ValueError as e:
            raise RuntimeError(f"Invalid JSON from Odds API: {text[:300]}") from e

    # If we got here, all retries failed
    raise RuntimeError(f"Failed to fetch Odds API after retries: {last_err}")

###############################################################################
# 2. FLATTEN JSON  →  LONG DATAFRAME
###############################################################################

def json_to_long(
    json_blob: List[Dict],
    sport_key: str,
    capture_point: bool = False,
) -> pd.DataFrame:
    """Flatten Odds‑API JSON into one row per outcome.

    Parameters
    ----------
    capture_point : set to *True* when the market may carry a `point` (spreads / totals).
    """
    rows = []
    for g in json_blob:
        gid, t0 = g["id"], g["commence_time"]
        for bm in g.get("bookmakers", []):
            bk = bm["key"]
            for mk in bm.get("markets", []):
                mkey = mk["key"]
                for o in mk.get("outcomes", []):
                    rows.append({
                        "sport": sport_key,
                        "game_id": gid,
                        "commence_time": t0,
                        "bookmaker": bk,
                        "market": mkey,
                        "team": o["name"],
                        "price": o.get("price"),
                        "point": o.get("point") if capture_point else None,
                    })
    # 1️⃣  NOTHING scraped for this league → skip it entirely
    if not rows:
        return pd.DataFrame()          # empty frame is the signal to “skip”

    # 2️⃣  normal build & filter
    df = pd.DataFrame(rows)
    return df[df["market"] != "h2h_lay"].copy()

###############################################################################
# 3. BASIC FILTERS & FEATURE COLUMNS
###############################################################################

def drop_started_games(
    df: pd.DataFrame,
    *,
    buffer_minutes: int = 0,
    now: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """
    Remove events that are within `buffer_minutes` of kick-off
    (or have already started).

    buffer_minutes = 0  → cutoff exactly at commence_time
    """
    if now is None:
        now = pd.Timestamp.utcnow()
    buffer = pd.Timedelta(minutes=buffer_minutes)

    df = df.copy()
    df["commence_time"] = pd.to_datetime(df["commence_time"], utc=True)

    return df[df["commence_time"] - buffer > now]


def add_days_to_event(df: pd.DataFrame) -> pd.DataFrame:
    """Add `days_to_event` floating column (UTC)."""
    now = pd.Timestamp.utcnow()
    df["days_to_event"] = (df["commence_time"] - now).dt.total_seconds() / 86_400.0
    return df


def align_to_pin_line(
    long_df: pd.DataFrame,
    *,
    atol: float = 1e-3,          # tweak if you ever see false matches
) -> pd.DataFrame:
    """
    MLB-specific: keep only rows whose `point` is numerically equal to
    Pinnacle’s line (within `atol`).

    Expects columns: game_id, team, market, bookmaker, point
    """
    # ── 1. isolate Pinnacle rows ────────────────────────────────────────────
    pin = long_df[long_df["bookmaker"] == "pinnacle"]

    # helper tables for spreads and totals
    spread_pts = (
        pin.loc[pin["market"] == "spreads", ["game_id", "team", "point"]]
            .rename(columns={"point": "pin_point_spread"})
    )
    total_pts = (
        pin.loc[pin["market"] == "totals", ["game_id", "point"]]
            .drop_duplicates("game_id")
            .rename(columns={"point": "pin_point_total"})
    )

    # ── 2. attach Pinnacle reference lines back to every row ───────────────
    df = (
        long_df
        .merge(spread_pts, on=["game_id", "team"], how="left")
        .merge(total_pts,  on="game_id",       how="left")
    )

    # only keep the relevant reference per market
    df.loc[df["market"] != "spreads", "pin_point_spread"] = np.nan
    df.loc[df["market"] != "totals",  "pin_point_total"]  = np.nan
    df["pin_point"] = np.where(
        df["market"] == "totals",
        df["pin_point_total"],
        df["pin_point_spread"],
    )

    # ── 3. numeric equality test with tolerance ───────────────────────────
    both_vals   = df["point"].notna() & df["pin_point"].notna()
    almost_eq   = np.isclose(df.loc[both_vals, "point"],
                             df.loc[both_vals, "pin_point"],
                             atol=atol)
    mask_equal  = pd.Series(False, index=df.index)
    mask_equal.loc[both_vals] = almost_eq

    mask_both_nan = df["point"].isna() & df["pin_point"].isna()
    mask          = mask_equal | mask_both_nan

    out = df.loc[mask].copy()
    return out.drop(
        columns=["pin_point_spread", "pin_point_total", "pin_point"],
        errors="ignore",
    )


def require_sharp_and_soft(
    wide: pd.DataFrame,
    sharp_list: List[str],
    soft_list: List[str],
) -> pd.DataFrame:
    """Keep rows that have ≥1 sharp price and ≥1 soft price."""
    mask_sharp = wide[sharp_list].notna().any(axis=1)
    mask_soft  = ~wide[soft_list].isna().all(axis=1)
    return wide.loc[mask_sharp & mask_soft].copy()

def require_soft(df, soft_books, min_soft=1):
    # Keep only the soft columns that actually exist on the DF
    soft_cols = [b for b in soft_books if b in df.columns]

    # If no soft columns exist at all, return empty (nothing tradable)
    if not soft_cols:
        return df.iloc[0:0]

    # Row must have >= min_soft non-null soft prices
    mask = df[soft_cols].notna().sum(axis=1) >= int(min_soft)
    return df.loc[mask].copy()

###############################################################################
# 4. RESHAPING & BASIC COLUMN ENSURANCE
###############################################################################

def pivot_wide(
    long_df: pd.DataFrame,
    idx_cols: List[str],
) -> pd.DataFrame:
    """Pivot bookmaker column wide (one col per book)."""
    # ── NEW: protect money-lines ───────────────────────────────────────────
    if "point" in idx_cols:                     # <- spreads/totals present
        long_df = long_df.copy()                # avoid mutating original
        long_df["point"] = long_df["point"].fillna(0.0)  # sentinel for ML
    # ───────────────────────────────────────────────────────────────────────
    return (
        long_df.pivot_table(
            index=idx_cols,
            columns="bookmaker",
            values="price",
            aggfunc="first",
        )
        .reset_index()
    )


def ensure_book_columns(wide: pd.DataFrame, book_list: List[str]) -> pd.DataFrame:
    for bk in book_list:
        if bk not in wide.columns:
            wide[bk] = np.nan
    return wide



#def annotate_non_side_rows(wide: pd.DataFrame) -> pd.DataFrame:
    """
    Replace team labels that start with 'Over', 'Under', or equal 'Draw'
    with '<label> (Team A vs. Team B)', where Team A and Team B are the two
    side teams in that game_id.

    Works directly on the *wide* table, so the annotation persists through
    the rest of the pipeline.
    """
#    def _is_non_side(t: str) -> bool:
#        return t == "Draw" or t.startswith("Over") or t.startswith("Under")

    # 🔒 Guard: make sure 'team' is unique
#    if wide.columns.duplicated().any():
#        wide = wide.loc[:, ~wide.columns.duplicated()].copy()

    # Build   game_id → "Team1 vs. Team2"
#    side_map: dict[str, str] = {}
#    for gid, grp in wide.groupby("game_id"):
#        sides = grp.loc[~grp["team"].apply(_is_non_side), "team"].unique()
#        if len(sides) == 2:
#            side_map[gid] = f"{sides[0]} vs. {sides[1]}"

    # Do the assignment safely
#    new_vals = wide.apply(
#        lambda r: (f"{r['team']} ({side_map[r['game_id']]})"
#                   if _is_non_side(r["team"]) and r["game_id"] in side_map
#                   else r["team"]),
#        axis=1,
#    )

#    wide = wide.copy()
#    wide["team"] = new_vals.astype(str).to_numpy()  # ensure 1-D

#    return wide

def annotate_non_side_rows(wide: pd.DataFrame) -> pd.DataFrame:
    """
    Replace 'Over/Under/Draw' labels with '<label> (Team A vs. Team B)' using
    a per-game side map. Vectorized to avoid 2-D apply return issues.
    """
    def _is_non_side_val(x: object) -> bool:
        s = str(x)
        return (s == "Draw") or s.startswith("Over") or s.startswith("Under")

    df = wide.copy()

    # Guard: drop duplicate-named columns if any (can happen post-pivot)
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()].copy()

    # Build game_id -> "Team1 vs. Team2" for games where we clearly have two sides
    side_map: dict[str, str] = {}
    for gid, grp in df.groupby("game_id", sort=False):
        sides = (
            grp.loc[~grp["team"].map(_is_non_side_val), "team"]
               .dropna()
               .astype(str)
               .unique()
        )
        if len(sides) == 2:
            side_map[gid] = f"{sides[0]} vs. {sides[1]}"

    if not side_map:
        return df

    # Vectorized 1-D assignment (no apply, no 2-D)
    has_map = df["game_id"].isin(side_map.keys())
    is_non  = df["team"].map(_is_non_side_val)
    idx     = has_map & is_non

    df.loc[idx, "team"] = (
        df.loc[idx, "team"].astype(str)
        + " ("
        + df.loc[idx, "game_id"].map(side_map)
        + ")"
    )
    return df





###############################################################################
# 5. PROBABILITY MATH
###############################################################################

_DEF_NAN = np.nan

def add_implied_probs(wide: pd.DataFrame, book_list: List[str]) -> pd.DataFrame:
    """Add p_<book> columns with vig‑included implied probabilities."""
    for bk in book_list:
        wide[f"p_{bk}"] = np.where(wide[bk] > 0, 1 / wide[bk], _DEF_NAN)
    return wide


#def devig_pairwise(
#    wide: pd.DataFrame,
#    book_list: List[str],
#    group_cols: List[str] | None = None,
#) -> pd.DataFrame:
#    """Add fv_<book> columns with fair probabilities (no vig)."""
#    if group_cols is None:
#        group_cols = ["game_id", "market"]
#    for bk in book_list:
#        pcol = f"p_{bk}"
#        total = wide.groupby(group_cols)[pcol].transform("sum")
#        wide[f"fv_{bk}"] = wide[pcol] / total
#    return wide
# ───────────────────────────── helper routines ──────────────────────────────
def _power_log_devig(raw_probs: np.ndarray,
                     tol: float = 1e-12,
                     max_iter: int = 100) -> np.ndarray:
    """
    Iteratively find tau s.t. Σ raw^tau = 1   (power/logarithmic method).
    """
    if abs(raw_probs.sum() - 1.0) < tol:                 # already fair
        return raw_probs / raw_probs.sum()

    lo, hi = 0.10, 10.0                                  # search bounds
    for _ in range(max_iter):
        mid = (lo + hi) / 2
        s = (raw_probs ** mid).sum()
        if s > 1:                                        # need larger tau
            lo = mid
        else:
            hi = mid
    tau = (lo + hi) / 2
    fair = raw_probs ** tau
    return fair / fair.sum()


def _logistic_devig(raw_probs: np.ndarray,
                    tol: float = 1e-12,
                    max_iter: int = 100) -> np.ndarray:
    """
    Shared-k logit shift: find k s.t. Σ σ(logit(r_i) − k) = 1
    (behaves like probit/logit devig for balanced 2-way markets).
    """
    eps   = 1e-12                       # avoid log(0)
    r     = np.clip(raw_probs, eps, 1 - eps)
    logit = np.log(r / (1.0 - r))

    def _sum_p(k: float) -> float:
        return (1.0 / (1.0 + np.exp(-(logit - k)))).sum()

    lo, hi = -10.0, 10.0
    for _ in range(max_iter):
        mid = (lo + hi) / 2
        if _sum_p(mid) > 1.0:
            lo = mid          # need a larger downward shift
        else:
            hi = mid
    k    = (lo + hi) / 2
    fair = 1.0 / (1.0 + np.exp(-(logit - k)))
    return fair / fair.sum()


def _choose_devig(raw_probs: np.ndarray) -> np.ndarray:
    """
    Decide which devig method to use.
    • Logistic if exactly 2 outcomes and both fall in 0.40–0.60.
    • Otherwise power/log.
    """
    if (raw_probs.size == 2
        and raw_probs.max() <= 0.60
        and raw_probs.min() >= 0.40):
        return _logistic_devig(raw_probs)
    else:
        return _power_log_devig(raw_probs)


# ───────────────────────────── main routine ─────────────────────────────────
#def devig_pairwise(
#    wide: pd.DataFrame,
#    book_list: List[str],
#    group_cols: List[str] | None = None,
#) -> pd.DataFrame:
    """
    Add fv_<book> columns with fair (no-vig) probabilities.
    • Power/log devig for all markets except
    • Logistic devig for 2-way markets where both sides ∈ [0.40, 0.60].
    """
#    if group_cols is None:
#        group_cols = ["game_id", "market"]

#    out = wide.copy()
#    for bk in book_list:
#        fvcol = f"fv_{bk}"
#        out[fvcol]  = np.nan  # pre-allocate

    # apply devig group-by-group
#    for _, idx in out.groupby(group_cols).groups.items():
#        for bk in book_list:
#            r = out.loc[idx, f"p_{bk}"].values.astype(float)
#            if np.isnan(r).all():                # skip empty/NaN columns
#                continue
#            fair = _choose_devig(r)
#            out.loc[idx, f"fv_{bk}"] = fair

#    return out

def devig_pairwise(df: pd.DataFrame, books: list[str],
                   market_col: str = "market",
                   point_col: str = "point") -> pd.DataFrame:
    """
    Create fair-prob columns fv_<book> by devigging within each (game, market, pair_key) group.
    pair_key:
      - spreads: abs(point)  (so +6 and -6 pair together)
      - totals:  point
      - else (e.g., h2h): 0.0
    Leaves fv_* as NaN if a book has <2 outcomes in a group.
    Works even when `point` column is absent.
    """
    out = df.copy()

    # Safe numeric 'point' series (exists even if df has no 'point' col)
    if point_col in out.columns:
        pt = pd.to_numeric(out[point_col], errors="coerce")
    else:
        pt = pd.Series(np.nan, index=out.index, dtype="float64")

    is_spread = out[market_col].eq("spreads")
    is_totals = out[market_col].eq("totals")

    pair_key = np.zeros(len(out), dtype="float64")
    pair_key[is_spread.values] = np.abs(pt[is_spread].astype(float))
    pair_key[is_totals.values] = pt[is_totals].astype(float)
    out["_pair_key"] = pair_key

    # Ensure fv_* columns exist
    for b in books:
        col = f"fv_{b}"
        if col not in out.columns:
            out[col] = np.nan

    # Devig inside each (game, market, pair_key) group
    for _, idx in out.groupby(["game_id", market_col, "_pair_key"], sort=False).groups.items():
        sub = out.loc[idx]
        for b in books:
            pcol = f"p_{b}"
            fcol = f"fv_{b}"
            if pcol not in sub.columns:
                continue
            pvals = sub[pcol].astype(float).to_numpy()
            mask = np.isfinite(pvals)
            if mask.sum() < 2:
                continue  # only one side → can't devig
            fair = _choose_devig(pvals[mask])
            out.loc[sub.index[mask], fcol] = fair

    out.drop(columns=["_pair_key"], inplace=True)
    return out



###############PINNACLE EQUIVALENT LINES
import json, numpy as np
from pathlib import Path

# ----- shared math
def _logit(p, eps=1e-12):
    p = np.clip(np.asarray(p, float), eps, 1 - eps)
    return np.log(p/(1 - p))

def _sigmoid(z):
    return 1.0/(1.0 + np.exp(-z))

# ----- load your saved mappings
def _load_mapping(curve_id: str, dirpath: str = "mappings") -> dict:
    p = Path(dirpath) / curve_id
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

# ----- build curves from mapping payloads
_DEFAULT_SPREAD_WINDOWS = [
    {"name": "gamma_m3", "a": -3.5, "b": -2.5},
    {"name": "gamma_0",  "a": -1.0, "b":  1.0},
    {"name": "gamma_3",  "a":  2.5, "b":  3.5},
    {"name": "gamma_7",  "a":  6.5, "b":  7.5},
    {"name": "gamma_10", "a":  9.5, "b": 10.5},
]

def _make_totals_curve(payload: dict):
    beta = float(payload["beta_global"])
    print(beta)
    def z(s):  # non-centered
        s = np.asarray(s, float)
        return beta * s
    return z

def _make_spreads_curve(payload: dict):
    beta = float(payload["beta_global"])
    windows = payload.get("windows", _DEFAULT_SPREAD_WINDOWS)
    gammas = {w["name"]: float(payload.get(f'{w["name"]}_global', 0.0)) for w in windows}

    def _B(x, a, b):
        x = np.asarray(x, float)
        return np.maximum(0.0, x - a) - np.maximum(0.0, x - b)

    def z(s):  # non-centered global logit shape
        s = np.asarray(s, float)
        out = beta * s
        for w in windows:
            g = gammas.get(w["name"], 0.0)
            if g:
                out += g * _B(s, w["a"], w["b"])
        return out
    return z

# odds_engine.py

def drop_games_without_any_pinnacle(wide: pd.DataFrame) -> pd.DataFrame:
    """
    Remove whole games where Pinnacle never posted anything (no p_pinnacle anywhere).
    Call this BEFORE fill_missing_fv_pinnacle_from_globals().
    """
    if "p_pinnacle" not in wide.columns:
        return wide

    keep_game = wide.groupby("game_id")["p_pinnacle"].transform("any")  # any non-null in game
    return wide[keep_game].reset_index(drop=True)


def fill_missing_fv_pinnacle_from_globals(
    wide: pd.DataFrame,
    *,
    totals_curve_id: str = "NFL_totals",
    spreads_curve_id: str = "NFL_spreads",
    mappings_dir: str = "mappings",
) -> pd.DataFrame:
    if "fv_pinnacle" not in wide.columns:
        return wide

    out = wide.copy()
    if "point" in out.columns:
        out["point"] = pd.to_numeric(out["point"], errors="coerce")

    # --- load mappings
    tot_payload = _load_mapping(totals_curve_id, mappings_dir)
    spr_payload = _load_mapping(spreads_curve_id, mappings_dir)

    # totals curve: z_tot(t) = beta * t
    beta_tot = float(tot_payload["beta_global"])   # should be negative
    def z_tot(t): return beta_tot * np.asarray(t, float)

    # spreads curve: z_spr(s) = beta*s + sum gamma*B(s)
    z_spr = _make_spreads_curve(spr_payload)       # already non-centered

    # ---------------- TOTALS (Over modeled; Under = 1-Over) ----------------
    m_tot = (out["market"] == "totals") & out["point"].notna()
    if m_tot.any():
        gtot = out[m_tot].copy()

        for gid, g in gtot.groupby("game_id"):
            pin = g[g["fv_pinnacle"].notna()]
            if pin.empty:
                continue

            # choose anchor row closest to 50/50
            pin = pin.assign(_logit=_logit(pin["fv_pinnacle"].values))
            r = pin.loc[pin["_logit"].abs().idxmin()]

            t0 = float(r["point"])
            p0 = float(r["fv_pinnacle"])
            team_txt = str(r.get("team", "")).strip().lower()

            # convert anchor to OVER prob if the row is Under
            if team_txt.startswith("under"):
                p0 = 1.0 - p0
            z0 = _logit(p0)

            # delta form: z_over(t) = z0 + beta*(t - t0)
            rows = g.index
            t = g.loc[rows, "point"].astype(float).values
            z_over = z0 + beta_tot * (t - t0)
            p_over = _sigmoid(z_over)

            # flip for Under rows
            team_ser = g.loc[rows, "team"].astype(str).str.strip().str.lower()
            is_over = team_ser.str.startswith("over").to_numpy()
            p_fill = np.where(is_over, p_over, 1.0 - p_over)

            mask = out.loc[rows, "fv_pinnacle"].isna().values
            out.loc[rows[mask], "fv_pinnacle"] = p_fill[mask]

    # ---------------- SPREADS (Underdog modeled; Favorite = 1 - Underdog) ---
    m_spr = (out["market"] == "spreads") & out["point"].notna()
    if m_spr.any():
        gspr = out[m_spr].copy()

        for gid, g in gspr.groupby("game_id"):
            pin = g[g["fv_pinnacle"].notna()]
            if pin.empty:
                continue

            # pick anchor closest to 50/50
            pin = pin.assign(_logit=_logit(pin["fv_pinnacle"].values))
            r = pin.loc[pin["_logit"].abs().idxmin()]

            s0 = abs(float(r["point"]))               # underdog magnitude
            p0_dog = float(r["fv_pinnacle"])
            if float(r["point"]) < 0:                 # favorite row → convert
                p0_dog = 1.0 - p0_dog
            z0_dog = _logit(p0_dog)

            # delta form: z_dog(s) = z0_dog + ( z_spr(s) - z_spr(s0) )
            rows = g.index
            s = g.loc[rows, "point"].astype(float).values
            s_abs = np.abs(s)
            z_dog = z0_dog + (z_spr(s_abs) - z_spr(np.array([s0]))[0])
            p_dog = _sigmoid(z_dog)

            # map to row side
            p_row = np.where(s >= 0, p_dog, 1.0 - p_dog)

            mask = out.loc[rows, "fv_pinnacle"].isna().values
            out.loc[rows[mask], "fv_pinnacle"] = p_row[mask]

    return out




###############################################################################
# 6. WEIGHTING STRATEGIES
###############################################################################

class FootballWeights:
    """
    Weighting for football:
      - If Pinnacle present: 80% Pin + 10% FanDuel + 10% soft median (excluding FanDuel by default)
      - If no Pinnacle but FanDuel present: 50% FanDuel + 50% soft median
      - If neither present: soft median only
    """
    def __init__(self, soft_books: List[str], fanduel: str = "fanduel", include_fd_in_median: bool = False):
        # exclude FanDuel from the median to avoid double-counting it in the 10% FD leg
        self.fanduel = fanduel
        self.include_fd_in_median = include_fd_in_median
        self.soft_for_median = (
            soft_books if include_fd_in_median else [b for b in soft_books if b != fanduel]
        )

    def _soft_median(self, row: pd.Series):
        vals = [row.get(f"fv_{b}", _DEF_NAN) for b in self.soft_for_median]
        vals = [v for v in vals if not np.isnan(v)]
        return np.median(vals) if vals else _DEF_NAN

    def __call__(self, row: pd.Series):
        fv_pin = row.get("fv_pinnacle", _DEF_NAN)
        fv_fd  = row.get(f"fv_{self.fanduel}", _DEF_NAN)
        fv_med = self._soft_median(row)

        def wavg(weight_value_pairs):
            present = [(w, v) for (w, v) in weight_value_pairs if not np.isnan(v)]
            if not present:
                return _DEF_NAN
            tw = sum(w for w, _ in present)
            return sum((w / tw) * v for w, v in present)

        # Case 1: Pinnacle present → 80/10/10 with graceful renormalization if a leg is missing
        if not np.isnan(fv_pin):
            return wavg([(0.80, fv_pin), (0.10, fv_fd), (0.10, fv_med)])

        # Case 2: No Pinnacle, FanDuel present → 50/50
        if not np.isnan(fv_fd):
            return wavg([(0.50, fv_fd), (0.50, fv_med)])

        # Case 3: Neither Pinnacle nor FanDuel → soft median only
        return fv_med



class MLBWeights:
    """Use Pinnacle when present else median soft."""
    def __init__(self, soft_books: List[str]):
        self.soft = soft_books

    def __call__(self, row: pd.Series):
        fv_pin = row.get("fv_pinnacle", _DEF_NAN)
        if not np.isnan(fv_pin):
            return fv_pin
        vals = [row.get(f"fv_{b}", _DEF_NAN) for b in self.soft]
        vals = [v for v in vals if not np.isnan(v)]
        return np.median(vals) if vals else _DEF_NAN



class CombatWeights:
    """
    Replicates the original `sharp_prob` logic for BOTH
    'mma_mixed_martial_arts' and 'boxing_boxing'.

    • For MMA:
        – If both Pinnacle & BetOnline present → 0.7*Pin + 0.3*BOL
        – If Pin only  → 0.9*Pin + 0.1*soft-median   (if soft exists)
        – If BOL only → 0.7*BOL + 0.3*soft-median    (if soft exists)
    • For Boxing:
        – Pin present → 0.9*Pin + 0.1*soft-median   (if soft exists)
        – Else        → soft-median  (if ≥ min_soft books)
    """

    def __init__(self, soft_books: List[str], min_soft: int = 3):
        self.soft      = soft_books
        self.min_soft  = min_soft

    # ---------- helper ------------------------------------------------------
    def _soft_median(self, row: pd.Series) -> float:
        vals = [row.get(f"fv_{b}", _DEF_NAN) for b in self.soft]
        vals = [v for v in vals if not np.isnan(v)]
        return np.median(vals) if len(vals) >= self.min_soft else _DEF_NAN

    # ---------- main callable -----------------------------------------------
    def __call__(self, row: pd.Series) -> float:
        sport = row.get("sport", "")
        pin   = row.get("fv_pinnacle",     _DEF_NAN)
        bol   = row.get("fv_betonlineag",  _DEF_NAN)
        soft  = self._soft_median(row)

        has_pin  = not np.isnan(pin)
        has_bol  = not np.isnan(bol)
        has_soft = not np.isnan(soft)

        # ---------- MMA ----------
        if sport == "mma_mixed_martial_arts":
            if has_pin and has_bol:
                return 0.7 * pin + 0.3 * bol
            if has_pin:
                return 0.9 * pin + 0.1 * soft if has_soft else pin
            if has_bol:
                return 0.7 * bol + 0.3 * soft if has_soft else bol
            return _DEF_NAN

        # ---------- BOXING ----------
        if sport == "boxing_boxing":
            if has_pin:
                return 0.9 * pin + 0.1 * soft if has_soft else pin
            return soft if has_soft else _DEF_NAN

        # Fallback for any other sport (shouldn't happen here)
        return _DEF_NAN


class SoccerWeights:
    """Return Pinnacle’s fair prob when available, else soft-book median."""
    def __init__(self, soft_books: List[str], cutoff_days: float = 0):
        self.soft = soft_books
        self.cut  = cutoff_days        # kept for API compatibility

    def __call__(self, row: pd.Series) -> float:
        pin = row.get("fv_pinnacle", _DEF_NAN)

        if not np.isnan(pin):          # Pinnacle present → use it
            return pin

        # ---------- fall-back: median of softs ----------
        vals = [row.get(f"fv_{b}", _DEF_NAN) for b in self.soft]
        vals = [v for v in vals if not np.isnan(v)]
        return np.median(vals) if vals else _DEF_NAN


class TennisWeights:
    """95 % Pinnacle, 5 % median soft (falls back gracefully)."""
    def __init__(self, soft_books: List[str], alpha: float = 0.95):
        self.soft  = soft_books
        self.alpha = alpha          # weight on Pinnacle

    def __call__(self, row: pd.Series):
        fv_pin = row.get("fv_pinnacle", _DEF_NAN)

        # median of whatever soft books are present
        vals = [row.get(f"fv_{b}", _DEF_NAN) for b in self.soft]
        vals = [v for v in vals if not np.isnan(v)]
        fv_soft = np.median(vals) if vals else _DEF_NAN

        # ----- fallback logic -----
        if np.isnan(fv_pin) and np.isnan(fv_soft):
            return _DEF_NAN
        if np.isnan(fv_pin):
            return fv_soft
        if np.isnan(fv_soft):
            return fv_pin

        # weighted blend
        return self.alpha * fv_pin + (1.0 - self.alpha) * fv_soft


class HockeyWeights:
    """
    NHL weighting: use Pinnacle’s fair probability when available,
    otherwise fall back to the median of the US soft books you pass in.
    Mirrors SoccerWeights for now (easy to tweak later).
    """
    def __init__(self, soft_books: List[str], cutoff_days: float = 0):
        self.soft = soft_books
        self.cut  = cutoff_days  # kept for API compatibility / future use

    def __call__(self, row: pd.Series) -> float:
        pin = row.get("fv_pinnacle", _DEF_NAN)
        if not np.isnan(pin):
            return pin

        vals = [row.get(f"fv_{b}", _DEF_NAN) for b in self.soft]
        vals = [v for v in vals if not np.isnan(v)]
        return np.median(vals) if vals else _DEF_NAN


# --- NEW: Basketball weights -----------------------------------------------
class BasketballWeights:
    """
    For NBA/NCAAB: use the median of all available fair values on the row.
    Includes Pinnacle if fv_pinnacle exists, and any soft books that exist.
    """
    def __init__(self, books: list[str]):
        # pass in soft_books + ["pinnacle"] (or any others you want included)
        self.books = list(dict.fromkeys(books))  # de-dupe, keep order

    def __call__(self, row: pd.Series) -> float:
        vals = []
        for b in self.books:
            v = row.get(f"fv_{b}")
            if pd.notna(v):
                vals.append(float(v))

        return float(np.median(vals)) if vals else np.nan




###############################################################################
# 7. SHARP PROBABILITY WRAPPER
###############################################################################

def build_sharp_prob(wide: pd.DataFrame, weighting: Callable[[pd.Series], float]) -> pd.DataFrame:
    wide["sharp_p"] = wide.apply(weighting, axis=1)
    wide["sharp_odds"] = 1 / wide["sharp_p"]
    return wide

###############################################################################
# 8. BEST SOFT PRICE, EV, KELLY, SHARPE
###############################################################################

#def pick_best_soft_price(wide: pd.DataFrame, soft_books: List[str]) -> pd.DataFrame:
#    soft_p_cols = [f"p_{b}" for b in soft_books]
#    wide["best_col"] = wide[soft_p_cols].idxmin(axis=1)
#    wide = wide[wide["best_col"].notna()].copy()
#    wide["best_book"] = wide["best_col"].str.removeprefix("p_")
#    col_idx = wide.columns.get_indexer(wide["best_col"])
#    wide["best_ip"] = wide.to_numpy()[np.arange(len(wide)), col_idx]
#    return wide

def pick_best_soft_price(wide: pd.DataFrame, soft_books: List[str]) -> pd.DataFrame:
    """
    Set `best_book` to a CSV of all soft books whose implied probability equals
    the row-min across soft books (i.e., tied for best decimal odds).
    Keeps existing `best_col` (single primary) and `best_ip` logic unchanged.
    """
    # only keep p_<book> columns that actually exist
#    soft_p_cols = [f"p_{b}" for b in soft_books if f"p_{b}" in wide.columns]
#    if not soft_p_cols:
  #      return wide

 #   out = wide.copy()

    # Primary best column (deterministic tie-break via column order)
#    out["best_col"] = out[soft_p_cols].idxmin(axis=1)
#    out = out[out["best_col"].notna()].copy()

    # best_ip from best_col (unchanged)
#    col_idx = out.columns.get_indexer(out["best_col"])
#    out["best_ip"] = out.to_numpy()[np.arange(len(out)), col_idx]

    # CSV of all books tied for best (min implied prob)
#    row_min = out[soft_p_cols].min(axis=1)
#    eq = out[soft_p_cols].eq(row_min, axis=0)  # True where p_<book> == row_min

    # deterministic order follows soft_books
#    ordered_pcols = [c for c in soft_p_cols if c in eq.columns]
#    out["best_book"] = eq[ordered_pcols].apply(
#        lambda r: ", ".join([c.removeprefix("p_") for c, ok in r.items() if ok]),
#        axis=1,
#    )

#    return out

def pick_best_soft_price(wide: pd.DataFrame, soft_books: List[str]) -> pd.DataFrame:
    """
    Find the soft book(s) offering the best price (min implied probability).
    Robust to rows where all soft prices are NaN.
    Produces:
      - best_col : one p_<book> column name (deterministic tie-break)
      - best_book: CSV of all books tied for best
      - best_ip  : the min implied probability for that row
    """
    # only keep p_<book> columns that actually exist
    soft_p_cols = [f"p_{b}" for b in soft_books if f"p_{b}" in wide.columns]
    if not soft_p_cols:
        # nothing to choose from
        wide = wide.copy()
        wide["best_col"] = np.nan
        wide["best_book"] = pd.NA
        wide["best_ip"] = np.nan
        return wide

    out = wide.copy()

    # rows that have at least one finite soft price
    valid = out[soft_p_cols].notna().any(axis=1)

    # compute row-min safely
    row_min = out.loc[valid, soft_p_cols].min(axis=1, skipna=True)

    # choose a primary best column with fillna(+inf) so idxmin never errors
    filled = out.loc[valid, soft_p_cols].fillna(np.inf)
    out.loc[valid, "best_col"] = filled.idxmin(axis=1)

    # drop rows with no soft prices at all
    out = out.loc[valid].copy()

    # best_ip from the precomputed row_min
    out["best_ip"] = row_min

    # CSV of all books tied for best (deterministic order follows soft_books)
    eq = out[soft_p_cols].eq(row_min, axis=0)
    ordered = [c for c in soft_p_cols if c in eq.columns]
    out["best_book"] = eq[ordered].apply(
        lambda r: ", ".join([c.removeprefix("p_") for c, ok in r.items() if ok]),
        axis=1,
    )

    return out



def add_ev_metrics(wide: pd.DataFrame) -> pd.DataFrame:
    D = 1 / wide["best_ip"]
    wide["ev"]    = wide["sharp_p"] * (D - 1) - (1 - wide["sharp_p"])
    wide["kelly"] = ((wide["sharp_p"] * D - 1) / (D - 1)).clip(lower=0)
    wide["kelly"] = 0.5*wide["kelly"]
    denom = np.sqrt(wide["sharp_p"] * (1 - wide["sharp_p"])) * (wide["sharp_odds"] - 1)
    wide["sharpe"] = wide["ev"] / denom
    return wide

###############################################################################
# 9. HORIZON FILTER
###############################################################################

def horizon_filter(wide: pd.DataFrame, horizon_days: int) -> pd.DataFrame:
    cut = pd.Timestamp.utcnow() + pd.Timedelta(days=horizon_days)
    return wide[wide["commence_time"] <= cut].copy()

###############################################################################
# 10. PIPELINE WRAPPER (example stub)
###############################################################################

def process(
    api_key: str,
    sport_key: str,
    markets: str,
    soft_books: List[str],
    sharp_books: List[str],
    weighting: Callable[[pd.Series], float],
    *,
    capture_point: bool = False,
    pre_align_to_pin: bool = False,
    horizon_days: int = 7,
    use_pin_globals: bool = False,
    totals_curve_id: str | None = None,
    spreads_curve_id: str | None = None,
    mappings_dir: str = "mappings",
) -> pd.DataFrame:
    """End‑to‑end fetch → +EV sheet for one sport & markets."""
    books = ",".join(soft_books + sharp_books)
    url = build_odds_url(api_key, sport_key, markets, books)
    #jsn, _ = fetch_odds_json(url)
    
    #FIX
    
    resp = fetch_odds_json(url)
    if not isinstance(resp, tuple) or len(resp) != 2:
        raise RuntimeError(f"fetch_odds_json returned {type(resp)} for URL={url}")
    jsn, _ = resp

    # sport-specific buffer
    BUFFER_MAP = {
        "mma_mixed_martial_arts": 30,   # minutes
        "boxing_boxing":          30,
        "tennis_wta_wimbledon":   45,
        "tennis_atp_wimbledon":   45,
    # everything else falls back to 0
    }


    long = json_to_long(jsn, sport_key, capture_point=capture_point)
    #long.to_csv(f"debug_long_{sport_key.replace('-', '_')}.csv", index=False)
    #  EARLY EXIT ────────────────
    if long.empty:          # nothing available for this league
        return pd.DataFrame()
    
    buf = BUFFER_MAP.get(sport_key, 0)    
    long = drop_started_games(long, buffer_minutes=buf)

    if pre_align_to_pin:
        long = align_to_pin_line(long)

    idx_cols = ["sport", "game_id", "commence_time", "team", "market"]
    if "point" in long.columns and long["point"].notna().any():
        idx_cols.append("point")
        
    wide = (
        pivot_wide(long, idx_cols)
        .pipe(annotate_non_side_rows)
        .pipe(ensure_book_columns, soft_books + sharp_books)
        .pipe(add_implied_probs, soft_books + sharp_books)
        .pipe(devig_pairwise,      soft_books + sharp_books)
        .pipe(drop_games_without_any_pinnacle)
    )
    
    # run filler only when enabled for this sport (e.g., NFL)
    if use_pin_globals and (("totals" in markets) or ("spreads" in markets)):
        wide = fill_missing_fv_pinnacle_from_globals(
            wide,
            totals_curve_id = totals_curve_id,
            spreads_curve_id= spreads_curve_id,
            mappings_dir    = mappings_dir,
        )
        
    wide = (wide 
        .pipe(add_days_to_event)
        .pipe(build_sharp_prob,    weighting)
        .pipe(pick_best_soft_price, soft_books)
        #.pipe(lambda df: (df.to_csv(f"debug_wide_post_devig_{sport_key.replace('-', '_')}.csv", index=False) or df))
        .pipe(add_ev_metrics)
        .pipe(horizon_filter, horizon_days)
    )
    return wide.reset_index(drop=True)



# ---------------------------------------------------------------------------
# 11.  DATACLASS + CONFIG-LEVEL PROCESSOR
# ---------------------------------------------------------------------------
from dataclasses import dataclass, field

@dataclass
class SportConfig:
    api_key:        str
    sport_key:      List[str]
    markets:        str
    soft_books:     List[str]
    sharp_books:    List[str]
    min_soft:       int
    pre_filters:    List[Callable[[pd.DataFrame], pd.DataFrame]]
    sharp_weighting:Callable[[pd.Series], float]
    ev_hurdle:      Callable[[float], float] = lambda _: 0.0   # not used yet
    horizon_days:   int = 7
    # convenience switches
    capture_point:  bool = False          # MLB spreads/totals
    align_to_pin:   bool = False          # MLB line-match
    use_pin_globals: bool = False                     # NEW: turn the filler on/off per sport
    totals_curve_id: str | None = None               # NEW: which totals mapping file to use
    spreads_curve_id: str | None = None              # NEW: which spreads mapping file to use
    mappings_dir: str = "mappings"                   # NEW: where the mapping files live

# ---------------------------------------------------------------------------
# helper factories so run_edge_board can just `from odds_engine import …`
# ---------------------------------------------------------------------------
def football_weighting(soft: List[str], fanduel: str = "fanduel") -> Callable[[pd.Series], float]:
    """Factory to match your existing pattern."""
    return FootballWeights(soft_books=soft, fanduel=fanduel)

def mlb_weighting(soft: List[str]) -> Callable[[pd.Series], float]:
    """Return a row-callable MLB weighting function bound to soft_books."""
    return MLBWeights(soft)

def combat_weighting(soft: List[str], min_soft: int = 3) -> Callable[[pd.Series], float]:
    return CombatWeights(soft, min_soft=min_soft)

def soccer_weighting(soft: List[str], cutoff_days: float = 1.5) -> Callable[[pd.Series], float]:
    return SoccerWeights(soft, cutoff_days=cutoff_days)

def tennis_weighting(soft: List[str]) -> Callable[[pd.Series], float]:
    return TennisWeights(soft)

def hockey_weighting(soft: List[str], cutoff_days: float = 0) -> Callable[[pd.Series], float]:
    return HockeyWeights(soft, cutoff_days=cutoff_days)

def basketball_weighting(soft: List[str]) -> Callable[[pd.Series], float]:
    return BasketballWeights(soft)

# ---------------------------------------------------------------------------
def process_cfg(cfg: SportConfig) -> pd.DataFrame:
    """
    Run the pipeline for *every* key in cfg.sport_key (which may be a list),
    then concatenate the results.
    """
    frames = []
    for sk in cfg.sport_key:                     # ← iterate over each league
        frames.append(
            process(
                api_key         = cfg.api_key,
                sport_key       = sk,            # ← pass ONE key, not the list
                markets         = cfg.markets,
                soft_books      = cfg.soft_books,
                sharp_books     = cfg.sharp_books,
                weighting       = cfg.sharp_weighting,
                capture_point = cfg.capture_point or ("spreads" in cfg.markets) or ("totals" in cfg.markets),
                pre_align_to_pin= cfg.align_to_pin,
                horizon_days    = cfg.horizon_days,
                use_pin_globals = cfg.use_pin_globals,
                totals_curve_id = cfg.totals_curve_id,
                spreads_curve_id= cfg.spreads_curve_id,
                mappings_dir    = cfg.mappings_dir,
            )
        )

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

