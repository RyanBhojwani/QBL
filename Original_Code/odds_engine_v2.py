"""
odds_engine_v2.py  —  per-book EV expansion

Schema change vs. odds_engine.py
---------------------------------
v1  process() returns one row per (game, team, market, point):
        best_book, best_ip, ev, kelly, sharpe
    The single "best" soft book wins; all others are discarded.

v2  process() returns one row per (game, team, market, point, book):
        book, book_ip, book_odds, ev, kelly, sharpe
    Every soft book that posted a valid price gets its own row with
    EV/Kelly/Sharpe computed against that book's actual posted odds.

Everything upstream of step 6 (fetch, devig, Pinnacle fill,
build_sharp_prob) is IDENTICAL to odds_engine.py.  Do not touch
those functions.

Downstream note (run_edge_board.py)
------------------------------------
Columns that rename in the new output:
    best_book          ->  book
    best_ip            ->  book_ip
    odds_from_best_book->  book_odds  (already a column; no wide lookup needed)
"""

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
        f"https://api.the-odds-api.com/v4/sports/{sport}/odds?"
        f"apiKey={api_key}&bookmakers={books}&markets={markets}&oddsFormat=decimal"
    )


import time, requests
from typing import Tuple, List, Dict

def fetch_odds_json(url: str, timeout: int = 12) -> Tuple[List[Dict], Dict[str, str]]:
    """GET the Odds API v4 endpoint. Always returns (json, headers) or raises."""
    backoffs = [0, 1.0, 3.0]
    last_err = None
    for i, sleep_s in enumerate(backoffs):
        if sleep_s:
            time.sleep(sleep_s)
        try:
            resp = requests.get(url, timeout=timeout)
        except Exception as e:
            last_err = e
            continue

        if resp.status_code in (429, 500, 502, 503, 504):
            last_err = RuntimeError(
                f"HTTP {resp.status_code} from Odds API; "
                f"x-requests-remaining={resp.headers.get('x-requests-remaining')}, "
                f"x-requests-used={resp.headers.get('x-requests-used')}, "
                f"x-requests-reset={resp.headers.get('x-requests-reset')}"
            )
            continue

        if resp.status_code != 200:
            snippet = resp.text[:300].replace("\n", " ")
            raise RuntimeError(
                f"Odds API HTTP {resp.status_code}: {snippet} | "
                f"headers={{'x-requests-remaining': {resp.headers.get('x-requests-remaining')}, "
                f"'x-requests-used': {resp.headers.get('x-requests-used')}, "
                f"'x-requests-reset': {resp.headers.get('x-requests-reset')}}}"
            )

        text = (resp.text or "").strip()
        if not text:
            return [], resp.headers
        try:
            return resp.json(), resp.headers  # type: ignore[return-value]
        except ValueError as e:
            raise RuntimeError(f"Invalid JSON from Odds API: {text[:300]}") from e

    raise RuntimeError(f"Failed to fetch Odds API after retries: {last_err}")

###############################################################################
# 2. FLATTEN JSON  →  LONG DATAFRAME
###############################################################################

def json_to_long(
    json_blob: List[Dict],
    sport_key: str,
    capture_point: bool = False,
) -> pd.DataFrame:
    """Flatten Odds‑API JSON into one row per outcome."""
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
    if not rows:
        return pd.DataFrame()

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
    atol: float = 1e-3,
) -> pd.DataFrame:
    """MLB-specific: keep only rows whose point matches Pinnacle's line."""
    pin = long_df[long_df["bookmaker"] == "pinnacle"]

    spread_pts = (
        pin.loc[pin["market"] == "spreads", ["game_id", "team", "point"]]
            .rename(columns={"point": "pin_point_spread"})
    )
    total_pts = (
        pin.loc[pin["market"] == "totals", ["game_id", "point"]]
            .drop_duplicates("game_id")
            .rename(columns={"point": "pin_point_total"})
    )

    df = (
        long_df
        .merge(spread_pts, on=["game_id", "team"], how="left")
        .merge(total_pts,  on="game_id",       how="left")
    )

    df.loc[df["market"] != "spreads", "pin_point_spread"] = np.nan
    df.loc[df["market"] != "totals",  "pin_point_total"]  = np.nan
    df["pin_point"] = np.where(
        df["market"] == "totals",
        df["pin_point_total"],
        df["pin_point_spread"],
    )

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
    soft_cols = [b for b in soft_books if b in df.columns]
    if not soft_cols:
        return df.iloc[0:0]
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
    if "point" in idx_cols:
        long_df = long_df.copy()
        long_df["point"] = long_df["point"].fillna(0.0)
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


