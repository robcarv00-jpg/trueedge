# trueedge.py — as pasted by Robert 2026-10-25, saved verbatim for review.
"""TrueEdge: personal calibration + edge decay + de-biased estimate engine."""
from __future__ import annotations
import random, statistics
from dataclasses import dataclass
from typing import Iterable


def american_to_decimal(a: float) -> float:
    return 1 + a / 100 if a > 0 else 1 + 100 / abs(a)


def decimal_to_prob(d: float) -> float:
    return 1.0 / d


def devig(decs: list[float]) -> list[float]:
    imps = [decimal_to_prob(d) for d in decs]
    s = sum(imps)
    return [i / s for i in imps]


@dataclass
class Bet:
    bet_id: str
    user_prob: float
    opening_dec: float
    closing_dec: float
    stake: float
    won: bool
    hours_before_game: float


def calibration_table(bets: Iterable[Bet], bucket: float = 0.05) -> list[dict]:
    buckets: dict[int, list[Bet]] = {}
    for b in bets:
        k = int(b.user_prob / bucket)
        buckets.setdefault(k, []).append(b)
    out = []
    for k, rows in sorted(buckets.items()):
        lo, hi = k * bucket, (k + 1) * bucket
        n = len(rows)
        claimed = statistics.mean(r.user_prob for r in rows)
        actual = statistics.mean(1.0 if r.won else 0.0 for r in rows)
        bias = actual - claimed
        out.append({"range": f"{lo:.0%}-{hi:.0%}", "n": n,
                    "claimed": round(claimed, 3), "actual": round(actual, 3),
                    "bias": round(bias, 3)})
    return out


def bias_for(bets: list[Bet], user_prob: float, bucket: float = 0.05) -> float:
    k = int(user_prob / bucket)
    rows = [b for b in bets if int(b.user_prob / bucket) == k]
    if len(rows) < 8:
        return 0.0
    return statistics.mean((1.0 if r.won else 0.0) - r.user_prob for r in rows)


def edge_decay(bets: list[Bet]) -> dict:
    edges_open, edges_close, clvs = [], [], []
    for b in bets:
        fair_open = decimal_to_prob(b.opening_dec)
        fair_close = decimal_to_prob(b.closing_dec)
        edges_open.append(b.user_prob - fair_open)
        edges_close.append(b.user_prob - fair_close)
        clvs.append(fair_close - fair_open)
    return {
        "edge_at_bet": round(statistics.mean(edges_open), 4),
        "edge_at_close": round(statistics.mean(edges_close), 4),
        "decay": round(statistics.mean(edges_open) - statistics.mean(edges_close), 4),
        "avg_clv": round(statistics.mean(clvs), 4),
        "clv_positive_rate": round(sum(1 for c in clvs if c > 0) / len(clvs), 3),
    }


def timing(bets: list[Bet]) -> dict:
    early = [b for b in bets if b.hours_before_game >= 4]
    late = [b for b in bets if b.hours_before_game < 4]
    def clv(group):
        if not group: return None
        return round(statistics.mean(
            decimal_to_prob(b.closing_dec) - decimal_to_prob(b.opening_dec)
            for b in group), 4)
    return {"early_bets": len(early), "early_clv": clv(early),
            "late_bets": len(late), "late_clv": clv(late)}


def tilt(bets: list[Bet]) -> dict:
    ordered = sorted(bets, key=lambda b: b.bet_id)
    after_win, after_loss = [], []
    for prev, cur in zip(ordered, ordered[1:]):
        (after_win if prev.won else after_loss).append(cur.stake)
    if not after_win or not after_loss:
        return {"tilt_ratio": 1.0, "verdict": "insufficient data"}
    ratio = statistics.mean(after_loss) / statistics.mean(after_win)
    return {"after_win_avg": round(statistics.mean(after_win), 2),
            "after_loss_avg": round(statistics.mean(after_loss), 2),
            "tilt_ratio": round(ratio, 2),
            "verdict": ("TILT DETECTED" if ratio > 1.3
                        else "MILD" if ratio > 1.15 else "clean")}


def ruin_probability(bets: list[Bet], n_sims: int = 5000, horizon: int = 500,
                     bankroll: float = 1000.0) -> dict:
    base_stake = statistics.mean(b.stake for b in bets)
    win_rate = sum(1 for b in bets if b.won) / len(bets)
    avg_dec = statistics.mean(b.opening_dec for b in bets)
    ruined = 0
    endings = []
    for _ in range(n_sims):
        bank = bankroll
        for _ in range(horizon):
            if bank < base_stake:
                ruined += 1
                break
            if random.random() < win_rate:
                bank += base_stake * (avg_dec - 1)
            else:
                bank -= base_stake
        endings.append(bank)
    return {"win_rate_observed": round(win_rate, 3),
            "avg_stake": round(base_stake, 2),
            "ruin_pct": round(ruined / n_sims, 3),
            "median_ending_bankroll": round(statistics.median(endings), 2)}


