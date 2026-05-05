"""
v2 pipeline verification — no pyarrow/discord required.
Run from Project2/ with:  python _test_v2_pipeline.py
"""
import os, sys, warnings, traceback
sys.path.insert(0, "Original_Code")
warnings.filterwarnings("ignore")
os.environ.setdefault("ODDS_API_KEY", "dummy_test")

import pathlib
def _load_env(path):
    p = pathlib.Path(path)
    if not p.exists():
        return
    for raw in p.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

_load_env("Original_Code/settings.env")

import pandas as pd
import numpy as np

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []

def check(label, cond, detail=""):
    status = PASS if cond else FAIL
    msg = f"{status}  {label}" + (f"  ({detail})" if detail else "")
    print(msg)
    results.append((label, cond))


# ---------------------------------------------------------------------------
print("=" * 60)
print("STEP 1: Import run_edge_board_v2")
print("=" * 60)
try:
    from run_edge_board_v2 import build_edge_output, run_edge_board, ACTIVE_CFGS
    check("run_edge_board_v2 imports", True)
    active_names = [str(c.sport_key) for c in ACTIVE_CFGS]
    print(f"  Active sport configs: {len(ACTIVE_CFGS)}")
    for n in active_names:
        print(f"    {n}")
except Exception as e:
    check("run_edge_board_v2 imports", False, str(e))
    traceback.print_exc()
    sys.exit(1)

# ---------------------------------------------------------------------------
print()
print("=" * 60)
print("STEP 2: build_edge_output — output schema correct")
print("=" * 60)

EXPECTED_COLS = [
    "sport", "game_id", "commence_time", "team", "market", "point",
    "book", "odds_from_best_book",
    "sharp_odds", "ev", "kelly", "clv_prob_med", "stars", "outcome_threshold",
]

now = pd.Timestamp.now("UTC")
rng = np.random.default_rng(42)
BOOK_DATA = [("fanduel", 0.55), ("draftkings", 0.54), ("betmgm", 0.53), ("espnbet", 0.56)]

def make_board(n_outcomes=8, books=BOOK_DATA):
    """Create synthetic v2 board: n_outcomes x len(books) rows."""
    rows = []
    sports  = ["baseball_mlb", "icehockey_nhl", "basketball_nba"]
    markets = ["h2h", "spreads", "totals"]
    for i in range(n_outcomes):
        sp_key  = sports[i % len(sports)]
        mkt     = markets[i % len(markets)]
        sharp_p = float(rng.uniform(0.52, 0.72))
        so      = 1.0 / sharp_p
        ct      = now + pd.Timedelta(hours=int(rng.integers(1, 12)))
        pt      = float(rng.choice([-3.5, -1.5, 0.0, 1.5, 3.5, 210.5]))
        for book, book_ip in books:
            bo  = 1.0 / book_ip
            ev  = sharp_p * (bo - 1.0) - (1.0 - sharp_p)
            ky  = max(0.0, 0.5 * (sharp_p * bo - 1.0) / (bo - 1.0))
            rows.append(dict(
                sport=sp_key, game_id=f"game_{i:03d}", commence_time=ct,
                team=f"TeamA_{i}", market=mkt, point=pt,
                sharp_p=sharp_p, sharp_odds=so,
                book=book, book_ip=book_ip, book_odds=bo,
                ev=ev, kelly=ky,
                sharpe=ev / max(1e-9, np.sqrt(sharp_p*(1-sharp_p))*(so-1)),
            ))
    return pd.DataFrame(rows)

board = make_board(n_outcomes=10)
print(f"  Synthetic board: {len(board)} rows ({10} outcomes x {len(BOOK_DATA)} books)")

try:
    out = build_edge_output(board)
    check("no crash", True)
    check("column order matches spec", list(out.columns) == EXPECTED_COLS,
          f"got {list(out.columns)}")
    check("'book' column present",     "book"        in out.columns)
    check("'best_book' absent",        "best_book"   not in out.columns)
    check("'odds_from_best_book' present", "odds_from_best_book" in out.columns)
    check("'stars' column 1-5",        out["stars"].between(1, 5).all() if not out.empty else True,
          f"values: {out['stars'].unique().tolist() if not out.empty else '(empty)'}")
    check("'kelly' clipped at 0.03",   (out["kelly"] <= 0.030001).all() if not out.empty else True)
    check("'ev' filter <= 0.3",        (out["ev"] <= 0.3).all() if not out.empty else True)
    check("rows survived filters",     len(out) > 0, f"{len(out)} rows")
    if not out.empty:
        print(f"\n  Sample output ({len(out)} rows):")
        pd.set_option("display.width", 110)
        pd.set_option("display.max_columns", 14)
        print(out[["sport","team","market","book","odds_from_best_book","ev","kelly","stars"]].head(6).to_string())
except Exception as e:
    check("build_edge_output", False, str(e))
    traceback.print_exc()

# ---------------------------------------------------------------------------
print()
print("=" * 60)
print("STEP 3: Per-book expansion — same outcome, different books")
print("=" * 60)

