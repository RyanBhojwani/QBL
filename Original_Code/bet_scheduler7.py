# cd "C:\Users\rajbh\Documents\Ryan\Coding Projects\Sports Betting"

# Cross-platform pickle compatibility: models were saved on Windows where sklearn's
# Cython _loss extension lands in sys.modules as '_loss'. On Linux it lives at
# sklearn._loss._loss, so joblib.load fails unless we alias it first.
import sys as _sys
try:
    import sklearn._loss._loss as _sklearn_loss_shim
    _sys.modules.setdefault('_loss', _sklearn_loss_shim)
except ImportError:
    pass

import time, threading, asyncio, logging
import pandas as pd, numpy as np
from discord.ext import commands
from run_edge_board_v2 import run_edge_board, build_edge_output
from zoneinfo import ZoneInfo  # std-lib in Python ≥3.9
from pathlib import Path
import pyarrow as pa, pyarrow.parquet as pq
import pyarrow.dataset as ds   # already imported elsewhere
import aiohttp
import discord
from discord import Embed            # Embed is still handy to import directly
import traceback
import settle_ledger
import supabase_writer as sb

# --- load .env-style files into process env (no extra deps needed) ---
import os, pathlib

def _load_env_file(path: str) -> None:
    p = pathlib.Path(path)
    if not p.exists():
        return
    for raw in p.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):        # skip blanks & comments
            continue
        if "=" not in s:
            continue
        k, v = s.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")    # allow quoted values
        os.environ.setdefault(k, v)            # don't overwrite if already set

# Load local files (current folder) if present — skipped gracefully on Railway
_load_env_file("secrets.env")
_load_env_file("settings.env")

# Structured logging — Railway captures stdout; force UTC timestamps, unbuffered
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger(__name__)

# Data directory — set DATA_DIR on Railway to a persistent volume path (e.g. /data)
# Defaults to current working directory for local runs
DATA_DIR  = pathlib.Path(os.getenv("DATA_DIR", "."))
BETS_PATH = DATA_DIR / "bets.csv"

def _require_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return v

# Day/Night polling cadence (minutes). Defaults to POLL_MINUTES if specific values not set.
DAY_POLL_MINUTES   = int(os.getenv("DAY_POLL_MINUTES",   os.getenv("POLL_MINUTES", "15")))
NIGHT_POLL_MINUTES = int(os.getenv("NIGHT_POLL_MINUTES", os.getenv("POLL_MINUTES", "60")))
# Night window in US/Eastern; default 22:00 (10 PM) → 07:00 (7 AM)
NIGHT_START_HOUR = int(os.getenv("NIGHT_START_HOUR", "22"))
NIGHT_END_HOUR   = int(os.getenv("NIGHT_END_HOUR",   "7"))

def _is_night_eastern(now_est=None) -> bool:
    """Return True if local Eastern time is within the 'night' window."""
    tz = ZoneInfo("US/Eastern")
    if now_est is None:
        import pandas as pd
        now_est = pd.Timestamp.now(tz=tz)
    else:
        now_est = now_est.astimezone(tz)
    h = now_est.hour
    if NIGHT_START_HOUR <= NIGHT_END_HOUR:
        return NIGHT_START_HOUR <= h < NIGHT_END_HOUR
    else:
        # Overnight window (e.g., 22 → 7): hours >= start OR < end
        return (h >= NIGHT_START_HOUR) or (h < NIGHT_END_HOUR)

def current_poll_seconds() -> int:
    """Return the current cadence in seconds based on Eastern day/night."""
    day   = int(os.getenv("DAY_POLL_MINUTES",   "15"))
    night = int(os.getenv("NIGHT_POLL_MINUTES", "60"))
    minutes = night if _is_night_eastern() else day
    return max(1, int(minutes) * 60)

POLL_SECONDS = current_poll_seconds()

# Discord auth: either a bot token (optional) or webhooks (preferred).
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")  # optional if you're only using webhooks

# If you’re posting via channel-specific webhooks (recommended), set these:
WEBHOOKS = {
    "basic":   os.getenv("DISCORD_WEBHOOK_BASIC"),
    "premium": os.getenv("DISCORD_WEBHOOK_PREMIUM"),
    "vip":     os.getenv("DISCORD_WEBHOOK_VIP"),
    "test":    os.getenv("DISCORD_WEBHOOK_TEST"),  # optional
}
# Guard: at least one webhook should be present
if not any(WEBHOOKS.values()) and not DISCORD_TOKEN:
    raise RuntimeError("Provide at least one Discord webhook or a DISCORD_TOKEN.")

# (Optional) if you still post by channel ID somewhere, read them from env:
CH_BASIC   = int(os.getenv("DISCORD_CH_BASIC",   "0") or 0)
CH_PREMIUM = int(os.getenv("DISCORD_CH_PREMIUM", "0") or 0)
CH_VIP     = int(os.getenv("DISCORD_CH_VIP",     "0") or 0)
TEST_CH    = int(os.getenv("DISCORD_CH_TEST",    "0") or 0)


# ───-- Friendly display names  ──────────────────────────────────────────

