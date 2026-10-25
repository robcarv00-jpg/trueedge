# Sharp Score — published rubric

The score is the product, so the formula is public and versioned. If the
weights change, the version changes. No silent retunes.

Scale: 1-99 (99, not 100, so a perfect score stays theoretically open).

## v1 (2026-10-25, as first coded)

```
score = clamp(1..99, round(
    50
  + avg_clv_pct * 6
  + (beat_close_rate - 0.5) * 40
  - parlay_share * 30
  - tilt_events * 1.5
  - max(0, brier - 0.24) * 100
))
```

### Known flaws in v1 (found on review, fixed in v1.1)

1. **Tilt is a raw count.** A 1,000-bet bettor is punished ~8x harder than a
   120-bet bettor for the same habit. Must be a rate.
2. **Parlay share is punished even when parlays win.** Volume isn't a leak;
   losing money is. The penalty must key on parlay ROI, not share alone.
3. **CLV and beat-close double-count.** They're correlated measures of the
   same skill. v1.1 keeps both but caps each term so neither dominates.
4. **No late-bet term**, despite late-bet ROI being a headline leak.
5. **Brier is computed against the price taken**, not the bettor's own
   stated probability (most bettors don't record one). It's a calibration
   proxy and is labeled as such in the report.

## v1.1 (2026-10-25, current)

```
score = clamp(1..99, round(
    50
  + clamp(avg_clv_pct * 6, -24, +24)
  + clamp((beat_close_rate - 0.5) * 40, -20, +20)
  - clamp((brier - 0.24) * 100, 0, 20)              # only if brier > 0.24
  - parlay_share * min(1, -parlay_roi / 0.20) * 30   # only if parlay_roi < 0
  - 10 * min(1, -late_roi / 0.20)                    # only if late_roi < 0 and n >= 10
  - tilt_per_100_bets * 0.75
))
```

Demo journal (seed 7, 120 synthetic bets): v1 = 22, v1.1 = 39. The v1 score
was dragged down by the raw tilt count and the unconditional parlay-share
penalty; v1.1's 39 is the more defensible number for this profile. The gap
between versions is itself disclosed to the user — rubric changes are
news, not patches.

## Confidence intervals are part of the rubric (added same day)

Every rate in the report carries a 95% CI (Wilson for rates, bootstrap for
ROI). On the demo journal this immediately mattered: parlay ROI -11.5%
has a CI of -82% to +74% at n=34 — the "biggest leak" is statistically
indistinguishable from noise at that sample. Beat-close 71% (CI 61-80%)
is the only demo signal that clearly survives. Product rule that follows:
**a leak whose CI crosses zero is labeled "not statistically clear yet,"
never presented as fact** — including inside the sealed receipt text.

## Rubric v1.2 — two axes (2026-10-25)

The single-axis score conflates two different things, and the cohort test
exposed it: a planted sharp averaged only 57/99 because discipline
penalties drag the same number that measures skill. v1.2 splits it:

- **Skill** — do you find edge: CLV, beat-close rate, price-calibration
  gap, Brier. (Weights: AXES_WEIGHTS["skill"] in sharp_mirror.py.)
- **Discipline** — do you keep it: tilt rate, parlay leak, parlay share
  excess over 30%, late-bet leak. (AXES_WEIGHTS["discipline"].)

A sharp with one leak now reads "Skill 82, Discipline 41 — fix parlays"
instead of one misleading 57. v1.1 single-axis remains computed and
pinned for continuity; v1.2 axes are reported alongside and get pinned
the same way once they've survived the 5-bettor test.

## Pinning rule (non-negotiable)

Every sealed report embeds, inside the signed receipt meta:
`rubric = {name, version, weights (full), formula_sha, code_sha}` —
sha256 of this file AND of the scoring code file at signing time, plus
the score itself. Anyone can recompute the score from the journal and
the pinned weights (`verify_score()` in sharp_mirror.py) — the receipt
then proves the score is the correct output of its rubric, not just a
number in a signed file. **verify_score fails closed**: missing meta,
missing weights, missing keys, or a non-integer score each return an
explicit failure with the reason named. A verifier that silently
defaults to current weights is worse than no verifier.

Receipts are pinned to the rubric version at signing time and are NEVER
re-scored. A newer rubric may offer a separate "recompute under v1.2" view;
it may not overwrite history. The version number is VISIBLE to the user —
hiding it would be the same betrayal as editing a grade after a bad week.

## Leak tiers

Every leak is presented as point estimate + CI bar + one of three tiers:
- **signal** — CI entirely on one side of zero: the leak (or strength) is real.
- **noise** — CI straddles zero: suggestive, not proven. Shown with an
  estimate of bets needed to resolve ("clear answer in ~N more bets").
- **inconclusive** — n < 30: not shown as a finding at all.

Known UX wart: the resolve estimate explodes for high-variance leaks
(demo parlay ROI: ~1,534 bets). Above ~500 the honest wording is "not
resolvable at realistic volume — tracked in units lost instead." Cap and
rewording are queued; the raw number is not hidden in the meantime.

## Validation so far

Cohort separation test (`cohort_test.py`, synthetic ground truth, 2026-10-25):
20 planted-sharp journals vs 20 planted-square journals, 200 bets each.
Sharp mean 57.3 (range 48-65), square mean 8.7 (range 1-19), separation
+48.6 points, 0/400 pairwise inversions. This proves the rubric measures
the planted behaviors in the right direction. It does NOT validate against
real bettors — planted cohorts are extremes, and even a planted sharp only
averages 57 under the current caps, which says the top of the scale is
stingy. Real-journal validation is still outstanding. Public records
(Agatha/Cappix) cannot substitute: they don't publish closing pairs,
stakes, and timing in the schema the mirror requires.

## Not yet earned (do not claim until done)

- Backtest against known sharp and known losing bettors.
- Any claim that the score predicts future profit. CLV correlates with
  long-run profit; this composite has not been validated yet.
- Cross-asset scoring. A stock has no closing line in the betting sense;
  the asset ladder stays betting-only until execution-quality metrics are
  defined honestly.
