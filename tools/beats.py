"""Original synthesized backing tracks for ONC reels (no samples, no licensed music).

make_track(style, dur, hits, seed) -> float32 mono array at SR, normalized.
Default (used for automatic reels):
  "rap"       - boom-bap rap beat: punchy drums + 808 bass, drops in full on the 3rd highlight (the card zoom)
  "taps"      - no music: one light drum tap on each highlight point (the hit times passed in)
  "lofi"      - low, mellow lo-fi hip-hop bed (soft drums, electric piano, sub bass, vinyl crackle); 3 variants by seed
Stadium styles:
  "ballpark"  - stadium organ playing "Take Me Out to the Ball Game" (1908, public domain) as a waltz, light crowd
  "fightsong" - original marching-band fight song: brass, snare cadence, bass drum, cymbals, bells
  "chant"     - stadium organ runs + "da-da, da-da-da" clap chant, crowd
  "stomp"     - stomp-stomp-clap with organ
Other styles: "trap", "drive", "synthwave".
"""
import numpy as np
from scipy.signal import lfilter

SR = 44100
STYLES = ["rap", "taps", "lofi", "ballpark", "fightsong", "chant", "stomp", "trap", "drive", "synthwave"]
ROTATION = ["rap"]    # automatic reels: boom-bap rap beat, kept low
QUIET = {"lofi"}      # styles with a quieter, warmer master


def hz(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    return lfilter([1 - a], [1, -a], x).astype(np.float32)


def env(n, attack, decay):
    t = np.arange(n) / SR
    a = np.minimum(1, t / max(attack, 1e-4))
    return (a * np.exp(-t * decay)).astype(np.float32)


def saw(f, n):
    t = np.arange(n) / SR
    return (2 * ((t * f) % 1) - 1).astype(np.float32)


def square(f, n):
    t = np.arange(n) / SR
    return np.sign(np.sin(2 * np.pi * f * t)).astype(np.float32)



# ---------- stadium instruments ----------
def organ(note, dur, rng=None):
    """Hammond-style stadium organ: drawbar harmonics + leslie wobble."""
    n = int(SR * dur); t = np.arange(n) / SR
    f0 = hz(note)
    vib = 1 + 0.0025 * np.sin(2 * np.pi * 6.2 * t)
    ph = 2 * np.pi * f0 * np.cumsum(vib) / SR
    x = np.zeros(n, dtype=np.float32)
    for ratio, w in [(0.5, 0.45), (1, 1.0), (1.5, 0.35), (2, 0.55), (3, 0.22), (4, 0.18), (6, 0.06)]:
        x += w * np.sin(ratio * ph)
    x *= (1 + 0.12 * np.sin(2 * np.pi * 5.8 * t + 1.0))          # leslie amplitude
    a = np.minimum(1, t / 0.006); r = np.clip((dur - t) / 0.05, 0, 1)
    click = np.exp(-t * 300) * 0.25 * np.sin(2 * np.pi * 4 * f0 * t)  # key click
    return ((x / 2.8) * a * r + click).astype(np.float32)


def organ_chord(notes, dur):
    return sum(organ(p, dur) for p in notes) / max(1, len(notes)) ** 0.7


def brass(note, dur):
    """Marching brass: detuned saws, soft swell attack, late vibrato."""
    n = int(SR * dur); t = np.arange(n) / SR
    f0 = hz(note)
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * t) * np.clip((t - 0.15) / 0.2, 0, 1)
    x = saw(1, n) * 0
    for det in (0.997, 1.0, 1.004):
        ph = (f0 * det * np.cumsum(vib) / SR) % 1
        x += 2 * ph - 1
    x = lowpass(lowpass(x / 3, 2600), 3800)
    a = np.minimum(1, t / 0.035); r = np.clip((dur - t) / 0.06, 0, 1)
    return (x * a * r * (0.85 + 0.15 * np.exp(-t * 6))).astype(np.float32)


def bell(note, dur=0.9):
    n = int(SR * dur); t = np.arange(n) / SR; f0 = hz(note)
    x = np.sin(2 * np.pi * f0 * t) + 0.3 * np.sin(2 * np.pi * f0 * 2.76 * t) * np.exp(-t * 6)
    return (x * np.exp(-t * 4.5)).astype(np.float32)


