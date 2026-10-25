"use strict";
/** Canonical JSON — must byte-match Python's
 *  json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=True),
 *  exactly as the HTML verifier implements it (parity-proven there). */
Object.defineProperty(exports, "__esModule", { value: true });
exports.canon = exports.canonStr = void 0;
function canonStr(s) {
    let out = '"';
    for (let i = 0; i < s.length; i++) {
        const c = s.charCodeAt(i);
        if (c === 0x22)
            out += '\\"';
        else if (c === 0x5c)
            out += '\\\\';
        else if (c === 0x08)
            out += '\\b';
        else if (c === 0x0c)
            out += '\\f';
        else if (c === 0x0a)
            out += '\\n';
        else if (c === 0x0d)
            out += '\\r';
        else if (c === 0x09)
            out += '\\t';
        else if (c < 0x20 || c > 0x7e)
            out += '\\u' + c.toString(16).padStart(4, '0');
        else
            out += s[i];
    }
    return out + '"';
}
exports.canonStr = canonStr;
function canon(v) {
    if (v === null || v === undefined)
        return 'null';
    if (typeof v === 'boolean')
        return v ? 'true' : 'false';
    if (typeof v === 'number')
        return String(v);
    if (typeof v === 'string')
        return canonStr(v);
    if (Array.isArray(v))
        return '[' + v.map(canon).join(',') + ']';
    const obj = v;
    const keys = Object.keys(obj).filter((k) => obj[k] !== undefined).sort();
    return '{' + keys.map((k) => canonStr(k) + ':' + canon(obj[k])).join(',') + '}';
}
exports.canon = canon;
