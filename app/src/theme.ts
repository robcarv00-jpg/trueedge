/** TrueEdge theme — THE MASTER LOOK (2026-10-25, Robert's direction):
 *  the app wears the logo. Navy field, electric blue, metallic silver,
 *  gold accent — the master emblem's system, contrast-audited with
 *  design_audit.py (all pairs AA or better; faint is labels-only,
 *  blue is large-elements-only). Supersedes the near-black/amber
 *  diagnostic palette; that restraint survives in the layout rules:
 *  1px borders, 8pt grid, numerals in mono. */
export const colors = {
  bg: '#03122F',          // master navy
  bgDeep: '#020B20',      // gradient floor / tab bar
  surface: '#0A2148',
  border: '#1D3A66',
  text: '#F2F6FC',        // silver-white — 17.1:1 on bg, AAA
  textMuted: '#9DB2CE',   // blue-silver — AAA on bg and surface
  textFaint: '#5E7799',   // 3.46:1 — LARGE / non-essential labels ONLY
  accent: '#F0AE35',      // logo gold — 9.6:1 AAA; primary actions
  accentDeep: '#A86E0F',  // deep gold for FILLED surfaces that carry
                          // silver text (silver on bright gold = 1.9:1,
                          // unreadable; on deep gold = 4.1:1) — Robert's
                          // call 2026-10-25: silver font, no black letters
  onAccent: '#F2F6FC',    // silver — the font color on filled gold
  accentBlue: '#2F9DFF',  // logo electric blue — AA; large elements, bars, links
  success: '#4ADE80',     // verified states only — AAA on navy
  danger: '#F87171',      // leaks only — AA on navy
} as const;

/** The logo's voice in type: heavy italic display for headings and the
 *  wordmark; Inter for UI text; JetBrains Mono for every number. */
export const display = {
  fontWeight: '800' as const,
  fontStyle: 'italic' as const,
  letterSpacing: -0.5,
};

/** Base-16 modular scale (ratio 1.25). */
export const type = {
  caption: 13, footnote: 16, bodySm: 20, body: 16, bodyLg: 20,
  title3: 25, title2: 31, title1: 39, display: 49,
} as const;

export const space = { xs: 4, sm: 8, md: 16, lg: 24, xl: 32 } as const;
export const radius = { card: 12, chip: 6 } as const;
export const MIN_TOUCH = 44; // Apple HIG — no exceptions
export const mono = 'JetBrains Mono'; // numbers; system mono until the font ships
