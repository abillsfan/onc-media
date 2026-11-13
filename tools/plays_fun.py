"""More reel plays for the ONC reel engine (Carl, Nov 13 2026: daily reels need more plays so nothing repeats;
"even if the reels have some humor in them is fine"). Registered into retro_reel's game table, so they work in every
era (tools/era_reel.py). Every play cuts between several camera angles. Original art and sound only.

FOOTBALL
  fb_pick6    = overhead behind the CPU quarterback: he throws, ONC #21 jumps the route -> close-up cut-in: the pick ->
                sideline camera: 70-yard return, and he high-steps the last 10 yards backwards. "PICK SIX!"
  fb_goalline = behind the ONC goal posts: 4th & goal from the 1, CPU back launches over the pile -> close-up cut-in:
                ONC #55 meets him in mid-air -> overhead replay box: ball an inch short. "STOPPED!"
  fb_bucket   = sideline: game's won, two ONC players tiptoe up behind the coach with the bucket ("SHHH...") ->
                close-up: the bucket tips -> front view: the coach, soaked and covered in ice, gives a thumbs-up. "ICE BATH!"
BASEBALL (ONC is the home team protecting a lead in the TOP of the 9th)
  bb_dive     = behind-the-plate camera: sinking liner to center -> sideline-scroll outfield cam: #8 sprints and dives ->
                close-up: skidding face-down, glove pops up with the ball, cap lands on his back. "WHAT A CATCH!"
  bb_dp       = overhead full field: grounder to short, flip to second, throw to first -> cut-in at second: the turn over
                the sliding runner (his helmet flies off) -> ground cam at first: #3 stretches into a full split. "DOUBLE PLAY!"
  bb_nachos   = behind-the-plate camera: high pop foul -> sideline view down the first-base line: #3 races to the rail
                where a fan holds a tray of nachos -> close-up: the ball lands in the nachos, #3 flips over the rail and pops
                up with a cheesy ball. "NACHO CATCH!" (final out)
"""
import math, random
from PIL import Image, ImageDraw
import retro_reel as R
from retro_reel import (LW, LH, YD, BLK, WHT, GRY, DGRY, BLU, LBLU, NAVY, YEL, GOLD, RED, ORG, BRN, SKIN, DIRT, G1, G2,
                        G3, DGRN, PINK, F, txt, fit, clamp, ease, lerp, digits)

KHAKI = (200, 168, 112); ICE = (200, 240, 252); DRINK = (90, 200, 250); CHIP = (248, 200, 64); CHEESE = (252, 160, 0)

def _fball(d, x, y, r=5):
    d.ellipse((x - r * 1.4 - 1, y - r - 1, x + r * 1.4 + 1, y + r + 1), fill=BLK); d.ellipse((x - r * 1.4, y - r, x + r * 1.4, y + r), fill=BRN)
    if r >= 5: d.line((x - r * 0.6, y, x + r * 0.6, y), fill=WHT)

def _bball(d, x, y, r=3):
    d.ellipse((x - r, y - r, x + r, y + r), fill=WHT)
    if r >= 5: d.arc((x - r, y - r, x + r, y + r), 200, 300, fill=RED)

def _stars(d, cx, cy, n=8, r0=10, r1=28, col=YEL):
    for i in range(n):
        a = i * 2 * math.pi / n
        d.line((cx + r0 * math.cos(a), cy + r0 * math.sin(a), cx + r1 * math.cos(a), cy + r1 * math.sin(a)), fill=col, width=3)

def _win(sp, h):
    return f"{sp['home']} WINS {h}-{sp['away_score']}"

def _ump(call):
    """Umpire facing camera. call: None (crouched set), "out" (fist pumped), "safe"."""
    def fn(dd, cx, fy):
        dd.rectangle((cx - 4, fy - 7, cx - 2, fy), fill=NAVY); dd.rectangle((cx + 2, fy - 7, cx + 4, fy), fill=NAVY)
        dd.rectangle((cx - 6, fy - 19, cx + 6, fy - 7), fill=NAVY); dd.ellipse((cx - 4, fy - 26, cx + 4, fy - 18), fill=SKIN)
        dd.rectangle((cx - 5, fy - 27, cx + 5, fy - 24), fill=NAVY)
        if call == "out":
            dd.rectangle((cx + 6, fy - 34, cx + 9, fy - 17), fill=NAVY); dd.rectangle((cx + 5, fy - 38, cx + 10, fy - 33), fill=SKIN)
            dd.rectangle((cx - 9, fy - 17, cx - 6, fy - 10), fill=NAVY)
        else:
            dd.rectangle((cx - 9, fy - 17, cx - 6, fy - 10), fill=NAVY); dd.rectangle((cx + 6, fy - 17, cx + 9, fy - 10), fill=NAVY)
    return fn

