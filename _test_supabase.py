"""
Supabase connectivity and write-layer test.
Run from Project2/ with:  python _test_supabase.py

Tests all four tables and the tracked_picks RPC.
All test rows are cleaned up at the end.
"""
import os, sys, pathlib, json

# ── Load env BEFORE importing supabase_writer (it reads SUPABASE_ENABLED at import) ──
def _load_env(path):
    p = pathlib.Path(path)
    if not p.exists():
        return
    for raw in p.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        os.environ[k.strip()] = v.strip().strip('"').strip("'")

_load_env("Original_Code/secrets.env")
_load_env("Original_Code/settings.env")

sys.path.insert(0, "Original_Code")

import pandas as pd
import numpy as np

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []

def check(label, cond, detail=""):
    status = PASS if cond else FAIL
    msg = f"{status}  {label}" + (f"\n        >> {detail}" if detail else "")
    print(msg)
    results.append((label, cond))
    return cond

# ────────────────────────────────────────────────────────────────
print("=" * 60)
print("STEP 1: Environment + supabase_writer import")
print("=" * 60)

enabled = os.getenv("SUPABASE_ENABLED", "0") == "1"
url     = os.getenv("SUPABASE_URL", "")
key     = os.getenv("SUPABASE_SERVICE_KEY", "")

check("SUPABASE_ENABLED=1", enabled)
check("SUPABASE_URL set",   bool(url),  url[:40] + "..." if url else "(missing)")
check("SUPABASE_SERVICE_KEY set", bool(key), key[:20] + "..." if key else "(missing)")

if not (enabled and url and key):
    print("\nCannot continue — fix env vars first.")
    sys.exit(1)

try:
    import supabase_writer as sb
    check("supabase_writer imports", True)
except Exception as e:
    check("supabase_writer imports", False, str(e))
    sys.exit(1)

# ────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("STEP 2: Raw Supabase client connection")
print("=" * 60)

TEST_RUN_ID = None
try:
    client = sb._client()
    check("create_client() succeeds", True)
    # ping by listing model_runs (should return empty list, not error)
    res = client.table("model_runs").select("id").limit(1).execute()
    check("can query model_runs", True, f"{len(res.data)} rows returned")
except Exception as e:
    check("create_client() / query", False, str(e))
    sys.exit(1)

# ────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("STEP 3: model_runs — start / finish / error cycle")
print("=" * 60)

run_id = sb.start_model_run(active_sports="TEST")
check("start_model_run returns a run_id", run_id is not None, str(run_id))

if run_id:
    TEST_RUN_ID = run_id
    # verify row exists in DB
    try:
        res = client.table("model_runs").select("*").eq("id", run_id).execute()
        row = res.data[0] if res.data else {}
        check("model_run row inserted", bool(row))
        check("status = 'running'", row.get("status") == "running", row.get("status"))
        check("active_sports = 'TEST'", row.get("active_sports") == "TEST")
    except Exception as e:
        check("verify model_run row", False, str(e))

# ────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("STEP 4: current_picks — write_current_picks")
print("=" * 60)

now = pd.Timestamp.now("UTC")
TEST_GAME_ID = "TESTGAME_DELETE_ME"

sample_output = pd.DataFrame([{
    "sport":               "baseball_mlb",
    "game_id":             TEST_GAME_ID,
    "commence_time":       now + pd.Timedelta(hours=3),
    "team":                "Test Team A",
    "market":              "h2h",
    "point":               np.nan,
    "book":                "fanduel",
    "odds_from_best_book": 1.91,
    "sharp_odds":          1.85,
    "ev":                  0.07,
    "kelly":               0.025,
    "clv_prob_med":        0.72,
    "stars":               4,
    "outcome_threshold":   0.04,
}, {
    "sport":               "baseball_mlb",
    "game_id":             TEST_GAME_ID,
    "commence_time":       now + pd.Timedelta(hours=3),
    "team":                "Test Team A",
    "market":              "h2h",
    "point":               np.nan,
    "book":                "draftkings",
    "odds_from_best_book": 1.95,
    "sharp_odds":          1.85,
    "ev":                  0.09,
    "kelly":               0.028,
    "clv_prob_med":        0.72,
    "stars":               4,
    "outcome_threshold":   0.04,
}])

