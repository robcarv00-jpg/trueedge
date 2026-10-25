"use strict";
/** Odds math — direct port of sharp_mirror.py (implied, Shin devig, profit, ROI). */
Object.defineProperty(exports, "__esModule", { value: true });
exports.roi = exports.profit = exports.shin = exports.implied = void 0;
function implied(american) {
    return american > 0 ? 100 / (american + 100) : -american / (-american + 100);
}
exports.implied = implied;
/** Shin's method: fair probabilities from a book's implied probabilities. */
function shin(prices) {
    const total = prices.reduce((a, b) => a + b, 0);
    if (total <= 1.0)
        return prices.map((p) => p / total);
    let lo = 0.0, hi = 0.5;
    for (let i = 0; i < 60; i++) {
        const z = (lo + hi) / 2;
        const est = prices.reduce((s, p) => s + Math.sqrt(z * z + (4 * (1 - z) * p * p) / total), 0);
        if (est > 1.0)
            lo = z;
        else
            hi = z;
    }
    const z = (lo + hi) / 2;
    return prices.map((p) => (Math.sqrt(z * z + (4 * (1 - z) * p * p) / total) - z) / (2 * (1 - z)));
}
exports.shin = shin;
function profit(r) {
    const dec = 1 + (r.odds > 0 ? r.odds / 100 : 100 / -r.odds);
    return r.won ? r.stake * (dec - 1) : -r.stake;
}
exports.profit = profit;
function roi(rs) {
    const staked = rs.reduce((s, r) => s + r.stake, 0);
    return staked ? rs.reduce((s, r) => s + profit(r), 0) / staked : 0;
}
exports.roi = roi;
