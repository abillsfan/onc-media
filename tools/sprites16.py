"""16-bit player sprites for the ONC reel engine (original art).

Same footprint as the 8-bit sprites (so every play's choreography still lines up), redrawn the way 16-bit sports
games drew players: dark outline, shoulder pads, glossy helmet with a highlight and center stripe, facemask cage,
two-tone jersey with sleeve stripes, numbers with a drop shadow, pants with a team side stripe, team socks, cleats.
install(R) swaps them into retro_reel, so every play (and every camera angle) picks them up.
"""
OL = (20, 16, 32)
WHT = (248, 248, 240); PANT = (232, 228, 214); PANT_D = (180, 176, 164); CLEAT = (24, 24, 28)
SKIN = (236, 176, 120); SKIN_D = (196, 132, 84); MASK = (200, 200, 210)

def lt(c, k=0.45): return tuple(int(v + (255 - v) * k) for v in c)
def dk(c, k=0.6): return tuple(int(v * k) for v in c)

class _Off:
    """Draw proxy that shifts everything by (dx, dy) and paints it in the outline color."""
    def __init__(self, d, dx, dy): self.d, self.dx, self.dy = d, dx, dy
    def _s(self, xy):
        if xy and isinstance(xy[0], (tuple, list)): return [(p[0] + self.dx, p[1] + self.dy) for p in xy]
        return [v + (self.dx if i % 2 == 0 else self.dy) for i, v in enumerate(xy)]
    def rectangle(self, xy, fill=None, outline=None, width=1): self.d.rectangle(self._s(xy), fill=OL)
    def ellipse(self, xy, fill=None, outline=None, width=1): self.d.ellipse(self._s(xy), fill=OL)
    def line(self, xy, fill=None, width=1): self.d.line(self._s(xy), fill=OL, width=width)
    def point(self, xy, fill=None): self.d.point(self._s(xy), fill=OL)
    def polygon(self, xy, fill=None, outline=None): self.d.polygon(self._s(xy), fill=OL)
    def arc(self, *a, **k): pass
    def text(self, *a, **k): pass

def outlined(fn):
    def wrapped(d, *a, **k):
        k2 = dict(k); k2["shadow"] = False
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            try: fn(_Off(d, dx, dy), *a, **k2)
            except TypeError: fn(_Off(d, dx, dy), *a, **k)
        fn(d, *a, **k)
    return wrapped

