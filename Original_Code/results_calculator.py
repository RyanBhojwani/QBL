"""
results_calculator.py — nightly performance metrics for Quant Bet Labs.

Reads settled_picks from Supabase, deduplicates on (game_id, market, team),
computes comprehensive stats across three time windows and five segment
breakdowns, and upserts to the model_results table.

Called by the 4:30 AM ET daemon thread in bet_scheduler7.py.
Can also be run standalone for testing:
    python results_calculator.py
"""

import json
import logging
import math
import os
import pathlib

import numpy as np
import pandas as pd
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# ── env loading (for standalone runs) ────────────────────────────────────────
def _load_env(path: str) -> None:
    p = pathlib.Path(path)
    if not p.exists():
        return
    for raw in p.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

_load_env("secrets.env")
_load_env("Original_Code/secrets.env")

import supabase_writer as sb  # noqa: E402

# ── Constants ─────────────────────────────────────────────────────────────────
KELLY_SCALE   = 0.5          # half-Kelly
RISK_FREE     = 0.0396       # 3.96% annual risk-free rate
INITIAL_BK    = 1000.0       # starting bankroll for compounding simulation
ET_TZ         = ZoneInfo("US/Eastern")


# ─────────────────────────────────────────────────────────────────────────────
# Data loading & preparation
# ─────────────────────────────────────────────────────────────────────────────

def _load_data() -> pd.DataFrame | None:
    """Load and return settled_picks from Supabase, or None if unavailable."""
    df = sb.load_settled_picks()
    if df is None or df.empty:
        logger.warning("results_calculator: no data from settled_picks — aborting.")
        return None
    return df