def annotate_non_side_rows(wide: pd.DataFrame) -> pd.DataFrame:
    """Replace Over/Under/Draw labels with '<label> (Team A vs. Team B)'."""
    def _is_non_side_val(x: object) -> bool:
        s = str(x)
        return (s == "Draw") or s.startswith("Over") or s.startswith("Under")

    df = wide.copy()
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()].copy()

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


def _power_log_devig(raw_probs: np.ndarray,
                     tol: float = 1e-12,
                     max_iter: int = 100) -> np.ndarray:
    if abs(raw_probs.sum() - 1.0) < tol:
        return raw_probs / raw_probs.sum()
    lo, hi = 0.10, 10.0
    for _ in range(max_iter):
        mid = (lo + hi) / 2
        s = (raw_probs ** mid).sum()
        if s > 1:
            lo = mid
        else:
            hi = mid
    tau = (lo + hi) / 2
    fair = raw_probs ** tau
    return fair / fair.sum()


def _logistic_devig(raw_probs: np.ndarray,
                    tol: float = 1e-12,
                    max_iter: int = 100) -> np.ndarray:
    eps   = 1e-12
    r     = np.clip(raw_probs, eps, 1 - eps)
    logit = np.log(r / (1.0 - r))

    def _sum_p(k: float) -> float:
        return (1.0 / (1.0 + np.exp(-(logit - k)))).sum()

    lo, hi = -10.0, 10.0
    for _ in range(max_iter):
        mid = (lo + hi) / 2
        if _sum_p(mid) > 1.0:
            lo = mid
        else:
            hi = mid
    k    = (lo + hi) / 2
    fair = 1.0 / (1.0 + np.exp(-(logit - k)))
    return fair / fair.sum()


def _choose_devig(raw_probs: np.ndarray) -> np.ndarray:
    if (raw_probs.size == 2
        and raw_probs.max() <= 0.60
        and raw_probs.min() >= 0.40):
        return _logistic_devig(raw_probs)
    else:
        return _power_log_devig(raw_probs)


def devig_pairwise(df: pd.DataFrame, books: list[str],
                   market_col: str = "market",
                   point_col: str = "point") -> pd.DataFrame:
    """Create fair-prob columns fv_<book> by devigging within each (game, market, pair_key) group."""
    out = df.copy()

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

    for b in books:
        col = f"fv_{b}"
        if col not in out.columns:
            out[col] = np.nan

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
                continue
            fair = _choose_devig(pvals[mask])
            out.loc[sub.index[mask], fcol] = fair

    out.drop(columns=["_pair_key"], inplace=True)
    return out


###############################################################################
# PINNACLE EQUIVALENT LINES
###############################################################################

import json
from pathlib import Path

def _logit(p, eps=1e-12):
    p = np.clip(np.asarray(p, float), eps, 1 - eps)
    return np.log(p/(1 - p))

def _sigmoid(z):
    return 1.0/(1.0 + np.exp(-z))

def _load_mapping(curve_id: str, dirpath: str = "mappings") -> dict:
    p = Path(dirpath) / curve_id
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

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
    def z(s):
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

    def z(s):
        s = np.asarray(s, float)
        out = beta * s
        for w in windows:
            g = gammas.get(w["name"], 0.0)
            if g:
                out += g * _B(s, w["a"], w["b"])
        return out
    return z


