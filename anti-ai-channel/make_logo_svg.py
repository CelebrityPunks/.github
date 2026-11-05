#!/usr/bin/env python3
"""Vector ouroboros logo (SVG): a snake eating its own tail.

Front half: smooth body with negative-space scales. Swallowed half: breaks
apart into pixels that get bigger and sparser toward the tail.

Usage: python3 make_logo_svg.py   -> logo/*.svg
"""
import math
import os
import random

VB = 1000
C = VB / 2
R = 300                       # centre line of the body
HEAD_ANGLE = math.radians(-62)
HEAD_SPAN = 0.50              # head length (radians along the ring)
TAIL_IN_MOUTH = 0.40
SWEEP = 2 * math.pi - TAIL_IN_MOUTH
PIXEL_FROM = 0.50

EMBER = "#FF7028"
BG = "#08080A"


def pt(th, r=R):
    return C + r * math.cos(th), C + r * math.sin(th)


def width(s):
    return 72 * (1 - s) ** 0.6 + 42


def f(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def smooth_path(points, closed=True):
    """Catmull-Rom -> cubic Bezier, for perfectly smooth outlines."""
    n = len(points)
    d = [f"M{f(points[0][0])},{f(points[0][1])}"]
    rng_ = range(n if closed else n - 1)
    for i in rng_:
        p0 = points[(i - 1) % n] if closed or i > 0 else points[0]
        p1 = points[i]
        p2 = points[(i + 1) % n]
        p3 = points[(i + 2) % n] if closed or i + 2 < n else points[-1]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append(f"C{f(c1[0])},{f(c1[1])} {f(c2[0])},{f(c2[1])} {f(p2[0])},{f(p2[1])}")
    if closed:
        d.append("Z")
    return "".join(d)


def _curve_through(points):
    """Cubic Bezier commands through points (open Catmull-Rom), no leading M."""
    n = len(points)
    out = []
    for i in range(n - 1):
        p0 = points[max(0, i - 1)]
        p1, p2 = points[i], points[i + 1]
        p3 = points[min(n - 1, i + 2)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        out.append(f"C{f(c1[0])},{f(c1[1])} {f(c2[0])},{f(c2[1])} {f(p2[0])},{f(p2[1])}")
    return "".join(out)


def body_path():
    n = 90
    s_end = PIXEL_FROM + 0.02
    ss = [-0.03 + (s_end + 0.03) * i / n for i in range(n + 1)]
    outer = [pt(HEAD_ANGLE - x * SWEEP, R + width(max(0, x)) / 2) for x in ss]
    inner = [pt(HEAD_ANGLE - x * SWEEP, R - width(max(0, x)) / 2) for x in reversed(ss)]
    return (f"M{f(outer[0][0])},{f(outer[0][1])}" + _curve_through(outer)
            + f"L{f(inner[0][0])},{f(inner[0][1])}" + _curve_through(inner) + "Z")


def head_path():
    def hw(fr):
        return 57 + 25 * math.sin(math.pi * min(1, max(0, fr) / 0.75)) - 20 * max(0, fr - 0.75) / 0.25

    def opening(fr):
        return 0 if fr < 0.52 else ((fr - 0.52) / 0.48) ** 0.9 * hw(fr) * 0.66

    def P(fr, r):
        return pt(HEAD_ANGLE + fr * HEAD_SPAN, r)

    n = 40
    fr_all = [-0.06 + 1.06 * i / n for i in range(n + 1)]
    upper = [P(x, R + hw(x)) for x in fr_all]
    jaw = [x for x in fr_all if x >= 0.52]
    upper_in = [P(x, R + opening(x)) for x in reversed(jaw)]
    lower_in = [P(x, R - opening(x)) for x in jaw]
    lower = [P(x, R - hw(x)) for x in reversed(fr_all)]
    # rounded jaw tips
    def tip(sign):
        a = P(1.0, R + sign * hw(1.0))
        b = P(1.0, R + sign * opening(1.0))
        m = P(1.04, R + sign * (hw(1.0) + opening(1.0)) / 2)
        return [a, m, b]
    pts = upper + tip(1)[1:2] + upper_in + lower_in + tip(-1)[1:2] + lower
    # open curve + straight closing edge at the back of the head (hidden under the neck)
    return f"M{f(pts[0][0])},{f(pts[0][1])}" + _curve_through(pts) + "Z"


def scale_cuts():
    """Chevron scale marks (negative space) along the smooth half."""
    out = []
    for i in range(16):
        s = 0.03 + i * (PIXEL_FROM - 0.06) / 15
        th = HEAD_ANGLE - s * SWEEP
        w = width(s)
        a = pt(th + 0.045, R - w * 0.30)
        b = pt(th, R)
        c = pt(th + 0.045, R + w * 0.30)
        out.append(f"M{f(a[0])},{f(a[1])}Q{f(b[0])},{f(b[1])} {f(c[0])},{f(c[1])}")
    return out


def eye_cuts():
    def P(fr, r):
        return pt(HEAD_ANGLE + fr * HEAD_SPAN, r)
    ex, ey = P(0.36, R + 28)
    brow = [P(0.24 + 0.28 * i / 12, R + 58 - 4 * math.sin(math.pi * i / 12)) for i in range(13)]
    brow_d = "M" + " L".join(f"{f(x)},{f(y)}" for x, y in brow)
    return (ex, ey), brow_d


def pixels():
    """Grid-aligned squares filling the swallowed half, coarser toward the tail."""
    r = random.Random(9)
    tiers = [(PIXEL_FROM - 0.015, 0.70, 15), (0.70, 0.86, 22), (0.86, 1.0, 30)]
    sq = []
    for (s0, s1, g) in tiers:
        for gy in range(int(C - R - 80) // g, int(C + R + 80) // g + 1):
            for gx in range(int(C - R - 80) // g, int(C + R + 80) // g + 1):
                cx, cy = gx * g + g / 2, gy * g + g / 2
                th = math.atan2(cy - C, cx - C)
                rad = math.hypot(cx - C, cy - C)
                s = ((HEAD_ANGLE - th) % (2 * math.pi)) / SWEEP
                if not (s0 <= s < s1) or s > 1:
                    continue
                if abs(rad - R) > width(s) / 2:
                    continue
                k = (s - PIXEL_FROM) / (1 - PIXEL_FROM)
                if r.random() < 0.18 * k:   # dissolving: some pixels missing
                    continue
                size = g * 0.82
                tone = 1.0 if (gx + gy) % 2 else 0.74
                sq.append((cx - size / 2, cy - size / 2, size, tone))
        # a few loose pixels drifting off the edges
    for i in range(14):
        s = PIXEL_FROM + (1 - PIXEL_FROM) * (0.15 + 0.8 * r.random())
        th = HEAD_ANGLE - s * SWEEP
        side = r.choice((-1, 1))
        off = width(s) / 2 + 14 + r.random() * 34
        g = 9 + 10 * r.random()
        x, y = pt(th, R + side * off)
        sq.append((x - g / 2, y - g / 2, g, 0.74 if r.random() < 0.5 else 1.0))
    return sq


def build(fill, bg=None, alt=None):
    """fill: main colour; alt: colour for the darker pixel tone (default: fill @ 74%)."""
    (ex, ey), brow = eye_cuts()
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VB} {VB}" width="{VB}" height="{VB}">',
             '<title>Ouroboros</title>',
             '<defs><mask id="cut" maskUnits="userSpaceOnUse" x="0" y="0" width="1000" height="1000">',
             f'<rect width="{VB}" height="{VB}" fill="#fff"/>',
             '<g fill="none" stroke="#000" stroke-linecap="round" stroke-linejoin="round">']
    parts += [f'<path d="{d}" stroke-width="7"/>' for d in scale_cuts()]
    parts.append(f'<path d="{brow}" stroke-width="6"/>')
    parts.append('</g>')
    parts.append(f'<circle cx="{f(ex)}" cy="{f(ey)}" r="13" fill="#000"/>')
    parts.append('</mask></defs>')
    if bg:
        parts.append(f'<rect width="{VB}" height="{VB}" fill="{bg}"/>')
    # pixels first (the tail goes into the mouth, under the head)
    parts.append(f'<g fill="{fill}">')
    for (x, y, sz, tone) in pixels():
        op = "" if tone == 1.0 else (f' fill="{alt}"' if alt else f' fill-opacity="{tone}"')
        parts.append(f'<rect x="{f(x)}" y="{f(y)}" width="{f(sz)}" height="{f(sz)}" rx="1.5"{op}/>')
    parts.append('</g>')
    parts.append(f'<g fill="{fill}" mask="url(#cut)">')
    parts.append(f'<path d="{body_path()}"/>')
    parts.append(f'<path d="{head_path()}"/>')
    parts.append('</g>')
    # slit pupil inside the eye cut-out
    parts.append(f'<ellipse cx="{f(ex)}" cy="{f(ey)}" rx="3.5" ry="9.5" fill="{fill}" '
                 f'transform="rotate({f(math.degrees(HEAD_ANGLE + 0.18 * HEAD_SPAN))} {f(ex)} {f(ey)})"/>')
    parts.append('</svg>')
    return "\n".join(parts)


def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo")
    os.makedirs(out, exist_ok=True)
    variants = {
        "ouroboros.svg": build(EMBER),
        "ouroboros_on_dark.svg": build(EMBER, bg=BG, alt="#B94A17"),
        "ouroboros_white.svg": build("#FFFFFF", alt="#FFFFFF"),
        "ouroboros_black.svg": build("#000000", alt="#000000"),
    }
    for name, svg in variants.items():
        with open(os.path.join(out, name), "w") as fh:
            fh.write(svg)
    print("wrote", ", ".join(variants))


if __name__ == "__main__":
    main()