def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean raw settled_picks for metric computation:
    - Parse commence_time to UTC, add Eastern-date column
    - Clip kelly to 0.1
    - Ensure result column uses 'W'/'L'/'P'
    - Filter to settled rows only (result in W/L/P)
    """
    df = df.copy()

    # Parse timestamps
    df["commence_time"] = pd.to_datetime(df["commence_time"], utc=True, errors="coerce")
    df["found_at"]      = pd.to_datetime(df["found_at"],      utc=True, errors="coerce")

    # Eastern date column — used for windowing and daily compounding
    df["date_et"] = df["commence_time"].dt.tz_convert(ET_TZ).dt.date

    # Ensure numeric columns
    for col in ("kelly", "odds_from_best_book", "ev", "clv", "stars"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["kelly"] = df["kelly"].clip(upper=0.1)

    # Keep only settled rows
    df = df[df["result"].isin(["W", "L", "P"])].copy()

    return df


def _keep_first(df: pd.DataFrame) -> pd.DataFrame:
    """
    Deduplicate on (game_id, market, team), keeping the earliest found_at.
    Upgrade versions (same outcome, higher stars) are collapsed to the first alert.
    """
    if df.empty:
        return df
    return (
        df.sort_values("found_at", kind="stable")
          .drop_duplicates(subset=["game_id", "market", "team"], keep="first")
          .reset_index(drop=True)
    )


# ─────────────────────────────────────────────────────────────────────────────
# Windowing
# ─────────────────────────────────────────────────────────────────────────────

def _filter_window(df: pd.DataFrame, time_window: str) -> pd.DataFrame:
    today_et = pd.Timestamp.now(tz=ET_TZ).date()

    if time_window == "all_time":
        return df

    if time_window == "30d":
        cutoff = today_et - pd.Timedelta(days=30)
        return df[df["date_et"] >= cutoff].copy()

    if time_window == "1d":
        yesterday = today_et - pd.Timedelta(days=1)
        return df[df["date_et"] == yesterday].copy()

    raise ValueError(f"Unknown time_window: {time_window!r}")


# ─────────────────────────────────────────────────────────────────────────────
# Metric computation helpers
# ─────────────────────────────────────────────────────────────────────────────

def _actual_metrics(df: pd.DataFrame) -> dict:
    """Win%, avg odds (kelly-weighted), ROI, total profit in units."""
    if df.empty:
        return {}

    wins   = df["result"] == "W"
    losses = df["result"] == "L"
    pushes = df["result"] == "P"

    n_picks  = len(df)
    n_wins   = int(wins.sum())
    n_losses = int(losses.sum())
    n_pushes = int(pushes.sum())
    wl_total = n_wins + n_losses
    win_pct  = (n_wins / wl_total) if wl_total > 0 else None

    kelly = df["kelly"]
    odds  = df["odds_from_best_book"]

    # Kelly-weighted average odds
    k_sum = kelly.sum()
    avg_odds = float((odds * kelly).sum() / k_sum) if k_sum > 0 else None

    # Profit per bet in units (half-Kelly sized)
    stake = kelly * KELLY_SCALE
    profit = pd.Series(0.0, index=df.index)
    profit[wins]   = (odds[wins] - 1) * stake[wins]
    profit[losses] = -stake[losses]
    # pushes: profit = 0

    total_stake  = stake.sum()
    total_profit = float(profit.sum())
    roi = float(total_profit / total_stake) if total_stake > 0 else None

    return {
        "n_picks":            n_picks,
        "n_wins":             n_wins,
        "n_losses":           n_losses,
        "n_pushes":           n_pushes,
        "win_pct":            win_pct,
        "avg_odds":           avg_odds,
        "roi":                roi,
        "total_profit_units": total_profit,
    }


def _clv_metrics(df: pd.DataFrame) -> dict:
    """CLV-based expected performance metrics."""
    clv_df = df[df["clv"].notna()].copy()
    if clv_df.empty:
        return {}

    clv_n_picks = len(clv_df)
    clv_win_pct = float((clv_df["clv"] > 0).sum() / clv_n_picks)

    k = clv_df["kelly"]
    c = clv_df["clv"]
    k_sum = k.sum()

    clv_roi          = float((c * k).sum() / k_sum)       if k_sum > 0 else None
    clv_profit_units = float((c * k * KELLY_SCALE).sum()) if k_sum > 0 else None

    return {
        "clv_n_picks":     clv_n_picks,
        "clv_win_pct":     clv_win_pct,
        "clv_roi":         clv_roi,
        "clv_profit_units": clv_profit_units,
    }


def _ev_metrics(df: pd.DataFrame) -> dict:
    """Model EV-based expected performance metrics."""
    ev_df = df[df["ev"].notna()].copy()
    if ev_df.empty:
        return {}

    k = ev_df["kelly"]
    e = ev_df["ev"]
    k_sum = k.sum()

    ev_roi          = float((e * k).sum() / k_sum)       if k_sum > 0 else None
    ev_profit_units = float((e * k * KELLY_SCALE).sum()) if k_sum > 0 else None

    return {
        "ev_roi":          ev_roi,
        "ev_profit_units": ev_profit_units,
    }


def _bankroll_metrics(df: pd.DataFrame) -> dict | None:
    """
    Daily-compounded bankroll simulation + risk metrics.
    Returns None if fewer than 2 trading days exist.
    """
    if df.empty:
        return None

    wins   = df["result"] == "W"
    losses = df["result"] == "L"
    pushes = df["result"] == "P"

    # Build daily P&L series — two parallel tracks: real and CLV-expected
    days = sorted(df["date_et"].unique())
    if len(days) < 2:
        return None

    bankroll_real = INITIAL_BK
    bankroll_exp  = INITIAL_BK
    curve = []

    for day in days:
        day_df = df[df["date_et"] == day]

        bet_sizes = day_df["kelly"] * bankroll_real * KELLY_SCALE

        day_wins   = day_df["result"] == "W"
        day_losses = day_df["result"] == "L"

        profit_real = (
            ((day_df["odds_from_best_book"] - 1) * bet_sizes)[day_wins].sum()
            - bet_sizes[day_losses].sum()
        )

        # CLV-expected: use clv where available, else 0 for that pick
        clv_vals = day_df["clv"].fillna(0.0)
        profit_exp = (clv_vals * bet_sizes).sum()

        bankroll_real += profit_real
        bankroll_exp  += profit_exp

        # Guard against bankroll going to zero or negative
        bankroll_real = max(bankroll_real, 0.01)
        bankroll_exp  = max(bankroll_exp,  0.01)

        curve.append({
            "date":           str(day),
            "bankroll_real":  round(bankroll_real, 4),
            "bankroll_exp":   round(bankroll_exp,  4),
        })

    # ── Scalar risk metrics from the real bankroll curve ──────────────────
    bk_values = [INITIAL_BK] + [c["bankroll_real"] for c in curve]
    bk_series = pd.Series(bk_values, dtype=float)

    # Daily log returns
    log_r = np.log(bk_series / bk_series.shift(1)).dropna()

    n_days = len(days)
    final  = bk_series.iloc[-1]

    bankroll_return = (final - INITIAL_BK) / INITIAL_BK
    log_return      = float(np.log(final / INITIAL_BK))
    cagr            = float((final / INITIAL_BK) ** (365.0 / n_days) - 1) if n_days > 0 else None

    # Volatility (annualized std of daily log returns)
    vol = float(log_r.std(ddof=1) * math.sqrt(365)) if len(log_r) > 1 else None

    # Sharpe
    sharpe = float((cagr - RISK_FREE) / vol) if (vol and vol > 0 and cagr is not None) else None

    # Sortino — downside vol only (negative log returns)
    neg_r = log_r[log_r < 0]
    if len(neg_r) > 1:
        down_vol = float(neg_r.std(ddof=1) * math.sqrt(365))
        sortino  = float((cagr - RISK_FREE) / down_vol) if (down_vol > 0 and cagr is not None) else None
    else:
        sortino = None

    # Max drawdown from peak
    peaks = bk_series.cummax()
    drawdowns = (peaks - bk_series) / peaks
    max_drawdown = float(drawdowns.max())

    return {
        "bankroll_return": round(bankroll_return, 6),
        "log_return":      round(log_return, 6),
        "cagr":            round(cagr, 6)        if cagr is not None else None,
        "max_drawdown":    round(max_drawdown, 6),
        "volatility":      round(vol, 6)         if vol is not None else None,
        "sharpe":          round(sharpe, 6)      if sharpe is not None else None,
        "sortino":         round(sortino, 6)     if sortino is not None else None,
        "daily_curve":     curve,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Segment iteration
# ─────────────────────────────────────────────────────────────────────────────

def _segment_slices(df: pd.DataFrame):
    """
    Yield (segment_type, segment_val, slice_df) for every combination
    that has at least one settled row.
    """
    # overall
    yield "overall", "overall", df

    # by star
    for star in sorted(df["stars"].dropna().unique()):
        yield "star", str(int(star)), df[df["stars"] == star]

    # by sport
    for sport in sorted(df["sport"].dropna().unique()):
        yield "sport", str(sport), df[df["sport"] == sport]

    # by market
    for mkt in sorted(df["market"].dropna().unique()):
        yield "market", str(mkt), df[df["market"] == mkt]

    # by sport × market
    for (sport, mkt), grp in df.groupby(["sport", "market"]):
        yield "sport_market", f"{sport}|{mkt}", grp


# ─────────────────────────────────────────────────────────────────────────────
# Master computation
# ─────────────────────────────────────────────────────────────────────────────

def compute_and_store_results() -> None:
    """
    Main entry point. Loads settled_picks, computes all metrics, upserts
    to model_results. Non-fatal: logs warnings and returns on any failure.
    """
    logger.info("results_calculator: starting nightly computation.")

    raw = _load_data()
    if raw is None:
        return

    df = _prepare(raw)
    df = _keep_first(df)
    logger.info("results_calculator: %d deduplicated picks to process.", len(df))

    records: list[dict] = []
    computed_at = pd.Timestamp.utcnow().isoformat()

    for time_window in ("all_time", "30d", "1d"):
        df_win = _filter_window(df, time_window)
        has_bankroll = time_window != "1d"

        for seg_type, seg_val, df_seg in _segment_slices(df_win):
            if df_seg.empty:
                continue

            row: dict = {
                "computed_at":  computed_at,
                "time_window":  time_window,
                "segment_type": seg_type,
                "segment_val":  seg_val,
            }

            row.update(_actual_metrics(df_seg))
            row.update(_clv_metrics(df_seg))
            row.update(_ev_metrics(df_seg))

            if has_bankroll:
                bk = _bankroll_metrics(df_seg)
                if bk:
                    curve = bk.pop("daily_curve")
                    row.update(bk)
                    row["daily_curve"] = curve   # kept as Python list; _to_records() will JSON-encode

            records.append(row)

    # daily_curve is a Python list — JSON-encode it so _to_records doesn't choke
    for r in records:
        if "daily_curve" in r and isinstance(r["daily_curve"], list):
            r["daily_curve"] = json.dumps(r["daily_curve"])

    logger.info("results_calculator: upserting %d rows to model_results.", len(records))
    sb.write_model_results(records)
    logger.info("results_calculator: done.")


# ── Standalone entry point ────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    compute_and_store_results()
