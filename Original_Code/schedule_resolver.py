"""
schedule_resolver.py — daily schedule automation for the Quant Bet Labs worker.

Runs once at startup and once at 5 AM ET each day. Determines which sport groups
have games within their configured horizon, computes an API-quota-aware daytime
poll interval, and writes the results back to Supabase worker_config.

The main loop in bet_scheduler7.py already calls fetch_worker_config() on every
cycle, so new values are picked up automatically — no restart needed.

To tune sport coverage: edit LEAGUE_THRESHOLDS (add/remove leagues, adjust
threshold and horizon_h). To tune API cost assumptions: edit SPORT_GROUP_CREDITS.
"""

import logging
import math
import os
import time
from datetime import datetime, timedelta, timezone

import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1. League config — one entry per Odds API league key
# ---------------------------------------------------------------------------
# threshold : minimum number of events in the horizon window to activate
# horizon_h : how many hours ahead to check for games
# sport_group: the ACTIVE_SPORTS token that run_edge_board_v2 recognises

LEAGUE_THRESHOLDS: dict[str, dict] = {
    # ── Non-soccer ──────────────────────────────────────────────────────────
    "baseball_mlb":           {"sport_group": "BASEBALL", "threshold": 4, "horizon_h": 24},
    "icehockey_nhl":          {"sport_group": "HOCKEY",   "threshold": 2, "horizon_h": 24},
    "basketball_nba":         {"sport_group": "NBA",      "threshold": 2, "horizon_h": 24},
    "basketball_ncaab":       {"sport_group": "NCAAB",    "threshold": 4, "horizon_h": 24},
    "americanfootball_nfl":   {"sport_group": "NFL",      "threshold": 1, "horizon_h": 48},
    "americanfootball_ncaaf": {"sport_group": "NCAAF",    "threshold": 2, "horizon_h": 48},
    "mma_mixed_martial_arts": {"sport_group": "FIGHTS",   "threshold": 1, "horizon_h": 48},
    "boxing_boxing":          {"sport_group": "FIGHTS",   "threshold": 1, "horizon_h": 48},

    # ── Tennis — Grand Slams only; horizon_h=24 matches the engine's horizon_days=1.
    #    Off-season keys return 0 events (treated as 0) — harmless.
    "tennis_atp_aus_open_singles": {"sport_group": "TENNIS", "threshold": 2, "horizon_h": 24},
    "tennis_wta_aus_open_singles": {"sport_group": "TENNIS", "threshold": 2, "horizon_h": 24},
    "tennis_atp_french_open":     {"sport_group": "TENNIS", "threshold": 2, "horizon_h": 24},
    "tennis_wta_french_open":     {"sport_group": "TENNIS", "threshold": 2, "horizon_h": 24},
    "tennis_atp_wimbledon":       {"sport_group": "TENNIS", "threshold": 2, "horizon_h": 24},
    "tennis_wta_wimbledon":       {"sport_group": "TENNIS", "threshold": 2, "horizon_h": 24},
    "tennis_atp_us_open":         {"sport_group": "TENNIS", "threshold": 2, "horizon_h": 24},
    "tennis_wta_us_open":         {"sport_group": "TENNIS", "threshold": 2, "horizon_h": 24},

    # ── Soccer — each league has its own threshold ───────────────────────────
    "soccer_fifa_world_cup":        {"sport_group": "SOCCER", "threshold": 2, "horizon_h": 48},
    "soccer_fifa_world_cup_womens": {"sport_group": "SOCCER", "threshold": 2, "horizon_h": 48},
    "soccer_france_ligue_one":      {"sport_group": "SOCCER", "threshold": 5, "horizon_h": 48},
    "soccer_germany_bundesliga":    {"sport_group": "SOCCER", "threshold": 5, "horizon_h": 48},
    "soccer_italy_serie_a":         {"sport_group": "SOCCER", "threshold": 5, "horizon_h": 48},
    "soccer_spain_la_liga":         {"sport_group": "SOCCER", "threshold": 4, "horizon_h": 48},
    "soccer_uefa_champs_league":    {"sport_group": "SOCCER", "threshold": 3, "horizon_h": 48},
    "soccer_uefa_europa_league":    {"sport_group": "SOCCER", "threshold": 4, "horizon_h": 48},
    "soccer_usa_mls":               {"sport_group": "SOCCER", "threshold": 4, "horizon_h": 48},
    "soccer_epl":                   {"sport_group": "SOCCER", "threshold": 4, "horizon_h": 48},
}

