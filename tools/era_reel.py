"""ONC reel engine with console-era styles on top of the 8-bit game engine (tools/retro_reel.py).

Usage:
    python3 -I tools/era_reel.py SPEC.json OUT.mp4 [t1,t2,...]   # same spec as retro_reel.py, plus "era"

"era": "8bit"  -> exactly the original 8-bit reel (NES-style pixels, square-wave chiptune, scanlines)
       "16bit" -> same games and camera angles, upgraded to a 16-bit console look (original art, no licensed assets):
                  shaded sprites (lit top edge, shadowed bottom edge), smooth gradient skies instead of black,
                  mowed-stripe turf, 15-bit color depth, a 16-bit "PRESS START" title screen with a perspective
                  (scrolling floor) field and logo shine, a shine sweep across the hit card, and FM-synth music
                  (brassy lead, punchy bass, softer drums, echo) instead of square waves.
Every game variant (fb_pass, fb_kick, fb_return, bb_homer, bb_gap, ...) works in every era.
"""
import json, math, os, sys, wave
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import retro_reel as R  # noqa: E402

ERAS = ["8bit", "16bit"]
LW, LH, S = R.LW, R.LH, R.S

# ================================================================ 16-bit look
def _sh(m, dy, dx):
    """m shifted so out[y, x] = m[y - dy, x - dx] (edges repeat)."""
    p = np.pad(m, ((abs(dy), abs(dy)), (abs(dx), abs(dx))) + ((0, 0),) * (m.ndim - 2), mode="edge")
    return p[abs(dy) - dy: abs(dy) - dy + m.shape[0], abs(dx) - dx: abs(dx) - dx + m.shape[1]]

_ys = np.arange(LH)[:, None]
SKY_TOP, SKY_BOT = np.array([14, 10, 44]), np.array([70, 34, 110])
_grad = (SKY_TOP + (SKY_BOT - SKY_TOP) * (np.arange(LH) / LH)[:, None])[:, None, :].repeat(LW, 1)