SPORT_NAMES = {
    "baseball_mlb":              "MLB",
    "soccer_fifa_club_world_cup": "FIFA Club WC",
    "soccer_usa_mls":            "MLS",
    "soccer_brazil_serie_b":     "Brazil Serie B",
    "soccer_brazil_campeonato":  "Brazil Serie A",
    "soccer_china_superleague":  "Chinese Superleague",
    "tennis_atp_wimbledon":      "ATP Tennis",
    "tennis_wta_wimbledon":      "WTA Tennis",
    "basketball_nba":            "NBA",
    "boxing_boxing":             "Boxing",
    "mma_mixed_martial_arts":    "MMA",
    "soccer_argentina_primera_division": "Argentinian Primera Div",
    "americanfootball_ncaaf":         "NCAA Football",
    "americanfootball_nfl": "NFL",
    "icehockey_nhl": "NHL",
    "basketball_ncaab": "NCAA Basketball",
    # …add more as needed
}

MARKET_NAMES = {
    "h2h":     "Moneyline",
    "spreads": "Spread",
    "totals":  "Total",
}

BOOK_NAMES = {
    "fanduel":          "FanDuel",
    "williamhill_us":   "Caesars",
    "betmgm":           "BetMGM",
    "espnbet":          "ESPN Bet",
    "betrivers":        "BetRivers",
    "ballybet":         "Bally Bet",
    "draftkings":       "Draftkings",
    "hardrockbet":      "Hard Rock Bet",
    # …add any others you pull
}


# ────────────── 1.  spin up the bot in a background thread ────────────────
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ───────── add this just below `bot = commands.Bot(...)` ──────────
@bot.event
async def on_ready():
    print("Bot online")                                   # console heartbeat
    await bot.change_presence(activity=discord.Game("Watching for edges…"))

    chan = bot.get_channel(TEST_CH)                       # private log channel
    if chan:
        embed = discord.Embed(
            title="🟢 Bot restarted",
            description="Live and ready to post picks.",
            color=0x2ecc71
        )
        await chan.send(embed=embed)

def dec_to_american(decimal_odds: float) -> str:
    """
    Convert decimal odds (e.g. 2.58) to American format (+158).
    """
    if decimal_odds >= 2:
        return f"+{int(round((decimal_odds - 1) * 100))}"
    else:
        return f"-{int(round(100 / (decimal_odds - 1)))}"



def _tier_for_stars(row) -> str:
    """Map the numeric stars column to a subscription tier string."""
    if row.stars >= 5:
        return "vip"
    elif row.stars >= 3:
        return "premium"
    else:
        return "basic"

def _first_book(best_book_val) -> str:
    if pd.isna(best_book_val):
        return ""
    return str(best_book_val).split(",")[0].strip()

def _pretty_book_list(best_book_val: str) -> str:
    if pd.isna(best_book_val):
        return ""
    books = [b.strip() for b in str(best_book_val).split(",") if b.strip()]
    return ", ".join(BOOK_NAMES.get(b, b.replace("_", " ").title()) for b in books)


TESTING_MODE: dict[str, bool] = {
    "soccer_efl_champ":       True,
    "tennis": True,
    "soccer_netherlands_eredivisie": True,
    "soccer_belgium_first_div": True,
    "soccer_portugal_primeira_liga": True,
    "soccer_turkey_super_league": True,
    "americanfootball_ncaaf": True,
    "tennis_atp_us_open": True,
    "tennis_wta_us_open": True,
    "soccer_fifa_world_cup_qualifiers_europe": True,
    "icehockey_nhl": True,
    "basketball_nba": True,
    "basketball_ncaab": True
}

DONT_SEND: dict[str, bool] = {
    "baseball_milb": True,
    "americanfootball_nfl_preseason": True,
    "basketball_ncaab": True
    # add other sport keys here
}

def is_testing_mode(sport_key: str) -> bool:
    return bool(TESTING_MODE.get(str(sport_key), False))

def is_dont_send(sport_key: str) -> bool:
    return bool(DONT_SEND.get(str(sport_key), False))


