"""ONC 8-bit reel engine: original pixel-art sports game clip -> pack rip -> title screen.

Usage:
    python3 tools/retro_reel.py SPEC.json OUT.mp4 [t1,t2,...]   # optional times = save preview PNGs instead

Renders at 270x480, scales 4x (nearest) to 1080x1920, 30 fps, 14 s. Original art + original chiptune.

SPEC (all keys optional except "variant"):
{
  "variant": "fb_run" | "fb_kick" | "fb_pass" | "bb_homer",
      fb_pass  = overhead behind the QB (scramble, Hail Mary), then a cut to the back of the end zone: jump-ball catch
      fb_run   = overhead view behind the runner, last-second touchdown
      fb_kick  = behind-the-kicker view, then a cut to behind the goalposts: game-winning field goal
      bb_homer = behind-the-catcher view, then a cut to the outfield wall: walk-off home run
  "hook": ["DOWN BY 3.", "4 SECONDS LEFT."],      # frame-0 text (2 short lines)
  "home": "ONC", "away": "CPU",                  # scoreboard names (<= 3 chars)
  "away_color": "red" | "green" | "orange" | "purple",
  "end": {"banner": ["NEXT BREAK", "SUN 10/26 6 AM CT"],   # optional show banner (use only real Whatnot facts)
          "lines": ["LIVE BREAKS ON", "WHATNOT"]},
  "pack_label": ["HOBBY", "PACK"],               # 2 short words on the pixel wrapper
  "seed": 1
}
"""
import json, math, os, random, subprocess, sys, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
LW, LH, S, FPS = 270, 480, 4, 30
W, H = LW * S, LH * S
DUR = 14.0
N = int(DUR * FPS)
T_GAME, T_WIPE, T_PACK, T_RIP, T_FLIP, T_END = 5.1, 5.1, 5.5, 6.7, 8.3, 9.8

_fc = {}
def F(sz):
    if sz not in _fc: _fc[sz] = ImageFont.truetype(os.path.join(ROOT, "brand", "ps2p.woff"), sz)
    return _fc[sz]

BLK = (0, 0, 0); WHT = (252, 252, 252); GRY = (188, 188, 188); DGRY = (116, 116, 116)
G1 = (0, 168, 0); G2 = (0, 140, 0); G3 = (0, 112, 0); BLU = (0, 88, 248); LBLU = (60, 188, 252); NAVY = (0, 0, 168)
RED = (216, 40, 0); DRED = (168, 16, 0); YEL = (248, 216, 0); GOLD = (248, 184, 0); ORG = (228, 92, 16)
SKIN = (252, 188, 116); BRN = (136, 72, 0); DIRT = (200, 120, 60); PUR = (104, 68, 252); DPUR = (68, 40, 188)
PINK = (248, 120, 248); SKY = (60, 188, 252); DGRN = (0, 80, 40)
AWAY = {"red": RED, "green": (0, 136, 56), "orange": ORG, "purple": (120, 40, 200)}

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(t): t = clamp(t); return 1 - (1 - t) ** 3
def lerp(a, b, t): return a + (b - a) * t

def txt(d, xy, s, f, col, anchor="mm", sh=BLK):
    x, y = xy
    if sh is not None:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 1)):
            d.text((x + dx, y + dy), s, font=f, fill=sh, anchor=anchor)
    d.text((x, y), s, font=f, fill=col, anchor=anchor)

def fit(s, maxw, sz):
    while sz > 6 and F(sz).getlength(s) > maxw: sz -= 2
    return F(sz)

DIG = {"0": "111101101101111", "1": "010110010010111", "2": "111001111100111", "3": "111001111001111",
       "4": "101101111001001", "5": "111100111001111", "6": "111100111101111", "7": "111001001001001",
       "8": "111101111101111", "9": "111101111001111"}
