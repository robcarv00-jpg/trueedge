"""TrueEdge, fixed — the corrections from the 2026-10-25 review, implemented.

Fixes vs the pasted original (trueedge-review/trueedge.py):
1. Bucket float bug (0.60/0.05 = 11.999...) — epsilon-safe bucketing, and
   the correction is no longer raw bucket bias: it's empirical-Bayes
   shrinkage toward zero, shrink = n/(n+k). k is a TUNING KNOB: it's
   disclosed here and must be versioned with the rubric, not hidden.
2. The bias carries its own CI. De-bias "unlocks" when the bias CI
   half-width is <= 3 points — a computable per-user trigger, not a
   magic count of estimates.
3. Ruin simulation resamples the bettor's ACTUAL (odds, stake, outcome)
   profit distribution instead of pairing an average win rate with an
   average price (which broke the joint distribution and lied).
4. Stakes use HALF-Kelly capped at 2% — the Betting Lab standard.

Run: python3 trueedge_fixed.py  (reuses the original's synthetic bettor)
"""
from __future__ import annotations
import math, random, statistics, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "trueedge-review"))
from trueedge import Bet, make_synthetic, ruin_probability  # noqa: E402

SHRINK_K = 15          # disclosed tuning knob — version with the rubric.
                       # Future step (not a promise): when ~100 users exist,
                       # re-estimate k from data (method of moments / MLE)
                       # and version the change like any rubric change.
UNLOCK_HALF_WIDTH = 0.03
MIN_EDGE = 0.03        # the Betting Lab's established 3% bar


def _bucket(p: float, width: float = 0.05) -> int:
    return int((p + 1e-9) / width)


def bucket_bias(estimates: list[tuple[float, bool]], user_prob: float,
                width: float = 0.05) -> dict:
    k = _bucket(user_prob, width)
    rows = [(p, w) for p, w in estimates if _bucket(p, width) == k]
    n = len(rows)
    if n == 0:
        return {"n": 0, "bias_raw": 0.0, "bias_shrunk": 0.0, "half_width": 1.0}
    actual = statistics.mean(1.0 if w else 0.0 for _, w in rows)
    claimed = statistics.mean(p for p, _ in rows)
    raw = actual - claimed
    shrink = n / (n + SHRINK_K)
    se = math.sqrt(max(actual * (1 - actual), 1e-6) / n)
    return {"n": n, "bias_raw": round(raw, 3),
            "bias_shrunk": round(raw * shrink, 3),
            "half_width": round(1.96 * se, 3)}


def debias(estimates: list[tuple[float, bool]], user_prob: float,
           market_dec: float, bankroll: float = 1000.0) -> dict:
    """Legacy bucket path — kept for comparison only. Same verdict rule as
    the curve path (fixed 2026-10-25): the verdict follows the CONSERVATIVE
    edge against the 3% bar, and the stake is sized off the conservative
    probability. An earlier version let the headline edge drive the verdict
    at a 2% threshold — two verdict rules in one file, one of them wrong."""
    b = bucket_bias(estimates, user_prob)
    corrected = max(0.01, min(0.99, user_prob + b["bias_shrunk"]))
    fair = 1.0 / market_dec
    edge = corrected - fair
    conservative_p = corrected - b["half_width"]
    conservative_edge = conservative_p - fair
    dec_b = market_dec - 1
    kelly = (conservative_p * dec_b - (1 - conservative_p)) / dec_b if dec_b > 0 else 0.0
    bet = conservative_edge > MIN_EDGE
    stake = round(max(0.0, min(kelly / 2, 0.02)) * bankroll, 2) if bet else 0.0
    return {"user_prob": user_prob, **b, "corrected": round(corrected, 3),
            "market_fair": round(fair, 3), "headline_edge": round(edge, 4),
            "conservative_edge": round(conservative_edge, 4),
            "stake_half_kelly_on_conservative": stake,
            "unlocked": b["half_width"] <= UNLOCK_HALF_WIDTH,
            "verdict": "BET" if bet else "NO BET"}


# ---------- pooled calibration curve (replaces bucket lookup) ---------------
# Bias is a smooth function of the estimate; it does not jump at bucket
# boundaries. Fit outcome ~ a + b*prob by least squares (Platt-style, linear),
# pool ALL estimates into every correction, and get uncertainty from a
# bootstrap SIMULTANEOUS band — one band for the whole curve, so the
# multiple-comparisons problem of 20 per-bucket CIs doesn't apply.

