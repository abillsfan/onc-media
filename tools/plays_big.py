"""Big-moment plays for the ONC reel engine (not just scoring plays). Registered into retro_reel's game table,
so they work in every era (tools/era_reel.py). Every play cuts between several camera angles.

  fb_sack  = overhead behind the defense: CPU QB drops back, ONC blitzer loops in free -> close-up cut-in:
             blindside hit -> ground-level camera: QB down, ball loose. "SACKED!" ends the game.
  fb_block = behind the CPU kicker: game-winning kick try, ONC rusher leaps -> close-up cut-in: ball smacks his
             hands, "BLOCKED!" -> reverse angle from behind the posts: ball bouncing loose, ref waves it off.
"""
import math, random
from PIL import Image, ImageDraw
import retro_reel as R
from retro_reel import (LW, LH, YD, BLK, WHT, GRY, DGRY, BLU, LBLU, NAVY, YEL, GOLD, RED, DRED, BRN, SKIN, G1, G2, G3,
                        DGRN, F, txt, fit, clamp, ease, lerp)

# =============================================================== FOOTBALL: QB sack (fb_sack)
T_SSNAP, T_SCUT1, T_SHIT, T_SCUT2, T_SACKED = 0.45, 1.6, 2.15, 2.4, 2.7
SLOS = 28 * YD
def _sqb_y(t): return SLOS + 10 + 40 * ease((t - T_SSNAP) / 0.8)
def _blitz(t):
    """ONC blitzer path: edge -> loop around the tackle -> straight at the QB."""
    if t < T_SSNAP: return 228.0, SLOS - 16.0
    a = ease((t - T_SSNAP) / 0.55)
    x, y = lerp(228, 214, a), lerp(SLOS - 16, SLOS + 22, a)
    b = ease((t - 1.0) / 0.6)
    return lerp(x, 150, b), lerp(y, _sqb_y(t) - 4, b)

