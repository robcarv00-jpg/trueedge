# Sharp Mirror — affordable App Store launch plan

Robert's call (2026-10-25): affordable to build, affordable to run,
affordable for users, listed on the App Store. This plan is built around
that constraint. Every number below was checked against current sources
on 2026-10-25.

## The cost sheet (the whole thing)

| Item | Cost | Notes |
|---|---|---|
| Apple Developer Program | $99/yr | Required to list on the App Store. Renews yearly. |
| Google Play (optional, later) | $25 once | Personal accounts must first run a closed test: 12 testers opted in for 14 days before production. iOS first avoids this entirely. |
| App builds | $0 | Expo EAS cloud builds — no Mac needed (Robert's box is an HP ProBook). Free tier covers a solo launch cadence. |
| Backend / hosting | $0 at launch | See architecture below. |
| Odds data | $0 at launch | No Odds API in v1 (see scope). |
| Domain + privacy policy page | ~$12/yr | One domain, one static page. |
| **Total to launch** | **~$111 first year, ~$99/yr after** | |
| Store commission | 15% | Apple Small Business Program (under $1M/yr proceeds). On a $5.99 sub Robert nets ~$5.09; on $39.99/yr, ~$34. |

## Architecture decision that makes it affordable: on-device first

The Mirror engine is arithmetic over the user's own journal rows. Nothing
in v1 needs a server:

- Journal stored on the phone (SQLite). Import = CSV file picker.
  Manual entry = a form. All Mirror math (CLV, price-calibration, axes,
  leaks, trend) computed on-device from the Python prototype's logic.
- Receipts sealed on-device; verification works offline (that's the
  format's whole point).
- No accounts, no auth, no Supabase, no FastAPI in v1. Sync and accounts
  are a v1.1 decision, made only if users ask — and they move running
  costs from $0 to real money, so they wait for revenue.

This is also a privacy story competitors can't copy cheaply: "your
betting history never leaves your phone."

## v1 scope (what's in, what's cut, and why)

IN: CSV import, manual bet entry, Mirror report (CLV, price-calibration,
Skill/Discipline, leak tiers, trend baseline), sealed receipt + share,
"your number" estimate logging (feeds de-bias later).

CUT for v1 (each is a cost or review risk):
- Live odds / Odds API — imports and manual entry already carry closing
  lines; a paid data feed is the first step off $0/mo.
- Picks, tips, recommendations of specific bets — App Store + FTC risk,
  and against the product's own philosophy.
- Sportsbook links or affiliate deals — the fastest way to get a journal
  app treated as a gambling app.
- Accounts/social — no server, no moderation burden, nothing to breach.

## App Store compliance checklist (Guideline 5.3)

5.3.4's licensing/geo-restriction rules bind apps that OFFER real-money
gaming. Sharp Mirror offers no wagering: no bet placement, no deposits,
no withdrawals, no fund transfers (also keeps 5.3.3 clean). Precedent:
bet-tracker apps sit on the store today on exactly this basis. The
review risk is framing, so:

- [ ] Age rating 17+ (gambling *references* — do not fight this, take it).
- [ ] Store copy and screenshots: journal/analytics language only
      ("track", "grade", "see your real numbers"). Never "win", "beat
      the book", "guaranteed", "picks", "tips".
- [ ] No outbound links to sportsbooks anywhere in the app or metadata.
- [ ] In-app disclaimer: analytics on your own history; not gambling
      advice; no outcome is promised.
- [ ] Review notes to Apple, first line: "This app does not offer
      wagering of any kind. It is a personal journal and analytics
      tool for bets the user placed elsewhere." Attach a demo video.
- [ ] Privacy policy URL live before submission; data collection: none
      leaves the device in v1 — say exactly that in the privacy label.

## Pricing for users (modeled 2026-10-25, `pricing_model.py`)

Free download, free Mirror report on up to 50 imported bets; Premium
unlocks unlimited history, attribution (when volume qualifies), sealed
receipts archive, trend history.

Competitor anchors (checked): Pikkit Pro $29.99/mo / $199.99/yr,
Action PRO $24.99/mo / ~$99.99/yr, Rithmm $29.99/mo, Dimers $25/mo.
The lane's headline prices cluster $25–40/mo — anything under $10 is
the affordable option on the shelf by a wide margin.

Model: constant-elasticity demand around a 3% conversion reference at
$6.99, 60/40 annual/monthly mix, price-scaled churn, Apple 15%.
24-month net revenue per 1,000 activated users is remarkably flat
between $4.99 and $9.99 ($1,460–$2,013 depending on scenario) — inside
that band, conversion and retention matter more than the price point.
The robust pick (maximizes the worst-case elasticity scenario) is
$6.99/mo, $39.99/yr: worst case $1,810 vs $1,625 at $4.99 and
$940 at $19.99. True optimum can't be known until elasticity is
measured — the 5-bettor cohort gets a price question, and the price
can move after launch; it just can't be the launch blocker.

**STRUCTURE LOCKED by Robert (2026-10-25, final revision): two paid
tiers, not a single price.** (History: $4.99 single, then $14.99
single, then this — the two-tier supersedes both.)

- **Free — "who you are":** CSV import, Mirror profile, Skill/
  Discipline score, price-calibration. The identity report is the
  acquisition surface; it is never paywalled.
- **Plus $4.99/mo ($34.99/yr) — "where you're improving," basics:**
  unlimited history, trend lines, live-leak tracking.
- **Pro $14.99/mo ($89.99/yr) — the full improvement engine:**
  de-bias on sealed estimates, attribution, base-rate grading of
  live bets, report sealing. **Verification stays free for anyone,
  forever** — a receipt anyone can check is the distribution loop;
  only sealing is Pro.

Gate design (the waiting-room rule): Plus is the user's PAST —
what happened, static analysis, history. Pro is the user's FUTURE —
the model learns you and says what to do next. Different value
propositions, not a crippled tier and a full tier. Inside Plus, a
visible progress line does the upgrade work: "Your Pro tools
activate as you log — de-bias sharpens at 30 sealed estimates.
You have 12." Without it, Plus feels complete and cannibalization
(the exception below) happens at whatever rate semis prefer $4.99.

On verification, the load-bearing line, verbatim for all copy:
**"Verification is free forever because a seal that only paying
parties can check isn't a seal."** Free verification isn't a growth
hack; it's structurally required — a paywalled check would prove
only that the issuer paid, which is the exact trust problem the
format exists to kill. Share links shipped 2026-10-25: the HTML
verifier now encodes a receipt into a `#r=` fragment link (never
sent to a server, works from any static copy of the file), so
"check this receipt" is one click in any browser — no app, no
account. Parity suite still 8/8 after the change.

Why two tiers (`pricing_tiers.py`, segment model: casuals convert
only at $4.99, semi-serious pay $14.99 when asked): two-tier beats
every single price in the plausible range — $2,883–$3,217 per 1,000
activated users at a 30% semi-serious share, vs $2,104–$2,278 for
the best single price. The honest exception: if semis are ~50% of
the base AND half of them cannibalize down to Plus, single $14.99
wins ($3,615 vs $3,216). The paywall placement is the conversion
lever, and conversion is what the model says matters.

**Price test (post-launch): Pro at $9.99 vs $14.99.** Sample size,
computed not asserted: separating 4% from 3% conversion at 80%
power takes ~5,300 users per arm. At 1,500/arm power is 32% — that
test would be a coin flip wearing a lab coat. Either run it long,
or judge it on revenue per user (a more sensitive metric than
binary conversion). Not $4.99 vs $9.99: under realistic elasticity
those convert too closely to separate at any feasible n.

## Live module — scope ruling (2026-10-25)

Live/in-play is a v1.1 Mirror MODULE, not a v1 feature and not a
prediction product: pre-sealed live bet journaling, live leak detection
(Q4 ROI, live tilt, trailing-vs-leading), and situational base rates
from free logs (`prototype/live_engine.py`). In-play prediction is
declined permanently: it's a latency race against Sportradar/Genius
feeds, and "more accurate picks" framing is barred (5.3/FTC).
Real-data check already run on the free nflverse games file (7,370
games, 1999–2026): home win rate 57.3% (2003–09) → 56.9% (2010–19) →
53.9% (2020–25) — home-field advantage really is decaying, which is
why baselines use recent windows and store the window in the report.
Note the tension, recorded honestly: live CLV needs a real odds feed
(~$30/mo class) — that spend waits for revenue, per the $0 v1 rule;
v1.1 live ships journaling + leaks + base rates, CLV when the feed pays
for itself.

## Sequence and gates

1. Robert: Apple Developer enrollment ($99, his Apple ID, his payment) —
   the only hard gate only he can clear.
2. Build: Expo app, on-device engine port from the Python prototype,
   EAS build, TestFlight.
3. The 5-bettor test runs on TestFlight builds — same cohort plan,
   better instrument (real app, real journals).
4. Submit with the checklist above. Expect one review round-trip on
   5.3 framing; the review notes and demo video are prepared for it.
