import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR, DUR = 48000, 12.0
N = int(SR * DUR)
BEAT = 60 / 96          # 96 BPM
E8 = BEAT / 2
rng = np.random.default_rng(11)

def bw(kind, f, sig, order=2):
    return sosfilt(butter(order, f, kind, fs=SR, output="sos"), sig)

def reverb_ir(length=1.8, decay=3.6):
    n = int(length * SR)
    ir = rng.standard_normal((n, 2)) * np.exp(-np.arange(n) / SR * decay)[:, None]
    for c in range(2):
        ir[:, c] = bw("low", 4000, ir[:, c])
    return ir / np.sqrt((ir ** 2).sum(axis=0))

class Bus:
    def __init__(self): self.x = np.zeros((N + SR * 4, 2))
    def add(self, sig, t0, gain=1.0, pan=0.0):
        i = int(round(t0 * SR)); j = i + len(sig)
        self.x[i:j, 0] += sig * gain * np.sqrt(0.5 * (1 - pan))
        self.x[i:j, 1] += sig * gain * np.sqrt(0.5 * (1 + pan))

dry, wet = Bus(), Bus()   # wet bus goes through reverb

NOTE = dict(G2=98.0, A2=110.0, B2=123.47, D2=73.42, D3=146.83, G3=196.0, A3=220.0, B3=246.94,
            Cs4=277.18, D4=293.66, E4=329.63, Fs4=369.99, G4=392.0, A4=440.0, B4=493.88,
            Cs5=554.37, D5=587.33, E5=659.26, Fs5=739.99, G5=783.99, A5=880.0)

# ---------- instruments ----------
def santoor(f, dur=1.6):
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.zeros(n)
    for det in (-0.0009, 0.0009):                      # paired strings, slight chorus
        for k, (a, tau) in enumerate([(1, .9), (.55, .6), (.32, .45), (.18, .3), (.1, .2)]):
            fk = f * (k + 1) * (1 + 0.0007 * k * k) * (1 + det)
            s += a * np.sin(2 * np.pi * fk * t + rng.uniform(0, 6)) * np.exp(-t / tau)
    s += rng.standard_normal(n) * np.exp(-t / 0.003) * 0.4   # hammer tick
    return s / 4

def bass(f, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    env = np.clip(t / 0.03, 0, 1) * np.exp(-t / (dur * 0.6))
    return (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t)) * env

def baya(dur=0.6):        # low tabla
    n = int(dur * SR); t = np.arange(n) / SR
    f = 70 + 55 * np.exp(-t / 0.05)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.22)
    return s + rng.standard_normal(n) * np.exp(-t / 0.004) * 0.2

def daya(f=640, dur=0.5): # high tabla "na"
    n = int(dur * SR); t = np.arange(n) / SR
    s = sum(a * np.sin(2 * np.pi * f * m * t) for m, a in [(1, 1), (2.02, .45), (3.01, .3), (4.1, .12)])
    return s * np.exp(-t / 0.11) / 1.6 + bw("high", 2500, rng.standard_normal(n)) * np.exp(-t / 0.006) * 0.5

def tik(dur=0.15):        # muted "ti/ke"
    n = int(dur * SR); t = np.arange(n) / SR
    return bw("band", [1800, 6000], rng.standard_normal(n)) * np.exp(-t / 0.025)

def shaker(dur=0.12):
    n = int(dur * SR); t = np.arange(n) / SR
    e = np.clip(t / 0.012, 0, 1) * np.exp(-t / 0.035)
    return bw("high", 6000, rng.standard_normal(n)) * e

def bell(f0=1180.0, dur=3.0):
    n = int(dur * SR); t = np.arange(n) / SR
    parts = [(1.0, 1.0, 1.3), (2.0, .55, .9), (2.76, .5, .7), (4.07, .3, .5), (5.4, .2, .35), (6.8, .12, .25)]
    s = sum(a * np.sin(2 * np.pi * f0 * r * t + rng.uniform(0, 6)) * np.exp(-t / d) for r, a, d in parts)
    s *= 1 + 0.08 * np.sin(2 * np.pi * 3.5 * t)
    return s / np.max(np.abs(s)) + rng.standard_normal(n) * np.exp(-t / 0.004) * 0.5

def conch(dur=2.6, f0=293.66):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f0 * (0.93 + 0.07 * (1 - np.exp(-t / 0.15))) * (1 + 0.004 * np.sin(2 * np.pi * 5.4 * t) * np.clip(t - 0.5, 0, 1))
    f *= np.where(t > dur - 0.5, 1 - 0.05 * ((t - (dur - 0.5)) / 0.5) ** 2, 1)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = sum(a * np.sin((k + 1) * ph) for k, a in enumerate([1, .85, .7, .55, .38, .26, .17, .11, .07]))
    s = s / np.max(np.abs(s)) + bw("band", [600, 3000], rng.standard_normal(n)) * 0.2
    env = np.clip(t / 0.3, 0, 1) ** 1.5 * np.where(t > dur - 0.7, np.clip((dur - t) / 0.7, 0, 1), 1)
    return bw("low", 4200, s * env)