def fb_sack_overhead(t, sp):
    cam = _sqb_y(t) - 40
    img, d, off = R.fb_field(cam, t, sp); fr = int(t * 10) % 2; ac = sp["acol"]; go = t > T_SSNAP
    run = lambda t0, spd: max(0.0, t - t0) * spd
    # receivers run their routes upfield; ONC defensive backs blanket them
    for k, (wx, num) in enumerate([(32, "81"), (238, "84"), (196, "15")]):
        wy = SLOS - 4 - run(T_SSNAP, 120 + 15 * k)
        R.player(d, wx, wy + off, ac, fr ^ k if go else 0, "up", num=num)
        R.player(d, wx + 9, wy - 14 + off, BLU, fr ^ k ^ 1 if go else 0, "down", num="")
    push = 4 * math.sin(t * 9) if go else 0
    for i in range(5):   # CPU offensive line (backs to camera)
        R.player(d, 87 + i * 24, SLOS + 8 + off + (push if i % 2 else -push) * 0.5, ac, fr if go else 0, "up", num="", shadow=False)
    for i in range(4):   # ONC defensive line
        R.player(d, 99 + i * 24, SLOS - 4 + off + (-push if i % 2 else push) * 0.5, BLU, fr if go else 0, "down", num="", shadow=False)
    # running back tries to pick up the blitz and whiffs
    rbx = 150 + 26 * ease((t - 0.9) / 0.4)
    R.player(d, rbx, SLOS + 34 + off, ac, fr if go else 0, "up", num="28")
    bx, by = _blitz(min(t, T_SCUT1))
    R.player(d, bx, by + off, BLU, fr if go else 0, "down", num="52")
    R.player(d, 135, _sqb_y(t) + off, ac, fr if T_SSNAP < t < 1.25 else 0, "up", ball=True, num="9")
    secs = 5 if t < T_SSNAP else max(1, 5 - int((t - T_SSNAP) * 3))
    R.fb_hud(d, sp, sp["home_score"], f"0:0{secs}", flash=int(t * 4) % 2 == 0)
    R.hook_text(d, sp, t, until=1.0)
    if 1.0 <= t: txt(d, (LW // 2, 62), "BLITZ!", F(24), LBLU if int(t * 8) % 2 else WHT)
    if go and t < 1.4:
        txt(d, (bx, by + off - 38), "52", F(8), YEL)
    return img

def _arms_up_front(col, num, look="down"):
    """Front-view player with both arms raised (the sprite set draws the pose, so no arms stay at the sides)."""
    def fn(dd, cx, fy):
        R.player(dd, cx, fy, col, 0, look, num=num, shadow=False, arms="up")
    return fn

def fb_sack_cutin(t, sp):
    """Close-up: blitzer comes in from the blind side while the QB winds up."""
    img = Image.new("RGB", (LW, LH), BLK); u = t - T_SCUT1
    R.speed_lines(img, t, (88, 16, 24), (152, 40, 48), LW // 2 - 20, 250)
    hit = t >= T_SHIT
    shake = int(5 * math.sin(u * 70)) if hit and t < T_SHIT + 0.25 else 0
    qb = lambda dd, cx, fy: R.side_player(dd, cx, fy, sp["acol"], 0, 1, num="9", shadow=False, arm_back=True)
    bl = lambda dd, cx, fy: R.side_player(dd, cx, fy, BLU, int(u * 10) % 2, 1, num="52", shadow=False)
    if not hit:
        R.big(img, qb, 178, 340, 4, (40, 34))
        R.big(img, bl, lerp(-30, 112, ease(u / (T_SHIT - T_SCUT1))), 344, 4, (40, 34))
    else:
        v = t - T_SHIT
        R.big(img, lambda dd, cx, fy: R.side_fallen(dd, cx, fy, sp["acol"], 1), 168 + 20 * ease(v / 0.2) + shake, 350, 4, (44, 20))
        R.big(img, bl, 124 + 18 * ease(v / 0.2) + shake, 336, 4, (40, 34))
    d = ImageDraw.Draw(img); R.letterbox(d, 90, 380)
    if hit:
        if t < T_SHIT + 0.05: d.rectangle((0, 0, LW, LH), fill=WHT)
        for i in range(10):
            a = i * 0.628; cx, cy = 176, 220
            d.line((cx + 12 * math.cos(a), cy + 12 * math.sin(a), cx + 34 * math.cos(a), cy + 34 * math.sin(a)), fill=YEL, width=3)
        txt(d, (LW // 2, 420), "BLINDSIDE!", F(24), [YEL, WHT][int(u * 10) % 2])
    else:
        txt(d, (LW // 2, 420), "HE'S UNBLOCKED!", fit("HE'S UNBLOCKED!", LW - 12, 16), WHT)
    if u < 0.05: d.rectangle((0, 0, LW, LH), fill=BLK)
    R.fb_hud(d, sp, sp["home_score"], "0:01", flash=int(t * 4) % 2 == 0)
    return img

def _ground_cam(t, sp, hz=200):
    img = Image.new("RGB", (LW, LH), G1); d = ImageDraw.Draw(img)
    R.crowd(d, 34, hz - 22, t, 23); d.rectangle((0, hz - 22, LW, hz), fill=DGRN)
    txt(d, (LW // 2, hz - 11), "OUTTA NOWHERE CARDS", F(6), WHT, sh=None)
    for i in range(12):
        y0 = hz + (LH - hz) * (i / 12) ** 1.5; y1 = hz + (LH - hz) * ((i + 1) / 12) ** 1.5
        if i % 2: d.rectangle((0, y0, LW, y1), fill=G2)
    return img, d

def fb_sack_ground(t, sp):
    """Ground-level camera: QB slammed down, ball pops loose, defender celebrates."""
    img, d = _ground_cam(t, sp); u = t - T_SCUT2
    R.big(img, lambda dd, cx, fy: R.side_fallen(dd, cx, fy, sp["acol"], 1), 120, 360, 3, (44, 20))
    up = t >= T_SACKED
    if up:
        R.big(img, _arms_up_front(BLU, "52"), 196, 372, 3, (30, 44))
    else:
        R.big(img, lambda dd, cx, fy: R.side_player(dd, cx, fy, BLU, 0, 1, num="52", shadow=False), 150, 352 + 8 * ease(u / 0.2), 3, (40, 34))
    d = ImageDraw.Draw(img)
    for k in range(5):   # dust kicked up by the hit
        v = clamp(u / 0.6); r = 4 + 18 * v
        if v < 1:
            cx = 120 + (k - 2) * 22 * v; cy = 362 - 10 * v - (k % 2) * 6
            d.ellipse((cx - r, cy - r * 0.6, cx + r, cy + r * 0.6), fill=(200, 180, 140) if k % 2 else (170, 150, 110))
    bx = 160 + 140 * clamp(u / 1.4); by = 360 - abs(math.sin(u * 7)) * 40 * max(0, 1 - u / 1.4)   # loose ball
    d.ellipse((bx - 6, by - 4, bx + 6, by + 4), fill=BLK); d.ellipse((bx - 5, by - 3, bx + 5, by + 3), fill=BRN)
    if u < 0.05: d.rectangle((0, 0, LW, LH), fill=BLK)
    R.fb_hud(d, sp, sp["home_score"], "0:00")
    if not up: txt(d, (LW // 2, 120), "DOWN HE GOES!", fit("DOWN HE GOES!", LW - 12, 16), YEL)
    else:
        u2 = t - T_SACKED; R.fireworks(d, u2, ((60, 90, 0.0), (210, 110, 0.3), (135, 70, 0.6)))
        R.flash_title(d, u2, "SACKED!", "", y=130, sub=f"{sp['home']} WINS {sp['home_score']}-{sp['away_score']}")
    return img

def fb_sack(t, sp):
    if t < T_SCUT1: return fb_sack_overhead(t, sp), None
    if t < T_SCUT2: return fb_sack_cutin(t, sp), None
    return fb_sack_ground(t, sp), (T_SACKED if t >= T_SACKED else None)

# =============================================================== FOOTBALL: blocked field goal (fb_block)
T_BSNAP, T_BKICK, T_BCUT1, T_BLOCK, T_BCUT2 = 0.85, 1.3, 1.45, 1.95, 2.55
def fb_block_behind(t, sp):
    """Behind the CPU kicker: ONC's front wall surges, #99 leaps at the line."""
    img = Image.new("RGB", (LW, LH), G1); d = ImageDraw.Draw(img); HZ = R.HZ; ac = sp["acol"]
    R.crowd(d, 34, HZ - 26, t, 3); d.rectangle((0, HZ - 26, LW, HZ), fill=NAVY)
    txt(d, (LW // 2, HZ - 13), " ".join(sp["home"]), F(8), WHT, sh=None)
    for i in range(14):
        y0, y1 = R.persp_y(i / 14), R.persp_y((i + 1) / 14)
        if i % 2: d.rectangle((0, y0, LW, y1), fill=G2)
        d.line((0, y0, LW, y0), fill=WHT)
    d.rectangle((134, HZ - 4, 136, HZ + 6), fill=YEL); d.rectangle((122, HZ - 5, 148, HZ - 4), fill=YEL)
    d.rectangle((122, HZ - 34, 123, HZ - 4), fill=YEL); d.rectangle((147, HZ - 34, 148, HZ - 4), fill=YEL)
    fr = int(t * 8) % 2; go = t > T_BSNAP
    surge = 10 * ease((t - T_BSNAP) / 0.5)
    for i in range(7):
        if i == 3: continue
        R.player(d, 60 + i * 25, 246 + surge, BLU, fr if go else 0, "down", num="", shadow=False)
    # #99 in the middle: rises up over the line with both arms high
    jump = math.sin(math.pi * clamp((t - (T_BKICK - 0.25)) / 0.7)) * 34
    R.big(img, _arms_up_front(BLU, "99") if t > T_BKICK - 0.3 else (lambda dd, cx, fy: R.player(dd, cx, fy, BLU, 0, "down", num="99", shadow=False)),
          135, 250 + surge - jump, 2, (30, 44))
    d = ImageDraw.Draw(img)
    for i in range(7):
        R.player(d, 60 + i * 25, 290 - surge * 0.6, ac, 0, "up", num="", shadow=False)
    hold = lambda dd, cx, fy: (dd.rectangle((cx - 6, fy - 10, cx + 6, fy), fill=ac), dd.ellipse((cx - 4, fy - 17, cx + 4, fy - 9), fill=ac))
    R.big(img, hold, 150, 395, 2, (24, 24)); d = ImageDraw.Draw(img)
    if t < T_BKICK: d.ellipse((132, 368, 140, 374), fill=BRN)
    else:   # low line drive straight into the leaper's hands
        p = clamp((t - T_BKICK) / (T_BCUT1 - T_BKICK + 0.05)); bx, by = 136, lerp(370, 250 + surge - jump - 70, ease(p))
        d.ellipse((bx - 5, by - 4, bx + 5, by + 4), fill=BLK); d.ellipse((bx - 4, by - 3, bx + 4, by + 3), fill=BRN)
    step = ease((t - 0.95) / (T_BKICK - 0.95)) * 28
    leg = 1 if T_BKICK - 0.05 < t else 0
    def kicker(dd, cx, fy):
        dd.rectangle((cx - 4, fy - 7, cx - 2, fy), fill=WHT)
        if leg: dd.rectangle((cx + 2, fy - 13, cx + 4, fy - 7), fill=WHT); dd.rectangle((cx + 2, fy - 15, cx + 4, fy - 13), fill=BLK)
        else: dd.rectangle((cx + 2, fy - 7, cx + 4, fy), fill=WHT)
        dd.rectangle((cx - 5, fy - 11, cx + 5, fy - 7), fill=GRY); dd.rectangle((cx - 6, fy - 19, cx + 6, fy - 11), fill=ac)
        R.digits(dd, cx - 1, fy - 18, "4", WHT)
        dd.ellipse((cx - 4, fy - 26, cx + 4, fy - 18), fill=ac); dd.line((cx, fy - 26, cx, fy - 19), fill=WHT)
    R.big(img, kicker, 108 + step * 0.5, 478 - step, 2, (30, 32)); d = ImageDraw.Draw(img)
    R.fb_hud(d, sp, sp["home_score"], "0:03" if t < T_BSNAP else "0:01", flash=int(t * 4) % 2 == 0)
    R.hook_text(d, sp, t, until=1.0)
    if 1.0 <= t: txt(d, (LW // 2, 62), "FOR THE WIN...", fit("FOR THE WIN...", LW - 12, 16), YEL)
    return img

def fb_block_cutin(t, sp):
    """Close-up: the ball smacks off #99's outstretched hands."""
    img = Image.new("RGB", (LW, LH), BLK); u = t - T_BCUT1
    R.speed_lines(img, t, (16, 40, 120), (40, 88, 200), LW // 2, 160)
    blocked = t >= T_BLOCK
    shake = int(5 * math.sin(u * 70)) if blocked and t < T_BLOCK + 0.25 else 0
    R.big(img, _arms_up_front(BLU, "99"), 135 + shake, 400, 4, (30, 44))
    d = ImageDraw.Draw(img)
    hx, hy = 135, 400 - 37 * 4 + 6
    if not blocked:   # ball rising up from below toward his hands, growing as it nears
        p = ease(clamp(u / (T_BLOCK - T_BCUT1))); bx, by = lerp(150, hx, p), lerp(470, hy, p); r = 4 + int(6 * p)
        d.ellipse((bx - r * 1.4 - 1, by - r - 1, bx + r * 1.4 + 1, by + r + 1), fill=BLK); d.ellipse((bx - r * 1.4, by - r, bx + r * 1.4, by + r), fill=BRN)
        txt(d, (LW // 2, 420), "GET A HAND ON IT!", fit("GET A HAND ON IT!", LW - 12, 16), WHT)
    else:
        v = t - T_BLOCK
        if v < 0.05: d.rectangle((0, 0, LW, LH), fill=WHT)
        bx, by = hx - 120 * v, hy - 140 * v + 160 * v * v; r = 10
        d.ellipse((bx - r * 1.4 - 1, by - r - 1, bx + r * 1.4 + 1, by + r + 1), fill=BLK); d.ellipse((bx - r * 1.4, by - r, bx + r * 1.4, by + r), fill=BRN)
        d.line((bx - 6, by, bx + 6, by), fill=WHT, width=2)
        for i in range(10):
            a = i * 0.628
            d.line((hx + 14 * math.cos(a), hy + 14 * math.sin(a), hx + 36 * math.cos(a), hy + 36 * math.sin(a)), fill=YEL, width=3)
        R.flash_title(d, v, "BLOCKED!", "", y=420)
    if u < 0.05: d.rectangle((0, 0, LW, LH), fill=BLK)
    R.fb_hud(d, sp, sp["home_score"], "0:00" if blocked else "0:01")
    return img

def fb_block_posts(t, sp):
    """Reverse angle from behind the posts: ball bouncing loose, ref waves it off, ONC sideline erupts."""
    img = Image.new("RGB", (LW, LH), G1); d = ImageDraw.Draw(img); hz = 210; u = t - T_BCUT2
    d.rectangle((0, 34, LW, hz), fill=(40, 40, 40)); R.crowd(d, 34, hz - 20, t, 11); d.rectangle((0, hz - 20, LW, hz), fill=DGRN)
    for i in range(10):
        y0 = hz + (LH - hz) * (i / 10) ** 1.6; y1 = hz + (LH - hz) * ((i + 1) / 10) ** 1.6
        if i % 2: d.rectangle((0, y0, LW, y1), fill=G2)
    d.rectangle((0, hz + 150, LW, LH), fill=NAVY); txt(d, (LW // 2, hz + 200), " ".join(sp["home"]), F(24), WHT, sh=BLU)
    fr = int(t * 8) % 2
    for i in range(7):   # ONC players jumping around, CPU players hands on helmets
        R.player(d, 60 + i * 25, hz + 30 - abs(math.sin(t * 9 + i)) * 10, BLU, fr ^ (i % 2), "down", num="", shadow=False)
    for i in range(3): R.player(d, 90 + i * 45, hz + 52, sp["acol"], 0, "up", num="", shadow=False)
    bx = 60 + 150 * clamp(u / 1.6); by = hz + 110 - abs(math.sin(u * 6)) * 40 * max(0.2, 1 - u / 1.6)
    d.ellipse((bx - 6, by - 4, bx + 6, by + 4), fill=BLK); d.ellipse((bx - 5, by - 3, bx + 5, by + 3), fill=BRN)
    d.rectangle((131, 330, 139, LH), fill=YEL); d.rectangle((50, 326, 220, 334), fill=YEL)
    d.rectangle((50, 40, 58, 334), fill=YEL); d.rectangle((212, 40, 220, 334), fill=YEL)
    wave = int(t * 6) % 2
    def ref(dd, cx, fy):   # arms crossing back and forth: no good
        dd.rectangle((cx - 4, fy - 7, cx - 2, fy), fill=BLK); dd.rectangle((cx + 2, fy - 7, cx + 4, fy), fill=BLK)
        dd.rectangle((cx - 6, fy - 19, cx + 6, fy - 8), fill=WHT)
        for k in range(-6, 7, 3): dd.line((cx + k, fy - 19, cx + k, fy - 8), fill=BLK)
        if wave: dd.line((cx - 12, fy - 22, cx + 12, fy - 12), fill=WHT, width=2); dd.line((cx - 12, fy - 12, cx + 12, fy - 22), fill=WHT, width=2)
        else: dd.line((cx - 14, fy - 16, cx + 14, fy - 16), fill=WHT, width=2)
        dd.ellipse((cx - 4, fy - 26, cx + 4, fy - 18), fill=SKIN); dd.rectangle((cx - 4, fy - 27, cx + 4, fy - 24), fill=BLK)
    R.big(img, ref, 236, 460, 2, (34, 36)); d = ImageDraw.Draw(img)
    if u < 0.05: d.rectangle((0, 0, LW, LH), fill=BLK)
    R.fb_hud(d, sp, sp["home_score"], "0:00")
    v = t - T_BLOCK; R.fireworks(d, u, ((70, 90, 0.0), (200, 110, 0.3), (135, 70, 0.6)))
    R.flash_title(d, v, "NO GOOD!", "", y=150, sub=f"{sp['home']} WINS {sp['home_score']}-{sp['away_score']}")
    return img

def fb_block(t, sp):
    if t < T_BCUT1: return fb_block_behind(t, sp), None
    if t < T_BCUT2: return fb_block_cutin(t, sp), (T_BLOCK if t >= T_BLOCK else None)
    return fb_block_posts(t, sp), T_BLOCK

# =============================================================== sound effects + registration
def sfx(buf, v, add):
    if v == "fb_sack":
        add(buf, R.noise(0.06, 0.15, 0.02, 2), T_SSNAP)
        for k in range(3): add(buf, R.sq(84 + k * 3, 0.06, 0.05, 0.125), 1.0 + k * 0.08)
        add(buf, R.sq(84, 0.3, 0.05, 0.125, slide=-0.4), T_SCUT1)
        add(buf, R.noise(0.25, 0.3, 0.08, 1), T_SHIT); add(buf, R.tri(33, 0.35, 0.35), T_SHIT)
        add(buf, R.noise(0.2, 0.2, 0.06, 2), T_SCUT2)
    if v == "fb_block":
        add(buf, R.noise(0.06, 0.15, 0.02, 2), T_BSNAP); add(buf, R.noise(0.08, 0.2, 0.03, 2), T_BKICK)
        add(buf, R.sq(84, 0.3, 0.05, 0.125, slide=-0.4), T_BCUT1)
        add(buf, R.noise(0.18, 0.3, 0.05, 1), T_BLOCK); add(buf, R.sq(60, 0.4, 0.07, 0.5, slide=-0.6), T_BLOCK)
        for k in range(4): add(buf, R.noise(0.04, 0.12, 0.02, 2), T_BCUT2 + 0.15 + k * 0.3)

def register():
    R.GAMES.update({"fb_sack": fb_sack, "fb_block": fb_block})
    R.PAYOFF.update({"fb_sack": T_SACKED, "fb_block": T_BLOCK})
    R.DEFAULTS.update({
        "fb_sack": {"hook": ["UP BY 4. 0:05 LEFT.", "THEY NEED A TOUCHDOWN."], "home_score": 24, "away_score": 20},
        "fb_block": {"hook": ["UP BY 1. 0:03 LEFT.", "THEY KICK FOR THE WIN."], "home_score": 21, "away_score": 20},
    })
