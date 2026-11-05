#!/usr/bin/env python3
"""AINTIA brand kit: vector ouroboros mark, wordmark, lockups, icons, banner.

All output is pure SVG with text converted to outlines (no font needed to view).
Usage: python3 make_brand.py   ->  brand/logo, brand/icons, brand/banner
Then:  node export_brand.js     ->  PNG exports + brand sheet preview
"""
import math
import os

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ palette
WHITE = "#FFFFFF"      # primary
BLACK = "#0D0D0D"      # background
SURFACE = "#2F2F2F"    # surface
SAGE = "#747F67"       # accent (as shown on the brand sheet swatch)
CREAM = "#F2EFE8"      # light icon background

# ------------------------------------------------------------------ helpers
def f(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s == "-0" else s


def catmull(points, closed=False, samples=10):
    """Densify a polyline with Catmull-Rom so it maps smoothly through polar space."""
    n = len(points)
    out = []
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = points[(i - 1) % n] if closed else points[max(0, i - 1)]
        p1 = points[i % n]
        p2 = points[(i + 1) % n]
        p3 = points[(i + 2) % n] if closed else points[min(n - 1, i + 2)]
        for k in range(samples):
            t = k / samples
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t
                                    + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    if not closed:
        out.append(points[-1])
    return out


def poly_d(pts, close=True):
    d = f"M{f(pts[0][0])},{f(pts[0][1])}" + "".join(f"L{f(x)},{f(y)}" for x, y in pts[1:])
    return d + ("Z" if close else "")


# ------------------------------------------------------------------ the mark
# Drawn in a 1000x1000 box. The ring is a circle; the head lies along the top
# of the ring facing right, and the tapering tail slides into its mouth.
C = 500.0
R = 268.0          # ring centre line
W = 66.0           # body thickness
HEAD_AT = math.radians(-108)     # where the head's local x=0 sits on the ring


def polar(th, r):
    return C + r * math.cos(th), C + r * math.sin(th)


def head_local_to_xy(x, y):
    # local x runs along the ring (toward the snout), local y outward from the centre line
    return polar(HEAD_AT + x / R, R + y)


HEAD_PROFILE = [  # (along, out) — clockwise outline of the head silhouette
    (-64, 33), (-32, 35), (-2, 45), (40, 55), (92, 59), (138, 54), (178, 43),
    (208, 31), (228, 19), (236, 10), (231, 3), (217, 0),          # snout
    (200, -4), (178, -11), (150, -21), (116, -32), (80, -38), (40, -39),
    (0, -37), (-34, -35), (-64, -35),
]
TAIL_TIP_X = 206                 # tail tip ends inside the jaw, at this head-local x


def head_outline():
    pts = catmull(HEAD_PROFILE, closed=True, samples=12)
    return [head_local_to_xy(x, y) for x, y in pts]


def body_outline():
    th0 = HEAD_AT - 70 / R                      # body starts under the back of the head
    th_end = HEAD_AT + TAIL_TIP_X / R - 2 * math.pi
    taper_from = th_end + math.radians(58)
    n = 360
    outer, inner = [], []
    for i in range(n + 1):
        th = th0 + (th_end - th0) * i / n
        if th < taper_from:
            t = (taper_from - th) / (taper_from - th_end)
            e = t * t * (3 - 2 * t)                 # smooth start of the taper (no kink)
            w = W * (1 - e) * (1 - 0.15 * e) + 3 * e * (1 - t)
            shift = -5 * e                          # tail tucks slightly inward
        else:
            w, shift = W, 0
        outer.append(polar(th, R + shift + w / 2))
        inner.append(polar(th, R + shift - w / 2))
    return outer + inner[::-1]


def eye_outline():
    cx, cy, L, H, tilt = 142, 36, 16, 6, -0.2
    pts = []
    for i in range(48):
        a = 2 * math.pi * i / 48
        x = L * math.cos(a)
        y = H * math.sin(a) * (1 - 0.35 * math.cos(a))   # sharper at the front
        xr = x * math.cos(tilt) - y * math.sin(tilt)
        yr = x * math.sin(tilt) + y * math.cos(tilt)
        pts.append(head_local_to_xy(cx + xr, cy + yr))
    return pts


def mouth_line():
    pts = catmull([(234, 8), (210, 5), (184, 1), (162, -5)], samples=8)
    return [head_local_to_xy(x, y) for x, y in pts]


def mark_group(fill, uid):
    """Returns (defs, body) SVG strings for the mark in a 1000x1000 box."""
    head = poly_d(head_outline())
    defs = (
        f'<mask id="b{uid}" maskUnits="userSpaceOnUse" x="0" y="0" width="1000" height="1000">'
        f'<rect width="1000" height="1000" fill="#fff"/>'
        # keyline: the body stops a hair short of the head, so the head reads as on top
        f'<path d="{head}" fill="#000" stroke="#000" stroke-width="16" stroke-linejoin="round"/>'
        f'</mask>'
        f'<mask id="h{uid}" maskUnits="userSpaceOnUse" x="0" y="0" width="1000" height="1000">'
        f'<rect width="1000" height="1000" fill="#fff"/>'
        f'<path d="{poly_d(eye_outline())}" fill="#000"/>'
        f'<path d="{poly_d(mouth_line(), close=False)}" fill="none" stroke="#000" '
        f'stroke-width="5" stroke-linecap="round"/>'
        f'</mask>'
    )
    body = (
        f'<path d="{poly_d(body_outline())}" fill="{fill}" mask="url(#b{uid})"/>'
        f'<path d="{head}" fill="{fill}" mask="url(#h{uid})"/>'
    )
    return defs, body


# Bounding box of the mark artwork inside the 1000 box (for tight layouts)
def mark_bbox():
    pts = head_outline() + body_outline()
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


# ------------------------------------------------------------------ type
_fonts = {}


def font(weight):
    if weight not in _fonts:
        _fonts[weight] = TTFont(os.path.join(HERE, "fonts", f"Montserrat-{weight}.ttf"))
    return _fonts[weight]


def text_path(text, size, tracking=0.0, weight="500"):
    """Text -> outlined SVG path. Returns (d, width, cap_height). Baseline at y=0."""
    ft = font(weight)
    gs = ft.getGlyphSet()
    cmap = ft.getBestCmap()
    upm = ft["head"].unitsPerEm
    sc = size / upm
    cap = ft["OS/2"].sCapHeight * sc
    pen = SVGPathPen(gs)
    x = 0.0
    names = [cmap[ord(ch)] for ch in text]
    for i, name in enumerate(names):
        tp = TransformPen(pen, (sc, 0, 0, -sc, x, 0))
        gs[name].draw(tp)
        x += gs[name].width * sc
        if i < len(names) - 1:
            x += tracking * size
    return pen.getCommands(), x, cap


# ------------------------------------------------------------------ documents
def svg_doc(w, h, inner, defs="", title="AINTIA"):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {f(w)} {f(h)}" '
            f'width="{f(w)}" height="{f(h)}"><title>{title}</title>'
            f'<defs>{defs}</defs>{inner}</svg>\n')