async def publish_pick(row):
    """
    Build the embed and send it through the channel-specific webhook.
    Webhooks ignore bot roles entirely, so they always post.
    """
    tier = _tier_for_stars(row)            # "basic" / "premium" / "vip"
    url  = WEBHOOKS[tier]

    # ---------- pretty-name look-ups ----------
    # raw key (for testing-mode check) vs. friendly display name (for printing)
    sport_key = str(row.sport)
    if is_dont_send(sport_key):
        print(f"[SKIP] {sport_key} is in DONT_SEND list — not posting.")
        return
    
    if (
            sport_key == "americanfootball_ncaaf"
            and str(row.market) == "spreads"
            and pd.notna(row.point)
            and abs(float(row.point)) > 25
    ):
        print(f"[SKIP] {sport_key} spread {row.point} too large (>25) — not posting.")
        return
    
    if (
            sport_key == "americanfootball_nfl"
            and str(row.market) == "spreads"
            and pd.notna(row.point)
            and abs(float(row.point)) > 12.5
    ):
        print(f"[SKIP] {sport_key} spread {row.point} too large (>12.5) — not posting.")
        return
    
    if sport_key == "americanfootball_ncaaf" or sport_key == "americanfootball_nfl":
        # compute hours-to-game from current UTC and the row's commence_time
        ct = pd.to_datetime(getattr(row, "commence_time", None), utc=True, errors="coerce")
        if pd.notna(ct):
            htg = (ct - pd.Timestamp.utcnow()).total_seconds() / 3600.0
            if htg > 12.0:
                print(f"[SKIP] {sport_key} kickoff in {htg:.1f}h (>12h) — not posting.")
                return
    
    if sport_key == "basketball_ncaab":
        # compute hours-to-game from current UTC and the row's commence_time
        ct = pd.to_datetime(getattr(row, "commence_time", None), utc=True, errors="coerce")
        if pd.notna(ct):
            htg = (ct - pd.Timestamp.utcnow()).total_seconds() / 3600.0
            if htg > 4.0:
                print(f"[SKIP] {sport_key} kickoff in {htg:.1f}h (>4 h) — not posting.")
                return
    
    if sport_key == "basketball_nba":
        # compute hours-to-game from current UTC and the row's commence_time
        ct = pd.to_datetime(getattr(row, "commence_time", None), utc=True, errors="coerce")
        if pd.notna(ct):
            htg = (ct - pd.Timestamp.utcnow()).total_seconds() / 3600.0
            if htg > 8.0:
                print(f"[SKIP] {sport_key} kickoff in {htg:.1f}h (>8h) — not posting.")
                return
            
    
    sport     = SPORT_NAMES.get(sport_key, sport_key.replace("_", " ").title())
    market    = MARKET_NAMES.get(row.market, row.market.capitalize())
    book      = BOOK_NAMES.get(str(row.book), str(row.book).replace("_", " ").title())

    # testing-mode banner (only affects printed text)
    testing_note = " (This sport is in testing mode)" if is_testing_mode(sport_key) else ""

    point_str = "" if pd.isna(row.point) else f" {row.point}"
    odds_am   = dec_to_american(row.odds_from_best_book)
    start_est = (
        pd.to_datetime(row.commence_time, utc=True)
          .astimezone(ZoneInfo("US/Eastern"))
          .strftime("%b %d %I:%M %p ET")
    )
    units     = row.kelly * 100
    stars_str = "⭐" * int(row.stars)

    header = (
        f"**{sport} | {row.team} | {market}:{point_str} "
        f"| {odds_am} | Start: {start_est}**"
    )
    footer = (
        f"Sportsbooks: {book}\n"
        f"Stars: {stars_str}\n"
        f"Bet Size: {units:.1f} U"
        f"\n{testing_note}"
    )

    embed = Embed(description=f"{header}\n{footer}", color=0x2ecc71)

    # ---------- async webhook send ----------
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(url, session=session)
        try:
            await webhook.send(embed=embed, username="PickBot")
            tag = " (TESTING)" if testing_note else ""
            print(f"[SEND]{tag} {tier.upper()} pick posted via webhook.")
        except Exception as e:
            print(f"[ERROR] Webhook send failed ({tier}): {e}")




# ─────────────── Daily 4 AM Eastern settlement worker ───────────────
from datetime import datetime, timedelta

def _seconds_until_next_4am_est(now_utc=None) -> int:
    """Return seconds until the next 4:00 AM US/Eastern from 'now'."""
    tz_est = ZoneInfo("US/Eastern")
    now = (pd.Timestamp.utcnow() if now_utc is None else pd.Timestamp(now_utc)).to_pydatetime()
    now_est = now.astimezone(tz_est)

    # target today at 04:00 in EST/EDT
    target = now_est.replace(hour=4, minute=0, second=0, microsecond=0)
    if now_est >= target:
        target = target + timedelta(days=1)  # move to tomorrow

    # convert back to naive UTC seconds to sleep
    target_utc = target.astimezone(ZoneInfo("UTC"))
    return max(1, int((target_utc - now.astimezone(ZoneInfo("UTC"))).total_seconds()))


def _seconds_until_next_hhmm_est(hour: int, minute: int, now_utc=None) -> int:
    """Return seconds until the next HH:MM US/Eastern from 'now'."""
    tz_est = ZoneInfo("US/Eastern")
    now = (pd.Timestamp.utcnow() if now_utc is None else pd.Timestamp(now_utc)).to_pydatetime()
    now_est = now.astimezone(tz_est)

    target = now_est.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if now_est >= target:
        target = target + timedelta(days=1)

    target_utc = target.astimezone(ZoneInfo("UTC"))
    return max(1, int((target_utc - now.astimezone(ZoneInfo("UTC"))).total_seconds()))

def _daily_settlement_worker():
    """Forever: sleep until next 4 AM Eastern, then run settle_ledger.main()."""
    while True:
        try:
            secs = _seconds_until_next_4am_est()
            print(f"[settle] Sleeping {secs/3600:.2f} hours until next 4:00 AM ET …")
            time.sleep(secs)

            started = datetime.now(tz=ZoneInfo("US/Eastern")).strftime("%Y-%m-%d %I:%M %p %Z")
            print(f"[settle] {started} — running settle_ledger.main()")
            try:
                settle_ledger.main()   # ← runs your CSV move+delete + W/L settlement
            except Exception:
                print("[settle] ERROR inside settle_ledger.main():")
                traceback.print_exc()

            # Recompute every loop (handles DST changes correctly)
        except Exception:
            # absolutely never die — log and retry in 5 minutes
            print("[settle] FATAL in worker loop; retrying in 300s")
            traceback.print_exc()
            time.sleep(300)



def start_bot():
    asyncio.set_event_loop(asyncio.new_event_loop())
    bot.run(DISCORD_TOKEN)          # blocking call, but inside its own thread