def debiased_edge(bets: list[Bet], user_prob: float,
                  market_dec: float) -> dict:
    bias = bias_for(bets, user_prob)
    corrected = max(0.01, min(0.99, user_prob + bias))
    fair = decimal_to_prob(market_dec)
    raw_edge = user_prob - fair
    true_edge = corrected - fair
    def stake(edge_p, p):
        if edge_p <= 0: return 0.0
        b = market_dec - 1
        kelly = (p * b - (1 - p)) / b
        return round(max(0.0, min(kelly, 0.02)) * 1000, 2)
    return {"user_prob": user_prob, "historical_bias": round(bias, 3),
            "corrected_prob": round(corrected, 3), "market_fair": round(fair, 3),
            "raw_edge": round(raw_edge, 4), "true_edge": round(true_edge, 4),
            "suggested_stake_on_1000": stake(true_edge, corrected),
            "verdict": "BET" if true_edge > 0.02 else "NO BET"}


def make_synthetic(n: int = 300, seed: int = 7) -> list[Bet]:
    rng = random.Random(seed)
    bets, last_loss, stake = [], False, 10.0
    for i in range(n):
        true_p = rng.uniform(0.45, 0.65)
        user_p = min(0.99, true_p + rng.uniform(0.03, 0.10))
        fair_dec = 1 / true_p
        open_dec = fair_dec * rng.uniform(0.94, 0.99)
        close_dec = fair_dec * rng.uniform(0.98, 1.02)
        if last_loss: stake = min(stake * 1.15, 40)
        else:         stake = max(stake * 0.95, 5)
        won = rng.random() < true_p
        bets.append(Bet(f"b{i:04d}", user_p, open_dec, close_dec, stake,
                        won, rng.choice([0.5, 1, 2, 4, 6, 12])))
        last_loss = not won
    return bets


def report(bets: list[Bet]) -> None:
    print(f"\n=== TrueEdge report: {len(bets)} bets ===\n")

    print("1. CALIBRATION — where you lie to yourself")
    print(f"   {'bucket':10} {'n':>4} {'claimed':>8} {'actual':>7} {'bias':>7}")
    for row in calibration_table(bets):
        flag = "  <-- OVERCONFIDENT" if row["bias"] < -0.04 else ""
        print(f"   {row['range']:10} {row['n']:>4} {row['claimed']:>8.1%} "
              f"{row['actual']:>7.1%} {row['bias']:>+7.1%}{flag}")

    print("\n2. EDGE DECAY — are you finding edge or stale lines?")
    d = edge_decay(bets)
    print(f"   edge at bet time:   {d['edge_at_bet']:+.1%}")
    print(f"   edge at close:      {d['edge_at_close']:+.1%}")
    print(f"   decay:              {d['decay']:+.1%}  "
          f"{'<-- stale lines, not skill' if d['decay'] > 0.01 else ''}")
    print(f"   avg CLV:            {d['avg_clv']:+.1%}  "
          f"({'positive — you beat the close' if d['avg_clv'] > 0 else 'negative — you bet too early'})")
    print(f"   positive-CLV rate:  {d['clv_positive_rate']:.0%}")

    print("\n3. TIMING — when do you actually have edge?")
    t = timing(bets)
    print(f"   4+ hrs before game: {t['early_bets']} bets, CLV {t['early_clv']:+.1%}")
    print(f"   <4 hrs before game: {t['late_bets']} bets, CLV {t['late_clv']:+.1%}")
    if t['late_clv'] and t['early_clv'] and t['late_clv'] > t['early_clv'] + 0.005:
        print("   <-- you are better later. Stop betting early.")

    print("\n4. TILT — do you chase losses?")
    ti = tilt(bets)
    print(f"   after win: avg ${ti['after_win_avg']} | after loss: avg ${ti['after_loss_avg']}")
    print(f"   ratio: {ti['tilt_ratio']}x  -- {ti['verdict']}")

    print("\n5. BANKROLL SURVIVAL — Monte Carlo on YOUR behavior")
    r = ruin_probability(bets)
    print(f"   observed win rate:  {r['win_rate_observed']:.1%}")
    print(f"   avg stake:          ${r['avg_stake']}")
    print(f"   P(ruin in 500 bets):{r['ruin_pct']:.1%}  "
          f"{'<-- fix sizing before you bet again' if r['ruin_pct'] > 0.10 else ''}")
    print(f"   median final bank:  ${r['median_ending_bankroll']}")

    print("\n6. THE FEATURE — de-biased estimate on a new bet")
    print("   User says: 'I think this is 60%. Market is -110.'")
    out = debiased_edge(bets, user_prob=0.60, market_dec=american_to_decimal(-110))
    print(f"   your estimate:      {out['user_prob']:.0%}")
    print(f"   your bias:          {out['historical_bias']:+.1%}")
    print(f"   corrected estimate: {out['corrected_prob']:.0%}")
    print(f"   market fair:        {out['market_fair']:.0%}")
    print(f"   raw edge (you):     {out['raw_edge']:+.1%}  <-- what other apps show")
    print(f"   TRUE edge:          {out['true_edge']:+.1%}  <-- what TrueEdge shows")
    print(f"   suggested stake:    ${out['suggested_stake_on_1000']} on $1000 bankroll")
    print(f"   verdict:            {out['verdict']}")


if __name__ == "__main__":
    report(make_synthetic())
