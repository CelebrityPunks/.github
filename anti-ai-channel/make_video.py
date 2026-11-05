#!/usr/bin/env python3
"""Render the "MADE BY HANDS" statement video (kinetic typography + ambient drone).

Usage:  python3 make_video.py [output.mp4]
Needs:  Pillow, ffmpeg on PATH.

The output has no voiceover. Record your VO from SCRIPT.md and lay it over
this track in your editor (the scene timings match the script's sections).
"""
import math
import random
import subprocess
import sys

from multiprocessing import Pool

from PIL import Image, ImageDraw, ImageFont, ImageFilter

import visuals

W, H, FPS = 1920, 1080, 30
BG = (8, 8, 9)
WHITE = (240, 238, 232)
GREY = (120, 118, 114)
EMBER = (255, 112, 40)

FONT_BOLD = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
FONT_BLACK = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FONT_LIGHT = "/usr/share/fonts/opentype/inter/Inter-ExtraLight.otf"

_font_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


# Each scene: (start, end, list of lines)
# A line: dict(text, at=seconds after scene start it appears, size, font, color, style)
# style: "fade" (default), "type" (typewriter), "slam" (scale-in punch)
def L(text, at, size=84, f=FONT_BOLD, color=WHITE, style="fade"):
    return dict(text=text, at=at, size=size, font=f, color=color, style=style)


SCENES = [
    # COLD OPEN
    (1.0, 13.5, [
        L("Everything you saw today", 0.5, 78, FONT_LIGHT, style="type"),
        L("might have been made by no one.", 4.5, 78, FONT_BOLD, style="type"),
    ]),
    # THE PROBLEM
    (14.5, 30.0, [
        L("Art with no artist.", 0.5, 92),
        L("Songs with no singer.", 4.0, 92),
        L("Words with no one behind them.", 7.5, 92, color=EMBER),
    ]),
    (31.0, 44.0, [
        L("Trained on our work.", 0.5, 80, FONT_LIGHT),
        L("Without asking.", 3.5, 80, FONT_BOLD),
        L("Sold back to us as new.", 7.0, 80, FONT_BOLD, color=EMBER),
    ]),
    # THE TURN
    (45.0, 56.0, [
        L("But here's what", 0.5, 96, FONT_LIGHT),
        L("they can't automate.", 2.5, 96, FONT_BLACK, style="slam"),
    ]),
    (57.0, 75.0, [
        L("The mistakes.", 0.5, 110, FONT_BLACK, style="slam"),
        L("The effort.", 3.0, 110, FONT_BLACK, style="slam"),
        L("The person.", 5.5, 110, FONT_BLACK, color=EMBER, style="slam"),
        L("That's the point.", 10.0, 64, FONT_LIGHT),
    ]),
    # THE REVEAL
    (76.0, 85.0, [
        L("Something only a human could make.", 0.5, 80, FONT_BOLD, style="type"),
    ]),
    (86.0, 97.0, [
        L("Except", 0.3, 96, FONT_LIGHT),
        L("no human made this.", 2.0, 110, FONT_BLACK, color=EMBER, style="slam"),
    ]),
    (98.0, 109.0, [
        L("The script. The visuals. The music.", 0.5, 76, FONT_BOLD),
        L("All AI.", 3.5, 130, FONT_BLACK, color=EMBER, style="slam"),
        L("Minutes, not months.", 6.5, 56, FONT_LIGHT, color=GREY),
    ]),
    (110.0, 121.0, [
        L("And you felt something anyway.", 0.5, 84, FONT_BOLD, style="type"),
        L("That's the problem.", 6.0, 84, FONT_BLACK, color=EMBER, style="slam"),
    ]),
    # CLOSE
    (122.0, 136.0, [
        L("MADE BY NO ONE.", 1.0, 170, FONT_BLACK, style="slam"),
        L("An anti-AI channel. Made entirely by AI.", 5.0, 46, FONT_LIGHT, color=GREY),
    ]),
]
DURATION = 138.0

# Background visual for each scene (same order as SCENES) and how bright it is
# behind the text. All drawn procedurally in visuals.py.
SCENE_BG = [
    ("feed", 0.55), ("clones", 0.6), ("scan", 0.55), ("pulse", 1.0),
    ("ink", 0.75), ("fp_draw", 0.7), ("fp_glitch", 0.75), ("feed_fast", 0.45),
    ("flatline", 1.0), ("closing", 0.9),
]

