# ---------------------------------------------------------------------------
# 0)  Imports
# ---------------------------------------------------------------------------
import pandas as pd
import numpy as np
from odds_engine_v2 import (
    SportConfig, process_cfg,          # <- renamed wrapper
    mlb_weighting, combat_weighting, soccer_weighting, tennis_weighting, football_weighting, hockey_weighting,
    require_soft, require_sharp_and_soft, align_to_pin_line, basketball_weighting
)
from live_lag_filler import augment_board_after_run  # NEW
from pathlib import Path
import json
import statsmodels.api as sm
import joblib


# --- load local .env-style files into environment (optional convenience) ---
import os, pathlib
def _load_env_file(path: str) -> None:
    p = pathlib.Path(path)
    if not p.exists():
        return
    for raw in p.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

# try to load (won't overwrite real env if already set)
_load_env_file("secrets.env")
_load_env_file("settings.env")

API_KEY = os.getenv("ODDS_API_KEY")  # required
if not API_KEY:
    raise RuntimeError("Missing ODDS_API_KEY")

SOFT_US  = ["betmgm","draftkings", "fanduel",
            "ballybet","espnbet","hardrockbet", "betrivers", "williamhill_us"] #"fanatics"
PIN      = "pinnacle"
BETONL   = "betonlineag"


# Build weight objects bound to the US soft-book list
MLB_W   = mlb_weighting(soft=SOFT_US)              # Pinnacle only
COMBAT_W = combat_weighting(soft=SOFT_US)   # one callable for BOTH sports
SOC_W   = soccer_weighting(soft=SOFT_US, cutoff_days=1.5)  # 80/20 Pin/BF
TENNIS_W = tennis_weighting(soft=SOFT_US)
FOOTBALL_W = football_weighting(soft=SOFT_US)
HOCKEY_W = hockey_weighting(soft=SOFT_US)
BASKETBALL_W = basketball_weighting(soft=SOFT_US)  # NEW


# ---------------------------------------------------------------------------
# 1)  Sport-specific configs
# ---------------------------------------------------------------------------
NFL_CFG = SportConfig(
    api_key        = API_KEY,
    sport_key      = ["americanfootball_nfl"],  # _preseason
    markets        = "h2h,spreads,totals",
    soft_books     = SOFT_US,
    sharp_books    = [PIN],
    min_soft       = 1,
    pre_filters    = [align_to_pin_line],  # kept for consistency
    sharp_weighting= FOOTBALL_W,
    horizon_days   = 2,       # weekly cadence; tweak to taste
    align_to_pin   = False,    # ensure spreads/totals match Pin's number before pricing
    use_pin_globals = True,
    totals_curve_id = "NFL_totals",
    spreads_curve_id= "NFL_spreads",
    mappings_dir    = "mappings",
)

# NCAAF (college)
NCAAF_CFG = SportConfig(
    api_key        = API_KEY,
    sport_key      = ["americanfootball_ncaaf"],
    markets        = "h2h,spreads,totals",
    soft_books     = SOFT_US,
    sharp_books    = [PIN],
    min_soft       = 1,
    pre_filters    = [align_to_pin_line],
    sharp_weighting= FOOTBALL_W,
    horizon_days   = 2,
    align_to_pin   = False,
    use_pin_globals = True,                 # ← turn on global filler
    totals_curve_id = "NCAAF_totals",       # ← your new file in mappings/
    spreads_curve_id= "NCAAF_spreads",      # ← your new file in mappings/
    mappings_dir    = "mappings",
)


NBA_CFG = SportConfig(
    api_key         = API_KEY,
    sport_key       = ["basketball_nba"],         # ← Odds API league key
    markets         = "h2h,spreads,totals",
    soft_books      = SOFT_US,
    sharp_books     = [PIN],
    min_soft        = 1,
    pre_filters     = [align_to_pin_line],        # kept for consistency
    sharp_weighting = BASKETBALL_W,
    horizon_days    = 2,

    # Alt-line synthesis like NFL/NCAAF:
    align_to_pin    = False,        # don't force-match lines; we generate alts
    use_pin_globals = True,         # ← enable the global curve filler
    totals_curve_id = "NBA_totals", # ← new mapping file in /mappings
    spreads_curve_id= "NBA_spreads",# ← new mapping file in /mappings
    mappings_dir    = "mappings",
)