def drop_games_without_any_pinnacle(wide: pd.DataFrame) -> pd.DataFrame:
    if "p_pinnacle" not in wide.columns:
        return wide
    keep_game = wide.groupby("game_id")["p_pinnacle"].transform("any")
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

    tot_payload = _load_mapping(totals_curve_id, mappings_dir)
    spr_payload = _load_mapping(spreads_curve_id, mappings_dir)

    beta_tot = float(tot_payload["beta_global"])
    def z_tot(t): return beta_tot * np.asarray(t, float)

    z_spr = _make_spreads_curve(spr_payload)

    # TOTALS
    m_tot = (out["market"] == "totals") & out["point"].notna()
    if m_tot.any():
        gtot = out[m_tot].copy()
        for gid, g in gtot.groupby("game_id"):
            pin = g[g["fv_pinnacle"].notna()]
            if pin.empty:
                continue
            pin = pin.assign(_logit=_logit(pin["fv_pinnacle"].values))
            r = pin.loc[pin["_logit"].abs().idxmin()]
            t0 = float(r["point"])
            p0 = float(r["fv_pinnacle"])
            team_txt = str(r.get("team", "")).strip().lower()
            if team_txt.startswith("under"):
                p0 = 1.0 - p0
            z0 = _logit(p0)
            rows = g.index
            t = g.loc[rows, "point"].astype(float).values
            z_over = z0 + beta_tot * (t - t0)
            p_over = _sigmoid(z_over)
            team_ser = g.loc[rows, "team"].astype(str).str.strip().str.lower()
            is_over = team_ser.str.startswith("over").to_numpy()
            p_fill = np.where(is_over, p_over, 1.0 - p_over)
            mask = out.loc[rows, "fv_pinnacle"].isna().values
            out.loc[rows[mask], "fv_pinnacle"] = p_fill[mask]

    # SPREADS
    m_spr = (out["market"] == "spreads") & out["point"].notna()
    if m_spr.any():
        gspr = out[m_spr].copy()
        for gid, g in gspr.groupby("game_id"):
            pin = g[g["fv_pinnacle"].notna()]
            if pin.empty:
                continue
            pin = pin.assign(_logit=_logit(pin["fv_pinnacle"].values))
            r = pin.loc[pin["_logit"].abs().idxmin()]
            s0 = abs(float(r["point"]))
            p0_dog = float(r["fv_pinnacle"])
            if float(r["point"]) < 0:
                p0_dog = 1.0 - p0_dog
            z0_dog = _logit(p0_dog)
            rows = g.index
            s = g.loc[rows, "point"].astype(float).values
            s_abs = np.abs(s)
            z_dog = z0_dog + (z_spr(s_abs) - z_spr(np.array([s0]))[0])
            p_dog = _sigmoid(z_dog)
            p_row = np.where(s >= 0, p_dog, 1.0 - p_dog)
            mask = out.loc[rows, "fv_pinnacle"].isna().values
            out.loc[rows[mask], "fv_pinnacle"] = p_row[mask]

    return out


###############################################################################
# 6. WEIGHTING STRATEGIES  (unchanged from odds_engine.py)
###############################################################################

class FootballWeights:
    def __init__(self, soft_books: List[str], fanduel: str = "fanduel", include_fd_in_median: bool = False):
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

        if not np.isnan(fv_pin):
            return wavg([(0.80, fv_pin), (0.10, fv_fd), (0.10, fv_med)])
        if not np.isnan(fv_fd):
            return wavg([(0.50, fv_fd), (0.50, fv_med)])
        return fv_med


class MLBWeights:
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
    def __init__(self, soft_books: List[str], min_soft: int = 3):
        self.soft      = soft_books
        self.min_soft  = min_soft

    def _soft_median(self, row: pd.Series) -> float:
        vals = [row.get(f"fv_{b}", _DEF_NAN) for b in self.soft]
        vals = [v for v in vals if not np.isnan(v)]
        return np.median(vals) if len(vals) >= self.min_soft else _DEF_NAN

    def __call__(self, row: pd.Series) -> float:
        sport = row.get("sport", "")
        pin   = row.get("fv_pinnacle",     _DEF_NAN)
        bol   = row.get("fv_betonlineag",  _DEF_NAN)
        soft  = self._soft_median(row)

        has_pin  = not np.isnan(pin)
        has_bol  = not np.isnan(bol)
        has_soft = not np.isnan(soft)

        if sport == "mma_mixed_martial_arts":
            if has_pin and has_bol:
                return 0.7 * pin + 0.3 * bol
            if has_pin:
                return 0.9 * pin + 0.1 * soft if has_soft else pin
            if has_bol:
                return 0.7 * bol + 0.3 * soft if has_soft else bol
            return _DEF_NAN

        if sport == "boxing_boxing":
            if has_pin:
                return 0.9 * pin + 0.1 * soft if has_soft else pin
            return soft if has_soft else _DEF_NAN

        return _DEF_NAN


