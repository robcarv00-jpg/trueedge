"""Sharp Mirror — the sportsbook's-eye view of YOU, receipted.

Books profile every bettor (CLV capture, bet timing, stake patterns, market
selection) to decide who gets limited. This computes that profile from a bet
journal and seals the report with carver_receipts.

Integrity rules (SHARP_SCORE.md):
- Every rate ships with a 95% CI; leaks are tiered signal / noise /
  inconclusive. A leak that cannot resolve at the bettor's volume is
  demoted, and reported as expected units lost per 100 bets (with CI).
- The sealed receipt PINS the rubric: version, full weights, sha256 of
  SHARP_SCORE.md, sha256 of this code file, and the score — all inside the
  signed meta. verify_score() recomputes from the journal under the pinned
  weights and FAILS CLOSED: missing or malformed pinning is an error,
  never a silent default to current weights.
- Receipts are never re-scored under a newer rubric.

Scores: single-axis v1.1 (continuity) + two axes from rubric v1.2 —
Skill (do you find edge) and Discipline (do you keep it).

Run: python3 sharp_mirror.py   (stdlib only; demo journal generated in-file)
"""
from __future__ import annotations
import copy, hashlib, json, math, random, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "carver"))
from carver_receipts.receipt import Receipt                # noqa: E402
from carver_receipts.extract import build_claims           # noqa: E402
from carver_receipts.evidence import Evidence              # noqa: E402

RUBRIC_VERSION = "1.1"        # single-axis score pinned in receipts
AXES_VERSION = "1.2"          # two-axis scores (reported, not yet pinned)


# ---------- odds math -------------------------------------------------------

def implied(american: int) -> float:
    return 100 / (american + 100) if american > 0 else -american / (-american + 100)

def _shin(prices: list[float]) -> list[float]:
    """Shin's method: fair probabilities from a book's implied probabilities."""
    total = sum(prices)
    if total <= 1.0:
        return [p / total for p in prices]
    lo, hi = 0.0, 0.5
    for _ in range(60):
        z = (lo + hi) / 2
        est = sum(math.sqrt(z * z + 4 * (1 - z) * p * p / total) for p in prices)
        if est > 1.0: lo = z
        else: hi = z
    z = (lo + hi) / 2
    return [(math.sqrt(z * z + 4 * (1 - z) * p * p / total) - z) / (2 * (1 - z))
            for p in prices]

def _profit(r: dict) -> float:
    dec = 1 + (r["odds"] / 100 if r["odds"] > 0 else 100 / -r["odds"])
    return r["stake"] * (dec - 1) if r["won"] else -r["stake"]

def _roi(rs: list[dict]) -> float:
    staked = sum(r["stake"] for r in rs)
    return sum(_profit(r) for r in rs) / staked if staked else 0.0


# ---------- confidence intervals + tiers ------------------------------------

def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(max(0.0, c - h), 3), round(min(1.0, c + h), 3))

def bootstrap_roi_ci(rs: list[dict], iters: int = 2000, seed: int = 3) -> tuple[float, float]:
    if len(rs) < 5:
        return (0.0, 0.0)
    rng = random.Random(seed)
    ests = sorted(_roi([rs[rng.randrange(len(rs))] for _ in rs]) for _ in range(iters))
    return (round(ests[int(0.025 * iters)], 3), round(ests[int(0.975 * iters)], 3))

def units_per_100(rs: list[dict], iters: int = 2000, seed: int = 4) -> tuple[float, tuple[float, float]]:
    """Expected units won/lost per 100 bets (1 unit = each bet's own stake),
    with a bootstrap CI. Stays meaningful when the ROI CI is too wide to
    resolve — the honest fallback metric for unresolvable leaks."""
    if not rs:
        return 0.0, (0.0, 0.0)
    vals = [_profit(r) / r["stake"] for r in rs]
    mean = sum(vals) / len(vals) * 100
    if len(vals) < 5:
        return round(mean, 1), (round(mean, 1), round(mean, 1))
    rng = random.Random(seed)
    ests = sorted(sum(vals[rng.randrange(len(vals))] for _ in vals) / len(vals) * 100
                  for _ in range(iters))
    return round(mean, 1), (round(ests[int(0.025 * iters)], 1),
                            round(ests[int(0.975 * iters)], 1))

def leak_tier(est: float, ci: tuple[float, float], n: int) -> str:
    if n < 30:
        return "inconclusive"
    return "signal" if ci[0] > 0 or ci[1] < 0 else "noise"

