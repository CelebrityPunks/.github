"""Procedural background visuals for the statement video.

Every visual here is drawn with code (shapes, lines, noise): no stock footage
and no AI-generated imagery. Each function takes (img, t, dur) where t is the
time since the scene started, and draws onto the RGB image `img`.
"""
import math
import random

from PIL import Image, ImageDraw, ImageFilter

W, H = 1920, 1080
EMBER = (255, 112, 40)
EMBER_DIM = (120, 52, 20)
rng = random.Random(42)


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def mix(c, a, bg=(8, 8, 9)):
    a = max(0.0, min(1.0, a))
    return tuple(int(c[i] * a + bg[i] * (1 - a)) for i in range(3))


# ---------------------------------------------------------------- FEED
# An endless, speeding-up scroll of identical grey "content" cards, glitching.
FEED_COLS = 5
FEED_CARDS = []
for col in range(FEED_COLS):
    y = 0
    cards = []
    while y < H * 6:
        h = rng.choice([300, 360, 420, 480])
        tint = rng.randint(30, 52)
        cards.append((y, h, tint, rng.randint(2, 4)))
        y += h + 24
    FEED_CARDS.append((cards, y))


def feed(img, t, dur):
    d = ImageDraw.Draw(img)
    cw = 340
    x0 = (W - (FEED_COLS * cw + (FEED_COLS - 1) * 24)) // 2
    # scroll distance accelerates: the flood never stops
    dist = 120 * t + 38 * t * t
    for c, (cards, total) in enumerate(FEED_CARDS):
        x = x0 + c * (cw + 24)
        off = (dist * (0.8 + 0.12 * c)) % total
        for (cy, h, tint, bars) in cards:
            for wrap in (0, total):
                y = cy - off + wrap
                if y > H or y + h < 0:
                    continue
                d.rounded_rectangle([x, y, x + cw, y + h], 18, fill=(22, 22, 25))
                th = h - 40 - bars * 26
                d.rounded_rectangle([x + 14, y + 14, x + cw - 14, y + 14 + th], 12,
                                    fill=(tint, tint, tint + 4))
                # a blank "face" in every thumbnail: the same face, again and again
                fx, fy = x + cw / 2, y + 14 + th / 2
                d.ellipse([fx - 34, fy - 40, fx + 34, fy + 40], fill=(tint + 18,) * 3)
                for b in range(bars):
                    by = y + 28 + th + b * 26
                    bw = cw - 28 - (b * 61 % 120)
                    d.rounded_rectangle([x + 14, by, x + 14 + bw, by + 12], 6, fill=(40, 40, 44))
    # glitch: shift horizontal slices, more often as the scroll speeds up
    g = random.Random(int(t * 12))
    for _ in range(int(2 + t * 0.6)):
        if g.random() < 0.5:
            sy = g.randint(0, H - 60)
            sh = g.randint(6, 50)
            dx = g.randint(-90, 90)
            band = img.crop((0, sy, W, sy + sh))
            img.paste(band, (dx, sy))