class SoccerWeights:
    def __init__(self, soft_books: List[str], cutoff_days: float = 0):
        self.soft = soft_books
        self.cut  = cutoff_days

    def __call__(self, row: pd.Series) -> float:
        pin = row.get("fv_pinnacle", _DEF_NAN)
        if not np.isnan(pin):
            return pin
        vals = [row.get(f"fv_{b}", _DEF_NAN) for b in self.soft]
        vals = [v for v in vals if not np.isnan(v)]
        return np.median(vals) if vals else _DEF_NAN


class TennisWeights:
    def __init__(self, soft_books: List[str], alpha: float = 0.95):
        self.soft  = soft_books
        self.alpha = alpha

    def __call__(self, row: pd.Series):
        fv_pin = row.get("fv_pinnacle", _DEF_NAN)
        vals = [row.get(f"fv_{b}", _DEF_NAN) for b in self.soft]
        vals = [v for v in vals if not np.isnan(v)]
        fv_soft = np.median(vals) if vals else _DEF_NAN

        if np.isnan(fv_pin) and np.isnan(fv_soft):
            return _DEF_NAN
        if np.isnan(fv_pin):
            return fv_soft
        if np.isnan(fv_soft):
            return fv_pin
        return self.alpha * fv_pin + (1.0 - self.alpha) * fv_soft


class HockeyWeights:
    def __init__(self, soft_books: List[str], cutoff_days: float = 0):
        self.soft = soft_books
        self.cut  = cutoff_days

    def __call__(self, row: pd.Series) -> float:
        pin = row.get("fv_pinnacle", _DEF_NAN)
        if not np.isnan(pin):
            return pin
        vals = [row.get(f"fv_{b}", _DEF_NAN) for b in self.soft]
        vals = [v for v in vals if not np.isnan(v)]
        return np.median(vals) if vals else _DEF_NAN


class BasketballWeights:
    def __init__(self, books: list[str]):
        self.books = list(dict.fromkeys(books))

    def __call__(self, row: pd.Series) -> float:
        vals = []
        for b in self.books:
            v = row.get(f"fv_{b}")
            if pd.notna(v):
                vals.append(float(v))
        return float(np.median(vals)) if vals else np.nan


###############################################################################
# 7. SHARP PROBABILITY WRAPPER  (unchanged)
###############################################################################

def build_sharp_prob(wide: pd.DataFrame, weighting: Callable[[pd.Series], float]) -> pd.DataFrame:
    wide["sharp_p"]    = wide.apply(weighting, axis=1)
    wide["sharp_odds"] = 1 / wide["sharp_p"]
    return wide

###############################################################################
# 8-NEW. PER-BOOK EXPANSION  (replaces pick_best_soft_price + add_ev_metrics)
###############################################################################

