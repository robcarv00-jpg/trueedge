# TrueEdge — From This Folder to a Real App on the Store

Everything is already built and verified. This guide is the path from
this folder to (1) your GitHub, (2) running on your phone, (3) a real
installable build, (4) the App Store. Follow it top to bottom.

## What you have (file map)

| Path | What it is |
|---|---|
| `app/` | The phone app (Expo / React Native, TypeScript) |
| `app/src/core/` | The engine: odds math, Mirror profile, scoring, sealing. Pure TypeScript, no phone dependencies |
| `app/src/screens/` | The 5 screens: Profile, Trend, Log, Seal, Plan |
| `app/assets/` | `icon.png` (home-screen icon), `logo-master.png` (your full logo, the splash screen) |
| `app/app.json` | App name, bundle ID `com.carver.trueedge`, store settings |
| `app/eas.json` | Build profiles for EAS (the build service) |
| `prototype/` | The original Python engine and research the app was ported from |
| `LAUNCH_PLAN.md` | Pricing, App Store compliance checklist, launch costs |
| `DESIGN.md` | The master-look design system (colors, type, rules) |
| `APP_BRIEF.md` | The product brief and research behind every decision |
| `build_icon.py` | Regenerates the icon if you ever change the logo |

Costs, total: Apple Developer $99/year. Everything else below is free
until the app earns (Expo builds free tier, GitHub free).

---

## STEP 1 — The code on GitHub (DONE 2026-10-25)

**Live: https://github.com/robcarv00-jpg/trueedge** (public).

The repo exists and the full project is pushed: app source, engine,
docs, and brand assets. My GitHub connection cannot create
repositories (403), so the empty repo was created in Robert's
signed-in browser session; the code itself was pushed through the
connection as snapshot commits.

For future changes, the flow is: tell me what changed and I push it,
or from a terminal inside this folder:

```
git add -A
git commit -m "what changed"
```

then ask me to push (plain `git push` needs your own GitHub login on
that machine; the connection push runs through me).

## STEP 2 — Run it on your phone today (free, 15 minutes)

This uses Expo Go, a free app that runs your app live while you
develop. No Apple account needed for this step.

1. Install **Node.js LTS** from nodejs.org (the big green button).
2. On your phone, install **Expo Go** from the App Store / Play Store.
3. In a terminal, go to the app folder and install dependencies:

```
cd carver-app/app
npm install
```

   (If install throws permission errors, run it again as
   `npm install --ignore-scripts --no-bin-links`.)
4. Start the dev server:

```
npx expo start
```

5. A QR code appears in the terminal. Scan it with your phone camera
   (iPhone) or inside Expo Go (Android). The app opens on your phone.
6. Edit any file, save, and the phone updates instantly. That is the
   whole development loop.

## STEP 3 — Build a real installable app (EAS Build)

Expo Application Services (EAS) builds the actual app file in the
cloud. No Mac needed; this works from your ProBook.

1. Create a free account at expo.dev.
2. Install the build tool and sign in:

```
npm install -g eas-cli
eas login
```

3. Link the project (one time, inside `carver-app/app`):

```
eas init
```

4. Build a test version:

```
eas build --platform android --profile preview
```

   Android gives you an APK file you can install on any Android
   phone directly. iPhone builds need Step 4 first.
5. Every build lands on your Expo dashboard with a download link and
   a QR code.

## STEP 4 — Apple: the $99 gate (only you can do this)

1. Enroll at developer.apple.com with YOUR Apple ID. $99/year.
   Enroll as an **Individual** (a business account needs a DUNS
   number and adds 1-2 weeks; you can convert later).
2. Once approved, build for iOS and send it to TestFlight:

```
eas build --platform ios --profile production
eas submit --platform ios
```

3. TestFlight (Apple's free beta app) is where your 5 test bettors
   install it. Add their emails in App Store Connect under
   TestFlight and they get an invite link.
4. Run the 5-bettor test from `prototype/TEST_PLAN.md` on the
   TestFlight build before submitting for review.

## STEP 5 — The App Store listing (App Store Connect)

In App Store Connect (appstoreconnect.apple.com) → your app:

- **Name:** TrueEdge
- **Subtitle:** Know your betting profile (never use "win", "picks",
  "guaranteed", or "beat the books" anywhere; this is a journal and
  analytics app, and Guideline 5.3 is enforced on wording)
- **Age rating:** 17+
- **Category:** Sports (secondary: Finance is fine too, but Sports
  first)
- **Screenshots:** take them from the running app (Step 2 or a
  TestFlight build): Profile, Trend, Log, Seal, Plan
- **Review note** (paste this in the "Notes for Review" box):

> This app does not offer wagering of any kind: no bet placement, no
> deposits, no sportsbook links, no picks or predictions. It is a
> personal journal and analytics tool. All data is stored on the
> user's device only.

- **Privacy:** the app collects nothing and sends nothing. In the
  privacy questionnaire, answer "Data Not Collected".

Submit, and Apple reviews in roughly 1-3 days. If they ask questions,
the answer is always the review note above, plus the disclaimer that
is already inside the app (`app/app.json`, "extra.privacy").

## STEP 6 — Before you charge money (hardening list)

The app works today with these honest stubs (listed in
`app/README.md`). Each one gets finished before or right after the
public launch, in this order:

1. **Billing:** wire StoreKit through Expo's in-app purchase module
   so Plus ($4.99/mo) and Pro ($14.99/mo) actually charge. Apple
   keeps 15% under the Small Business Program (apply in App Store
   Connect).
2. **Sealing keys:** replace the demo sealing key with a per-user
   key plus Ed25519 signing (the design is done; the Python side in
   the Carver Receipts project already works this way).
3. **Host the verifier page** so "copy share link" points at a real
   URL (any free static host: GitHub Pages works, and you already
   have the repo from Step 1).
4. **Ship the JetBrains Mono font** as an app asset so numbers render
   in the real brand font instead of the system mono.

None of these block TestFlight or the bettor test. They block
charging strangers, in that order.

## If anything breaks

Tell me the step number and what the screen says. The code, the
verified engine tests (`app/tests/parity.mjs`), and this guide all
live in the repo, so any developer (or me, next session) can pick it
up cold.