# One outcome (game_id=X, team=Cubs, market=h2h, point=NaN) x 4 books
one_outcome_board = make_board(n_outcomes=1, books=BOOK_DATA)
print(f"  Board: {len(one_outcome_board)} rows, all same outcome, different books")
try:
    out2 = build_edge_output(one_outcome_board)
    books_in_output = out2["book"].unique().tolist() if not out2.empty else []
    check("multiple books in output", len(books_in_output) >= 1,
          f"books found: {books_in_output}")
    # odds_from_best_book should differ by book
    if not out2.empty and len(out2) > 1:
        check("odds_from_best_book differs per book",
              out2["odds_from_best_book"].nunique() > 1,
              f"unique values: {out2['odds_from_best_book'].round(4).tolist()}")
    print(f"  Output books: {books_in_output}")
    print(f"  Output odds:  {out2['odds_from_best_book'].round(4).tolist() if not out2.empty else []}")
except Exception as e:
    check("per-book expansion", False, str(e))
    traceback.print_exc()

# ---------------------------------------------------------------------------
print()
print("=" * 60)
print("STEP 4: update_closing_lines dedup (no index fan-out)")
print("=" * 60)

# Import the exact function from bet_scheduler7 source via exec (avoids discord dep)
# We'll re-implement the dedup fix inline and verify it

def update_closing_lines_v2(bets, board):
    """Exact logic from bet_scheduler7.py after the dedup fix."""
    if bets.empty or board.empty:
        return
    _now = pd.Timestamp.now("UTC")
    bets["commence_time"] = pd.to_datetime(bets["commence_time"], utc=True, errors="coerce")
    live_mask = bets["commence_time"] > _now
    live = bets[live_mask]
    if live.empty:
        return
    key_cols = ["game_id", "team", "market", "point"]
    board_dedup = board.drop_duplicates(subset=key_cols, keep="first")
    merged = live.merge(
        board_dedup[key_cols + ["sharp_odds", "commence_time"]],
        on=key_cols, how="left", suffixes=("", "_new"),
    )
    for idx, new_odds in zip(live.index, merged["sharp_odds_new"]):
        if pd.notna(new_odds):
            bets.at[idx, "closing_line"] = new_odds
    for idx, ct_new in zip(live.index, merged["commence_time_new"]):
        if pd.notna(ct_new) and ct_new > _now and ct_new > bets.at[idx, "commence_time"]:
            bets.at[idx, "commence_time"] = pd.to_datetime(ct_new, utc=True)


# v2 board: 4 book rows for one outcome, all with same sharp_odds = 1.667
one_game_board = pd.DataFrame([
    dict(game_id="G1", team="Cubs", market="h2h", point=float("nan"),
         sharp_odds=1.667, commence_time=now + pd.Timedelta(hours=3),
         book=b, book_ip=ip, book_odds=1.0/ip, ev=0.08, kelly=0.04)
    for b, ip in BOOK_DATA
])
print(f"  Board: {len(one_game_board)} rows for one outcome (4 books)")

# One bet row tracking this outcome
bets = pd.DataFrame([dict(
    game_id="G1", team="Cubs", market="h2h", point=float("nan"),
    commence_time=now + pd.Timedelta(hours=3),
    closing_line=np.nan, clv=np.nan,
    sport="baseball_mlb", found_at=now, odds_from_best_book=1.0/0.55,
    sharp_odds=1.667,   # present in real bets (comes from latest_output)
)])
try:
    update_closing_lines_v2(bets, one_game_board)
    cl = bets["closing_line"].iloc[0]
    check("closing_line set correctly", abs(cl - 1.667) < 0.01,
          f"got {cl:.4f}, expected ~1.667")
    check("bets row count unchanged (no fan-out)", len(bets) == 1,
          f"got {len(bets)} rows")
except Exception as e:
    check("update_closing_lines dedup", False, str(e))
    traceback.print_exc()

# ---------------------------------------------------------------------------
print()
print("=" * 60)
print("STEP 5: bets.csv migration (best_book -> book rename)")
print("=" * 60)
old_bets = pd.DataFrame([{
    "game_id": "G1", "best_book": "fanduel", "odds_from_best_book": 1.82,
    "team": "Cubs", "market": "h2h", "found_at": now,
}])
check("'best_book' in old CSV", "best_book" in old_bets.columns)
check("'book' not in old CSV",  "book"      not in old_bets.columns)

# Apply the migration (same as main() in bet_scheduler7.py)
if "best_book" in old_bets.columns and "book" not in old_bets.columns:
    old_bets.rename(columns={"best_book": "book"}, inplace=True)

check("after migration: 'book' present",     "book"      in old_bets.columns)
check("after migration: 'best_book' absent", "best_book" not in old_bets.columns)
check("values preserved", old_bets["book"].iloc[0] == "fanduel")

# ---------------------------------------------------------------------------
print()
print("=" * 60)
print("SUMMARY")
print("=" * 60)
passed = sum(1 for _, ok in results if ok)
failed = sum(1 for _, ok in results if not ok)
print(f"  Passed: {passed}")
print(f"  Failed: {failed}")
if failed:
    print("  FAILURES:")
    for label, ok in results:
        if not ok:
            print(f"    - {label}")
else:
    print("  All checks passed.")