def expand_per_book(
    wide: pd.DataFrame,
    soft_books: List[str],
) -> pd.DataFrame:
    """
    Convert one-row-per-outcome wide DataFrame into one-row-per-(outcome, book).

    For each soft book that posted a valid price on an outcome, a separate row
    is produced with EV/Kelly/Sharpe computed against that book's actual price.

    Parameters
    ----------
    wide       : post-build_sharp_prob wide DataFrame; must contain sharp_p,
                 sharp_odds, days_to_event, and p_<book> for each book in soft_books.
    soft_books : the soft books to expand over.

    Returns
    -------
    DataFrame with columns:
        sport, game_id, commence_time, team, market, point,
        days_to_event, sharp_p, sharp_odds,
        book, book_ip, book_odds, ev, kelly, sharpe
    """
    id_cols = [c for c in [
        "sport", "game_id", "commence_time", "team", "market", "point",
        "days_to_event", "sharp_p", "sharp_odds",
    ] if c in wide.columns]

    soft_p_cols = [f"p_{b}" for b in soft_books if f"p_{b}" in wide.columns]
    if not soft_p_cols:
        return pd.DataFrame()

    # Melt to long: one row per (outcome, soft book)
    long = (
        wide[id_cols + soft_p_cols]
        .melt(
            id_vars=id_cols,
            value_vars=soft_p_cols,
            var_name="_book_col",
            value_name="book_ip",
        )
    )

    # Drop outcomes where this book had no price
    long = long.dropna(subset=["book_ip"]).copy()
    if long.empty:
        return pd.DataFrame()

    long["book"]      = long["_book_col"].str.removeprefix("p_")
    long["book_odds"] = 1.0 / long["book_ip"].astype(float)
    long = long.drop(columns="_book_col")

    # EV / Kelly / Sharpe per (outcome, book)
    D  = long["book_odds"].astype(float)
    sp = long["sharp_p"].astype(float)

    long["ev"]    = sp * (D - 1.0) - (1.0 - sp)
    raw_kelly     = (sp * D - 1.0) / (D - 1.0)
    long["kelly"] = (0.5 * raw_kelly).clip(lower=0.0)
    denom         = np.sqrt(sp * (1.0 - sp)) * (long["sharp_odds"].astype(float) - 1.0)
    long["sharpe"] = long["ev"] / denom

    return long.reset_index(drop=True)


###############################################################################
# 8-LEGACY. SINGLE-BOOK HELPERS  (kept for reference; not used in process())
###############################################################################

def pick_best_soft_price(wide: pd.DataFrame, soft_books: List[str]) -> pd.DataFrame:
    """Legacy: single best-book selection.  Not called by process() in v2."""
    soft_p_cols = [f"p_{b}" for b in soft_books if f"p_{b}" in wide.columns]
    if not soft_p_cols:
        wide = wide.copy()
        wide["best_col"]  = np.nan
        wide["best_book"] = pd.NA
        wide["best_ip"]   = np.nan
        return wide

    out = wide.copy()
    valid   = out[soft_p_cols].notna().any(axis=1)
    row_min = out.loc[valid, soft_p_cols].min(axis=1, skipna=True)
    filled  = out.loc[valid, soft_p_cols].fillna(np.inf)
    out.loc[valid, "best_col"] = filled.idxmin(axis=1)
    out = out.loc[valid].copy()
    out["best_ip"] = row_min
    eq      = out[soft_p_cols].eq(row_min, axis=0)
    ordered = [c for c in soft_p_cols if c in eq.columns]
    out["best_book"] = eq[ordered].apply(
        lambda r: ", ".join([c.removeprefix("p_") for c, ok in r.items() if ok]),
        axis=1,
    )
    return out


def add_ev_metrics(wide: pd.DataFrame) -> pd.DataFrame:
    """Legacy: EV against best_ip.  Not called by process() in v2."""
    D = 1 / wide["best_ip"]
    wide["ev"]    = wide["sharp_p"] * (D - 1) - (1 - wide["sharp_p"])
    wide["kelly"] = ((wide["sharp_p"] * D - 1) / (D - 1)).clip(lower=0)
    wide["kelly"] = 0.5 * wide["kelly"]
    denom = np.sqrt(wide["sharp_p"] * (1 - wide["sharp_p"])) * (wide["sharp_odds"] - 1)
    wide["sharpe"] = wide["ev"] / denom
    return wide

###############################################################################
# 9. HORIZON FILTER  (unchanged)
###############################################################################

def horizon_filter(wide: pd.DataFrame, horizon_days: int) -> pd.DataFrame:
    cut = pd.Timestamp.utcnow() + pd.Timedelta(days=horizon_days)
    return wide[wide["commence_time"] <= cut].copy()

