"""Attribution — find WHICH bets carry the leak, not just that it exists.

The Mirror diagnoses ("parlays are a leak"). Attribution localizes it
("the leak is parlays placed at night; your daytime parlays are fine") —
the difference between a stat and a hypothesis the bettor can test next
week. No competitor in the lane does this; it needs the importer's
sport / placed-at covariates to have anything to split on.

Honesty rules, enforced in code:
- Volume gate: below MIN_JOURNAL bets the function refuses to name
  segments. Segments on small data are noise even when a p-value
  looks fine.
- Splits are tested on EXCESS WINS (won minus the price-implied
  probability of each bet) instead of raw ROI: every bet is normalized
  by its own price first, which is far better powered — a +900 parlay
  no longer drowns the statistic in payout variance. ROI is still
  what's reported for a found segment.
- Candidates are screened with a z-test on excess wins, Bonferroni-
  corrected across everything tested at that node; a reported split
  is then confirmed with a permutation test.
- Two-covariate CROSSES are tested at the root. A first version used
  greedy main-effect descent and missed a planted night-parlay leak
  twice: the segment was 12% of the journal, so it moved its parent
  buckets by only 12% of its effect — dilution killed every main
  effect. Pure interactions are the common shape of real leaks
  (fine by day, bleeding at night), so crosses are not optional.
- Depth capped at 2 below the root split. Power reality, stated
  plainly: at a few hundred bets only egregious leaks are findable;
  moderate segment effects need ~1,000+ bets. The gate below is a
  floor, not a promise.
"""
from __future__ import annotations
import math, random, statistics, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sharp_mirror import _profit, implied  # noqa: E402

MIN_JOURNAL = 200
MIN_SEGMENT = 15


def _dec(american: int) -> float:
    return 1 + (american / 100 if american > 0 else 100 / -american)


def _hour_bucket(r: dict) -> str | None:
    if "hour" not in r:
        return None
    return "night" if r["hour"] >= 21 else "day" if r["hour"] >= 12 else "morning"


def _dow_bucket(r: dict) -> str | None:
    if "dow" not in r:
        return None
    return "weekend" if r["dow"] >= 5 else "weekday"


def _odds_bucket(r: dict) -> str:
    d = _dec(r["odds"])
    return ("heavy_fav" if d < 1.5 else "fav" if d < 1.8 else "pick"
            if d < 2.2 else "dog" if d < 3.0 else "longshot")


def covariates(rows: list[dict]) -> dict:
    """Covariates available for THIS journal. A covariate is offered only
    when at least 70% of rows carry it — splitting on a mostly-missing
    field manufactures segments out of missingness."""
    med_stake = statistics.median(r["stake"] for r in rows)
    covs = {
        "market": lambda r: r["market"],
        "odds_bucket": _odds_bucket,
        "stake_bucket": lambda r: "big" if r["stake"] > 1.5 * med_stake else "small",
    }
    for name, fn in [("sport", lambda r: r.get("sport")),
                     ("hour", _hour_bucket), ("dow", _dow_bucket)]:
        if sum(1 for r in rows if fn(r) is not None) >= 0.7 * len(rows):
            covs[name] = fn
    return covs


def _roi_pairs(pairs: list[tuple[float, float]]) -> float:
    staked = sum(s for _, s in pairs)
    return sum(p for p, _ in pairs) / staked if staked else 0.0


def permutation_p(a: list[float], b: list[float],
                  iters: int = 1000, seed: int = 5) -> tuple[float, float]:
    """Observed difference in mean excess wins, with permutation p-value
    (labels shuffled, group sizes preserved)."""
    obs = statistics.mean(a) - statistics.mean(b)
    combined = a + b
    rng = random.Random(seed)
    extreme = 0
    for _ in range(iters):
        rng.shuffle(combined)
        d = statistics.mean(combined[:len(a)]) - statistics.mean(combined[len(a):])
        if abs(d) >= abs(obs):
            extreme += 1
    return obs, (extreme + 1) / (iters + 1)


