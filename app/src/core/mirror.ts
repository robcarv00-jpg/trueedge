/** Sharp Mirror engine — full TypeScript port of prototype/sharp_mirror.py.
 *  Same formulas, same rubric weights, same honesty rules:
 *  every rate ships with a 95% CI; leaks tier signal/noise/inconclusive;
 *  sealed receipts PIN the rubric and verifyScore FAILS CLOSED. */
import { implied, shin, roi } from './odds';
import {
  wilsonCI, bootstrapRoiCI, unitsPer100, leakTier, betsToResolve, round, Tier,
} from './stats';
import { Claim, ReceiptDict, sealReceipt } from './receipt';
import { canon } from './canon';
import { sha256hex } from './sha256';

export interface BetRow {
  market: string;               // spread | total | moneyline | prop | parlay
  odds: number;                 // American odds taken
  mins: number;                 // minutes before start
  stake: number;
  close: [number, number];      // closing odds (my side, other side)
  won: boolean;
  sport?: string;
  placed_at?: string;           // ISO timestamp, optional
  hour?: number;
  dow?: number;
}

export interface MirrorReport {
  bets: number;
  avg_clv_pct: number;
  beat_close_rate: number;
  beat_close_ci: [number, number];
  brier: number;
  price_cal_gap: number;
  parlay_share: number;
  parlay_n: number;
  parlay_roi: number;
  parlay_roi_ci: [number, number];
  parlay_tier: Tier;
  parlay_resolve_in: number | null;
  parlay_units100: number;
  parlay_units100_ci: [number, number];
  early_main_roi: number;
  early_main_roi_ci: [number, number];
  late_roi: number;
  late_roi_ci: [number, number];
  late_n: number;
  late_tier: Tier;
  late_resolve_in: number | null;
  late_units100: number;
  late_units100_ci: [number, number];
  tilt_events: number;
  tilt_per_100: number;
}

export function mirror(rows: BetRow[]): MirrorReport {
  const n = rows.length;
  const clvs: number[] = [];
  let brier = 0;
  for (const r of rows) {
    if (r.market !== 'parlay') {
      const fairClose = shin([implied(r.close[0]), implied(r.close[1])])[0];
      clvs.push(fairClose - implied(r.odds));
    }
    brier += (implied(r.odds) - (r.won ? 1 : 0)) ** 2;
  }
  const singles = rows.filter((r) => r.market !== 'parlay');
  const calGap =
    singles.reduce((s, r) => s + (r.won ? 1 : 0), 0) / Math.max(singles.length, 1) -
    singles.reduce((s, r) => s + implied(r.odds), 0) / Math.max(singles.length, 1);
  const late = rows.filter((r) => r.mins <= 15);
  const earlyMain = rows.filter(
    (r) => r.mins > 60 && (r.market === 'spread' || r.market === 'total'));
  const parlays = rows.filter((r) => r.market === 'parlay');
  const beat = clvs.filter((c) => c > 0).length;
  let tilt = 0;
  for (let i = 0; i + 1 < rows.length; i++) {
    if (!rows[i].won && rows[i + 1].stake > rows[i].stake) tilt++;
  }
  const pRoi = roi(parlays), pCi = bootstrapRoiCI(parlays);
  const lRoi = roi(late), lCi = bootstrapRoiCI(late);
  const [pUnits, pUnitsCi] = unitsPer100(parlays);
  const [lUnits, lUnitsCi] = unitsPer100(late);
  return {
    bets: n,
    avg_clv_pct: round((100 * clvs.reduce((a, b) => a + b, 0)) / Math.max(clvs.length, 1), 2),
    beat_close_rate: round(beat / Math.max(clvs.length, 1), 2),
    beat_close_ci: wilsonCI(beat, clvs.length),
    brier: round(brier / n, 3),
    price_cal_gap: round(calGap, 3),
    parlay_share: round(parlays.length / n, 2),
    parlay_n: parlays.length,
    parlay_roi: round(pRoi, 3),
    parlay_roi_ci: pCi,
    parlay_tier: leakTier(pRoi, pCi, parlays.length),
    parlay_resolve_in: betsToResolve(pRoi, pCi, parlays.length),
    parlay_units100: pUnits,
    parlay_units100_ci: pUnitsCi,
    early_main_roi: round(roi(earlyMain), 3),
    early_main_roi_ci: bootstrapRoiCI(earlyMain),
    late_roi: round(lRoi, 3),
    late_roi_ci: lCi,
    late_n: late.length,
    late_tier: leakTier(lRoi, lCi, late.length),
    late_resolve_in: betsToResolve(lRoi, lCi, late.length),
    late_units100: lUnits,
    late_units100_ci: lUnitsCi,
    tilt_events: tilt,
    tilt_per_100: round((100 * tilt) / n, 1),
  };
}