if DISCORD_TOKEN:
    threading.Thread(target=start_bot, daemon=True).start()
else:
    logger.info("DISCORD_TOKEN not set — running in webhook-only mode (no bot thread)")
threading.Thread(target=_daily_settlement_worker, daemon=True).start()


def _daily_results_worker():
    """Forever: sleep until 4:30 AM Eastern, then compute and store model results."""
    while True:
        try:
            secs = _seconds_until_next_hhmm_est(hour=4, minute=30)
            print(f"[results] Sleeping {secs/3600:.2f} hours until next 4:30 AM ET …")
            time.sleep(secs)

            started = datetime.now(tz=ZoneInfo("US/Eastern")).strftime("%Y-%m-%d %I:%M %p %Z")
            print(f"[results] {started} — running results_calculator.compute_and_store_results()")
            try:
                import results_calculator
                results_calculator.compute_and_store_results()
            except Exception:
                print("[results] ERROR inside results_calculator:")
                traceback.print_exc()
        except Exception:
            print("[results] FATAL in results worker loop; retrying in 300s")
            traceback.print_exc()
            time.sleep(300)

threading.Thread(target=_daily_results_worker, daemon=True).start()


# ─────────────── 2.  helper to schedule posts from main thread ─────────────
def queue_pick(row):
    """Thread-safe: schedule publish_pick on the bot loop."""
    fut = asyncio.run_coroutine_threadsafe(publish_pick(row), bot.loop)
    fut.add_done_callback(lambda f: f.exception() and print(f.exception()))
    

# ------- make them global so you can inspect in a REPL ----------------------
latest_board  = None
latest_output = None
bets          = pd.DataFrame()