NCAAB_CFG = SportConfig(
    api_key         = API_KEY,
    sport_key       = ["basketball_ncaab"],         # ← Odds API league key
    markets         = "h2h,spreads,totals",
    soft_books      = SOFT_US,
    sharp_books     = [PIN],
    min_soft        = 1,
    pre_filters     = [align_to_pin_line],        # kept for consistency
    sharp_weighting = BASKETBALL_W,
    horizon_days    = 2,

    # Alt-line synthesis like NFL/NCAAF:
    align_to_pin    = False,        # don't force-match lines; we generate alts
    use_pin_globals = True,         # ← enable the global curve filler
    totals_curve_id = "NCAAB_totals", # ← new mapping file in /mappings
    spreads_curve_id= "NCAAB_spreads",# ← new mapping file in /mappings
    mappings_dir    = "mappings",
)

#Every Day
BASEBALL_CFG = SportConfig(
    api_key       = API_KEY,
    sport_key     = ["baseball_mlb"],
    markets       = "h2h,spreads,totals",
    soft_books    = SOFT_US,
    sharp_books   = [PIN],
    min_soft      = 1,
    pre_filters   = [require_sharp_and_soft, align_to_pin_line],
    sharp_weighting = MLB_W,
    horizon_days  = 2,
    align_to_pin  = True,        # tells process_cfg to run align_to_pin_line
)

#Thurs-Sat/Sun
FIGHTS_CFG = SportConfig(
    api_key        = API_KEY,
    sport_key     = ["mma_mixed_martial_arts", "boxing_boxing"],
    markets        = "h2h",
    soft_books     = SOFT_US,
    sharp_books    = [PIN, BETONL],
    min_soft       = 1,
    pre_filters    = [require_sharp_and_soft],
    sharp_weighting= COMBAT_W,   # <-- new weighting
    horizon_days   = 2,
)


#Every Day
SOCCER_CFG = SportConfig(
    api_key       = API_KEY,
    sport_key     = ["soccer_efl_champ",   "soccer_epl", "soccer_spain_la_liga", "soccer_france_ligue_one",
                     "soccer_italy_serie_a", "soccer_germany_bundesliga","soccer_usa_mls",
                     "soccer_argentina_primera_division", "soccer_england_league1",
                     "soccer_england_league2", "soccer_brazil_campeonato"
                     ],  #
                                       #
    markets       = "h2h",
    soft_books    = SOFT_US,
    sharp_books   = [PIN],
    min_soft      = 1,
    pre_filters   = [require_sharp_and_soft],
    sharp_weighting = SOC_W,
    horizon_days  = 2,
)


TENNIS_CFG = SportConfig(
    api_key        = API_KEY,
    sport_key      = ["tennis_atp_us_open", "tennis_wta_us_open"],
    markets        = "h2h",
    soft_books     = SOFT_US,
    sharp_books    = [PIN],
    min_soft       = 1,
    pre_filters    = [require_sharp_and_soft],
    sharp_weighting= TENNIS_W,
    horizon_days   = 1,           # keep short – tennis schedules move fast
)


HOCKEY_CFG = SportConfig(
    api_key        = API_KEY,
    sport_key      = ["icehockey_nhl"],           # add "icehockey_nhl_preseason" if desired
    markets        = "h2h,spreads,totals",
    soft_books     = SOFT_US,
    sharp_books    = [PIN],
    min_soft       = 1,
    pre_filters    = [require_sharp_and_soft, align_to_pin_line],
    sharp_weighting= HOCKEY_W,
    horizon_days   = 2,
    align_to_pin   = True,     # ensures puck line / total points match Pin before EV
)