def bets_to_resolve(est: float, ci: tuple[float, float], n: int) -> int | None:
    if est == 0 or leak_tier(est, ci, n) != "noise":
        return None
    half = (ci[1] - ci[0]) / 2
    return max(1, math.ceil(n * (half / abs(est)) ** 2) - n)


# ---------- price calibration (import-supported) ----------------------------

def price_calibration(rows: list[dict], width: float = 0.10) -> list[dict]:
    """Did your bets win as often as the price you took said they should?
    Buckets by implied probability of the price taken. Parlays excluded."""
    buckets: dict[int, list[dict]] = {}
    for r in rows:
        if r["market"] == "parlay":
            continue
        buckets.setdefault(int(implied(r["odds"]) / width), []).append(r)
    out = []
    for k, rs in sorted(buckets.items()):
        wins = sum(1 for r in rs if r["won"])
        imp = sum(implied(r["odds"]) for r in rs) / len(rs)
        ci = wilson_ci(wins, len(rs))
        tier = "inconclusive" if len(rs) < 30 else (
            "signal" if imp < ci[0] or imp > ci[1] else "noise")
        out.append({"range": f"{k * width:.0%}-{(k + 1) * width:.0%}", "n": len(rs),
                    "implied": round(imp, 3), "actual": round(wins / len(rs), 3),
                    "actual_ci": ci, "tier": tier})
    return out


# ---------- demo journal ----------------------------------------------------

def demo_journal(n: int = 120, seed: int = 7) -> list[dict]:
    rng = random.Random(seed)
    rows, prev_won = [], True
    for i in range(n):
        parlay = rng.random() < 0.25
        market = "parlay" if parlay else rng.choice(["spread", "total", "moneyline", "prop"])
        odds = rng.choice([-110, -115, -105, 100, 120, 250]) if not parlay else rng.choice([300, 550, 900])
        mins_before = rng.choice([5, 15, 45, 180, 720, 1440])
        stake = 50.0 if (not prev_won and rng.random() < 0.35) else 25.0  # tilt
        p_true = implied(odds) * rng.uniform(0.94, 1.04)
        if market in ("spread", "total") and mins_before > 60:
            p_true *= 1.06
        if mins_before <= 15:
            p_true *= 0.95
        if parlay:
            p_true *= 0.85
        won = rng.random() < min(max(p_true, 0.02), 0.95)
        close_my = odds - rng.choice([0, 5, 10, 15]) if not parlay else odds
        rows.append(dict(market=market, odds=odds, mins=mins_before, stake=stake,
                         close=(close_my, -close_my if close_my < 0 else 100),
                         won=won))
        prev_won = won
    return rows


# ---------- the mirror ------------------------------------------------------

def mirror(rows: list[dict]) -> dict:
    n = len(rows)
    clvs, brier = [], 0.0
    for r in rows:
        if r["market"] != "parlay":
            fair_close = _shin([implied(r["close"][0]), implied(r["close"][1])])[0]
            clvs.append(fair_close - implied(r["odds"]))
        brier += (implied(r["odds"]) - (1.0 if r["won"] else 0.0)) ** 2
    singles = [r for r in rows if r["market"] != "parlay"]
    cal_gap = (sum(1.0 if r["won"] else 0.0 for r in singles) / max(len(singles), 1)
               - sum(implied(r["odds"]) for r in singles) / max(len(singles), 1))
    late = [r for r in rows if r["mins"] <= 15]
    early_main = [r for r in rows if r["mins"] > 60 and r["market"] in ("spread", "total")]
    parlays = [r for r in rows if r["market"] == "parlay"]
    beat = sum(1 for c in clvs if c > 0)
    tilt = sum(1 for a, b in zip(rows, rows[1:])
               if not a["won"] and b["stake"] > a["stake"])
    p_roi, p_ci = _roi(parlays), bootstrap_roi_ci(parlays)
    l_roi, l_ci = _roi(late), bootstrap_roi_ci(late)
    p_units, p_units_ci = units_per_100(parlays)
    l_units, l_units_ci = units_per_100(late)
    return {
        "bets": n,
        "avg_clv_pct": round(100 * sum(clvs) / max(len(clvs), 1), 2),
        "beat_close_rate": round(beat / max(len(clvs), 1), 2),
        "beat_close_ci": wilson_ci(beat, len(clvs)),
        "brier": round(brier / n, 3),
        "price_cal_gap": round(cal_gap, 3),
        "parlay_share": round(len(parlays) / n, 2),
        "parlay_n": len(parlays),
        "parlay_roi": round(p_roi, 3),
        "parlay_roi_ci": p_ci,
        "parlay_tier": leak_tier(p_roi, p_ci, len(parlays)),
        "parlay_resolve_in": bets_to_resolve(p_roi, p_ci, len(parlays)),
        "parlay_units100": p_units, "parlay_units100_ci": p_units_ci,
        "early_main_roi": round(_roi(early_main), 3),
        "early_main_roi_ci": bootstrap_roi_ci(early_main),
        "late_roi": round(l_roi, 3),
        "late_roi_ci": l_ci,
        "late_n": len(late),
        "late_tier": leak_tier(l_roi, l_ci, len(late)),
        "late_resolve_in": bets_to_resolve(l_roi, l_ci, len(late)),
        "late_units100": l_units, "late_units100_ci": l_units_ci,
        "tilt_events": tilt,
        "tilt_per_100": round(100 * tilt / n, 1),
    }


