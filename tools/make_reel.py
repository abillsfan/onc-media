"""ONC reel builder.

Usage:
    python3 tools/make_reel.py SPEC.json OUT.mp4

SPEC.json shape:
{
  "intro": ["LIVE BREAK", "TOMORROW"],          # 1-2 short lines under the logo slam
  "scenes": [                                     # 3 scenes work best (each ~2.8s)
    {"lines": ["RANDOM", "TEAM", "BREAKS"], "sizes": [190, 190, 190], "accent": 1},
    ...
  ],
  "outro": {"lines": ["SUNDAY 6 AM CT", "LIVE ON WHATNOT", "@outta_nowhere_cards"],
            "sizes": [104, 104, 58], "accent": 1, "cta": "TAP IN  ·  SET YOUR ALARM"},
  "bg_shift": 0,                                  # -1..1 shifts which part of the banner is the backdrop
  "seed": 7                                       # varies streaks/beat feel between reels
}
"accent" is the index of the line drawn in ONC blue. Keep each line short (fits ~16 chars at 120px).
Output: 1080x1920, 30 fps, H.264 + AAC, ~14 s. Audio is an original, gently mixed beat from tools/beats.py
(optional "audio": "ballpark" | "fightsong" | "chant" | "stomp" | ...; otherwise it rotates through the stadium styles by seed). No licensed music.
"""
import json, math, os, random, subprocess, sys, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
BRAND = os.path.join(HERE, "..", "brand")
FONT = "/usr/share/fonts/truetype/freefont/FreeSansBoldOblique.ttf"
if not os.path.exists(FONT):
    FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

W, H, FPS = 1080, 1920, 30
BLUE = (26, 60, 255)
ACCENT = (95, 145, 255)
WHITE = (255, 255, 255)