try:
    sb.write_current_picks(sample_output, run_id)
    res = client.table("current_picks").select("*").eq("game_id", TEST_GAME_ID).execute()
    check("current_picks rows inserted", len(res.data) == 2, f"got {len(res.data)} rows")
    books = sorted([r["book"] for r in res.data])
    check("both books written", books == ["draftkings", "fanduel"], str(books))
    check("run_id FK set", all(r.get("run_id") == run_id for r in res.data))
except Exception as e:
    check("write_current_picks", False, str(e))
    import traceback; traceback.print_exc()

# ────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("STEP 5: model_runs — finish_model_run")
print("=" * 60)

fake_result = {
    "latest_board": list(range(40)),
    "n_new": 2,
    "n_to_send": 1,
}
try:
    sb.finish_model_run(run_id, fake_result, sample_output)
    res = client.table("model_runs").select("*").eq("id", run_id).execute()
    row = res.data[0] if res.data else {}
    check("status updated to 'success'",   row.get("status") == "success", row.get("status"))
    check("finished_at is set",            bool(row.get("finished_at")))
    check("latest_output_count = 2",       row.get("latest_output_count") == 2,  str(row.get("latest_output_count")))
    check("latest_board_count = 40",       row.get("latest_board_count")  == 40, str(row.get("latest_board_count")))
    check("new_rows_count = 2",            row.get("new_rows_count") == 2,       str(row.get("new_rows_count")))
except Exception as e:
    check("finish_model_run", False, str(e))
    import traceback; traceback.print_exc()

# ────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("STEP 6: tracked_picks — upsert_tracked_picks (RPC)")
print("=" * 60)

bets_df = pd.DataFrame([{
    "found_at":            now - pd.Timedelta(minutes=10),
    "sport":               "baseball_mlb",
    "game_id":             TEST_GAME_ID,
    "commence_time":       now + pd.Timedelta(hours=3),
    "team":                "Test Team A",
    "market":              "h2h",
    "point":               np.nan,
    "book":                "fanduel",
    "odds_from_best_book": 1.91,
    "sharp_odds":          1.85,
    "ev":                  0.07,
    "kelly":               0.025,
    "clv_prob_med":        0.72,
    "stars":               4,
    "outcome_threshold":   0.04,
    "closing_line":        np.nan,
    "clv":                 np.nan,
    "posted":              0,
    "tier":                np.nan,
}])

try:
    sb.upsert_tracked_picks(bets_df)
    res = client.table("tracked_picks").select("*").eq("game_id", TEST_GAME_ID).execute()
    check("tracked_picks row inserted",  len(res.data) == 1, f"got {len(res.data)} rows")
    if res.data:
        row = res.data[0]
        check("posted = false",  row.get("posted") == False)
        check("point = null",    row.get("point") is None)
        check("book = fanduel",  row.get("book") == "fanduel")

    # Test upsert idempotency: run again, count should still be 1
    sb.upsert_tracked_picks(bets_df)
    res2 = client.table("tracked_picks").select("*").eq("game_id", TEST_GAME_ID).execute()
    check("upsert idempotent (no duplicate row)", len(res2.data) == 1, f"got {len(res2.data)} rows")

    # Test update: simulate closing_line being filled in
    bets_updated = bets_df.copy()
    bets_updated["closing_line"] = 1.83
    bets_updated["posted"] = 1
    sb.upsert_tracked_picks(bets_updated)
    res3 = client.table("tracked_picks").select("*").eq("game_id", TEST_GAME_ID).execute()
    if res3.data:
        row3 = res3.data[0]
        check("closing_line updated on conflict",  abs((row3.get("closing_line") or 0) - 1.83) < 0.01,
              str(row3.get("closing_line")))
        check("posted updated to true on conflict", row3.get("posted") == True,
              str(row3.get("posted")))
