"""Original synthesized backing tracks for ONC reels (no samples, no licensed music).

make_track(style, dur, hits, seed) -> float32 mono array at SR, normalized.
styles: "trap" (140 bpm 808s + hat rolls), "drive" (128 bpm four-on-the-floor, saw bass),
        "synthwave" (100 bpm arps + pads), "stomp" (stadium stomp-stomp-clap + organ)
"""
import numpy as np
from scipy.signal import lfilter

SR = 44100
STYLES = ["trap", "drive", "synthwave", "stomp"]


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

    def impact(self, at, gain=0.55):
        n = int(SR * 1.2); t = np.arange(n) / SR
        x = lowpass(self.noise(n), 2500) * np.exp(-t * 5) * 0.5 + np.sin(2 * np.pi * 48 * t) * np.exp(-t * 3)
        self.add(x, at, gain)

    def riser(self, at, dur, gain=0.18):
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
                x = np.tanh(2.2 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-t * 2.2)
                m.add(x.astype(np.float32), t0 + beat * b, 0.55)
            m.kick(t0, 0.8); m.kick(t0 + 2.5 * b, 0.6)
            m.clap(t0 + 2 * b, 0.7)
            for i in range(8):
                m.hat(t0 + i * b / 2, 0.22)
            if k % 2 == 1:                               # hat roll on last beat
                for i in range(6):
                    m.hat(t0 + 3 * b + i * b / 6, 0.16)
            t0 += bar; k += 1

    elif style == "drive":
        b = 60 / 128
        chords = [(45, [57, 60, 64]), (41, [53, 57, 60]), (48, [55, 60, 64]), (43, [55, 59, 62])]
        bar = 4 * b; t0 = 0.0; k = 0
        while t0 < dur:
            root, tri = chords[k % 4]
            for i in range(4):
                m.kick(t0 + i * b, 0.85)
                m.hat(t0 + i * b + b / 2, 0.18, open_=True)
            m.clap(t0 + b, 0.55); m.clap(t0 + 3 * b, 0.55)
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
            m.kick(t0, 0.8); m.kick(t0 + 2 * b, 0.8)
            m.snare(t0 + b, 0.55); m.snare(t0 + 3 * b, 0.55)
            for i in range(8):
                m.hat(t0 + i * b / 2, 0.12)
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
                    m.kick(t0 + pos, 0.9, punch=0.6); m.kick(t0 + pos + b / 2, 0.9, punch=0.6)
                else:
                    m.clap(t0 + pos, 0.9)
            n = int(SR * bar)
            t = np.arange(n) / SR
            org = sum(np.sin(2 * np.pi * hz(p) * t) + 0.4 * np.sin(4 * np.pi * hz(p) * t) for p in organ_notes[k % 4])
            org *= (1 + 0.15 * np.sin(2 * np.pi * 6 * t))  # leslie wobble
            m.add((org / 4 * env(n, 0.05, 0.8)).astype(np.float32), t0, 0.22)
            t0 += bar; k += 1
    else:
        raise ValueError(style)

    for h in hits:
        m.impact(h)
    for at, d in risers:
        m.riser(at, d)
    audio = m.a[: int(SR * dur)]
    audio = np.tanh(audio / max(1e-6, np.abs(audio).max()) * 1.3)
    audio /= max(1e-6, np.abs(audio).max()) / 0.88
    fn = int(SR * 0.8); audio[-fn:] *= np.linspace(1, 0, fn)
    return audio.astype(np.float32)
