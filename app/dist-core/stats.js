"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.betsToResolve = exports.leakTier = exports.unitsPer100 = exports.bootstrapRoiCI = exports.wilsonCI = exports.round = void 0;
/** CIs + leak tiers — port of sharp_mirror.py.
 *  NOTE: the bootstrap uses a mulberry32 PRNG, not Python's Mersenne
 *  stream, so bootstrap CI endpoints are the same method within
 *  sampling noise of the Python prototype — not bit-identical.
 *  Wilson CIs and every deterministic metric ARE identical. */
const odds_1 = require("./odds");
function round(x, dp) {
    const f = 10 ** dp;
    return Math.round(x * f) / f;
}
exports.round = round;
function wilsonCI(k, n, z = 1.96) {
    if (n === 0)
        return [0, 1];
    const p = k / n;
    const d = 1 + (z * z) / n;
    const c = (p + (z * z) / (2 * n)) / d;
    const h = (z * Math.sqrt((p * (1 - p)) / n + (z * z) / (4 * n * n))) / d;
    return [round(Math.max(0, c - h), 3), round(Math.min(1, c + h), 3)];
}
exports.wilsonCI = wilsonCI;
function mulberry32(seed) {
    let a = seed >>> 0;
    return () => {
        a = (a + 0x6d2b79f5) | 0;
        let t = Math.imul(a ^ (a >>> 15), 1 | a);
        t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
}
function bootstrapRoiCI(rs, iters = 2000, seed = 3) {
    if (rs.length < 5)
        return [0, 0];
    const rng = mulberry32(seed);
    const ests = [];
    for (let i = 0; i < iters; i++) {
        const sample = rs.map(() => rs[Math.floor(rng() * rs.length)]);
        ests.push((0, odds_1.roi)(sample));
    }
    ests.sort((a, b) => a - b);
    return [round(ests[Math.floor(0.025 * iters)], 3), round(ests[Math.floor(0.975 * iters)], 3)];
}
exports.bootstrapRoiCI = bootstrapRoiCI;
function unitsPer100(rs, iters = 2000, seed = 4) {
    if (!rs.length)
        return [0, [0, 0]];
    const vals = rs.map((r) => (0, odds_1.profit)(r) / r.stake);
    const mean = (vals.reduce((a, b) => a + b, 0) / vals.length) * 100;
    if (vals.length < 5)
        return [round(mean, 1), [round(mean, 1), round(mean, 1)]];
    const rng = mulberry32(seed);
    const ests = [];
    for (let i = 0; i < iters; i++) {
        let s = 0;
        for (let j = 0; j < vals.length; j++)
            s += vals[Math.floor(rng() * vals.length)];
        ests.push((s / vals.length) * 100);
    }
    ests.sort((a, b) => a - b);
    return [round(mean, 1),
        [round(ests[Math.floor(0.025 * iters)], 1), round(ests[Math.floor(0.975 * iters)], 1)]];
}
exports.unitsPer100 = unitsPer100;
function leakTier(est, ci, n) {
    if (n < 30)
        return 'inconclusive';
    return ci[0] > 0 || ci[1] < 0 ? 'signal' : 'noise';
}
exports.leakTier = leakTier;
function betsToResolve(est, ci, n) {
    if (est === 0 || leakTier(est, ci, n) !== 'noise')
        return null;
    const half = (ci[1] - ci[0]) / 2;
    return Math.max(1, Math.ceil(n * (half / Math.abs(est)) ** 2) - n);
}
exports.betsToResolve = betsToResolve;
