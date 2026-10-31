"""More reel styles for tools/era_reel.py (original art + original music, no licensed assets).

synthwave = neon '80s look: night-sky gradients, purple turf with a glowing pink grid, cyan/pink team colors,
            soft neon glow, VHS scanlines and color fringing, a striped-sunset "PRESS START" screen, detuned
            saw-wave synths with long echo.
arcade    = '90s arcade cabinet: punchy oversaturated color, outlined 16-bit sprites, CRT phosphor mask and
            scanlines, flames roaring up the screen on the big moment, an "INSERT COIN" attract screen,
            FM music plus a crowd roar.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

def _hsv(a):
    return np.asarray(Image.fromarray(a.astype(np.uint8)).convert("HSV")).astype(np.float32)

def _rgb(h):
    return np.asarray(Image.fromarray(np.clip(h, 0, 255).astype(np.uint8), "HSV").convert("RGB")).astype(np.float32)

# =============================================================== synthwave
def install_synthwave(R, E):
    LW, LH = R.LW, R.LH
    ys = np.arange(LH)[:, None]
    top, bot = np.array([10, 4, 34]), np.array([110, 20, 120])
    grad = (top + (bot - top) * (np.arange(LH) / LH)[:, None])[:, None, :].repeat(LW, 1)

    def finish(img):
        a = np.asarray(img.convert("RGB")).astype(np.float32)
        blk = (a.sum(2) == 0); bg = blk.copy()
        for dy, dx in ((2, 0), (-2, 0), (0, 2), (0, -2)): bg &= E._sh(blk, dy, dx)
        turf = (a[..., 0] < 10) & (a[..., 2] < 10) & (a[..., 1] > 100)
        h = _hsv(a); H, S, V = h[..., 0], h[..., 1], h[..., 2]
        deg = H * 360 / 255
        green = (deg > 70) & (deg < 170) & (S > 60)
        blue = (deg >= 170) & (deg < 260) & (S > 60)
        red = ((deg < 45) | (deg > 330)) & (S > 60)
        H = np.where(green, 272 * 255 / 360, H); V = np.where(green, V * 0.42, V)
        H = np.where(blue, 188 * 255 / 360, H)
        H = np.where(red, 322 * 255 / 360, H)
        S = np.clip(S * 1.25, 0, 255)
        out = _rgb(np.stack([H, S, V], 2))
        white = (a.min(2) > 200)
        out[white] = [210, 250, 255]
        # glowing pink grid on the turf
        grid = turf & (((ys % 16) == 0) | ((np.arange(LW)[None] % 18) == 0))
        out[grid] = [255, 60, 190]
        out[bg] = grad[bg]
        lo = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
        big = lo.resize((R.W, R.H), Image.NEAREST)
        glow = lo.filter(ImageFilter.GaussianBlur(2)).resize((R.W, R.H), Image.BILINEAR)
        b = np.asarray(big).astype(np.float32); g = np.asarray(glow).astype(np.float32)
        b = 255 - (255 - b) * (255 - g * 0.55) / 255          # screen-blend glow
        b[:, 3:, 0] = b[:, :-3, 0]                             # VHS color fringe
        b[3::4] *= 0.72
        return Image.fromarray(np.clip(b, 0, 255).astype(np.uint8))

    def title(t, sp):
        sport = "BASEBALL" if sp["variant"].startswith("bb") else "FOOTBALL"
        k = np.clip(np.arange(LH) / 290, 0, 1)[:, None]
        tp, bt = np.array([8, 2, 30]), np.array([255, 70, 120])
        a = (tp + (bt - tp) * k ** 1.4)[:, None, :].repeat(LW, 1).astype(np.float32)
        img = Image.fromarray(a.astype(np.uint8)); d = ImageDraw.Draw(img)
        cx, cy, r = LW // 2, 290, 78                            # striped sunset
        d.pieslice((cx - r, cy - r, cx + r, cy + r), 180, 360, fill=(255, 200, 60))
        for i, yy in enumerate(range(cy - 50, cy, 9)): d.rectangle((0, yy, LW, yy + 2 + i), fill=tuple(int(v) for v in a[yy, 0]))
        d.rectangle((0, 290, LW, LH), fill=(14, 2, 34))
        for i in range(16):                                     # scrolling neon grid
            z = (i + (t * 3) % 1) / 16; y = 290 + (LH - 290) * z ** 2
            d.line((0, y, LW, y), fill=(255, 60, 190))
        for x in range(-400, LW + 400, 36): d.line((cx + (x - cx) * 0.08, 290, x, LH), fill=(255, 60, 190))
        rgb, al = R.pixel_logo(150); drop = int(-180 * (1 - R.ease(t / 0.35)))
        img.paste(rgb, ((LW - rgb.width) // 2, 30 + drop), al); d = ImageDraw.Draw(img)
        if t > 0.3:
            R.txt(d, (LW // 2 + 2, 222), sport, R.F(24), (255, 60, 190), sh=None)
            R.txt(d, (LW // 2, 220), sport, R.F(24), (120, 240, 255), sh=(20, 0, 60))
        pressed = t >= 1.05
        if 0.55 < t and (pressed and int(t * 16) % 2 == 0 or not pressed and int(t * 4) % 2 == 0):
            R.txt(d, (LW // 2, 360), "PRESS START", R.F(16), (255, 255, 255), sh=(255, 40, 170))
        if pressed: R.txt(d, (LW // 2, 396), "> 1 PLAYER", R.F(8), (120, 240, 255), sh=(20, 0, 60))
        if t > 0.55: R.txt(d, (LW // 2, 458), "© 2026 OUTTA NOWHERE CARDS", R.F(6), (210, 250, 255), sh=(20, 0, 60))
        if t > R.T_START - 0.12: d.rectangle((0, 0, LW, LH), fill=(0, 0, 0))
        return img

    SR = R.SR
    def saw(n, dur, vol, duty=0.5, slide=0.0):
        t = np.arange(int(dur * SR)) / SR; out = 0
        for det in (-0.006, 0.006):
            f = R.hz(n) * (1 + det) * (1 + slide * t / max(dur, 1e-6)); ph = np.cumsum(f) / SR % 1.0
            out = out + (2 * ph - 1)
        out = np.convolve(out, np.ones(6) / 6, mode="same")
        env = np.minimum(1, t / 0.01) * (0.7 + 0.3 * np.exp(-t * 4)) * np.minimum(1, (dur - t) / 0.03).clip(0)
        return out * env * vol * 0.6
    def sub(n, dur, vol):
        t = np.arange(int(dur * SR)) / SR
        return np.sin(2 * np.pi * R.hz(n) * t) * np.minimum(1, t / 0.005) * np.minimum(1, (dur - t) / 0.02).clip(0) * vol * 1.3

    R.scanlines = finish; R.scene_start = title; R.scene_pack = E.scene_pack16
    R.sq = saw; R.tri = sub; R.noise = E.soft_noise
    E.sprites16.install(R); R.pixel_logo = E.pixel_logo16
    E.ECHO["synthwave"] = [(0.25, 0.35), (0.5, 0.2), (0.75, 0.1)]

# =============================================================== arcade
def install_arcade(R, E):
    LW, LH = R.LW, R.LH
    mask = np.ones((R.H, R.W, 3), np.float32) * 0.82                 # CRT phosphor stripes
    for c in range(3): mask[:, c::3, c] = 1.0
    mask[3::4] *= 0.75
    yy, xx = np.mgrid[0:R.H, 0:R.W]
    vig = 1 - 0.35 * (((xx - R.W / 2) / (R.W / 2)) ** 2 + ((yy - R.H / 2) / (R.H / 2)) ** 2) ** 1.5
    mask *= np.clip(vig, 0.5, 1)[..., None]

    def finish(img):
        a = np.asarray(img.convert("RGB")).astype(np.float32)
        h = _hsv(a); h[..., 1] = np.clip(h[..., 1] * 1.4, 0, 255); h[..., 2] = np.clip((h[..., 2] - 128) * 1.15 + 140, 0, 255)
        a = _rgb(h)
        b = np.asarray(Image.fromarray(a.astype(np.uint8)).resize((R.W, R.H), Image.NEAREST)).astype(np.float32) * mask * 1.12
        return Image.fromarray(np.clip(b, 0, 255).astype(np.uint8))

    _flash = R.flash_title
    def flash_title(d, u, l1, l2, y=262, sub=None):
        rnd = random.Random(int(u * 14))                            # flames roar up from the bottom on the big moment
        hgt = 110 * R.ease(min(1, u / 0.4))
        for x in range(-6, LW + 6, 9):
            fh = hgt * (0.6 + 0.4 * rnd.random())
            for k, col in enumerate([(200, 20, 0), (255, 110, 0), (255, 220, 40)]):
                h2 = fh * (1 - k * 0.32)
                d.polygon([(x - 7 + k * 2, LH), (x + rnd.randint(-3, 3), LH - h2), (x + 7 - k * 2, LH)], fill=col)
        _flash(d, u, l1, l2, y, sub)

    def title(t, sp):
        sport = "BASEBALL" if sp["variant"].startswith("bb") else "FOOTBALL"
        img = Image.new("RGB", (LW, LH), (12, 8, 30)); d = ImageDraw.Draw(img)
        off = int(t * 24) % 24
        for y in range(-24, LH, 24):                                # scrolling checkerboard
            for x in range(0, LW, 24):
                if ((x + y) // 24) % 2: d.rectangle((x, y + off, x + 23, y + off + 23), fill=(30, 20, 80))
        d.rectangle((0, 20, LW, 196), fill=(10, 6, 24)); d.rectangle((0, 20, LW, 23), fill=(255, 200, 40)); d.rectangle((0, 193, LW, 196), fill=(255, 200, 40))
        rgb, al = R.pixel_logo(150); img.paste(rgb, ((LW - rgb.width) // 2, 30 + int(-160 * (1 - R.ease(t / 0.3)))), al); d = ImageDraw.Draw(img)
        if t > 0.3:
            R.txt(d, (LW // 2 + 3, 243), sport, R.F(32) if R.F(32).getlength(sport) < LW - 40 else R.F(24), (200, 20, 0), sh=None)
            R.txt(d, (LW // 2, 240), sport, R.F(32) if R.F(32).getlength(sport) < LW - 40 else R.F(24), (255, 220, 40), sh=(60, 0, 0))
        credit = t >= 1.05
        if not credit and int(t * 4) % 2 == 0: R.txt(d, (LW // 2, 330), "INSERT COIN", R.F(16), (255, 255, 255), sh=(200, 20, 0))
        if credit:
            if int(t * 16) % 2 == 0: R.txt(d, (LW // 2, 330), "PRESS START", R.F(16), (255, 220, 40), sh=(200, 20, 0))
            R.txt(d, (LW // 2, 370), "1 PLAYER GAME", R.F(8), (255, 255, 255))
        R.txt(d, (LW - 10, 462), f"CREDIT {1 if credit else 0}", R.F(8), (255, 255, 255), "rm")
        R.txt(d, (10, 462), "© 2026 ONC", R.F(6), (200, 200, 220), "lm")
        if t > R.T_START - 0.12: d.rectangle((0, 0, LW, LH), fill=(0, 0, 0))
        return img

    R.scanlines = finish; R.scene_start = title; R.flash_title = flash_title; R.scene_pack = E.scene_pack16
    R.sq = E.fm_lead; R.tri = E.fm_bass; R.noise = E.soft_noise
    E.sprites16.install(R); R.pixel_logo = E.pixel_logo16
    E.ECHO["arcade"] = [(0.09, 0.2)]

    def crowd(x, sp, payoff, SR=R.SR):                              # crowd roar swelling on the big moment
        n = int(2.4 * SR); rng = np.random.default_rng(3)
        s = np.convolve(rng.standard_normal(n), np.ones(40) / 40, mode="same")
        env = np.minimum(1, np.arange(n) / (0.3 * SR)) * np.exp(-np.arange(n) / (1.6 * SR))
        i = int(payoff * SR)   # game audio only; the title jingle is prepended later
        j = min(len(x), i + n)
        if 0 <= i < len(x): x[i:j] += (s * env)[: j - i] / np.abs(s).max() * 0.5
        return x
    E.POST["arcade"] = crowd

# =============================================================== holo prizm
def _rainbow(n, phase):
    h = (np.arange(n) / n + phase) % 1.0
    return np.asarray(Image.fromarray((np.stack([h * 255, np.full(n, 200), np.full(n, 255)], 1)[None]).astype(np.uint8), "HSV").convert("RGB"))[0].astype(np.float32)

def install_holo(R, E):
    """Holo prizm: rainbow refractor light sweeping across the action, shimmering diagonal prism stripes on the field,
    deep black-blue backgrounds, crisp 16-bit sprites, a prism-beam title screen, bell-like FM music with shimmer."""
    LW, LH = R.LW, R.LH
    yy, xx = np.mgrid[0:LH, 0:LW]
    diag = (xx + yy * 0.6)
    stripes = ((diag // 3) % 2).astype(np.float32)
    clock = {"f": 0}

    def finish(img):
        clock["f"] += 1; t = clock["f"] / R.FPS
        a = np.asarray(img.convert("RGB")).astype(np.float32)
        blk = (a.sum(2) == 0); bg = blk.copy()
        for dy, dx in ((2, 0), (-2, 0), (0, 2), (0, -2)): bg &= E._sh(blk, dy, dx)
        turf = (a[..., 0] < 10) & (a[..., 2] < 10) & (a[..., 1] > 100)
        rb = _rainbow(512, t * 0.25)[((diag * 1.2 + t * 160) % 512).astype(int)]
        a[turf] = a[turf] * 0.55 + rb[turf] * 0.25 + stripes[turf][:, None] * 18      # refractor field
        band = np.exp(-(((diag - (t * 260) % (LW + LH)) / 26) ** 2))                     # light sweep
        a = a * (1 - band[..., None] * 0.45) + rb * band[..., None] * 0.45 + band[..., None] * 40
        g = (np.arange(LH) / LH)[:, None, None]
        a[bg] = (np.array([4, 6, 18]) + np.array([20, 10, 50]) * g + 0 * a)[bg]
        sp = (np.random.default_rng(clock["f"] // 3).random((LH, LW)) > 0.9985) & ~turf       # sparkles
        a[sp] = 255
        lo = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
        return lo.resize((R.W, R.H), Image.NEAREST)

    def title(t, sp):
        sport = "BASEBALL" if sp["variant"].startswith("bb") else "FOOTBALL"
        img = Image.new("RGB", (LW, LH), (4, 6, 18)); d = ImageDraw.Draw(img)
        cx, cy = LW // 2, 110; rb = _rainbow(24, t * 0.3)
        for i in range(24):                                          # prism light beams
            a0 = i * 0.2618 + t * 0.4
            d.polygon([(cx, cy), (cx + 500 * math.cos(a0), cy + 500 * math.sin(a0)), (cx + 500 * math.cos(a0 + 0.1), cy + 500 * math.sin(a0 + 0.1))],
                      fill=tuple(int(v * 0.35) for v in rb[i]))
        rgb, al = R.pixel_logo(150); img.paste(rgb, ((LW - rgb.width) // 2, 34 + int(-180 * (1 - R.ease(t / 0.35)))), al); d = ImageDraw.Draw(img)
        if t > 0.3:
            rb2 = _rainbow(len(sport), t * 0.5); w = R.F(24).getlength(sport); x = LW / 2 - w / 2
            for k, ch in enumerate(sport):
                R.txt(d, (x + R.F(24).getlength(sport[:k]) + R.F(24).getlength(ch) / 2, 240), ch, R.F(24), tuple(int(v) for v in rb2[k]), sh=(10, 10, 30))
            R.txt(d, (LW // 2, 274), "PRIZM EDITION", R.F(8), (230, 230, 255), sh=(10, 10, 30))
        pressed = t >= 1.05
        if 0.55 < t and (pressed and int(t * 16) % 2 == 0 or not pressed and int(t * 4) % 2 == 0):
            R.txt(d, (LW // 2, 350), "PRESS START", R.F(16), (255, 255, 255), sh=(80, 40, 160))
        if t > 0.55: R.txt(d, (LW // 2, 458), "© 2026 OUTTA NOWHERE CARDS", R.F(6), (200, 200, 230), sh=None)
        if t > R.T_START - 0.12: d.rectangle((0, 0, LW, LH), fill=(0, 0, 0))
        return img

    SR = R.SR
    def bell(n, dur, vol, duty=0.5, slide=0.0):
        t = np.arange(int(dur * SR)) / SR; f = R.hz(n) * (1 + slide * t / max(dur, 1e-6)); ph = 2 * np.pi * np.cumsum(f) / SR
        s = np.sin(ph + (1.2 + 2.5 * np.exp(-t * 5)) * np.sin(ph * 3.5)) * 0.6 + np.sin(ph) * 0.4
        return s * np.minimum(1, t / 0.003) * np.exp(-t * 2.2) * np.minimum(1, (dur - t) / 0.02).clip(0) * vol * 1.3
    R.scanlines = finish; R.scene_start = title; R.scene_pack = E.scene_pack16
    R.sq = bell; R.tri = E.fm_bass; R.noise = E.soft_noise
    E.sprites16.install(R); R.pixel_logo = E.pixel_logo16
    E.ECHO["holo"] = [(0.18, 0.3), (0.36, 0.18), (0.54, 0.08)]

# =============================================================== anime
def install_anime(R, E):
    """Anime power-up: cel-shaded flat colors with bold ink outlines, manga screentone dots, radial speed lines and an
    impact frame on the big moment, a manga-panel title screen, fast bright FM music."""
    LW, LH = R.LW, R.LH
    yy, xx = np.mgrid[0:LH, 0:LW]
    tone = (((xx % 4) == 0) & ((yy % 4) == 0))
    clock = {"f": 0}

    def finish(img):
        clock["f"] += 1
        a = np.asarray(img.convert("RGB")).astype(np.float32)
        blk = (a.sum(2) == 0); bg = blk.copy()
        for dy, dx in ((2, 0), (-2, 0), (0, 2), (0, -2)): bg &= E._sh(blk, dy, dx)
        turf = (a[..., 0] < 10) & (a[..., 2] < 10) & (a[..., 1] > 100)
        h = _hsv(a); h[..., 1] = np.clip(h[..., 1] * 1.3, 0, 255)
        h[..., 2] = np.where(h[..., 2] > 150, 245, np.where(h[..., 2] > 70, 170, 70))      # cel-shade: 3 flat tones
        a = _rgb(h)
        a[turf] = np.where(tone[turf][:, None], a[turf] * 0.6, a[turf] * 1.05)             # screentone on the turf
        edge = np.zeros(blk.shape, bool)                                                    # ink lines around players on the field
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            edge |= ~turf & E._sh(turf, dy, dx)
        a[edge & ~bg] = [16, 12, 20]
        bg[:36] = False                                                                     # keep the scoreboard bar dark
        a[bg] = np.where(tone[bg][:, None], [235, 225, 210], [250, 246, 236])              # paper
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((R.W, R.H), Image.NEAREST)

    _flash = R.flash_title
    def flash_title(d, u, l1, l2, y=262, sub=None):
        cx, cy = LW // 2, y
        for i in range(40):                                                                 # radial speed lines
            a0 = i * 0.157 + (i % 3) * 0.03
            r0 = 70 + (i * 37 % 40)
            d.polygon([(cx + r0 * math.cos(a0), cy + r0 * math.sin(a0)), (cx + 420 * math.cos(a0 - 0.02), cy + 420 * math.sin(a0 - 0.02)),
                       (cx + 420 * math.cos(a0 + 0.02), cy + 420 * math.sin(a0 + 0.02))], fill=(16, 12, 20))
        if u < 0.08: d.rectangle((0, 0, LW, LH), fill=(250, 246, 236))                     # impact frame
        _flash(d, u, l1, l2, y, sub)

    def title(t, sp):
        sport = "BASEBALL" if sp["variant"].startswith("bb") else "FOOTBALL"
        img = Image.new("RGB", (LW, LH), (250, 246, 236)); d = ImageDraw.Draw(img)
        cx, cy = LW // 2, 120
        for i in range(48):
            a0 = i * 0.1309 + t * 0.15
            d.polygon([(cx + 90 * math.cos(a0), cy + 90 * math.sin(a0)), (cx + 500 * math.cos(a0 - 0.015), cy + 500 * math.sin(a0 - 0.015)),
                       (cx + 500 * math.cos(a0 + 0.015), cy + 500 * math.sin(a0 + 0.015))], fill=(16, 12, 20))
        rgb, al = R.pixel_logo(150); img.paste(rgb, ((LW - rgb.width) // 2, 40 + int(-180 * (1 - R.ease(t / 0.3)))), al); d = ImageDraw.Draw(img)
        d.rectangle((0, 206, LW, 290), fill=(250, 246, 236)); d.line((0, 206, LW, 206), fill=(16, 12, 20), width=3); d.line((0, 290, LW, 290), fill=(16, 12, 20), width=3)
        if t > 0.3:
            s = R.F(32) if R.F(32).getlength(sport) < LW - 30 else R.F(24)
            R.txt(d, (LW // 2 + 3, 251), sport, s, (220, 30, 50), sh=None); R.txt(d, (LW // 2, 248), sport, s, (16, 12, 20), sh=None)
        pressed = t >= 1.05
        if 0.55 < t and (pressed and int(t * 16) % 2 == 0 or not pressed and int(t * 4) % 2 == 0):
            R.txt(d, (LW // 2, 350), "PRESS START", R.F(16), (220, 30, 50), sh=(16, 12, 20))
        if t > 0.55: R.txt(d, (LW // 2, 458), "© 2026 OUTTA NOWHERE CARDS", R.F(6), (16, 12, 20), sh=None)
        if t > R.T_START - 0.12: d.rectangle((0, 0, LW, LH), fill=(0, 0, 0))
        return img

    R.scanlines = finish; R.scene_start = title; R.flash_title = flash_title; R.scene_pack = E.scene_pack16
    R.sq = E.fm_lead; R.tri = E.fm_bass; R.noise = E.soft_noise
    E.sprites16.install(R); R.pixel_logo = E.pixel_logo16
    E.ECHO["anime"] = [(0.11, 0.22)]

# =============================================================== N64-style (late-'90s early 3D)
def _lt(c, k=0.35): return tuple(int(v + (255 - v) * k) for v in c)
def _dk(c, k=0.62): return tuple(int(v * k) for v in c)

def install_n64(R, E):
    """Early-3D look: faceted low-poly players (lit/dark facets, no outlines), smeared bilinear texture filtering,
    distance fog rolling over the far side of every shot, chunky extruded title lettering, muffled FM music with reverb."""
    LW, LH = R.LW, R.LH
    E.sprites16.install(R)
    PANT = (226, 222, 210); CLEAT = (40, 40, 46); SKIN = (232, 172, 120)

    def player(d, x, y, col, frame, facing="up", ball=False, num="7", pants=None, shadow=True):
        x, y = int(x), int(y)
        if shadow: d.ellipse((x - 9, y - 3, x + 9, y + 3), fill=(20, 70, 30))
        l = -2 if frame else 0; r = 0 if frame else -2
        for x0, x1, o in ((x - 5, x - 1, l), (x + 1, x + 5, r)):
            d.polygon([(x0, y - 9 + o), (x1, y - 9 + o), (x1 - 1, y - 3 + o), (x0 + 1, y - 3 + o)], fill=PANT)
            d.polygon([(x0 + 1, y - 3 + o), (x1 - 1, y - 3 + o), (x1, y + o), (x0, y + o)], fill=CLEAT)
        d.polygon([(x - 6, y - 13), (x + 6, y - 13), (x + 5, y - 8), (x - 5, y - 8)], fill=PANT)
        d.polygon([(x - 9, y - 22), (x, y - 23), (x, y - 12), (x - 6, y - 12)], fill=_lt(col))
        d.polygon([(x, y - 23), (x + 9, y - 22), (x + 6, y - 12), (x, y - 12)], fill=_dk(col))
        a1 = 1 if frame else -1
        d.polygon([(x - 10, y - 20), (x - 8, y - 20), (x - 8, y - 13 + a1), (x - 10, y - 13 + a1)], fill=_lt(col))
        d.polygon([(x + 8, y - 20), (x + 10, y - 20), (x + 10, y - 13 - a1), (x + 8, y - 13 - a1)], fill=_dk(col))
        if num: R.digits(d, x - 1 if len(num) == 1 else x - 3, y - 20, num, (250, 250, 250))
        hx, hy = x, y - 26
        oct_ = [(hx - 3, hy - 5), (hx + 3, hy - 5), (hx + 5, hy - 2), (hx + 5, hy + 2), (hx + 3, hy + 4), (hx - 3, hy + 4), (hx - 5, hy + 2), (hx - 5, hy - 2)]
        d.polygon(oct_, fill=col); d.polygon([oct_[0], (hx, hy - 5), (hx, hy + 4), oct_[5], oct_[6], oct_[7]], fill=_lt(col, 0.3))
        if facing == "down": d.polygon([(hx - 3, hy - 1), (hx + 3, hy - 1), (hx + 2, hy + 4), (hx - 2, hy + 4)], fill=SKIN); d.line((hx - 3, hy + 1, hx + 3, hy + 1), fill=(170, 170, 180))
        if ball: d.polygon([(x + 6, y - 15), (x + 9, y - 18), (x + 12, y - 15), (x + 9, y - 12)], fill=(140, 72, 20))

    def side_player(d, x, y, col, frame, f=1, ball=False, num="", pants=None, mask=None, shadow=True, arm_back=False):
        x, y = int(x), int(y)
        if shadow: d.ellipse((x - 9, y - 3, x + 9, y + 3), fill=(20, 70, 30))
        legs = ((-7, -3), (2, 6)) if frame else ((-2, 2), (0, 3))
        for a0, a1 in legs:
            d.polygon([(x + a0 * f, y - 9), (x + a1 * f, y - 9), (x + a1 * f, y - 2), (x + a0 * f, y - 2)], fill=PANT)
            d.polygon([(x + a0 * f, y - 2), (x + (a1 + 2) * f, y - 2), (x + (a1 + 2) * f, y), (x + a0 * f, y)], fill=CLEAT)
        d.polygon([(x - 5, y - 13), (x + 5, y - 13), (x + 5, y - 8), (x - 5, y - 8)], fill=PANT)
        d.polygon([(x - 6, y - 22), (x + 6, y - 22), (x + 5, y - 12), (x - 5, y - 12)], fill=col)
        d.polygon([(x - 6 * f, y - 22), (x, y - 22), (x, y - 12), (x - 5 * f, y - 12)], fill=_dk(col))
        if num: R.digits(d, x - 3, y - 20, num, (250, 250, 250))
        if arm_back: d.polygon([(x - 4 * f, y - 19), (x - 14 * f, y - 19), (x - 14 * f, y - 15), (x - 4 * f, y - 15)], fill=_lt(col))
        else: d.polygon([(x + 2 * f, y - 18), (x + 8 * f, y - 16), (x + 7 * f, y - 13), (x + 2 * f, y - 14)], fill=_lt(col))
        if ball: d.polygon([(x + 5 * f, y - 16), (x + 8 * f, y - 19), (x + 11 * f, y - 16), (x + 8 * f, y - 13)], fill=(140, 72, 20))
        hx, hy = x, y - 26
        d.polygon([(hx - 5, hy - 2), (hx - 3, hy - 5), (hx + 3, hy - 5), (hx + 5, hy - 2), (hx + 5, hy + 3), (hx - 5, hy + 3)], fill=col)
        d.polygon([(hx - 5 * f, hy - 2), (hx - 3 * f, hy - 5), (hx, hy - 5), (hx, hy + 3), (hx - 5 * f, hy + 3)], fill=_lt(col, 0.3))
        d.polygon([(hx + 3 * f, hy - 1), (hx + 7 * f, hy - 1), (hx + 7 * f, hy + 3), (hx + 3 * f, hy + 3)], fill=(170, 170, 180))

    R.player = player; R.side_player = side_player
    _d = None

    fogc = np.array([178, 192, 214], np.float32)
    def finish(img):
        raw = img.info.get("raw"); a = E.light16(img, depth=False)
        y = np.arange(R.LH)[:, None, None]
        fog = np.clip((250 - y) / 210, 0, 1) ** 1.3 * (0 if raw else 0.62)
        fog[:36] = 0
        a = a * (1 - fog) + fogc * fog
        m = a.mean(2, keepdims=True); a = m + (a - m) * 0.88
        lo = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
        return lo.resize((LW * 2, LH * 2), Image.BILINEAR).resize((R.W, R.H), Image.BILINEAR)

    def title(t, sp):
        sport = "BASEBALL" if sp["variant"].startswith("bb") else "FOOTBALL"
        img = Image.new("RGB", (LW, LH), (120, 152, 200)); d = ImageDraw.Draw(img)
        d.polygon([(0, 150), (LW, 130), (LW, 250), (0, 270)], fill=(84, 70, 120)); d.polygon([(0, 150), (LW, 130), (LW, 170), (0, 190)], fill=(104, 88, 146))
        d.polygon([(0, 250), (LW, 232), (LW, 262), (0, 282)], fill=(130, 40, 56))
        d.polygon([(0, 282), (LW, 262), (LW, LH), (0, LH)], fill=(52, 140, 60))
        for k in range(6): d.polygon([(40 + k * 40, 268 - k * 3), (46 + k * 40, 268 - k * 3), (20 + k * 50, LH), (10 + k * 50, LH)], fill=(220, 226, 210))
        a = np.asarray(img).astype(np.float32); y = np.arange(LH)[:, None, None]
        fog = np.clip((300 - y) / 260, 0, 1) * 0.6; a = a * (1 - fog) + np.array([200, 210, 228]) * fog
        img = Image.fromarray(a.astype(np.uint8))
        rgb, al = R.pixel_logo(150); img.paste(rgb, ((LW - rgb.width) // 2, 24 + int(-180 * (1 - R.ease(t / 0.35)))), al); d = ImageDraw.Draw(img)
        if t > 0.3:
            s = R.F(32) if R.F(32).getlength(sport) < LW - 30 else R.F(24)
            for k in range(6, 0, -1): R.txt(d, (LW // 2 + k, 236 + k), sport, s, (90 - k * 8, 10, 20), sh=None)
            R.txt(d, (LW // 2, 236), sport, s, (255, 214, 60), sh=None)
        pressed = t >= 1.05
        if 0.55 < t and (pressed and int(t * 16) % 2 == 0 or not pressed and int(t * 4) % 2 == 0):
            for k in range(3, 0, -1): R.txt(d, (LW // 2 + k, 350 + k), "PRESS START", R.F(16), (40, 20, 80), sh=None)
            R.txt(d, (LW // 2, 350), "PRESS START", R.F(16), (255, 255, 255), sh=None)
        if t > 0.55: R.txt(d, (LW // 2, 460), "© 2026 OUTTA NOWHERE CARDS", R.F(6), (255, 255, 255), sh=(20, 20, 40))
        if t > R.T_START - 0.12: d.rectangle((0, 0, LW, LH), fill=(0, 0, 0))
        return img

    def muffled(n, dur, vol, duty=0.5, slide=0.0):
        s = E.fm_lead(n, dur, vol, duty, slide); return np.convolve(s, np.ones(8) / 8, mode="same") * 1.2
    R.scanlines = finish; R.scene_start = title; R.scene_pack = E.scene_pack16
    R.sq = muffled; R.tri = E.fm_bass; R.noise = E.soft_noise; R.pixel_logo = E.pixel_logo16
    E.ECHO["n64"] = [(0.07, 0.3), (0.15, 0.22), (0.24, 0.14), (0.34, 0.08)]

# =============================================================== GameCube-style (early-2000s glossy 3D)
def install_gamecube(R, E):
    """Glossy early-2000s 3D look: smooth anti-aliased edges, bold cel outlines, soft bloom on everything bright,
    warm vibrant grade with a vignette, lens-flare stadium lights on a polished title screen, clean bright music."""
    LW, LH = R.LW, R.LH
    E.sprites16.install(R)
    yy, xx = np.mgrid[0:R.H, 0:R.W]
    vig = np.clip(1 - 0.28 * (((xx - R.W / 2) / (R.W / 2)) ** 2 + ((yy - R.H / 2) / (R.H / 2)) ** 2), 0.6, 1)[..., None]

    def finish(img):
        a = E.light16(img, depth=False)
        h = _hsv(a); h[..., 1] = np.clip(h[..., 1] * 1.12, 0, 255); a = _rgb(h)
        a[..., 0] *= 1.04; a[..., 2] *= 0.97
        lo = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
        big = lo.resize((LW * 2, LH * 2), Image.NEAREST).resize((R.W, R.H), Image.BICUBIC)
        b = np.asarray(big).astype(np.float32)
        bright = Image.fromarray(np.clip((b - 170) * 2.2, 0, 255).astype(np.uint8)).resize((R.W // 8, R.H // 8), Image.BILINEAR)
        bright = bright.filter(ImageFilter.GaussianBlur(3)).resize((R.W, R.H), Image.BILINEAR)
        g = np.asarray(bright).astype(np.float32)
        b = 255 - (255 - b) * (255 - g * 0.6) / 255
        return Image.fromarray(np.clip(b * vig, 0, 255).astype(np.uint8))

    def title(t, sp):
        sport = "BASEBALL" if sp["variant"].startswith("bb") else "FOOTBALL"
        k = (np.arange(LH) / LH)[:, None]
        a = (np.array([8, 8, 40]) + np.array([60, 30, 120]) * k)[:, None, :].repeat(LW, 1).astype(np.float32)
        for lx, ly in ((50, 40), (220, 40)):                                     # stadium light glows
            r2 = ((np.arange(LW)[None] - lx) ** 2 + (np.arange(LH)[:, None] - ly) ** 2)
            a += (np.exp(-r2 / 1800) * 230)[..., None] * np.array([1, 0.95, 0.8])
        img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(img)
        d.polygon([(0, 330), (LW, 330), (LW, LH), (0, LH)], fill=(24, 90, 50))
        rgb, al = R.pixel_logo(150); lx, ly = (LW - rgb.width) // 2, 40 + int(-180 * (1 - R.ease(t / 0.35)))
        img.paste(rgb, (lx, ly), al)
        ref = rgb.transpose(Image.FLIP_TOP_BOTTOM); ra = al.transpose(Image.FLIP_TOP_BOTTOM).point(lambda v: int(v * 0.12))
        img.paste(ref, (lx, 332), ra); d = ImageDraw.Draw(img)
        if t > 0.3:
            s = R.F(32) if R.F(32).getlength(sport) < LW - 30 else R.F(24)
            R.txt(d, (LW // 2, 244), sport, s, (255, 236, 150), sh=(26, 16, 60))
            R.txt(d, (LW // 2, 241), sport, s, (255, 250, 220), sh=None)
        for i in range(6):                                                       # sparkles
            sx = (37 * i + int(t * 40)) % LW; sy = 200 + (i * 53) % 110
            d.line((sx - 4, sy, sx + 4, sy), fill=(255, 255, 255)); d.line((sx, sy - 4, sx, sy + 4), fill=(255, 255, 255))
        pressed = t >= 1.05
        if 0.55 < t and (pressed and int(t * 16) % 2 == 0 or not pressed and int(t * 4) % 2 == 0):
            R.txt(d, (LW // 2, 300), "PRESS START", R.F(16), (255, 255, 255), sh=(60, 30, 140))
        if t > 0.55: R.txt(d, (LW // 2, 462), "© 2026 OUTTA NOWHERE CARDS", R.F(6), (220, 230, 255), sh=None)
        if t > R.T_START - 0.12: d.rectangle((0, 0, LW, LH), fill=(0, 0, 0))
        return img

    SR = R.SR
    def clean(n, dur, vol, duty=0.5, slide=0.0):
        t = np.arange(int(dur * SR)) / SR; f = R.hz(n) * (1 + slide * t / max(dur, 1e-6)); ph = 2 * np.pi * np.cumsum(f) / SR
        s = np.sin(ph + (0.5 + 1.2 * np.exp(-t * 8)) * np.sin(ph * 2)) * 0.7 + np.sin(ph * 2) * 0.15
        return s * np.minimum(1, t / 0.008) * (0.7 + 0.3 * np.exp(-t * 3)) * np.minimum(1, (dur - t) / 0.03).clip(0) * vol * 1.2
    R.scanlines = finish; R.scene_start = title; R.scene_pack = E.scene_pack16
    R.sq = clean; R.tri = E.fm_bass; R.noise = E.soft_noise; R.pixel_logo = E.pixel_logo16
    E.ECHO["gamecube"] = [(0.12, 0.25), (0.26, 0.15), (0.42, 0.08)]
