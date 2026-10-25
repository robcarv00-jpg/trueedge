"""Cohort separation test for Sharp Score rubric v1.1.

Question: does the score separate bettors with planted sharp behavior from
bettors with planted square behavior? Ground truth is known here because we
plant it — this validates that the rubric MEASURES the right things. It does
not validate against real bettors; that needs real journals (see REVIEW /
brief). Public records (Agatha/Cappix) can't be used directly: they don't
publish closing pairs, stakes, and timing in the schema the mirror needs.

Run: python3 cohort_test.py
"""
from __future__ import annotations
import random, statistics, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sharp_mirror import implied, mirror, sharp_score_v11, sharp_axes  # noqa: E402


def journal(seed: int, *, clv_shift: int, parlay_rate: float, tilt_rate: float,
            edge_mult: float, n: int = 200) -> list[dict]:
    """clv_shift: points the close moves toward (sharp, +) or away (square, -)
    from the price taken. edge_mult: true-prob multiplier vs implied."""
    rng = random.Random(seed)
    rows, prev_won = [], True
    for _ in range(n):
        parlay = rng.random() < parlay_rate
        market = "parlay" if parlay else rng.choice(["spread", "total", "moneyline"])
        odds = rng.choice([-110, -115, -105, 100, 120]) if not parlay else rng.choice([300, 550])
        mins = rng.choice([10, 30, 240, 1440])
        stake = 50.0 if (not prev_won and rng.random() < tilt_rate) else 25.0
        p_true = min(0.95, max(0.05, implied(odds) * edge_mult))
        if parlay:
            p_true *= 0.85
        won = rng.random() < p_true
        close_my = odds - clv_shift if not parlay else odds
        rows.append(dict(market=market, odds=odds, mins=mins, stake=stake,
                         close=(close_my, -close_my if close_my < 0 else 100),
                         won=won))
        prev_won = won
    return rows


def cohort(label: str, seeds=range(20), **kw) -> list[int]:
    return [sharp_score_v11(mirror(journal(s, **kw))) for s in seeds]


if __name__ == "__main__":
    sharp = cohort("sharp", clv_shift=12, parlay_rate=0.05, tilt_rate=0.05, edge_mult=1.05)
    square = cohort("square", clv_shift=-8, parlay_rate=0.35, tilt_rate=0.40, edge_mult=0.97)
    ms, mq = statistics.mean(sharp), statistics.mean(square)
    overlap = sum(1 for a in sharp for b in square if a <= b)
    pairs = len(sharp) * len(square)
    print(f"sharp cohort   n=20  mean {ms:.1f}  range {min(sharp)}-{max(sharp)}")
    print(f"square cohort  n=20  mean {mq:.1f}  range {min(square)}-{max(square)}")
    print(f"separation      {ms - mq:+.1f} points")
    print(f"pairwise inversions (sharp <= square): {overlap}/{pairs} "
          f"({overlap / pairs:.0%}) — lower is better; 0% = perfect separation")
    print("verdict:", "SEPARATES" if ms - mq > 15 and overlap / pairs < 0.1
          else "WEAK — rubric needs work")
    ax_s = [sharp_axes(mirror(journal(s, clv_shift=12, parlay_rate=0.05,
                                       tilt_rate=0.05, edge_mult=1.05))) for s in range(20)]
    ax_q = [sharp_axes(mirror(journal(s, clv_shift=-8, parlay_rate=0.35,
                                       tilt_rate=0.40, edge_mult=0.97))) for s in range(20)]
    print(f"axes v1.2 — sharp cohort:  Skill {statistics.mean(a['skill'] for a in ax_s):.0f}, "
          f"Discipline {statistics.mean(a['discipline'] for a in ax_s):.0f}")
    print(f"axes v1.2 — square cohort: Skill {statistics.mean(a['skill'] for a in ax_q):.0f}, "
          f"Discipline {statistics.mean(a['discipline'] for a in ax_q):.0f}")
