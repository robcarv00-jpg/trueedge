# design_audit.py — run: python3 design_audit.py
"""Computable parts of design. Stdlib only.

What this does: contrast, type scale, palette constraints, touch targets,
icon stroke check, name scoring.

What this does NOT do: tell you the design looks good.
"""
import math


# ---------- 1. WCAG contrast (real math) ----------

def _lin(c: float) -> float:
    c /= 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

def luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)

def contrast(fg: str, bg: str) -> float:
    l1, l2 = sorted([luminance(fg), luminance(bg)], reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)

def wcag_pass(ratio: float, large: bool = False) -> str:
    """AA large needs 3:1, AA normal 4.5:1, AAA normal 7:1."""
    if ratio >= 7: return "AAA"
    if ratio >= 4.5 or (large and ratio >= 3): return "AA"
    if large and ratio >= 3: return "AA large"
    return "FAIL"


# ---------- 2. Type scale ----------

def type_scale(base: float = 15, ratio: float = 1.25, steps: int = 8) -> list[float]:
    """Modular scale. Apple's iOS scale is close to ratio 1.20 — start there."""
    return [round(base * (ratio ** i), 1) for i in range(steps)]


# ---------- 3. Palette with constraints ----------

PALETTE = {
    "bg":          "#0A0A0B",   # near-black, not pure (pure black is harsh on OLED)
    "surface":     "#141517",
    "border":      "#26282C",
    "text":        "#F5F6F7",
    "text_muted":  "#9BA1A6",
    "text_faint":  "#6B7075",
    "accent":      "#E8B048",   # amber — caution, terminal, NOT casino-green
    "success":     "#4ADE80",   # verified only
    "danger":      "#F87171",   # leaks only
}

def audit_palette(pal: dict) -> None:
    pairs = [
        ("text", "bg"), ("text", "surface"), ("text_muted", "bg"),
        ("text_muted", "surface"), ("text_faint", "surface"),
        ("accent", "bg"), ("success", "bg"), ("danger", "bg"),
    ]
    print(f"  {'foreground':14} {'background':10} {'ratio':>6} {'verdict':>10}")
    for fg, bg in pairs:
        r = contrast(pal[fg], pal[bg])
        print(f"  {fg:14} {bg:10} {r:>6.2f} {wcag_pass(r):>10}")


# ---------- 4. Touch targets ----------

APPLE_MIN = 44  # points
MATERIAL_MIN = 48  # dp

def check_targets(spec: dict[str, int]) -> None:
    print(f"  {'element':18} {'size':>5} {'apple':>7} {'material':>9}")
    for name, px in spec.items():
        a = "PASS" if px >= APPLE_MIN else "FAIL"
        m = "PASS" if px >= MATERIAL_MIN else "FAIL"
        print(f"  {name:18} {px:>5} {a:>7} {m:>9}")


# ---------- 5. Icon legibility at real sizes ----------

def icon_legibility(stroke_px: float, sizes: list[int]) -> None:
    """Apple icon grid: 1024 base, displayed at 29–60px. Stroke < 1px at 29 = mush."""
    print(f"  rendered size  stroke  verdict")
    for s in sizes:
        rendered = stroke_px * s / 1024
        v = "clean" if rendered >= 1.5 else ("ok" if rendered >= 1.0 else "mush")
        print(f"  {s:>12}px  {rendered:>5.2f}px  {v}")


# ---------- 6. Name scoring ----------

def _syllables_word(w: str) -> int:
    import re
    w = w.lower()
    groups = list(re.finditer(r"[aeiouy]+", w))
    count = len(groups)
    if w.endswith("e") and count > 1:
        count -= 1                       # trailing silent e: "line" -> 1
    for i, g in enumerate(groups):
        # Mid-word silent e: the "e" in "base-line" — a lone "e" group
        # between consonants with another vowel group after it.
        if g.group() == "e" and 0 < i < len(groups) - 1:
            before = w[g.start() - 1]
            after = w[g.end()] if g.end() < len(w) else ""
            if before not in "aeiouy" and after and after not in "aeiouy":
                count -= 1
    return max(1, count)

def syllables(word: str) -> int:
    # Split CamelCase and spaces first: "TrueEdge" -> True + Edge.
    # The naive single-pass counter merged vowel runs across the seam
    # and scored TrueEdge as 1 syllable and Baseline as 3 (both wrong).
    import re
    parts = re.findall(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+", word)
    return sum(_syllables_word(p) for p in parts) if parts else _syllables_word(word)

def name_score(name: str) -> dict:
    s = syllables(name)
    # keyboard distance (typing friction)
    home = set("asdfghjkl")
    home_hits = sum(1 for c in name.lower() if c in home)
    home_ratio = home_hits / max(1, len(name.replace(" ", "")))
    # syllable scoring: 2 is ideal, 3 ok, 1 too short, 4+ too long
    syl_pts = {1: 5, 2: 10, 3: 7, 4: 3}.get(s, 0)
    typability = round(home_ratio * 10, 1)
    return {"name": name, "syllables": s, "syl_score": syl_pts,
            "home_key_ratio": typability,
            "total_heuristic": round((syl_pts + typability) / 2, 1)}


# ---------- report ----------

def report() -> None:
    print("=" * 66)
    print("PALETTE — WCAG contrast on the proposed dark theme")
    print("=" * 66)
    audit_palette(PALETTE)

    print("\n" + "=" * 66)
    print("TYPE SCALE — base 15, ratio 1.25 (Apple-ish)")
    print("=" * 66)
    for i, size in enumerate(type_scale()):
        label = ["caption", "footnote", "body-sm", "body",
                 "body-lg", "title-3", "title-2", "title-1"][i]
        print(f"  {label:10} {size:>5}pt")

    print("\n" + "=" * 66)
    print("TOUCH TARGETS — Apple 44pt, Material 48dp")
    print("=" * 66)
    check_targets({"primary_button": 52, "tab_bar_item": 49,
                   "inline_link": 20, "close_x": 40, "score_badge": 44})

    print("\n" + "=" * 66)
    print("ICON — 'mirror mark': a 12px stroke at 1024 base")
    print("=" * 66)
    icon_legibility(12, [29, 40, 60, 76, 1024])

    print("\n" + "=" * 66)
    print("NAMES — heuristic scoring (NOT a real test)")
    print("=" * 66)
    for n in ["Trueline", "Sharp Mirror", "TrueEdge", "Baseline",
              "Gauge", "Verity", "Carver"]:
        r = name_score(n)
        print(f"  {n:14} syll={r['syllables']}  "
              f"syl={r['syl_score']:>2}/10  home={r['home_key_ratio']:>4}/10  "
              f"total={r['total_heuristic']}")


if __name__ == "__main__":
    report()
