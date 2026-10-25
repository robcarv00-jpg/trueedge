"""Build the simplified TrueEdge icon from the master logo's TE + arrow core.
Master (Robert's): navy esports emblem — silver TE, gold rising arrow,
blue/gold swooshes. Simplified for 29px: same core, nothing else.
Run: python3 build_icon.py  -> app/assets/icon.png (1024) + icon_sizetest.png
"""
from PIL import Image, ImageDraw, ImageFont

S = 1024
NAVY_TOP, NAVY_BOT = (5, 28, 64), (2, 11, 32)
SILVER = [(0.0, (253, 254, 255)), (0.45, (205, 216, 230)),
          (0.55, (240, 244, 249)), (1.0, (169, 184, 204))]
GOLD = [(0.0, (255, 217, 105)), (0.55, (243, 176, 53)), (1.0, (207, 128, 22))]
BLUE, GOLD_SOLID, OUTLINE = (47, 157, 255), (240, 174, 53), (6, 14, 30)
FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf"


def vgrad(stops, h=S):
    img = Image.new("RGB", (1, h))
    px = img.load()
    for y in range(h):
        t = y / (h - 1)
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                f = 0 if t1 == t0 else (t - t0) / (t1 - t0)
                px[0, y] = tuple(round(c0[j] + (c1[j] - c0[j]) * f) for j in range(3))
                break
    return img.resize((S, S))


def text_mask(draw_xy, ch, size):
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    d.text(draw_xy, ch, font=ImageFont.truetype(FONT, size), fill=255)
    return m


def paste_grad(canvas, grad_stops, mask):
    canvas.paste(vgrad(grad_stops), (0, 0), mask)


img = vgrad([(0.0, NAVY_TOP), (1.0, NAVY_BOT)]).convert("RGB")
d = ImageDraw.Draw(img)

# --- ONE blue swoosh under the letters (v1's two arcs fought each other) ---
d.arc((-190, -180, 1214, 940), start=28, end=152, fill=BLUE, width=42)

# --- letters: T tall at left, E lower-right, silver metallic ---
def letter(ch, xy, size):
    mask = text_mask(xy, ch, size)
    edge = Image.new("L", (S, S), 0)
    de = ImageDraw.Draw(edge)
    de.text(xy, ch, font=ImageFont.truetype(FONT, size), fill=255,
            stroke_width=14, stroke_fill=255)
    img.paste(OUTLINE, (0, 0), edge)
    paste_grad(img, SILVER, mask)

# --- gold rising arrow FIRST: letters drawn over its tail (weave) ---
arrow = [(573, 592), (716, 320), (906, 259), (876, 456), (627, 638)]
am = Image.new("L", (S, S), 0)
da = ImageDraw.Draw(am)
da.polygon(arrow, fill=255)
edge = Image.new("L", (S, S), 0)
de = ImageDraw.Draw(edge)
de.line(arrow + [arrow[0]], fill=255, width=26, joint="curve")
img.paste(OUTLINE, (0, 0), edge)
paste_grad(img, GOLD, am)

letter("T", (128, 258), 560)
letter("E", (415, 372), 490)

img.save("app/assets/icon.png")
print("icon.png saved")

# --- size test: master vs simplified ---
master = Image.open("app/assets/logo-master.png").convert("RGBA")
emblem = master.crop((48, 6, 432, 350))
side = max(emblem.size)
sq = Image.new("RGBA", (side, side), (3, 18, 47, 255))
sq.paste(emblem, ((side - emblem.width) // 2, (side - emblem.height) // 2), emblem)
sizes = [180, 60, 40, 29]
W = 2 * (sum(sizes) + 20 * (len(sizes) + 1)) + 30
strip = Image.new("RGB", (W, 300), (16, 17, 19))
ds = ImageDraw.Draw(strip)
for row, (label, source) in enumerate([("MASTER", sq.convert("RGB")),
                                       ("SIMPLIFIED", img)]):
    x, y = 20, 20 + row * 140
    ds.text((x, y - 14), label, fill=(245, 246, 247))
    for s in sizes:
        strip.paste(source.resize((s, s), Image.LANCZOS), (x, y + 8))
        ds.text((x, y + 8 + s + 4 if s < 60 else y + 116), f"{s}", fill=(155, 161, 166))
        x += s + 20
strip.save("icon_sizetest.png")
print("icon_sizetest.png saved")
