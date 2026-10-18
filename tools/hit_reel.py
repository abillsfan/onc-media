"""ONC hit reel: shows a real pull from a break.

Usage:
    python3 tools/hit_reel.py SPEC.json OUT.mp4

SPEC.json:
{
  "photo": "hits/2026-10-18/martinez.jpg",
  "card_rect": [x0, y0, x1, y1],        # the card in the photo (pixels); ~0.8 width/height looks best
  "name": "PEDRO MARTINEZ",
  "detail": "AUTOGRAPH  ·  #'D 16/50",
  "product": "2026 TOPPS ALLEN & GINTER",
  "outro": ["PULLED LIVE ON WHATNOT", "@outta_nowhere_cards", "NEXT BREAK: SUN 10/25 · 6 AM CT"],
  "audio": "trap",                    # trap | drive | synthwave | stomp
  "opener": ["TODAY'S", "HITS"],
  "seed": 3
}
Output: 1080x1920, 30 fps, ~12 s, original synthesized beat (no licensed music).
"""
import json, math, os, random, subprocess, sys, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
FONT = "/usr/share/fonts/truetype/freefont/FreeSansBoldOblique.ttf"
if not os.path.exists(FONT):
    FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
W, H, FPS = 1080, 1920, 30
BLUE, ACCENT, WHITE, GOLD = (26, 60, 255), (95, 145, 255), (255, 255, 255), (255, 214, 64)

_fonts = {}
def font(sz):
    if sz not in _fonts:
        _fonts[sz] = ImageFont.truetype(FONT, sz)
    return _fonts[sz]

def ease(t):
    t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3

def ease_io(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)

def text_layer(lines, sizes, colors, maxw=1000):
    rows = []
    for txt, sz, col in zip(lines, sizes, colors):
        while sz > 28 and font(sz).getbbox(txt)[2] - font(sz).getbbox(txt)[0] > maxw:
            sz -= 4
        f = font(sz); l, t, r, b = f.getbbox(txt)
        rows.append((txt, f, col, r - l, b - t, l, t))
    gap = 16
    tw = max(r[3] for r in rows) + 80
    th = sum(r[4] for r in rows) + gap * (len(rows) - 1) + 80
    layer = Image.new("RGBA", (tw, th), (0, 0, 0, 0)); glow = layer.copy()
    d, g = ImageDraw.Draw(layer), ImageDraw.Draw(glow)
    y = 40
    for txt, f, col, w, h, l, t in rows:
        x = (tw - w) // 2 - l
        g.text((x, y - t), txt, font=f, fill=BLUE + (255,), stroke_width=10, stroke_fill=BLUE + (255,))
        d.text((x, y - t), txt, font=f, fill=col + (255,), stroke_width=4, stroke_fill=(0, 0, 0, 255))
        y += h + gap
    return Image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(14)), layer)

def paste(canvas, layer, cx, cy, scale=1.0, alpha=1.0):
    if scale != 1.0:
        layer = layer.resize((max(1, int(layer.width * scale)), max(1, int(layer.height * scale))), Image.BICUBIC)
    if alpha < 1.0:
        layer = layer.copy(); layer.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha)))
    canvas.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))

