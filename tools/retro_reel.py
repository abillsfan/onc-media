"""ONC 8-bit football reel. Renders at 270x480 and scales 4x (nearest) to 1080x1920, 30 fps, ~14 s.
Original pixel art + original chiptune. Usage: python3 retro_reel.py OUT.mp4 [t1,t2,... preview]"""
import math, random, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

LW, LH, S, FPS = 270, 480, 4, 30
W, H = LW * S, LH * S
DUR = 14.0
N = int(DUR * FPS)
OUT = sys.argv[1] if len(sys.argv) > 1 else "onc_8bit.mp4"
PREVIEW = [float(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else None
LOGO = "/home/claude/onc-media/brand/logo.png"

T_TD, T_WIPE, T_PACK, T_RIP, T_FLIP, T_END = 3.6, 5.1, 5.5, 6.7, 8.3, 9.8

def F(sz): return ImageFont.truetype("/home/claude/onc-media/brand/ps2p.woff", sz)
F8, F16, F24 = F(8), F(16), F(24)

# NES-ish palette
BLK = (0, 0, 0); WHT = (252, 252, 252); GRY = (188, 188, 188); DGRY = (116, 116, 116)
G1 = (0, 168, 0); G2 = (0, 140, 0); BLU = (0, 88, 248); LBLU = (60, 188, 252); NAVY = (0, 0, 168)
RED = (216, 40, 0); DRED = (168, 16, 0); YEL = (248, 216, 0); GOLD = (248, 184, 0); ORG = (228, 92, 16)
SKIN = (252, 188, 116); BRN = (136, 72, 0); PUR = (104, 68, 252); DPUR = (68, 40, 188); PINK = (248, 120, 248)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(t): t = clamp(t); return 1 - (1 - t) ** 3

def txt(d, xy, s, f, col, anchor="mm", sh=BLK):
    x, y = xy
    if sh is not None:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 1)):
            d.text((x + dx, y + dy), s, font=f, fill=sh, anchor=anchor)
    d.text((x, y), s, font=f, fill=col, anchor=anchor)

DIG = {"0": "111101101101111", "1": "010110010010111", "2": "111001111100111", "3": "111001111001111",
       "4": "101101111001001", "5": "111100111001111", "6": "111100111101111", "7": "111001001001001",
       "8": "111101111101111", "9": "111101111001111"}