# ---------- scores (see SHARP_SCORE.md) --------------------------------------

def sharp_score_v1(m: dict) -> int:
    """Original rubric. Kept for comparison; flaws documented in SHARP_SCORE.md."""
    s = 50 + m["avg_clv_pct"] * 6 + (m["beat_close_rate"] - 0.5) * 40 \
        - m["parlay_share"] * 30 - m["tilt_events"] * 1.5 - max(0, m["brier"] - 0.24) * 100
    return max(1, min(99, round(s)))

WEIGHTS_V11 = {
    "base": 50,
    "clv_coef": 6, "clv_cap": 24,
    "beat_coef": 40, "beat_cap": 20,
    "brier_threshold": 0.24, "brier_coef": 100, "brier_cap": 20,
    "parlay_coef": 30, "parlay_scale": 0.20,
    "late_coef": 10, "late_scale": 0.20, "late_min_n": 10,
    "tilt_coef": 0.75,
}

def sharp_score_v11(m: dict, w: dict = WEIGHTS_V11) -> int:
    s = w["base"]
    s += max(-w["clv_cap"], min(w["clv_cap"], m["avg_clv_pct"] * w["clv_coef"]))
    s += max(-w["beat_cap"], min(w["beat_cap"], (m["beat_close_rate"] - 0.5) * w["beat_coef"]))
    s -= max(0.0, min(w["brier_cap"], (m["brier"] - w["brier_threshold"]) * w["brier_coef"]))
    if m["parlay_roi"] < 0:
        s -= m["parlay_share"] * min(1.0, -m["parlay_roi"] / w["parlay_scale"]) * w["parlay_coef"]
    if m["late_roi"] < 0 and m["late_n"] >= w["late_min_n"]:
        s -= w["late_coef"] * min(1.0, -m["late_roi"] / w["late_scale"])
    s -= m["tilt_per_100"] * w["tilt_coef"]
    return max(1, min(99, round(s)))

AXES_WEIGHTS = {   # rubric v1.2 — two axes; single-axis v1.1 unchanged
    "skill": {"base": 50, "clv_coef": 7, "clv_cap": 28, "beat_coef": 50,
              "beat_cap": 25, "cal_gap_coef": 200, "cal_gap_cap": 10,
              "brier_threshold": 0.24, "brier_coef": 100, "brier_cap": 15},
    "discipline": {"base": 90, "tilt_coef": 1.2, "tilt_cap": 30,
                   "parlay_coef": 40, "parlay_cap": 30, "parlay_scale": 0.20,
                   "share_excess_over": 0.30, "share_excess_coef": 50, "share_excess_cap": 10,
                   "late_coef": 20, "late_scale": 0.25, "late_min_n": 10},
}

def sharp_axes(m: dict, w: dict = AXES_WEIGHTS) -> dict:
    """Skill = do you find edge (CLV, beat-close, price calibration, Brier).
    Discipline = do you keep it (tilt, parlay leak, late-bet leak)."""
    sk = w["skill"]
    skill = sk["base"]
    skill += max(-sk["clv_cap"], min(sk["clv_cap"], m["avg_clv_pct"] * sk["clv_coef"]))
    skill += max(-sk["beat_cap"], min(sk["beat_cap"], (m["beat_close_rate"] - 0.5) * sk["beat_coef"]))
    skill += max(-sk["cal_gap_cap"], min(sk["cal_gap_cap"], m["price_cal_gap"] * sk["cal_gap_coef"]))
    skill -= max(0.0, min(sk["brier_cap"], (m["brier"] - sk["brier_threshold"]) * sk["brier_coef"]))
    di = w["discipline"]
    disc = di["base"]
    disc -= min(di["tilt_cap"], m["tilt_per_100"] * di["tilt_coef"])
    if m["parlay_roi"] < 0:
        disc -= min(di["parlay_cap"],
                    m["parlay_share"] * min(1.0, -m["parlay_roi"] / di["parlay_scale"]) * di["parlay_coef"])
    disc -= min(di["share_excess_cap"],
                max(0.0, m["parlay_share"] - di["share_excess_over"]) * di["share_excess_coef"])
    if m["late_roi"] < 0 and m["late_n"] >= di["late_min_n"]:
        disc -= di["late_coef"] * min(1.0, -m["late_roi"] / di["late_scale"])
    return {"skill": max(1, min(99, round(skill))),
            "discipline": max(1, min(99, round(disc)))}