def fit_curve(estimates: list[tuple[float, bool]]) -> tuple[float, float]:
    n = len(estimates)
    mx = statistics.mean(p for p, _ in estimates)
    my = statistics.mean(1.0 if w else 0.0 for _, w in estimates)
    sxx = sum((p - mx) ** 2 for p, _ in estimates)
    if sxx == 0:
        return my, 0.0
    sxy = sum((p - mx) * ((1.0 if w else 0.0) - my) for p, w in estimates)
    b = sxy / sxx
    return my - b * mx, b

def _curve(a: float, b: float, p: float) -> float:
    return max(0.01, min(0.99, a + b * p))

def curve_band(estimates: list[tuple[float, bool]], iters: int = 500,
               seed: int = 11) -> dict:
    a, b = fit_curve(estimates)
    # Band only over the OBSERVED estimate range (5th-95th percentile).
    # A first version used a fixed 0.10-0.90 grid and produced a +-42%
    # band: pure extrapolation variance where the user has never placed
    # an estimate. Pooling tightens the CI inside the data; outside the
    # data there is nothing to pool. Measured, not assumed.
    ps = sorted(p for p, _ in estimates)
    lo = ps[int(0.05 * len(ps))]
    hi = ps[int(0.95 * len(ps))]
    grid = [lo + (hi - lo) * i / 16 for i in range(17)]
    rng = random.Random(seed)
    n = len(estimates)
    sup, at = [], {g: [] for g in grid}
    for _ in range(iters):
        sample = [estimates[rng.randrange(n)] for _ in range(n)]
        ai, bi = fit_curve(sample)
        sup.append(max(abs(_curve(ai, bi, g) - _curve(a, b, g)) for g in grid))
        for g in grid:
            at[g].append(_curve(ai, bi, g))
    sup.sort()
    return {"a": a, "b": b, "simul_hw": round(sup[int(0.95 * iters)], 3),
            "pointwise": {g: (round(at[g][int(0.025 * iters)], 3),
                              round(at[g][int(0.975 * iters)], 3)) for g in grid}}

def debias_curve(estimates: list[tuple[float, bool]], user_prob: float,
                 market_dec: float, bankroll: float = 1000.0,
                 band: dict | None = None) -> dict:
    """THE verdict rule: the recommendation follows the CONSERVATIVE edge —
    corrected probability minus the simultaneous band's half-width, against
    the market. Headline edge is displayed, never acted on alone."""
    band = band or curve_band(estimates)
    corrected = _curve(band["a"], band["b"], user_prob)
    fair = 1.0 / market_dec
    headline_edge = corrected - fair
    conservative_p = corrected - band["simul_hw"]
    conservative_edge = conservative_p - fair
    dec_b = market_dec - 1
    kelly = (conservative_p * dec_b - (1 - conservative_p)) / dec_b if dec_b > 0 else 0.0
    bet = conservative_edge > MIN_EDGE
    stake = round(max(0.0, min(kelly / 2, 0.02)) * bankroll, 2) if bet else 0.0
    why = ("conservative edge clears the 3% bar" if bet else
           "edge not confirmed: conservative bound is under the 3% bar — "
           "we don't bet on noise")
    return {"user_prob": user_prob, "corrected_curve": round(corrected, 3),
            "simul_hw": band["simul_hw"], "market_fair": round(fair, 3),
            "headline_edge": round(headline_edge, 4),
            "conservative_edge": round(conservative_edge, 4),
            "stake_half_kelly_on_conservative": stake,
            "verdict": "BET" if bet else "NO BET", "why": why}


def unlock_status(estimates: list[tuple[float, bool]]) -> dict:
    """Overall bias CI across ALL sealed estimates, and roughly how many
    more estimates until the half-width reaches the unlock threshold."""
    n = len(estimates)
    if n == 0:
        return {"n": 0, "half_width": 1.0, "unlocked": False, "est_more_needed": None}
    actual = statistics.mean(1.0 if w else 0.0 for _, w in estimates)
    hw = 1.96 * math.sqrt(max(actual * (1 - actual), 1e-6) / n)
    more = None
    if hw > UNLOCK_HALF_WIDTH:
        more = max(1, math.ceil(n * (hw / UNLOCK_HALF_WIDTH) ** 2) - n)
    return {"n": n, "half_width": round(hw, 3),
            "unlocked": hw <= UNLOCK_HALF_WIDTH, "est_more_needed": more}


def ruin_empirical(bets: list[Bet], sims: int = 5000, horizon: int = 500,
                   bankroll: float = 1000.0, seed: int = 5) -> dict:
    """Bootstrap the bankroll path from the bettor's actual per-bet profits.
    Preserves the joint (price, stake, outcome) distribution the original
    sim destroyed by averaging."""
    profits = [b.stake * (b.opening_dec - 1) if b.won else -b.stake for b in bets]
    min_unit = statistics.median(b.stake for b in bets)
    rng = random.Random(seed)
    ruined, endings = 0, []
    for _ in range(sims):
        bank = bankroll
        for _ in range(horizon):
            if bank < min_unit:
                ruined += 1
                break
            bank += profits[rng.randrange(len(profits))]
        endings.append(bank)
    return {"ruin_pct": round(ruined / sims, 3),
            "median_ending_bankroll": round(statistics.median(endings), 2)}