def place_mark(fill, uid, x, y, size):
    """Place the mark so its artwork bbox fits a square of `size` at (x, y)."""
    x0, y0, x1, y1 = mark_bbox()
    s = size / max(x1 - x0, y1 - y0)
    ox = x + (size - (x1 - x0) * s) / 2 - x0 * s
    oy = y + (size - (y1 - y0) * s) / 2 - y0 * s
    d, b = mark_group(fill, uid)
    return d, f'<g transform="translate({f(ox)} {f(oy)}) scale({f(s)})">{b}</g>'


def text_at(text, size, tracking, weight, fill, cx, baseline, anchor="middle"):
    d, w, cap = text_path(text, size, tracking, weight)
    x = cx - w / 2 if anchor == "middle" else cx
    return f'<path d="{d}" fill="{fill}" transform="translate({f(x)} {f(baseline)})"/>', w, cap


def tagline(fill, cx, baseline, size, line_len, gap):
    t, w, cap = text_at("AUTOMATED BY AI", size, 0.42, "500", fill, cx, baseline)
    mid = baseline - cap / 2
    sw = max(1.0, size * 0.07)
    lines = (f'<path d="M{f(cx - w / 2 - gap - line_len)},{f(mid)}H{f(cx - w / 2 - gap)}'
             f'M{f(cx + w / 2 + gap)},{f(mid)}H{f(cx + w / 2 + gap + line_len)}" '
             f'stroke="{fill}" stroke-width="{f(sw)}" stroke-linecap="round"/>')
    return t + lines