from typing import Iterable
from fnmatch import fnmatch  # not needed for explicit lists, but handy if you add wildcards later

def _csv_env(name: str) -> list[str]:
    v = os.getenv(name, "")
    return [s.strip() for s in v.split(",") if s.strip()]

def _get_keys_from_cfg(cfg) -> list[str]:
    # Return current sport_key/sport_keys (supports dicts or objects)
    if isinstance(cfg, dict):
        return list(cfg.get("sport_key", []) or cfg.get("sport_keys", []))
    if hasattr(cfg, "sport_key"):
        return list(getattr(cfg, "sport_key"))
    if hasattr(cfg, "sport_keys"):
        return list(getattr(cfg, "sport_keys"))
    return []

def _set_keys_on_cfg(cfg, new_keys: Iterable[str]):
    keys = list(new_keys)
    if isinstance(cfg, dict):
        return {**cfg, "sport_key": keys}
    if hasattr(cfg, "_replace"):  # namedtuple
        try:
            return cfg._replace(sport_key=keys)
        except:
            pass
    try:
        if hasattr(cfg, "sport_key"):
            setattr(cfg, "sport_key", keys)
        elif hasattr(cfg, "sport_keys"):
            setattr(cfg, "sport_keys", keys)
    except:
        pass
    return cfg

def _apply_explicit_leagues(cfg, sport_upper: str):
    """
    If LEAGUES_<SPORT> is set (comma-separated exact sport_key names),
    override the config's sport_key(s) with that exact list.
    Example: LEAGUES_SOCCER=soccer_usa_mls,soccer_epl
    """
    override = _csv_env(f"LEAGUES_{sport_upper}")
    if override:
        return _set_keys_on_cfg(cfg, override)
    return cfg

NAME_TO_CFG = {
    "NFL":      NFL_CFG,
    "NCAAF":    NCAAF_CFG,
    "BASEBALL": BASEBALL_CFG,
    "SOCCER":   SOCCER_CFG,
    "TENNIS":   TENNIS_CFG,
    "FIGHTS":   FIGHTS_CFG,
    "HOCKEY":   HOCKEY_CFG,
    "NBA":      NBA_CFG,
    "NCAAB":    NCAAB_CFG,
}

def _build_active_cfgs() -> list:
    """Build ACTIVE_CFGS fresh from current env vars — called each poll cycle."""
    _active = os.getenv("ACTIVE_SPORTS", "NFL,NCAAF,BASEBALL,TENNIS,SOCCER")
    wanted = [s.strip().upper() for s in _active.split(",") if s.strip()]
    cfgs = []
    for name in wanted:
        cfg = NAME_TO_CFG.get(name)
        if not cfg:
            continue
        cfg = _apply_explicit_leagues(cfg, name)
        cfgs.append(cfg)
    if not cfgs:
        raise RuntimeError("ACTIVE_SPORTS yielded no configs. Check settings.env.")
    return cfgs

# Module-level list for backwards compatibility (used on initial import only)
ACTIVE_CFGS = _build_active_cfgs()


# ---------------------------------------------------------------------------
# 2)  Run once (manual) – exactly what your three old scripts did
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 2)  Run once – return the DataFrame *and* write the CSV
# ---------------------------------------------------------------------------
def run_edge_board(
        *,            # keyword-only for clarity
        sort_cols=("ev", "commence_time"),
        head_rows=25,
        csv_path="edge_board.csv",
) -> pd.DataFrame:
    """
    Build the +EV board for the active configs.

    Returns
    -------
    board : pd.DataFrame
        The full edge board, already sorted.

    Side effect
    -----------
    Writes `csv_path` to disk.
    """
    frames = [process_cfg(c) for c in _build_active_cfgs()]
    board  = pd.concat(frames, ignore_index=True)
    board = board[(board["sharp_odds"] > 1.2) & (board["sharp_odds"] < 6)]

    # --- NCAAF blowout filter: drop ENTIRE games if any spread > 17.5 ---
    # (remove all rows for those game_ids, including totals and moneyline)
    pt = pd.to_numeric(board.get("point"), errors="coerce")

    is_ncaaf  = board["sport"].astype(str).eq("americanfootball_ncaaf")
    is_spread = board["market"].astype(str).eq("spreads")

    bad_gids = board.loc[is_ncaaf & is_spread & (pt.abs() > 17.5), "game_id"].unique()

    if bad_gids.size:
        board = board[~board["game_id"].isin(bad_gids)].copy()