def main(spec_path, out_path):
    spec = json.load(open(spec_path))
    random.seed(spec.get("seed", 7))
    scenes_spec = spec["scenes"]
    scene_len = 2.8
    intro_len = 2.4
    outro_len = 3.4
    DUR = intro_len + scene_len * len(scenes_spec) + outro_len
    N = int(DUR * FPS)

    banner = Image.open(os.path.join(BRAND, "banner.jpg")).convert("RGB")
    bw, bh = banner.size
    cx = bw // 2 + int(spec.get("bg_shift", 0) * (bw // 2 - 520))
    crop = banner.crop((cx - 520, 0, cx + 520, bh))
    bg_base = crop.resize((int(H * 1040 / bh), H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(18))
    bg_base = Image.blend(bg_base, Image.new("RGB", bg_base.size, (3, 5, 12)), 0.62)
    logo = Image.open(os.path.join(BRAND, "logo.png")).convert("RGBA")

    fonts = {}

    def font(sz):
        if sz not in fonts:
            fonts[sz] = ImageFont.truetype(FONT, sz)
        return fonts[sz]

    def fit_size(txt, sz, maxw=980):
        while sz > 30 and (font(sz).getbbox(txt)[2] - font(sz).getbbox(txt)[0]) > maxw:
            sz -= 4
        return sz

    def ease_out(t):
        t = max(0.0, min(1.0, t))
        return 1 - (1 - t) ** 3

    def text_layer(lines, sizes=None, accent=None):
        sizes = sizes or [110] * len(lines)
        rendered = []
        for k, txt in enumerate(lines):
            sz = fit_size(txt, sizes[min(k, len(sizes) - 1)])
            f = font(sz)
            l, t, r, b = f.getbbox(txt)
            col = ACCENT if k == accent else WHITE
            rendered.append((txt, f, col, r - l, b - t, l, t))
        gap = 18
        tw = max(r[3] for r in rendered) + 80
        th = sum(r[4] for r in rendered) + gap * (len(rendered) - 1) + 80
        layer = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        glow = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        d, g = ImageDraw.Draw(layer), ImageDraw.Draw(glow)
        y = 40
        for txt, f, col, w, h, l, t in rendered:
            x = (tw - w) // 2 - l
            g.text((x, y - t), txt, font=f, fill=BLUE + (255,), stroke_width=10, stroke_fill=BLUE + (255,))
            d.text((x, y - t), txt, font=f, fill=col + (255,), stroke_width=4, stroke_fill=(0, 0, 0, 255))
            y += h + gap
        return Image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(16)), layer)

    scenes = []
    t0 = intro_len
    for s in scenes_spec:
        scenes.append((t0, t0 + scene_len, text_layer(s["lines"], s.get("sizes"), s.get("accent")), 900, False))
        t0 += scene_len
    o = spec["outro"]
    scenes.append((t0, DUR, text_layer(o["lines"], o.get("sizes"), o.get("accent")), 1180, True))
    cta = text_layer([o.get("cta", "FOLLOW  ·  TAP IN")], [54])
    intro_tag = text_layer(spec.get("intro", ["OUTTA NOWHERE", "CARDS"]), [96, 96], 1) if spec.get("intro") else None
    HITS = [0.0] + [s[0] for s in scenes]

    streaks = [(random.uniform(-200, W), random.uniform(0, H), random.uniform(250, 700),
                random.uniform(14, 40), random.uniform(2, 7)) for _ in range(26)]

    def paste_center(canvas, layer, cx, cy, scale=1.0, alpha=1.0):
        if scale != 1.0:
            layer = layer.resize((max(1, int(layer.width * scale)), max(1, int(layer.height * scale))), Image.BICUBIC)
        if alpha < 1.0:
            layer = layer.copy()
            layer.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha)))
        canvas.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))

    def frame(i):
        t = i / FPS
        zoom = 1.0 + 0.06 * (t / DUR)
        bg = bg_base.resize((int(bg_base.width * zoom), int(H * zoom)), Image.BILINEAR)
        ox = int((bg.width - W) / 2 + 120 * math.sin(t * 0.4))
        oy = int((bg.height - H) / 2)
        canvas = bg.crop((ox, oy, ox + W, oy + H)).convert("RGBA")
        st = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(st)
        for (x0, y0, ln, sp, wd) in streaks:
            x = (x0 + sp * i * 1.6) % (W + 800) - 400
            y = (y0 - sp * i * 0.9) % H
            sd.line([(x, y), (x + ln, y - ln * 0.55)], fill=BLUE + (150,), width=int(wd))
        canvas.alpha_composite(st.filter(ImageFilter.GaussianBlur(2)))
        since = min([t - h for h in HITS if t >= h] or [99])
        shake = 22 * max(0.0, 1 - since / 0.35)
        sx, sy = random.uniform(-shake, shake), random.uniform(-shake, shake)
        if t < intro_len:
            p = ease_out(t / 0.45)
            paste_center(canvas, logo, W / 2 + sx, H / 2 - 40 + sy, scale=(2.4 - 1.4 * p) * 1.25, alpha=min(1, t / 0.15))
            if intro_tag is not None and t > 0.9:
                paste_center(canvas, intro_tag, W / 2 + sx, 1500 + sy, scale=1.6 - 0.6 * ease_out((t - 0.9) / 0.3))
        for (a, b, layer, cy, is_outro) in scenes:
            if a <= t < b:
                p = ease_out((t - a) / 0.28)
                fade = 1.0 if (is_outro or t < b - 0.15) else max(0.0, (b - t) / 0.15)
                paste_center(canvas, layer, W / 2 + sx, cy + sy, scale=1.9 - 0.9 * p, alpha=min(fade, 0.2 + p))
                if is_outro:
                    lp = ease_out((t - a - 0.35) / 0.4)
                    if lp > 0:
                        paste_center(canvas, logo, W / 2, 560, scale=0.95 * lp + 0.01)
                    if t > a + 0.8:
                        paste_center(canvas, cta, W / 2, 1560, scale=1.0 + 0.04 * (0.5 + 0.5 * math.sin(t * 9)))
        if since < 0.12:
            canvas.alpha_composite(Image.new("RGBA", (W, H), (200, 215, 255, int(170 * (1 - since / 0.12)))))
        return canvas.convert("RGB")

    # audio: gentle original beat; style rotates with the seed unless the spec names one
    sys.path.insert(0, HERE)
    from beats import make_track, SR, ROTATION
    style = spec.get("audio") or ROTATION[spec.get("seed", 7) % len(ROTATION)]
    audio = make_track(style, DUR, HITS, seed=spec.get("seed", 7),
                       risers=[(0.1, 2.3), (max(0.1, scenes[-1][0] - 2.4), 2.3)])
    wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    with wave.open(wav, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((audio * 32767).astype(np.int16).tobytes())

    proc = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", "-", "-i", wav,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out_path,
    ], stdin=subprocess.PIPE)
    for i in range(N):
        proc.stdin.write(frame(i).tobytes())
    proc.stdin.close(); proc.wait()
    os.unlink(wav)
    print("wrote", out_path, f"{DUR:.1f}s")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