def install(R):
    digits = R.digits; _r = R._r

    def num_on(d, x, y, num):
        if not num: return
        nx = x - 1 if len(num) == 1 else x - 3
        digits(d, nx + 1, y + 1, num, OL); digits(d, nx, y, num, WHT)

    def player(d, x, y, col, frame, facing="up", ball=False, num="7", pants=None, shadow=True):
        """Overhead / broadcast-camera player (back view 'up', front view 'down'). (x, y) = feet."""
        x, y = int(x), int(y)
        if shadow: d.ellipse((x - 8, y - 2, x + 8, y + 2), fill=(0, 92, 24))
        l = -2 if frame else 0; r = 0 if frame else -2
        for sx, o in ((-1, l), (1, r)):   # legs: pants, team socks, cleats
            x0, x1 = (x - 4, x - 1) if sx < 0 else (x + 1, x + 4)
            d.rectangle((x0, y - 8 + o, x1, y - 5 + o), fill=PANT)
            d.rectangle((x0, y - 4 + o, x1, y - 2 + o), fill=col); d.line((x0, y - 3 + o, x1, y - 3 + o), fill=WHT)
            d.rectangle((x0, y - 1 + o, x1, y + o), fill=CLEAT)
        d.rectangle((x - 5, y - 12, x + 5, y - 8), fill=PANT); d.line((x + 2, y - 12, x + 5, y - 8), fill=PANT_D)
        d.line((x - 5, y - 12, x - 5, y - 8), fill=col); d.line((x + 5, y - 12, x + 5, y - 8), fill=col)
        d.rectangle((x - 6, y - 20, x + 6, y - 12), fill=col); d.rectangle((x + 3, y - 20, x + 6, y - 12), fill=dk(col, 0.75))
        d.rectangle((x - 8, y - 21, x + 8, y - 17), fill=col); d.line((x - 8, y - 21, x + 8, y - 21), fill=lt(col))   # shoulder pads
        a1 = 1 if frame else -1
        for sx, o in ((-1, a1), (1, -a1)):
            ax = x - 9 if sx < 0 else x + 8
            d.rectangle((ax, y - 19, ax + 1, y - 13 + o), fill=col); d.line((ax, y - 17, ax + 1, y - 17), fill=WHT)
            d.rectangle((ax, y - 13 + o, ax + 1, y - 12 + o), fill=SKIN)
        num_on(d, x, y - 19, num)
        d.ellipse((x - 5, y - 29, x + 5, y - 20), fill=col)                      # helmet
        d.ellipse((x - 1, y - 29, x + 5, y - 21), fill=dk(col, 0.8))
        d.line((x, y - 29, x, y - 21), fill=WHT)
        d.rectangle((x - 3, y - 27, x - 2, y - 26), fill=lt(col, 0.8))           # gloss
        if facing == "down":
            d.rectangle((x - 3, y - 25, x + 3, y - 21), fill=SKIN); d.line((x - 3, y - 24, x + 3, y - 24), fill=MASK)
            d.line((x - 3, y - 22, x + 3, y - 22), fill=MASK); d.line((x, y - 25, x, y - 21), fill=MASK)
        if ball:
            d.ellipse((x + 6, y - 18, x + 12, y - 13), fill=(150, 80, 20)); d.line((x + 8, y - 16, x + 10, y - 16), fill=WHT)

    def side_player(d, x, y, col, frame, f=1, ball=False, num="", pants=None, mask=None, shadow=True, arm_back=False):
        """Sideline-camera player. f=1 faces right, -1 faces left. (x, y) = feet."""
        x, y = int(x), int(y)
        if shadow: d.ellipse((x - 9, y - 2, x + 9, y + 2), fill=(0, 92, 24))
        def leg(a, b, lift=0):
            _r(d, x + a * f, y - 8 - lift, x + b * f, y - 5 - lift, PANT); _r(d, x + a * f, y - 4 - lift, x + b * f, y - 2 - lift, col)
            _r(d, x + a * f, y - 1 - lift, x + (b + 2) * f, y - lift, CLEAT)
        if frame: leg(-7, -4, 1); leg(2, 5)
        else: leg(-2, 1); leg(1, 3)
        _r(d, x - 5, y - 12, x + 5, y - 8, PANT); _r(d, x - 5, y - 10, x + 5, y - 10, col)
        _r(d, x - 5, y - 20, x + 5, y - 12, col); _r(d, x - 5 * f, y - 20, x - 2 * f, y - 12, dk(col, 0.75))
        _r(d, x - 6, y - 21, x + 6, y - 18, col); _r(d, x - 6, y - 21, x + 6, y - 21, lt(col))
        if arm_back:
            _r(d, x - 5 * f, y - 18, x - 13 * f, y - 16, col); _r(d, x - 9 * f, y - 18, x - 9 * f, y - 16, WHT)
            _r(d, x - 13 * f, y - 19, x - 15 * f, y - 15, SKIN)
        else:
            _r(d, x + 2 * f, y - 17, x + 6 * f, y - 14, col); _r(d, x + 6 * f, y - 16, x + 7 * f, y - 14, SKIN)
        num_on(d, x - 1 * f + (1 if f < 0 else 0), y - 19, num)
        if ball: d.ellipse((min(x + 3 * f, x + 10 * f), y - 18, max(x + 3 * f, x + 10 * f), y - 12), fill=(150, 80, 20))
        d.ellipse((x - 5, y - 29, x + 5, y - 20), fill=col)
        _r(d, x - 4 * f, y - 28, x - 1 * f, y - 26, lt(col, 0.7))
        _r(d, x + 3 * f, y - 25, x + 6 * f, y - 21, SKIN)
        _r(d, x + 5 * f, y - 26, x + 7 * f, y - 21, MASK); _r(d, x + 4 * f, y - 24, x + 7 * f, y - 24, MASK)

    def _leaper(col, num, arms_up, catch=False):
        """Back-view player going up for a ball."""
        def fn(dd, cx, fy, shadow=True):
            player(dd, cx, fy, col, 0, "up", num=num, shadow=False)
            if arms_up:
                for ax in (cx - 9, cx + 8):
                    dd.rectangle((ax, fy - 33, ax + 1, fy - 18), fill=col); dd.line((ax, fy - 26, ax + 1, fy - 26), fill=WHT)
                    dd.rectangle((ax, fy - 35, ax + 1, fy - 33), fill=SKIN)
                if catch:
                    dd.ellipse((cx - 6, fy - 39, cx + 6, fy - 32), fill=(150, 80, 20)); dd.line((cx - 2, fy - 36, cx + 2, fy - 36), fill=WHT)
        return outlined(fn)

    def side_fallen(d, x, y, col, f=1, shadow=True):
        x, y = int(x), int(y)
        if shadow: d.ellipse((x - 13, y - 2, x + 13, y + 2), fill=(0, 92, 24))
        _r(d, x - 13 * f, y - 5, x - 5 * f, y - 2, PANT); _r(d, x - 14 * f, y - 5, x - 12 * f, y - 1, col)
        _r(d, x - 5 * f, y - 7, x + 6 * f, y - 1, col); _r(d, x - 5 * f, y - 2, x + 6 * f, y - 1, dk(col, 0.7))
        _r(d, x - 3 * f, y - 8, x + 6 * f, y - 7, lt(col))
        d.ellipse((min(x + 5 * f, x + 14 * f), y - 9, max(x + 5 * f, x + 14 * f), y - 1), fill=col)
        _r(d, x + 12 * f, y - 7, x + 15 * f, y - 3, MASK)

    def diver(d, x, y, col, flip=False, shadow=True):
        x, y = int(x), int(y); s = -1 if flip else 1
        if shadow: d.ellipse((x - 11, y - 2, x + 11, y + 3), fill=(0, 92, 24))
        _r(d, x - 13 * s, y - 8, x - 7 * s, y - 6, col); _r(d, x - 14 * s, y - 8, x - 13 * s, y - 6, CLEAT)
        _r(d, x - 7 * s, y - 10, x, y - 5, PANT)
        _r(d, x, y - 11, x + 9 * s, y - 4, col); _r(d, x, y - 11, x + 9 * s, y - 10, lt(col))
        _r(d, x + 9 * s, y - 9, x + 15 * s, y - 7, col)
        cx = x + 13 * s; d.ellipse((cx - 5, y - 13, cx + 5, y - 4), fill=col); _r(d, cx - 2, y - 12, cx, y - 11, lt(col, 0.8))
        _r(d, x + 17 * s, y - 9, x + 20 * s, y - 7, SKIN)

    R.player = outlined(player)
    R.side_player = outlined(side_player)
    R.side_fallen = outlined(side_fallen)
    R.diver = outlined(diver)
    R._leaper = _leaper