#    board = _annotate_and_filter(board)
    board = augment_board_after_run(
        board,
        snap_dir="snapshots",
        mappings_dir="mappings",
        max_lag_minutes=600,
    )

    # Sort
    board = board.sort_values(list(sort_cols), ascending=[False, True])

    if "point" not in board.columns:
        board["point"] = np.nan



    # Console preview
    preview_cols = ["sport", "team", "market", "point",
                    "book", "sharp_p", "book_ip", "ev", "kelly"]
    pd.set_option("display.max_columns", None)
    print(board[preview_cols].head(head_rows))

    # CSV export
    board.to_csv(csv_path, index=False)
    print(f"\nSaved full board to: {csv_path}")

    return board        # <-- NOW YOU ALSO GET THE DF BACK

# ---------------------------------------------------------------------------
# 3)  Build the trimmed "output" view
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------
#FIRST_SEEN_FILE = Path("first_seen.csv")   # small, lives next to the script
#KEY_COLS        = ["sport", "game_id", "team", "market",]

#def _load_first_seen() -> dict:
#    if FIRST_SEEN_FILE.exists():
#        df = pd.read_csv(FIRST_SEEN_FILE, parse_dates=["first_seen"])
#        return {tuple(df.loc[i, KEY_COLS]): df.loc[i, "first_seen"]
#                for i in df.index}
#    return {}

#def _save_first_seen(d: dict) -> None:
#    if not d:
#        return
#    rows = [list(k) + [v] for k, v in d.items()]
#    out  = pd.DataFrame(rows, columns=KEY_COLS + ["first_seen"])
#    out.to_csv(FIRST_SEEN_FILE, index=False)

#FIRST_SEEN = _load_first_seen()          # ← dictionary lives in RAM

#FIRST_SEEN = {}                 # key-tuple → timestamp (lives only in RAM)
#KEY_COLS   = ["sport", "game_id", "team", "market", "point"]

#def buffer_for_sport(sport: str) -> int:
#    s = SHARPNESS.get(sport, 5)          # default to mid-tier if unknown
#    return int(round(5 + 7 * ((11 - s) ** 1.4)))

#def _annotate_and_filter(board: pd.DataFrame) -> pd.DataFrame:
#    """
#    • Fill/attach the column `first_seen`.
#    • Remove rows newer than BUFFER_MIN minutes.
#    """
#    now = pd.Timestamp.utcnow()

#    # 1️⃣  attach first_seen  (create a new entry if key not present)
#    board["first_seen"] = [
#        FIRST_SEEN.setdefault(
#            tuple(
#                row[c] if c != "point" else (0 if pd.isna(row[c]) else row[c])  # NaN → 0
#                for c in KEY_COLS
#                ),
#            now
#            )
#        for _, row in board.iterrows()
#    ]

#    # 2️⃣  drop rows inside the buffer window
#    age_min = (now - board["first_seen"]).dt.total_seconds() / 60
#    buf_min   = board["sport"].map(buffer_for_sport)        # ← FIX
#    board     = board.loc[age_min >= buf_min].copy()        # element-wise
#    _save_first_seen(FIRST_SEEN)

#    return board



# ── LOAD models & constants (NEW PIPELINE) ────────────────────────────
MODELDIR = Path("models")

# Volatility (Tweedie/Gamma-log analogue)
SIGMA_MODEL = joblib.load(MODELDIR / "sigma_tweedie.pkl")
SIGMA_META  = json.load(open(MODELDIR / "sigma_design.json"))  # scalers + dummy vocab + master_cols

