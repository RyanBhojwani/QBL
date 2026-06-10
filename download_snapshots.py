"""
download_snapshots.py — pull daily snapshots from Cloudflare R2 to local machine.

Run manually or via Windows Task Scheduler at 6:00 AM daily.

What it does:
  1. Reads R2 credentials from Original_Code/secrets.env (no manual env var setup needed)
  2. Lists all .parquet files in the R2 bucket
  3. Downloads any not already present locally to ./snapshots/
  4. Deletes each file from R2 after a successful download
  5. Appends a one-line entry to ./snapshots/download.log

The R2 bucket stays near-empty — it's just a nightly relay between Railway and
your local machine, not permanent storage.
"""

import logging
import os
import pathlib
from datetime import datetime

# ── Load credentials from secrets.env so no manual Windows env var setup needed
_secrets_path = pathlib.Path(__file__).parent / "Original_Code" / "secrets.env"
if _secrets_path.exists():
    for _line in _secrets_path.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

import boto3
from botocore.config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
LOCAL_DIR = pathlib.Path(__file__).parent / "snapshots"
ACCOUNT_ID = os.environ["R2_ACCOUNT_ID"]
BUCKET     = os.getenv("R2_BUCKET", "qbl-snapshots")


def _client():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def run():
    LOCAL_DIR.mkdir(exist_ok=True)
    log_path = LOCAL_DIR / "download.log"
    client   = _client()

    # List everything in the bucket
    response = client.list_objects_v2(Bucket=BUCKET)
    objects  = response.get("Contents", [])

    if not objects:
        logger.info("Nothing in R2 bucket — no snapshots to download.")
        return

    downloaded = []
    for obj in objects:
        key  = obj["Key"]          # e.g. "20260609.parquet"
        dest = LOCAL_DIR / key

        if dest.exists():
            logger.info("Already have %s locally — skipping.", key)
            continue

        try:
            client.download_file(BUCKET, key, str(dest))
            size_mb = dest.stat().st_size / 1_000_000
            logger.info("Downloaded  %s  (%.1f MB)", key, size_mb)
            downloaded.append(key)
        except Exception as exc:
            logger.error("Failed to download %s: %s", key, exc)

    # Delete from R2 only after confirmed local download
    for key in downloaded:
        try:
            client.delete_object(Bucket=BUCKET, Key=key)
            logger.info("Deleted     %s  from R2.", key)
        except Exception as exc:
            logger.warning("Could not delete %s from R2: %s", key, exc)

    # Append summary to log
    with open(log_path, "a", encoding="utf-8") as f:
        files = ", ".join(downloaded) if downloaded else "none"
        f.write(f"{datetime.now().isoformat()}  downloaded={len(downloaded)}  files={files}\n")

    logger.info("Done. %d file(s) downloaded this run.", len(downloaded))


if __name__ == "__main__":
    run()
