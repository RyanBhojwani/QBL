"""
supabase_writer.py — write-only adapter between the Python worker and Supabase.

Activated only when SUPABASE_ENABLED=1.  All functions are non-fatal: a Supabase
failure logs a warning and the cycle continues; Discord and CSV are unaffected.

Required env vars (when SUPABASE_ENABLED=1):
    SUPABASE_URL         https://<project-ref>.supabase.co
    SUPABASE_SERVICE_KEY service-role secret key (never exposed to frontend)

Optional:
    SUPABASE_ENABLED     "1" to activate; omit or "0" for local / CSV-only runs
"""

import json
import logging
import os
from datetime import datetime, timezone

import pandas as pd

logger = logging.getLogger(__name__)

SUPABASE_ENABLED: bool = os.getenv("SUPABASE_ENABLED", "0") == "1"

_BATCH_SIZE = 500   # max rows per Supabase insert call


# ─────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────

def _client():
    """Lazily create a Supabase client. Raises if env vars are missing."""
    from supabase import create_client  # noqa: PLC0415
    return create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_KEY"],
    )


def _to_records(df: pd.DataFrame) -> list[dict]:
    """
    Convert a DataFrame to a list of JSON-safe dicts suitable for Supabase insert.

    Conversion rules applied by df.to_json():
        pd.Timestamp  → ISO 8601 string  (e.g. "2026-05-05T14:00:00.000Z")
        np.nan / pd.NA → null            (becomes Python None after json.loads)
        np.int64 / np.float64 → Python int / float
    """
    return json.loads(df.to_json(orient="records", date_format="iso"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─────────────────────────────────────────────────────────────────
# model_runs
# ─────────────────────────────────────────────────────────────────

def fetch_worker_config() -> dict[str, str]:
    """Read all rows from worker_config. Returns {} if Supabase is disabled or on error."""
    if not SUPABASE_ENABLED:
        return {}
    try:
        resp = _client().table("worker_config").select("key,value").execute()
        return {row["key"]: row["value"] for row in (resp.data or [])}
    except Exception as exc:
        logger.warning("Supabase: fetch_worker_config failed: %s", exc)
        return {}


def upsert_worker_config(key: str, value: str) -> None:
    """Upsert a single key/value row in worker_config. No-op if Supabase is disabled."""
    if not SUPABASE_ENABLED:
        return
    try:
        _client().table("worker_config").upsert(
            {"key": key, "value": value},
            on_conflict="key",
        ).execute()
    except Exception as exc:
        logger.warning("Supabase: upsert_worker_config(%s) failed: %s", key, exc)


def start_model_run(active_sports: str = "") -> str | None:
    """
    Insert a model_run row at the start of each poll cycle.

    Returns the new run_id (UUID string) so finish_model_run / fail_model_run
    can update it.  Returns None if Supabase is disabled or the insert fails.
    """
    if not SUPABASE_ENABLED:
        return None
    try:
        res = _client().table("model_runs").insert({
            "status":        "running",
            "active_sports": active_sports,
        }).execute()
        run_id: str = res.data[0]["id"]
        logger.info("Supabase: model_run started  id=%s", run_id)
        return run_id
    except Exception as exc:
        logger.warning("Supabase: start_model_run failed: %s", exc)
        return None


def finish_model_run(
    run_id: str | None,
    result: dict,
    latest_output: pd.DataFrame,
) -> None:
    """
    Write current_picks then mark the model_run row as 'success'.
    Called after run_once() returns without raising.
    """
    if not SUPABASE_ENABLED:
        return

    write_current_picks(latest_output, run_id)

    if run_id is None:
        return
    try:
        _client().table("model_runs").update({
            "finished_at":         _now_iso(),
            "status":              "success",
            "latest_board_count":  len(result.get("latest_board", [])),
            "latest_output_count": len(latest_output),
            "new_rows_count":      result.get("n_new", 0),
            "to_send_count":       result.get("n_to_send", 0),
        }).eq("id", run_id).execute()
        logger.info("Supabase: model_run finished id=%s", run_id)
    except Exception as exc:
        logger.warning("Supabase: finish_model_run failed: %s", exc)


def fail_model_run(run_id: str | None, error: Exception) -> None:
    """
    Mark model_run as 'error'.  Called when run_once() raises; the exception
    is re-raised by the caller so existing crash behavior is unchanged.
    """
    if not SUPABASE_ENABLED or run_id is None:
        return
    try:
        _client().table("model_runs").update({
            "finished_at":  _now_iso(),
            "status":       "error",
            "error_message": str(error),
        }).eq("id", run_id).execute()
    except Exception as exc:
        logger.warning("Supabase: fail_model_run failed: %s", exc)


# ─────────────────────────────────────────────────────────────────
# current_picks
# ─────────────────────────────────────────────────────────────────

def write_current_picks(latest_output: pd.DataFrame, run_id: str | None) -> None:
    """
    Replace current_picks with the rows from latest_output.

    MVP strategy — delete then insert:
      1. Delete all existing rows from current_picks.
      2. Insert all rows from latest_output in batches.

    latest_output is produced before we touch the table, so the only
    window where current_picks is empty is a few milliseconds between steps
    1 and 2.  This is acceptable for MVP.  An atomic Postgres RPC can make
    this zero-downtime in a later phase.

    Note: tracked_picks is NOT written here.  The caller (bet_scheduler7.py)
    already deduplicates new picks against existing bets_df before appending;
    the Supabase write for tracked_picks will be added in a separate step.
    """
    if not SUPABASE_ENABLED:
        return

    try:
        client = _client()

        # ── 1. Clear the board ──────────────────────────────────────────
        # Always delete regardless of whether there are new picks — an empty
        # latest_output means no picks exist right now, and the table should
        # reflect that rather than showing stale rows from a previous run.
        client.table("current_picks").delete().gte("stars", 1).execute()

        if latest_output is None or latest_output.empty:
            logger.info("Supabase: current_picks cleared (latest_output is empty — no picks this run).")
            return

        # ── 2. Build records ────────────────────────────────────────────
        df = latest_output.copy()
        records = _to_records(df)
        now_str = _now_iso()
        for r in records:
            r["run_id"]       = run_id
            r["last_updated"] = now_str

        # ── 3. Insert in batches ────────────────────────────────────────
        for i in range(0, len(records), _BATCH_SIZE):
            client.table("current_picks").insert(records[i : i + _BATCH_SIZE]).execute()

        logger.info(
            "Supabase: wrote %d rows to current_picks (run_id=%s).",
            len(records), run_id,
        )

    except Exception as exc:
        logger.warning("Supabase: write_current_picks failed: %s", exc)


# ─────────────────────────────────────────────────────────────────
# raw_model_output
# ─────────────────────────────────────────────────────────────────

def write_raw_output(full_output: pd.DataFrame) -> None:
    """
    Replace raw_model_output with all pre-threshold model rows from this run.

    Same delete-then-insert pattern as write_current_picks.  The table is
    wiped completely on every worker cycle so it always reflects the current
    model run — no stale rows from prior cycles accumulate.

    Used by the Explore tab (team search + sportsbook explorer) to let
    premium/VIP subscribers browse all model output regardless of pick
    thresholds.
    """
    if not SUPABASE_ENABLED:
        return

    try:
        client = _client()

        # Delete all existing rows (id is bigserial starting at 1, so > 0 matches all)
        client.table("raw_model_output").delete().gt("id", 0).execute()

        if full_output is None or full_output.empty:
            logger.info("Supabase: raw_model_output cleared (full_output is empty).")
            return

        df = full_output.copy()
        records = _to_records(df)
        now_str = _now_iso()
        for r in records:
            r["last_updated"] = now_str

        for i in range(0, len(records), _BATCH_SIZE):
            client.table("raw_model_output").insert(records[i : i + _BATCH_SIZE]).execute()

        logger.info("Supabase: wrote %d rows to raw_model_output.", len(records))

    except Exception as exc:
        logger.warning("Supabase: write_raw_output failed: %s", exc)


# ─────────────────────────────────────────────────────────────────
# tracked_picks
# ─────────────────────────────────────────────────────────────────

def upsert_tracked_picks(bets_df: pd.DataFrame) -> None:
    """
    Upsert bets_df into tracked_picks — one row per (game_id, team, market, point).

    Uses the upsert_tracked_picks_batch RPC (PostgreSQL function) because the
    conflict target includes a functional expression COALESCE(point, -9999.0),
    which PostgREST cannot express directly in its upsert API.

    On conflict: updates closing_line, clv, posted, tier only (preserves found_at
    and all model-output columns from the original pick).
    """
    if not SUPABASE_ENABLED:
        return
    if bets_df is None or bets_df.empty:
        return

    try:
        df = bets_df.copy()
        # cast posted int (0/1) → bool; replace pd.NA/NaN tier → None
        df["posted"] = df["posted"].fillna(0).astype(bool)
        df["tier"]   = df["tier"].where(df["tier"].notna(), other=None)

        cols = [
            "found_at", "posted", "tier",
            "sport", "game_id", "commence_time", "team", "market", "point", "book",
            "odds_from_best_book", "sharp_odds", "ev", "kelly", "clv_prob_med",
            "stars", "outcome_threshold", "closing_line", "clv",
        ]
        records = _to_records(df[cols])

        client = _client()
        for i in range(0, len(records), _BATCH_SIZE):
            client.rpc(
                "upsert_tracked_picks_batch",
                {"rows": records[i : i + _BATCH_SIZE]},
            ).execute()

        logger.info("Supabase: upserted %d rows to tracked_picks.", len(records))
    except Exception as exc:
        logger.warning("Supabase: upsert_tracked_picks failed: %s", exc)


# ─────────────────────────────────────────────────────────────────
# tracked_picks — settlement helpers
# ─────────────────────────────────────────────────────────────────

def load_unsettled_picks(now_utc: "pd.Timestamp") -> "pd.DataFrame | None":
    """
    Load past unsettled rows from tracked_picks for settlement.

    Returns a DataFrame with a 'W/L' column (= '') so settle_ledger.py's
    settle_row() works without modification.  Returns None when
    SUPABASE_ENABLED=0 so settle_ledger.py falls back to CSVs.
    Returns an empty DataFrame when Supabase is enabled but there are no
    unsettled past picks.
    """
    if not SUPABASE_ENABLED:
        return None
    try:
        now_iso = now_utc.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        res = (
            _client()
            .table("tracked_picks")
            .select("*")
            .lte("commence_time", now_iso)
            .is_("result", "null")
            .execute()
        )
        if not res.data:
            logger.info("Supabase: no unsettled past picks in tracked_picks.")
            return pd.DataFrame()
        df = pd.DataFrame(res.data)
        df["W/L"] = ""   # blank = unsettled; required by settle_row()
        logger.info("Supabase: loaded %d unsettled picks from tracked_picks.", len(df))
        return df
    except Exception as exc:
        logger.warning("Supabase: load_unsettled_picks failed: %s", exc)
        return None


def update_tracked_picks_results(graded_df: "pd.DataFrame") -> None:
    """
    Write W/L/P back to tracked_picks.result for rows that were just graded.

    Uses the 'id' UUID column returned by load_unsettled_picks() to target
    each row precisely — avoids the COALESCE functional index entirely.
    """
    if not SUPABASE_ENABLED:
        return
    if graded_df is None or graded_df.empty:
        return
    if "id" not in graded_df.columns or "W/L" not in graded_df.columns:
        logger.warning(
            "Supabase: update_tracked_picks_results — missing 'id' or 'W/L' column; skipping."
        )
        return

    try:
        client = _client()
        graded = graded_df[graded_df["W/L"].isin(["W", "L", "P"])]
        count = 0
        for _, row in graded.iterrows():
            client.table("tracked_picks").update(
                {"result": str(row["W/L"])}
            ).eq("id", str(row["id"])).execute()
            count += 1
        logger.info("Supabase: marked %d tracked_picks rows as settled.", count)
    except Exception as exc:
        logger.warning("Supabase: update_tracked_picks_results failed: %s", exc)


# ─────────────────────────────────────────────────────────────────
# settled_picks
# ─────────────────────────────────────────────────────────────────

def upsert_settled_picks(settled_rows: pd.DataFrame) -> None:
    """
    Upsert graded rows from ledger_updated into settled_picks.

    Expects rows with a "W/L" column (Python ledger format); renames it to
    "result" for Supabase.  Only rows with result in {'W','L','P'} are written.
    Conflict key: (game_id, market, team) — matches settled_picks_dedup index.
    """
    if not SUPABASE_ENABLED:
        return
    if settled_rows is None or settled_rows.empty:
        return

    try:
        df = settled_rows.copy()

        # W/L column holds the graded result; result column (from tracked_picks) is stale null.
        # Drop the stale result first so rename doesn't create duplicate columns.
        if "W/L" in df.columns:
            df = df.drop(columns=["result"], errors="ignore")
            df = df.rename(columns={"W/L": "result"})
        df = df[df["result"].isin(["W", "L", "P"])].copy()
        if df.empty:
            return

        # Cast posted int (0/1) → bool
        df["posted"] = df["posted"].fillna(0).astype(bool)
        df["tier"]   = df["tier"].where(df["tier"].notna(), other=None)

        cols = [
            "found_at", "posted", "tier",
            "sport", "game_id", "commence_time", "team", "market", "point", "book",
            "odds_from_best_book", "sharp_odds", "ev", "kelly", "clv_prob_med",
            "stars", "outcome_threshold", "closing_line", "clv", "result",
        ]
        # Only keep columns that exist (ledger may be missing some on first run)
        present = [c for c in cols if c in df.columns]
        records = _to_records(df[present])

        client = _client()
        for i in range(0, len(records), _BATCH_SIZE):
            client.table("settled_picks").upsert(
                records[i : i + _BATCH_SIZE],
                on_conflict="game_id,market,team,book,stars",
            ).execute()

        logger.info("Supabase: upserted %d rows to settled_picks.", len(records))
    except Exception as exc:
        logger.warning("Supabase: upsert_settled_picks failed: %s", exc)


# ─────────────────────────────────────────────────────────────────
# model_results  (nightly computed performance stats)
# ─────────────────────────────────────────────────────────────────

def load_settled_picks() -> "pd.DataFrame | None":
    """
    Load all rows from settled_picks for the nightly results calculation.
    Paginates in pages of 1000 to handle large tables.
    Returns None when SUPABASE_ENABLED=0 so the caller falls back to CSV.
    Returns an empty DataFrame when enabled but the table is empty.
    """
    if not SUPABASE_ENABLED:
        return None
    try:
        client = _client()
        rows: list[dict] = []
        page_size = 1000
        offset = 0
        while True:
            res = (
                client.table("settled_picks")
                .select("*")
                .range(offset, offset + page_size - 1)
                .execute()
            )
            batch = res.data or []
            rows.extend(batch)
            if len(batch) < page_size:
                break
            offset += page_size
        if not rows:
            logger.info("Supabase: settled_picks is empty.")
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        logger.info("Supabase: loaded %d rows from settled_picks.", len(df))
        return df
    except Exception as exc:
        logger.warning("Supabase: load_settled_picks failed: %s", exc)
        return None


def clear_1d_model_results() -> None:
    """
    Delete all time_window='1d' rows from model_results before recomputing.

    The 1d window only shows picks from yesterday. If no picks existed yesterday
    when the calculator last ran, those rows were never written and stale values
    from a prior run persist indefinitely. Clearing first ensures the table always
    reflects the current nightly computation rather than a stale snapshot.
    """
    if not SUPABASE_ENABLED:
        return
    try:
        _client().table("model_results").delete().eq("time_window", "1d").execute()
        logger.info("Supabase: cleared 1d rows from model_results.")
    except Exception as exc:
        logger.warning("Supabase: clear_1d_model_results failed: %s", exc)


def write_model_results(records: list[dict]) -> None:
    """
    Upsert pre-computed model_results rows.
    Conflict key: (time_window, segment_type, segment_val) — one row per combination,
    always overwritten with the latest nightly run.
    """
    if not SUPABASE_ENABLED:
        return
    if not records:
        return
    try:
        client = _client()
        for i in range(0, len(records), _BATCH_SIZE):
            client.table("model_results").upsert(
                records[i : i + _BATCH_SIZE],
                on_conflict="time_window,segment_type,segment_val",
            ).execute()
        logger.info("Supabase: wrote %d rows to model_results.", len(records))
    except Exception as exc:
        logger.warning("Supabase: write_model_results failed: %s", exc)


# ─────────────────────────────────────────────────────────────────
# tracked_picks — post-settlement cleanup
# ─────────────────────────────────────────────────────────────────

def post_settlement_cleanup() -> None:
    """
    Called at the end of every settlement run.  Executes the
    post_settlement_cleanup() Postgres RPC which:

      1. Copies any tracked_picks rows with result IN ('W','L','P') into
         settled_picks (handles picks graded manually in Supabase).
      2. Deletes from tracked_picks every row whose composite key
         (game_id, market, team, book, stars) already exists in settled_picks.

    Using a server-side SQL function avoids all Python ID-serialization issues
    and handles both the just-graded rows AND any backlog from prior runs.
    """
    if not SUPABASE_ENABLED:
        return
    try:
        _client().rpc("post_settlement_cleanup", {}).execute()
        logger.info("Supabase: post_settlement_cleanup complete.")
    except Exception as exc:
        logger.warning("Supabase: post_settlement_cleanup failed: %s", exc)


# ─────────────────────────────────────────────────────────────────
# Cloudflare R2 — daily snapshot backup
# ─────────────────────────────────────────────────────────────────
# Separate from Supabase. Activated when R2_ACCOUNT_ID is set.
# Uses boto3's S3-compatible API pointed at R2's endpoint.

_R2_ENABLED: bool = bool(os.getenv("R2_ACCOUNT_ID"))


def _r2_client():
    try:
        import boto3
        from botocore.config import Config
    except ImportError:
        raise RuntimeError("boto3 not installed — add it to requirements.txt")

    account_id = os.getenv("R2_ACCOUNT_ID")
    return boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def upload_snapshot_to_r2(snap_dir) -> None:
    """
    Upload yesterday's consolidated daily snapshot to R2.

    Called at 4:15 AM ET — after settlement (4:00 AM) consolidates the previous
    day's parts into a single part-000000.parquet, and before the results
    calculator runs (4:30 AM).

    The file is uploaded as YYYYMMDD.parquet at the bucket root. The local file
    is left intact on the Railway volume — R2 is the off-site backup only.
    """
    if not _R2_ENABLED:
        logger.info("[r2] R2_ACCOUNT_ID not set — skipping snapshot upload.")
        return

    from pathlib import Path
    yesterday = (pd.Timestamp.utcnow() - pd.Timedelta(days=1)).strftime("%Y%m%d")
    parquet_path = Path(snap_dir) / yesterday / "part-000000.parquet"

    if not parquet_path.exists():
        logger.warning("[r2] No consolidated snapshot for %s at %s — skipping.", yesterday, parquet_path)
        return

    bucket = os.getenv("R2_BUCKET", "qbl-snapshots")
    key = f"{yesterday}.parquet"

    try:
        size_mb = parquet_path.stat().st_size / 1_000_000
        _r2_client().upload_file(str(parquet_path), bucket, key)
        logger.info("[r2] Uploaded %s (%.1f MB) to bucket '%s'.", key, size_mb, bucket)
    except Exception as exc:
        logger.warning("[r2] Upload failed for %s: %s", key, exc)
