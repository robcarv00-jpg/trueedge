"""Import a bet-journal CSV (Pikkit-style export) into Sharp Mirror rows.

Flexible headers — column names are matched case-insensitively against the
aliases below, because every tracker exports slightly different names.
Required: market/type, odds, stake, result, closing odds.
Optional: closing odds (other side), minutes before start (default 180),
sport, and placed-at timestamp. Placed-at is what unlocks the time
covariates (hour, day-of-week) that attribution needs; sport unlocks the
sport split. Without them the Mirror still runs — attribution just has
fewer covariates to test, and says so.

If only one closing price is given, the other side is approximated as the
mirror price (-close for favorites, +100 for underdogs). That's an
approximation and the report should say so; with both sides, devig is exact.

Usage: python3 import_journal.py [journal.csv]
With no argument it generates a sample CSV from the demo journal and runs
the mirror on the imported file, proving the path end to end.
"""
from __future__ import annotations
import csv, sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sharp_mirror import demo_journal, mirror, sharp_score_v1, sharp_score_v11  # noqa: E402

ALIASES = {
    "market": ["market", "bet_type", "type", "bet type"],
    "odds": ["odds", "price", "odds taken", "bet odds"],
    "stake": ["stake", "wager", "amount", "risk"],
    "result": ["result", "outcome", "status", "won"],
    "close": ["closing_odds", "close", "closing odds", "closing line odds"],
    "close_other": ["closing_odds_other", "close_other", "opponent closing odds"],
    "mins": ["mins_before", "minutes_before", "minutes before", "mins", "minutes before start"],
    "sport": ["sport", "league"],
    "placed_at": ["placed_at", "placed at", "date placed", "bet date", "date", "timestamp"],
}
WON = {"win", "won", "w", "true", "1", "yes", "cash"}
LOST = {"loss", "lost", "lose", "l", "false", "0", "no"}


def _col(headers: list[str], key: str) -> str | None:
    low = {h.strip().lower(): h for h in headers}
    for alias in ALIASES[key]:
        if alias in low:
            return low[alias]
    return None


def load_journal(path: Path) -> list[dict]:
    with path.open(newline="") as f:
        rdr = csv.DictReader(f)
        cols = {k: _col(rdr.fieldnames or [], k) for k in ALIASES}
    missing = [k for k in ("market", "odds", "stake", "result", "close") if not cols[k]]
    if missing:
        raise SystemExit(f"CSV is missing required columns: {missing}")
    rows = []
    with path.open(newline="") as f:
        for raw in csv.DictReader(f):
            res = str(raw[cols["result"]]).strip().lower()
            if res not in WON | LOST:
                continue                      # pushes/pending: not graded
            close = int(float(raw[cols["close"]]))
            if cols["close_other"]:
                other = int(float(raw[cols["close_other"]]))
            else:
                other = -close if close < 0 else 100   # documented approximation
            row = dict(
                market=str(raw[cols["market"]]).strip().lower(),
                odds=int(float(raw[cols["odds"]])),
                stake=float(raw[cols["stake"]]),
                mins=int(float(raw[cols["mins"]])) if cols["mins"] else 180,
                close=(close, other),
                won=res in WON,
            )
            if cols["sport"] and str(raw[cols["sport"]]).strip():
                row["sport"] = str(raw[cols["sport"]]).strip().lower()
            if cols["placed_at"] and str(raw[cols["placed_at"]]).strip():
                try:
                    ts = datetime.fromisoformat(
                        str(raw[cols["placed_at"]]).strip().replace("Z", "+00:00"))
                    row["hour"], row["dow"] = ts.hour, ts.weekday()
                except ValueError:
                    pass      # unparseable timestamp: row still imports, no time covariates
            rows.append(row)
    return rows


def write_sample_csv(path: Path) -> None:
    # Sport and placed-at are synthesized deterministically from the row
    # index (the demo journal itself carries neither) so the sample also
    # exercises the attribution covariates. Demo Mirror metrics unaffected.
    from datetime import timedelta
    base = datetime(2026, 8, 2, 13, 0)
    sports = ["nfl", "nba", "nfl", "nba", "mlb"]
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Bet Type", "Odds", "Stake", "Result", "Closing Odds",
                    "Closing Odds Other", "Minutes Before", "Sport", "Placed At"])
        for i, r in enumerate(demo_journal()):
            placed = base + timedelta(hours=31 * i)
            w.writerow([r["market"], r["odds"], r["stake"],
                        "Win" if r["won"] else "Loss",
                        r["close"][0], r["close"][1], r["mins"],
                        sports[i % len(sports)], placed.isoformat(timespec="minutes")])


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("sample_journal.csv")
    if len(sys.argv) <= 1:
        write_sample_csv(path)
        print(f"sample CSV written -> {path.name} (from the demo journal)")
    rows = load_journal(path)
    m = mirror(rows)
    print(f"imported {len(rows)} graded bets")
    print(f"  avg CLV {m['avg_clv_pct']:+.2f}%  beat close {m['beat_close_rate']:.0%} "
          f"CI {m['beat_close_ci']}  Brier {m['brier']}")
    print(f"  parlay ROI {m['parlay_roi']:+.1%} CI {m['parlay_roi_ci']}  tilt {m['tilt_events']}")
    print(f"  SHARP SCORE v1 {sharp_score_v1(m)}/99   v1.1 {sharp_score_v11(m)}/99")