def update_closing_lines(bets: pd.DataFrame, board: pd.DataFrame) -> None:
    """
    Update `closing_line` for all not-yet-started bets.

    Phase 1 (unchanged): if the exact (game_id, team, market, point) is still on the board,
    copy board.sharp_odds → bets.closing_line and also advance commence_time if the API pushed it forward.

    Phase 2 (NEW): for NFL/NCAAF spreads/totals when the bet's point is no longer on the board,
    use the global mapping curves (underdog for spreads, Over for totals) to translate
    from an anchor board row (same game/market; for +spreads & Overs use SAME team, for -spreads & Unders use OPPOSITE team)
    and synthesize a fair probability at the bet’s point, then set closing_line = 1 / p_target.
    """
    if bets.empty or board.empty:
        return

    now = pd.Timestamp.utcnow()
    bets["commence_time"] = pd.to_datetime(bets["commence_time"], utc=True, errors="coerce")

    # Only update rows that haven't started yet (based on the *current* commence_time in bets)
    live_mask = bets["commence_time"] > now
    live = bets[live_mask]
    if live.empty:
        return

    # ---------------- Phase 1: direct point matches (same game_id, team, market, point) ----------------
    key_cols = ["game_id", "team", "market", "point"]
    board_dedup = board.drop_duplicates(subset=key_cols, keep="first")
    merged = live.merge(
        board_dedup[key_cols + ["sharp_odds", "commence_time"]],
        on=key_cols,
        how="left",
        suffixes=("", "_new"),
    )

    # (A) update closing_line for direct matches
    for idx, new_odds in zip(live.index, merged["sharp_odds_new"]):
        if pd.notna(new_odds):
            bets.at[idx, "closing_line"] = new_odds

    # (B) accept forward-moved commence_time (for direct matches only)
    for idx, ct_new in zip(live.index, merged["commence_time_new"]):
        if pd.notna(ct_new) and ct_new > now and ct_new > bets.at[idx, "commence_time"]:
            bets.at[idx, "commence_time"] = pd.to_datetime(ct_new, utc=True)

    # ---------------- Phase 2: mapped updates for moved points (NFL/NCAAF spreads & totals) -------------
    # Only rows still missing a fresh odds after Phase 1
    need_map_mask = live.index[merged["sharp_odds_new"].isna()]
    if need_map_mask.empty:
        return

    # Lazy import here to avoid any circulars and keep top-level imports minimal.
    from functools import lru_cache
    from odds_engine import _load_mapping, _make_spreads_curve, _make_totals_curve, _logit, _sigmoid  # type: ignore

    # Which sports/markets use mappings and which curve id to load
    # (filenames under the "mappings/" directory; you already use these ids in run_edge_board)
    MAPPING_IDS = {
        ("americanfootball_nfl",   "spreads"): "NFL_spreads",
        ("americanfootball_nfl",   "totals"):  "NFL_totals",
        ("americanfootball_ncaaf", "spreads"): "NCAAF_spreads",
        ("americanfootball_ncaaf", "totals"):  "NCAAF_totals",
        ("basketball_nba",         "spreads"): "NBA_spreads",
        ("basketball_nba",         "totals"):  "NBA_totals",
        ("basketball_ncaab",       "spreads"): "NCAAB_spreads",   # <-- add
        ("basketball_ncaab",       "totals"):  "NCAAB_totals",    # <-- add        
    }

    @lru_cache(maxsize=None)
    def _get_curve(curve_id: str, market: str):
        """
        Return a 'z' function (non-centered logit shape) for the given curve id.
        - totals: z(t) = beta * t
        - spreads: z(s) = beta*s + Σ gamma_k * B_k(s)  (windowed bumps)
        """
        payload = _load_mapping(curve_id, "mappings")
        if market == "totals":
            return _make_totals_curve(payload)
        else:
            return _make_spreads_curve(payload)

    def _pick_anchor_row(gid: str, market: str, team: str, want_same_team: bool) -> pd.Series | None:
        """
        Choose an anchor row on today's board for the same game & market.
        If want_same_team=True, look for same team; else look for the other team.
        If multiple exist, just take the first non-null sharp_odds with a defined point.
        """
        sub = board[(board["game_id"] == gid) & (board["market"] == market)].copy()
        if sub.empty:
            return None
        if want_same_team:
            cand = sub[(sub["team"] == team)]
        else:
            cand = sub[(sub["team"] != team)]
        cand = cand[pd.notna(cand["sharp_odds"]) & pd.notna(cand["point"])]
        if cand.empty:
            return None
        return cand.iloc[0]

    def _map_prob_from_anchor(p_anchor: float, pt_anchor: float, pt_target: float, z_fn) -> float:
        """
        Core mapping: logit-shift using your global curve z(·)
        logit(p_tgt) = logit(p_anchor) + (z(pt_tgt) - z(pt_anchor))
        """
        return float(_sigmoid(_logit(p_anchor) + (z_fn(pt_target) - z_fn(pt_anchor))))

    # Iterate rows that need mapping
    for idx in need_map_mask:
        r = bets.loc[idx]
        sport  = str(r.get("sport", ""))
        market = str(r.get("market", ""))
        team   = str(r.get("team", ""))
        try:
            target_point = float(r.get("point"))
        except Exception:
            target_point = np.nan

        # Only apply mapping for our configured sports/markets and valid point
        curve_id = MAPPING_IDS.get((sport, market))
        if (curve_id is None) or (not np.isfinite(target_point)):
            continue  # not a mapped league/market or we have no point → skip

        # Build the curve once (cached)
        z = _get_curve(curve_id, market)

        # Decide SAME-team vs OTHER-team anchor based on your rules:
        # - spreads: use SAME team if bet point > 0 (underdog), OTHER team if bet point < 0 (favorite)
        # - totals: use SAME team if "Over", OTHER team if "Under"
        if market == "spreads":
            want_same_team = bool(target_point > 0)
        else:  # totals
            tl = team.lower()
            want_same_team = ("over" in tl)

        anchor = _pick_anchor_row(r.game_id, market, team, want_same_team=want_same_team)
        if anchor is None:
            continue  # nothing to map from

        try:
            pt_anchor = float(anchor.point)
            odds_anchor = float(anchor.sharp_odds)
            if not (np.isfinite(pt_anchor) and np.isfinite(odds_anchor) and odds_anchor > 0):
                continue
            p_anchor = 1.0 / odds_anchor
        except Exception:
            continue

        # Compute mapped probability per market semantics
        if market == "spreads":
            # Curves are on UNDERDOG probability at positive spreads
            s_target = abs(float(target_point))
            # We must map on the underdog side:
            # If bet is underdog (+): anchor SAME team (should be the underdog); p_und_target directly
            # If bet is favorite (-): anchor OTHER team (underdog); then flip back to favorite
            p_und_target = _map_prob_from_anchor(p_anchor, float(pt_anchor), s_target, z)
            p_target = p_und_target if (target_point > 0) else (1.0 - p_und_target)
        else:
            # totals: curves are on Over probability
            t_target = float(target_point)
            p_over_target = _map_prob_from_anchor(p_anchor, float(pt_anchor), t_target, z)
            p_target = p_over_target if ("over" in team.lower()) else (1.0 - p_over_target)

        if p_target <= 0 or p_target >= 1:
            continue  # guard against numerical edge cases

        bets.at[idx, "closing_line"] = 1.0 / p_target



def refresh_tennis_commence_times(bets: pd.DataFrame, board: pd.DataFrame) -> None:
    """
    Tennis-only fix for placeholder commence times:
    If a tennis bet's stored commence_time is in the past (placeholder),
    keep polling the latest board for a newer commence_time that is in the future.
    Do NOT touch closing_line here (prevents live-odds leakage).
    """
    if bets.empty or board.empty:
        return

    now = pd.Timestamp.utcnow()

    # Normalize types
    bets["commence_time"]  = pd.to_datetime(bets["commence_time"],  utc=True, errors="coerce")
    board = board.copy()
    board["commence_time"] = pd.to_datetime(board["commence_time"], utc=True, errors="coerce")

    # Detect tennis rows with placeholder already passed
    tennis_mask = bets["sport"].astype(str).str.lower().str.startswith("tennis")
    past_mask   = bets["commence_time"] <= now
    gap_mask    = tennis_mask & past_mask
    if not gap_mask.any():
        return

    key_cols = ["game_id", "team", "market", "point"]

    # Merge only commence_time from the board; never read odds here
    gap = bets.loc[gap_mask, key_cols + ["commence_time"]]
    board_dedup = board.drop_duplicates(subset=key_cols, keep="first")
    merged = gap.merge(
        board_dedup[key_cols + ["commence_time"]],
        on=key_cols, how="left", suffixes=("", "_new")
    )

    # If the API publishes a newer FUTURE commence_time, accept it
    for idx, ct_new in zip(gap.index, merged["commence_time_new"]):
        if pd.notna(ct_new):
            ct_new = pd.to_datetime(ct_new, utc=True)
            cur    = bets.at[idx, "commence_time"]
            if pd.isna(cur) or (ct_new > now and ct_new > cur):
                bets.at[idx, "commence_time"] = ct_new
                # Optional: clear stale closing_line on revival (uncomment if you prefer)
                # bets.at[idx, "closing_line"] = pd.NA



