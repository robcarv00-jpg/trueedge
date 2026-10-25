"""Two-state de-bias demo: the feature says BET and NO BET, honestly.

The standard demo bettor (300 estimates, overconfident) only ever produces
NO BET under the conservative-edge rule — correct, but a first impression
of "we can't confirm anything about you." This demo pairs him with a
heavy user (1,500 sealed estimates, well calibrated at high confidence)
whose band is tight enough for an edge to survive it. Both verdicts come
from the same rule; the difference is evidence volume, which is the point.

Run: python3 demo_verdicts.py
"""
from __future__ import annotations
import random, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "trueedge-review"))
from trueedge_fixed import curve_band, debias_curve  # noqa: E402
from trueedge import make_synthetic  # noqa: E402

MARKET_DEC = 1 + 100 / 110          # -110


def heavy_user(n: int = 1500, seed: int = 21) -> list[tuple[float, bool]]:
    """Well calibrated, slight under-confidence at the top end: says 68%,
    hits ~66%. 1,500 sealed estimates — a year-plus of logging."""
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        p = rng.uniform(0.45, 0.80)
        true_p = min(0.97, p - 0.01 + rng.uniform(-0.01, 0.01))
        out.append((round(p, 2), rng.random() < true_p))
    return out


if __name__ == "__main__":
    casual = [(b.user_prob, b.won) for b in make_synthetic()]
    heavy = heavy_user()

    print("=== STATE 1: casual user, 300 estimates, says 60% at -110 ===")
    band1 = curve_band(casual)
    v1 = debias_curve(casual, 0.60, MARKET_DEC, band=band1)
    print(f"  band ±{band1['simul_hw']:.1%}  corrected {v1['corrected_curve']:.1%}  "
          f"headline {v1['headline_edge']:+.1%}  conservative {v1['conservative_edge']:+.1%}"
          f"  -> {v1['verdict']} (${v1['stake_half_kelly_on_conservative']})")
    print(f"  why: {v1['why']}")

    print("\n=== STATE 2: heavy user, 1,500 estimates, says 68% at -110 ===")
    band2 = curve_band(heavy)
    v2 = debias_curve(heavy, 0.68, MARKET_DEC, band=band2)
    print(f"  band ±{band2['simul_hw']:.1%}  corrected {v2['corrected_curve']:.1%}  "
          f"headline {v2['headline_edge']:+.1%}  conservative {v2['conservative_edge']:+.1%}"
          f"  -> {v2['verdict']} (${v2['stake_half_kelly_on_conservative']})")
    print(f"  why: {v2['why']}")
    print("\nSame rule, same bar. The difference is evidence volume —")
    print("which is exactly what the product should teach on day 1.")