# Pre-rendered film grain tiles (cheap, gives the black some texture)
random.seed(7)
GRAIN = []
for _ in range(6):
    g = Image.effect_noise((W // 2, H // 2), 22).resize((W, H))
    GRAIN.append(g)


def put_text(img, xy, text, f, color, a):
    if a <= 0 or not text:
        return
    x, y = int(xy[0]), int(xy[1])
    bb = f.getbbox(text)
    w, h = bb[2] + 4, bb[3] + 4
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).text((0, 0), text, font=f, fill=int(255 * min(1, a)))
    img.paste(Image.new("RGB", (w, h), color), (x, y), mask)


def draw_scene(img, scene, t):
    start, end, lines = scene
    local = t - start
    # scene-level fade out over the last 1.0s
    scene_alpha = 1.0 - ease((t - (end - 1.0)) / 1.0)

    # layout: stack lines vertically, centered
    metrics = []
    for ln in lines:
        f = font(ln["font"], ln["size"])
        bbox = f.getbbox(ln["text"])
        # small subtitle lines get extra breathing room above them
        lh = ln["size"] + (36 if ln["size"] < 70 else 0)
        metrics.append((f, bbox[2] - bbox[0], lh))
    gap = 28
    total_h = sum(m[2] for m in metrics) + gap * (len(lines) - 1)
    y = (H - total_h) / 2

    draw = ImageDraw.Draw(img)
    for ln, (f, tw, lh) in zip(lines, metrics):
        appear = local - ln["at"]
        if appear < 0:
            y += lh + gap
            continue
        text = ln["text"]
        x = (W - tw) / 2
        if lh > ln["size"]:
            y += lh - ln["size"]
            lh = ln["size"]
        alpha = scene_alpha

        if ln["style"] == "type":
            n = int(appear / 0.055)
            text_vis = text[:n]
            cursor_on = (int(appear * 2.5) % 2 == 0) and scene_alpha > 0.5
            put_text(img, (x, y), text_vis, f, ln["color"], alpha)
            if n <= len(text) and cursor_on:
                cx = x + f.getlength(text_vis) + 8
                draw.rectangle([cx, y + lh * 0.15, cx + 6, y + lh * 1.05], fill=EMBER)
        elif ln["style"] == "slam":
            k = ease(appear / 0.35)
            scale = 1.0 + (1 - k) * 0.6
            a = alpha * k
            layer = Image.new("L", (int(tw * 1.7) + 40, int(lh * 2.2)), 0)
            ImageDraw.Draw(layer).text((20, lh * 0.3), text, font=f, fill=255)
            if scale != 1.0:
                layer = layer.resize((int(layer.width * scale), int(layer.height * scale)))
            px = int(W / 2 - (20 + tw / 2) * scale)
            py = int(y + lh / 2 - (lh * 0.3 + lh / 2) * scale)
            solid = Image.new("RGB", layer.size, ln["color"])
            mask = layer.point(lambda v: int(v * a))
            img.paste(solid, (px, py), mask)
        else:  # fade + slight rise
            k = ease(appear / 0.9)
            a = alpha * k
            dy = (1 - k) * 18
            put_text(img, (x, y + dy), text, f, ln["color"], a)
        y += lh + gap


def _text_band():
    # darken a soft horizontal band where the text sits
    col = Image.new("L", (1, H))
    for y in range(H):
        d = (y - H / 2) / 260
        col.putpixel((0, y), int(255 * (1 - 0.6 * math.exp(-d * d))))
    return col.resize((W, H))


TEXT_BAND = _text_band()
BLACK = Image.new("RGB", (W, H), BG)


def render_frame(i):
    t = i / FPS
    img = Image.new("RGB", (W, H), BG)
    for idx, sc in enumerate(SCENES):
        if sc[0] <= t < sc[1]:
            name, dim = SCENE_BG[idx]
            dur = sc[1] - sc[0]
            local = t - sc[0]
            visuals.BACKGROUNDS[name](img, local, dur)
            fade = ease(local / 0.8) * (1 - ease((t - (sc[1] - 1.0)) / 1.0))
            img = Image.blend(BLACK, img, dim * fade)
            img = Image.composite(img, BLACK, TEXT_BAND)
            draw_scene(img, sc, t)
    # subtle vignette + grain
    grain = GRAIN[i % len(GRAIN)]
    img = Image.blend(img, Image.merge("RGB", (grain, grain, grain)), 0.035)
    img = Image.composite(img, Image.new("RGB", (W, H), (0, 0, 0)), VIGNETTE)
    return img


def _frame_bytes(i):
    return render_frame(i).tobytes()


def make_vignette():
    v = Image.new("L", (W // 8, H // 8), 0)
    d = ImageDraw.Draw(v)
    w, h = v.size
    for r in range(60, 0, -1):
        k = r / 60
        val = int(255 * (1 - (1 - k) ** 2 * 0.0) * min(1, (1 - k) * 2.2 + 0.25))
        d.ellipse([w / 2 - w * k * 0.9, h / 2 - h * k * 0.9, w / 2 + w * k * 0.9, h / 2 + h * k * 0.9],
                  fill=min(255, val))
    return v.resize((W, H)).filter(ImageFilter.GaussianBlur(40))


VIGNETTE = make_vignette()


def audio_filter():
    # Low drone (A1 + E2 + A2) with slow swell, a soft "heartbeat" thump
    # on every slam beat region, and fades in/out.
    drone = (
        "0.30*sin(2*PI*55*t)*(0.6+0.4*sin(2*PI*0.07*t))"
        "+0.18*sin(2*PI*82.41*t)*(0.5+0.5*sin(2*PI*0.05*t+1))"
        "+0.10*sin(2*PI*110*t+0.3*sin(2*PI*0.2*t))"
    )
    # thumps: decaying 48Hz pulse once every 2.5s during the second half
    thump = "if(gt(t,45)*lt(t,115),0.55*sin(2*PI*48*t)*exp(-9*mod(t-45,2.5)),0)"
    beep = "if(gt(t,115.3)*lt(t,121),0.09*sin(2*PI*988*t),0)"
    expr = f"({drone}+{thump}+{beep})*0.8"
    return (
        f"aevalsrc='{expr}|{expr}':s=48000:d={DURATION},"
        f"afade=t=in:st=0:d=4,afade=t=out:st={DURATION - 6}:d=6,"
        "lowpass=f=900,volume=0.9"
    )


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "made_by_hands.mp4"
    n = int(DURATION * FPS)
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", audio_filter(),
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out,
    ]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool() as pool:
        for i, frame in enumerate(pool.imap(_frame_bytes, range(n), chunksize=8)):
            p.stdin.write(frame)
            if i % (FPS * 10) == 0:
                print(f"  {i // FPS:>3}s / {int(DURATION)}s", flush=True)
    p.stdin.close()
    p.wait()
    print("done:", out)


if __name__ == "__main__":
    main()