# ─── NEW helper  (place near update_closing_lines) ───────────
SNAP_DIR   = DATA_DIR / "snapshots"          # root folder — respects DATA_DIR env var
EV_CUTOFF  = -0.5
LAG_COLS  = [f"sharp_odds_lag{k}" for k in range(1, 26)]
MINS_COLS = [f"mins_ago_lag{k}"   for k in range(1, 26)]

SNAP_COLS  = [
    "snapshot_time", "sport", "game_id", "commence_time", "team",
    "market", "point", "sharp_odds", "odds_from_best_book",
    "ev", "kelly", "closing_line", "clv", "first_line", "first_point", "time_of_first_line",
    *LAG_COLS, *MINS_COLS,
]
# -----------------------------------------------------------------------
# put this once, near SNAP_COLS / NUMERIC
SNAP_SCHEMA = pa.schema([
    ("snapshot_time",        pa.timestamp("us", tz="UTC")),
    ("sport",                pa.string()),
    ("game_id",              pa.string()),
    ("commence_time",        pa.timestamp("us", tz="UTC")),
    ("team",                 pa.string()),
    ("market",               pa.string()),
    ("point",                pa.float64()),
    ("sharp_odds",           pa.float64()),
    ("odds_from_best_book",  pa.float64()),
    ("ev",                   pa.float64()),
    ("kelly",                pa.float64()),
    ("closing_line",         pa.float64()),
    ("clv",                  pa.float64()),
    ("first_line",           pa.float64()),
    ("first_point",          pa.float64()),
    ("time_of_first_line",   pa.timestamp("us", tz="UTC")),
    *[(c, pa.float64()) for c in LAG_COLS],
    *[(c, pa.float64()) for c in MINS_COLS],
])