def flute(notes, t_start):
    """notes: list of (name, start_beat, len_beats). Legato bansuri-style line."""
    end = t_start + max(b + l for _, b, l in notes) * BEAT + 0.4
    n = int((end - t_start) * SR); t = np.arange(n) / SR
    freq = np.full(n, NOTE[notes[0][0]]); amp = np.zeros(n); vib = np.zeros(n)
    for name, b, l in notes:
        i0, i1 = int(b * BEAT * SR), int((b + l) * BEAT * SR)
        freq[i0:] = NOTE[name]
        tt = np.arange(i1 - i0) / SR
        a = np.clip(tt / 0.05, 0, 1) * (0.88 + 0.12 * np.exp(-tt / 0.15))
        a *= np.clip((tt[-1] - tt) / 0.06, 0, 1) * 0.85 + 0.15     # small articulation dip
        amp[i0:i1] = np.maximum(amp[i0:i1], a)
        vib[i0:i1] = np.clip((tt - 0.22) / 0.3, 0, 1)
    last_end = int(max(b + l for _, b, l in notes) * BEAT * SR)
    amp[last_end:] = 0
    k = int(0.05 * SR); win = np.hanning(k) / np.hanning(k).sum()
    freq = np.convolve(np.log(freq), win, "same"); freq = np.exp(freq)    # portamento
    amp = np.convolve(amp, np.hanning(int(0.02 * SR)) / np.hanning(int(0.02 * SR)).sum(), "same")
    f = freq * (1 + 0.006 * vib * np.sin(2 * np.pi * 5.6 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) + 0.32 * np.sin(2 * ph) + 0.1 * np.sin(3 * ph) + 0.04 * np.sin(4 * ph)
    breath = bw("band", [1200, 4000], rng.standard_normal(n), 4) * 0.035
    return (s * (1 + 0.03 * rng.standard_normal(n).cumsum() / np.sqrt(np.arange(1, n + 1))) + breath) * amp


CH = {"D": ["D4", "Fs4", "A4", "D5", "Fs5", "A5"], "G": ["G3", "B3", "D4", "G4", "B4", "D5"],
      "Bm": ["B3", "D4", "Fs4", "B4", "D5", "Fs5"], "A": ["A3", "Cs4", "E4", "A4", "Cs5", "E5"]}
PROG = [("D", "D2"), ("G", "G2"), ("Bm", "B2"), ("A", "A2"), ("D", "D2")]
PAT = [0, 2, 3, 2]
for bar, (ch, root) in enumerate(PROG):
    t_bar = bar * 4 * BEAT
    for i, idx in enumerate(PAT):
        t = t_bar + i * BEAT + 0.3
        if t > 11.0: continue
        sig = santoor(NOTE[CH[ch][idx]], 2.0)
        dry.add(sig, t, 0.22, -0.3 + 0.2 * i); wet.add(sig, t, 0.2, -0.3 + 0.2 * i)
    dry.add(bass(NOTE[root], 4 * BEAT), t_bar, 0.16)
t = np.arange(N) / SR
dr = sum(g * sum((0.7 ** k) * np.sin(2 * np.pi * f * (k + 1) * t + k) for k in range(6))
         for f, g in [(146.83, 1.0), (220.0, .6), (73.42, .5)])
dr = bw("low", 1200, dr); dr /= np.max(np.abs(dr))
dr *= np.clip(t / 1.5, 0, 1) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.2 * t))
dry.add(dr, 0, 0.12)
# mix down
ir = reverb_ir()
w = np.stack([fftconvolve(wet.x[:, c], ir[:, c])[: len(wet.x)] for c in range(2)], axis=1)
mix = (dry.x + 0.55 * w)[:N]
mix[:, 0] = bw("high", 35, mix[:, 0]); mix[:, 1] = bw("high", 35, mix[:, 1])
mix /= np.max(np.abs(mix))
mix = np.tanh(1.1 * mix) / np.tanh(1.1)                      # gentle glue / loudness
mix *= np.clip((DUR - t) / 1.0, 0, 1)[:, None] * np.clip(t / 0.05, 0, 1)[:, None]
mix *= 0.89 / np.max(np.abs(mix))
wavfile.write("shloka_bed.wav", SR, (mix * 32767).astype(np.int16))
print("done")