# ---------- behavioral gap: what you SAID vs what you STAKED ----------------
# Only possible because TrueEdge collects the bettor's own stated number.
# Invert half-Kelly on the actual stake to get the probability the stake
# itself implies, then compare. Caveat, stated in the product too: this is
# informative only if the bettor sizes by conviction. A flat-staker's stake
# carries no probability information — the report must offer an "I stake
# flat" toggle that hides this diagnostic rather than faking a reading.

def implied_prob_from_stake(stake: float, bankroll: float, market_dec: float,
                            kelly_mult: float = 0.5) -> float | None:
    b = market_dec - 1
    if b <= 0 or bankroll <= 0:
        return None
    p = ((stake / bankroll) / kelly_mult + 1 / b) / (1 + 1 / b)
    return max(0.0, min(1.0, p))


def behavioral_gap(bets: list[dict]) -> list[dict]:
    """bets: dicts with stated_prob, stake, bankroll, market_dec."""
    out = []
    for i, bt in enumerate(bets):
        implied = implied_prob_from_stake(bt["stake"], bt["bankroll"], bt["market_dec"])
        if implied is None:
            continue
        gap = bt["stated_prob"] - implied
        verdict = ("SAID MORE THAN STAKED — wrote a number, bet like a smaller one"
                   if gap > 0.05 else
                   "STAKED MORE THAN SAID — bet like a bigger number than written (tilt or sizing error)"
                   if gap < -0.05 else "consistent")
        out.append({"bet": i + 1, "stated": round(bt["stated_prob"], 2),
                    "implied_by_stake": round(implied, 2), "gap": round(gap, 2),
                    "verdict": verdict})
    return out


if __name__ == "__main__":
    bets = make_synthetic()
    estimates = [(b.user_prob, b.won) for b in bets]

    print("=== DE-BIAS, BUCKET VERSION (v1, for comparison) ===")
    out = debias(estimates, 0.60, 1 + 100 / 110)
    for k, v in out.items():
        print(f"  {k:24} {v}")
    print("  (original pasted code said: corrected 45%, edge -7.4%, NO BET.)")

    print("\n=== DE-BIAS, CURVE VERSION (v2 — the one that ships) ===")
    band = curve_band(estimates)
    print(f"  calibration curve: corrected(p) = {band['a']:.3f} + {band['b']:.3f}*p"
          f"   simultaneous band half-width ±{band['simul_hw']:.1%}")
    cv = debias_curve(estimates, 0.60, 1 + 100 / 110, band=band)
    for k, v in cv.items():
        print(f"  {k:34} {v}")
    print("  Verdict follows the CONSERVATIVE edge vs the 3% lab bar.")
    print("  Pooling all 300 estimates into the curve is what tightens the")
    print("  band: no bucket boundaries, no 757-estimate lock.")

    st = unlock_status(estimates)
    print(f"\n=== UNLOCK STATUS ===  {st}")
    print("  Unlock rule: bias CI half-width <= 3 pts (not a magic estimate count).")

    print("\n=== RUIN, FIXED (empirical bootstrap) ===")
    fixed = ruin_empirical(bets)
    flawed = ruin_probability(bets)
    print(f"  fixed : ruin {fixed['ruin_pct']:.1%}, median ending ${fixed['median_ending_bankroll']}")
    print(f"  flawed: ruin {flawed['ruin_pct']:.1%}, median ending ${flawed['median_ending_bankroll']}"
          "  (avg win rate x avg odds — joint distribution broken)")

    print("\n=== BEHAVIORAL GAP (stated number vs stake-implied number) ===")
    demo_bets = [
        {"stated_prob": 0.60, "stake": 80.0, "bankroll": 1000.0, "market_dec": 1 + 100 / 110},
        {"stated_prob": 0.60, "stake": 10.0, "bankroll": 1000.0, "market_dec": 1 + 100 / 110},
        {"stated_prob": 0.55, "stake": 90.0, "bankroll": 1000.0, "market_dec": 1 + 100 / 110},
    ]
    for g in behavioral_gap(demo_bets):
        print(f"  bet {g['bet']}: said {g['stated']:.0%}, stake implies {g['implied_by_stake']:.0%} "
              f"-> {g['verdict']}")