def crowd(n, rng, level=1.0):
    """Distant stadium crowd: band-limited noise with slow swells."""
    x = rng.standard_normal(n).astype(np.float32)
    band = lowpass(x, 2200) - lowpass(x, 350)
    t = np.arange(n) / SR
    swell = 0.7 + 0.3 * np.sin(2 * np.pi * 0.23 * t + 0.5) * np.sin(2 * np.pi * 0.11 * t)
    return (band * swell * level).astype(np.float32)


def epiano(note, dur):
    """Warm electric piano (Rhodes-ish FM tine) with soft tremolo."""
    n = int(SR * dur); t = np.arange(n) / SR; f = hz(note)
    idx = 1.6 * np.exp(-t * 3.5)
    x = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * t))
    x += 0.25 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 2)
    x *= (1 + 0.08 * np.sin(2 * np.pi * 4.5 * t))
    a = np.minimum(1, t / 0.008); r = np.clip((dur - t) / 0.15, 0, 1)
    return (x * a * r * np.exp(-t * 0.7)).astype(np.float32)


class Mix:
    def __init__(self, dur, rng):
        self.a = np.zeros(int(SR * dur) + SR, dtype=np.float32)
        self.rng = rng

    def add(self, sig, at, gain=1.0):
        s = int(at * SR)
        if s >= len(self.a):
            return
        e = min(len(self.a), s + len(sig))
        self.a[s:e] += sig[: e - s] * gain

    # --- drums ---
    def kick(self, at, gain=1.0, punch=1.0):
        n = int(SR * 0.45); t = np.arange(n) / SR
        f = 45 + 110 * punch * np.exp(-t * 22)
        self.add(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7), at, gain)

    def noise(self, n):
        return self.rng.standard_normal(n).astype(np.float32)

    def hat(self, at, gain=0.25, open_=False):
        n = int(SR * (0.25 if open_ else 0.05))
        x = np.diff(self.noise(n + 1)) * env(n, 0.001, 9 if open_ else 70)
        self.add(x, at, gain)

    def clap(self, at, gain=0.6):
        n = int(SR * 0.3)
        x = lowpass(self.noise(n), 5000) * env(n, 0.001, 16)
        for k, d in enumerate([0, 0.011, 0.022]):
            self.add(x * (0.6 if k < 2 else 1.0), at + d, gain * 0.6)

    def snare(self, at, gain=0.6):
        n = int(SR * 0.35); t = np.arange(n) / SR
        x = lowpass(self.noise(n), 7000) * env(n, 0.001, 10) + np.sin(2 * np.pi * 185 * t) * env(n, 0.001, 25)
        self.add(x, at, gain)

    def crash(self, at, gain=0.12):
        n = int(SR * 1.8)
        x = np.diff(self.noise(n + 1)) * env(n, 0.002, 2.2)
        self.add(lowpass(x, 9000), at, gain)

    def bassdrum(self, at, gain=0.5):
        n = int(SR * 0.5); t = np.arange(n) / SR
        x = np.sin(2 * np.pi * (60 + 30 * np.exp(-t * 30)) * t) * np.exp(-t * 6)
        x += lowpass(self.noise(n), 400) * np.exp(-t * 20) * 0.3
        self.add(x.astype(np.float32), at, gain)

    def impact(self, at, gain=0.16):
        n = int(SR * 1.2); t = np.arange(n) / SR
        x = lowpass(self.noise(n), 2500) * np.exp(-t * 5) * 0.5 + np.sin(2 * np.pi * 48 * t) * np.exp(-t * 3)
        self.add(x, at, gain)

    def riser(self, at, dur, gain=0.06):
        n = int(SR * dur); t = np.arange(n) / SR
        hi = np.diff(self.noise(n + 1))
        noise = (lowpass(self.noise(n), 1200) * (1 - t / dur) + hi * 0.5 * (t / dur)) * (t / dur) ** 2
        self.add(noise, at, gain)


