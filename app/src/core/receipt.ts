/** Carver Receipt (carver-receipt/v1) — TypeScript port of the Python
 *  package's sealing path: canonical JSON, Merkle root over claim
 *  leaves, receipt_digest binding header+meta+root, HMAC-SHA256 sign.
 *  Byte-compatible: a receipt sealed here verifies with the Python
 *  CLI and the single-file HTML verifier (proven in tests/parity). */
import { canon } from './canon';
import { sha256hex, hmacSha256hex } from './sha256';

export interface Evidence {
  source: string;
  retrieved_at: string;
  independence: string; // primary | independent | vendor
  snippet: string;
  contradicts: boolean;
}

export interface Claim {
  id: string;
  text: string;
  status: 'verified' | 'unverified' | 'contested' | 'stale' | 'opinion';
  evidence: Evidence[];
  stale_after_days: number | null;
  note: string;
}

export interface ReceiptDict {
  issuer: string;
  subject: string;
  created_at: string;
  claims: Claim[];
  meta: Record<string, unknown>;
  format: string;
  merkle_root: string;
  receipt_digest: string;
  mode: 'hmac' | 'detached' | 'ed25519' | 'flagged';
  signature: string;
  public_key: string;
  summary: Record<string, number>;
}

export const FORMAT = 'carver-receipt/v1';

export function merkleRoot(claims: Claim[]): string {
  if (!claims.length) return sha256hex('EMPTY');
  let level = claims.map((c) => sha256hex(canon(c)));
  while (level.length > 1) {
    if (level.length % 2) level.push(level[level.length - 1]);
    const next: string[] = [];
    for (let i = 0; i < level.length; i += 2) next.push(sha256hex(level[i] + level[i + 1]));
    level = next;
  }
  return level[0];
}

export function receiptDigest(d: {
  format?: string; issuer: string; subject: string; created_at: string;
  meta?: Record<string, unknown>;
}, root: string): string {
  return sha256hex(canon({
    format: d.format ?? FORMAT,
    issuer: d.issuer,
    subject: d.subject,
    created_at: d.created_at,
    meta: d.meta ?? {},
    merkle_root: root,
  }));
}

export function summarize(claims: Claim[]): Record<string, number> {
  const counts: Record<string, number> = { total: claims.length };
  for (const c of claims) counts[c.status] = (counts[c.status] ?? 0) + 1;
  return counts;
}

export function sealReceipt(input: {
  issuer: string; subject: string; created_at: string;
  claims: Claim[]; meta?: Record<string, unknown>; key?: string;
}): ReceiptDict {
  const meta = input.meta ?? {};
  const root = merkleRoot(input.claims);
  const digest = receiptDigest({ ...input, meta }, root);
  const mode = input.key ? 'hmac' as const : 'detached' as const;
  return {
    issuer: input.issuer,
    subject: input.subject,
    created_at: input.created_at,
    claims: input.claims,
    meta,
    format: FORMAT,
    merkle_root: root,
    receipt_digest: digest,
    mode,
    signature: input.key ? hmacSha256hex(input.key, digest) : '',
    public_key: '',
    summary: summarize(input.claims),
  };
}

export function verifyReceipt(d: ReceiptDict, key?: string): { ok: boolean; msg: string } {
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
      if (!key) return { ok: false, msg: 'hmac receipt requires the key to verify' };
      if (hmacSha256hex(key, digest) !== d.signature) {
        return { ok: false, msg: 'hmac signature mismatch (wrong key or forged)' };
      }
      return { ok: true, msg: `OK mode=hmac root=${root.slice(0, 12)}...` };
    }
  }
  return { ok: true, msg: `OK mode=${d.mode} root=${root.slice(0, 12)}... (integrity only; no issuer proof)` };
}

/** Share-link codec — identical to the HTML verifier's #r= fragment format.
 *  The receipt rides in the URL fragment; it is never sent to a server. */
export function encodeSharePayload(receiptJson: string): string {
  const bytes = new TextEncoder().encode(receiptJson);
  let bin = '';
  bytes.forEach((b) => { bin += String.fromCharCode(b); });
  return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

export function shareLink(verifierBaseUrl: string, receipt: ReceiptDict): string {
  return verifierBaseUrl.split('#')[0] + '#r=' + encodeSharePayload(JSON.stringify(receipt));
}