def finish16(img):
    a = np.asarray(img.convert("RGB")).astype(np.float32)
    blk = (a.sum(2) == 0)
    bg = blk.copy()
    for dy, dx in ((2, 0), (-2, 0), (0, 2), (0, -2), (2, 2), (-2, -2)): bg &= _sh(blk, dy, dx)
    same_up = (a == _sh(a, 1, 0)).all(2); same_dn = (a == _sh(a, -1, 0)).all(2)
    same_lf = (a == _sh(a, 0, 1)).all(2); same_rt = (a == _sh(a, 0, -1)).all(2)
    top = ~same_up & same_dn & ~bg; bot = ~same_dn & same_up & ~bg
    lft = ~same_lf & same_rt & ~bg & ~top & ~bot; rgt = ~same_rt & same_lf & ~bg & ~top & ~bot
    # mowed turf stripes on the field greens
    g = a[..., 1]; turf = (a[..., 0] < 10) & (a[..., 2] < 10) & (g > 100)
    stripe = np.where(((_ys // 12) % 2) == 0, 1.13, 0.87) * np.ones((1, LW))
    a[turf] *= stripe[turf][:, None]
    # sprites cast soft shadows down-right onto the turf (depth the 8-bit look doesn't have)
    solid = ~turf & ~bg & ~((a > 200).all(2))
    shadow = turf & (_sh(solid, 2, 2) | _sh(solid, 1, 1))
    a[shadow] *= 0.55
    # interior of big flat areas gets lit from above: lighter toward the top of each scene, darker low
    interior = same_up & same_dn & same_lf & same_rt & ~bg
    light = (1.12 - 0.24 * (_ys / LH)) * np.ones((1, LW))
    a[interior] *= light[interior][:, None]
    # shading: lit top/left edges, shadowed bottom/right edges
    a[top] = a[top] + (255 - a[top]) * 0.38
    a[lft] = a[lft] + (255 - a[lft]) * 0.18
    a[bot] *= 0.58; a[rgt] *= 0.78
    # richer color, then gradient sky where the 8-bit game had flat black
    m = a.mean(2, keepdims=True); a = m + (a - m) * 1.18
    a[bg] = _grad[bg]
    a = (np.clip(a, 0, 255) // 8) * 8 + 4          # 15-bit console color depth
    out = Image.fromarray(a.astype(np.uint8)).resize((R.W, R.H), Image.NEAREST)
    return out

def _shine(img, box, p, alpha=0.55, width=18):
    """White diagonal shine band across box=(x0,y0,x1,y1) at progress p (0..1)."""
    x0, y0, x1, y1 = box
    if not (0 <= p <= 1) or x1 <= x0: return img
    ov = Image.new("L", img.size, 0); d = ImageDraw.Draw(ov)
    cx = x0 - 40 + (x1 - x0 + 80) * p
    d.polygon([(cx, y0), (cx + width, y0), (cx + width - 30, y1), (cx - 30, y1)], fill=int(255 * alpha))
    clip = Image.new("L", img.size, 0); ImageDraw.Draw(clip).rectangle(box, fill=255)
    ov = Image.fromarray(np.minimum(np.asarray(ov), np.asarray(clip)))
    return Image.composite(Image.new("RGB", img.size, (255, 255, 255)), img, ov)

_scene_pack8 = R.scene_pack
def scene_pack16(t, sp):
    img = _scene_pack8(t, sp)
    w = t - R.T_FLIP
    if w > 0.45:
        cw, ch = 84, 117; cx, cy = LW // 2, 230 - 40
        img = _shine(img, (cx - cw // 2, cy - ch // 2, cx + cw // 2, cy + ch // 2), ((w - 0.45) % 1.3) / 0.6)
    return img

def scene_start16(t, sp):
    sport = "BASEBALL" if sp["variant"].startswith("bb") else "FOOTBALL"
    top, bot = np.array([20, 12, 60]), np.array([236, 110, 70])
    k = np.clip(np.arange(LH) / 300, 0, 1)[:, None]
    a = (top + (bot - top) * k)[:, None, :].repeat(LW, 1).astype(np.float32)
    # scrolling perspective field below the horizon (16-bit "floor plane" look)
    hz = 300
    for y in range(hz, LH):
        z = 40.0 / (y - hz + 4)
        xs = (np.arange(LW) - LW / 2) * z
        band = int(z * 30 + t * 9) % 2
        row = np.tile(np.array([40.0, 150.0, 60.0]) * (1.0 if band else 0.86), (LW, 1))
        line = (np.abs(((xs + 1000) % 22) - 11) > 11 - z * 0.45)
        row[line] = [150, 220, 140]
        a[y] = row
    a[hz - 2:hz] = [255, 200, 120]
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(img)
    rgb, al = R.pixel_logo(150)
    drop = int(-180 * (1 - R.ease(t / 0.35)))
    lx, ly = (LW - rgb.width) // 2, 34 + drop
    img.paste(rgb, (lx, ly), al)
    if 0.4 < t < 1.2:
        sh = _shine(img, (lx, ly, lx + rgb.width, ly + rgb.height), (t - 0.4) / 0.6, 0.6, 22)
        img = Image.composite(sh, img, _paste_mask(al, img.size, (lx, ly)))
    d = ImageDraw.Draw(img)
    if t > 0.3:
        w = int(LW * R.ease((t - 0.3) / 0.25))
        d.rectangle((LW // 2 - w // 2, 214, LW // 2 + w // 2, 276), fill=(24, 16, 72), outline=(248, 200, 64), width=2)
        if w > LW * 0.8:
            R.txt(d, (LW // 2 + 2, 248), sport, R.F(24), (120, 40, 0), sh=None)
            R.txt(d, (LW // 2, 246), sport, R.F(24), (252, 216, 72), sh=(88, 24, 0))
    pressed = t >= 1.05
    if 0.55 < t and not pressed and int(t * 4) % 2 == 0: R.txt(d, (LW // 2, 338), "PRESS START", R.F(16), (252, 252, 252), sh=(24, 16, 72))
    if pressed:
        if int(t * 16) % 2 == 0: R.txt(d, (LW // 2, 338), "PRESS START", R.F(16), (252, 216, 72), sh=(24, 16, 72))
        R.txt(d, (LW // 2 - 4, 378), "► 1 PLAYER", R.F(8), (252, 252, 252), "mm", sh=(24, 16, 72))
        R.txt(d, (LW // 2 + 4, 396), "2 PLAYERS", R.F(8), (200, 200, 220), "mm", sh=(24, 16, 72))
    if t > 0.55: R.txt(d, (LW // 2, 458), "© 2026 OUTTA NOWHERE CARDS", R.F(6), (252, 252, 252), sh=(24, 16, 72))
    if t > R.T_START - 0.12: d.rectangle((0, 0, LW, LH), fill=(0, 0, 0))
    return img

def _paste_mask(al, size, xy):
    m = Image.new("L", size, 0); m.paste(al, xy); return m

# ================================================================ 16-bit FM-synth audio (original)
SR = R.SR
def fm_lead(n, dur, vol, duty=0.5, slide=0.0):
    t = np.arange(int(dur * SR)) / SR
    f = R.hz(n) * (1 + slide * t / max(dur, 1e-6)) * (1 + 0.004 * np.sin(2 * np.pi * 5.5 * t) * np.clip(t / 0.15, 0, 1))
    ph = 2 * np.pi * np.cumsum(f) / SR
    ratio = 3.0 if duty < 0.2 else 1.0
    idx = 0.8 + 2.4 * np.exp(-t * 7)
    s = np.sin(ph + idx * np.sin(ph * ratio))
    env = np.minimum(1, t / 0.006) * (0.65 + 0.35 * np.exp(-t * 5)) * np.minimum(1, (dur - t) / 0.02).clip(0)
    return s * env * vol * 1.1

def fm_bass(n, dur, vol):
    t = np.arange(int(dur * SR)) / SR; ph = 2 * np.pi * R.hz(n) * t
    s = np.sin(ph + (0.6 + 1.8 * np.exp(-t * 14)) * np.sin(ph))
    return s * np.minimum(1, t / 0.004) * np.exp(-t * 2.5) * np.minimum(1, (dur - t) / 0.015).clip(0) * vol * 1.2

_noise8 = R.noise
def soft_noise(dur, vol, decay=0.06, period=1):
    s = _noise8(dur, vol, decay, 1)
    k = max(2, period * 3)
    s = np.convolve(s, np.ones(k) / k, mode="same") * math.sqrt(k) * 0.8
    if period >= 3:  # snare/kick-ish body
        t = np.arange(len(s)) / SR; s = s + np.sin(2 * np.pi * 120 * t) * np.exp(-t * 30) * vol * 0.8
    return s

_make_audio8 = R.make_audio
def make_audio16(path, sp, payoff):
    _make_audio8(path, sp, payoff)
    with wave.open(path) as w: x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32767
    y = x.copy()
    for dl, g in ((0.14, 0.28), (0.29, 0.14)):
        k = int(dl * SR); y[k:] += x[:-k] * g
    y /= max(1e-9, np.abs(y).max()) / 0.45
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((y * 32767).astype(np.int16).tobytes())

def use_era(era):
    if era == "8bit": return
    if era == "16bit":
        R.scanlines = finish16; R.scene_pack = scene_pack16; R.scene_start = scene_start16
        R.sq = fm_lead; R.tri = fm_bass; R.noise = soft_noise; R.make_audio = make_audio16
        return
    raise SystemExit(f"unknown era {era!r}; choose from {ERAS}")

if __name__ == "__main__":
    spec = json.load(open(sys.argv[1]))
    use_era(spec.get("era", "8bit"))
    R.main(sys.argv[1], sys.argv[2], [float(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else None)