def make_track(style, dur, hits, seed=1, risers=()):
    rng = np.random.default_rng(seed)
    m = Mix(dur, rng)

    if style == "trap":
        b = 60 / 140
        roots = [33, 33, 36, 31]                      # A1 A1 C2 G1
        bar = 4 * b; t0 = 0.0; k = 0
        while t0 < dur:
            # 808 line
            for beat, note in [(0, roots[k % 4]), (1.5, roots[k % 4]), (2.75, roots[(k + 2) % 4])]:
                n = int(SR * b * 1.4); t = np.arange(n) / SR
                f = hz(note) * (1 + 1.0 * np.exp(-t * 40))
                x = np.tanh(1.2 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-t * 2.8)
                m.add(x.astype(np.float32), t0 + beat * b, 0.38)
            m.kick(t0, 0.55); m.kick(t0 + 2.5 * b, 0.4)
            m.clap(t0 + 2 * b, 0.4)
            for i in range(8):
                m.hat(t0 + i * b / 2, 0.1)
            if k % 2 == 1:                               # hat roll on last beat
                for i in range(6):
                    m.hat(t0 + 3 * b + i * b / 6, 0.06)
            t0 += bar; k += 1

    elif style == "drive":
        b = 60 / 128
        chords = [(45, [57, 60, 64]), (41, [53, 57, 60]), (48, [55, 60, 64]), (43, [55, 59, 62])]
        bar = 4 * b; t0 = 0.0; k = 0
        while t0 < dur:
            root, tri = chords[k % 4]
            for i in range(4):
                m.kick(t0 + i * b, 0.55)
                m.hat(t0 + i * b + b / 2, 0.09, open_=True)
            m.clap(t0 + b, 0.35); m.clap(t0 + 3 * b, 0.35)
            for i in range(8):                           # off-beat saw bass
                if i % 2 == 1:
                    n = int(SR * b * 0.45)
                    x = lowpass(saw(hz(root), n), 900) * env(n, 0.003, 9)
                    m.add(x, t0 + i * b / 2, 0.45)
            n = int(SR * b * 0.6)                        # chord stab
            st = sum(saw(hz(p), n) for p in tri) / 3
            m.add(lowpass(st, 2600) * env(n, 0.002, 8), t0, 0.35)
            m.add(lowpass(st, 2600) * env(n, 0.002, 8), t0 + 2.5 * b, 0.25)
            t0 += bar; k += 1

    elif style == "synthwave":
        b = 60 / 100
        chords = [[57, 60, 64, 69], [53, 57, 60, 65], [48, 52, 55, 60], [55, 59, 62, 67]]
        bar = 4 * b; t0 = 0.0; k = 0
        arp = np.zeros_like(m.a)
        while t0 < dur:
            ch = chords[k % 4]
            m.kick(t0, 0.55); m.kick(t0 + 2 * b, 0.55)
            m.snare(t0 + b, 0.35); m.snare(t0 + 3 * b, 0.35)
            for i in range(8):
                m.hat(t0 + i * b / 2, 0.07)
            n = int(SR * bar)                            # pad
            pad = sum(saw(hz(p - 12), n) for p in ch) / 4
            m.add(lowpass(pad, 700) * env(n, 0.4, 0.3), t0, 0.22)
            for i in range(16):                          # arp
                note = ch[[0, 1, 2, 3, 2, 1, 2, 3][i % 8]] + 12
                n = int(SR * b / 4 * 0.9)
                x = lowpass(square(hz(note), n), 3200) * env(n, 0.002, 14)
                s = int((t0 + i * b / 4) * SR); e = min(len(arp), s + n)
                if s < len(arp):
                    arp[s:e] += x[: e - s] * 0.16
            t0 += bar; k += 1
        d = int(SR * 0.75 * b)                           # dotted-8th echo
        echo = arp.copy()
        for rep in range(1, 4):
            echo[d * rep:] += arp[: len(arp) - d * rep] * (0.35 ** rep)
        m.a += echo

    elif style == "stomp":
        b = 60 / 92
        bar = 4 * b; t0 = 0.0; k = 0
        organ_notes = [[57, 64, 69], [55, 62, 67], [53, 60, 65], [52, 59, 64]]
        while t0 < dur:
            for beat in (0, 1, 2, 3):                    # stomp stomp CLAP x2 per bar
                pos = beat * b
                if beat in (0, 2):
                    m.kick(t0 + pos, 0.55, punch=0.5); m.kick(t0 + pos + b / 2, 0.5, punch=0.5)
                else:
                    m.clap(t0 + pos, 0.45)
            n = int(SR * bar)
            t = np.arange(n) / SR
            org = sum(np.sin(2 * np.pi * hz(p) * t) + 0.4 * np.sin(4 * np.pi * hz(p) * t) for p in organ_notes[k % 4])
            org *= (1 + 0.15 * np.sin(2 * np.pi * 6 * t))  # leslie wobble
            m.add((org / 4 * env(n, 0.05, 0.8)).astype(np.float32), t0, 0.22)
            t0 += bar; k += 1




    elif style == "rap":
        var = seed % 3
        b = 60 / [90, 86, 94][var]
        bar = 4 * b
        s16 = b / 4
        drop = hits[2] if len(hits) > 2 else 0.0            # full beat lands on the card zoom
        origin = drop - bar * np.ceil(drop / bar)          # bar grid that lines up with the drop
        roots = [[33, 33, 29, 31], [28, 28, 36, 31], [31, 34, 29, 29]][var]   # Am / Em / Gm feels
        t0 = origin; k = 0
        while t0 < dur:
            full = t0 >= drop - 1e-6
            intro = not full
            def at(step):
                return t0 + step * s16 + (0.035 * b if step % 4 == 2 else 0.0)   # swing on the off 8ths
            # kick
            for st in ([0, 7, 10] if full else [0, 10]):
                if at(st) >= 0:
                    m.kick(at(st), 0.62 if st == 0 else 0.48, punch=0.8)
            # snare on 2 and 4 (from the second intro bar on)
            if full or t0 + bar > drop - bar * 0.5:
                for st in (4, 12):
                    if at(st) >= 0:
                        m.snare(at(st), 0.40 if full else 0.28)
            # hats
            for st in range(0, 16, 2):
                if at(st) >= 0:
                    m.hat(at(st), 0.10 if st % 4 == 0 else 0.07, open_=(st == 14 and full))
            # 808 bass only after the drop
            if full:
                root = roots[k % 4]
                for st, length, note in [(0, 6, root), (10, 5, root + (3 if k % 2 else 0))]:
                    n = int(SR * length * s16); tt = np.arange(n) / SR
                    f = hz(note) * (1 + 0.5 * np.exp(-tt * 45))
                    x = np.tanh(1.4 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-tt * 1.6)
                    x *= np.minimum(1, tt / 0.004) * np.clip((length * s16 - tt) / 0.04, 0, 1)
                    m.add(x.astype(np.float32), at(st), 0.42)
                k += 1
            t0 += bar
        # crash-free accent on the first highlight so the opener still lands
        if hits:
            m.kick(hits[0], 0.5, punch=0.8)
    elif style == "taps":
        # no instruments: a soft kick + rim tap on each highlight point, a double tap on the last one
        def tap(at, g=1.0):
            m.kick(at, 0.45 * g, punch=0.35)
            n = int(SR * 0.09); tt = np.arange(n) / SR
            rim = (np.diff(m.noise(n + 1)) * 0.5 + np.sin(2 * np.pi * 820 * tt)) * np.exp(-tt * 55)
            m.add(lowpass(rim.astype(np.float32), 6000), at, 0.22 * g)
        for i, h in enumerate(hits):
            tap(h, 0.8 if i == 0 else 1.0)
        if hits:
            tap(hits[-1] + 0.17, 0.7)
    elif style == "lofi":
        progs = [
            [[53, 64, 67, 72, 76], [52, 62, 67, 71, 74], [50, 60, 65, 69, 72], [48, 59, 64, 67, 71]],   # Fmaj7 Em7 Dm7 Cmaj7
            [[45, 59, 60, 64, 67], [41, 57, 60, 64, 67], [48, 59, 62, 64, 67], [43, 59, 62, 64, 69]],   # Am9 Fmaj9 Cmaj9 G6
            [[50, 60, 64, 65, 69], [43, 59, 64, 65, 69], [48, 59, 62, 64, 67], [45, 59, 60, 64, 67]],   # Dm9 G13 Cmaj9 Am9
        ]
        var = seed % 3
        prog = progs[var]
        b = 60 / [82, 86, 78][var]
        bar = 4 * b; t0 = 0.0; k = 0
        while t0 < dur:
            ch = prog[k % 4]
            root = ch[0] - 12
            # chords: soft, slightly strummed, held most of the bar, re-hit on beat 3 &
            for j, p in enumerate(ch[1:]):
                m.add(epiano(p, bar * 0.95), t0 + j * 0.012, 0.13)
            for j, p in enumerate(ch[2:]):
                m.add(epiano(p, b * 1.2), t0 + 2.5 * b + j * 0.01, 0.06)
            # sub bass
            for at, d in [(0, 1.5 * b), (2.5 * b, 1.2 * b)]:
                n = int(SR * d); tt = np.arange(n) / SR
                x = np.sin(2 * np.pi * hz(root) * tt) * np.minimum(1, tt / 0.01) * np.clip((d - tt) / 0.08, 0, 1)
                m.add(x.astype(np.float32), t0 + at, 0.30)
            # soft drums, lazy swing
            m.kick(t0, 0.34, punch=0.45); m.kick(t0 + 2.5 * b, 0.26, punch=0.45)
            m.snare(t0 + b, 0.14); m.snare(t0 + 3 * b, 0.14)
            for i in range(8):
                sw = 0.06 * b if i % 2 else 0.0
                m.hat(t0 + i * b / 2 + sw, 0.035 if i % 2 else 0.05)
            t0 += bar; k += 1
        # vinyl crackle + hiss
        n = len(m.a)
        crackle = np.zeros(n, dtype=np.float32)
        pos = rng.integers(0, n, size=int(dur * 18))
        crackle[pos] = rng.uniform(-1, 1, size=len(pos)).astype(np.float32)
        m.a += lowpass(crackle, 3000) * 0.25 + lowpass(rng.standard_normal(n).astype(np.float32), 4000) * 0.004
    elif style == "ballpark":
        # "Take Me Out to the Ball Game" (Albert Von Tilzer, 1908 - public domain), 3/4 waltz on stadium organ
        q = 0.36                                   # quarter note
        bar = 3 * q
        mel = [(60, 2), (72, 1), (69, 1), (67, 1), (64, 1), (67, 3), (62, 3),
               (60, 2), (72, 1), (69, 1), (67, 1), (64, 1), (67, 3), (67, 3)]
        harm = [[48, 52, 55]] * 3 + [[43, 50, 53, 55]] + [[48, 52, 55]] * 3 + [[43, 47, 50, 53]]
        start = 1.1
        # intro: organ run up to a held C chord
        for i, p in enumerate([48, 52, 55, 60, 64, 67, 72]):
            m.add(organ(p, 0.16), 0.05 + i * 0.07, 0.30)
        m.add(organ_chord([60, 64, 67, 72], 0.55), 0.55, 0.32)
        t = start
        for p, beats in mel:
            m.add(organ(p + 12, beats * q * 0.92), t, 0.42)
            t += beats * q
        for b_i, ch in enumerate(harm):              # oom-pah-pah
            t0 = start + b_i * bar
            m.add(organ(ch[0] - 12, q * 0.9), t0, 0.30)
            for k in (1, 2):
                m.add(organ_chord(ch[1:] if len(ch) > 3 else ch, q * 0.5), t0 + k * q, 0.16)
        end = start + len(harm) * bar
        for i, p in enumerate([67, 69, 71]):         # turnaround into the final chord
            m.add(organ(p + 12, q * 0.45), end + i * q * 0.5, 0.36)
        fin = end + 1.5 * q
        m.add(organ_chord([48, 60, 64, 67, 72, 76], max(1.0, dur - fin)), fin, 0.40)
        cr = crowd(len(m.a), rng)
        t = np.arange(len(m.a)) / SR
        m.a += cr * (0.035 + 0.06 * np.clip((t - fin + 0.5) / 1.0, 0, 1))

    elif style == "fightsong":
        # original fight-song melody (C major), marching band
        b = 60 / 144
        mel = [  # (note, beats)
            [(67, .5), (67, .5), (72, 1), (76, 1), (79, 1)],
            [(76, 1.5), (72, .5), (76, 1), (79, 1)],
            [(81, 1), (79, 1), (77, 1), (76, 1)],
            [(74, 2), (67, .5), (69, .5), (71, 1)],
            [(74, 1), (79, 1), (77, 1), (74, 1)],
            [(72, 3), (72, 1)],
        ]
        chords = [[48, 55, 64], [48, 55, 64], [53, 57, 65], [43, 55, 62], [43, 53, 59], [48, 55, 64]]
        # intro snare roll + crash
        for i in range(16):
            m.snare(i * 0.055, 0.04 + 0.12 * i / 16)
        start = 0.95
        m.crash(start, 0.14)
        t0 = start
        for bar_i, (phrase, ch) in enumerate(zip(mel, chords)):
            t = t0
            for p, beats in phrase:
                d = beats * b
                m.add(brass(p, d * 0.94), t, 0.30)
                m.add(bell(p + 12), t, 0.05)
                t += d
            for k in (0, 2):                                    # low brass on 1 and 3
                for p in ch:
                    m.add(brass(p, 2 * b * 0.9), t0 + k * b, 0.10)
            for k in range(4):                                  # bass drum on every beat, accent 1
                m.bassdrum(t0 + k * b, 0.42 if k % 2 == 0 else 0.28)
            for k in range(8):                                  # snare cadence
                acc = 0.22 if k in (1, 5) else 0.10
                m.snare(t0 + k * b / 2, acc)
            if bar_i % 2 == 1:
                for k in range(6):                              # roll into next phrase
                    m.snare(t0 + 3.5 * b + k * b / 12, 0.07)
            t0 += 4 * b
        m.crash(t0, 0.14)
        m.add(sum(brass(p, max(1.0, dur - t0)) for p in [60, 64, 67, 72]) / 2.2, t0, 0.32)
        m.bassdrum(t0, 0.5)
        m.a += crowd(len(m.a), rng) * 0.03

    elif style == "chant":
        # stadium organ runs + "da-da, da-da-da" clap chant (original)
        b = 0.5
        t0 = 0.0
        m.add(organ_chord([60, 64, 67], 0.9), 0.0, 0.25)
        t0 = 1.0
        for rep, key in enumerate([0, 0, 2, 2, 5]):
            if t0 > dur - 1.8:
                break
            # bar A: chant rhythm, organ stabs + claps
            for beat in (0, 1, 2, 2.5, 3):
                m.clap(t0 + beat * b, 0.38)
                m.add(organ_chord([60 + key, 64 + key, 67 + key], b * 0.4), t0 + beat * b, 0.26)
            m.kick(t0, 0.35); m.kick(t0 + 2 * b, 0.3)
            t0 += 4 * b
            if t0 > dur - 1.8:
                break
            # bar B: organ run up the scale
            run = [60, 62, 64, 65, 67, 69, 71, 72]
            for i, p in enumerate(run):
                m.add(organ(p + key + 12, b * 0.45), t0 + i * b / 2, 0.30)
            m.kick(t0, 0.3); m.kick(t0 + 2 * b, 0.3)
            t0 += 4 * b
        m.add(organ_chord([60 + 5, 64 + 5, 67 + 5, 72 + 5], max(1.0, dur - t0)), t0, 0.36)
        t = np.arange(len(m.a)) / SR
        m.a += crowd(len(m.a), rng) * (0.04 + 0.05 * np.clip((t - t0 + 0.5), 0, 1))
    else:
        raise ValueError(style)

    if style in ("trap", "drive", "synthwave"):   # only the trailer-style beats get booms/risers
        for h in hits:
            m.impact(h)
        for at, d in risers:
            m.riser(at, d)
    audio = m.a[: int(SR * dur)]
    audio = lowpass(audio, 6500 if style in QUIET else 9000)
    audio /= max(1e-6, np.abs(audio).max())
    if style == "taps":
        audio *= 0.4                                     # sparse taps: set by peak, light
    else:
        rms = float(np.sqrt(np.mean(audio ** 2)))
        target = 0.05 if style in QUIET else (0.065 if style == "rap" else 0.09)   # keep beds low under the video
        audio *= min(0.5, target / max(rms, 1e-6))
    if style != "taps":
        fi = int(SR * 0.3); audio[:fi] *= np.linspace(0, 1, fi)
    fn = int(SR * 1.2); audio[-fn:] *= np.linspace(1, 0, fn)
    return audio.astype(np.float32)