def digits(d, x, y, s, col, k=1):
    for n, ch in enumerate(s):
        for i, b in enumerate(DIG[ch]):
            if b == "1":
                px, py = x + n * 4 * k + (i % 3) * k, y + (i // 3) * k
                d.rectangle((px, py, px + k - 1, py + k - 1), fill=col)

# ------------------------------------------------------------- sprites
def player(d, x, y, team, frame, facing="up", ball=False, num="7"):
    """x,y = feet center (native px). ~14w x 24h."""
    jer, hel, trim = (BLU, BLU, WHT) if team == "onc" else (RED, RED, WHT)
    x, y = int(x), int(y)
    # shadow
    d.ellipse((x - 7, y - 2, x + 7, y + 2), fill=(0, 100, 0))
    l = -2 if frame else 0; r = 0 if frame else -2
    d.rectangle((x - 4, y - 7 + l, x - 2, y - 1 + l), fill=WHT)  # legs (socks)
    d.rectangle((x + 2, y - 7 + r, x + 4, y - 1 + r), fill=WHT)
    d.rectangle((x - 4, y - 1 + l, x - 2, y + l), fill=BLK)
    d.rectangle((x + 2, y - 1 + r, x + 4, y + r), fill=BLK)
    d.rectangle((x - 5, y - 11, x + 5, y - 7), fill=GRY if team == "onc" else WHT)  # pants
    d.rectangle((x - 6, y - 19, x + 6, y - 11), fill=jer)  # jersey
    d.rectangle((x - 8, y - 18, x - 7, y - 13 + (1 if frame else -1)), fill=jer)  # arms
    d.rectangle((x + 7, y - 18, x + 8, y - 13 + (-1 if frame else 1)), fill=jer)
    d.rectangle((x - 8, y - 13 + (1 if frame else -1), x - 7, y - 12 + (1 if frame else -1)), fill=SKIN)
    d.rectangle((x + 7, y - 13 + (-1 if frame else 1), x + 8, y - 12 + (-1 if frame else 1)), fill=SKIN)
    digits(d, x - 1 if len(num) == 1 else x - 3, y - 18, num, trim)
    d.ellipse((x - 4, y - 26, x + 4, y - 18), fill=hel)  # helmet
    d.line((x, y - 26, x, y - 19), fill=trim)
    if facing == "down":
        d.rectangle((x - 3, y - 22, x + 3, y - 19), fill=SKIN)
        d.line((x - 3, y - 21, x + 3, y - 21), fill=GRY)
    if ball:
        d.ellipse((x + 6, y - 17, x + 11, y - 13), fill=BRN); d.point((x + 8, y - 15), fill=WHT)

def diver(d, x, y, team, flip=False):
    """Defender laid out horizontally mid-dive."""
    jer = RED if team != "onc" else BLU
    x, y = int(x), int(y)
    s = -1 if flip else 1
    d.ellipse((x - 10, y - 2, x + 10, y + 3), fill=(0, 100, 0))
    pts = lambda a, b: (min(x + s * a, x + s * b), max(x + s * a, x + s * b))
    a, b = pts(-12, -6); d.rectangle((a, y - 8, b, y - 6), fill=WHT)
    a, b = pts(-6, 0); d.rectangle((a, y - 10, b, y - 5), fill=WHT)
    a, b = pts(0, 9); d.rectangle((a, y - 11, b, y - 4), fill=jer)
    a, b = pts(9, 15); d.rectangle((a, y - 9, b, y - 7), fill=jer)
    cx = x + s * 13; d.ellipse((cx - 4, y - 12, cx + 4, y - 4), fill=jer)
    hx = x + s * 17; d.rectangle((min(hx, hx + s * 3), y - 9, max(hx, hx + s * 3), y - 7), fill=SKIN)

# ------------------------------------------------------------- field
YD = 6  # px per yard
EZ = 10 * YD
def field(cam, t):
    img = Image.new("RGB", (LW, LH), G1); d = ImageDraw.Draw(img)
    off = 300 - cam  # screen = world + off
    for yd in range(-10, 100, 5):
        y0 = yd * YD + off
        if y0 > LH or y0 + 5 * YD < 0: continue
        if yd < 0:
            d.rectangle((0, y0, LW, y0 + 5 * YD), fill=NAVY)
        elif (yd // 5) % 2:
            d.rectangle((0, y0, LW, y0 + 5 * YD), fill=G2)
    # end zone text
    ezy = -EZ + off
    if ezy + EZ > 0:
        txt(d, (LW // 2, ezy + EZ // 2 + 2), "O N C", F24, WHT, sh=BLU)
    for yd in range(0, 100, 5):
        y = yd * YD + off
        if -2 < y < LH + 2:
            d.line((8, y, LW - 9, y), fill=WHT, width=2 if yd % 10 == 0 else 1)
            if yd % 10 == 0 and yd > 0:
                n = str(min(yd, 100 - yd))
                digits(d, 16, y + 4, n, WHT, k=3); digits(d, LW - 16 - len(n) * 12, y + 4, n, WHT, k=3)
        for k in range(1, 5):  # hash marks
            hy = (yd + k) * YD + off
            if 0 < hy < LH:
                d.line((92, hy, 98, hy), fill=WHT); d.line((LW - 99, hy, LW - 93, hy), fill=WHT)
    d.line((8, 0, 8, LH), fill=WHT, width=2); d.line((LW - 9, 0, LW - 9, LH), fill=WHT, width=2)
    # goal post at back of end zone
    gy = -EZ + off
    if gy > -40:
        d.rectangle((LW // 2 - 1, gy - 18, LW // 2 + 1, gy + 2), fill=YEL)
        d.rectangle((LW // 2 - 30, gy - 18, LW // 2 + 30, gy - 16), fill=YEL)
        d.rectangle((LW // 2 - 30, gy - 44, LW // 2 - 28, gy - 16), fill=YEL)
        d.rectangle((LW // 2 + 28, gy - 44, LW // 2 + 30, gy - 16), fill=YEL)
    # crowd strip beyond end zone
    if gy - 46 > 0:
        d.rectangle((0, 0, LW, gy - 46), fill=(40, 40, 40))
        rnd = random.Random(int(t * 8))
        for cy in range(int(gy - 50), 0, -7):
            for cx in range(3, LW, 7):
                c = rnd.choice([RED, BLU, YEL, WHT, SKIN, PINK, LBLU])
                d.rectangle((cx, cy - 4 - rnd.randint(0, 1), cx + 3, cy - 1), fill=c)
    return img, d, off

def hud(d, score_onc, clock, flash=False):
    d.rectangle((0, 0, LW, 34), fill=BLK)
    d.line((0, 34, LW, 34), fill=WHT)
    txt(d, (8, 10), "ONC", F8, LBLU, "lm", None)
    txt(d, (46, 10), f"{score_onc:2d}", F8, WHT, "lm", None)
    txt(d, (LW - 8, 10), "CPU", F8, ORG, "rm", None)
    txt(d, (LW - 46, 10), "20", F8, WHT, "rm", None)
    txt(d, (LW // 2, 10), "4TH QTR", F8, YEL, "mm", None)
    txt(d, (LW // 2, 24), clock, F8, RED if flash else WHT, "mm", None)

# ------------------------------------------------------------- scene 1: the play
def run_x(t):
    x = 135.0
    x += 38 * ease((t - 0.85) / 0.35)   # juke right
    x -= 62 * ease((t - 2.05) / 0.35)   # juke left
    return x
def run_y(t): return 60 * YD - (60 * YD + 12) * clamp(t / T_TD) ** 0.92  # world y, to inside end zone

def scene_play(t):
    tt = min(t, T_TD)
    py = run_y(tt); px = run_x(tt)
    cam = max(py, -EZ + 150)  # stop scrolling once end zone is in view
    img, d, off = field(cam, t)
    fr = int(t * 10) % 2
    # chasers from behind
    for k, (dx, lag) in enumerate([(-40, 34), (52, 46)]):
        cy = run_y(max(0, tt - 0.0)) + lag + 10 * math.sin(t * 3 + k)
        player(d, px + dx * (0.6 + 0.4 * math.cos(t + k)), cy + off, "cpu", fr ^ k, "up")
    # diver 1 (left side) dives at ~0.95 s, misses
    for (t0, sx, flip) in [(0.95, -1, False), (2.15, 1, True)]:
        wy = run_y(t0) - 6
        if tt < t0 - 0.05:
            ix = run_x(t0 - 0.35) + sx * 30 - sx * 30 * ease((tt - (t0 - 0.6)) / 0.55)
            iy = wy - 70 + 70 * ease((tt - (t0 - 0.9)) / 0.85)
            player(d, ix, iy + off, "cpu", fr, "down")
        else:
            gx = run_x(t0 - 0.35) - 4 + (0 if not flip else -10)
            slide = ease((tt - t0) / 0.3) * 10
            diver(d, gx + (slide if not flip else -slide), wy + off + 4, "cpu", flip)
    # blocker escort
    player(d, px - 22, py + off + 8, "onc", fr ^ 1, "up", num="44")
    if t < T_TD:
        player(d, px, py + off, "onc", fr, "up", ball=True, num="7")
    else:
        # celebration: spike + jump
        u = t - T_TD
        jy = -abs(math.sin(u * 9)) * 8
        player(d, px, py + off + jy, "onc", int(u * 8) % 2, "down", num="7")
        by = py + off - 30 + 60 * min(u, 0.25) / 0.25 - 40 * max(0, u - 0.25) * (1 - min(1, (u - 0.25) / 0.8))
        bx = px + 14 + 30 * u
        if u < 1.1: d.ellipse((bx - 3, by - 2, bx + 3, by + 2), fill=BRN)
        for i in range(10):  # fireworks
            ang = i * 0.628 + u
            for c, (cx0, cy0, ph) in enumerate([(60, 70, 0.0), (210, 90, 0.35), (135, 55, 0.7)]):
                v = u - ph
                if 0 < v < 1.0:
                    rr = 40 * ease(v)
                    d.rectangle((cx0 + rr * math.cos(ang), cy0 + rr * math.sin(ang),
                                 cx0 + rr * math.cos(ang) + 2, cy0 + rr * math.sin(ang) + 2),
                                fill=[YEL, LBLU, PINK][c] if int(v * 12) % 3 else WHT)
    # HUD
    secs = max(0, 4 - int(t / T_TD * 4)) if t < T_TD else 0
    hud(d, 17 if t < T_TD else 23, f"0:0{secs}", flash=t < T_TD and int(t * 4) % 2 == 0)
    # hook / callouts
    if t < 1.5:
        if int(t * 6) % 6 != 5:
            txt(d, (LW // 2, 58), "DOWN BY 3.", F16, YEL)
            txt(d, (LW // 2, 80), "4 SECONDS LEFT.", F8 if False else F(12), WHT)
    elif t < 2.5:
        txt(d, (LW // 2, 62), "JUKE!", F24, LBLU)
    elif t < T_TD:
        txt(d, (LW // 2, 62), "GO! GO! GO!", F16, YEL)
    if t >= T_TD:
        u = t - T_TD
        col = [YEL, WHT, LBLU, GOLD][int(u * 10) % 4]
        sc = 1 if u > 0.12 else 2
        txt(d, (LW // 2, 262), "TOUCH", F(24 * sc) if sc == 2 else F24, col)
        txt(d, (LW // 2, 294), "DOWN!", F(24 * sc) if sc == 2 else F24, col)
        if u > 0.6: txt(d, (LW // 2, 326), "ONC WINS 23-20", F(12), WHT)
        if u < 0.08:
            ImageDraw.Draw(img).rectangle((0, 0, LW, LH), fill=WHT)
    return img

# ------------------------------------------------------------- scene 2: the pack
def pixel_card(d, x, y, kind, w=56, h=78):
    x, y = int(x - w / 2), int(y - h / 2)
    if kind == "back":
        cb = Image.new("RGB", (w + 1, h + 1), NAVY); cbd = ImageDraw.Draw(cb)
        for i in range(0, w + h, 8):
            cbd.line((i, 0, 0, i), fill=BLU)
        cbd.rectangle((0, 0, w, h), outline=GOLD, width=2)
        d._image.paste(cb, (x, y))
        txt(d, (x + w // 2, y + h // 2), "?", F24, WHT)
        return
    body = {"b1": (LBLU, BLU), "b2": (GRY, DGRY), "gold": (GOLD, YEL)}[kind]
    d.rectangle((x, y, x + w, y + h), fill=body[0], outline=WHT if kind != "gold" else (252, 252, 168), width=2)
    d.rectangle((x + 5, y + 5, x + w - 5, y + h - 20), fill=body[1])
    # mini player silhouette
    cx, cy = x + w // 2, y + 18
    d.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=BLK)
    d.rectangle((cx - 9, cy + 6, cx + 9, cy + 26), fill=BLK)
    d.rectangle((cx + 9, cy + 8, cx + 14, cy + 11), fill=BRN)
    d.rectangle((x + 2, y + h - 16, x + w - 2, y + h - 3), fill=BLK if kind != "gold" else DRED)
    txt(d, (x + w // 2, y + h - 9), "RC AUTO" if kind == "gold" else "BASE", F(6) if kind == "gold" else F(6),
        GOLD if kind == "gold" else WHT, sh=None)
    if kind == "gold":
        d.line([(x + 10, y + h - 26), (x + 16, y + h - 32), (x + 22, y + h - 24), (x + 30, y + h - 31),
                (x + 38, y + h - 25), (x + 46, y + h - 29)], fill=NAVY, width=2)

def scene_pack(t):
    img = Image.new("RGB", (LW, LH), (24, 24, 56)); d = ImageDraw.Draw(img)
    # starfield / bg
    rnd = random.Random(4)
    for _ in range(60):
        sx, sy = rnd.randint(0, LW), rnd.randint(40, 300)
        if (int(t * 6) + sx) % 7: d.point((sx, sy), fill=GRY)
    d.rectangle((0, 330, LW, LH), fill=BRN); d.rectangle((0, 330, LW, 334), fill=(180, 100, 30))
    for x in range(0, LW, 18): d.line((x, 336, x - 30, LH), fill=(110, 56, 0))
    cx, cy = LW // 2, 230
    u = t - T_PACK
    if t < T_RIP:
        shake = int(math.sin(t * 50) * (1 + 3 * clamp(u / 1.1)))
        x0, y0 = cx - 34 + shake, cy - 50
        d.rectangle((x0, y0, x0 + 68, y0 + 100), fill=PUR)
        for k in range(0, 68, 6): d.line((x0 + k, y0, x0 + k, y0 + 100), fill=DPUR)
        d.rectangle((x0, y0, x0 + 68, y0 + 12), fill=DPUR)
        d.rectangle((x0, y0 + 90, x0 + 68, y0 + 100), fill=DPUR)
        txt(d, (cx + shake, cy - 10), "HOBBY", F8, WHT)
        txt(d, (cx + shake, cy + 6), "PACK", F8, YEL)
        g = int(((t * 1.5) % 1.0) * 100)  # foil glint, kept inside the wrapper
        if 20 <= g <= 68: d.line((x0 + g, y0 + 14, x0 + g - 20, y0 + 88), fill=WHT, width=2)
        txt(d, (LW // 2, 90), "NOW DO IT", F16, WHT)
        txt(d, (LW // 2, 114), "WITH CARDS.", F16, YEL)
        if u > 0.6: txt(d, (LW // 2, 360 + 20), "RIP IT...", F16, LBLU, sh=BLK)
    else:
        v = t - T_RIP
        # top of pack flying off
        if v < 0.6:
            tx, ty = cx + 120 * v, cy - 50 - 200 * v + 300 * v * v
            d.rectangle((tx - 34, ty, tx + 34, ty + 12), fill=DPUR)
        # torn pack body sinking
        x0, y0 = cx - 34, cy - 38 + int(160 * ease((v - 0.3) / 0.6))
        if t < T_FLIP:
            # card stack rising
            rise = int(46 * ease(v / 0.3))
            order = ["b1", "b2", "back"]
            n_gone = 0 if v < 0.55 else 1 if v < 0.95 else 2
            for k in range(2, n_gone - 1, -1):
                if k < n_gone: continue
                pixel_card(d, cx + (k - n_gone), cy - 30 - rise + (k - n_gone) * 2, order[k])
            for k in range(n_gone):  # slid-away cards
                st = 0.55 if k == 0 else 0.95
                q = ease((v - st) / 0.3)
                pixel_card(d, cx + (-1 if k == 0 else 1) * 160 * q, cy - 30 - rise, order[k])
            d.rectangle((x0, y0, x0 + 68, y0 + 88), fill=PUR)
            for k in range(0, 68, 6): d.line((x0 + k, y0, x0 + k, y0 + 88), fill=DPUR)
            for k in range(0, 68, 8): d.polygon([(x0 + k, y0), (x0 + k + 4, y0 - 4), (x0 + k + 8, y0)], fill=PUR)
            d.rectangle((x0, y0 + 78, x0 + 68, y0 + 88), fill=DPUR)
            if v < 0.25:
                for i in range(8):
                    a = i * 0.785
                    d.line((cx + 30 * math.cos(a), cy - 50 + 20 * math.sin(a), cx + 50 * math.cos(a), cy - 50 + 34 * math.sin(a)), fill=YEL, width=2)
            if v < 0.5: txt(d, (LW // 2, 90), "RIIIP!", F24, YEL)
            elif v < 1.3: txt(d, (LW // 2, 90), "BASE...", F16, GRY)
            else:
                txt(d, (LW // 2, 90), "WAIT FOR IT...", F(12), WHT)
        else:
            w = (t - T_FLIP)
            flip = clamp(w / 0.25)
            kind = "back" if flip < 0.5 else "gold"
            sc = abs(1 - flip * 2) if flip < 1 else 1
            big = 1 + 0.5 * ease((w - 0.25) / 0.3)
            cw, ch = int(56 * big * max(sc, 0.05)), int(78 * big)
            # glow rays
            if kind == "gold":
                for i in range(12):
                    a = i * 0.5236 + w * 1.5
                    d.polygon([(cx, cy - 40), (cx + 140 * math.cos(a), cy - 40 + 140 * math.sin(a)),
                               (cx + 140 * math.cos(a + 0.2), cy - 40 + 140 * math.sin(a + 0.2))], fill=(64, 52, 20))
            card = Image.new("RGB", (60, 82), (0, 0, 0)); cd = ImageDraw.Draw(card)
            pixel_card(cd, 30, 41, kind)
            m = Image.new("L", (60, 82), 0); ImageDraw.Draw(m).rectangle((2, 2, 58, 80), fill=255)
            card = card.resize((max(1, cw), ch), Image.NEAREST); m = m.resize((max(1, cw), ch), Image.NEAREST)
            img.paste(card, (cx - cw // 2, cy - 40 - ch // 2), m)
            d = ImageDraw.Draw(img)
            if kind == "gold":
                rnd2 = random.Random(int(t * 12))
                for _ in range(10):
                    sx = cx + rnd2.randint(-70, 70); sy = cy - 40 + rnd2.randint(-90, 90)
                    d.line((sx - 3, sy, sx + 3, sy), fill=WHT); d.line((sx, sy - 3, sx, sy + 3), fill=WHT)
                col = [YEL, WHT, GOLD, PINK][int(w * 10) % 4]
                txt(d, (LW // 2, 70), "BIG HIT!", F24, col)
                if w > 0.5:
                    txt(d, (LW // 2, 372), "THAT FEELING?", F(12), WHT)
                    txt(d, (LW // 2, 394), "WE RIP FOR IT", F(12), YEL)
                    txt(d, (LW // 2, 416), "LIVE.", F(12), YEL)
    return img

# ------------------------------------------------------------- scene 3: title screen
_logo = None
def pixel_logo(size=150):
    global _logo
    if _logo is None:
        lg = Image.open(LOGO).convert("RGBA")
        lg.thumbnail((size, size), Image.LANCZOS)
        a = lg.getchannel("A").point(lambda v: 255 if v > 110 else 0)
        rgb = lg.convert("RGB").quantize(colors=10, dither=Image.Dither.NONE).convert("RGB")
        _logo = (rgb, a)
    return _logo

def scene_end(t):
    img = Image.new("RGB", (LW, LH), BLK); d = ImageDraw.Draw(img)
    u = t - T_END
    rnd = random.Random(9)
    for _ in range(80):
        sx, sy, sp = rnd.randint(0, LW), rnd.randint(0, LH), rnd.uniform(20, 80)
        y = (sy + sp * u) % LH
        d.point((sx, y), fill=WHT if sp > 50 else DGRY)
    rgb, a = pixel_logo()
    drop = int(-200 * (1 - ease(u / 0.5))) + int(4 * math.sin(u * 4))
    img.paste(rgb, ((LW - rgb.width) // 2, 40 + drop), a)
    d = ImageDraw.Draw(img)
    if u > 0.5:
        txt(d, (LW // 2, 220), "OUTTA NOWHERE", F16, WHT)
        txt(d, (LW // 2, 244), "CARDS", F16, YEL)
    if u > 0.9:
        txt(d, (LW // 2, 288), "LIVE BREAKS ON", F8, LBLU)
        txt(d, (LW // 2, 304), "WHATNOT", F16, WHT)
    if u > 1.3 and int(u * 2.5) % 2 == 0:
        txt(d, (LW // 2, 360), "PRESS FOLLOW", F(12), YEL)
    if u > 1.6:
        d.rectangle((40, 400, LW - 40, 428), fill=NAVY, outline=WHT)
        txt(d, (LW // 2, 414), "ON-CARDS.COM", F(12), WHT, sh=None)
    txt(d, (LW // 2, 460), "INSERT CARDS TO CONTINUE", F(6), DGRY, sh=None)
    return img

def wipe(img, t):
    """Classic horizontal-bar wipe across the cut between play and pack."""
    v = (t - T_WIPE) / (T_PACK - T_WIPE)
    if 0 <= v < 1:
        d = ImageDraw.Draw(img)
        k = v * 2 if v < 0.5 else (1 - v) * 2
        for i in range(0, LH, 16):
            w = int(LW * k)
            if (i // 16) % 2: d.rectangle((0, i, w, i + 16), fill=BLK)
            else: d.rectangle((LW - w, i, LW, i + 16), fill=BLK)
    return img

def scanlines(img):
    big = img.resize((W, H), Image.NEAREST)
    a = np.asarray(big).astype(np.int16)
    a[3::4] = (a[3::4] * 0.72).astype(np.int16)  # subtle CRT lines
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))

def render(t):
    if t < (T_WIPE + T_PACK) / 2: img = scene_play(t)
    elif t < T_END: img = scene_pack(t)
    else: img = scene_end(t)
    if T_WIPE <= t < T_PACK: img = wipe(img, t)
    if T_END - 0.15 < t < T_END: img = Image.new("RGB", (LW, LH), WHT)
    return scanlines(img)

# ------------------------------------------------------------- chiptune (original)
SR = 44100
def hz(n): return 440 * 2 ** ((n - 69) / 12)
def sq(n, dur, vol, duty=0.5, slide=0.0):
    t = np.arange(int(dur * SR)) / SR
    f = hz(n) * (1 + slide * t / max(dur, 1e-6))
    ph = np.cumsum(f) / SR % 1.0
    s = np.where(ph < duty, 1.0, -1.0)
    env = np.minimum(1, t / 0.004) * np.clip(1 - t / dur * 0.35, 0, 1) * np.minimum(1, (dur - t) / 0.01).clip(0)
    return s * env * vol
def tri(n, dur, vol):
    t = np.arange(int(dur * SR)) / SR
    ph = hz(n) * t % 1.0
    s = 4 * np.abs(ph - 0.5) - 1
    s = np.round(s * 8) / 8  # 4-bit stepping like the NES triangle
    return s * np.minimum(1, (dur - t) / 0.01).clip(0) * vol
def noise(dur, vol, decay=0.06, period=1):
    n = int(dur * SR); rng = np.random.default_rng(len(_mix_count)); _mix_count.append(1)
    s = np.repeat(rng.choice([-1.0, 1.0], n // period + 1), period)[:n]
    return s * np.exp(-np.arange(n) / SR / decay) * vol
_mix_count = []
def add(buf, sig, t0):
    i = int(t0 * SR); j = min(len(buf), i + len(sig))
    if 0 <= i < len(buf): buf[i:j] += sig[: j - i]

def make_audio(path):
    buf = np.zeros(int((DUR + 0.3) * SR))
    bpm = 150; b = 60 / bpm; e = b / 2
    # fight-song march melody (original), C major, 2 bars x 2
    mel = [(72, 1), (72, .5), (74, .5), (76, 1), (72, 1), (79, 1.5), (77, .5), (76, 1), (74, 1),
           (76, 1), (76, .5), (77, .5), (79, 1), (81, 1), (79, 1), (76, 1), (74, 2)]
    t = 0.0
    while t < T_TD - 0.05:
        for n, d_ in mel:
            if t >= T_TD - 0.05: break
            dd = min(d_ * b, T_TD - t)
            add(buf, sq(n, dd * 0.9, 0.11, 0.25), t); t += d_ * b
    bass = [48, 55, 52, 55, 53, 57, 55, 50]
    t = 0.0; k = 0
    while t < T_TD:
        add(buf, tri(bass[(k // 2) % 8] - 12 if k % 2 == 0 else bass[(k // 2) % 8], e * 0.9, 0.22), t)
        add(buf, noise(0.03, 0.05, 0.01), t + e / 2)  # hat
        if k % 4 == 2: add(buf, noise(0.12, 0.10, 0.05, 3), t)  # snare
        t += e; k += 1
    # dive "whoosh" + juke blips
    for tj in (0.85, 2.05):
        add(buf, sq(84, 0.12, 0.06, 0.125, slide=0.8), tj)
    # touchdown fanfare
    fan = [(60, .1), (64, .1), (67, .1), (72, .1), (76, .1), (79, .1), (84, .45), (79, .12), (84, .7)]
    t = T_TD
    for n, d_ in fan:
        add(buf, sq(n, d_ * 0.95, 0.13, 0.5), t); add(buf, sq(n - 12, d_ * 0.95, 0.06, 0.25), t); t += d_
    add(buf, tri(48, 1.0, 0.25), T_TD + 0.6)
    crowd = noise(1.6, 0.06, 0.9, 6); add(buf, crowd, T_TD)
    add(buf, noise(0.4, 0.06, 0.2, 2), T_WIPE)
    # pack tension: pulsing bass + rising arpeggio
    t = T_PACK; k = 0
    while t < T_RIP:
        add(buf, tri(43, e * 0.8, 0.22), t)
        add(buf, sq(67 + (k % 4) * 2 + k // 4, e * 0.6, 0.06, 0.125), t)
        t += e; k += 1
    add(buf, noise(0.35, 0.16, 0.12, 1), T_RIP)  # rip
    for tb in (T_RIP + 0.55, T_RIP + 0.95):  # base card slides
        add(buf, sq(60, 0.08, 0.06, 0.5), tb); add(buf, sq(55, 0.1, 0.05, 0.5), tb + 0.08)
    t = T_RIP + 1.3
    while t < T_FLIP:  # heartbeat
        add(buf, tri(36, 0.1, 0.3), t); add(buf, tri(36, 0.1, 0.22), t + 0.16); t += 0.42
    # flip power-up + hit jingle
    for i in range(10): add(buf, sq(60 + i * 3, 0.03, 0.09, 0.25), T_FLIP + i * 0.025)
    jing = [(72, .12), (76, .12), (79, .12), (84, .3), (83, .12), (84, .6)]
    t = T_FLIP + 0.28
    for n, d_ in jing:
        add(buf, sq(n, d_ * 0.95, 0.12, 0.5), t); add(buf, sq(n - 5, d_ * 0.95, 0.05, 0.25), t); t += d_
    add(buf, noise(1.2, 0.05, 0.8, 6), T_FLIP + 0.3)
    # title screen theme: melody reprise, softer
    t = T_END; k = 0
    for n, d_ in mel:
        if t > DUR - 0.3: break
        add(buf, sq(n, d_ * b * 0.9, 0.08, 0.5), t); t += d_ * b
    t = T_END
    while t < DUR - 0.2:
        add(buf, tri(bass[(k // 2) % 8], e * 0.9, 0.16), t)
        if k % 4 == 2: add(buf, noise(0.1, 0.06, 0.05, 3), t)
        t += e; k += 1
    fade = np.clip((DUR - np.arange(len(buf)) / SR) / 0.5, 0, 1); buf *= fade
    buf /= max(1e-9, np.abs(buf).max()) / 0.45
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((buf * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    if PREVIEW:
        for tp in PREVIEW: render(tp).save(f"prev_{tp:05.2f}.png")
        sys.exit()
    make_audio("chip.wav")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", "chip.wav", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                          "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT],
                         stdin=subprocess.PIPE)
    for i in range(N):
        p.stdin.write(render(i / FPS).tobytes())
    p.stdin.close(); p.wait(); print("done", OUT)
