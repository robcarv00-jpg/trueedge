"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.verifyScore = exports.sealMirrorReport = exports.reportClaims = exports.rollingTrend = exports.sharpAxes = exports.AXES_WEIGHTS = exports.sharpScoreV11 = exports.WEIGHTS_V11 = exports.sharpScoreV1 = exports.AXES_VERSION = exports.RUBRIC_VERSION = exports.priceCalibration = exports.mirror = void 0;
/** Sharp Mirror engine — full TypeScript port of prototype/sharp_mirror.py.
 *  Same formulas, same rubric weights, same honesty rules:
 *  every rate ships with a 95% CI; leaks tier signal/noise/inconclusive;
 *  sealed receipts PIN the rubric and verifyScore FAILS CLOSED. */
const odds_1 = require("./odds");
const stats_1 = require("./stats");
const receipt_1 = require("./receipt");
const canon_1 = require("./canon");
const sha256_1 = require("./sha256");
function mirror(rows) {
    const n = rows.length;
    const clvs = [];
    let brier = 0;
    for (const r of rows) {
        if (r.market !== 'parlay') {
            const fairClose = (0, odds_1.shin)([(0, odds_1.implied)(r.close[0]), (0, odds_1.implied)(r.close[1])])[0];
            clvs.push(fairClose - (0, odds_1.implied)(r.odds));
        }
        brier += ((0, odds_1.implied)(r.odds) - (r.won ? 1 : 0)) ** 2;
    }
    const singles = rows.filter((r) => r.market !== 'parlay');
    const calGap = singles.reduce((s, r) => s + (r.won ? 1 : 0), 0) / Math.max(singles.length, 1) -
        singles.reduce((s, r) => s + (0, odds_1.implied)(r.odds), 0) / Math.max(singles.length, 1);
    const late = rows.filter((r) => r.mins <= 15);
    const earlyMain = rows.filter((r) => r.mins > 60 && (r.market === 'spread' || r.market === 'total'));
    const parlays = rows.filter((r) => r.market === 'parlay');
    const beat = clvs.filter((c) => c > 0).length;
    let tilt = 0;
    for (let i = 0; i + 1 < rows.length; i++) {
        if (!rows[i].won && rows[i + 1].stake > rows[i].stake)
            tilt++;
    }
    const pRoi = (0, odds_1.roi)(parlays), pCi = (0, stats_1.bootstrapRoiCI)(parlays);
    const lRoi = (0, odds_1.roi)(late), lCi = (0, stats_1.bootstrapRoiCI)(late);
    const [pUnits, pUnitsCi] = (0, stats_1.unitsPer100)(parlays);
    const [lUnits, lUnitsCi] = (0, stats_1.unitsPer100)(late);
    return {
        bets: n,
        avg_clv_pct: (0, stats_1.round)((100 * clvs.reduce((a, b) => a + b, 0)) / Math.max(clvs.length, 1), 2),
        beat_close_rate: (0, stats_1.round)(beat / Math.max(clvs.length, 1), 2),
        beat_close_ci: (0, stats_1.wilsonCI)(beat, clvs.length),
        brier: (0, stats_1.round)(brier / n, 3),
        price_cal_gap: (0, stats_1.round)(calGap, 3),
        parlay_share: (0, stats_1.round)(parlays.length / n, 2),
        parlay_n: parlays.length,
        parlay_roi: (0, stats_1.round)(pRoi, 3),
        parlay_roi_ci: pCi,
        parlay_tier: (0, stats_1.leakTier)(pRoi, pCi, parlays.length),
        parlay_resolve_in: (0, stats_1.betsToResolve)(pRoi, pCi, parlays.length),
        parlay_units100: pUnits,
        parlay_units100_ci: pUnitsCi,
        early_main_roi: (0, stats_1.round)((0, odds_1.roi)(earlyMain), 3),
        early_main_roi_ci: (0, stats_1.bootstrapRoiCI)(earlyMain),
        late_roi: (0, stats_1.round)(lRoi, 3),
        late_roi_ci: lCi,
        late_n: late.length,
        late_tier: (0, stats_1.leakTier)(lRoi, lCi, late.length),
        late_resolve_in: (0, stats_1.betsToResolve)(lRoi, lCi, late.length),
        late_units100: lUnits,
        late_units100_ci: lUnitsCi,
        tilt_events: tilt,
        tilt_per_100: (0, stats_1.round)((100 * tilt) / n, 1),
    };
}
exports.mirror = mirror;
/** Price calibration — CIs are individual 95%, not family-wise (say so in UI). */
function priceCalibration(rows, width = 0.1) {
    const buckets = new Map();
    for (const r of rows) {
        if (r.market === 'parlay')
            continue;
        const k = Math.floor((0, odds_1.implied)(r.odds) / width);
        buckets.set(k, [...(buckets.get(k) ?? []), r]);
    }
    return [...buckets.entries()]
        .sort((a, b) => a[0] - b[0])
        .map(([k, rs]) => {
        const wins = rs.filter((r) => r.won).length;
        const imp = rs.reduce((s, r) => s + (0, odds_1.implied)(r.odds), 0) / rs.length;
        const ci = (0, stats_1.wilsonCI)(wins, rs.length);
        const tier = rs.length < 30 ? 'inconclusive'
            : imp < ci[0] || imp > ci[1] ? 'signal' : 'noise';
        return {
            range: `${Math.round(k * width * 100)}%-${Math.round((k + 1) * width * 100)}%`,
            n: rs.length, implied: (0, stats_1.round)(imp, 3), actual: (0, stats_1.round)(wins / rs.length, 3),
            actual_ci: ci, tier,
        };
    });
}
exports.priceCalibration = priceCalibration;
// ---------- scores (SHARP_SCORE.md — rubric versions are news, not patches) ---
exports.RUBRIC_VERSION = '1.1';
exports.AXES_VERSION = '1.2';
function sharpScoreV1(m) {
    const s = 50 + m.avg_clv_pct * 6 + (m.beat_close_rate - 0.5) * 40
        - m.parlay_share * 30 - m.tilt_events * 1.5
        - Math.max(0, m.brier - 0.24) * 100;
    return Math.max(1, Math.min(99, Math.round(s)));
}
exports.sharpScoreV1 = sharpScoreV1;
exports.WEIGHTS_V11 = {
    base: 50,
    clv_coef: 6, clv_cap: 24,
    beat_coef: 40, beat_cap: 20,
    brier_threshold: 0.24, brier_coef: 100, brier_cap: 20,
    parlay_coef: 30, parlay_scale: 0.2,
    late_coef: 10, late_scale: 0.2, late_min_n: 10,
    tilt_coef: 0.75,
};
const clamp = (x, cap) => Math.max(-cap, Math.min(cap, x));
function sharpScoreV11(m, w = { ...exports.WEIGHTS_V11 }) {
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
exports.sharpScoreV11 = sharpScoreV11;
exports.AXES_WEIGHTS = {
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
};
function sharpAxes(m) {
    const sk = exports.AXES_WEIGHTS.skill;
    let skill = sk.base;
    skill += clamp(m.avg_clv_pct * sk.clv_coef, sk.clv_cap);
    skill += clamp((m.beat_close_rate - 0.5) * sk.beat_coef, sk.beat_cap);
    skill += clamp(m.price_cal_gap * sk.cal_gap_coef, sk.cal_gap_cap);
    skill -= Math.max(0, Math.min(sk.brier_cap, (m.brier - sk.brier_threshold) * sk.brier_coef));
    const di = exports.AXES_WEIGHTS.discipline;
    let disc = di.base;
    disc -= Math.min(di.tilt_cap, m.tilt_per_100 * di.tilt_coef);
    if (m.parlay_roi < 0) {
        disc -= Math.min(di.parlay_cap, m.parlay_share * Math.min(1, -m.parlay_roi / di.parlay_scale) * di.parlay_coef);
    }
    disc -= Math.min(di.share_excess_cap, Math.max(0, m.parlay_share - di.share_excess_over) * di.share_excess_coef);
    if (m.late_roi < 0 && m.late_n >= di.late_min_n) {
        disc -= di.late_coef * Math.min(1, -m.late_roi / di.late_scale);
    }
    return {
        skill: Math.max(1, Math.min(99, Math.round(skill))),
        discipline: Math.max(1, Math.min(99, Math.round(disc))),
    };
}
exports.sharpAxes = sharpAxes;
/** Rolling 40-bet windows over the journal IN ORDER (import order is
 *  chronological). Week 1 this is a baseline, not a verdict. */
function rollingTrend(rows, window = 40, step = 20) {
    const out = [];
    for (let start = 0; start < Math.max(1, rows.length - window + 1); start += step) {
        const seg = rows.slice(start, start + window);
        if (seg.length < window)
            break;
        const m = mirror(seg);
        const ax = sharpAxes(m);
        out.push({
            through_bet: start + window, skill: ax.skill, discipline: ax.discipline,
            tilt_per_100: m.tilt_per_100, avg_clv_pct: m.avg_clv_pct,
        });
    }
    return out;
}
exports.rollingTrend = rollingTrend;
// ---------- sealing -----------------------------------------------------------
const pct = (x, dp = 0, signed = false) => {
    const v = (x * 100).toFixed(dp);
    return (signed && x >= 0 ? '+' : '') + v + '%';
};
/** The five sealed claims — same sentences the Python prototype seals. */
function reportClaims(m, score, evidenceSource, retrievedAt) {
    const lines = [
        `Across ${m.bets} tracked bets the bettor's average closing line value was ${m.avg_clv_pct >= 0 ? '+' : ''}${m.avg_clv_pct.toFixed(2)} percent.`,
        `The bettor beat the closing price in ${pct(m.beat_close_rate)} of graded bets (95% CI ${pct(m.beat_close_ci[0])} to ${pct(m.beat_close_ci[1])}).`,
        `Parlays were ${pct(m.parlay_share)} of volume and returned ${pct(m.parlay_roi, 1, true)} ROI (95% CI ${pct(m.parlay_roi_ci[0], 1, true)} to ${pct(m.parlay_roi_ci[1], 1, true)}, n=${m.parlay_n}, tier ${m.parlay_tier}).`,
        `Stake-escalation after a loss (tilt) appeared ${m.tilt_events} times, ${m.tilt_per_100.toFixed(0)} per 100 bets.`,
        `The bettor's Sharp Score under rubric v${exports.RUBRIC_VERSION} is ${score} out of 99.`,
    ];
    return lines.map((text, i) => ({
        id: `c${String(i + 1).padStart(3, '0')}`,
        text,
        status: 'verified',
        evidence: [{
                source: evidenceSource, retrieved_at: retrievedAt,
                independence: 'primary', snippet: '', contradicts: false,
            }],
        stale_after_days: null,
        note: '',
    }));
}
exports.reportClaims = reportClaims;
function sealMirrorReport(rows, opts) {
    const m = mirror(rows);
    const score = sharpScoreV11(m);
    // Pinning must COPY the weights, never reference the live object —
    // a caller mutating receipt meta must not corrupt the rubric
    // (the deepcopy bug, round 4 of the prototype; do not regress).
    const weights = JSON.parse(JSON.stringify(exports.WEIGHTS_V11));
    const meta = {
        rubric: {
            name: 'sharp_score', version: exports.RUBRIC_VERSION, weights,
            weights_sha: (0, sha256_1.sha256hex)((0, canon_1.canon)(weights)),
        },
        score,
    };
    return (0, receipt_1.sealReceipt)({
        issuer: 'TrueEdge', subject: 'mirror-report', created_at: opts.created_at,
        claims: reportClaims(m, score, opts.evidenceSource, opts.retrievedAt),
        meta, key: opts.key,
    });
}
exports.sealMirrorReport = sealMirrorReport;
/** Recompute under the PINNED weights. FAILS CLOSED — any missing or
 *  malformed pinning is a named error, never a silent default. */
function verifyScore(rows, receipt) {
    const meta = receipt.meta;
    if (!meta || typeof meta !== 'object' || !Object.keys(meta).length) {
        return { ok: false, msg: 'receipt meta missing — no pinned rubric to verify against' };
    }
    const rub = meta.rubric;
    if (!rub || typeof rub !== 'object') {
        return { ok: false, msg: 'receipt meta.rubric missing or malformed' };
    }
    if (rub.name !== 'sharp_score') {
        return { ok: false, msg: `unexpected rubric name: ${JSON.stringify(rub.name)}` };
    }
    const weights = rub.weights;
    if (!weights || typeof weights !== 'object') {
        return { ok: false, msg: 'pinned weights missing or malformed' };
    }
    const missing = Object.keys(exports.WEIGHTS_V11).filter((k) => !(k in weights));
    if (missing.length) {
        return { ok: false, msg: `pinned weights missing keys: ${missing.join(', ')}` };
    }
    const sealed = meta.score;
    if (typeof sealed !== 'number' || !Number.isInteger(sealed)) {
        return { ok: false, msg: 'sealed score missing or not an integer' };
    }
    const recomputed = sharpScoreV11(mirror(rows), weights);
    if (recomputed !== sealed) {
        return { ok: false, msg: `score mismatch: recomputed ${recomputed} != sealed ${sealed}` };
    }
    const notes = [`score ${sealed} recomputed OK under pinned rubric v${String(rub.version)}`];
    if (rub.weights_sha !== (0, sha256_1.sha256hex)((0, canon_1.canon)(weights))) {
        return { ok: false, msg: 'pinned weights failed their own sha check (meta tampered)' };
    }
    if ((0, sha256_1.sha256hex)((0, canon_1.canon)(weights)) !== (0, sha256_1.sha256hex)((0, canon_1.canon)({ ...exports.WEIGHTS_V11 }))) {
        notes.push('pinned weights differ from the current app rubric (pinned weights govern)');
    }
    return { ok: true, msg: notes.join('; ') };
}
exports.verifyScore = verifyScore;
