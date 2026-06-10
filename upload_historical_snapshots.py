"""
upload_historical_snapshots.py — one-time backfill of all historical Railway snapshots to R2.

Run once on Railway via:
    python Original_Code/upload_historical_snapshots.py

What it does:
  1. Scans DATA_DIR/snapshots/ for all YYYYMMDD subdirectories that contain part-000000.parquet
  2. Lists what's already in the R2 bucket (skips those)
  3. Uploads each missing day to R2 as YYYYMMDD.parquet
  4. Logs a summary — does NOT delete from Railway (local files stay intact)

Safe to run multiple times — already-uploaded days are skipped via the R2 listing check.
"""

import logging
import os
import pathlib
import re
import sys

# ── Env loading (mirrors bet_scheduler7.py) ───────────────────────────────────
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

# Load whichever env files exist (Railway has neither; env vars come from Railway dashboard)
_load_env("secrets.env")
_load_env("Original_Code/secrets.env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
DATA_DIR  = pathlib.Path(os.getenv("DATA_DIR", "."))
SNAP_DIR  = DATA_DIR / "snapshots"
ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "")
BUCKET     = os.getenv("R2_BUCKET", "qbl-snapshots")

if not ACCOUNT_ID:
    sys.exit("ERROR: R2_ACCOUNT_ID env var not set. Cannot connect to R2.")

# ── R2 client ─────────────────────────────────────────────────────────────────
try:
    import boto3
    from botocore.config import Config
except ImportError:
    sys.exit("ERROR: boto3 not installed. Run: pip install boto3")

def _client():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def _already_in_r2(client) -> set:
    """Return the set of keys already present in the bucket."""
    resp = client.list_objects_v2(Bucket=BUCKET)
    return {obj["Key"] for obj in resp.get("Contents", [])}


def run():
    if not SNAP_DIR.exists():
        sys.exit(f"ERROR: Snapshot directory not found: {SNAP_DIR}")

    # Find all YYYYMMDD subdirs that have a consolidated parquet
    day_pattern = re.compile(r"^\d{8}$")
    candidates = sorted(
        d for d in SNAP_DIR.iterdir()
        if d.is_dir() and day_pattern.match(d.name) and (d / "part-000000.parquet").exists()
    )

    if not candidates:
        logger.info("No consolidated snapshots found in %s — nothing to upload.", SNAP_DIR)
        return

    logger.info("Found %d day(s) with consolidated snapshots.", len(candidates))

    client = _client()
    already = _already_in_r2(client)
    logger.info("%d file(s) already in R2 bucket '%s'.", len(already), BUCKET)

    uploaded = 0
    skipped  = 0
    failed   = 0

    for day_dir in candidates:
        key = f"{day_dir.name}.parquet"
        parquet_path = day_dir / "part-000000.parquet"

        if key in already:
            logger.info("SKIP  %s — already in R2.", key)
            skipped += 1
            continue

        size_mb = parquet_path.stat().st_size / 1_000_000
        try:
            client.upload_file(str(parquet_path), BUCKET, key)
            logger.info("UP    %s  (%.2f MB)", key, size_mb)
            uploaded += 1
        except Exception as exc:
            logger.error("FAIL  %s: %s", key, exc)
            failed += 1

    logger.info(
        "Done. uploaded=%d  skipped=%d  failed=%d  total_candidates=%d",
        uploaded, skipped, failed, len(candidates),
    )
    if failed:
        logger.warning("%d upload(s) failed — re-run to retry.", failed)


if __name__ == "__main__":
    run()