# ---------- trend (the retention layer) --------------------------------------
# A Mirror report is a snapshot; the product is the line. Rolling windows
# over the journal IN ORDER (import order is assumed chronological — the
# importer preserves file order, and exports are chronological) show
# whether the bettor is actually getting better. Day 1 this prints the
# baseline and what will be tracked; that framing is the point.

def rolling_trend(rows: list[dict], window: int = 40, step: int = 20) -> list[dict]:
    out = []
    for start in range(0, max(1, len(rows) - window + 1), step):
        seg = rows[start:start + window]
        if len(seg) < window:
            break
        m = mirror(seg)
        ax = sharp_axes(m)
        out.append({"through_bet": start + window, "skill": ax["skill"],
                    "discipline": ax["discipline"],
                    "tilt_per_100": m["tilt_per_100"],
                    "avg_clv_pct": m["avg_clv_pct"]})
    return out


# ---------- sealing with the rubric + code pinned inside ---------------------

def _sha_file(name: str) -> str:
    return hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()

def seal_report(rows: list[dict], key: str = "demo") -> Receipt:
    m = mirror(rows)
    score = sharp_score_v11(m)
    meta = {"rubric": {"name": "sharp_score", "version": RUBRIC_VERSION,
                       "weights": copy.deepcopy(WEIGHTS_V11),  # never share the live dict:
                       # a caller mutating receipt meta must not corrupt the rubric
                       "formula_sha": _sha_file("SHARP_SCORE.md"),
                       "code_sha": _sha_file("sharp_mirror.py")},
            "score": score}
    lines = [
        f"Across {m['bets']} tracked bets the bettor's average closing line value was {m['avg_clv_pct']:+.2f} percent.",
        f"The bettor beat the closing price in {m['beat_close_rate']:.0%} of graded bets (95% CI {m['beat_close_ci'][0]:.0%} to {m['beat_close_ci'][1]:.0%}).",
        f"Parlays were {m['parlay_share']:.0%} of volume and returned {m['parlay_roi']:+.1%} ROI (95% CI {m['parlay_roi_ci'][0]:+.1%} to {m['parlay_roi_ci'][1]:+.1%}, n={m['parlay_n']}, tier {m['parlay_tier']}).",
        f"Stake-escalation after a loss (tilt) appeared {m['tilt_events']} times, {m['tilt_per_100']:.0f} per 100 bets.",
        f"The bettor's Sharp Score under rubric v{RUBRIC_VERSION} is {score} out of 99.",
    ]
    evidence = {f"c{i+1:03d}": [Evidence(source="bet-journal export (demo, seed 7)",
                                         retrieved_at="2026-10-25",
                                         independence="primary")]
                for i in range(len(lines))}
    claims = build_claims(" ".join(lines), evidence)
    return Receipt(issuer="Carver Sharp Mirror", subject="mirror-report",
                   claims=claims, meta=meta).seal(key=key)

def verify_score(rows: list[dict], receipt: Receipt) -> tuple[bool, str]:
    """Recompute under the PINNED weights. FAILS CLOSED: any missing or
    malformed pinning is an error with a named reason — never a default."""
    meta = getattr(receipt, "meta", None)
    if not isinstance(meta, dict) or not meta:
        return False, "receipt meta missing — no pinned rubric to verify against"
    rub = meta.get("rubric")
    if not isinstance(rub, dict):
        return False, "receipt meta.rubric missing or malformed"
    if rub.get("name") != "sharp_score":
        return False, f"unexpected rubric name: {rub.get('name')!r}"
    weights = rub.get("weights")
    if not isinstance(weights, dict):
        return False, "pinned weights missing or malformed"
    missing = [k for k in WEIGHTS_V11 if k not in weights]
    if missing:
        return False, f"pinned weights missing keys: {missing}"
    sealed = meta.get("score")
    if not isinstance(sealed, int):
        return False, "sealed score missing or not an integer"
    recomputed = sharp_score_v11(mirror(rows), weights)
    if recomputed != sealed:
        return False, f"score mismatch: recomputed {recomputed} != sealed {sealed}"
    notes = [f"score {sealed} recomputed OK under pinned rubric v{rub.get('version')}"]
    if rub.get("formula_sha") != _sha_file("SHARP_SCORE.md"):
        notes.append("rubric doc changed since signing (pinned weights govern)")
    if rub.get("code_sha") != _sha_file("sharp_mirror.py"):
        notes.append("score code changed since signing (pinned weights govern; "
                     "recompute used current code and still matched)")
    return True, "; ".join(notes)


