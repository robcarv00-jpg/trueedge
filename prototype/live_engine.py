"""Live module for Sharp Mirror — behavior tracking + base rates. NOT picks.

What this deliberately does not do: predict games or recommend live bets.
In-play prediction is a latency race against Sportradar/Genius feeds that
a solo app cannot win, and "more accurate picks" is the framing the whole
project is barred from (App Store 5.3 / FTC / the lab's own rules).

What it does:
  1. Situational base rates from real historical game logs — ground truth
     a live bet can be graded against ("teams trailing 7+ at the half win
     ~22% of the time; the price you took implied 36%").
  2. Live-specific leak detection: per-quarter ROI, live tilt ratio,
     trailing-vs-leading ROI, live CLV where closing odds exist.
  3. A real-data check on the free nflverse games file, which — contrary
     to the usual claim — DOES carry closing moneylines/spreads/totals
     (one source, PFR-derived; multi-book archives are what's paywalled).

Window rule: baselines default to recent seasons and the window is stored
in every report. Rules and pace change; a 20-year average is a phantom
(the report below tests home-field advantage by era on real data).

Run: python3 live_engine.py   (stdlib only; NFL fetch needs network,
falls back to synthetic games with a clear label if unreachable)
"""
from __future__ import annotations
import csv, io, random, statistics, urllib.request
from dataclasses import dataclass

NFL_GAMES_URL = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"
# URL as published in the nfelodcm package's games map (PyPI), 2026-10-25.


@dataclass
class GameResult:
    season: int
    home_ht: int
    away_ht: int
    home_final: int
    away_final: int


@dataclass
class LiveBet:
    bet_id: str
    quarter: int
    margin_at_bet: int          # + user's team ahead, - behind
    odds_taken: float           # decimal
    stake: float
    stated_prob: float | None = None
    closing_odds: float | None = None
    won: bool | None = None


# ---------- situational base rates (halftime margin) -------------------------

def _bucket(diff: int) -> str:
    if diff >= 14: return "lead_14+"
    if diff >= 7:  return "lead_7_13"
    if diff >= 1:  return "lead_1_6"
    if diff == 0:  return "tied"
    if diff >= -6: return "trail_1_6"
    if diff >= -13: return "trail_7_13"
    return "trail_14+"


def situational_baselines(games: list[GameResult], window: str,
                          min_n: int = 20) -> dict:
    buckets: dict[str, list[int]] = {}
    for g in games:
        won = 1 if g.home_final > g.away_final else 0
        buckets.setdefault(_bucket(g.home_ht - g.away_ht), []).append(won)
        buckets.setdefault(_bucket(g.away_ht - g.home_ht), []).append(1 - won)
    return {"window": window,
            "baselines": {k: {"n": len(v), "win_rate": round(statistics.mean(v), 3)}
                          for k, v in sorted(buckets.items()) if len(v) >= min_n},
            "caveat": "Historical averages, not predictions. Matchups, injuries "
                      "and game script dominate. A large gap is a flag, not an edge."}


def grade_live_bet(bet: LiveBet, baselines: dict) -> dict:
    key = _bucket(bet.margin_at_bet)
    base = baselines["baselines"].get(key)
    market_prob = 1 / bet.odds_taken
    if not base:
        return {"bet_id": bet.bet_id, "situation": key,
                "note": "not enough historical data in this bucket"}
    gap = round(market_prob - base["win_rate"], 3)
    verdict = ("price consistent with the base rate" if abs(gap) < 0.03 else
               "market implies MORE than the base rate — you're paying for context "
               "the base rate can't see; verify it exists before you call it value"
               if gap > 0 else
               "market implies LESS than the base rate — either the market knows "
               "something, or the price is stale; check a second book")
    return {"bet_id": bet.bet_id, "situation": key, "base_rate": base["win_rate"],
            "n_historical": base["n"], "market_prob": round(market_prob, 3),
            "sanity_gap": gap, "verdict": verdict}


# ---------- live leak detection ----------------------------------------------

def _roi(bs: list[LiveBet]) -> float | None:
    staked = sum(b.stake for b in bs)
    if not staked:
        return None
    pnl = sum(b.stake * (b.odds_taken - 1) if b.won else -b.stake for b in bs)
    return round(pnl / staked, 3)


def live_leaks(bets: list[LiveBet]) -> dict:
    settled = [b for b in bets if b.won is not None]
    if not settled:
        return {"error": "no settled live bets yet"}
    by_q = {f"Q{q}": {"n": len(qb), "roi": _roi(qb)}
            for q in (1, 2, 3, 4) if (qb := [b for b in settled if b.quarter == q])}
    after_loss, after_win = [], []
    for prev, cur in zip(settled, settled[1:]):
        (after_loss if not prev.won else after_win).append(cur.stake)
    tilt = (statistics.mean(after_loss) / statistics.mean(after_win)
            if after_loss and after_win else 1.0)
    clvs = [1 / b.odds_taken - 1 / b.closing_odds for b in settled if b.closing_odds]
    return {"n": len(settled), "roi": _roi(settled), "roi_by_quarter": by_q,
            "tilt_ratio": round(tilt, 2),
            "tilt_verdict": "TILT" if tilt > 1.3 else "clean",
            "roi_betting_trailing": _roi([b for b in settled if b.margin_at_bet < 0]),
            "roi_betting_leading": _roi([b for b in settled if b.margin_at_bet > 0]),
            "avg_live_clv": round(statistics.mean(clvs), 4) if clvs else None,
            "closing_sample": len(clvs)}