def _ensure_snapshot_cols(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in SNAP_COLS:
        if c not in out.columns:
            out[c] = (pd.NaT if c == "time_of_first_line" or c == "snapshot_time"
                      else np.nan)
    # enforce timestamp dtypes
    out["snapshot_time"] = pd.to_datetime(out["snapshot_time"], utc=True, errors="coerce")
    out["commence_time"] = pd.to_datetime(out["commence_time"], utc=True, errors="coerce")
    out["time_of_first_line"] = pd.to_datetime(out["time_of_first_line"], utc=True, errors="coerce")
    return out


def append_snapshot(board: pd.DataFrame) -> None:
    if board.empty:
        return

    snap = board.loc[board["ev"] >= EV_CUTOFF].copy()

    snap["odds_from_best_book"] = pd.to_numeric(snap["book_odds"], errors="coerce")

    snap.insert(0, "snapshot_time", pd.Timestamp.utcnow())
    snap["closing_line"] = np.nan
    snap["clv"]          = np.nan
    # Make sure all expected snapshot columns exist (adds NaNs if missing)
    snap = _ensure_snapshot_cols(snap)
    snap = snap[SNAP_COLS]

    # ========== write one file per scrape ====================
    day_dir = SNAP_DIR / f"{pd.Timestamp.utcnow():%Y%m%d}"
    day_dir.mkdir(parents=True, exist_ok=True)

    fname  = day_dir / f"part-{pd.Timestamp.utcnow():%H%M%S%f}.parquet"
    # force all numeric columns to float64 so every part has the same Arrow schema
    # Ensure consistent dtypes for numerics (Arrow schema consistency)
    NUMERIC = ["ev", "kelly", "sharp_odds", "odds_from_best_book",
               "closing_line", "clv", "point", "first_line", "first_point", *LAG_COLS, *MINS_COLS]
    for c in NUMERIC:
        if c in snap.columns:
            snap[c] = pd.to_numeric(snap[c], errors="coerce").astype(float)

    table = pa.Table.from_pandas(snap, schema=SNAP_SCHEMA, preserve_index=False)
    pq.write_table(table, fname)




def backfill_snapshot_clv(latest_board: pd.DataFrame,
                        lookback_days: int = 3) -> None:
    """
    Update `closing_line` and `clv` for each snapshot folder dated
    [today, today-1, … today-(lookback_days-1)].

    A row qualifies for update if
        • commence_time > now OR
        • closing_line is NaN
    """
    now = pd.Timestamp.utcnow()

    for d in range(lookback_days):
        day_str = (now - pd.Timedelta(days=d)).strftime("%Y%m%d")
        day_dir = SNAP_DIR / day_str
        if not day_dir.exists():
            continue

        # ---------- load the entire day ----------
        snap = (
            ds.dataset(day_dir, format="parquet", schema=SNAP_SCHEMA)
            .to_table()
            .to_pandas()
            )

        # rows that still need a closing price
        future_mask  = pd.to_datetime(snap["commence_time"], utc=True) > now
        missing_mask = snap["closing_line"].isna()
        need_upd_idx = snap.index[future_mask | missing_mask]

        if need_upd_idx.empty:
            continue

        # ---------- merge fresh sharp_odds -------
        key_cols = ["game_id", "team", "market", "point"]
        
        
        
        
        board_dedup = latest_board.drop_duplicates(subset=key_cols, keep="first")
        merged = snap.loc[need_upd_idx].merge(
            board_dedup[key_cols + ["sharp_odds"]],
            on=key_cols, how="left", suffixes=("", "_new")
        )

        # fill closing_line where we found a newer sharp price
        has_new = merged["sharp_odds_new"].notna()
        snap.loc[need_upd_idx[has_new], "closing_line"] = \
            merged.loc[has_new, "sharp_odds_new"].values

        # ---------- recompute clv ---------------
        mask = snap["closing_line"].notna() & (snap["closing_line"] > 0)
        snap.loc[mask, "clv"] = (
            (1 / snap.loc[mask, "closing_line"])
            * snap.loc[mask, "odds_from_best_book"] - 1
        )

        # ---------- overwrite folder ------------
        for p in day_dir.glob("part-*.parquet"):
            p.unlink()                                # remove old parts
        pq.write_table(
            pa.Table.from_pandas(snap, preserve_index=False),
            day_dir / "part-000000.parquet"
        )



def run_once(bets: pd.DataFrame) -> dict:
    """
    Execute one complete poll cycle.

    Takes the current bets DataFrame, runs the full pipeline, and returns
    all outputs without touching Discord, the CSV, or the display.  The
    caller (main) is responsible for posting, persisting, and sleeping.

    Parameters
    ----------
    bets : pd.DataFrame
        Tracked bets going into this cycle (may be empty on first run).
        A copy is made internally so the caller's object is never mutated.

    Returns
    -------
    dict:
        latest_board  – full edge board DataFrame
        latest_output – filtered pick output (14 columns)
        bets          – updated bets DataFrame for this cycle
        new_rows      – rows appended this cycle (empty df if none)
        to_send       – unposted rows ready for Discord (copy)
        n_bets        – int: total tracked bets after this cycle
        n_new         – int: rows appended this cycle
        n_to_send     – int: rows queued for posting
    """
    bets = bets.copy()

    # ── 1. Fetch fresh board and filtered output ──────────────────────────
    latest_board  = run_edge_board()
    # Commented hotfix (re-enable if a duplicate league appears):
    #if "sport" in latest_board.columns:
    #    mask_league1 = latest_board["sport"].astype(str).eq("soccer_england_league1")
    #    if mask_league1.any():
    #        print(f"[HOTFIX] Dropping {mask_league1.sum()} League One rows.")
    #        latest_board = latest_board.loc[~mask_league1].copy()
    latest_output = build_edge_output(latest_board)

    # ── 2. Snapshot & backfill CLV ────────────────────────────────────────
    append_snapshot(latest_board)
    backfill_snapshot_clv(latest_board)

    # ── 3. Init bets column schema on first run ───────────────────────────
    if bets.empty:
        bet_cols = (
            ["found_at"]
            + latest_output.columns.tolist()
            + ["closing_line", "clv", "posted", "tier"]
        )
        bets = pd.DataFrame(columns=bet_cols)

    # ── 4. Find new / upgraded rows ───────────────────────────────────────
    key = ["game_id", "market", "stars"]

    new_rows = (
        latest_output
        .merge(bets[key], on=key, how="left", indicator=True)
        .query("_merge == 'left_only'")
        .drop(columns="_merge")
    )

    if not new_rows.empty:
        # Keep only rows whose stars exceed the current max for that game+market
        cur_max = (
            bets.groupby(["game_id", "market"])["stars"]
                .max()
                .rename("cur_max_stars")
        )
        new_rows = (
            new_rows
            .merge(cur_max, on=["game_id", "market"], how="left")
            .query("cur_max_stars.isna() or stars > cur_max_stars")
            .drop(columns="cur_max_stars")
        )

        if not new_rows.empty:
            # ── 5. Opposite-side guard: never bet both sides of the same game+market
            last_side = (
                bets.sort_values("found_at")
                    .drop_duplicates(subset=["game_id", "market"], keep="last")
                    .set_index(["game_id", "market"])["team"]
            )
            new_rows["team_old"] = new_rows.apply(
                lambda r: last_side.get((r.game_id, r.market), np.nan),
                axis=1,
            )
            new_rows = (
                new_rows
                .loc[
                    new_rows["team_old"].isna()
                    | (new_rows["team"] == new_rows["team_old"])
                ]
                .drop(columns="team_old")
                .copy()
            )

        if not new_rows.empty:
            # ── 6. Append surviving rows ──────────────────────────────────
            # Keep only the max-EV book per outcome (one bet per opportunity)
            new_rows = (
                new_rows
                .sort_values("ev", ascending=False)
                .drop_duplicates(subset=["game_id", "team", "market", "point"], keep="first")
            )
            new_rows.insert(0, "found_at", pd.Timestamp.utcnow())
            new_rows["closing_line"] = np.nan
            new_rows["posted"]       = 0
            new_rows["tier"]         = np.nan
            bets = pd.concat([bets, new_rows], ignore_index=True)

    # ── 7. Update closing lines and CLV ───────────────────────────────────
    refresh_tennis_commence_times(bets, latest_board)
    update_closing_lines(bets, latest_board)

    mask = bets["closing_line"].notna() & (bets["closing_line"] > 0)
    p_close = 1 / bets.loc[mask, "closing_line"]
    bets.loc[mask, "clv"] = p_close * bets.loc[mask, "odds_from_best_book"] - 1

    # ── 8. Dedup rule 1: h2h vs spread conflict → drop later-found row ───
    conflict_drop = []
    for gid, grp in bets.groupby("game_id"):
        if {"h2h", "spreads"}.issubset(grp["market"].unique()):
            h2h_rows    = grp[grp["market"] == "h2h"]
            spread_rows = grp[grp["market"] == "spreads"]
            for _, h in h2h_rows.iterrows():
                for _, s in spread_rows.iterrows():
                    if h["team"] != s["team"]:
                        later_idx = h.name if h["found_at"] > s["found_at"] else s.name
                        conflict_drop.append(later_idx)
    bets.drop(index=conflict_drop, inplace=True)

    # ── 9. Dedup rule 2: duplicate h2h on same game+found_at → keep highest EV
    h2h = bets[bets["market"] == "h2h"].copy()
    keep = (
        h2h.sort_values(["game_id", "found_at", "ev"], ascending=[True, True, False])
           .drop_duplicates(subset=["game_id", "found_at"], keep="first")
           .index
    )
    bets.drop(index=h2h.index.difference(keep), inplace=True)

    # ── 10. Identify unposted rows ────────────────────────────────────────
    to_send = bets[bets["posted"] == 0].copy()

    return {
        "latest_board":  latest_board,
        "latest_output": latest_output,
        "bets":          bets,
        "new_rows":      new_rows,
        "to_send":       to_send,
        "n_bets":        len(bets),
        "n_new":         len(new_rows),
        "n_to_send":     len(to_send),
    }


def main():
    global latest_board, latest_output, bets

    logger.info("Worker starting — DATA_DIR=%s  ACTIVE_SPORTS=%s",
                DATA_DIR, os.getenv("ACTIVE_SPORTS", "(from settings.env)"))

    # ── Load any prior bets.csv (once, before the loop) ──────────────────
    if BETS_PATH.is_file():
        bets = pd.read_csv(
            BETS_PATH,
            parse_dates=["found_at", "commence_time"],
            low_memory=False,
        )
        if "best_book" in bets.columns and "book" not in bets.columns:
            bets.rename(columns={"best_book": "book"}, inplace=True)
        logger.info("Loaded %d rows from %s", len(bets), BETS_PATH)
    else:
        bets = pd.DataFrame()

    while True:
        t0 = time.time()

        # ── Pull remote config from Supabase and apply to env ─────────────
        remote_cfg = sb.fetch_worker_config()
        for k, v in remote_cfg.items():
            os.environ[k.upper()] = v

        # ── Run one complete poll cycle ───────────────────────────────────
        run_id = sb.start_model_run(active_sports=os.getenv("ACTIVE_SPORTS", ""))
        try:
            result = run_once(bets)
        except Exception as _exc:
            sb.fail_model_run(run_id, _exc)
            logger.error("run_once() failed — sleeping 60s before retry. Error: %s", _exc)
            traceback.print_exc()
            time.sleep(60)
            continue
        latest_board  = result["latest_board"]
        latest_output = result["latest_output"]
        bets          = result["bets"]
        to_send       = result["to_send"]

        # ── Post anything not yet sent to Discord ─────────────────────────
        for idx, r in to_send.iterrows():
            queue_pick(r)
            bets.at[idx, "posted"] = 1
            bets.at[idx, "tier"]   = _tier_for_stars(r)

        # ── Reconcile with disk (settlement worker may have removed rows) ─
        try:
            disk = pd.read_csv(
                BETS_PATH,
                parse_dates=["found_at", "commence_time"],
                low_memory=False,
            )
            if not disk.empty and not bets.empty:
                key_cols = ["game_id", "market", "team", "found_at"]
                if "found_at" in bets and not pd.api.types.is_datetime64_any_dtype(bets["found_at"]):
                    bets["found_at"] = pd.to_datetime(bets["found_at"], utc=True, errors="coerce")
                if "found_at" in disk and not pd.api.types.is_datetime64_any_dtype(disk["found_at"]):
                    disk["found_at"] = pd.to_datetime(disk["found_at"], utc=True, errors="coerce")
                disk_keys    = set(map(tuple, disk[key_cols].astype(str).to_numpy()))
                now_utc      = pd.Timestamp.utcnow()
                mem_keys     = bets[key_cols].astype(str).apply(tuple, axis=1)
                to_drop_mask = (~mem_keys.isin(disk_keys)) & (bets["commence_time"] <= now_utc)
                if to_drop_mask.any():
                    bets = bets.loc[~to_drop_mask].copy()
        except FileNotFoundError:
            pass
        except Exception as e:
            print("[persist] Reconcile warning:", e)

        bets.to_csv(BETS_PATH, index=False)
        sb.finish_model_run(run_id, result, latest_output)
        sb.upsert_tracked_picks(bets)

        elapsed = time.time() - t0
        logger.info(
            "cycle complete | bets=%d | new=%d | output=%d | elapsed=%.1fs",
            len(bets), result["n_new"], len(latest_output), elapsed,
        )

        # ── Wait for next cycle ───────────────────────────────────────────
        poll    = current_poll_seconds()
        elapsed = time.time() - t0
        time.sleep(max(0, poll - elapsed))


if __name__ == "__main__":
    main()