if __name__ == "__main__":
    rows = demo_journal()
    m = mirror(rows)
    axes = sharp_axes(m)
    print("=== SHARP MIRROR (demo journal, 120 bets) ===")
    print(f"  avg CLV          {m['avg_clv_pct']:+.2f}%   beat close {m['beat_close_rate']:.0%} "
          f"(95% CI {m['beat_close_ci'][0]:.0%}-{m['beat_close_ci'][1]:.0%})")
    print(f"  Brier            {m['brier']:.3f}   price-cal gap {m['price_cal_gap']:+.1%} "
          f"(actual minus price-implied, singles)")
    headline, demoted = [], []
    for label, roi, ci, n, tier, resolve, units, units_ci in [
            ("parlay leak", m["parlay_roi"], m["parlay_roi_ci"], m["parlay_n"],
             m["parlay_tier"], m["parlay_resolve_in"], m["parlay_units100"], m["parlay_units100_ci"]),
            ("late bets", m["late_roi"], m["late_roi_ci"], m["late_n"],
             m["late_tier"], m["late_resolve_in"], m["late_units100"], m["late_units100_ci"])]:
        (demoted if (resolve or 0) > 500 else headline).append(
            (label, roi, ci, n, tier, resolve, units, units_ci))
    for label, roi, ci, n, tier, resolve, units, units_ci in headline:
        extra = f" — clear answer in ~{resolve} more bets at this rate" if resolve else ""
        print(f"  {label:16} ROI {roi:+.1%} (95% CI {ci[0]:+.1%} to {ci[1]:+.1%}, n={n}) [{tier}]{extra}")
    if demoted:
        print("  observed, unresolvable at your volume:")
        for label, roi, ci, n, tier, resolve, units, units_ci in demoted:
            print(f"    {label}: {units:+.1f} units per 100 bets "
                  f"(95% CI {units_ci[0]:+.1f} to {units_ci[1]:+.1f}) — at n={n} this market "
                  f"may never give a clear answer; that is a reason to cut it, not ignore it")
    print(f"  early main       ROI {m['early_main_roi']:+.1%} "
          f"(95% CI {m['early_main_roi_ci'][0]:+.1%} to {m['early_main_roi_ci'][1]:+.1%})")
    print(f"  tilt             {m['tilt_events']} events ({m['tilt_per_100']:.0f} per 100 bets)")
    print("  price calibration (your results vs the price you took;"
          " CIs are individual 95%, not family-wise):")
    for b in price_calibration(rows):
        print(f"    {b['range']:>9}  n={b['n']:<3} price said {b['implied']:.0%}, "
              f"you hit {b['actual']:.0%} (CI {b['actual_ci'][0]:.0%}-{b['actual_ci'][1]:.0%}) [{b['tier']}]")
    print(f"  SHARP SCORE      v1.1 single-axis {sharp_score_v11(m)}/99   |   "
          f"v{AXES_VERSION} axes: Skill {axes['skill']}/99, Discipline {axes['discipline']}/99")
    trend = rolling_trend(rows)
    if len(trend) >= 2:
        first, last = trend[0], trend[-1]
        print(f"  TREND (40-bet windows)  Skill {first['skill']} -> {last['skill']}, "
              f"Discipline {first['discipline']} -> {last['discipline']}, "
              f"tilt {first['tilt_per_100']:.0f} -> {last['tilt_per_100']:.0f} per 100 bets")
        print("    (week 1 this is a baseline, not a verdict — the line is the product)")

    receipt = seal_report(rows)
    out = Path(__file__).with_name("mirror_receipt.json")
    out.write_text(json.dumps(receipt.to_dict(), indent=2))
    ok, why = verify_score(rows, receipt)
    print(f"\nReport sealed -> {out.name}")
    print(f"Rubric pin check: {'OK  ' if ok else 'FAIL'} {why}")
    print("Receipt verify:   cd ~/workspace/carver && PYTHONPATH=. python3 -m "
          "carver_receipts.cli verify ../carver-app/prototype/mirror_receipt.json --key demo")
