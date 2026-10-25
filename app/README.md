# TrueEdge — the app

Expo / React Native, iOS first. On-device everything: the Mirror math,
the journal (SQLite), and receipt sealing all run on the phone. No
backend, no accounts, no odds feed in v1 (LAUNCH_PLAN.md).

Name locked 2026-10-25: **TrueEdge** (company: Carver; firm product:
Carver Receipts). Design system: `../DESIGN.md`. Pricing/gate:
`../LAUNCH_PLAN.md` (Free = who you are; Plus $4.99 = your past,
trends; Pro $14.99 = your future, de-bias + sealing; verification
free for anyone forever).

## Layout

- `src/core/` — pure TypeScript engine, zero RN imports, Node-testable.
  Port of `../prototype/sharp_mirror.py` + the Carver Receipts sealing
  path. **Parity-proven**: same demo journal → same scores (v1 22,
  v1.1 39, Skill 74, Discipline 48), claim texts byte-identical, and
  the Python CLI verifies a JS-sealed receipt (`OK mode=hmac`).
  One disclosed difference: bootstrap CIs use a mulberry32 PRNG, so CI
  endpoints match the Python prototype's method within sampling noise,
  not bit-for-bit. Wilson CIs and all deterministic metrics are exact.
- `src/storage/db.ts` — expo-sqlite: bets, sealed estimates, kv (tier).
- `src/screens/` — Profile (free), Trend (Plus), Log (import + manual
  + "your number" sealed estimates), Seal (Pro), Plan (tiers + the
  Plus→Pro progress line).
- `tests/parity.mjs` — the parity suite. Run:
  `npx tsc -p tsconfig.core.json && node tests/parity.mjs`

## Run it

```
npm install
npx expo start        # scan the QR with Expo Go
```

## Ship it (needs Robert)

1. Apple Developer enrollment ($99, his Apple ID) — the only hard gate.
2. `eas build --platform ios` (EAS cloud builds, $0, no Mac needed).
3. TestFlight → the 5-bettor test (`../prototype/TEST_PLAN.md`).
4. Submit with the LAUNCH_PLAN checklist: 17+ rating, journal-language
   metadata, review note leading with "does not offer wagering."

## Known v1 stubs (honest list)

- Tier switching in Plan is a preview toggle; StoreKit billing wires
  at launch. The GATE logic (what each tier sees) is real.
- Sealing uses the demo HMAC key on-device; per-user key + Ed25519
  (public-key receipts) is the launch hardening step. The receipt
  format already supports it.
- De-bias/attribution are Pro roadmap: estimate logging (the data
  de-bias needs) ships in v1; the pooled calibration curve ports
  from `../prototype/trueedge_fixed.py` once a user has the volume.
- VERIFIER_URL in SealScreen is a placeholder until the verifier page
  is hosted; share links work from any copy of the verifier file.
