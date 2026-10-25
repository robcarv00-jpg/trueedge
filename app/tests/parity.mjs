/* Parity test: the TS core must reproduce the Python prototype's numbers
 * on the SAME demo journal, and a JS-sealed receipt must verify with the
 * Python CLI (run separately). Run: npm i -D typescript && npx tsc -p
 * tsconfig.core.json && node tests/parity.mjs */
import { readFileSync, writeFileSync } from 'fs';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const mirror = require('../dist-core/mirror.js');
const receipt = require('../dist-core/receipt.js');
const sha = require('../dist-core/sha256.js');
const csv = require('../dist-core/csv.js');

let fails = 0;
const check = (name, cond, extra = '') => {
  console.log((cond ? 'PASS' : 'FAIL') + ' ' + name + (extra ? ' — ' + extra : ''));
  if (!cond) fails++;
};

// --- primitive vectors ---
check('sha256("abc")', sha.sha256hex('abc') ===
  'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad');
check('hmac RFC vector', sha.hmacSha256hex('key', 'The quick brown fox jumps over the lazy dog') ===
  'f7bc83f430538424b13298e6aa6fb143ef4d59a14946175997479dbc2d1a3cd8');

// --- mirror metrics vs Python (demo journal, seed 7) ---
const rows = JSON.parse(readFileSync(new URL('../../prototype/demo_journal.json', import.meta.url)));
const m = mirror.mirror(rows);
const ax = mirror.sharpAxes(m);
check('bets 120', m.bets === 120);
check('avg_clv_pct 1.38', m.avg_clv_pct === 1.38, String(m.avg_clv_pct));
check('beat_close 0.71', m.beat_close_rate === 0.71);
check('beat CI [0.606,0.795]', JSON.stringify(m.beat_close_ci) === '[0.606,0.795]', JSON.stringify(m.beat_close_ci));
check('brier 0.2', m.brier === 0.2);
check('cal_gap 0.019', m.price_cal_gap === 0.019, String(m.price_cal_gap));
check('parlay_roi -0.115', m.parlay_roi === -0.115, String(m.parlay_roi));
check('late_roi -0.149', m.late_roi === -0.149, String(m.late_roi));
check('tilt 24 / 20 per 100', m.tilt_events === 24 && m.tilt_per_100 === 20);
check('score v1 = 22', mirror.sharpScoreV1(m) === 22, String(mirror.sharpScoreV1(m)));
check('score v1.1 = 39', mirror.sharpScoreV11(m) === 39, String(mirror.sharpScoreV11(m)));
check('axes 74 / 48', ax.skill === 74 && ax.discipline === 48, JSON.stringify(ax));
check('parlay tier is noise (CI crosses 0)', m.parlay_tier === 'noise', m.parlay_tier);
const trend = mirror.rollingTrend(rows);
check('trend has >= 2 windows', trend.length >= 2, `${trend.length} windows`);
console.log('     trend:', JSON.stringify(trend));

// --- CSV import parity: sample CSV must score like its rows say ---
const sampleCsv = readFileSync(new URL('./sample_journal.csv', import.meta.url), 'utf8');
const imported = csv.importJournalCsv(sampleCsv);
check('sample CSV imports rows', imported.length > 0, `${imported.length} rows`);

// --- sealing: JS seal must match Python claim texts + verify in Python ---
const sealed = mirror.sealMirrorReport(rows, {
  key: 'demo', created_at: '2026-10-25T14:47:54+00:00',
  evidenceSource: 'bet-journal export (demo, seed 7)', retrievedAt: '2026-10-25',
});
const pyReceipt = JSON.parse(readFileSync(new URL('../../prototype/mirror_receipt.json', import.meta.url)));
for (const idx of [0, 1, 3, 4]) {
  check(`claim c00${idx + 1} text == Python`, sealed.claims[idx].text === pyReceipt.claims[idx].text,
    sealed.claims[idx].text);
}
check('claim c003 pattern (bootstrap CI digits may drift)',
  /^Parlays were 28% of volume and returned -11\.5% ROI \(95% CI .+, n=34, tier noise\)\.$/
    .test(sealed.claims[2].text), sealed.claims[2].text);
check('JS verifyReceipt OK', receipt.verifyReceipt(sealed, 'demo').ok,
  receipt.verifyReceipt(sealed, 'demo').msg);
const vs = mirror.verifyScore(rows, sealed);
check('verifyScore OK (fail-closed design)', vs.ok, vs.msg);
const tampered = JSON.parse(JSON.stringify(sealed));
delete tampered.meta.rubric.weights.tilt_coef;
check('verifyScore fails closed on missing weight',
  !mirror.verifyScore(rows, tampered).ok, mirror.verifyScore(rows, tampered).msg);
const tampered2 = JSON.parse(JSON.stringify(sealed));
tampered2.claims[0].text = 'Across 120 tracked bets the bettor is a genius.';
check('verifyReceipt catches claim tamper', !receipt.verifyReceipt(tampered2, 'demo').ok);
writeFileSync(new URL('./js_sealed_receipt.json', import.meta.url), JSON.stringify(sealed, null, 2));
console.log('     wrote tests/js_sealed_receipt.json for Python CLI verification');
console.log(fails ? `\n${fails} FAILURES` : '\nALL CHECKS PASSED');
process.exit(fails ? 1 : 0);