def digits(d, x, y, s, col, k=1):
    for n, ch in enumerate(s):
        for i, b in enumerate(DIG[ch]):
            if b == "1":
                px, py = x + n * 4 * k + (i % 3) * k, y + (i // 3) * k
                d.rectangle((px, py, px + k - 1, py + k - 1), fill=col)

# ================================================================ sprites
def player(d, x, y, col, frame, facing="up", ball=False, num="7", pants=GRY, shadow=True):
    x, y = int(x), int(y)
    if shadow: d.ellipse((x - 7, y - 2, x + 7, y + 2), fill=(0, 100, 0))
    l = -2 if frame else 0; r = 0 if frame else -2
    d.rectangle((x - 4, y - 7 + l, x - 2, y - 1 + l), fill=WHT); d.rectangle((x + 2, y - 7 + r, x + 4, y - 1 + r), fill=WHT)
    d.rectangle((x - 4, y - 1 + l, x - 2, y + l), fill=BLK); d.rectangle((x + 2, y - 1 + r, x + 4, y + r), fill=BLK)
    d.rectangle((x - 5, y - 11, x + 5, y - 7), fill=pants)
    d.rectangle((x - 6, y - 19, x + 6, y - 11), fill=col)
    a1 = 1 if frame else -1
    d.rectangle((x - 8, y - 18, x - 7, y - 13 + a1), fill=col); d.rectangle((x + 7, y - 18, x + 8, y - 13 - a1), fill=col)
    d.rectangle((x - 8, y - 13 + a1, x - 7, y - 12 + a1), fill=SKIN); d.rectangle((x + 7, y - 13 - a1, x + 8, y - 12 - a1), fill=SKIN)
    if num: digits(d, x - 1 if len(num) == 1 else x - 3, y - 18, num, WHT)
    d.ellipse((x - 4, y - 26, x + 4, y - 18), fill=col)
    d.line((x, y - 26, x, y - 19), fill=WHT)
    if facing == "down":
        d.rectangle((x - 3, y - 22, x + 3, y - 19), fill=SKIN); d.line((x - 3, y - 21, x + 3, y - 21), fill=GRY)
    if ball:
        d.ellipse((x + 6, y - 17, x + 11, y - 13), fill=BRN); d.point((x + 8, y - 15), fill=WHT)

def big(img, fn, x, y, scale=2, box=(40, 44)):
    """Draw a sprite at 2x pixel size: fn(draw, cx, feet_y) on a small canvas, then nearest-upscale and paste."""
    bw, bh = box
    tmp = Image.new("RGBA", (bw, bh), (0, 0, 0, 0)); fn(ImageDraw.Draw(tmp), bw // 2, bh - 3)
    tmp = tmp.resize((bw * scale, bh * scale), Image.NEAREST)
    img.paste(tmp, (int(x - bw * scale / 2), int(y - (bh - 3) * scale)), tmp)

def diver(d, x, y, col, flip=False):
    x, y = int(x), int(y); s = -1 if flip else 1
    d.ellipse((x - 10, y - 2, x + 10, y + 3), fill=(0, 100, 0))
    pts = lambda a, b: (min(x + s * a, x + s * b), max(x + s * a, x + s * b))
    a, b = pts(-12, -6); d.rectangle((a, y - 8, b, y - 6), fill=WHT)
    a, b = pts(-6, 0); d.rectangle((a, y - 10, b, y - 5), fill=WHT)
    a, b = pts(0, 9); d.rectangle((a, y - 11, b, y - 4), fill=col)
    a, b = pts(9, 15); d.rectangle((a, y - 9, b, y - 7), fill=col)
    cx = x + s * 13; d.ellipse((cx - 4, y - 12, cx + 4, y - 4), fill=col)
    hx = x + s * 17; d.rectangle((min(hx, hx + s * 3), y - 9, max(hx, hx + s * 3), y - 7), fill=SKIN)

def crowd(d, y0, y1, t, seed=0, step=7):
    d.rectangle((0, y0, LW, y1), fill=(40, 40, 40))
    rnd = random.Random(int(t * 8) * 7 + seed)
    for cy in range(int(y1) - 2, int(y0) + 4, -step):
        for cx in range(3, LW, 7):
            c = rnd.choice([RED, BLU, YEL, WHT, SKIN, PINK, LBLU])
            d.rectangle((cx, cy - 4 - rnd.randint(0, 1), cx + 3, cy - 1), fill=c)

def fireworks(d, u, spots=((60, 70, 0.0), (210, 90, 0.35), (135, 55, 0.7))):
    for i in range(10):
        ang = i * 0.628 + u
        for c, (cx0, cy0, ph) in enumerate(spots):
            v = u - ph
            if 0 < v < 1.0:
                rr = 40 * ease(v)
                px, py = cx0 + rr * math.cos(ang), cy0 + rr * math.sin(ang)
                d.rectangle((px, py, px + 2, py + 2), fill=[YEL, LBLU, PINK][c] if int(v * 12) % 3 else WHT)

def flash_title(d, u, l1, l2, y=262, sub=None):
    col = [YEL, WHT, LBLU, GOLD][int(u * 10) % 4]
    f = F(32) if u < 0.12 else F(24)
    txt(d, (LW // 2, y), l1, fit(l1, LW - 12, 32 if u < 0.12 else 24), col)
    if l2: txt(d, (LW // 2, y + 32), l2, fit(l2, LW - 12, 32 if u < 0.12 else 24), col)
    if sub and u > 0.6: txt(d, (LW // 2, y + 64), sub, fit(sub, LW - 16, 12), WHT)

def fb_hud(d, sp, home_score, clock, flash=False):
    d.rectangle((0, 0, LW, 34), fill=BLK); d.line((0, 34, LW, 34), fill=WHT)
    txt(d, (8, 10), sp["home"], F(8), LBLU, "lm", None); txt(d, (46, 10), f"{home_score:2d}", F(8), WHT, "lm", None)
    txt(d, (LW - 8, 10), sp["away"], F(8), ORG, "rm", None); txt(d, (LW - 46, 10), f"{sp['away_score']}", F(8), WHT, "rm", None)
    txt(d, (LW // 2, 10), "4TH QTR", F(8), YEL, "mm", None)
    txt(d, (LW // 2, 24), clock, F(8), RED if flash else WHT, "mm", None)

def hook_text(d, sp, t, until=1.5, y=58):
    if t < until and int(t * 6) % 6 != 5:
        h = sp["hook"]
        txt(d, (LW // 2, y), h[0], fit(h[0], LW - 12, 16), YEL)
        if len(h) > 1: txt(d, (LW // 2, y + 22), h[1], fit(h[1], LW - 12, 12), WHT)

# ================================================================ FOOTBALL: overhead run (fb_run)
YD = 6; EZ = 10 * YD; T_TD = 3.6
def fb_field(cam, t, sp):
    img = Image.new("RGB", (LW, LH), G1); d = ImageDraw.Draw(img); off = 300 - cam
    for yd in range(-10, 100, 5):
        y0 = yd * YD + off
        if y0 > LH or y0 + 5 * YD < 0: continue
        if yd < 0: d.rectangle((0, y0, LW, y0 + 5 * YD), fill=NAVY)
        elif (yd // 5) % 2: d.rectangle((0, y0, LW, y0 + 5 * YD), fill=G2)
    ezy = -EZ + off
    if ezy + EZ > 0: txt(d, (LW // 2, ezy + EZ // 2 + 2), " ".join(sp["home"]), F(24), WHT, sh=BLU)
    for yd in range(0, 100, 5):
        y = yd * YD + off
        if -2 < y < LH + 2:
            d.line((8, y, LW - 9, y), fill=WHT, width=2 if yd % 10 == 0 else 1)
            if yd % 10 == 0 and yd > 0:
                n = str(min(yd, 100 - yd)); digits(d, 16, y + 4, n, WHT, k=3); digits(d, LW - 16 - len(n) * 12, y + 4, n, WHT, k=3)
        for k in range(1, 5):
            hy = (yd + k) * YD + off
            if 0 < hy < LH: d.line((92, hy, 98, hy), fill=WHT); d.line((LW - 99, hy, LW - 93, hy), fill=WHT)
    d.line((8, 0, 8, LH), fill=WHT, width=2); d.line((LW - 9, 0, LW - 9, LH), fill=WHT, width=2)
    gy = -EZ + off
    if gy > -40:
        d.rectangle((LW // 2 - 1, gy - 18, LW // 2 + 1, gy + 2), fill=YEL); d.rectangle((LW // 2 - 30, gy - 18, LW // 2 + 30, gy - 16), fill=YEL)
        d.rectangle((LW // 2 - 30, gy - 44, LW // 2 - 28, gy - 16), fill=YEL); d.rectangle((LW // 2 + 28, gy - 44, LW // 2 + 30, gy - 16), fill=YEL)
    if gy - 46 > 0: crowd(d, 0, gy - 46, t)
    return img, d, off

def fb_run(t, sp):
    run_x = lambda t: 135.0 + 38 * ease((t - 0.85) / 0.35) - 62 * ease((t - 2.05) / 0.35)
    run_y = lambda t: 60 * YD - (60 * YD + 12) * clamp(t / T_TD) ** 0.92
    tt = min(t, T_TD); py, px = run_y(tt), run_x(tt)
    img, d, off = fb_field(max(py, -EZ + 150), t, sp); fr = int(t * 10) % 2; ac = sp["acol"]
    for k, (dx, lag) in enumerate([(-40, 34), (52, 46)]):
        player(d, px + dx * (0.6 + 0.4 * math.cos(t + k)), run_y(tt) + lag + 10 * math.sin(t * 3 + k) + off, ac, fr ^ k, "up")
    for (t0, sx, flip) in [(0.95, -1, False), (2.15, 1, True)]:
        wy = run_y(t0) - 6
        if tt < t0 - 0.05:
            ix = run_x(t0 - 0.35) + sx * 30 - sx * 30 * ease((tt - (t0 - 0.6)) / 0.55)
            iy = wy - 70 + 70 * ease((tt - (t0 - 0.9)) / 0.85)
            player(d, ix, iy + off, ac, fr, "down")
        else:
            gx = run_x(t0 - 0.35) - 4 + (0 if not flip else -10); slide = ease((tt - t0) / 0.3) * 10
            diver(d, gx + (slide if not flip else -slide), wy + off + 4, ac, flip)
    player(d, px - 22, py + off + 8, BLU, fr ^ 1, "up", num="44")
    if t < T_TD:
        player(d, px, py + off, BLU, fr, "up", ball=True)
    else:
        u = t - T_TD
        player(d, px, py + off - abs(math.sin(u * 9)) * 8, BLU, int(u * 8) % 2, "down")
        fireworks(d, u)
    secs = max(0, 4 - int(t / T_TD * 4)) if t < T_TD else 0
    fb_hud(d, sp, sp["home_score"] if t < T_TD else sp["home_score"] + 6, f"0:0{secs}", flash=t < T_TD and int(t * 4) % 2 == 0)
    hook_text(d, sp, t)
    if 1.5 <= t < 2.5: txt(d, (LW // 2, 62), "JUKE!", F(24), LBLU)
    elif 2.5 <= t < T_TD: txt(d, (LW // 2, 62), "GO! GO! GO!", F(16), YEL)
    if t >= T_TD:
        u = t - T_TD
        flash_title(d, u, "TOUCH", "DOWN!", sub=f"{sp['home']} WINS {sp['home_score'] + 6}-{sp['away_score']}")
    return img, (T_TD if t >= T_TD else None)

# ================================================================ FOOTBALL: field goal, two angles (fb_kick)
T_KICK, T_CUT_FG, T_GOOD = 1.35, 2.35, 3.25
HZ = 120  # horizon
def persp_y(k):  # k: 0 (horizon) .. 1 (bottom)
    return HZ + (LH - HZ) * k ** 1.7
def fb_kick_behind(t, sp):
    img = Image.new("RGB", (LW, LH), G1); d = ImageDraw.Draw(img)
    crowd(d, 34, HZ - 26, t, 3); d.rectangle((0, HZ - 26, LW, HZ), fill=NAVY)
    txt(d, (LW // 2, HZ - 13), " ".join(sp["home"]), F(8), WHT, sh=None)
    for i in range(14):  # stripes
        y0, y1 = persp_y(i / 14), persp_y((i + 1) / 14)
        if i % 2: d.rectangle((0, y0, LW, y1), fill=G2)
        d.line((0, y0, LW, y0), fill=WHT)
    d.polygon([(135 - 40, HZ), (135 + 40, HZ), (LW + 140, LH), (-140, LH)], outline=WHT)
    # goal post
    d.rectangle((134, HZ - 4, 136, HZ + 6), fill=YEL); d.rectangle((122, HZ - 5, 148, HZ - 4), fill=YEL)
    d.rectangle((122, HZ - 34, 123, HZ - 4), fill=YEL); d.rectangle((147, HZ - 34, 148, HZ - 4), fill=YEL)
    fr = int(t * 8) % 2
    # lines of players
    for i in range(7):
        player(d, 60 + i * 25, 246, sp["acol"], fr if t > 0.4 else 0, "down", num="", shadow=False)
    for i in range(7):
        player(d, 60 + i * 25, 290, BLU, 0, "up", num="", shadow=False)
    # holder
    hold = lambda dd, cx, fy: (dd.rectangle((cx - 6, fy - 10, cx + 6, fy), fill=BLU), dd.ellipse((cx - 4, fy - 17, cx + 4, fy - 9), fill=BLU))
    big(img, hold, 150, 395, 2, (24, 24))
    # ball
    if t < T_KICK:
        d.ellipse((132, 368, 140, 374), fill=BRN)
    elif t < T_CUT_FG:
        p = (t - T_KICK) / (T_CUT_FG - T_KICK + 0.6)
        bx = 136 + 4 * p; by = lerp(370, HZ - 40, p) - math.sin(math.pi * p) * 70
        r = max(2, int(5 * (1 - p)))
        d.ellipse((bx - r - 1, by - r - 1, bx + r + 1, by + r + 1), fill=BLK); d.ellipse((bx - r, by - r, bx + r, by + r), fill=BRN)
    # kicker (2x, back view), steps forward
    step = ease((t - 0.9) / (T_KICK - 0.9)) * 28
    leg = 1 if T_KICK - 0.05 < t < T_KICK + 0.35 else 0
    def kicker(dd, cx, fy):
        dd.rectangle((cx - 4, fy - 7, cx - 2, fy), fill=WHT)
        if leg: dd.rectangle((cx + 2, fy - 13, cx + 4, fy - 7), fill=WHT); dd.rectangle((cx + 2, fy - 15, cx + 4, fy - 13), fill=BLK)
        else: dd.rectangle((cx + 2, fy - 7, cx + 4, fy), fill=WHT)
        dd.rectangle((cx - 5, fy - 11, cx + 5, fy - 7), fill=GRY); dd.rectangle((cx - 6, fy - 19, cx + 6, fy - 11), fill=BLU)
        digits(dd, cx - 3, fy - 18, "3", WHT); digits(dd, cx + 1, fy - 18, "3", WHT)
        dd.ellipse((cx - 4, fy - 26, cx + 4, fy - 18), fill=BLU); dd.line((cx, fy - 26, cx, fy - 19), fill=WHT)
    big(img, kicker, 108 + step * 0.5, 478 - step, 2, (30, 32))
    d = ImageDraw.Draw(img)
    fb_hud(d, sp, sp["home_score"], "0:02" if t < T_KICK else "0:00", flash=int(t * 4) % 2 == 0)
    hook_text(d, sp, t, until=1.3)
    if 1.3 <= t < T_CUT_FG: txt(d, (LW // 2, 62), "IT'S UP...", F(16), YEL)
    return img

def fb_kick_posts(t, sp):
    """Reverse angle: camera behind the goal posts, ball coming at you."""
    img = Image.new("RGB", (LW, LH), G1); d = ImageDraw.Draw(img)
    hz = 210
    d.rectangle((0, 34, LW, hz), fill=(40, 40, 40)); crowd(d, 34, hz - 20, t, 11)
    d.rectangle((0, hz - 20, LW, hz), fill=DGRN)
    for i in range(10):
        y0 = hz + (LH - hz) * (i / 10) ** 1.6; y1 = hz + (LH - hz) * ((i + 1) / 10) ** 1.6
        if i % 2: d.rectangle((0, y0, LW, y1), fill=G2)
    d.rectangle((0, hz + 150, LW, LH), fill=NAVY)  # end zone close to camera
    txt(d, (LW // 2, hz + 200), " ".join(sp["home"]), F(24), WHT, sh=BLU)
    for i in range(7): player(d, 70 + i * 22, hz + 18, sp["acol"], 0, "up", num="", shadow=False)
    # posts (big, close)
    d.rectangle((131, 330, 139, LH), fill=YEL)
    d.rectangle((50, 326, 220, 334), fill=YEL)
    d.rectangle((50, 40, 58, 334), fill=YEL); d.rectangle((212, 40, 220, 334), fill=YEL)
    u = t - T_CUT_FG
    p = clamp(u / (T_GOOD - T_CUT_FG))
    if p < 1:
        bx = lerp(135, 150, p); by = lerp(hz - 10, 140, ease(p)); r = 2 + int(16 * p ** 1.5)
        d.ellipse((bx - r * 1.4 - 1, by - r - 1, bx + r * 1.4 + 1, by + r + 1), fill=BLK)
        d.ellipse((bx - r * 1.4, by - r, bx + r * 1.4, by + r), fill=BRN)
        d.line((bx - r * 0.6, by, bx + r * 0.6, by), fill=WHT, width=max(1, r // 5))
    # referee signals
    up = t >= T_GOOD
    rx, ry = 34, 460
    def ref(dd, cx, fy):
        dd.rectangle((cx - 4, fy - 7, cx - 2, fy), fill=BLK); dd.rectangle((cx + 2, fy - 7, cx + 4, fy), fill=BLK)
        dd.rectangle((cx - 6, fy - 19, cx + 6, fy - 8), fill=WHT)
        for k in range(-6, 7, 3): dd.line((cx + k, fy - 19, cx + k, fy - 8), fill=BLK)
        if up:
            dd.rectangle((cx - 9, fy - 32, cx - 7, fy - 17), fill=WHT); dd.rectangle((cx + 7, fy - 32, cx + 9, fy - 17), fill=WHT)
        dd.ellipse((cx - 4, fy - 26, cx + 4, fy - 18), fill=SKIN); dd.rectangle((cx - 4, fy - 27, cx + 4, fy - 24), fill=BLK)
    big(img, ref, rx, ry, 2, (24, 36))
    d = ImageDraw.Draw(img)
    fb_hud(d, sp, sp["home_score"] + (3 if up else 0), "0:00")
    if not up: txt(d, (LW // 2, 62), "IS IT GOOD?", F(16), YEL)
    else:
        u2 = t - T_GOOD
        fireworks(d, u2, ((70, 90, 0.0), (200, 110, 0.3), (135, 70, 0.6)))
        flash_title(d, u2, "IT'S", "GOOD!", y=150, sub=f"{sp['home']} WINS {sp['home_score'] + 3}-{sp['away_score']}")
    return img

def fb_kick(t, sp):
    if t < T_CUT_FG: return fb_kick_behind(t, sp), None
    return fb_kick_posts(t, sp), (T_GOOD if t >= T_GOOD else None)

# ================================================================ BASEBALL: walk-off homer, two angles (bb_homer)
T_PITCH, T_HIT, T_CUT_BB, T_HR = 0.75, 1.45, 2.5, 4.0
def bb_hud(d, sp, home, inning="BOT 9TH"):
    d.rectangle((0, 0, LW, 34), fill=BLK); d.line((0, 34, LW, 34), fill=WHT)
    txt(d, (8, 10), sp["home"], F(8), LBLU, "lm", None); txt(d, (46, 10), f"{home}", F(8), WHT, "lm", None)
    txt(d, (LW - 8, 10), sp["away"], F(8), ORG, "rm", None); txt(d, (LW - 46, 10), f"{sp['away_score']}", F(8), WHT, "rm", None)
    txt(d, (LW // 2, 10), inning, F(8), YEL, "mm", None)
    txt(d, (LW // 2 - 30, 24), "B3 S2", F(8), WHT, "mm", None)
    d.ellipse((LW // 2 + 18, 20, LW // 2 + 25, 27), fill=RED); d.ellipse((LW // 2 + 30, 20, LW // 2 + 37, 27), fill=RED)
    txt(d, (LW // 2 + 52, 24), "OUT", F(6), WHT, "mm", None)

def bb_catcher_view(t, sp):
    img = Image.new("RGB", (LW, LH), G1); d = ImageDraw.Draw(img)
    crowd(d, 34, 104, t, 5); d.rectangle((0, 104, LW, 116), fill=DGRN); d.line((0, 116, LW, 116), fill=YEL)
    txt(d, (LW // 2, 110), "OUTTA NOWHERE CARDS", F(6), WHT, sh=None)
    for i in range(0, 8):
        if i % 2: d.rectangle((0, 116 + i * 16, LW, 132 + i * 16), fill=G2)
    d.polygon([(135, 196), (262, 336), (135, 480), (8, 336)], fill=DIRT)  # infield dirt
    d.polygon([(135, 226), (226, 334), (135, 444), (44, 334)], fill=G1)   # infield grass
    d.ellipse((115, 250, 155, 270), fill=DIRT); d.rectangle((129, 258, 141, 261), fill=WHT)  # mound + rubber
    for bx, by in ((226, 334), (135, 210), (44, 334)): d.rectangle((bx - 4, by - 3, bx + 4, by + 3), fill=WHT)
    d.line((135, 444, 262, 300), fill=WHT); d.line((135, 444, 8, 300), fill=WHT)
    d.polygon([(127, 446), (143, 446), (143, 452), (135, 458), (127, 452)], fill=WHT)  # plate
    # pitcher (faces camera)
    wind = clamp(t / T_PITCH)
    player(d, 135, 262 - (3 if wind > 0.5 and t < T_PITCH else 0), sp["acol"], 1 if 0.4 < wind < 1 else 0, "down", num="", shadow=False)
    # ball
    if T_PITCH <= t < T_HIT:
        p = (t - T_PITCH) / (T_HIT - T_PITCH); bx, by = lerp(140, 136, p), lerp(250, 436, p ** 1.3); r = 1 + int(3 * p)
        d.ellipse((bx - r, by - r, bx + r, by + r), fill=WHT)
    elif t >= T_HIT:
        p = clamp((t - T_HIT) / (T_CUT_BB - T_HIT)); bx, by = lerp(136, 172, p), lerp(430, -10, p ** 0.7); r = max(1, int(4 - 3 * p))
        d.ellipse((bx - r, by - r, bx + r, by + r), fill=WHT)
    # batter (2x, left-handed box), bat swings around at the hit
    sw = clamp((t - (T_HIT - 0.1)) / 0.2)
    def batter(dd, cx, fy):
        dd.rectangle((cx - 5, fy - 8, cx - 2, fy), fill=GRY); dd.rectangle((cx + 2, fy - 8, cx + 5, fy), fill=GRY)
        dd.rectangle((cx - 5, fy - 1, cx - 2, fy), fill=BLK); dd.rectangle((cx + 2, fy - 1, cx + 5, fy), fill=BLK)
        dd.rectangle((cx - 6, fy - 19, cx + 6, fy - 8), fill=BLU); digits(dd, cx - 3, fy - 18, "24", WHT)
        dd.ellipse((cx - 5, fy - 27, cx + 5, fy - 18), fill=NAVY); dd.rectangle((cx - 6, fy - 22, cx - 3, fy - 20), fill=NAVY)
        hx, hy = cx + 6, fy - 17
        ang = math.radians(-120 + 230 * sw)
        dd.line((hx, hy, hx + 16 * math.cos(ang), hy + 16 * math.sin(ang)), fill=(220, 180, 120), width=2)
        dd.rectangle((hx - 2, hy - 1, hx + 1, hy + 2), fill=SKIN)
    big(img, batter, 100, 470, 2, (48, 40))
    # catcher + ump (back view, crouched, cut off by bottom edge)
    def catcher(dd, cx, fy):
        dd.rectangle((cx - 7, fy - 9, cx + 7, fy), fill=GRY); dd.ellipse((cx - 5, fy - 16, cx + 5, fy - 7), fill=sp["acol"])
        dd.rectangle((cx + 6, fy - 12, cx + 10, fy - 8), fill=BRN)
    big(img, catcher, 142, 492, 2, (26, 20))
    d = ImageDraw.Draw(img)
    bb_hud(d, sp, sp["home_score"])
    hook_text(d, sp, t, until=T_HIT - 0.05, y=150)
    if T_HIT <= t < T_HIT + 0.07: d.rectangle((0, 0, LW, LH), fill=WHT)
    if t >= T_HIT:
        txt(d, (LW // 2, 160), "CRACK!", F(24), YEL)
        if t > T_HIT + 0.4: txt(d, (LW // 2, 190), "IT'S HIGH...", F(12), WHT)
    return img

def bb_outfield_view(t, sp):
    """Reverse angle: behind the outfielder, ball sailing toward the wall."""
    img = Image.new("RGB", (LW, LH), G1); d = ImageDraw.Draw(img)
    crowd(d, 34, 150, t, 9, 6)
    d.rectangle((0, 150, LW, 178), fill=DGRN); d.line((0, 150, LW, 150), fill=YEL)
    for i, x in enumerate(range(10, LW, 64)):
        d.rectangle((x, 156, x + 50, 172), fill=[NAVY, DRED, NAVY, DRED][i % 4])
    txt(d, (42, 164), "ONC", F(8), WHT, sh=None); txt(d, (170, 164), "400", F(8), WHT, sh=None)
    d.rectangle((0, 178, LW, 204), fill=DIRT)  # warning track
    for i in range(0, 18):
        if i % 2: d.rectangle((0, 204 + i * 16, LW, 220 + i * 16), fill=G2)
    u = t - T_CUT_BB
    p = clamp(u / (T_HR - T_CUT_BB))
    # outfielder runs back toward the wall, jumps
    fy = lerp(420, 214, ease(p * 1.1)); jump = 0
    if p > 0.82: jump = math.sin(clamp((p - 0.82) / 0.25) * math.pi) * 22
    def fielder(dd, cx, fyy):
        f = int(t * 10) % 2 if p < 0.82 else 0
        dd.rectangle((cx - 4, fyy - 7 + (-2 if f else 0), cx - 2, fyy - 1), fill=GRY); dd.rectangle((cx + 2, fyy - 7 + (0 if f else -2), cx + 4, fyy - 1), fill=GRY)
        dd.rectangle((cx - 6, fyy - 19, cx + 6, fyy - 8), fill=sp["acol"])
        dd.ellipse((cx - 5, fyy - 27, cx + 5, fyy - 18), fill=sp["acol"])
        if p > 0.8: dd.rectangle((cx + 6, fyy - 34, cx + 8, fyy - 17), fill=sp["acol"]); dd.rectangle((cx + 4, fyy - 39, cx + 10, fyy - 33), fill=BRN)
    if t < T_HR + 0.6:
        d.ellipse((150 - 9, fy - 3, 150 + 9, fy + 3), fill=(0, 100, 0))
        big(img, fielder, 150, fy - jump, 2, (30, 44)); d = ImageDraw.Draw(img)
    # ball: from behind the camera, high, shrinking toward the seats
    if t < T_HR + 0.5:
        q = clamp(u / (T_HR + 0.4 - T_CUT_BB))
        bx, by = lerp(110, 170, q), lerp(520, 95, q) - math.sin(math.pi * q) * 40
        r = max(1, int(9 * (1 - q) + 1))
        sx, sy = lerp(110, 168, q), lerp(470, 160, q)
        if sy > 178: d.ellipse((sx - r, sy - r / 2, sx + r, sy + r / 2), fill=(0, 100, 0))
        d.ellipse((bx - r, by - r, bx + r, by + r), fill=WHT); d.arc((bx - r, by - r, bx + r, by + r), 200, 300, fill=RED)
    hr = t >= T_HR
    bb_hud(d, sp, sp["home_score"] + (2 if hr else 0))
    if not hr:
        txt(d, (LW // 2, 252), "BACK...", F(16), YEL)
        if p > 0.4: txt(d, (LW // 2, 276), "BACK...", F(16), YEL)
        if p > 0.7: txt(d, (LW // 2, 300), "GONE?!", F(16), WHT)
    else:
        u2 = t - T_HR; fireworks(d, u2, ((60, 80, 0.0), (210, 100, 0.3), (135, 60, 0.6)))
        flash_title(d, u2, "HOME", "RUN!", y=250, sub=f"{sp['home']} WINS {sp['home_score'] + 2}-{sp['away_score']}")
    return img

def bb_homer(t, sp):
    if t < T_CUT_BB: return bb_catcher_view(t, sp), None
    return bb_outfield_view(t, sp), (T_HR if t >= T_HR else None)

# ================================================================ FOOTBALL: Hail Mary, two angles (fb_pass)
T_SNAP, T_THROW, T_CUT_PASS, T_CATCH = 0.35, 1.75, 2.6, 3.55
LOS = 45 * YD  # line of scrimmage, field units (0 = goal line)
def _qb_x(t):
    return 135 - 34 * ease((t - 1.15) / 0.3)   # scramble left away from the free rusher
def _qb_y(t):
    return LOS + 10 + 30 * ease((t - T_SNAP) / 0.6) - 8 * ease((t - 1.15) / 0.3)
_TGT = (150, -EZ // 2)
def _ball(t):
    """Ball after the throw: ground position + height (overhead view)."""
    p = clamp((t - T_THROW) / 1.0)
    bx = lerp(_qb_x(T_THROW) + 8, _TGT[0], p); by = lerp(_qb_y(T_THROW) - 14, _TGT[1], p)
    return bx, by, math.sin(math.pi * p) * 70, p

def fb_pass_overhead(t, sp):
    ball = _ball(t) if t >= T_THROW else None
    cam = _qb_y(t) - 10 if ball is None else lerp(_qb_y(T_THROW) - 10, max(ball[1] + 80, 70), ease((t - T_THROW) / 0.35))
    img, d, off = fb_field(cam, t, sp); fr = int(t * 10) % 2; ac = sp["acol"]; go = t > T_SNAP
    run = lambda t0, spd: max(0.0, t - t0) * spd
    # receivers sprint upfield, safeties backpedal then turn and run
    for k, (wx, num) in enumerate([(30, "81"), (232, "88"), (190, "11")]):
        wy = LOS - 4 - run(T_SNAP, 150 + 12 * k)
        wy = max(wy, -EZ + 14 + 10 * k)
        player(d, wx + (_TGT[0] - wx) * ease((t - 1.9) / 0.8) * 0.7, wy + off, BLU, fr ^ k if go else 0, "up", num=num)
        dy = LOS - 70 - run(T_SNAP + 0.2, 140 + 10 * k); dy = max(dy, -EZ + 6 + 8 * k)
        player(d, wx + 10 + (_TGT[0] - wx) * ease((t - 1.9) / 0.8) * 0.6, dy + off, ac, fr ^ k ^ 1 if go else 0, "up" if t > 1.0 else "down", num="")
    # lines
    push = 4 * math.sin(t * 9) if go else 0
    for i in range(5):
        player(d, 87 + i * 24, LOS + 8 + off + (push if i % 2 else -push) * 0.5, BLU, fr if go else 0, "up", num="", shadow=False)
    for i in range(4):
        if i == 3 and go:  # free rusher loops around and lunges at the QB, misses
            rx = lerp(200, _qb_x(1.1) + 26, ease((t - T_SNAP) / 0.85)); ry = lerp(LOS - 4, _qb_y(1.1), ease((t - T_SNAP) / 0.85))
            if t < 1.25: player(d, rx, ry + off, ac, fr, "down", num="")
            else: diver(d, rx - 6 - ease((t - 1.25) / 0.3) * 10, ry + off + 4, ac, True)
            continue
        player(d, 99 + i * 24, LOS - 4 + off + (push if i % 2 else -push) * 0.5, ac, fr if go else 0, "down", num="", shadow=False)
    # QB
    qx, qy = _qb_x(min(t, T_THROW)), _qb_y(min(t, T_THROW))
    player(d, qx, qy + off, BLU, fr if T_SNAP < t < T_THROW else 0, "up", ball=t < T_THROW, num="12")
    if T_THROW - 0.05 < t < T_THROW + 0.25:  # throwing arm
        d.rectangle((qx + 6, qy + off - 27, qx + 8, qy + off - 17), fill=SKIN)
    if ball:
        bx, by, h, p = ball; r = 3 + int(h / 20)
        d.ellipse((bx - 3, by + off - 1, bx + 3, by + off + 2), fill=(0, 100, 0))
        d.ellipse((bx - r - 1, by + off - h - r, bx + r + 1, by + off - h + r - 1), fill=BLK)
        d.ellipse((bx - r, by + off - h - r + 1, bx + r, by + off - h + r - 2), fill=BRN)
        d.point((bx, by + off - h), fill=WHT)
    secs = 4 if t < T_SNAP else max(0, 4 - int((t - T_SNAP) / (T_THROW - T_SNAP) * 4))
    fb_hud(d, sp, sp["home_score"], f"0:0{secs}", flash=int(t * 4) % 2 == 0)
    hook_text(d, sp, t, until=1.15)
    if 1.15 <= t < T_THROW: txt(d, (LW // 2, 62), "SCRAMBLE!", F(16), LBLU)
    elif t >= T_THROW: txt(d, (LW // 2, 62), "HAIL MARY!", F(16), YEL)
    return img

def _leaper(col, num, arms_up, catch=False):
    def fn(dd, cx, fy):
        dd.rectangle((cx - 4, fy - 7, cx - 2, fy), fill=WHT); dd.rectangle((cx + 2, fy - 7, cx + 4, fy), fill=WHT)
        dd.rectangle((cx - 4, fy - 1, cx - 2, fy), fill=BLK); dd.rectangle((cx + 2, fy - 1, cx + 4, fy), fill=BLK)
        dd.rectangle((cx - 5, fy - 11, cx + 5, fy - 7), fill=GRY); dd.rectangle((cx - 6, fy - 19, cx + 6, fy - 11), fill=col)
        if num: digits(dd, cx - 1 if len(num) == 1 else cx - 3, fy - 18, num, WHT)
        if arms_up:
            dd.rectangle((cx - 8, fy - 31, cx - 6, fy - 17), fill=col); dd.rectangle((cx + 6, fy - 31, cx + 8, fy - 17), fill=col)
            dd.rectangle((cx - 8, fy - 33, cx - 6, fy - 31), fill=SKIN); dd.rectangle((cx + 6, fy - 33, cx + 8, fy - 31), fill=SKIN)
            if catch:
                dd.ellipse((cx - 5, fy - 36, cx + 5, fy - 30), fill=BRN); dd.point((cx, fy - 33), fill=WHT)
        else:
            dd.rectangle((cx - 8, fy - 18, cx - 7, fy - 12), fill=col); dd.rectangle((cx + 7, fy - 18, cx + 8, fy - 12), fill=col)
        dd.ellipse((cx - 4, fy - 26, cx + 4, fy - 18), fill=col); dd.line((cx, fy - 26, cx, fy - 19), fill=WHT)
    return fn

def fb_pass_endzone(t, sp):
    """Reverse angle from the back of the end zone: ball drops in, jump ball, catch."""
    img = Image.new("RGB", (LW, LH), G1); d = ImageDraw.Draw(img); hz = 170
    crowd(d, 34, hz - 16, t, 5); d.rectangle((0, hz - 16, LW, hz), fill=DGRN)
    for i in range(10):
        y0 = hz + (LH - hz) * (i / 10) ** 1.6; y1 = hz + (LH - hz) * ((i + 1) / 10) ** 1.6
        if i % 2: d.rectangle((0, y0, LW, y1), fill=G2)
        d.line((0, y0, LW, y0), fill=WHT)
    d.rectangle((0, 300, LW, LH), fill=NAVY); d.line((0, 300, LW, 300), fill=WHT, width=2)
    txt(d, (LW // 2, 440), " ".join(sp["home"]), F(24), WHT, sh=BLU)
    u = t - T_CUT_PASS; caught = t >= T_CATCH
    jump = lambda t0: math.sin(math.pi * clamp((t - t0) / 0.75)) * 34
    ground = 392
    # two defenders and the receiver going up for it (backs to the camera)
    for x, t0, num in [(92, 3.0, ""), (182, 3.05, "")]:
        big(img, _leaper(sp["acol"], num, t > 2.85), x, ground - jump(t0), 2, (24, 40))
    rj = jump(3.15) if not caught else max(jump(3.15), 0)
    big(img, _leaper(BLU, "81", t > 2.95, catch=caught and t < 4.2), 137, ground - 6 - rj, 2, (24, 40))
    d = ImageDraw.Draw(img)
    if not caught:  # ball dropping toward the pile, growing as it nears the camera
        p = clamp(u / (T_CATCH - T_CUT_PASS)); r = 2 + int(5 * p)
        bx = lerp(140, 137, p); by = lerp(hz - 40, ground - 6 - jump(3.15) - 68, ease(p))
        d.ellipse((bx - r * 1.4 - 1, by - r - 1, bx + r * 1.4 + 1, by + r + 1), fill=BLK)
        d.ellipse((bx - r * 1.4, by - r, bx + r * 1.4, by + r), fill=BRN)
        txt(d, (LW // 2, 62), "JUMP BALL!", F(16), YEL)
    fb_hud(d, sp, sp["home_score"] + (6 if caught else 0), "0:00")
    if caught:
        u2 = t - T_CATCH
        fireworks(d, u2, ((60, 80, 0.0), (210, 100, 0.3), (135, 60, 0.6)))
        flash_title(d, u2, "TOUCH", "DOWN!", y=210, sub=f"{sp['home']} WINS {sp['home_score'] + 6}-{sp['away_score']}")
    return img

def fb_pass(t, sp):
    if t < T_CUT_PASS: return fb_pass_overhead(t, sp), None
    return fb_pass_endzone(t, sp), (T_CATCH if t >= T_CATCH else None)

GAMES = {"fb_pass": fb_pass, "fb_run": fb_run, "fb_kick": fb_kick, "bb_homer": bb_homer}

# ================================================================ pack rip (shared)
def pixel_card(d, x, y, kind, sport, w=56, h=78):
    x, y = int(x - w / 2), int(y - h / 2)
    if kind == "back":
        cb = Image.new("RGB", (w + 1, h + 1), NAVY); cbd = ImageDraw.Draw(cb)
        for i in range(0, w + h, 8): cbd.line((i, 0, 0, i), fill=BLU)
        cbd.rectangle((0, 0, w, h), outline=GOLD, width=2)
        d._image.paste(cb, (x, y)); txt(d, (x + w // 2, y + h // 2), "?", F(24), WHT); return
    body = {"b1": (LBLU, BLU), "b2": (GRY, DGRY), "gold": (GOLD, YEL)}[kind]
    d.rectangle((x, y, x + w, y + h), fill=body[0], outline=WHT if kind != "gold" else (252, 252, 168), width=2)
    d.rectangle((x + 5, y + 5, x + w - 5, y + h - 20), fill=body[1])
    cx, cy = x + w // 2, y + 18
    d.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=BLK); d.rectangle((cx - 9, cy + 6, cx + 9, cy + 26), fill=BLK)
    if sport == "bb": d.line((cx + 9, cy + 9, cx + 18, cy - 8), fill=(220, 180, 120), width=3)
    else: d.rectangle((cx + 9, cy + 8, cx + 14, cy + 11), fill=BRN)
    d.rectangle((x + 2, y + h - 16, x + w - 2, y + h - 3), fill=BLK if kind != "gold" else DRED)
    txt(d, (x + w // 2, y + h - 9), "RC AUTO" if kind == "gold" else "BASE", F(6), GOLD if kind == "gold" else WHT, sh=None)
    if kind == "gold":
        d.line([(x + 10, y + h - 26), (x + 16, y + h - 32), (x + 22, y + h - 24), (x + 30, y + h - 31), (x + 38, y + h - 25), (x + 46, y + h - 29)], fill=NAVY, width=2)

def scene_pack(t, sp):
    sport = "bb" if sp["variant"].startswith("bb") else "fb"
    img = Image.new("RGB", (LW, LH), (24, 24, 56)); d = ImageDraw.Draw(img)
    rnd = random.Random(4)
    for _ in range(60):
        sx, sy = rnd.randint(0, LW), rnd.randint(40, 300)
        if (int(t * 6) + sx) % 7: d.point((sx, sy), fill=GRY)
    d.rectangle((0, 330, LW, LH), fill=BRN); d.rectangle((0, 330, LW, 334), fill=(180, 100, 30))
    for x in range(0, LW, 18): d.line((x, 336, x - 30, LH), fill=(110, 56, 0))
    cx, cy = LW // 2, 230; u = t - T_PACK; pl = sp["pack_label"]
    if t < T_RIP:
        shake = int(math.sin(t * 50) * (1 + 3 * clamp(u / 1.1))); x0, y0 = cx - 34 + shake, cy - 50
        d.rectangle((x0, y0, x0 + 68, y0 + 100), fill=PUR)
        for k in range(0, 68, 6): d.line((x0 + k, y0, x0 + k, y0 + 100), fill=DPUR)
        d.rectangle((x0, y0, x0 + 68, y0 + 12), fill=DPUR); d.rectangle((x0, y0 + 90, x0 + 68, y0 + 100), fill=DPUR)
        txt(d, (cx + shake, cy - 10), pl[0], fit(pl[0], 62, 8), WHT); txt(d, (cx + shake, cy + 6), pl[1], fit(pl[1], 62, 8), YEL)
        g = int(((t * 1.5) % 1.0) * 100)
        if 20 <= g <= 68: d.line((x0 + g, y0 + 14, x0 + g - 20, y0 + 88), fill=WHT, width=2)
        txt(d, (LW // 2, 90), "NOW DO IT", F(16), WHT); txt(d, (LW // 2, 114), "WITH CARDS.", F(16), YEL)
        if u > 0.6: txt(d, (LW // 2, 380), "RIP IT...", F(16), LBLU)
    else:
        v = t - T_RIP
        if v < 0.6:
            tx, ty = cx + 120 * v, cy - 50 - 200 * v + 300 * v * v; d.rectangle((tx - 34, ty, tx + 34, ty + 12), fill=DPUR)
        x0, y0 = cx - 34, cy - 38 + int(160 * ease((v - 0.3) / 0.6))
        if t < T_FLIP:
            rise = int(46 * ease(v / 0.3)); order = ["b1", "b2", "back"]
            n_gone = 0 if v < 0.55 else 1 if v < 0.95 else 2
            for k in range(2, n_gone - 1, -1):
                pixel_card(d, cx + (k - n_gone), cy - 30 - rise + (k - n_gone) * 2, order[k], sport)
            for k in range(n_gone):
                q = ease((v - (0.55 if k == 0 else 0.95)) / 0.3)
                pixel_card(d, cx + (-1 if k == 0 else 1) * 160 * q, cy - 30 - rise, order[k], sport)
            d.rectangle((x0, y0, x0 + 68, y0 + 88), fill=PUR)
            for k in range(0, 68, 6): d.line((x0 + k, y0, x0 + k, y0 + 88), fill=DPUR)
            for k in range(0, 68, 8): d.polygon([(x0 + k, y0), (x0 + k + 4, y0 - 4), (x0 + k + 8, y0)], fill=PUR)
            d.rectangle((x0, y0 + 78, x0 + 68, y0 + 88), fill=DPUR)
            if v < 0.25:
                for i in range(8):
                    a = i * 0.785
                    d.line((cx + 30 * math.cos(a), cy - 50 + 20 * math.sin(a), cx + 50 * math.cos(a), cy - 50 + 34 * math.sin(a)), fill=YEL, width=2)
            if v < 0.5: txt(d, (LW // 2, 90), "RIIIP!", F(24), YEL)
            elif v < 1.3: txt(d, (LW // 2, 90), "BASE...", F(16), GRY)
            else: txt(d, (LW // 2, 90), "WAIT FOR IT...", F(12), WHT)
        else:
            w = t - T_FLIP; flip = clamp(w / 0.25); kind = "back" if flip < 0.5 else "gold"
            sc = abs(1 - flip * 2) if flip < 1 else 1; bigc = 1 + 0.5 * ease((w - 0.25) / 0.3)
            cw, ch = int(56 * bigc * max(sc, 0.05)), int(78 * bigc)
            if kind == "gold":
                for i in range(12):
                    a = i * 0.5236 + w * 1.5
                    d.polygon([(cx, cy - 40), (cx + 140 * math.cos(a), cy - 40 + 140 * math.sin(a)),
                               (cx + 140 * math.cos(a + 0.2), cy - 40 + 140 * math.sin(a + 0.2))], fill=(64, 52, 20))
            card = Image.new("RGB", (60, 82), (0, 0, 0)); pixel_card(ImageDraw.Draw(card), 30, 41, kind, sport)
            m = Image.new("L", (60, 82), 0); ImageDraw.Draw(m).rectangle((2, 2, 58, 80), fill=255)
            card = card.resize((max(1, cw), ch), Image.NEAREST); m = m.resize((max(1, cw), ch), Image.NEAREST)
            img.paste(card, (cx - cw // 2, cy - 40 - ch // 2), m); d = ImageDraw.Draw(img)
            if kind == "gold":
                rnd2 = random.Random(int(t * 12))
                for _ in range(10):
                    sx = cx + rnd2.randint(-70, 70); sy = cy - 40 + rnd2.randint(-90, 90)
                    d.line((sx - 3, sy, sx + 3, sy), fill=WHT); d.line((sx, sy - 3, sx, sy + 3), fill=WHT)
                txt(d, (LW // 2, 70), "BIG HIT!", F(24), [YEL, WHT, GOLD, PINK][int(w * 10) % 4])
                if w > 0.5:
                    txt(d, (LW // 2, 372), "THAT FEELING?", F(12), WHT); txt(d, (LW // 2, 394), "WE RIP FOR IT", F(12), YEL)
                    txt(d, (LW // 2, 416), "LIVE.", F(12), YEL)
    return img

# ================================================================ title screen (shared)
_logo = None
def pixel_logo(size=150):
    global _logo
    if _logo is None:
        lg = Image.open(os.path.join(ROOT, "brand", "logo.png")).convert("RGBA"); lg.thumbnail((size, size), Image.LANCZOS)
        a = lg.getchannel("A").point(lambda v: 255 if v > 110 else 0)
        _logo = (lg.convert("RGB").quantize(colors=10, dither=Image.Dither.NONE).convert("RGB"), a)
    return _logo

def scene_end(t, sp):
    img = Image.new("RGB", (LW, LH), BLK); d = ImageDraw.Draw(img); u = t - T_END
    rnd = random.Random(9)
    for _ in range(80):
        sx, sy, spd = rnd.randint(0, LW), rnd.randint(0, LH), rnd.uniform(20, 80)
        d.point((sx, (sy + spd * u) % LH), fill=WHT if spd > 50 else DGRY)
    banner = sp["end"].get("banner")
    rgb, a = pixel_logo(130 if banner else 150)
    drop = int(-200 * (1 - ease(u / 0.5))) + int(4 * math.sin(u * 4))
    img.paste(rgb, ((LW - rgb.width) // 2, 36 + drop), a); d = ImageDraw.Draw(img)
    y = 200 if banner else 220
    if u > 0.5: txt(d, (LW // 2, y), "OUTTA NOWHERE", F(16), WHT); txt(d, (LW // 2, y + 24), "CARDS", F(16), YEL)
    lines = sp["end"].get("lines", ["LIVE BREAKS ON", "WHATNOT"])
    if u > 0.9:
        txt(d, (LW // 2, y + 64), lines[0], fit(lines[0], LW - 20, 8), LBLU)
        if len(lines) > 1: txt(d, (LW // 2, y + 82), lines[1], fit(lines[1], LW - 20, 16), WHT)
    if banner and u > 1.1:
        d.rectangle((14, y + 104, LW - 14, y + 150), fill=DRED, outline=YEL, width=2)
        txt(d, (LW // 2, y + 116), banner[0], fit(banner[0], LW - 40, 8), YEL, sh=None)
        txt(d, (LW // 2, y + 136), banner[1], fit(banner[1], LW - 40, 12), WHT, sh=None)
    yb = y + 170 if banner else 360
    if u > 1.3 and int(u * 2.5) % 2 == 0: txt(d, (LW // 2, yb), "PRESS FOLLOW", F(12), YEL)
    if u > 1.6:
        d.rectangle((40, yb + 32, LW - 40, yb + 60), fill=NAVY, outline=WHT); txt(d, (LW // 2, yb + 46), "ON-CARDS.COM", F(12), WHT, sh=None)
    txt(d, (LW // 2, 466), "INSERT CARDS TO CONTINUE", F(6), DGRY, sh=None)
    return img

def wipe(img, t):
    v = (t - T_WIPE) / (T_PACK - T_WIPE)
    if 0 <= v < 1:
        d = ImageDraw.Draw(img); k = v * 2 if v < 0.5 else (1 - v) * 2
        for i in range(0, LH, 16):
            w = int(LW * k)
            if (i // 16) % 2: d.rectangle((0, i, w, i + 16), fill=BLK)
            else: d.rectangle((LW - w, i, LW, i + 16), fill=BLK)
    return img

def cut_flash(img, t, cuts):
    for c in cuts:
        if c <= t < c + 0.05: ImageDraw.Draw(img).rectangle((0, 0, LW, LH), fill=BLK)
    return img

def scanlines(img):
    a = np.asarray(img.resize((W, H), Image.NEAREST)).astype(np.int16)
    a[3::4] = (a[3::4] * 0.72).astype(np.int16)
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))

def render(t, sp):
    if t < (T_WIPE + T_PACK) / 2:
        img, _ = GAMES[sp["variant"]](t, sp)
        img = cut_flash(img, t, {"fb_kick": [T_CUT_FG], "fb_pass": [T_CUT_PASS], "bb_homer": [T_CUT_BB]}.get(sp["variant"], []))
    elif t < T_END: img = scene_pack(t, sp)
    else: img = scene_end(t, sp)
    if T_WIPE <= t < T_PACK: img = wipe(img, t)
    if T_END - 0.15 < t < T_END: img = Image.new("RGB", (LW, LH), WHT)
    return scanlines(img)

# ================================================================ chiptune (original)
SR = 44100
def hz(n): return 440 * 2 ** ((n - 69) / 12)
def sq(n, dur, vol, duty=0.5, slide=0.0):
    t = np.arange(int(dur * SR)) / SR; f = hz(n) * (1 + slide * t / max(dur, 1e-6))
    ph = np.cumsum(f) / SR % 1.0; s = np.where(ph < duty, 1.0, -1.0)
    return s * np.minimum(1, t / 0.004) * np.clip(1 - t / dur * 0.35, 0, 1) * np.minimum(1, (dur - t) / 0.01).clip(0) * vol
def tri(n, dur, vol):
    t = np.arange(int(dur * SR)) / SR; ph = hz(n) * t % 1.0
    return np.round((4 * np.abs(ph - 0.5) - 1) * 8) / 8 * np.minimum(1, (dur - t) / 0.01).clip(0) * vol
_rng = np.random.default_rng(7)
def noise(dur, vol, decay=0.06, period=1):
    n = int(dur * SR); s = np.repeat(_rng.choice([-1.0, 1.0], n // period + 1), period)[:n]
    return s * np.exp(-np.arange(n) / SR / decay) * vol
def add(buf, sig, t0):
    i = int(t0 * SR); j = min(len(buf), i + len(sig))
    if 0 <= i < len(buf): buf[i:j] += sig[: j - i]

FB_MEL = [(72, 1), (72, .5), (74, .5), (76, 1), (72, 1), (79, 1.5), (77, .5), (76, 1), (74, 1),
          (76, 1), (76, .5), (77, .5), (79, 1), (81, 1), (79, 1), (76, 1), (74, 2)]
BB_MEL = [(67, 1), (72, 1), (76, 1), (79, 2), (76, 1), (79, 3), (74, 1), (77, 1), (81, 1), (79, 2), (77, 1), (76, 3)]  # 3/4 ballpark-organ feel

def make_audio(path, sp, payoff):
    buf = np.zeros(int((DUR + 0.3) * SR)); bb = sp["variant"].startswith("bb")
    bpm = 160 if bb else 150; b = 60 / bpm; e = b / 2
    mel = BB_MEL if bb else FB_MEL
    end_game = payoff
    t = 0.0
    while t < end_game - 0.05:
        for n, d_ in mel:
            if t >= end_game - 0.05: break
            dd = min(d_ * b, end_game - t); add(buf, sq(n, dd * 0.9, 0.10, 0.5 if bb else 0.25), t)
            if bb: add(buf, sq(n - 12, dd * 0.9, 0.04, 0.5), t)
            t += d_ * b
    bass = [48, 55, 52, 55, 53, 57, 55, 50]
    t = 0.0; k = 0
    while t < end_game:
        if bb:  # oom-pah-pah
            add(buf, tri(bass[(k // 3) % 8] - (12 if k % 3 == 0 else 0), b * 0.5, 0.22 if k % 3 == 0 else 0.12), t); t += b
        else:
            add(buf, tri(bass[(k // 2) % 8] - 12 if k % 2 == 0 else bass[(k // 2) % 8], e * 0.9, 0.22), t)
            add(buf, noise(0.03, 0.05, 0.01), t + e / 2)
            if k % 4 == 2: add(buf, noise(0.12, 0.10, 0.05, 3), t)
            t += e
        k += 1
    v = sp["variant"]
    if v == "fb_run":
        for tj in (0.85, 2.05): add(buf, sq(84, 0.12, 0.06, 0.125, slide=0.8), tj)
    if v == "fb_pass":
        add(buf, noise(0.06, 0.15, 0.02, 2), T_SNAP); add(buf, sq(84, 0.12, 0.06, 0.125, slide=0.8), 1.2)
        add(buf, sq(70, 0.8, 0.05, 0.125, slide=0.7), T_THROW); add(buf, sq(84, 0.4, 0.05, 0.125, slide=-0.3), T_CUT_PASS)
        add(buf, noise(0.08, 0.2, 0.03, 2), T_CATCH)
    if v == "fb_kick":
        add(buf, noise(0.08, 0.2, 0.03, 2), T_KICK); add(buf, sq(76, 0.9, 0.05, 0.125, slide=0.6), T_KICK + 0.05)
        add(buf, sq(84, 0.4, 0.05, 0.125, slide=-0.3), T_CUT_FG)
    if v == "bb_homer":
        add(buf, noise(0.15, 0.25, 0.04, 1), T_HIT); add(buf, sq(88, 0.12, 0.08, 0.5), T_HIT)
        add(buf, sq(72, 1.0, 0.05, 0.125, slide=0.9), T_HIT + 0.05)
    fan = [(60, .1), (64, .1), (67, .1), (72, .1), (76, .1), (79, .1), (84, .45), (79, .12), (84, .7)]
    t = payoff
    for n, d_ in fan: add(buf, sq(n, d_ * 0.95, 0.13, 0.5), t); add(buf, sq(n - 12, d_ * 0.95, 0.06, 0.25), t); t += d_
    add(buf, tri(48, 1.0, 0.25), payoff + 0.6); add(buf, noise(min(1.6, T_WIPE - payoff + 0.3), 0.06, 0.9, 6), payoff)
    add(buf, noise(0.4, 0.06, 0.2, 2), T_WIPE)
    t = T_PACK; k = 0
    while t < T_RIP:
        add(buf, tri(43, e * 0.8, 0.22), t); add(buf, sq(67 + (k % 4) * 2 + k // 4, e * 0.6, 0.06, 0.125), t); t += e; k += 1
    add(buf, noise(0.35, 0.16, 0.12, 1), T_RIP)
    for tb in (T_RIP + 0.55, T_RIP + 0.95): add(buf, sq(60, 0.08, 0.06, 0.5), tb); add(buf, sq(55, 0.1, 0.05, 0.5), tb + 0.08)
    t = T_RIP + 1.3
    while t < T_FLIP: add(buf, tri(36, 0.1, 0.3), t); add(buf, tri(36, 0.1, 0.22), t + 0.16); t += 0.42
    for i in range(10): add(buf, sq(60 + i * 3, 0.03, 0.09, 0.25), T_FLIP + i * 0.025)
    t = T_FLIP + 0.28
    for n, d_ in [(72, .12), (76, .12), (79, .12), (84, .3), (83, .12), (84, .6)]:
        add(buf, sq(n, d_ * 0.95, 0.12, 0.5), t); add(buf, sq(n - 5, d_ * 0.95, 0.05, 0.25), t); t += d_
    add(buf, noise(1.2, 0.05, 0.8, 6), T_FLIP + 0.3)
    t = T_END
    for n, d_ in mel:
        if t > DUR - 0.3: break
        add(buf, sq(n, d_ * b * 0.9, 0.08, 0.5), t); t += d_ * b
    t = T_END; k = 0
    while t < DUR - 0.2:
        add(buf, tri(bass[(k // 2) % 8], e * 0.9, 0.16), t)
        if not bb and k % 4 == 2: add(buf, noise(0.1, 0.06, 0.05, 3), t)
        t += e; k += 1
    buf *= np.clip((DUR - np.arange(len(buf)) / SR) / 0.5, 0, 1)
    buf /= max(1e-9, np.abs(buf).max()) / 0.45
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((buf * 32767).astype(np.int16).tobytes())

DEFAULTS = {
    "fb_pass": {"hook": ["DOWN BY 3.", "4 SECONDS. 55 YARDS."], "home_score": 17, "away_score": 20},
    "fb_run": {"hook": ["DOWN BY 3.", "4 SECONDS LEFT."], "home_score": 17, "away_score": 20},
    "fb_kick": {"hook": ["DOWN BY 2.", "0:02 LEFT. 48 YARDS."], "home_score": 21, "away_score": 23},
    "bb_homer": {"hook": ["BOTTOM 9TH. 2 OUTS.", "DOWN BY 1. FULL COUNT."], "home_score": 3, "away_score": 4},
}
PAYOFF = {"fb_pass": T_CATCH, "fb_run": T_TD, "fb_kick": T_GOOD, "bb_homer": T_HR}

def load_spec(path):
    sp = json.load(open(path)); v = sp["variant"]
    base = dict(DEFAULTS[v]); base.update({"home": "ONC", "away": "CPU", "away_color": "red", "end": {}, "pack_label": ["HOBBY", "PACK"]})
    base.update(sp); base["acol"] = AWAY.get(base["away_color"], RED)
    return base

def main(spec_path, out, preview=None):
    sp = load_spec(spec_path); random.seed(sp.get("seed", 1))
    if preview:
        for tp in preview: render(tp, sp).save(f"{out}_{tp:05.2f}.png")
        return
    wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    make_audio(wav, sp, PAYOFF[sp["variant"]])
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                          "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out],
                         stdin=subprocess.PIPE)
    for i in range(N): p.stdin.write(render(i / FPS, sp).tobytes())
    p.stdin.close(); p.wait(); os.unlink(wav); print("wrote", out)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], [float(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else None)
