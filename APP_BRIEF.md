# Carver App — Brief (2026-10-25)

Robert is making an app. Working concept: **every dollar you're about to risk
gets scored and receipted** — cross-asset edge scoring + Carver Receipts on
every recommendation. Not "another investing app," not "AI tips."

## The four blockers (no code fixes these)

1. **Never "help people win bets."** App Store Guideline 5.3 + FTC/CFTC
   exposure for guaranteed-outcome claims. Compliant framing, already the
   Betting Lab's: "Track your edge. Journal every bet. See your real ROI."
2. **No personalized investing advice without a license.** Education +
   paper trading + journaling + third-party research only. Never "buy this."
3. **Real-estate listing data is the expensive trap.** MLS $500-5,000/mo per
   market. v1 uses free public data only (Census/ACS, HUD, FRED, RentCast)
   framed as "area context," never property picks.
4. **"All-in-one" and "won't crash" are opposites.** One vertical at launch.
   Every provider behind a circuit breaker + cache; a dead upstream returns
   `stale: true`, never a crash. (Pattern: `providers.py`, to be ported from
   the plan paste and tested before any UI work.)

## Feasibility — verified by running it (feasibility.py, this folder)

| Vertical | Ship score | Cost/mo | Weeks |
|---|---|---|---|
| Bet tracking + edge | 8.2 | $40 | 4 |
| Stocks journal | 7.4 | $30 | 3 |
| Crypto portfolio | 7.3 | $20 | 3 |
| Bonds / yield | 3.4 | $15 | 2 |
| Real estate areas | 1.4 | $400 | 8 |
| All-in-one dashboard | -7.8 | $600 | 20 |

All-in-one is the destination, not the launch.

## Scope ladder

1. Weeks 1-4: bet tracker + edge math (reuse `~/workspace/carver`
   betting_lab) + receipts on every analysis.
2. Weeks 5-10: stocks journal (yfinance + receipts) — first cross-asset step.
3. Weeks 11-16: crypto (CoinGecko).
4. Months 5-8: real-estate area context, free public data only.

## Stack (from the plan, not re-debated)

Expo / React Native, FastAPI backend (~$7/mo), Supabase Postgres + Auth,
Upstash Redis, Sentry free tier, `carver_receipts` reused as-is.
The Odds API is the only must-pay data source for the betting v1.

## Field (honest)

Betting trackers (Pikkit, Juice Reel) have no edge math and no receipts.
Odds tools (OddsJam) are $200-500/mo prosumer. Aggregators (Kubera) track
net worth, no edge scoring. Whitespace = cross-asset edge + signed receipts.
Marketing-claim discipline: never "the only finance app..." until a fresh
search backs the sentence (same rule as the receipts novelty check).

## Differentiator research (2026-10-25, searched, not assumed)

TAKEN — do not pitch as new:
- Sealed/verified pick records: Agatha.gg (blockchain-sealed AI picks),
  Cappix (tamper-proof capper records), SHMACKD (verifiable betting
  identity), Verodd — literally markets "Screenshots lie. Receipts don't."
- CLV tracking: Pikkit Pro already does it, incl. no-vig fair-price CLV.

STILL OPEN (per this search):
- **Sharp Mirror** — sportsbooks profile every bettor (CLV capture, bet
  timing, stake patterns, market selection) to decide who gets limited.
  Nobody sells the bettor his own profile. Prototype built and verified:
  `prototype/sharp_mirror.py` computes CLV (Shin devig), Brier calibration,
  parlay/late-bet ROI leaks, tilt events, and a Sharp Score from a bet
  journal, then seals the report as a Carver Receipt (verify = OK).
  Demo profile narrative: "prices like a sharp (+1.38% CLV, beats close
  71%), leaks like a fan (parlays -11.5% ROI, late bets -14.9%, 24 tilt
  events) — Sharp Score 22/99."
- Cross-asset single edge rubric (bets + stocks + crypto) with the mirror
  applied per asset. Cappix covers cappers and traders separately; nobody
  in the search unifies them under one score.

Positioning rule that follows: receipts are table stakes in this lane now,
not the headline. The headline is the Mirror; the receipt is its proof.
Brand line (from the Agatha observation — their headline record is a
curated "Best Bets" subset): **"We grade every bet, not just the ones
that worked."**

Honest demo narrative (revised after the CI finding — the old "biggest
leak: parlays" headline was noise): "This bettor's one statistically real
signal is that he beats the close 71% of the time (CI 61-80%) — genuinely
sharp pricing. His leaks are suggestive, not proven. The app proves what
you're good at, and tells you plainly what it can't prove yet." Receipts
pin the rubric itself (version + weights + formula sha in the signed
meta), so a score is recomputable by anyone, forever, under the rubric
that produced it. Two layers: Mirror on imported history (day 1) +
TrueEdge de-bias on sealed pre-game estimates (unlocks ~30 estimates).

Story order (settled 2026-10-25, after the pooling measurement): the
day-1 hook is the PROFILE — CLV, price-calibration, leaks, Skill/
Discipline axes, trend baseline. "Here's what the books see when they
look at you." De-bias is the retention unlock, NOT the hook: the pooled
curve's simultaneous band is ±11.8% at 300 estimates and ±4.9% at 1,500
(two-state demo: `prototype/demo_verdicts.py`), so corrections are
displayed from day 1 but rarely clear the conservative bar until a user
has logged for months. Lead marketing with the profile; de-bias is why
they stay.

Three calibration layers (clarified 2026-10-25): (1) CLV — import-supported,
table stakes (Verodd/Pikkit). (2) Price-calibration — import-supported,
built into the Mirror: buckets by implied price taken, "price said 52%,
you hit 56%," Wilson CIs, tiers. (3) Own-estimate calibration / de-bias —
needs sealed pre-game estimates; correction is empirical-Bayes shrunk
(k=15, a disclosed, versioned knob — `prototype/trueedge_fixed.py`) and
ships TIERED with its CI and a conservative edge, not behind a binary
lock: the proposed ±3pt CI lock was measured and rejected (a 300-estimate
user still needed ~757 more). "Your number" UX: one tap, pre-filled with
the market price, edit optional — the feature self-selects engaged users.
Ruin sim, if revived: bootstrap actual per-bet profits only; the
avg-rate × avg-odds version is banned (method wrong even though on the
demo data it landed within ~2 pts of the bootstrap).

## Open decisions (Robert's)

- v1 vertical, one word: betting (scoring winner) / stocks / crypto / realestate
- Receipts buyer (from the receipts thread): developer SDK vs law/consultancy

## Standing context

Robert's NOW focus per LifeMap is bootcamp + BI job hunt. This app is a real
candidate for NEXT — the ladder above is sized so it does not eat the job hunt.
