# TrueEdge

**Know your betting profile.** TrueEdge shows sports bettors the
profile the books build on them: closing line value, price
calibration, and the leaks that drain a bankroll (parlays, late bets,
tilt), graded on two axes, Skill and Discipline. Reports can be
sealed into tamper-evident Carver Receipts that anyone can verify
free, forever.

TrueEdge does not offer wagering of any kind: no bet placement, no
deposits, no sportsbook links, no picks or predictions. It is a
journal and analytics tool. All data stays on the user's device.

## Status

v0.1.0 — full app built and verified (engine parity-tested against
the reference Python implementation; a receipt sealed by the app's
JavaScript verifies in the Python CLI). Pre-launch: TestFlight and a
5-bettor validation test come next. See `BUILD_GUIDE.md`.

## Start here

| Doc | What it is |
|---|---|
| `BUILD_GUIDE.md` | Step by step: run it on your phone, build it with EAS, ship it to the App Store |
| `LAUNCH_PLAN.md` | Pricing (Free / Plus $4.99 / Pro $14.99), compliance checklist, launch costs |
| `DESIGN.md` | The master-look design system: navy, electric blue, silver, gold |
| `APP_BRIEF.md` | Product brief and the research behind every decision |
| `app/README.md` | App internals, honest v1 stubs, how to run the parity tests |

## Layout

- `app/` — the Expo / React Native app (TypeScript). Engine in
  `app/src/core/`, screens in `app/src/screens/`, brand assets in
  `app/assets/` (`icon.png` is the simplified TE + arrow icon derived
  from `logo-master.png`).
- `prototype/` — the Python research engine the app was ported from,
  including the Sharp Mirror prototype, rubric, and bettor test plan.
- `build_icon.py` — regenerates the app icon and its size tests.

## Brand

Carver is the company. TrueEdge is the app. Carver Receipts is the
sealing format. Verification is free forever because a seal that only
paying parties can check isn't a seal.
