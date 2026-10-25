# TrueEdge paste — review (2026-10-25, code run, not paraphrased)

Verdict: the core idea is real and merges into Sharp Mirror. The paste's own
"expected output" does not match its code's actual output in three places,
and its onboarding recommendation breaks its killer feature.

## What the run actually produced (300 synthetic bets, seed 7, 0.36s)

- Calibration: WORKS. 55-60% bucket: claimed 57.7%, actual 42.6%, bias -15.0
  pts. 65-70% bucket: -11.0 pts. The engine recovers planted overconfidence.
- De-bias demo: paste claimed corrected 53% / edge +2% / "BET small."
  ACTUAL: corrected 45%, true edge -7.4%, NO BET, stake $0. Two causes:
  (a) float bucket bug — 0.60/0.05 = 11.999... in binary, so a 60% estimate
  falls in the 55-60 bucket (bias -15) instead of 60-65 (bias -1.7);
  (b) bucket noise — with the other bucket the verdict flips to BET. A
  correction this fragile needs a continuous calibration curve (isotonic or
  Platt) or shrinkage toward 0 by bucket n, plus a CI on the bias itself.
- Edge decay: INVERTED vs the pitch. Edge at close (+6.4%) came out HIGHER
  than at bet time (+4.4%), "decay" -2.1%. As coded, the metric mostly
  restates CLV (avg CLV -2.1%, positive rate 4%) with extra steps. CLV is
  the signal; "decay" as a separate headline metric is not yet earned.
- Tilt: detector said "clean" (1.1x) on data with planted tilt — the stake
  cap ($40) saturates both groups and washes the signal out. Detector needs
  stake normalized (units or % of bankroll), not raw dollars.
- Monte Carlo ruin: 37.9% ruin and median ending bankroll $420 despite a
  55% win rate — the sim pairs the overall win rate with the AVERAGE odds,
  breaking the per-bet link between probability and price. Must resample
  actual (odds, outcome) pairs or simulate per-bucket.
- Kelly: code uses FULL Kelly capped at 2%. Robert's lab standard is
  half-Kelly capped at 2%. Fix before anything ships.

## The structural flaw in the paste's plan

The killer feature (de-bias) needs the bettor's OWN stated probability per
bet. Pikkit/CSV exports do not contain it — no tracker collects it. So
"import -> instant aha" cannot power the de-bias engine; import only powers
Mirror metrics (CLV, leaks, calibration-vs-price). De-bias needs sealed,
pre-game estimate logging going forward (~30+ estimates before corrections
are trustworthy, with shrinkage).

Receipts are what make stated probabilities honest: seal the estimate
before the game so it can't be backfilled after the outcome. Adjacent
proof this pattern works: BearScout (prediction markets) locks forecasts
at call time against the market ask for exactly this reason.

## Novelty spot-check (searched 2026-10-25)

Calibration scoring is established in forecasting/prediction-market tools
(BearScout, Hinsley, Metaculus-style Brier culture) and one picks site
publishes its own calibration page. No consumer BET TRACKER found that
(a) collects the bettor's stated probability, (b) builds their personal
calibration curve, and (c) feeds a de-biased estimate into stake sizing.
Claim it that narrowly or not at all.

## Merge decision (recommended)

TrueEdge is not a second product. It is Sharp Mirror's missing input:
- Mirror (import, day 1): grades prices and outcomes — CLV, leaks, tilt.
- TrueEdge layer (logged, going forward): grades your stated probabilities,
  sealed pre-game by receipt; de-bias unlocks after enough sealed estimates.
One app, two layers, receipts underneath both.