export interface CalBucket {
  range: string; n: number; implied: number; actual: number;
  actual_ci: [number, number]; tier: Tier;
}

/** Price calibration — CIs are individual 95%, not family-wise (say so in UI). */
export function priceCalibration(rows: BetRow[], width = 0.1): CalBucket[] {
  const buckets = new Map<number, BetRow[]>();
  for (const r of rows) {
    if (r.market === 'parlay') continue;
    const k = Math.floor(implied(r.odds) / width);
    buckets.set(k, [...(buckets.get(k) ?? []), r]);
  }
  return [...buckets.entries()]
    .sort((a, b) => a[0] - b[0])
    .map(([k, rs]) => {
      const wins = rs.filter((r) => r.won).length;
      const imp = rs.reduce((s, r) => s + implied(r.odds), 0) / rs.length;
      const ci = wilsonCI(wins, rs.length);
      const tier: Tier = rs.length < 30 ? 'inconclusive'
        : imp < ci[0] || imp > ci[1] ? 'signal' : 'noise';
      return {
        range: `${Math.round(k * width * 100)}%-${Math.round((k + 1) * width * 100)}%`,
        n: rs.length, implied: round(imp, 3), actual: round(wins / rs.length, 3),
        actual_ci: ci, tier,
      };
    });
}

// ---------- scores (SHARP_SCORE.md — rubric versions are news, not patches) ---

export const RUBRIC_VERSION = '1.1';
export const AXES_VERSION = '1.2';

export function sharpScoreV1(m: MirrorReport): number {
  const s = 50 + m.avg_clv_pct * 6 + (m.beat_close_rate - 0.5) * 40
    - m.parlay_share * 30 - m.tilt_events * 1.5
    - Math.max(0, m.brier - 0.24) * 100;
  return Math.max(1, Math.min(99, Math.round(s)));
}

export const WEIGHTS_V11 = {
  base: 50,
  clv_coef: 6, clv_cap: 24,
  beat_coef: 40, beat_cap: 20,
  brier_threshold: 0.24, brier_coef: 100, brier_cap: 20,
  parlay_coef: 30, parlay_scale: 0.2,
  late_coef: 10, late_scale: 0.2, late_min_n: 10,
  tilt_coef: 0.75,
} as const;
export type WeightsV11 = { [K in keyof typeof WEIGHTS_V11]: number };

const clamp = (x: number, cap: number) => Math.max(-cap, Math.min(cap, x));

export function sharpScoreV11(m: MirrorReport, w: WeightsV11 = { ...WEIGHTS_V11 }): number {
  let s = w.base;
  s += clamp(m.avg_clv_pct * w.clv_coef, w.clv_cap);
  s += clamp((m.beat_close_rate - 0.5) * w.beat_coef, w.beat_cap);
  s -= Math.max(0, Math.min(w.brier_cap, (m.brier - w.brier_threshold) * w.brier_coef));
  if (m.parlay_roi < 0) {
    s -= m.parlay_share * Math.min(1, -m.parlay_roi / w.parlay_scale) * w.parlay_coef;
  }
  if (m.late_roi < 0 && m.late_n >= w.late_min_n) {
    s -= w.late_coef * Math.min(1, -m.late_roi / w.late_scale);
  }
  s -= m.tilt_per_100 * w.tilt_coef;
  return Math.max(1, Math.min(99, Math.round(s)));
}