# CLV logistic (bagged sklearn.LogisticRegression)
CLV_MODELS = joblib.load(MODELDIR / "logit_bag.pkl")
CLV_META   = json.load(open(MODELDIR / "clv_meta.json"))       # feature_cols + s/m/sf keep + scalers

# === Soccer league buckets for sigma model ===
# A: Top 5 (treat UCL ~ A)
# B: Other top Euro + Championship
# C: Top LATAM/USA
# D: Other Euro top flights
# E: European lower tiers
# F: Asian & African top flights
SOCCER_LEAGUE_GROUP = {
    # --- A ---
    "soccer_epl": "A",
    "soccer_spain_la_liga": "A",
    "soccer_germany_bundesliga": "A",
    "soccer_italy_serie_a": "A",
    "soccer_france_ligue_one": "A",   # alias-friendly

    # --- B ---
    "soccer_portugal_primeira_liga": "B",
    "soccer_netherlands_eredivisie": "B",
    "soccer_belgium_first_div": "B",
    "soccer_turkey_super_league": "B",
    "soccer_efl_champ": "B",

    # --- C ---
    "soccer_brazil_campeonato": "C",
    "soccer_argentina_primera_division": "C",
    "soccer_mexico_ligamx": "C",
    "soccer_usa_mls": "C",
    "soccer_concacaf_leagues_cup": "C",

    # --- D ---
    "soccer_denmark_superliga": "D",

    # --- E ---
    "soccer_england_league1": "E",
    "soccer_england_league2": "E",

    # --- F ---
    "soccer_china_superleague": "F",
}
DEFAULT_SOCCER_GROUP = "E"  # safe middle if a league key isn't listed


# ------------------------------
# Helper: map sport → family key
#   • Baseball stays per-league (use full sport key: e.g., baseball_mlb)
#   • Others collapse to broad families
# ------------------------------
def _sport_family_key(s: str) -> str:
    s = str(s).lower()
    if s.startswith("baseball_"):
        return s  # keep MLB etc. separate as before
    if s.startswith("soccer_"):
        g = SOCCER_LEAGUE_GROUP.get(s, DEFAULT_SOCCER_GROUP)
        return f"soccer_{g}"   # e.g., soccer_A, soccer_B, ... soccer_F
    if s.startswith("tennis"):
        if "wta" in s:  return "tennis_wta"
        if "atp" in s:  return "tennis_atp"
        return "tennis_other"  # ITF/Challenger/etc.
    if s.startswith("mma_"):
        return "combat_mma"
    if s.startswith("boxing_"):
        return "combat_boxing"
    if s.startswith("americanfootball_nfl"):
        return "football_nfl"
    if s.startswith("americanfootball_ncaaf"):
        return "football_ncaaf"
    if s.startswith("basketball_nba"):
        return "basketball_nba"
    if s.startswith("basketball_ncaab"):
        return "basketball_ncaab"
    if s.startswith("icehockey_") or s.startswith("hockey_"):
        return "hockey"
    return "other"