def primary_lockup(fg, bg=None):
    Wd, Hd = 1200, 1200
    defs, mark = place_mark(fg, "p", 375, 150, 450)
    word, _, _ = text_at("AINTIA", 150, 0.32, "500", fg, Wd / 2, 840)
    tag = tagline(fg, Wd / 2, 940, 40, 90, 34)
    back = f'<rect width="{Wd}" height="{Hd}" fill="{bg}"/>' if bg else ""
    return svg_doc(Wd, Hd, back + mark + word + tag, defs)


def horizontal_lockup(fg, bg=None):
    Wd, Hd = 2000, 600
    defs, mark = place_mark(fg, "x", 150, 150, 300)
    div = f'<path d="M560,165V435" stroke="{fg}" stroke-width="5" stroke-linecap="round"/>'
    word, w, cap = text_at("AINTIA", 150, 0.32, "500", fg, 650, 345, anchor="start")
    tag, tw, _ = text_at("AUTOMATED BY AI", 42, 0.5, "500", fg, 654, 440, anchor="start")
    back = f'<rect width="{Wd}" height="{Hd}" fill="{bg}"/>' if bg else ""
    return svg_doc(Wd, Hd, back + mark + div + word + tag, defs)


def wordmark(fg, bg=None):
    d, w, cap = text_path("AINTIA", 200, 0.32, "500")
    pad = 60
    Wd, Hd = w + 2 * pad, cap + 2 * pad
    back = f'<rect width="{f(Wd)}" height="{f(Hd)}" fill="{bg}"/>' if bg else ""
    return svg_doc(Wd, Hd, back + f'<path d="{d}" fill="{fg}" transform="translate({pad} {f(pad + cap)})"/>')


def mark_only(fg, bg=None, size=1000, pad=0.12):
    defs, mark = place_mark(fg, "m", size * pad, size * pad, size * (1 - 2 * pad))
    back = f'<rect width="{size}" height="{size}" fill="{bg}"/>' if bg else ""
    return svg_doc(size, size, back + mark, defs)


def app_icon(bg, fg, shade=None, uid="i"):
    S = 1024
    grad = ""
    fillbg = bg
    if shade:
        grad = (f'<linearGradient id="g{uid}" x1="0" y1="0" x2="0" y2="1">'
                f'<stop offset="0" stop-color="{shade[0]}"/><stop offset="1" stop-color="{shade[1]}"/>'
                f'</linearGradient>')
        fillbg = f"url(#g{uid})"
    defs, mark = place_mark(fg, uid, 222, 222, 580)
    return svg_doc(S, S, f'<rect width="{S}" height="{S}" rx="230" fill="{fillbg}"/>' + mark, grad + defs)