# ---------------------------------------------------------------- CLONES
# One face, copied until it fills the screen.
def _face(size):
    im = Image.new("RGB", (size, size), (8, 8, 9))
    d = ImageDraw.Draw(im)
    s = size
    d.ellipse([s * 0.18, s * 0.1, s * 0.82, s * 0.9], fill=(58, 58, 62))
    d.ellipse([s * 0.34, s * 0.38, s * 0.43, s * 0.47], fill=(16, 16, 18))
    d.ellipse([s * 0.57, s * 0.38, s * 0.66, s * 0.47], fill=(16, 16, 18))
    d.line([s * 0.38, s * 0.68, s * 0.62, s * 0.68], fill=(16, 16, 18), width=max(1, s // 40))
    return im


FACE_BIG = _face(512)
_face_cache = {}


def clones(img, t, dur):
    # grid doubles density over the scene: 1 -> 2 -> 4 -> ... columns
    k = ease(t / (dur - 2))
    cols = max(1, int(round(2 ** (k * 5.3))))
    size = int(math.ceil(W / cols))
    if size not in _face_cache:
        _face_cache[size] = FACE_BIG.resize((size, size), Image.LANCZOS)
    face = _face_cache[size]
    rows = int(math.ceil(H / size)) + 1
    yoff = (H - rows * size) // 2
    for r in range(rows):
        for c in range(cols):
            img.paste(face, (c * size, yoff + r * size))


# ---------------------------------------------------------------- SCAN
# Colourful hand-drawn scribbles get scanned and turned into grey pixels.
def _human_art():
    im = Image.new("RGB", (W, H), (8, 8, 9))
    d = ImageDraw.Draw(im)
    pal = [(255, 112, 40), (240, 200, 90), (90, 170, 220), (220, 80, 110),
           (120, 200, 140), (240, 238, 232)]
    r = random.Random(3)
    for _ in range(46):
        x, y = r.uniform(0, W), r.uniform(0, H)
        a = r.uniform(0, 6.28)
        col = r.choice(pal)
        wdt = r.randint(3, 14)
        pts = []
        for i in range(r.randint(30, 90)):
            a += r.uniform(-0.35, 0.35)
            x += math.cos(a) * 14
            y += math.sin(a) * 14
            pts.append((x, y))
        d.line(pts, fill=col, width=wdt, joint="curve")
    return im.filter(ImageFilter.GaussianBlur(1.2))


ART = _human_art()
_px = ART.resize((W // 30, H // 30), Image.BILINEAR).convert("L")
ART_PIXELS = _px.point(lambda v: min(255, int(v * 1.3))).resize((W, H), Image.NEAREST).convert("RGB")


def scan(img, t, dur):
    sx = int(W * ease((t - 0.6) / (dur - 2.5)))
    img.paste(ART, (0, 0))
    if sx > 0:
        img.paste(ART_PIXELS.crop((0, 0, sx, H)), (0, 0))
    d = ImageDraw.Draw(img)
    for i, a in enumerate((0.12, 0.25, 0.5, 1.0)):
        w = 18 - i * 5
        d.rectangle([sx - w, 0, sx + w, H], fill=mix(EMBER, a * 0.6))


# ---------------------------------------------------------------- PULSE
# A flat machine line... that starts to beat.
def _beat(u):
    # one heartbeat (PQRST-ish) on u in [0,1)
    return (0.12 * math.exp(-((u - 0.18) / 0.04) ** 2)
            - 0.15 * math.exp(-((u - 0.33) / 0.012) ** 2)
            + 1.0 * math.exp(-((u - 0.37) / 0.014) ** 2)
            - 0.28 * math.exp(-((u - 0.41) / 0.014) ** 2)
            + 0.22 * math.exp(-((u - 0.62) / 0.05) ** 2))


def pulse(img, t, dur):
    d = ImageDraw.Draw(img)
    base = H * 0.80
    speed = W / 4.2
    head = (t * speed)
    beat_start = W * 0.55  # the first sweep stays flat until here
    pts_bright, pts = [], []
    for x in range(0, W, 3):
        # world position of this pixel on the current or previous sweep
        sweep = math.floor((head - x) / W)
        wx = x + sweep * W
        if wx > head or head - wx > W * 0.92:
            continue
        y = base
        if wx > beat_start:
            u = ((wx - beat_start) / 330.0) % 1.0
            y -= 230 * _beat(u)
        age = (head - wx) / (W * 0.92)
        pts.append((x, y, age))
    # draw as short segments, fading with age (phosphor trail)
    for (x1, y1, a1), (x2, y2, a2) in zip(pts, pts[1:]):
        if x2 < x1:
            continue
        a = 1 - a1
        d.line([x1, y1, x2, y2], fill=mix(EMBER_DIM, a), width=9)
        d.line([x1, y1, x2, y2], fill=mix(EMBER, a), width=3)
    if pts:
        hx = head % W
        d.ellipse([hx - 9, base - 9, hx + 9, base + 9], fill=(255, 200, 160))


# ---------------------------------------------------------------- INK
# A wobbly, imperfect hand-drawn line with ink blots: the "mistakes".
def _ink_path():
    r = random.Random(11)
    pts = []
    x, y, a = -40, H * 0.5, 0.0
    for i in range(1500):
        a += r.uniform(-0.22, 0.22) + 0.018 * math.sin(i * 0.02)
        a -= 0.0009 * (y - H * 0.5)  # drift back toward the middle
        a = max(-1.2, min(1.2, a))
        x += math.cos(a) * 3.2 + 0.25
        y += math.sin(a) * 3.2 + 2.2 * math.sin(i * 0.013)
        y = max(80, min(H - 80, y))
        pts.append((x, y))
    blots = [pts[i] + (r.randint(10, 26),) for i in (180, 520, 830, 1190, 1420)]
    return pts, blots


INK_PTS, INK_BLOTS = _ink_path()


def ink(img, t, dur):
    d = ImageDraw.Draw(img)
    n = int(len(INK_PTS) * ease(t / (dur - 1.5)))
    # a second, fainter "sketch" pass offset slightly, like a real pencil
    if n > 2:
        sk = [(x + 6, y - 5) for x, y in INK_PTS[:n]]
        d.line(sk, fill=(42, 41, 39), width=2)
        for i in range(0, n - 1, 1):
            w = 3 + int(2.5 * (1 + math.sin(i * 0.05)))  # pressure varies
            d.line([INK_PTS[i], INK_PTS[i + 1]], fill=(150, 146, 138), width=w)
    for (bx, by, br) in INK_BLOTS:
        idx = INK_PTS.index((bx, by))
        if idx < n:
            k = ease((n - idx) / 40)
            rr = br * k
            r = random.Random(idx)
            for _ in range(6):
                ox, oy = r.uniform(-rr * 0.6, rr * 0.6), r.uniform(-rr * 0.6, rr * 0.6)
                s = rr * r.uniform(0.4, 0.9)
                d.ellipse([bx + ox - s, by + oy - s, bx + ox + s, by + oy + s], fill=EMBER)
    if 2 < n < len(INK_PTS):
        px, py = INK_PTS[n - 1]
        d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=(255, 220, 190))


# ---------------------------------------------------------------- FINGERPRINT
def _fingerprint():
    r = random.Random(5)
    cx, cy = W / 2, H / 2
    rings = []
    for k in range(1, 34):
        rad = k * 15.5
        pts = []
        # open the inner loops at the bottom, like a real loop pattern
        gap = 0.55 if k < 8 else 0.25 + 0.01 * k
        steps = int(60 + k * 10)
        ph = r.uniform(0, 6.28)
        for s in range(steps + 1):
            th = -math.pi / 2 + gap + (2 * math.pi - 2 * gap) * s / steps
            wob = 1 + 0.035 * math.sin(3 * th + ph) + 0.02 * math.sin(7 * th + k)
            rx = rad * 0.78 * wob
            ry = rad * 1.0 * wob
            x = cx + rx * math.cos(th) + 18 * math.sin(k * 0.3)
            y = cy - ry * math.sin(th) + 4 * k * 0.15
            pts.append((x, y))
        # break some ridges (bifurcations / ridge endings)
        cuts = sorted(r.sample(range(5, steps - 5), 2)) if k > 3 else []
        segs, last = [], 0
        for c in cuts:
            segs.append(pts[last:c])
            last = c + r.randint(2, 5)
        segs.append(pts[last:])
        rings.append(segs)
    return rings


FP_RINGS = _fingerprint()
FP_MASK = Image.new("L", (W, H), 0)
ImageDraw.Draw(FP_MASK).ellipse([W / 2 - 400, H / 2 - 520, W / 2 + 400, H / 2 + 560], fill=255)
FP_MASK = FP_MASK.filter(ImageFilter.GaussianBlur(70))


def _draw_fp(img, progress, color, glow=1.0):
    layer = Image.new("RGB", (W, H), (8, 8, 9))
    d = ImageDraw.Draw(layer)
    total = len(FP_RINGS)
    for i, segs in enumerate(FP_RINGS):
        k = max(0.0, min(1.0, progress * total - i))
        if k <= 0:
            break
        for seg in segs:
            m = int(len(seg) * k)
            if m > 1:
                d.line(seg[:m], fill=mix(color, glow), width=5, joint="curve")
    img.paste(layer, (0, 0), FP_MASK)


def fingerprint_draw(img, t, dur):
    _draw_fp(img, ease(t / (dur - 1.5)), EMBER)


def fingerprint_hold(img, t, dur):
    glow = 0.55 + 0.45 * (0.5 + 0.5 * math.sin(t * 2.4))  # slow heartbeat glow
    _draw_fp(img, 1.0, EMBER, glow)
    embers(img, t + 20, dur)


# ---------------------------------------------------------------- EMBERS
EMBER_PARTS = [(rng.uniform(0, W), rng.uniform(30, 110), rng.uniform(0, 2000),
                rng.uniform(1.5, 5), rng.uniform(0, 6.28)) for _ in range(140)]


def embers(img, t, dur):
    d = ImageDraw.Draw(img)
    for (x0, sp, ph, sz, wp) in EMBER_PARTS:
        y = H + 40 - ((t * sp + ph) % (H + 80))
        x = x0 + 30 * math.sin(t * 0.7 + wp)
        a = 0.35 + 0.65 * (y / H)
        flick = 0.6 + 0.4 * math.sin(t * 6 + wp * 3)
        c = mix(EMBER, a * flick)
        d.ellipse([x - sz, y - sz, x + sz, y + sz], fill=c)


def closing(img, t, dur):
    _draw_fp(img, 1.0, EMBER, 0.35 * (1 - ease((t - (dur - 5)) / 4)))
    embers(img, t + 40, dur)


_LOGO = None


def logo(img, t, dur):
    # the ouroboros: fades and scales in, turns slowly, embers rise behind it
    global _LOGO
    if _LOGO is None:
        import make_logo
        _LOGO = make_logo.draw_logo().resize((640, 640), Image.LANCZOS)
    embers(img, t + 40, dur)
    k = ease(t / 2.5)
    size = int(640 * (0.86 + 0.14 * k))
    lg = _LOGO.rotate(-t * 4, resample=Image.BICUBIC).resize((size, size), Image.LANCZOS)
    a = lg.split()[3].point(lambda v: int(v * k))
    img.paste(lg, (W // 2 - size // 2, 420 - size // 2), a)


BACKGROUNDS = {
    "feed": feed, "clones": clones, "scan": scan, "pulse": pulse, "ink": ink,
    "fp_draw": fingerprint_draw, "fp_hold": fingerprint_hold, "closing": closing,
    "logo": logo,
}