# ——— build design for volatility model (matches _build_design spec you trained) ———
def build_sigma_X(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(index=df.index)

    sub = df.copy()

    # base transforms
    sub["sqrt_hours"] = np.sqrt(np.clip(sub["hours_to_game"].astype(float), 0, None))
    p = sub["implied_probability"].astype(float).clip(1e-6, 1-1e-6)
    sub["logit_ip"] = np.log(p / (1.0 - p))

    # z-scores using TRAIN scalers
    zh_mu, zh_sd = SIGMA_META["zh_mu"], max(SIGMA_META["zh_sd"], 1e-12)
    zl_mu, zl_sd = SIGMA_META["zl_mu"], max(SIGMA_META["zl_sd"], 1e-12)
    sub["z_sqrt_hours"] = (sub["sqrt_hours"] - zh_mu) / zh_sd
    sub["z_logit_ip"]   = (sub["logit_ip"]   - zl_mu) / zl_sd

    # sport family + market dummies aligned to training keeps
    sub["sport_family"] = sub["sport"].map(_sport_family_key)
    sf_keep = SIGMA_META["sf_keep"]
    m_keep  = SIGMA_META["m_keep"]

    sf = pd.get_dummies(sub["sport_family"], prefix="sf", dtype=int).reindex(columns=sf_keep, fill_value=0)
    mk = pd.get_dummies(sub["market"],       prefix="m",  dtype=int).reindex(columns=m_keep,  fill_value=0)

    # interactions
    sf_x_zh = {f"{c}__z_sqrt_hours": sf[c].values * sub["z_sqrt_hours"].values for c in sf_keep}
    m_x_zh  = {f"{c}__z_sqrt_hours": mk[c].values * sub["z_sqrt_hours"].values for c in m_keep}
    sf_x_zl = {f"{c}__z_logit_ip":   sf[c].values * sub["z_logit_ip"].values   for c in sf_keep}

    blocks = [
        sub[["z_sqrt_hours", "z_logit_ip"]],
        sf, mk,
        pd.DataFrame(sf_x_zh, index=sub.index),
        pd.DataFrame(m_x_zh,  index=sub.index),
        pd.DataFrame(sf_x_zl, index=sub.index),
    ]

    X = pd.concat(blocks, axis=1).reindex(columns=SIGMA_META["master_cols"], fill_value=0)
    X = sm.add_constant(X, has_constant="add")
    return X

def _predict_sigma(df: pd.DataFrame) -> pd.Series:
    """
    Predict expected line movement (σ̂) using the production Tweedie model.
    """
    if df.empty:
        return pd.Series(dtype=float, index=df.index, name="expected_line_movement")

    X = build_sigma_X(df)
    if X.empty:
        return pd.Series(dtype=float, index=df.index, name="expected_line_movement")

    sigma_hat = SIGMA_MODEL.predict(X.values)
    sigma_hat = np.clip(sigma_hat, 0.005, None)  # safety floor
    return pd.Series(sigma_hat, index=df.index, name="expected_line_movement")

# ——— build features for CLV logistic (must match training feature builder) ———
def build_clv_X(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # base transforms
    out["sqrt_hours"] = np.sqrt(np.clip(out["hours_to_game"].astype(float), 0, None))
    # prefer precomputed implied_probability if present; else use 'best_ip'
    if "implied_probability" not in out.columns:
        out["implied_probability"] = out["best_ip"]
    p = out["implied_probability"].astype(float).clip(1e-6, 1-1e-6)
    out["logit_ip"] = np.log(p / (1 - p))

    sh_mu = CLV_META["scalers"]["sqrt_hours_mean"]; sh_sd = max(CLV_META["scalers"]["sqrt_hours_std"], 1e-12)
    li_mu = CLV_META["scalers"]["logit_ip_mean"];   li_sd = max(CLV_META["scalers"]["logit_ip_std"],  1e-12)
    out["z_sqrt_hours"] = (out["sqrt_hours"] - sh_mu) / sh_sd
    out["z_logit_ip"]   = (out["logit_ip"]   - li_mu) / li_sd

    # log_ev & snr (uses volatility σ̂ we just predicted)
    out["log_ev"] = np.log(out["odds_from_best_book"].astype(float) / out["sharp_odds"].astype(float))
    out["expected_line_movement"] = out["expected_line_movement"].clip(lower=0.005)
    out["snr"] = out["log_ev"] / out["expected_line_movement"]

    # sport-family interactions and market-time interactions
    out["sport_family"] = out["sport"].map(_sport_family_key)
    sf_keep = CLV_META["sf_keep"]
    s_keep  = CLV_META["s_keep"]
    m_keep  = CLV_META["m_keep"]

    sf = pd.get_dummies(out["sport_family"], prefix="sf", dtype=int).reindex(columns=sf_keep, fill_value=0)

    # ensure intercept dummies align (s_* and m_* were used as intercepts in training)
    if s_keep:
        s_d = pd.get_dummies(out["sport"], prefix="s", dtype=int).reindex(columns=s_keep, fill_value=0)
        out = pd.concat([out, s_d], axis=1)
    if m_keep:
        m_d = pd.get_dummies(out["market"], prefix="m", dtype=int).reindex(columns=m_keep, fill_value=0)
        out = pd.concat([out, m_d], axis=1)

    # interactions
    for c in sf_keep:
        out[f"{c}__z_sqrt_hours"] = sf[c].values * out["z_sqrt_hours"].values
    for c in m_keep:
        out[f"{c}__z_sqrt_hours"] = out[c].astype(int).values * out["z_sqrt_hours"].values

    # the time×odds interaction you settled on
    out["z_hours_x_zlogitip"] = out["z_sqrt_hours"] * out["z_logit_ip"]

    # final reindex to training order
    feature_cols = list(dict.fromkeys(CLV_META["feature_cols"]))  # de-dup, preserve order
    X = out.reindex(columns=feature_cols, fill_value=0).astype(float)
    return X

def _add_clv_prob(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add clv_prob_med from the bagged logistic models.
    """
    if df.empty:
        return df.assign(clv_prob_med=pd.Series(dtype=float))

    out = df.copy()

    # build X with the same recipe + scalers used in training
    X_live = build_clv_X(out)
    if len(X_live) == 0:
        return out.assign(clv_prob_med=pd.Series(dtype=float, index=out.index))

    # bagged raw probs (no Platt in this pipeline)
    raw_stack = [m.predict_proba(X_live)[:, 1] for m in CLV_MODELS]
    out["clv_prob_med"] = np.mean(raw_stack, axis=0)
    return out


def build_edge_output(board: pd.DataFrame) -> pd.DataFrame:
    """
    From the full `board` return a smaller DataFrame with
    the columns   sport, game_id, commence_time, team, market, point,
    book, odds_from_best_book, sharp_odds, ev, kelly, clv_prob_med, stars, outcome_threshold
    (in that exact order).
    """
    df = board.copy()

    df["sport"] = df["sport"].astype(str).str.replace(r"^tennis.*$", "tennis", regex=True)

    # Read decimal odds directly from the per-book column produced by odds_engine_v2
    df["odds_from_best_book"] = pd.to_numeric(df["book_odds"], errors="coerce")


    df = df[df["kelly"] >= 0.0025].copy()
    df = df[df["ev"] <= 0.3]

    # live timing & inputs needed for models
    now = pd.Timestamp.utcnow()
    df["hours_to_game"] = (pd.to_datetime(df["commence_time"], utc=True).sub(now).dt.total_seconds() / 3600.0)
    df["implied_probability"] = df["book_ip"]  # same as training

    # σ̂ from Tweedie model
    df["expected_line_movement"] = _predict_sigma(df)

    # CLV prob from bagged logistic (uses σ̂ internally)
    df = _add_clv_prob(df)


    df = df[df["clv_prob_med"] >= 0.6]

    ##Outcome risk threshold
    df["min_ev_odds"] = 0.0167 * np.log(df["sharp_odds"]) + 0.01

    df["outcome_threshold"] = df["ev"] - df["min_ev_odds"]

    df = df[df["outcome_threshold"] >= -0.01].copy()
    df = df[df["ev"] >= 0.01].copy()
    #df = df[~(df["sport"].str.startswith("tennis") & (hrs > 8))]

    # ── star-rating column ──────────────────────────────────────────────
    bins   = [0.6, 0.65, 0.7, 0.75, 0.8, 1.01]   # right edge exclusive
    #bins   = [0.55, 0.6, 0.65, 0.7, 0.75, 1.01]   # right edge exclusive
    labels = [1, 2, 3, 4, 5]

    df["stars"] = (pd.cut(df["clv_prob_med"], bins=bins, labels=labels, right=False).astype(int))
    df["kelly"] = df["kelly"].clip(upper=0.03)  #choose clip

    # Re-order / subset
    columns = [
        "sport", "game_id", "commence_time", "team", "market", "point",
        "book", "odds_from_best_book",
        "sharp_odds", "ev", "kelly", "clv_prob_med", "stars", "outcome_threshold"
    ]
    return df[columns]


def build_full_output(board: pd.DataFrame) -> pd.DataFrame:
    """
    Run the full ML pipeline on every row in board and return all results
    with no pick-threshold filtering applied.

    This is the single compute entry point.  apply_pick_thresholds() and
    build_edge_output() both derive from this frame — the ML models (sigma
    Tweedie + CLV logistic) only need to run once per cycle.

    Stars are set to 0 for rows where clv_prob_med < 0.6 (below the binning
    range).  The ev <= 0.3 guard is kept as a data-quality filter to exclude
    obviously erroneous odds.  All other rows — including negative-EV lines —
    are returned.

    Includes home_team and away_team when present on the board (available
    from the Odds API response), used by the Explore tab team search.
    """
    df = board.copy()

    df["sport"] = df["sport"].astype(str).str.replace(r"^tennis.*$", "tennis", regex=True)
    df["odds_from_best_book"] = pd.to_numeric(df["book_odds"], errors="coerce")

    # Data quality guard only — extreme EV almost always signals bad/stale odds
    df = df[df["ev"] <= 0.3]

    # Timing inputs required by both ML models
    now = pd.Timestamp.utcnow()
    df["hours_to_game"] = (
        pd.to_datetime(df["commence_time"], utc=True).sub(now).dt.total_seconds() / 3600.0
    )
    df["implied_probability"] = df["book_ip"]

    # σ̂ from Tweedie volatility model
    df["expected_line_movement"] = _predict_sigma(df)

    # CLV probability from bagged logistic
    df = _add_clv_prob(df)

    # Stars: same bins as pick thresholds; rows below the 0.6 floor get 0
    bins   = [0.6, 0.65, 0.7, 0.75, 0.8, 1.01]
    labels = [1, 2, 3, 4, 5]
    df["stars"] = (
        pd.cut(df["clv_prob_med"], bins=bins, labels=labels, right=False)
        .pipe(lambda s: pd.to_numeric(s, errors="coerce"))
        .fillna(0)
        .astype(int)
    )

    df["kelly"] = df["kelly"].clip(upper=0.03)

    df["min_ev_odds"]       = 0.0167 * np.log(df["sharp_odds"]) + 0.01
    df["outcome_threshold"] = df["ev"] - df["min_ev_odds"]

    base_cols = [
        "sport", "game_id", "commence_time", "home_team", "away_team",
        "team", "market", "point",
        "book", "odds_from_best_book",
        "sharp_odds", "ev", "kelly", "clv_prob_med", "stars", "outcome_threshold",
    ]
    return df[[c for c in base_cols if c in df.columns]]


def apply_pick_thresholds(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply pick-selection thresholds to a frame already produced by
    build_full_output().  Returns only rows that would appear as picks
    in current_picks / Discord — same rows, same order as build_edge_output().

    Keeping this as a separate function lets the scheduler call
    build_full_output() once and derive both the full Explore dataset
    and the filtered picks dataset without running the ML models twice.
    """
    out = df[df["kelly"] >= 0.0025].copy()
    out = out[out["clv_prob_med"] >= 0.6]
    out = out[out["outcome_threshold"] >= -0.01].copy()
    out = out[out["ev"] >= 0.01].copy()
    columns = [
        "sport", "game_id", "commence_time", "team", "market", "point",
        "book", "odds_from_best_book",
        "sharp_odds", "ev", "kelly", "clv_prob_med", "stars", "outcome_threshold",
    ]
    return out[[c for c in columns if c in out.columns]]


# ---------------------------------------------------------------------------
# 4)  Script entry-point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    board = run_edge_board()                 # full DataFrame + CSV

    output = build_edge_output(board)        # trimmed DataFrame
    output.to_csv("edge_output.csv", index=False)

    # console confirmation
    print("\nSaved trimmed output to: edge_output.csv")