def youtube_banner():
    """2560x1440 channel art. Everything important sits in the 1546x423 safe area."""
    Wd, Hd = 2560, 1440
    defs = """
<radialGradient id="sky" cx="0.5" cy="0.62" r="0.75">
  <stop offset="0" stop-color="#1A1A1A"/><stop offset="0.55" stop-color="#0D0D0D"/><stop offset="1" stop-color="#050505"/>
</radialGradient>
<radialGradient id="planet" cx="0.38" cy="0.22" r="0.95">
  <stop offset="0" stop-color="#3A3A3A"/><stop offset="0.45" stop-color="#1C1C1C"/><stop offset="1" stop-color="#080808"/>
</radialGradient>
<linearGradient id="rim" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#FFFFFF" stop-opacity="0.55"/><stop offset="0.35" stop-color="#FFFFFF" stop-opacity="0.12"/><stop offset="0.6" stop-color="#FFFFFF" stop-opacity="0"/>
</linearGradient>
<linearGradient id="d1" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3A3A3A"/><stop offset="1" stop-color="#0A0A0A"/></linearGradient>
<linearGradient id="d2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#262626"/><stop offset="1" stop-color="#070707"/></linearGradient>
<linearGradient id="d3" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#171717"/><stop offset="1" stop-color="#040404"/></linearGradient>
<linearGradient id="fadeX" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.3" stop-color="#fff" stop-opacity="1"/>
  <stop offset="0.7" stop-color="#fff" stop-opacity="1"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
</linearGradient>
<filter id="soft"><feGaussianBlur stdDeviation="2.2"/></filter>
<filter id="grain" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="4"/>
  <feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.05 0"/>
</filter>"""
    # dunes: smooth layered ridges across the bottom
    def ridge(y0, amp, phase, freq, fill, hi):
        pts = []
        for i in range(0, 65):
            x = i * Wd / 64
            y = y0 - amp * (0.55 * math.sin(x / Wd * math.pi * freq + phase)
                            + 0.3 * math.sin(x / Wd * math.pi * freq * 2.3 + phase * 1.7)
                            + 0.15 * math.sin(x / Wd * math.pi * freq * 5.1 + phase * 0.4))
            pts.append((x, y))
        top = catmull(pts, samples=4)
        d = poly_d(top + [(Wd, Hd), (0, Hd)])
        edge = poly_d(top, close=False)
        return (f'<path d="{d}" fill="{fill}"/>'
                f'<path d="{edge}" fill="none" stroke="#FFFFFF" stroke-opacity="{hi}" stroke-width="2.5" filter="url(#soft)"/>')

    planet = ('<circle cx="1280" cy="1180" r="640" fill="url(#planet)"/>'
              '<circle cx="1280" cy="1180" r="640" fill="none" stroke="url(#rim)" stroke-width="5"/>')
    stars = []
    import random
    rr = random.Random(21)
    for _ in range(160):
        x, y = rr.uniform(0, Wd), rr.uniform(0, 820)
        stars.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(rr.uniform(0.6, 1.8))}" fill="#fff" '
                     f'fill-opacity="{f(rr.uniform(0.08, 0.45))}"/>')
    land = (ridge(1080, 70, 0.4, 2.1, "url(#d3)", 0.10) + ridge(1170, 90, 2.0, 1.6, "url(#d2)", 0.16)
            + ridge(1290, 70, 4.1, 2.6, "url(#d1)", 0.22))
    mdefs, mark = place_mark(WHITE, "y", 1280 - 110, 520, 220)
    word, _, _ = text_at("AINTIA", 120, 0.32, "500", WHITE, 1280, 870)
    tag = tagline(WHITE, 1280, 930, 30, 70, 26)
    inner = (f'<rect width="{Wd}" height="{Hd}" fill="url(#sky)"/>' + "".join(stars) + planet + land
             + mark + word + tag)
    return svg_doc(Wd, Hd, inner, defs + mdefs, "AINTIA YouTube banner")


def main():
    files = {
        "logo/aintia_mark_white.svg": mark_only(WHITE),
        "logo/aintia_mark_black.svg": mark_only(BLACK),
        "logo/aintia_mark_sage.svg": mark_only(SAGE),
        "logo/aintia_primary_white.svg": primary_lockup(WHITE),
        "logo/aintia_primary_on_dark.svg": primary_lockup(WHITE, BLACK),
        "logo/aintia_primary_black.svg": primary_lockup(BLACK),
        "logo/aintia_horizontal_white.svg": horizontal_lockup(WHITE),
        "logo/aintia_horizontal_black.svg": horizontal_lockup(BLACK),
        "logo/aintia_wordmark_white.svg": wordmark(WHITE),
        "logo/aintia_wordmark_black.svg": wordmark(BLACK),
        "icons/aintia_icon_dark.svg": app_icon(BLACK, WHITE, shade=("#1E1E1E", "#0D0D0D"), uid="id"),
        "icons/aintia_icon_cream.svg": app_icon(CREAM, BLACK, uid="ic"),
        "icons/aintia_icon_sage.svg": app_icon(SAGE, CREAM, shade=("#808B73", "#6A745E"), uid="is"),
        "banner/aintia_youtube_banner.svg": youtube_banner(),
    }
    for rel, svg in files.items():
        p = os.path.join(HERE, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as fh:
            fh.write(svg)
    print(f"wrote {len(files)} SVGs")


if __name__ == "__main__":
    main()