def main(spec_path, out):
    spec = json.load(open(spec_path))
    random.seed(spec.get("seed", 3))
    photo = Image.open(os.path.join(ROOT, spec["photo"])).convert("RGB")
    pw, ph = photo.size
    logo = Image.open(os.path.join(ROOT, "brand", "logo.png")).convert("RGBA")

    # blurred photo backdrop
    sc = max(W / pw, H / ph) * 1.15
    bg = photo.resize((int(pw * sc), int(ph * sc)), Image.BILINEAR).filter(ImageFilter.GaussianBlur(28))
    bg = Image.blend(bg, Image.new("RGB", bg.size, (3, 5, 14)), 0.72)

    full = (0, 0, pw, ph)
    card = tuple(spec["card_rect"])
    PANEL_W = 960

    T_ALERT, T_WIDE, T_ZOOM, T_OUT, DUR = 0.0, 1.5, 4.0, 9.0, 12.5
    N = int(DUR * FPS)
    HITS = [0.0, T_WIDE, T_ZOOM, T_ZOOM + 0.9, T_OUT]

    alert = text_layer(spec.get("opener", ["TODAY'S", "HITS"]), [220, 220], [WHITE, GOLD])
    pulled = text_layer(["PULLED LIVE", "TODAY ON WHATNOT"], [92, 64], [WHITE, ACCENT])
    info = text_layer([spec["name"], spec["detail"], spec["product"]], [104, 70, 50], [WHITE, GOLD, ACCENT])
    o = spec["outro"]
    outro = text_layer(o, [84, 64, 56][:len(o)], [WHITE, ACCENT, GOLD][:len(o)])
    cta = text_layer(["FOLLOW  ·  LIKE  ·  SHARE"], [52], [WHITE])

    streaks = [(random.uniform(-200, W), random.uniform(0, H), random.uniform(250, 700),
                random.uniform(14, 40), random.uniform(2, 6)) for _ in range(20)]

    def panel(t):
        if t < T_ZOOM:
            k = 0.0
        else:
            k = ease_io((t - T_ZOOM) / 0.9)
        rect = [full[j] + (card[j] - full[j]) * k for j in range(4)]
        # slow push after the zoom lands
        if t > T_ZOOM + 0.9:
            p = (t - T_ZOOM - 0.9) / (T_OUT - T_ZOOM - 0.9) * 0.06
            cx, cy = (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2
            hw, hh = (rect[2] - rect[0]) / 2 * (1 - p), (rect[3] - rect[1]) / 2 * (1 - p)
            rect = [cx - hw, cy - hh, cx + hw, cy + hh]
        elif t < T_ZOOM:
            p = (t - T_WIDE) / (T_ZOOM - T_WIDE) * 0.03
            cx, cy = pw / 2, ph / 2
            rect = [rect[0] + pw * p, rect[1] + ph * p, rect[2] - pw * p, rect[3] - ph * p]
        rw, rh = rect[2] - rect[0], rect[3] - rect[1]
        out_h = int(PANEL_W * rh / rw)
        img = photo.resize((PANEL_W, out_h), Image.BICUBIC, box=tuple(rect))
        # rounded frame with blue glow
        mask = Image.new("L", img.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, img.width - 1, img.height - 1), 28, fill=255)
        fr = Image.new("RGBA", (img.width + 60, img.height + 60), (0, 0, 0, 0))
        ImageDraw.Draw(fr).rounded_rectangle((22, 22, img.width + 38, img.height + 38), 34, fill=BLUE + (255,))
        fr = fr.filter(ImageFilter.GaussianBlur(12))
        rgba = img.convert("RGBA"); rgba.putalpha(mask)
        fr.alpha_composite(rgba, (30, 30))
        return fr

    def frame(i):
        t = i / FPS
        ox = int((bg.width - W) / 2 + 60 * math.sin(t * 0.5)); oy = int((bg.height - H) / 2)
        canvas = bg.crop((ox, oy, ox + W, oy + H)).convert("RGBA")
        st = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
        for (x0, y0, ln, sp, wd) in streaks:
            x = (x0 + sp * i * 1.6) % (W + 800) - 400; y = (y0 - sp * i * 0.9) % H
            sd.line([(x, y), (x + ln, y - ln * 0.55)], fill=BLUE + (140,), width=int(wd))
        canvas.alpha_composite(st.filter(ImageFilter.GaussianBlur(2)))
        since = min([t - h for h in HITS if t >= h] or [99])
        sh = 20 * max(0.0, 1 - since / 0.3)
        sx, sy = random.uniform(-sh, sh), random.uniform(-sh, sh)

        if t < T_WIDE:
            p = ease(t / 0.35)
            paste(canvas, logo, W / 2, 560, scale=0.75)
            paste(canvas, alert, W / 2 + sx, 1180 + sy, scale=2.0 - p)
        elif t < T_OUT:
            pin = ease((t - T_WIDE) / 0.4)
            pnl = panel(t)
            cy = 900 if t < T_ZOOM else 900 - 60 * ease_io((t - T_ZOOM) / 0.9)
            paste(canvas, pnl, W / 2 + sx, cy + sy + (1 - pin) * 300, alpha=min(1.0, pin * 1.5))
            if t < T_ZOOM:
                paste(canvas, pulled, W / 2, 250, scale=1.6 - 0.6 * ease((t - T_WIDE) / 0.3))
            if t > T_ZOOM + 0.9:
                k = ease((t - T_ZOOM - 0.9) / 0.35)
                paste(canvas, info, W / 2 + sx, 1660 + sy, scale=1.7 - 0.7 * k, alpha=min(1, k * 1.3))
            paste(canvas, logo, 120, 120, scale=0.28)
        else:
            k = ease((t - T_OUT) / 0.4)
            paste(canvas, logo, W / 2, 620, scale=0.4 + 0.55 * k)
            paste(canvas, outro, W / 2 + sx, 1220 + sy, scale=1.8 - 0.8 * k)
            if t > T_OUT + 0.8:
                paste(canvas, cta, W / 2, 1560, scale=1.0 + 0.04 * (0.5 + 0.5 * math.sin(t * 9)))
        if since < 0.12:
            canvas.alpha_composite(Image.new("RGBA", (W, H), (210, 220, 255, int(160 * (1 - since / 0.12)))))
        return canvas.convert("RGB")

    # audio: pick a style per reel so they don't all sound the same
    sys.path.insert(0, HERE)
    from beats import make_track, SR
    audio = make_track(spec.get("audio", "drive"), DUR, HITS, seed=spec.get("seed", 3),
                       risers=[(T_ZOOM - 1.6, 2.4)])
    wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    with wave.open(wav, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((audio * 32767).astype(np.int16).tobytes())

    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium",
        "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest",
        "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for i in range(N):
        proc.stdin.write(frame(i).tobytes())
    proc.stdin.close(); proc.wait(); os.unlink(wav)
    print("wrote", out)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