# =============================================================== shared baseball camera: behind the plate
def _plate_view(t, sp, t_pitch, t_hit, ball_after):
    """Behind home plate, looking out: ONC pitcher (home team in the field), CPU batter. ball_after(p) -> (x, y, r)."""
    img = Image.new("RGB", (LW, LH), G1); d = ImageDraw.Draw(img)
    R.crowd(d, 34, 104, t, 31); d.rectangle((0, 104, LW, 116), fill=DGRN); d.line((0, 116, LW, 116), fill=YEL)
    txt(d, (LW // 2, 110), "ON-CARDS.COM", F(6), WHT, sh=None)
    for i in range(8):
        if i % 2: d.rectangle((0, 116 + i * 16, LW, 132 + i * 16), fill=G2)
    d.polygon([(135, 196), (262, 336), (135, 480), (8, 336)], fill=DIRT)
    d.polygon([(135, 226), (226, 334), (135, 444), (44, 334)], fill=G1)
    d.ellipse((115, 250, 155, 270), fill=DIRT); d.rectangle((129, 258, 141, 261), fill=WHT)
    for bx, by in ((226, 334), (135, 210), (44, 334)): d.rectangle((bx - 4, by - 3, bx + 4, by + 3), fill=WHT)
    d.line((135, 444, 262, 300), fill=WHT); d.line((135, 444, 8, 300), fill=WHT)
    d.polygon([(127, 446), (143, 446), (143, 452), (135, 458), (127, 452)], fill=WHT)
    for x, y in ((80, 300), (190, 300), (150, 230), (60, 190), (135, 160), (210, 190)):   # ONC fielders
        R.player(d, x, y, BLU, 0, "down", num="", shadow=False)
    wind = clamp(t / t_pitch)
    R.player(d, 135, 262 - (3 if 0.5 < wind < 1 else 0), BLU, 1 if 0.4 < wind < 1 else 0, "down", num="", shadow=False)
    if t_pitch <= t < t_hit:
        p = (t - t_pitch) / (t_hit - t_pitch); _bball(d, lerp(140, 136, p), lerp(250, 436, p ** 1.3), 1 + int(3 * p))
    elif t >= t_hit:
        x, y, r = ball_after(t - t_hit); _bball(d, x, y, r)
    sw = clamp((t - (t_hit - 0.1)) / 0.2); ac = sp["acol"]
    def batter(dd, cx, fy):
        dd.rectangle((cx - 5, fy - 8, cx - 2, fy), fill=GRY); dd.rectangle((cx + 2, fy - 8, cx + 5, fy), fill=GRY)
        dd.rectangle((cx - 6, fy - 19, cx + 6, fy - 8), fill=ac); digits(dd, cx - 3, fy - 18, "17", WHT)
        dd.ellipse((cx - 5, fy - 27, cx + 5, fy - 18), fill=ac)
        hx, hy = cx + 6, fy - 17; a = math.radians(-120 + 230 * sw)
        dd.line((hx, hy, hx + 16 * math.cos(a), hy + 16 * math.sin(a)), fill=(220, 180, 120), width=2)
        dd.rectangle((hx - 2, hy - 1, hx + 1, hy + 2), fill=SKIN)
    R.big(img, batter, 100, 470, 2, (48, 40))
    def catcher(dd, cx, fy):
        dd.rectangle((cx - 7, fy - 9, cx + 7, fy), fill=GRY); dd.ellipse((cx - 5, fy - 16, cx + 5, fy - 7), fill=BLU)
        dd.rectangle((cx + 6, fy - 12, cx + 10, fy - 8), fill=BRN)
    R.big(img, catcher, 142, 492, 2, (26, 20))
    d = ImageDraw.Draw(img)
    if t_hit <= t < t_hit + 0.06: d.rectangle((0, 0, LW, LH), fill=WHT)
    return img, d

def _bb_hud(d, sp, home):
    R.bb_hud(d, sp, home, inning="TOP 9TH")

# =============================================================== BASEBALL: diving catch (bb_dive)
T_VPITCH, T_VHIT, T_VCUT1, T_VDIVE, T_VCUT2, T_VCATCH = 0.6, 1.05, 1.5, 2.25, 2.55, 3.2
def bb_dive_plate(t, sp):
    img, d = _plate_view(t, sp, T_VPITCH, T_VHIT, lambda u: (lerp(136, 150, clamp(u / 0.45)), lerp(430, 150, clamp(u / 0.45) ** 0.7), max(1, int(4 - 3 * clamp(u / 0.45)))))
    _bb_hud(d, sp, sp["home_score"])
    R.hook_text(d, sp, t, until=T_VHIT - 0.03, y=150, box=True)
    if t >= T_VHIT: R.bar(d, 160, 28); txt(d, (LW // 2, 160), "SINKING LINER!", fit("SINKING LINER!", LW - 12, 16), YEL)
    return img

def bb_dive_outfield(t, sp):
    """Side-scrolling camera across shallow center: fielder sprints right, lays out."""
    img = Image.new("RGB", (LW, LH), G1); d = ImageDraw.Draw(img); u = t - T_VCUT1
    R.crowd(d, 34, 140, t, 33, 6); d.rectangle((0, 140, LW, 168), fill=DGRN); d.line((0, 140, LW, 140), fill=YEL)
    scroll = int(u * 160)
    for i in range(-1, 6):
        x0 = i * 64 - scroll % 64
        d.rectangle((x0 + 4, 146, x0 + 58, 162), fill=[NAVY, (168, 16, 0)][(i + scroll // 64) % 2])
    d.rectangle((0, 168, LW, 192), fill=DIRT)
    for i in range(14):
        x0 = i * 40 - (scroll * 2) % 80
        d.rectangle((x0, 192, x0 + 20, LH), fill=G2)
    dive = t >= T_VDIVE; fx = 60 + 70 * ease(u / (T_VDIVE - T_VCUT1))
    if not dive:
        R.big(img, lambda dd, cx, fy: R.side_player(dd, cx, fy, BLU, int(t * 12) % 2, 1, num="8", shadow=False), fx, 380, 3, (40, 34))
    else:
        v = t - T_VDIVE
        R.big(img, lambda dd, cx, fy: R.diver(dd, cx, fy, BLU), fx + 40 * ease(v / 0.3), 380 - 22 * math.sin(math.pi * clamp(v / 0.3)), 3, (44, 20))
    d = ImageDraw.Draw(img)
    q = clamp(u / (T_VCUT2 - T_VCUT1)); bx, by = lerp(-10, 196, q), lerp(200, 330, q) - math.sin(math.pi * q) * 70
    _bball(d, bx, by, 4)
    _bb_hud(d, sp, sp["home_score"]); R.bar(d, 90, 28)
    txt(d, (LW // 2, 90), "HE'S GOT A SHOT..." if not dive else "HE LAYS OUT!", fit("HE'S GOT A SHOT...", LW - 12, 16), YEL if not dive else LBLU)
    return img

def bb_dive_closeup(t, sp):
    """Close-up: face-down skid, glove pops up with the ball, cap lands on his back."""
    img = Image.new("RGB", (LW, LH), G1); u = t - T_VCUT2; d = ImageDraw.Draw(img)
    for i in range(10):
        if i % 2: d.rectangle((0, 140 + i * 34, LW, 174 + i * 34), fill=G2)
    skid = 60 * ease(u / 0.5)
    R.big(img, lambda dd, cx, fy: R.diver(dd, cx, fy, BLU), 110 + skid, 360, 5, (44, 20))
    d = ImageDraw.Draw(img)
    rnd = random.Random(int(t * 12))
    if u < 0.9:   # grass chunks flying
        for _ in range(10):
            px, py = 40 + skid + rnd.randint(0, 50), 330 - rnd.randint(0, 50) * min(1, u * 3)
            d.rectangle((px, py, px + 4, py + 3), fill=rnd.choice([G3, DGRN, (120, 80, 30)]))
    gx = 110 + skid + 17 * 5 - 30; gy = 340
    caught = t >= T_VCATCH
    if caught:   # glove arm shoots straight up, ball in the glove
        d.rectangle((gx - 4, gy - 70, gx + 4, gy - 10), fill=BLU)
        d.rectangle((gx - 10, gy - 88, gx + 10, gy - 66), fill=BRN); _bball(d, gx, gy - 80, 6)
    else:
        q = clamp(u / (T_VCATCH - T_VCUT2)); _bball(d, lerp(gx + 120, gx, q), lerp(150, gy - 10, q), 7)
    cq = clamp((u - 0.2) / 0.8)   # cap flies off and lands on his back
    cx, cy = lerp(110 + skid + 70, 110 + skid - 10, cq), lerp(330, 312, cq) - math.sin(math.pi * cq) * 80
    d.pieslice((cx - 13, cy - 11, cx + 13, cy + 11), 180, 360, fill=WHT); d.pieslice((cx - 12, cy - 10, cx + 12, cy + 10), 180, 360, fill=NAVY)
    d.rectangle((cx + 8, cy - 2, cx + 22, cy + 2), fill=NAVY); txt(d, (cx, cy - 4), "O", F(6), WHT, sh=None)
    R.letterbox(d, 110, 420)
    _bb_hud(d, sp, sp["home_score"])
    if not caught: txt(d, (LW // 2, 445), "DID HE HOLD ON?!", fit("DID HE HOLD ON?!", LW - 12, 16), WHT)
    else:
        v = t - T_VCATCH; R.fireworks(d, v, ((60, 160, 0.0), (210, 170, 0.3), (135, 140, 0.6)))
        R.flash_title(d, v, "WHAT A", "CATCH!", y=60, sub=None)
        if v > 0.6: txt(d, (LW // 2, 445), _win(sp, sp["home_score"]), fit(_win(sp, sp["home_score"]), LW - 16, 16), [YEL, WHT][int(v * 6) % 2])
        if v > 1.0: txt(d, (LW // 2, 128), "(HE'S GOT GRASS IN HIS TEETH)", fit("(HE'S GOT GRASS IN HIS TEETH)", LW - 16, 8), WHT)
    return img

def bb_dive(t, sp):
    if t < T_VCUT1: return bb_dive_plate(t, sp), None
    if t < T_VCUT2: return bb_dive_outfield(t, sp), None
    return bb_dive_closeup(t, sp), (T_VCATCH if t >= T_VCATCH else None)

# =============================================================== BASEBALL: game-ending double play (bb_dp)
T_DHIT, T_DFLIP, T_DCUT1, T_DTURN, T_DCUT2, T_DOUT = 0.5, 1.35, 1.75, 2.15, 2.6, 3.25
HOME, B1, B2, B3 = (135, 446), (205, 376), (135, 306), (65, 376)
SS = (100, 330)
def _bb_overhead_field(d, t, seed=37):
    R.crowd(d, 34, 96, t, seed, 6); d.rectangle((0, 96, LW, 104), fill=DGRN); d.line((0, 104, LW, 104), fill=YEL)
    d.rectangle((0, 104, LW, 116), fill=DIRT)
    for i in range(12):
        if i % 2: d.rectangle((0, 116 + i * 26, LW, 142 + i * 26), fill=G2)
    d.polygon([(135, 270), (240, 376), (135, 480), (30, 376)], fill=DIRT)
    d.polygon([(135, 316), (195, 376), (135, 436), (75, 376)], fill=G1)
    d.ellipse((125, 366, 145, 386), fill=DIRT)
    d.line((135, 446, LW, 446 - 135), fill=WHT); d.line((135, 446, 0, 446 - 135), fill=WHT)
    for bx, by in (B1, B2, B3): d.rectangle((bx - 4, by - 3, bx + 4, by + 3), fill=WHT)
    d.polygon([(130, 444), (140, 444), (140, 448), (135, 451), (130, 448)], fill=WHT)

def bb_dp_overhead(t, sp):
    img = Image.new("RGB", (LW, LH), G1); d = ImageDraw.Draw(img); _bb_overhead_field(d, t)
    fr = int(t * 10) % 2; ac = sp["acol"]
    if t < T_DHIT: bx, by, h = 135, lerp(376, 446, t / T_DHIT), 0
    elif t < T_DFLIP - 0.25:   # bouncer to short
        p = clamp((t - T_DHIT) / (T_DFLIP - 0.25 - T_DHIT)); bx, by = lerp(135, SS[0] + 4, p), lerp(446, SS[1], p); h = abs(math.sin(p * 9)) * 10 * (1 - p)
    elif t < T_DFLIP: bx, by, h = SS[0] + 4, SS[1], 6
    else:   # flip to second
        p = clamp((t - T_DFLIP) / 0.35); bx, by = lerp(SS[0] + 4, B2[0], p), lerp(SS[1], B2[1] + 4, p); h = math.sin(math.pi * p) * 10
    for (x, y) in ((B1[0] - 6, B1[1] - 8), (B3[0] + 6, B3[1] - 8), (135, 376), (140, 470), (60, 190), (135, 160), (210, 190)):
        R.player(d, x, y, BLU, 0, "down", num="", shadow=False)
    R.player(d, SS[0], SS[1], BLU, fr if T_DHIT < t < T_DFLIP else 0, "down", num="6")
    sb = R._path(t, [(150, 330), B2], T_DHIT, T_DFLIP + 0.3); R.player(d, sb[0], sb[1], BLU, fr, "up", num="4")
    r1 = R._path(t, [(B1[0] - 10, B1[1] - 6), B2], T_DHIT, 2.3); R.player(d, r1[0], r1[1], ac, fr, "up", num="")
    bt = R._path(t, [HOME, B1], T_DHIT + 0.1, 3.4); R.player(d, bt[0], bt[1], ac, fr, "up", num="")
    for b0, b1 in ((B2, B3), (B3, HOME)):
        r = R._path(t, [b0, b1], T_DHIT, 2.4); R.player(d, r[0], r[1], ac, fr, "down", num="")
    d.ellipse((bx - 3, by - 1, bx + 3, by + 2), fill=(0, 100, 0)); _bball(d, bx, by - h, 3)
    _bb_hud(d, sp, sp["home_score"])
    R.hook_text(d, sp, t, until=T_DHIT, y=160, box=True)
    if t >= T_DHIT:
        R.bar(d, 240, 28)
        msg = "LINED... NO, A GROUNDER!" if t < T_DFLIP - 0.25 else "FLIP TO SECOND!"
        txt(d, (LW // 2, 240), msg, fit(msg, LW - 12, 16), YEL)
    return img

def bb_dp_turn(t, sp):
    """Cut-in at second: the turn over the sliding runner, whose helmet pops off."""
    img = Image.new("RGB", (LW, LH), BLK); u = t - T_DCUT1
    d = R.speed_lines(img, t, (88, 40, 16), (152, 80, 32), 135, 300)
    d.rectangle((0, 330, LW, 410), fill=DIRT); d.rectangle((120, 336, 150, 344), fill=WHT)
    slide = ease(u / 0.45); jumped = t >= T_DTURN
    def runner(dd, cx, fy):
        dd.rectangle((cx - 14, fy - 10, cx - 2, fy - 4), fill=sp["acol"]); dd.rectangle((cx - 2, fy - 7, cx + 12, fy - 3), fill=GRY)
        dd.rectangle((cx + 12, fy - 6, cx + 16, fy - 2), fill=BLK); dd.ellipse((cx - 20, fy - 15, cx - 12, fy - 7), fill=SKIN)
    R.big(img, runner, lerp(-40, 118, slide), 380, 3, (44, 24))
    jump = math.sin(math.pi * clamp((t - (T_DTURN - 0.2)) / 0.5)) * 50
    def fielder(dd, cx, fy):
        R.side_player(dd, cx, fy, BLU, 1 if jumped else 0, 1, num="4", shadow=False, arm_back=not jumped)
    R.big(img, fielder, 150, 370 - jump, 3, (40, 34))
    d = ImageDraw.Draw(img)
    if not jumped:
        q = clamp(u / (T_DTURN - T_DCUT1)); _bball(d, lerp(-10, 160, q), lerp(250, 270 - jump, q), 5)
    else:
        v = t - T_DTURN; _bball(d, 170 + 300 * v, 260 - jump - 40 * v, 5)
        hq = clamp(v / 0.6); hx, hy = lerp(70, 30, hq), 330 - math.sin(math.pi * hq) * 90   # helmet pops off
        d.pieslice((hx - 12, hy - 10, hx + 12, hy + 10), 180, 360, fill=sp["acol"])
        if v < 0.3: _stars(d, 150, 230, 8, 10, 24)
        rnd = random.Random(int(t * 15))
        for _ in range(12):
            px, py = 110 + rnd.randint(-40, 40), 360 + rnd.randint(-30, 10); s = rnd.randint(3, 8)
            d.rectangle((px, py, px + s, py + s), fill=(230, 190, 140))
    R.letterbox(d, 140, 410)
    _bb_hud(d, sp, sp["home_score"])
    msg = "TURN TWO!" if jumped else "HERE COMES THE RUNNER..."
    txt(d, (LW // 2, 100), msg, fit(msg, LW - 12, 24 if jumped else 12), [YEL, WHT][int(u * 10) % 2] if jumped else WHT)
    return img

def bb_dp_first(t, sp):
    """Ground cam at first base: #3 stretches into a full split, ball pops into the mitt, ump rings him up."""
    img, d = _ground_cam_bb(t)
    u = t - T_DCUT2; out = t >= T_DOUT
    split = ease(u / 0.5)
    def first_baseman(dd, cx, fy):
        w = int(4 + 12 * split)
        dd.rectangle((cx - w - 2, fy - 3, cx - 2, fy), fill=WHT); dd.rectangle((cx + 2, fy - 3, cx + w + 2, fy), fill=WHT)
        dd.rectangle((cx - w - 4, fy - 2, cx - w - 2, fy), fill=BLK); dd.rectangle((cx + w + 2, fy - 2, cx + w + 4, fy), fill=BLK)
        dd.rectangle((cx - 5, fy - 15, cx + 5, fy - 3), fill=BLU); digits(dd, cx - 1, fy - 14, "3", WHT)
        dd.ellipse((cx - 4, fy - 23, cx + 4, fy - 15), fill=BLU)
        dd.rectangle((cx - 12 - int(4 * split), fy - 13, cx - 5, fy - 11), fill=BLU)
        dd.rectangle((cx - 18 - int(4 * split), fy - 16, cx - 11 - int(4 * split), fy - 9), fill=BRN)
    fy = 380 - int(30 * split)
    R.big(img, first_baseman, 150, 380, 4, (50, 30))
    d = ImageDraw.Draw(img)
    gx = 150 + (-15 - 4 * split) * 4
    if not out:
        q = clamp(u / (T_DOUT - T_DCUT2)); _bball(d, lerp(-10, gx, q), lerp(250, 340, q), 6)
        R.big(img, lambda dd, cx, fy: R.side_player(dd, cx, fy, sp["acol"], int(t * 12) % 2, 1, num="", shadow=False), lerp(LW + 30, 220, q), 360, 3, (40, 34))
        d = ImageDraw.Draw(img)
        txt(d, (LW // 2, 130), "STRETCH!!", F(24), [YEL, WHT][int(t * 8) % 2])
    else:
        v = t - T_DOUT
        _bball(d, gx, 340, 6)
        R.big(img, lambda dd, cx, fy: R.side_player(dd, cx, fy, sp["acol"], 0, -1, num="", shadow=False), 225, 360, 3, (40, 34))
        R.big(img, _ump("out"), 50, 330, 2, (30, 44))
        d = ImageDraw.Draw(img)
        if v < 0.3: _stars(d, gx, 340, 8, 12, 30)
        R.fireworks(d, v, ((60, 90, 0.2), (210, 100, 0.45), (135, 70, 0.7)))
        R.flash_title(d, v, "DOUBLE", "PLAY!", y=110, sub=_win(sp, sp["home_score"]))
        if v > 1.1: txt(d, (LW // 2, 445), "(DON'T TRY THAT SPLIT AT HOME)", fit("(DON'T TRY THAT SPLIT AT HOME)", LW - 16, 8), WHT)
    _bb_hud(d, sp, sp["home_score"])
    return img

def _ground_cam_bb(t, hz=200):
    img = Image.new("RGB", (LW, LH), G1); d = ImageDraw.Draw(img)
    R.crowd(d, 34, hz - 22, t, 41); d.rectangle((0, hz - 22, LW, hz), fill=DGRN)
    txt(d, (LW // 2, hz - 11), "OUTTA NOWHERE CARDS", F(6), WHT, sh=None)
    d.rectangle((0, hz, LW, hz + 60), fill=G2); d.rectangle((0, hz + 60, LW, LH), fill=DIRT)
    d.rectangle((140, 372, 176, 384), fill=WHT)
    return img, d

def bb_dp(t, sp):
    if t < T_DCUT1: return bb_dp_overhead(t, sp), None
    if t < T_DCUT2: return bb_dp_turn(t, sp), None
    return bb_dp_first(t, sp), (T_DOUT if t >= T_DOUT else None)

# =============================================================== BASEBALL: nacho catch (bb_nachos)
T_NPITCH, T_NHIT, T_NCUT1, T_NCUT2, T_NCATCH = 0.6, 1.05, 1.6, 2.55, 3.15
RAIL_X = 196
def _nacho_tray(d, x, y, full=True, cheese_ball=False):
    d.polygon([(x - 20, y), (x + 20, y), (x + 16, y + 8), (x - 16, y + 8)], fill=WHT)
    if full:
        for k in range(7):
            cx = x - 15 + k * 5; d.polygon([(cx - 4, y), (cx + 4, y), (cx, y - 7 - (k % 2) * 2)], fill=CHIP)
        d.ellipse((x - 9, y - 6, x + 9, y + 1), fill=CHEESE)

def bb_nachos_plate(t, sp):
    img, d = _plate_view(t, sp, T_NPITCH, T_NHIT, lambda u: (lerp(140, 250, clamp(u / 0.55)), lerp(430, 40, clamp(u / 0.55) ** 0.6), max(1, int(4 - 3 * clamp(u / 0.55)))))
    _bb_hud(d, sp, sp["home_score"])
    R.hook_text(d, sp, t, until=T_NHIT - 0.03, y=150, box=True)
    if t >= T_NHIT:
        R.bar(d, 160, 28); msg = "WAY UP... FOUL SIDE!" if t > T_NHIT + 0.25 else "POPPED UP!"
        txt(d, (LW // 2, 160), msg, fit(msg, LW - 12, 16), YEL)
    return img

def _fan(dd, cx, fy, mouth_open=False, empty=False):
    dd.rectangle((cx - 7, fy - 20, cx + 7, fy), fill=WHT); digits(dd, cx - 3, fy - 17, "1", BLU)
    dd.ellipse((cx - 6, fy - 32, cx + 6, fy - 20), fill=SKIN)
    dd.pieslice((cx - 7, fy - 36, cx + 7, fy - 24), 180, 360, fill=BLU); dd.rectangle((cx + 3, fy - 31, cx + 11, fy - 29), fill=BLU)
    dd.point((cx - 2, fy - 27), fill=BLK); dd.point((cx + 2, fy - 27), fill=BLK)
    if mouth_open: dd.ellipse((cx - 2, fy - 25, cx + 2, fy - 21), fill=BLK)
    else: dd.line((cx - 2, fy - 23, cx + 2, fy - 23), fill=BLK)

def bb_nachos_line(t, sp):
    """Down the first-base line: #3 sprints toward the rail; a fan up front holds a tray of nachos."""
    img = Image.new("RGB", (LW, LH), G1); d = ImageDraw.Draw(img); u = t - T_NCUT1
    R.crowd(d, 34, 250, t, 43, 6)
    d.rectangle((RAIL_X, 250, LW, 420), fill=(60, 60, 60)); d.rectangle((RAIL_X - 4, 300, RAIL_X, 420), fill=GRY)
    d.rectangle((0, 250, RAIL_X - 4, 420), fill=G1)
    for i in range(6):
        if i % 2: d.rectangle((0, 250 + i * 30, RAIL_X - 4, 280 + i * 30), fill=G2)
    d.rectangle((0, 420, LW, LH), fill=DIRT); d.line((0, 300, RAIL_X - 4, 418), fill=WHT, width=2)
    R.big(img, lambda dd, cx, fy: _fan(dd, cx, fy, mouth_open=u > 0.5), 232, 330, 2, (30, 40))
    d = ImageDraw.Draw(img); _nacho_tray(d, 214, 300)
    fx = lerp(20, RAIL_X - 18, ease(u / (T_NCUT2 - T_NCUT1)))
    R.big(img, lambda dd, cx, fy: R.side_player(dd, cx, fy, BLU, int(t * 12) % 2, 1, num="3", shadow=False), fx, 400, 3, (40, 34))
    d = ImageDraw.Draw(img)
    q = clamp(u / (T_NCUT2 - T_NCUT1)); _bball(d, lerp(160, 212, q), lerp(60, 230, q ** 1.5), 4)
    _bb_hud(d, sp, sp["home_score"]); R.bar(d, 90, 28)
    msg = "HE'S RUNNING OUT OF ROOM..." if u > 0.4 else "#3 IS ON HIS HORSE!"
    txt(d, (LW // 2, 90), msg, fit(msg, LW - 12, 16), YEL)
    if u > 0.5: txt(d, (232, 252), "!!", F(16), YEL)
    return img

def bb_nachos_closeup(t, sp):
    """Close-up at the rail: ball drops into the nachos, #3 flips over and pops up with a cheesy ball."""
    img = Image.new("RGB", (LW, LH), BLK); u = t - T_NCUT2
    d = R.speed_lines(img, t, (120, 60, 0), (200, 110, 0), 200, 220)
    caught = t >= T_NCATCH
    R.big(img, lambda dd, cx, fy: _fan(dd, cx, fy, mouth_open=True), 200, 380, 4, (30, 40))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 370, LW, 384), fill=GRY)   # the rail
    if not caught:
        _nacho_tray(d, 160, 300)
        q = clamp(u / (T_NCATCH - T_NCUT2)); _bball(d, 160 + 10 * (1 - q), lerp(50, 292, q ** 1.6), 7)
        flip = clamp(u / (T_NCATCH - T_NCUT2))
        R.big(img, lambda dd, cx, fy: R.diver(dd, cx, fy, BLU), lerp(-30, 110, flip), lerp(400, 330, flip), 4, (44, 20))
        d = ImageDraw.Draw(img)
        txt(d, (LW // 2, 70), "INTO THE STANDS!", fit("INTO THE STANDS!", LW - 12, 16), WHT)
    else:
        v = t - T_NCATCH
        _nacho_tray(d, 230, 380, full=False)
        R.big(img, lambda dd, cx, fy: R.player(dd, cx, fy, BLU, 0, "down", num="3", shadow=False, arms="up"), 100, 440, 4, (30, 44))
        d = ImageDraw.Draw(img)
        bx, by = 100 + 30, 440 - 33 * 4 - 8
        _bball(d, bx, by, 9)
        d.ellipse((bx - 6, by - 6, bx + 6, by + 2), fill=CHEESE)
        for k in range(4): d.rectangle((bx - 8 + k * 5, by + 9 + (k % 2) * 6 + int(v * 30) % 12, bx - 6 + k * 5, by + 13 + (k % 2) * 6 + int(v * 30) % 12), fill=CHEESE)
        for k in range(5):   # chips raining down
            cx, cy = 40 + k * 46, (60 + k * 37 + v * 220) % 360 + 40
            d.polygon([(cx - 4, cy), (cx + 4, cy), (cx, cy - 7)], fill=CHIP)
        if v < 0.3: _stars(d, bx, by, 8, 12, 30)
        R.fireworks(d, v, ((60, 120, 0.2), (210, 130, 0.45)))
        R.flash_title(d, v, "NACHO", "CATCH!", y=70, sub=_win(sp, sp["home_score"]))
        if v > 0.9: txt(d, (210, 290), "MY NACHOS!", fit("MY NACHOS!", 110, 8), WHT)
    _bb_hud(d, sp, sp["home_score"])
    return img

def bb_nachos(t, sp):
    if t < T_NCUT1: return bb_nachos_plate(t, sp), None
    if t < T_NCUT2: return bb_nachos_line(t, sp), None
    return bb_nachos_closeup(t, sp), (T_NCATCH if t >= T_NCATCH else None)

# =============================================================== FOOTBALL: pick six (fb_pick6)
T_PSNAP, T_PTHROW, T_PCUT1, T_PINT, T_PCUT2, T_PTD = 0.4, 1.05, 1.45, 1.85, 2.3, 3.85
PLOS = 30 * YD
def _p_qb_y(t): return PLOS + 10 + 30 * ease((t - T_PSNAP) / 0.6)

def fb_pick6_overhead(t, sp):
    cam = PLOS - 20
    img, d, off = R.fb_field(cam, t, sp); fr = int(t * 10) % 2; ac = sp["acol"]; go = t > T_PSNAP
    run = lambda t0, spd: max(0.0, t - t0) * spd
    tgt = (196, PLOS - 72)
    wx, wy = lerp(220, tgt[0], clamp((t - T_PSNAP) / 0.9)), PLOS - 4 - min(68, run(T_PSNAP, 90))
    R.player(d, wx, wy + off, ac, fr if go else 0, "up", num="84")
    dbx = lerp(150, tgt[0] - 6, ease((t - 0.8) / 0.55)); dby = lerp(PLOS - 50, tgt[1] - 6, ease((t - 0.8) / 0.55))
    R.player(d, dbx, dby + off, BLU, fr if go else 0, "down", num="21")
    R.player(d, 50, PLOS - 4 - run(T_PSNAP, 100) + off, ac, fr if go else 0, "up", num="11")
    R.player(d, 60, PLOS - 40 - run(T_PSNAP, 80) + off, BLU, fr if go else 0, "down", num="")
    push = 3 * math.sin(t * 9) if go else 0
    for i in range(5): R.player(d, 87 + i * 24, PLOS + 8 + off + push * (1 if i % 2 else -1) * 0.5, ac, fr if go else 0, "up", num="", shadow=False)
    for i in range(4): R.player(d, 99 + i * 24, PLOS - 4 + off - push * (1 if i % 2 else -1) * 0.5, BLU, fr if go else 0, "down", num="", shadow=False)
    R.player(d, 135, _p_qb_y(t) + off, ac, 0, "up", ball=t < T_PTHROW, num="9")
    if t >= T_PTHROW:
        p = clamp((t - T_PTHROW) / (T_PCUT1 + 0.1 - T_PTHROW)); bx, by = lerp(140, tgt[0], p), lerp(_p_qb_y(T_PTHROW) - 20, tgt[1] - 14, p) - math.sin(math.pi * p) * 20
        _fball(d, bx, by + off, 4)
    R.fb_hud(d, sp, sp["home_score"], "0:20" if t < T_PSNAP else "0:1" + str(max(0, 9 - int((t - T_PSNAP) * 3))))
    R.hook_text(d, sp, t, until=T_PTHROW, y=58)
    if t >= T_PTHROW: R.bar(d, 62, 26); txt(d, (LW // 2, 62), "HE THROWS IT...", fit("HE THROWS IT...", LW - 12, 16), YEL)
    return img

def fb_pick6_cutin(t, sp):
    img = Image.new("RGB", (LW, LH), BLK); u = t - T_PCUT1
    R.speed_lines(img, t, (16, 40, 120), (40, 88, 200), LW // 2, 200)
    picked = t >= T_PINT
    jump = math.sin(math.pi * clamp(u / 0.8)) * 40
    R.big(img, lambda dd, cx, fy: R.side_player(dd, cx, fy, sp["acol"], 0, 1, num="84", shadow=False), 80, 380, 4, (40, 34))
    R.big(img, lambda dd, cx, fy: R.player(dd, cx, fy, BLU, 0, "down", num="21", shadow=False, arms="up"), 165, 390 - jump, 4, (30, 44))
    d = ImageDraw.Draw(img)
    hx, hy = 165, 390 - jump - 33 * 4 + 6
    if not picked:
        q = clamp(u / (T_PINT - T_PCUT1)); _fball(d, lerp(-20, hx, q), lerp(120, hy, q), 8)
        txt(d, (LW // 2, 430), "#21 READ IT ALL THE WAY!", fit("#21 READ IT ALL THE WAY!", LW - 12, 12), WHT)
    else:
        v = t - T_PINT; _fball(d, hx, hy, 8)
        if v < 0.06: d.rectangle((0, 0, LW, LH), fill=WHT)
        _stars(d, hx, hy, 10, 14, 34)
        R.flash_title(d, v, "PICKED OFF!", "", y=430)
    R.fb_hud(d, sp, sp["home_score"], "0:14")
    return img

def _p6_x(t):
    return min(106, lerp(32, 106, clamp((t - T_PCUT2) / (T_PTD + 0.1 - T_PCUT2)) ** 0.9))

def fb_pick6_sideline(t, sp):
    rx = _p6_x(t); cam = max(20, min(rx - 4, 92))
    img, d, X = R.side_field(cam, t, sp); fr = int(t * 14) % 2; ac = sp["acol"]
    backwards = rx > 88 and t < T_PTD
    for k, (y, lag) in enumerate([(240, 9), (290, 14), (220, 20)]):
        px = rx - lag - 4 * (t - T_PCUT2)
        if k == 0 and t > 3.2: R.side_fallen(d, X(px + 4), y, ac, 1)
        elif -20 < X(px) < LW + 20: R.side_player(d, X(px), y, ac, fr, 1, num="9" if k == 0 else "")
    if backwards:   # high-steppin' the last 10 yards, facing back at the defense
        bob = 6 * abs(math.sin(t * 22))
        R.side_player(d, X(rx), 262 - bob, BLU, fr, -1, ball=True, num="21")
    else:
        R.side_player(d, X(rx), 262, BLU, fr, 1, ball=True, num="21")
    td = t >= T_PTD; home = sp["home_score"] + (6 if td else 0)
    R.fb_hud(d, sp, home, "0:00" if td else "0:0" + str(max(1, 9 - int((t - T_PCUT2) * 4))), flash=not td and int(t * 4) % 2 == 0)
    if not td:
        R.bar(d, 86, 28); msg = "HIGH STEPPIN'!" if backwards else "HE'S GOT NOTHING BUT GRASS!"
        txt(d, (LW // 2, 86), msg, fit(msg, LW - 12, 16), YEL if backwards else LBLU)
    else:
        v = t - T_PTD; R.fireworks(d, v, ((60, 110, 0.0), (210, 120, 0.3), (135, 90, 0.6)))
        R.flash_title(d, v, "PICK", "SIX!", y=420, sub=None)
        if v > 0.6: R.bar(d, 120, 26); txt(d, (LW // 2, 120), _win(sp, home), fit(_win(sp, home), LW - 16, 12), WHT)
    return img

def fb_pick6(t, sp):
    if t < T_PCUT1: return fb_pick6_overhead(t, sp), None
    if t < T_PCUT2: return fb_pick6_cutin(t, sp), None
    return fb_pick6_sideline(t, sp), (T_PTD if t >= T_PTD else None)

# =============================================================== FOOTBALL: goal-line stand (fb_goalline)
T_GSNAP, T_GLEAP, T_GCUT1, T_GHIT, T_GCUT2, T_GSTOP = 0.75, 1.05, 1.4, 1.9, 2.45, 3.3
def fb_goalline_behind(t, sp):
    """Behind the ONC goal posts, looking out at the goal line: the CPU back launches over the pile."""
    img = Image.new("RGB", (LW, LH), G1); d = ImageDraw.Draw(img); ac = sp["acol"]; hz = 120
    R.crowd(d, 34, hz - 26, t, 47); d.rectangle((0, hz - 26, LW, hz), fill=NAVY)
    txt(d, (LW // 2, hz - 13), "GOAL LINE STAND", F(8), YEL, sh=None)
    for i in range(14):
        y0, y1 = R.persp_y(i / 14), R.persp_y((i + 1) / 14)
        if i % 2: d.rectangle((0, y0, LW, y1), fill=G2)
    d.rectangle((0, 300, LW, LH), fill=NAVY); txt(d, (LW // 2, 400), " ".join(sp["home"]), F(32), WHT, sh=BLU)
    d.line((0, 300, LW, 300), fill=WHT, width=3)
    fr = int(t * 8) % 2; go = t > T_GSNAP
    for i in range(7): R.player(d, 50 + i * 28, 262, ac, fr if go else 0, "down", num="", shadow=False)
    leap = clamp((t - T_GLEAP) / 0.5)
    rb_y = lerp(232, 250, leap) - math.sin(math.pi * min(1, leap)) * 70 if t > T_GLEAP else 232
    R.big(img, lambda dd, cx, fy: R.player(dd, cx, fy, ac, 0, "down", num="32", shadow=False, ball=True, arms="up" if t > T_GLEAP else "side"), 135, rb_y, 2, (30, 44))
    d = ImageDraw.Draw(img)
    for i in range(7): R.player(d, 50 + i * 28, 296 + (4 if go else 0), BLU, fr if go else 0, "up", num="", shadow=False)
    R.big(img, lambda dd, cx, fy: R.player(dd, cx, fy, BLU, 0, "up", num="55", shadow=False, arms="up" if t > T_GLEAP else "side"), 150, 330, 2, (30, 44))
    d = ImageDraw.Draw(img)
    d.rectangle((134, 380, 136, LH), fill=YEL); d.rectangle((60, 376, 210, 382), fill=YEL)
    d.rectangle((60, 200, 64, 382), fill=YEL); d.rectangle((206, 200, 210, 382), fill=YEL)
    R.fb_hud(d, sp, sp["home_score"], "0:01", flash=int(t * 4) % 2 == 0)
    R.hook_text(d, sp, t, until=T_GLEAP, y=430, box=True)
    if t >= T_GLEAP: R.bar(d, 445, 28); txt(d, (LW // 2, 445), "HE GOES AIRBORNE!", fit("HE GOES AIRBORNE!", LW - 12, 16), YEL)
    return img

def fb_goalline_cutin(t, sp):
    """Side close-up: back flying right toward the goal line, #55 meets him in mid-air."""
    img = Image.new("RGB", (LW, LH), BLK); u = t - T_GCUT1
    R.speed_lines(img, t, (88, 16, 24), (152, 40, 48), LW // 2, 240)
    hit = t >= T_GHIT
    d = ImageDraw.Draw(img); d.rectangle((196, 90, 200, 380), fill=WHT)
    if not hit:
        q = ease(clamp(u / (T_GHIT - T_GCUT1)))
        R.big(img, lambda dd, cx, fy: R.diver(dd, cx, fy, sp["acol"]), lerp(-20, 110, q), 250, 4, (44, 20))
        R.big(img, lambda dd, cx, fy: R.diver(dd, cx, fy, BLU, flip=True), lerp(LW + 30, 190, q), 254, 4, (44, 20))
        d = ImageDraw.Draw(img); R.letterbox(d, 90, 400); txt(d, (LW // 2, 430), "#55 MEETS HIM...", fit("#55 MEETS HIM...", LW - 12, 16), WHT)
    else:
        v = t - T_GHIT; shake = int(5 * math.sin(v * 70)) if v < 0.25 else 0
        back = 30 * ease(v / 0.4)
        R.big(img, lambda dd, cx, fy: R.diver(dd, cx, fy, sp["acol"]), 110 - back + shake, 250 + 40 * ease(v / 0.4), 4, (44, 20))
        R.big(img, lambda dd, cx, fy: R.diver(dd, cx, fy, BLU, flip=True), 190 - back * 0.5 + shake, 254, 4, (44, 20))
        d = ImageDraw.Draw(img)
        if v < 0.05: d.rectangle((0, 0, LW, LH), fill=WHT)
        _stars(d, 150, 220, 10, 14, 40)
        R.letterbox(d, 90, 400)
        txt(d, (LW // 2, 435), "WHAM!", F(32) if v < 0.12 else F(24), [YEL, WHT][int(v * 10) % 2])
    R.fb_hud(d, sp, sp["home_score"], "0:00")
    return img

def fb_goalline_replay(t, sp):
    """Overhead pile at the goal line + a zoomed replay box: the ball is an inch short."""
    img, d, off = R.fb_field(30, t, sp); u = t - T_GCUT2
    rnd = random.Random(7)
    for k in range(16):   # the pile
        x, y = 100 + rnd.randint(0, 70), off + 4 + rnd.randint(-6, 22)
        R.player(d, x, y, BLU if k % 2 else sp["acol"], 0, "up" if k % 3 else "down", num="", shadow=False)
    d.rectangle((40, 290, 230, 440), fill=BLK); d.rectangle((44, 294, 226, 436), fill=G1)
    d.rectangle((44, 294, 226, 340), fill=NAVY); d.line((44, 340, 226, 340), fill=WHT, width=4)
    zoom = ease(clamp(u / 0.6))
    _fball(d, 135, lerp(390, 362, zoom), int(lerp(8, 14, zoom)))
    txt(d, (135, 306), "REPLAY", F(8), YEL, sh=None)
    if u > 0.6:
        d.rectangle((131, 342, 139, 346), fill=YEL); txt(d, (192, 352), "1 INCH", F(8), YEL)
    stop = t >= T_GSTOP
    R.fb_hud(d, sp, sp["home_score"], "0:00")
    if not stop: R.bar(d, 110, 28); txt(d, (LW // 2, 110), "DID HE GET IN?", fit("DID HE GET IN?", LW - 12, 16), WHT)
    else:
        v = t - T_GSTOP; R.fireworks(d, v, ((60, 120, 0.0), (210, 130, 0.3), (135, 100, 0.6)))
        R.flash_title(d, v, "STOPPED!", "", y=110, sub=_win(sp, sp["home_score"]))
        if v > 1.0: R.bar(d, 462, 20); txt(d, (LW // 2, 462), "(BY THE WIDTH OF A PENNY SLEEVE)", fit("(BY THE WIDTH OF A PENNY SLEEVE)", LW - 16, 8), WHT)
    return img

def fb_goalline(t, sp):
    if t < T_GCUT1: return fb_goalline_behind(t, sp), None
    if t < T_GCUT2: return fb_goalline_cutin(t, sp), None
    return fb_goalline_replay(t, sp), (T_GSTOP if t >= T_GSTOP else None)

# =============================================================== FOOTBALL: the bucket (fb_bucket)
T_KCUT1, T_KTIP, T_KCUT2, T_KTHUMB = 1.7, 1.95, 2.55, 3.4
def _coach(dd, cx, fy, wet=0.0, thumb=False, ice=False, face="calm"):
    dd.rectangle((cx - 5, fy - 10, cx - 1, fy), fill=KHAKI); dd.rectangle((cx + 1, fy - 10, cx + 5, fy), fill=KHAKI)
    dd.rectangle((cx - 6, fy - 1, cx - 1, fy), fill=BLK); dd.rectangle((cx + 1, fy - 1, cx + 6, fy), fill=BLK)
    shirt = tuple(int(lerp(c, w, wet)) for c, w in zip(NAVY, (40, 110, 200)))
    dd.rectangle((cx - 7, fy - 22, cx + 7, fy - 10), fill=shirt)
    txt(dd, (cx, fy - 16), "ONC", F(6), WHT, sh=None)
    if thumb:
        dd.rectangle((cx + 7, fy - 22, cx + 10, fy - 18), fill=shirt); dd.rectangle((cx + 9, fy - 27, cx + 11, fy - 21), fill=SKIN)
    else:
        dd.rectangle((cx + 7, fy - 21, cx + 9, fy - 13), fill=shirt)
        dd.rectangle((cx - 13, fy - 20, cx - 7, fy - 12), fill=WHT); dd.line((cx - 12, fy - 17, cx - 8, fy - 17), fill=DGRY)   # clipboard
    dd.ellipse((cx - 5, fy - 32, cx + 5, fy - 22), fill=SKIN)
    dd.rectangle((cx - 6, fy - 33, cx + 6, fy - 31), fill=BLK); dd.rectangle((cx - 7, fy - 29, cx - 5, fy - 25), fill=BLK)   # headset
    if face == "shock":
        dd.ellipse((cx - 3, fy - 29, cx - 1, fy - 27), fill=WHT); dd.ellipse((cx + 1, fy - 29, cx + 3, fy - 27), fill=WHT)
        dd.ellipse((cx - 1, fy - 26, cx + 1, fy - 23), fill=BLK)
    else:
        dd.point((cx - 2, fy - 28), fill=BLK); dd.point((cx + 2, fy - 28), fill=BLK)
        dd.arc((cx - 2, fy - 27, cx + 2, fy - 24), 0, 180, fill=BLK)
    if wet > 0:
        for k in range(5): dd.line((cx - 6 + k * 3, fy - 22, cx - 6 + k * 3, fy - 16 + (k % 3) * 2), fill=DRINK)
    if ice:
        for k, (ix, iy) in enumerate(((-4, -35), (3, -36), (-1, -38))): dd.rectangle((cx + ix, fy + iy, cx + ix + 3, fy + iy + 3), fill=ICE)

def _bucket(dd, cx, fy, tilt=0.0):
    w = 8
    if tilt < 0.5:
        dd.polygon([(cx - w, fy - 14), (cx + w, fy - 14), (cx + w - 2, fy), (cx - w + 2, fy)], fill=ORG)
        dd.rectangle((cx - w, fy - 14, cx + w, fy - 12), fill=WHT)
    else:   # tipped over (open side facing the coach)
        dd.polygon([(cx - 14, fy - w), (cx, fy - w + 2), (cx, fy + w - 2), (cx - 14, fy + w)], fill=ORG)
        dd.rectangle((cx - 16, fy - w, cx - 14, fy + w), fill=WHT)

def fb_bucket_sideline(t, sp):
    """Sideline: game's over, two ONC players tiptoe up behind the coach with the bucket."""
    img, d, X = R.side_field(50, t, sp); fr = int(t * 4) % 2
    R.fb_hud(d, sp, sp["home_score"], "0:00")
    for i in range(6): R.side_player(d, 30 + i * 40, 280, sp["acol"], 0, -1, num="")   # CPU walking off
    R.big(img, lambda dd, cx, fy: _coach(dd, cx, fy), 222, 470, 3, (34, 42))
    sneak = ease(t / (T_KCUT1 - 0.2))
    for k, x0 in enumerate((20, 52)):
        R.big(img, lambda dd, cx, fy, k=k: R.side_player(dd, cx, fy, BLU, fr ^ k, 1, num=["72", "64"][k], shadow=False), x0 + 70 * sneak, 468, 3, (40, 34))
    R.big(img, lambda dd, cx, fy: _bucket(dd, cx, fy), 72 + 70 * sneak, 412, 3, (24, 18))
    d = ImageDraw.Draw(img)
    R.hook_text(d, sp, t, until=0.9, y=60, box=True)
    if t >= 0.9:
        R.bar(d, 66, 28); txt(d, (LW // 2, 66), "SHHH..." if fr else "SHHH.. .", F(16), [YEL, WHT][fr])
        if t > 1.3: txt(d, (222, 330), "?", F(16), WHT)
    return img

def fb_bucket_tip(t, sp):
    img = Image.new("RGB", (LW, LH), BLK); u = t - T_KCUT1
    R.speed_lines(img, t, (16, 80, 120), (40, 140, 200), LW // 2, 120)
    tilt = 1.0 if t >= T_KTIP else 0.0
    R.big(img, lambda dd, cx, fy: _bucket(dd, cx, fy, tilt), 120, 170, 6, (34, 30))
    R.big(img, lambda dd, cx, fy: _coach(dd, cx, fy, face="shock" if t >= T_KTIP else "calm"), 150, 470, 5, (34, 42))
    d = ImageDraw.Draw(img)
    if t >= T_KTIP:
        v = t - T_KTIP
        for k in range(28):   # the pour + ice
            px = 70 + (k * 37) % 120 + 6 * math.sin(k + v * 9); py = 150 + ((k * 53) % 160) + v * 260
            if py < 470:
                if k % 4 == 0: d.rectangle((px, py, px + 6, py + 6), fill=ICE)
                else: d.rectangle((px, py, px + 3, py + 10), fill=DRINK)
        txt(d, (LW // 2, 70), "INCOMING!", F(24), [YEL, WHT][int(v * 10) % 2])
    R.fb_hud(d, sp, sp["home_score"], "0:00")
    return img

def fb_bucket_front(t, sp):
    img, d = Image.new("RGB", (LW, LH), G1), None; u = t - T_KCUT2
    d = ImageDraw.Draw(img); R.crowd(d, 34, 200, t, 53); d.rectangle((0, 200, LW, 222), fill=DGRN)
    txt(d, (LW // 2, 211), "ON-CARDS.COM", F(8), WHT, sh=None)
    for i in range(10):
        if i % 2: d.rectangle((0, 222 + i * 26, LW, 248 + i * 26), fill=G2)
    thumb = t >= T_KTHUMB
    R.big(img, lambda dd, cx, fy: _coach(dd, cx, fy, wet=1.0, thumb=thumb, ice=True, face="calm" if thumb else "shock"), 135, 470, 6, (34, 42))
    d = ImageDraw.Draw(img)
    for k in range(10):   # drips
        px = 95 + k * 9; py = 260 + ((k * 31 + int(u * 120)) % 200)
        d.rectangle((px, py, px + 2, py + 6), fill=DRINK)
    d.ellipse((60, 455, 210, 475), fill=(60, 150, 200))   # puddle
    R.fb_hud(d, sp, sp["home_score"], "0:00")
    if not thumb: R.bar(d, 70, 28); txt(d, (LW // 2, 70), "...", F(24), WHT)
    else:
        v = t - T_KTHUMB; R.fireworks(d, v, ((60, 120, 0.0), (210, 130, 0.3), (135, 100, 0.6)))
        R.flash_title(d, v, "ICE BATH!", "", y=70, sub=_win(sp, sp["home_score"]))
    return img

def fb_bucket(t, sp):
    if t < T_KCUT1: return fb_bucket_sideline(t, sp), None
    if t < T_KCUT2: return fb_bucket_tip(t, sp), None
    return fb_bucket_front(t, sp), (T_KTHUMB if t >= T_KTHUMB else None)

# =============================================================== sound effects + registration
def sfx(buf, v, add):
    crack = lambda t0: (add(buf, R.noise(0.15, 0.25, 0.04, 1), t0), add(buf, R.sq(88, 0.12, 0.08, 0.5), t0))
    whoosh = lambda t0: add(buf, R.sq(84, 0.3, 0.05, 0.125, slide=-0.4), t0)
    thud = lambda t0: (add(buf, R.noise(0.25, 0.3, 0.08, 1), t0), add(buf, R.tri(33, 0.35, 0.35), t0))
    if v == "bb_dive":
        crack(T_VHIT); whoosh(T_VCUT1); add(buf, R.noise(0.4, 0.15, 0.2, 2), T_VDIVE); whoosh(T_VCUT2)
        add(buf, R.sq(79, 0.1, 0.07, 0.5), T_VCATCH); add(buf, R.sq(84, 0.2, 0.07, 0.5), T_VCATCH + 0.1)
    if v == "bb_dp":
        crack(T_DHIT); add(buf, R.noise(0.05, 0.15, 0.02, 2), T_DFLIP); whoosh(T_DCUT1); thud(T_DTURN)
        whoosh(T_DCUT2); add(buf, R.sq(60, 0.25, 0.08, 0.5, slide=0.9), T_DCUT2 + 0.2)   # the stretch "boing"
        add(buf, R.noise(0.08, 0.25, 0.03, 2), T_DOUT)
    if v == "bb_nachos":
        crack(T_NHIT); add(buf, R.sq(70, 0.9, 0.05, 0.125, slide=0.9), T_NHIT + 0.05); whoosh(T_NCUT1); whoosh(T_NCUT2)
        add(buf, R.noise(0.2, 0.25, 0.06, 1), T_NCATCH); add(buf, R.sq(72, 0.15, 0.08, 0.5, slide=-0.5), T_NCATCH + 0.05)
    if v == "fb_pick6":
        add(buf, R.noise(0.06, 0.15, 0.02, 2), T_PSNAP); add(buf, R.sq(70, 0.6, 0.05, 0.125, slide=0.7), T_PTHROW)
        whoosh(T_PCUT1); add(buf, R.noise(0.08, 0.2, 0.03, 2), T_PINT); whoosh(T_PCUT2)
        for k in range(5): add(buf, R.sq(76 + (k % 2) * 5, 0.06, 0.05, 0.25), 3.3 + k * 0.1)   # high-step boops
    if v == "fb_goalline":
        add(buf, R.noise(0.06, 0.15, 0.02, 2), T_GSNAP); add(buf, R.sq(70, 0.5, 0.05, 0.125, slide=0.8), T_GLEAP)
        whoosh(T_GCUT1); thud(T_GHIT); whoosh(T_GCUT2)
    if v == "fb_bucket":
        for k in range(6): add(buf, R.sq(67 if k % 2 else 64, 0.06, 0.04, 0.25), 0.9 + k * 0.13)   # tiptoe
        whoosh(T_KCUT1); add(buf, R.noise(0.8, 0.2, 0.4, 1), T_KTIP); add(buf, R.sq(84, 0.5, 0.06, 0.5, slide=-0.8), T_KTIP)
        whoosh(T_KCUT2)

def register():
    R.GAMES.update({"bb_dive": bb_dive, "bb_dp": bb_dp, "bb_nachos": bb_nachos,
                    "fb_pick6": fb_pick6, "fb_goalline": fb_goalline, "fb_bucket": fb_bucket})
    R.PAYOFF.update({"bb_dive": T_VCATCH, "bb_dp": T_DOUT, "bb_nachos": T_NCATCH,
                     "fb_pick6": T_PTD, "fb_goalline": T_GSTOP, "fb_bucket": T_KTHUMB})
    R.DEFAULTS.update({
        "bb_dive": {"hook": ["TOP 9TH. 2 OUTS.", "UP BY 1. TYING RUN ON 2ND."], "home_score": 4, "away_score": 3},
        "bb_dp": {"hook": ["TOP 9TH. BASES LOADED.", "UP BY 1. ONE OUT."], "home_score": 5, "away_score": 4},
        "bb_nachos": {"hook": ["TOP 9TH. 2 OUTS.", "UP BY 2. ONE MORE OUT."], "home_score": 6, "away_score": 4},
        "fb_pick6": {"hook": ["TIED 21-21. 0:20 LEFT.", "THEY'RE DRIVING..."], "home_score": 21, "away_score": 21},
        "fb_goalline": {"hook": ["UP BY 4. 4TH & GOAL.", "1 YARD. 1 SECOND."], "home_score": 24, "away_score": 20},
        "fb_bucket": {"hook": ["FINAL: ONC WINS.", "SOMEBODY GRAB THE BUCKET."], "home_score": 34, "away_score": 24},
    })