def attribute(rows: list[dict], min_segment: int = MIN_SEGMENT,
              alpha: float = 0.05, max_depth: int = 2) -> dict:
    if len(rows) < MIN_JOURNAL:
        return {"status": "insufficient_volume", "bets": len(rows),
                "needed": MIN_JOURNAL,
                "note": "Attribution needs ~200+ bets with >=15 per segment. "
                        "Below that, segments are noise even when a p-value "
                        "looks fine — so none are named."}
    covs = covariates(rows)
    pairs = {id(r): (_profit(r), r["stake"]) for r in rows}
    excess = {id(r): (1.0 if r["won"] else 0.0) - implied(r["odds"]) for r in rows}
    findings: list[dict] = []
    tested = [0]

    def z_screen(a: list[dict], rest: list[dict]) -> tuple[float, float]:
        xa = [excess[id(r)] for r in a]
        xr = [excess[id(r)] for r in rest]
        diff = statistics.mean(xa) - statistics.mean(xr)
        va = statistics.pvariance(xa) if len(xa) > 1 else 0.0
        vr = statistics.pvariance(xr) if len(xr) > 1 else 0.0
        se = math.sqrt(va / len(xa) + vr / len(xr))
        if se == 0:
            return diff, 1.0
        return diff, math.erfc(abs(diff / se) / math.sqrt(2))

    def candidates_for(subset: list[dict], crosses: bool) -> list[tuple[str, list[dict], list[dict]]]:
        out: list[tuple[str, list[dict], list[dict]]] = []
        specs: list[tuple[str, object]] = []
        for name, fn in covs.items():
            for value in sorted({str(fn(r)) for r in subset if fn(r) is not None}):
                specs.append((f"{name}={value}",
                              lambda r, fn=fn, v=value: fn(r) is not None and str(fn(r)) == v))
        if crosses:
            names = list(covs)
            for i in range(len(names)):
                for j in range(i + 1, len(names)):
                    f1, f2 = covs[names[i]], covs[names[j]]
                    for v1 in sorted({str(f1(r)) for r in subset if f1(r) is not None}):
                        for v2 in sorted({str(f2(r)) for r in subset if f2(r) is not None}):
                            specs.append((f"{names[i]}={v1} AND {names[j]}={v2}",
                                          lambda r, f1=f1, f2=f2, v1=v1, v2=v2:
                                          f1(r) is not None and f2(r) is not None
                                          and str(f1(r)) == v1 and str(f2(r)) == v2))
        for label, pred in specs:
            a = [r for r in subset if pred(r)]
            rest = [r for r in subset if not pred(r)]
            if len(a) >= min_segment and len(rest) >= min_segment:
                out.append((label, a, rest))
        return out

    def recurse(subset: list[dict], prefix: str, depth: int) -> None:
        if depth >= max_depth or len(subset) < 2 * min_segment:
            return
        candidates = candidates_for(subset, crosses=(depth == 0))
        if not candidates:
            return
        adj_alpha = alpha / len(candidates)
        best = None
        for label, a, rest in candidates:
            tested[0] += 1
            diff, p = z_screen(a, rest)
            if p < adj_alpha and (best is None or abs(diff) > abs(best[1])):
                best = (label, diff, p, a, rest)
        if best is None:
            return
        label, diff, p, a, rest = best
        _, p_perm = permutation_p([excess[id(r)] for r in a],
                                  [excess[id(r)] for r in rest])
        seg_roi = _roi_pairs([pairs[id(r)] for r in a])
        rest_roi = _roi_pairs([pairs[id(r)] for r in rest])
        direction = ("the leak lives here, not everywhere" if seg_roi < rest_roi
                     else "a strength lives here, not everywhere")
        findings.append({"segment": prefix + label, "n": len(a),
                         "roi": round(seg_roi, 3), "roi_rest": round(rest_roi, 3),
                         "excess_diff": round(diff, 3), "p_screen": round(p, 5),
                         "p_permutation": round(p_perm, 4),
                         "reading": (f"{prefix + label}: ROI {seg_roi:+.0%} vs {rest_roi:+.0%} "
                                     f"on the rest — {direction}")})
        recurse(a, prefix + label + " AND ", depth + 1)
        recurse(rest, f"{prefix}NOT({label}) AND ", depth + 1)

    recurse(rows, "", 0)
    return {"status": "ok", "bets": len(rows), "splits_tested": tested[0],
            "covariates": sorted(covs), "findings": findings}


# ---------- demo: planted segment leak ---------------------------------------

def planted_journal(n: int = 1500, seed: int = 11) -> list[dict]:
    """Planted truth: NIGHT parlays are the leak (win rate crushed).
    Day parlays are exactly fair. Singles are fair at all hours — a pure
    interaction, invisible to main effects. n=1500 because that is the
    honest scale at which a segment this size becomes findable."""
    rng = random.Random(seed)
    rows = []
    for i in range(n):
        night = rng.random() < 0.4
        parlay = rng.random() < 0.3
        market = "parlay" if parlay else rng.choice(["spread", "total", "moneyline"])
        odds = rng.choice([300, 550, 900]) if parlay else rng.choice([-110, -105, 100, 120])
        fair = 1 / _dec(odds)
        if parlay and night:
            p = fair * 0.40          # the planted leak: crushed win rate
        elif parlay:
            p = fair * 1.0           # daytime parlays: exactly fair
        else:
            p = fair                 # singles: exactly fair, all hours
        rows.append(dict(market=market, odds=odds, stake=25.0,
                         mins=rng.choice([30, 300]), close=(-110, -110),
                         won=rng.random() < p,
                         sport=rng.choice(["nfl", "nba"]),
                         hour=rng.choice([22, 23, 0]) if night else rng.choice([13, 15, 18]),
                         dow=rng.randrange(7)))
    return rows


if __name__ == "__main__":
    small = attribute(planted_journal(120))
    print("120-bet journal ->", small["status"], f"(needs {small['needed']})")
    out = attribute(planted_journal())
    print(f"\n1,500-bet journal, planted leak = night parlays (pure interaction)")
    print(f"  covariates tested: {out['covariates']}   splits tested: {out['splits_tested']}")
    for f in out["findings"]:
        print(f"  [{f['segment']}] n={f['n']} ROI {f['roi']:+.1%} vs rest {f['roi_rest']:+.1%} "
              f"(p_screen={f['p_screen']}, p_perm={f['p_permutation']})")
        print(f"    {f['reading']}")
    if not out["findings"]:
        print("  no segment cleared the corrected threshold — the planted leak was missed")