export const AXES_WEIGHTS = {
  skill: {
    base: 50, clv_coef: 7, clv_cap: 28, beat_coef: 50, beat_cap: 25,
    cal_gap_coef: 200, cal_gap_cap: 10,
    brier_threshold: 0.24, brier_coef: 100, brier_cap: 15,
  },
  discipline: {
    base: 90, tilt_coef: 1.2, tilt_cap: 30,
    parlay_coef: 40, parlay_cap: 30, parlay_scale: 0.2,
    share_excess_over: 0.3, share_excess_coef: 50, share_excess_cap: 10,
    late_coef: 20, late_scale: 0.25, late_min_n: 10,
  },
} as const;

export function sharpAxes(m: MirrorReport): { skill: number; discipline: number } {
  const sk = AXES_WEIGHTS.skill;
  let skill = sk.base;
  skill += clamp(m.avg_clv_pct * sk.clv_coef, sk.clv_cap);
  skill += clamp((m.beat_close_rate - 0.5) * sk.beat_coef, sk.beat_cap);
  skill += clamp(m.price_cal_gap * sk.cal_gap_coef, sk.cal_gap_cap);
  skill -= Math.max(0, Math.min(sk.brier_cap, (m.brier - sk.brier_threshold) * sk.brier_coef));
  const di = AXES_WEIGHTS.discipline;
  let disc = di.base;
  disc -= Math.min(di.tilt_cap, m.tilt_per_100 * di.tilt_coef);
  if (m.parlay_roi < 0) {
    disc -= Math.min(di.parlay_cap,
      m.parlay_share * Math.min(1, -m.parlay_roi / di.parlay_scale) * di.parlay_coef);
  }
  disc -= Math.min(di.share_excess_cap,
    Math.max(0, m.parlay_share - di.share_excess_over) * di.share_excess_coef);
  if (m.late_roi < 0 && m.late_n >= di.late_min_n) {
    disc -= di.late_coef * Math.min(1, -m.late_roi / di.late_scale);
  }
  return {
    skill: Math.max(1, Math.min(99, Math.round(skill))),
    discipline: Math.max(1, Math.min(99, Math.round(disc))),
  };
}

// ---------- trend -------------------------------------------------------------

export interface TrendPoint {
  through_bet: number; skill: number; discipline: number;
  tilt_per_100: number; avg_clv_pct: number;
}

/** Rolling 40-bet windows over the journal IN ORDER (import order is
 *  chronological). Week 1 this is a baseline, not a verdict. */
export function rollingTrend(rows: BetRow[], window = 40, step = 20): TrendPoint[] {
  const out: TrendPoint[] = [];
  for (let start = 0; start < Math.max(1, rows.length - window + 1); start += step) {
    const seg = rows.slice(start, start + window);
    if (seg.length < window) break;
    const m = mirror(seg);
    const ax = sharpAxes(m);
    out.push({
      through_bet: start + window, skill: ax.skill, discipline: ax.discipline,
      tilt_per_100: m.tilt_per_100, avg_clv_pct: m.avg_clv_pct,
    });
  }
  return out;
}

// ---------- sealing -----------------------------------------------------------

const pct = (x: number, dp = 0, signed = false) => {
  const v = (x * 100).toFixed(dp);
  return (signed && x >= 0 ? '+' : '') + v + '%';
};