except Exception as e:
    check("upsert_tracked_picks", False, str(e))
    import traceback; traceback.print_exc()

# ────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("STEP 7: settled_picks — upsert_settled_picks")
print("=" * 60)

ledger_row = pd.DataFrame([{
    "found_at":            now - pd.Timedelta(days=2),
    "sport":               "baseball_mlb",
    "game_id":             TEST_GAME_ID,
    "commence_time":       now - pd.Timedelta(days=1),
    "team":                "Test Team A",
    "market":              "h2h",
    "point":               np.nan,
    "book":                "fanduel",
    "odds_from_best_book": 1.91,
    "sharp_odds":          1.85,
    "ev":                  0.07,
    "kelly":               0.025,
    "clv_prob_med":        0.72,
    "stars":               4,
    "outcome_threshold":   0.04,
    "closing_line":        1.83,
    "clv":                 0.045,
    "posted":              1,
    "tier":                "basic",
    "W/L":                 "W",
}])

try:
    sb.upsert_settled_picks(ledger_row)
    res = client.table("settled_picks").select("*").eq("game_id", TEST_GAME_ID).execute()
    check("settled_picks row inserted",  len(res.data) == 1, f"got {len(res.data)} rows")
    if res.data:
        row = res.data[0]
        check("result = 'W'",      row.get("result") == "W", str(row.get("result")))
        check("clv filled",        abs((row.get("clv") or 0) - 0.045) < 0.001)
        check("posted = true",     row.get("posted") == True)
        check("W/L col absent (renamed to result)", "W/L" not in row)

    # Upsert idempotency
    sb.upsert_settled_picks(ledger_row)
    res2 = client.table("settled_picks").select("*").eq("game_id", TEST_GAME_ID).execute()
    check("upsert idempotent", len(res2.data) == 1, f"got {len(res2.data)} rows")
except Exception as e:
    check("upsert_settled_picks", False, str(e))
    import traceback; traceback.print_exc()

# ────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("STEP 8: fail_model_run (second run_id)")
print("=" * 60)

run_id_fail = sb.start_model_run(active_sports="FAIL_TEST")
if run_id_fail:
    sb.fail_model_run(run_id_fail, RuntimeError("simulated crash"))
    try:
        res = client.table("model_runs").select("*").eq("id", run_id_fail).execute()
        row = res.data[0] if res.data else {}
        check("status = 'error'",       row.get("status") == "error", row.get("status"))
        check("error_message set",      "simulated crash" in (row.get("error_message") or ""),
              row.get("error_message"))
        check("finished_at is set",     bool(row.get("finished_at")))
    except Exception as e:
        check("fail_model_run verify", False, str(e))
else:
    check("fail_model_run (run_id created)", False, "start_model_run returned None")

# ────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("STEP 9: Cleanup — delete all test rows")
print("=" * 60)

try:
    client.table("current_picks").delete().eq("game_id", TEST_GAME_ID).execute()
    client.table("tracked_picks").delete().eq("game_id", TEST_GAME_ID).execute()
    client.table("settled_picks").delete().eq("game_id", TEST_GAME_ID).execute()
    if TEST_RUN_ID:
        client.table("model_runs").delete().eq("id", TEST_RUN_ID).execute()
    if run_id_fail:
        client.table("model_runs").delete().eq("id", run_id_fail).execute()
    check("test rows cleaned up", True)
except Exception as e:
    check("cleanup", False, str(e))

# ────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("SUMMARY")
print("=" * 60)
passed = sum(1 for _, ok in results if ok)
failed = sum(1 for _, ok in results if not ok)
print(f"  Passed: {passed}")
print(f"  Failed: {failed}")
if failed:
    print("\n  FAILURES:")
    for label, ok in results:
        if not ok:
            print(f"    FAIL: {label}")
    sys.exit(1)
else:
    print("\n  All checks passed. Supabase write layer is fully operational.")