# API credits consumed per /odds call for one league in this group.
# Formula: n_markets × ceil(n_books / 10)
# All groups use 10 books (8 soft + PIN + BETONL) → 1 region-equivalent,
# except SOCCER which uses 9 books (8 soft + PIN only) → still 1 region-equivalent.
# h2h + spreads + totals = 3 markets → 3 credits.
# Soccer and Fights: h2h only = 1 market → 1 credit per league.
SPORT_GROUP_CREDITS: dict[str, int] = {
    "BASEBALL": 3,
    "HOCKEY":   3,
    "NBA":      3,
    "NCAAB":    3,
    "NFL":      3,
    "NCAAF":    3,
    "SOCCER":   1,  # h2h only
    "FIGHTS":   1,  # h2h only
    "TENNIS":   1,  # h2h only
}

# ---------------------------------------------------------------------------
# 2. Internal helpers
# ---------------------------------------------------------------------------

def _fetch_events(league_key: str, horizon_h: int, api_key: str) -> tuple[list | None, dict | None]:
    """
    Call /events (free — does not consume quota) for one league.
    Returns (events_list, response_headers) or (None, None) on failure.
    A 404 means the league is not in season — returns ([], headers).
    """
    now   = datetime.now(timezone.utc)
    until = now + timedelta(hours=horizon_h)
    url = (
        f"https://api.the-odds-api.com/v4/sports/{league_key}/events"
        f"?apiKey={api_key}"
        f"&commenceTimeFrom={now.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        f"&commenceTimeTo={until.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    )

    backoffs = [0, 1.0, 3.0]
    last_err = None
    for sleep_s in backoffs:
        if sleep_s:
            time.sleep(sleep_s)
        try:
            resp = requests.get(url, timeout=12)
        except Exception as exc:
            last_err = exc
            continue

        if resp.status_code == 404:
            return [], dict(resp.headers)

        if resp.status_code in (429, 500, 502, 503, 504):
            last_err = RuntimeError(f"HTTP {resp.status_code}")
            continue

        if resp.status_code != 200:
            logger.warning("[schedule] %s returned HTTP %d", league_key, resp.status_code)
            return None, None

        try:
            return resp.json(), dict(resp.headers)
        except ValueError:
            return None, None

    logger.warning("[schedule] %s: all retries failed — %s", league_key, last_err)
    return None, None


def _days_until_reset(headers: dict) -> int:
    """
    Parse x-requests-reset from response headers and return days until quota reset.
    Tries Unix timestamp (int) then ISO date string.
    Falls back to days until end of the current calendar month.
    """
    raw = headers.get("x-requests-reset") or headers.get("X-Requests-Reset")

    if raw:
        # Try Unix timestamp first
        try:
            reset_dt = datetime.fromtimestamp(int(raw), tz=timezone.utc)
            delta = (reset_dt - datetime.now(timezone.utc)).total_seconds()
            return max(1, math.ceil(delta / 86400))
        except (ValueError, OSError):
            pass

        # Try ISO string
        try:
            from datetime import date as _date
            reset_date = _date.fromisoformat(str(raw)[:10])
            today = datetime.now(timezone.utc).date()
            return max(1, (reset_date - today).days)
        except ValueError:
            pass

    # Fallback: days remaining in current month
    now = datetime.now(timezone.utc)
    if now.month == 12:
        first_next = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        first_next = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
    return max(1, (first_next - now).days)


# ---------------------------------------------------------------------------
# 3. Main entry point
# ---------------------------------------------------------------------------

def run_daily() -> None:
    """
    Resolve today's active sports and optimal poll interval, then write the
    result to Supabase worker_config (unless SCHEDULE_AUTO=false).

    Called once at worker startup and once daily at 5 AM ET.
    """
    import supabase_writer as sb  # local import to avoid circular at module level

    logger.info("[schedule] Daily schedule resolution starting")

    api_key = os.getenv("ODDS_API_KEY")
    if not api_key:
        logger.error("[schedule] ODDS_API_KEY missing — skipping resolver")
        return

    schedule_auto = os.getenv("SCHEDULE_AUTO", "true").strip().lower()
    dry_run = (schedule_auto == "false")
    if dry_run:
        logger.info("[schedule] SCHEDULE_AUTO=false — running read-only (will not write)")

    # ── Step 1: Fetch events for every configured league ─────────────────────
    first_headers: dict | None = None
    active_leagues: dict[str, int] = {}   # league_key → event count
    failed_leagues: list[str]      = []

    for league_key, cfg in LEAGUE_THRESHOLDS.items():
        events, headers = _fetch_events(league_key, cfg["horizon_h"], api_key)

        if first_headers is None and headers:
            first_headers = headers

        if events is None:
            failed_leagues.append(league_key)
            continue

        count = len(events)
        meets = count >= cfg["threshold"]
        logger.info(
            "[schedule] %-40s %2d events  threshold=%d  %s",
            league_key, count, cfg["threshold"], "✓" if meets else "✗",
        )
        if meets:
            active_leagues[league_key] = count

    if failed_leagues:
        logger.warning("[schedule] Failed to fetch events for: %s", ", ".join(failed_leagues))

    # ── Step 2: Group active leagues by sport group ───────────────────────────
    active_groups: dict[str, list[str]] = {}
    for league_key in active_leagues:
        group = LEAGUE_THRESHOLDS[league_key]["sport_group"]
        active_groups.setdefault(group, []).append(league_key)

    if not active_groups:
        logger.warning("[schedule] No sport groups meet threshold — keeping existing config unchanged")
        return

    # ── Step 3: Credits per poll cycle ───────────────────────────────────────
    # Each active league in a group costs SPORT_GROUP_CREDITS[group] per poll.
    credits_per_poll = sum(
        SPORT_GROUP_CREDITS[group] * len(leagues)
        for group, leagues in active_groups.items()
    )
    logger.info("[schedule] Active groups: %s", ", ".join(sorted(active_groups)))
    logger.info("[schedule] Credits per poll cycle: %d", credits_per_poll)

    # ── Step 4: Parse quota from headers ─────────────────────────────────────
    remaining: int | None = None
    reset_days: int = _days_until_reset(first_headers or {})

    if first_headers:
        raw_rem = first_headers.get("x-requests-remaining") or first_headers.get("X-Requests-Remaining")
        try:
            remaining = int(raw_rem)
        except (TypeError, ValueError):
            pass

    # ── Step 5: Compute day_poll_minutes ─────────────────────────────────────
    if remaining is None:
        # Quota unreadable — keep the current env value as a safe default
        day_poll_minutes = int(os.getenv("DAY_POLL_MINUTES", "15"))
        logger.warning(
            "[schedule] x-requests-remaining unreadable — defaulting to current DAY_POLL_MINUTES=%d",
            day_poll_minutes,
        )
    else:
        night_start    = int(os.getenv("NIGHT_START_HOUR",   "22"))
        night_end      = int(os.getenv("NIGHT_END_HOUR",      "7"))
        night_poll_min = int(os.getenv("NIGHT_POLL_MINUTES", "120"))

        # Night window spans overnight: (7 - 22 + 24) % 24 = 9 h = 540 min
        night_window_min = ((night_end - night_start) % 24) * 60   # 540
        daytime_min      = 24 * 60 - night_window_min               # 900

        night_polls    = night_window_min // night_poll_min          # 4
        night_cost     = night_polls * credits_per_poll
        daily_budget   = remaining / reset_days
        daytime_budget = daily_budget - night_cost

        logger.info(
            "[schedule] remaining=%d  reset_days=%d  daily_budget=%.1f  "
            "night_cost=%d  daytime_budget=%.1f",
            remaining, reset_days, daily_budget, night_cost, daytime_budget,
        )

        if daytime_budget <= 0:
            # So little budget remaining that even night polling eats it all.
            # Fall back to a single daytime poll matching the night interval.
            day_poll_minutes = night_poll_min
            logger.warning(
                "[schedule] Daytime budget exhausted — setting day_poll_minutes=%d",
                day_poll_minutes,
            )
        else:
            max_daytime_polls = daytime_budget / credits_per_poll
            day_poll_minutes  = round(daytime_min / max_daytime_polls)

        logger.info("[schedule] Computed day_poll_minutes: %d", day_poll_minutes)

    # ── Step 6: Build the config dict to write ────────────────────────────────
    active_sports_str = ",".join(sorted(active_groups.keys()))

    config: dict[str, str] = {
        "active_sports":    active_sports_str,
        "day_poll_minutes": str(day_poll_minutes),
    }

    # For multi-league groups, write which specific leagues are active so the
    # engine only queries leagues with games (saves credits on subsequent polls).
    for group, leagues in active_groups.items():
        env_key = f"leagues_{group.lower()}"
        config[env_key] = ",".join(sorted(leagues))

    logger.info("[schedule] Config resolved: %s", config)

    # ── Step 7: Write to Supabase ─────────────────────────────────────────────
    if dry_run:
        logger.info("[schedule] Dry run — skipping Supabase write")
        return

    for key, value in config.items():
        sb.upsert_worker_config(key, value)

    logger.info("[schedule] Config written to worker_config (%d keys)", len(config))
