# TrueEdge — Design System

## THE MASTER LOOK (2026-10-25, Robert: "create the look of the app
## based off the logo as the master look") — CURRENT, supersedes below

The app wears the master logo's system:
- **Colors (audited with design_audit.py):** bg navy #03122F, surface
  #0A2148, border #1D3A66, text silver-white #F2F6FC (17.1 AAA),
  muted blue-silver #9DB2CE (AAA), faint #5E7799 (3.46 — labels only,
  same rule as before), **gold #F0AE35 (9.6 AAA) = primary accent /
  Discipline**, **electric blue #2F9DFF (AA — large elements only) =
  Skill / links / swoosh**, success #4ADE80 and danger #F87171 keep
  their functional jobs.
- **Type:** headings and the wordmark in the logo's voice — heavy
  (800) italic, tight tracking. Body Inter. Numbers JetBrains Mono.
- **Brand header on every screen:** simplified icon + "TRUE EDGE"
  wordmark (TRUE silver, EDGE gold) + a blue swoosh rule.
- **Semantic color split:** Skill renders blue, Discipline renders
  gold — the logo's two colors, put to work.
- **Layout rules survive from the audit:** 8pt grid, 12pt cards, 1px
  borders, 44pt touch floor, mono numerals, faint = labels only.
  What changed is the skin, not the discipline.
Implemented in `app/src/theme.ts` (tokens + display type) and
`app/src/ui.tsx` (BrandHeader, AxisBar color prop); typecheck clean.

## Previous system (audited 2026-10-25) — superseded, kept for history

Audit script: `design_audit.py` (run it — the numbers below are its
output, not estimates). Design thesis: a diagnostic instrument, not a
casino. References: Bloomberg Terminal, 1Password, Credit Karma,
Oura, Linear. Explicitly NOT: DraftKings, FanDuel, Pikkit.

## Color (dark-first, WCAG-audited)

| token | hex | on bg | verdict |
|---|---|---|---|
| bg | #0A0A0B | — | near-black; pure black is harsh on OLED |
| surface | #141517 | — | |
| border | #26282C | — | 1px borders; no drop shadows |
| text | #F5F6F7 | 18.29 | AAA |
| text on surface | | 16.89 | AAA |
| text_muted | #9BA1A6 | 7.58 / 7.00 | AAA on bg; **AA on surface** (true value 6.996 — the display rounds to 7.00, the standard doesn't) |
| text_faint | #6B7075 | 3.65 | **FAIL for body text** — large/non-essential labels only (timestamps, footnotes, 18pt+); using it for copy is a bug |
| accent | #E8B048 | 10.12 | AAA — amber: caution/terminal, deliberately not casino-green |
| success | #4ADE80 | 11.36 | AAA — verified states only, sparingly |
| danger | #F87171 | 7.15 | AAA — leaks only, sparingly |

No gradients. No glows. No neon. That restraint IS the brand.

## Type

- UI: **Inter**. Numbers: **JetBrains Mono**, tabular numerals
  everywhere, right-aligned in tables. No exceptions — this app is
  numbers.
- Modular scale, ratio 1.25. The audit's base-15 run gives
  15 / 18.8 / 23.4 / 29.3 / 36.6 / 45.8 / 57.2 / 71.5.
  **Adopted: base 16** (16 / 20 / 25 / 31 / 39 / 49 / 61 / 76) —
  15pt base is small for a data-dense app. (Note: the pasted audit
  script's label order was inverted — caption printed largest-role
  values; the scale values are what carry over, mapped to roles
  largest-first: display 76 → caption 16.)
- The seal moment is the signature visual: a sealed report renders
  as a monospace document, 1px border, like a physical receipt.
  It's the shareable artifact and the brand anchor.

## Layout / structure

- 8pt grid, 4pt sub-grid. 16pt margins and gutters.
- Cards: 12pt radius, 1px border, no shadow.
- Screens (from the paywall structure): Profile (free) → History &
  Trends (Plus) → De-bias / Attribution / Seal (Pro), with the
  Plus→Pro progress line ("de-bias sharpens at 30 sealed estimates —
  you have 12") rendered as a persistent element in Plus.
- Touch targets: 44pt minimum, no exceptions. The audit's spec table
  failed `close_x` at 40pt on BOTH platforms — the modal close is the
  most-tapped element in a data app; it ships at 44+. Inline links
  are fine at 20pt text only if the tap area is padded to 44.

## Logo / icon

- **MASTER LOGO supplied by Robert 2026-10-25** (`app/assets/logo-master.png`):
  glossy esports-style emblem on navy (#03122F) — silver TE monogram
  with a rising arrow, blue/gold swoosh ring, football + checkered
  flag + stadium details, "TRUE EDGE" wordmark (TRUE silver, EDGE
  gold). This is the brand's hero face (splash, store listing,
  socials). Size test (`logo_sizetest.png`): reads at 180–120px,
  busy at 60, detail mushes at 29.
- **ICON DERIVATIVE BUILT 2026-10-25** (`app/assets/icon.png`, built
  by `build_icon.py`, Robert approved the direction): the master's
  TE + arrow core only — silver metallic TE on the master's navy,
  gold arrow weaving behind the E and breaking out top-right, one
  blue swoosh underneath. Nothing else. At 29px it still reads "TE"
  (`icon_sizetest.png`, master vs simplified rows). Wired as the app
  icon in app.json; the master is the splash image. The basketball
  below was the locked mark until the master superseded it; the SVGs
  are kept as `app/assets/mark-basketball.svg` / `mark-mirror.svg`.
- Mark (earlier lock, now the icon-derivative candidate): the basketball. The abstract
  circle-and-line read as a finance app; the football (oval + laces)
  and "The Step" (two-tone stepped bar — market line vs true line)
  were drawn as contenders and passed over for instant sports
  recognition. Final: a basketball-seamed ball whose vertical seam IS
  the mirror line (circle + vertical/horizontal seams + two arcs,
  one weight, ~88px at the 1024 base — above the legibility floor).
  Masters: `app/assets/icon.svg` (full-bleed store icon) and
  `app/assets/logo.svg` (transparent; monochrome-black variant for
  receipt headers).
- **Hard rule from the audit: stroke ≥ 53px at the 1024 base.** A
  12px stroke renders 0.34px at the 29px App Store size — a smudge.
  53px is what "clean at 29px" costs. Most logo drafts fail this;
  check the file, not the mockup.

## Name — LOCKED by Robert (2026-10-25): **TrueEdge**

Robert picked TrueEdge over the heuristic winner (Baseline) and the
thesis pick (Trueline). It scored 6.2 in the audit and it was already
the internal name of the de-bias engine (`trueedge_fixed.py`), so the
brand and the codebase agree. Architecture: Carver = company,
**TrueEdge = the consumer app**, Carver Receipts = the firm-facing
product. Bundle id: `com.carver.trueedge`. (Details below kept for
the record.)

## Name (the data that was on the table)

Heuristic scores (syllables + typing friction ONLY — the counter in
`design_audit.py` was wrong twice before it was right; treat all of
this as weak evidence): Baseline 6.9, TrueEdge 6.2, Carver 5.8,
Trueline 5.6, Gauge 5.5, Sharp Mirror 4.8, Verity 3.5.
The heuristic cannot measure ownability: "Baseline" is unsearchable
generic; "Trueline" carries the thesis (the line, made true) and
extends to "Trueline Verified." Brand architecture if Trueline:
Carver = company, Trueline = consumer app, Carver Receipts = the
firm-facing product. Working name in code remains Sharp Mirror
until Robert locks one.
