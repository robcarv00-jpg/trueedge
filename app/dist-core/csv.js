"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.importJournalCsv = exports.parseCsv = void 0;
const ALIASES = {
    market: ['market', 'bet_type', 'type', 'bet type'],
    odds: ['odds', 'price', 'odds taken', 'bet odds'],
    stake: ['stake', 'wager', 'amount', 'risk'],
    result: ['result', 'outcome', 'status', 'won'],
    close: ['closing_odds', 'close', 'closing odds', 'closing line odds'],
    close_other: ['closing_odds_other', 'close_other', 'opponent closing odds'],
    mins: ['mins_before', 'minutes_before', 'minutes before', 'mins', 'minutes before start'],
    sport: ['sport', 'league'],
    placed_at: ['placed_at', 'placed at', 'date placed', 'bet date', 'date', 'timestamp'],
};
const WON = new Set(['win', 'won', 'w', 'true', '1', 'yes', 'cash']);
const LOST = new Set(['loss', 'lost', 'lose', 'l', 'false', '0', 'no']);
function parseCsv(text) {
    const rows = [];
    let row = [], cell = '', quoted = false;
    for (let i = 0; i < text.length; i++) {
        const ch = text[i];
        if (quoted) {
            if (ch === '"') {
                if (text[i + 1] === '"') {
                    cell += '"';
                    i++;
                }
                else
                    quoted = false;
            }
            else
                cell += ch;
        }
        else if (ch === '"')
            quoted = true;
        else if (ch === ',') {
            row.push(cell);
            cell = '';
        }
        else if (ch === '\n' || ch === '\r') {
            if (ch === '\r' && text[i + 1] === '\n')
                i++;
            row.push(cell);
            cell = '';
            if (row.some((c) => c.trim() !== ''))
                rows.push(row);
            row = [];
        }
        else
            cell += ch;
    }
    row.push(cell);
    if (row.some((c) => c.trim() !== ''))
        rows.push(row);
    if (!rows.length)
        return [];
    const headers = rows[0].map((h) => h.trim());
    return rows.slice(1).map((r) => {
        const o = {};
        headers.forEach((h, i) => { o[h] = (r[i] ?? '').trim(); });
        return o;
    });
}
exports.parseCsv = parseCsv;
function col(headers, key) {
    const low = new Map(headers.map((h) => [h.trim().toLowerCase(), h]));
    for (const alias of ALIASES[key])
        if (low.has(alias))
            return low.get(alias);
    return null;
}
function importJournalCsv(text) {
    const records = parseCsv(text);
    if (!records.length)
        throw new Error('CSV has no data rows');
    const headers = Object.keys(records[0]);
    const cols = {};
    for (const k of Object.keys(ALIASES))
        cols[k] = col(headers, k);
    const missing = ['market', 'odds', 'stake', 'result', 'close'].filter((k) => !cols[k]);
    if (missing.length)
        throw new Error(`CSV is missing required columns: ${missing.join(', ')}`);
    const out = [];
    for (const raw of records) {
        const res = (raw[cols.result] ?? '').toLowerCase();
        if (!WON.has(res) && !LOST.has(res))
            continue; // pushes/pending: not graded
        const close = Math.trunc(Number(raw[cols.close]));
        // Documented approximation: single closing price -> mirrored other side.
        const other = cols.close_other
            ? Math.trunc(Number(raw[cols.close_other]))
            : close < 0 ? -close : 100;
        const row = {
            market: (raw[cols.market] ?? '').toLowerCase(),
            odds: Math.trunc(Number(raw[cols.odds])),
            stake: Number(raw[cols.stake]),
            mins: cols.mins ? Math.trunc(Number(raw[cols.mins])) : 180,
            close: [close, other],
            won: WON.has(res),
        };
        if (cols.sport && raw[cols.sport])
            row.sport = raw[cols.sport].toLowerCase();
        if (cols.placed_at && raw[cols.placed_at]) {
            row.placed_at = raw[cols.placed_at];
            const d = new Date(raw[cols.placed_at]);
            if (!Number.isNaN(d.getTime())) {
                row.hour = d.getHours();
                row.dow = d.getDay();
            }
        }
        out.push(row);
    }
    return out;
}
exports.importJournalCsv = importJournalCsv;