###############################################################################
# 10. PIPELINE WRAPPER
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
    """
    End-to-end fetch → per-book EV sheet for one sport & markets.

    Returns one row per (outcome, soft book) that had a valid price.
    No EV filtering is applied here — the caller (run_edge_board) filters.

    Output columns:
        sport, game_id, commence_time, team, market, point,
        days_to_event, sharp_p, sharp_odds,
        book, book_ip, book_odds, ev, kelly, sharpe
    """
    books = ",".join(soft_books + sharp_books)
    url   = build_odds_url(api_key, sport_key, markets, books)

    resp = fetch_odds_json(url)
    if not isinstance(resp, tuple) or len(resp) != 2:
        raise RuntimeError(f"fetch_odds_json returned {type(resp)} for URL={url}")
    jsn, _ = resp

    BUFFER_MAP = {
        "mma_mixed_martial_arts": 30,
        "boxing_boxing":          30,
        "tennis_wta_wimbledon":   45,
        "tennis_atp_wimbledon":   45,
    }

    long = json_to_long(jsn, sport_key, capture_point=capture_point)
    if long.empty:
        return pd.DataFrame()

    buf  = BUFFER_MAP.get(sport_key, 0)
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
        .pipe(add_implied_probs,   soft_books + sharp_books)
        .pipe(devig_pairwise,      soft_books + sharp_books)
        .pipe(drop_games_without_any_pinnacle)
    )

    if use_pin_globals and (("totals" in markets) or ("spreads" in markets)):
        wide = fill_missing_fv_pinnacle_from_globals(
            wide,
            totals_curve_id  = totals_curve_id,
            spreads_curve_id = spreads_curve_id,
            mappings_dir     = mappings_dir,
        )

    # Apply horizon filter while still wide (fewer rows to melt)
    wide = (
        wide
        .pipe(add_days_to_event)
        .pipe(build_sharp_prob, weighting)
        .pipe(horizon_filter,   horizon_days)
    )

    # Expand: one row per (outcome, soft book) with per-book EV stats
    return expand_per_book(wide, soft_books)


###############################################################################
# 11. DATACLASS + CONFIG-LEVEL PROCESSOR  (unchanged)
###############################################################################

from dataclasses import dataclass, field

@dataclass
class SportConfig:
    api_key:         str
    sport_key:       List[str]
    markets:         str
    soft_books:      List[str]
    sharp_books:     List[str]
    min_soft:        int
    pre_filters:     List[Callable[[pd.DataFrame], pd.DataFrame]]
    sharp_weighting: Callable[[pd.Series], float]
    ev_hurdle:       Callable[[float], float] = lambda _: 0.0
    horizon_days:    int = 7
    capture_point:   bool = False
    align_to_pin:    bool = False
    use_pin_globals: bool = False
    totals_curve_id: str | None = None
    spreads_curve_id: str | None = None
    mappings_dir:    str = "mappings"


def football_weighting(soft: List[str], fanduel: str = "fanduel") -> Callable[[pd.Series], float]:
    return FootballWeights(soft_books=soft, fanduel=fanduel)

def mlb_weighting(soft: List[str]) -> Callable[[pd.Series], float]:
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


def process_cfg(cfg: SportConfig) -> pd.DataFrame:
    """Run process() for every sport key in cfg and concatenate results."""
    frames = []
    for sk in cfg.sport_key:
        frames.append(
            process(
                api_key          = cfg.api_key,
                sport_key        = sk,
                markets          = cfg.markets,
                soft_books       = cfg.soft_books,
                sharp_books      = cfg.sharp_books,
                weighting        = cfg.sharp_weighting,
                capture_point    = cfg.capture_point or ("spreads" in cfg.markets) or ("totals" in cfg.markets),
                pre_align_to_pin = cfg.align_to_pin,
                horizon_days     = cfg.horizon_days,
                use_pin_globals  = cfg.use_pin_globals,
                totals_curve_id  = cfg.totals_curve_id,
                spreads_curve_id = cfg.spreads_curve_id,
                mappings_dir     = cfg.mappings_dir,
            )
        )
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