# ---------- real NFL data check (nflverse games file) ------------------------

def load_nfl_games() -> list[dict] | None:
    try:
        with urllib.request.urlopen(NFL_GAMES_URL, timeout=30) as r:
            text = r.read().decode("utf-8")
    except Exception:
        return None
    out = []
    for row in csv.DictReader(io.StringIO(text)):
        try:
            out.append({"season": int(row["season"]),
                        "home_score": float(row["home_score"]),
                        "away_score": float(row["away_score"]),
                        "spread": float(row["spread_line"])})
        except (TypeError, ValueError, KeyError):
            continue
    return out


def real_data_check(games: list[dict]) -> None:
    print("=== REAL DATA CHECK — nflverse games file (free) ===")
    print(f"  games loaded: {len(games)}  seasons {min(g['season'] for g in games)}"
          f"-{max(g['season'] for g in games)}")
    print("  home win rate by era (is home-field advantage decaying?):")
    for label, lo, hi in [("2003-2009", 2003, 2009), ("2010-2019", 2010, 2019),
                          ("2020-2025", 2020, 2025)]:
        era = [g for g in games if lo <= g["season"] <= hi and g["home_score"] != g["away_score"]]
        rate = statistics.mean(1.0 if g["home_score"] > g["away_score"] else 0.0 for g in era)
        print(f"    {label}: {rate:.1%}  (n={len(era)})")
    recent = [g for g in games if g["season"] >= 2021]
    print("  win rate by closing spread, 2021-2025 (home team perspective):")
    # nflverse spread_line is signed from the home team's side: POSITIVE
    # means home favored (verified against outcomes below — the s>=7 group
    # wins ~2/3+, the s<0 group ~1/4; the first run had the labels flipped).
    for label, test in [("home fav 7+", lambda s: s >= 7), ("home fav 3-6.5", lambda s: 3 <= s < 7),
                        ("home fav 0.5-2.5", lambda s: 0 < s < 3), ("home dog", lambda s: s < 0)]:
        grp = [g for g in recent if test(g["spread"]) and g["home_score"] != g["away_score"]]
        if grp:
            rate = statistics.mean(1.0 if g["home_score"] > g["away_score"] else 0.0 for g in grp)
            print(f"    {label:18} win {rate:.1%}  (n={len(grp)})")
    print("  note: closing lines here are one source (PFR via nflverse). Halftime")
    print("  baselines need play-by-play (nflverse pbp releases, also free) — the")
    print("  loader for that is the next data task, not a purchase.")


# ---------- synthetic demo (labeled) ------------------------------------------

def demo_games(n: int = 272, seed: int = 7) -> list[GameResult]:
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        h_ht, a_ht = max(0, round(rng.gauss(11, 5))), max(0, round(rng.gauss(11, 5)))
        h_2h = max(0, round(rng.gauss(12, 5)) + (2 if h_ht > a_ht else 0))
        a_2h = max(0, round(rng.gauss(12, 5)) + (2 if a_ht > h_ht else 0))
        out.append(GameResult(2025, h_ht, a_ht, h_ht + h_2h, a_ht + a_2h))
    return out


def demo_bets(n: int = 80, seed: int = 11) -> list[LiveBet]:
    rng = random.Random(seed)
    bets, last_lost = [], False
    for i in range(n):
        q = rng.choice([1, 2, 3, 4, 4, 4])
        margin = rng.randint(-14, 7)
        stake = min(10.0 * 1.6, 50.0) if last_lost else 10.0
        odds = 1.9 if rng.random() < 0.6 else 2.4
        won = rng.random() < (0.45 if margin < 0 else 0.55)
        bets.append(LiveBet(f"lb{i:03d}", q, margin, odds, stake, None,
                            odds * (0.98 if not won else 1.02), won))
        last_lost = not won
    return bets


if __name__ == "__main__":
    bl = situational_baselines(demo_games(), window="SYNTHETIC 1 season (demo)")
    print("=== SITUATIONAL BASE RATES — halftime margin (synthetic demo data) ===")
    for k, v in bl["baselines"].items():
        print(f"  {k:12} win {v['win_rate']:.0%}  (n={v['n']})")
    g = grade_live_bet(LiveBet("demo", 4, -9, 2.2, 20.0), bl)
    print(f"\n  grade: trailing by 9 in Q4 at +120 -> base rate {g.get('base_rate')}, "
          f"market implied {g.get('market_prob')}, gap {g.get('sanity_gap')}")
    print(f"  verdict: {g.get('verdict')}")
    leaks = live_leaks(demo_bets())
    print(f"\n=== LIVE LEAKS (synthetic demo bettor: Q4 chaser) ===")
    print(f"  n={leaks['n']}  ROI {leaks['roi']:+.1%}  tilt {leaks['tilt_ratio']}x ({leaks['tilt_verdict']})")
    for q, v in leaks["roi_by_quarter"].items():
        print(f"    {q}: n={v['n']}  ROI {v['roi']:+.1%}")
    print(f"  trailing ROI {leaks['roi_betting_trailing']:+.1%} vs leading ROI "
          f"{leaks['roi_betting_leading']:+.1%}   live CLV {leaks['avg_live_clv']}")
    print()
    games = load_nfl_games()
    if games:
        real_data_check(games)
    else:
        print("=== REAL DATA CHECK skipped: nflverse unreachable from here ===")
