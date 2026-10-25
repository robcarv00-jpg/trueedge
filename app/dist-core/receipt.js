"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.shareLink = exports.encodeSharePayload = exports.verifyReceipt = exports.sealReceipt = exports.summarize = exports.receiptDigest = exports.merkleRoot = exports.FORMAT = void 0;
/** Carver Receipt (carver-receipt/v1) — TypeScript port of the Python
 *  package's sealing path: canonical JSON, Merkle root over claim
 *  leaves, receipt_digest binding header+meta+root, HMAC-SHA256 sign.
 *  Byte-compatible: a receipt sealed here verifies with the Python
 *  CLI and the single-file HTML verifier (proven in tests/parity). */
const canon_1 = require("./canon");
const sha256_1 = require("./sha256");
exports.FORMAT = 'carver-receipt/v1';
function merkleRoot(claims) {
    if (!claims.length)
        return (0, sha256_1.sha256hex)('EMPTY');
    let level = claims.map((c) => (0, sha256_1.sha256hex)((0, canon_1.canon)(c)));
    while (level.length > 1) {
        if (level.length % 2)
            level.push(level[level.length - 1]);
        const next = [];
        for (let i = 0; i < level.length; i += 2)
            next.push((0, sha256_1.sha256hex)(level[i] + level[i + 1]));
        level = next;
    }
    return level[0];
}
exports.merkleRoot = merkleRoot;
function receiptDigest(d, root) {
    return (0, sha256_1.sha256hex)((0, canon_1.canon)({
        format: d.format ?? exports.FORMAT,
        issuer: d.issuer,
        subject: d.subject,
        created_at: d.created_at,
        meta: d.meta ?? {},
        merkle_root: root,
    }));
}
exports.receiptDigest = receiptDigest;
function summarize(claims) {
    const counts = { total: claims.length };
    for (const c of claims)
        counts[c.status] = (counts[c.status] ?? 0) + 1;
    return counts;
}
exports.summarize = summarize;
function sealReceipt(input) {
    const meta = input.meta ?? {};
    const root = merkleRoot(input.claims);
    const digest = receiptDigest({ ...input, meta }, root);
    const mode = input.key ? 'hmac' : 'detached';
    return {
        issuer: input.issuer,
        subject: input.subject,
        created_at: input.created_at,
        claims: input.claims,
        meta,
        format: exports.FORMAT,
        merkle_root: root,
        receipt_digest: digest,
        mode,
        signature: input.key ? (0, sha256_1.hmacSha256hex)(input.key, digest) : '',
        public_key: '',
        summary: summarize(input.claims),
    };
}
exports.sealReceipt = sealReceipt;
function verifyReceipt(d, key) {
    const root = merkleRoot(d.claims);
    if (root !== d.merkle_root) {
        return { ok: false, msg: `merkle mismatch: recomputed ${root.slice(0, 12)}... != sealed ${d.merkle_root.slice(0, 12)}... (receipt was tampered with)` };
    }
    if (d.receipt_digest) {
        const digest = receiptDigest(d, root);
        if (digest !== d.receipt_digest) {
            return { ok: false, msg: 'receipt digest mismatch (header, meta, or root was tampered with)' };
        }
        if (d.mode === 'hmac') {
            if (!key)
                return { ok: false, msg: 'hmac receipt requires the key to verify' };
            if ((0, sha256_1.hmacSha256hex)(key, digest) !== d.signature) {
                return { ok: false, msg: 'hmac signature mismatch (wrong key or forged)' };
            }
            return { ok: true, msg: `OK mode=hmac root=${root.slice(0, 12)}...` };
        }
    }
    return { ok: true, msg: `OK mode=${d.mode} root=${root.slice(0, 12)}... (integrity only; no issuer proof)` };
}
exports.verifyReceipt = verifyReceipt;
/** Share-link codec — identical to the HTML verifier's #r= fragment format.
 *  The receipt rides in the URL fragment; it is never sent to a server. */
function encodeSharePayload(receiptJson) {
    const bytes = new TextEncoder().encode(receiptJson);
    let bin = '';
    bytes.forEach((b) => { bin += String.fromCharCode(b); });
    return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
exports.encodeSharePayload = encodeSharePayload;
function shareLink(verifierBaseUrl, receipt) {
    return verifierBaseUrl.split('#')[0] + '#r=' + encodeSharePayload(JSON.stringify(receipt));
}
exports.shareLink = shareLink;
