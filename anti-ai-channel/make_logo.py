#!/usr/bin/env python3
"""Draw the channel logo: an ouroboros (a snake eating its own tail).

The front of the snake is smooth and alive; the part being swallowed breaks
down into pixels. Read it however you like.

Usage: python3 make_logo.py   ->  logo/ (transparent PNG, dark avatar, banner mark)
"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter

S = 2048                      # supersampled canvas
C = S / 2
R = 640                       # radius of the body's centre line
EMBER = (255, 112, 40)
EMBER_DARK = (150, 52, 14)
BONE = (240, 238, 232)
BG = (8, 8, 9)

HEAD_ANGLE = math.radians(-62)   # where the neck meets the head (top right)
HEAD_SPAN = 0.50                 # head length, in radians along the ring
TAIL_IN_MOUTH = 0.40             # how far the tail reaches into the jaws
SWEEP = 2 * math.pi - TAIL_IN_MOUTH


def pt(theta, r=R):
    return C + r * math.cos(theta), C + r * math.sin(theta)


def body_width(s):
    # s = 0 at the neck, 1 at the tail tip
    return 150 * (1 - s) ** 0.6 + 84


def _stamp_body(d, s0, s1, n=1400):
    for i in range(int(n * s1), int(n * s0) - 1, -1):
        s = i / n
        x, y = pt(HEAD_ANGLE - s * SWEEP)
        w = body_width(s)
        d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=EMBER + (255,))


def _pixelate(layer, block):
    a = layer.split()[3].resize((S // block, S // block), Image.BOX)
    a = a.point(lambda v: 255 if v > 110 else 0)
    big = a.resize((S, S), Image.NEAREST)
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    # each pixel a separate tile, with checker shading
    tiles = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    td = ImageDraw.Draw(tiles)
    for gy in range(S // block):
        for gx in range(S // block):
            if a.getpixel((gx, gy)):
                shade = 1.0 if (gx + gy) % 2 else 0.72
                col = tuple(int(c * shade) for c in EMBER) + (255,)
                td.rectangle([gx * block + 3, gy * block + 3,
                              gx * block + block - 4, gy * block + block - 4], fill=col)
    out.paste(tiles, (0, 0), big)
    return out


def _head(d):
    # head drawn in polar coords so it curves with the ring
    steps = 80
    def hw(f):  # half-width along the head
        return 118 + 52 * math.sin(math.pi * min(1, f / 0.75)) - 40 * max(0, f - 0.75) / 0.25
    def opening(f):  # jaw opening (half-gap around the centre line)
        return 0 if f < 0.5 else (f - 0.5) / 0.5 * hw(f) * 0.62
    def P(f, r):
        return pt(HEAD_ANGLE + f * HEAD_SPAN, r)
    # skull (closed part)
    fs = [i / steps for i in range(steps + 1) if i / steps <= 0.5]
    d.polygon([P(f, R + hw(f)) for f in fs] + [P(f, R - hw(f)) for f in reversed(fs)],
              fill=EMBER + (255,))
    # upper and lower jaws
    fj = [0.5 + 0.5 * i / steps for i in range(steps + 1)]
    for sign in (1, -1):
        outer = [P(f, R + sign * hw(f)) for f in fj]
        inner = [P(f, R + sign * opening(f)) for f in reversed(fj)]
        d.polygon(outer + inner, fill=EMBER + (255,))
        tip = P(1.0, R + sign * (hw(1.0) + opening(1.0)) / 2)
        rr = (hw(1.0) - opening(1.0)) / 2
        d.ellipse([tip[0] - rr, tip[1] - rr, tip[0] + rr, tip[1] + rr], fill=EMBER + (255,))
    # brow ridge + eye
    d.line([P(f, R + hw(f) * 0.55) for f in [0.15 + 0.4 * i / 20 for i in range(21)]],
           fill=EMBER_DARK + (255,), width=12, joint="curve")
    ex, ey = P(0.36, R + 58)
    d.ellipse([ex - 34, ey - 34, ex + 34, ey + 34], fill=BG + (255,))
    d.ellipse([ex - 9, ey - 25, ex + 9, ey + 25], fill=BONE + (255,))


def draw_logo(pixel_from=0.5):
    # living front half: smooth, with scale chevrons
    smooth = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(smooth)
    _stamp_body(d, 0.0, pixel_from + 0.01)
    for i in range(12, int(1400 * pixel_from), 34):
        s = i / 1400
        th = HEAD_ANGLE - s * SWEEP
        w = body_width(s)
        d.line([pt(th + 0.02, R - w * 0.33), pt(th - 0.01, R), pt(th + 0.02, R + w * 0.33)],
               fill=EMBER_DARK + (255,), width=10, joint="curve")
    # swallowed back half: breaks into pixels, coarser toward the tail
    tiers = [(pixel_from, 0.72, 34), (0.72, 0.88, 52), (0.88, 1.0, 74)]
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    for (s0, s1, block) in reversed(tiers):
        layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        _stamp_body(ImageDraw.Draw(layer), s0, s1)
        px = _pixelate(layer, block)
        img.alpha_composite(px)
    img.alpha_composite(smooth)
    _head(ImageDraw.Draw(img))
    return img


def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo")
    os.makedirs(out, exist_ok=True)
    logo = draw_logo()
    mark = logo.resize((1024, 1024), Image.LANCZOS)
    mark.save(os.path.join(out, "ouroboros_transparent.png"))

    # YouTube avatar: dark circle, logo centred with breathing room
    av = Image.new("RGB", (800, 800), BG)
    glow = logo.resize((800, 800), Image.LANCZOS).split()[3].filter(ImageFilter.GaussianBlur(40))
    av.paste(Image.new("RGB", (800, 800), (70, 26, 8)), (0, 0), glow)
    small = logo.resize((640, 640), Image.LANCZOS)
    av.paste(small, (80, 80), small)
    av.save(os.path.join(out, "avatar_800.png"))
    print("wrote", out)


if __name__ == "__main__":
    main()