/** The five sealed claims — same sentences the Python prototype seals. */
export function reportClaims(
  m: MirrorReport, score: number,
  evidenceSource: string, retrievedAt: string,
): Claim[] {
  const lines = [
    `Across ${m.bets} tracked bets the bettor's average closing line value was ${m.avg_clv_pct >= 0 ? '+' : ''}${m.avg_clv_pct.toFixed(2)} percent.`,
    `The bettor beat the closing price in ${pct(m.beat_close_rate)} of graded bets (95% CI ${pct(m.beat_close_ci[0])} to ${pct(m.beat_close_ci[1])}).`,
    `Parlays were ${pct(m.parlay_share)} of volume and returned ${pct(m.parlay_roi, 1, true)} ROI (95% CI ${pct(m.parlay_roi_ci[0], 1, true)} to ${pct(m.parlay_roi_ci[1], 1, true)}, n=${m.parlay_n}, tier ${m.parlay_tier}).`,
    `Stake-escalation after a loss (tilt) appeared ${m.tilt_events} times, ${m.tilt_per_100.toFixed(0)} per 100 bets.`,
    `The bettor's Sharp Score under rubric v${RUBRIC_VERSION} is ${score} out of 99.`,
  ];
  return lines.map((text, i) => ({
    id: `c${String(i + 1).padStart(3, '0')}`,
    text,
    status: 'verified' as const,
    evidence: [{
      source: evidenceSource, retrieved_at: retrievedAt,
      independence: 'primary', snippet: '', contradicts: false,
    }],
    stale_after_days: null,
    note: '',
  }));
}

export function sealMirrorReport(
  rows: BetRow[],
  opts: { key?: string; created_at: string; evidenceSource: string; retrievedAt: string },
): ReceiptDict {
  const m = mirror(rows);
  const score = sharpScoreV11(m);
  // Pinning must COPY the weights, never reference the live object —
  // a caller mutating receipt meta must not corrupt the rubric
  // (the deepcopy bug, round 4 of the prototype; do not regress).
  const weights: WeightsV11 = JSON.parse(JSON.stringify(WEIGHTS_V11));
  const meta = {
    rubric: {
      name: 'sharp_score', version: RUBRIC_VERSION, weights,
      weights_sha: sha256hex(canon(weights)),
    },
    score,
  };
  return sealReceipt({
    issuer: 'TrueEdge', subject: 'mirror-report', created_at: opts.created_at,
    claims: reportClaims(m, score, opts.evidenceSource, opts.retrievedAt),
    meta, key: opts.key,
  });
}

/** Recompute under the PINNED weights. FAILS CLOSED — any missing or
 *  malformed pinning is a named error, never a silent default. */
export function verifyScore(
  rows: BetRow[], receipt: ReceiptDict,
): { ok: boolean; msg: string } {
  const meta = receipt.meta as Record<string, unknown> | undefined;
  if (!meta || typeof meta !== 'object' || !Object.keys(meta).length) {
    return { ok: false, msg: 'receipt meta missing — no pinned rubric to verify against' };
  }
  const rub = meta.rubric as Record<string, unknown> | undefined;
  if (!rub || typeof rub !== 'object') {
    return { ok: false, msg: 'receipt meta.rubric missing or malformed' };
  }
  if (rub.name !== 'sharp_score') {
    return { ok: false, msg: `unexpected rubric name: ${JSON.stringify(rub.name)}` };
  }
  const weights = rub.weights as Record<string, number> | undefined;
  if (!weights || typeof weights !== 'object') {
    return { ok: false, msg: 'pinned weights missing or malformed' };
  }
  const missing = Object.keys(WEIGHTS_V11).filter((k) => !(k in weights));
  if (missing.length) {
    return { ok: false, msg: `pinned weights missing keys: ${missing.join(', ')}` };
  }
  const sealed = meta.score;
  if (typeof sealed !== 'number' || !Number.isInteger(sealed)) {
    return { ok: false, msg: 'sealed score missing or not an integer' };
  }
  const recomputed = sharpScoreV11(mirror(rows), weights as WeightsV11);
  if (recomputed !== sealed) {
    return { ok: false, msg: `score mismatch: recomputed ${recomputed} != sealed ${sealed}` };
  }
  const notes = [`score ${sealed} recomputed OK under pinned rubric v${String(rub.version)}`];
  if (rub.weights_sha !== sha256hex(canon(weights))) {
    return { ok: false, msg: 'pinned weights failed their own sha check (meta tampered)' };
  }
  if (sha256hex(canon(weights)) !== sha256hex(canon({ ...WEIGHTS_V11 }))) {
    notes.push('pinned weights differ from the current app rubric (pinned weights govern)');
  }
  return { ok: true, msg: notes.join('; ') };
}
