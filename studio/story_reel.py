"""Vedora story Reel (9:16): narrated, subtitle-driven, cold-to-warm mood.

Timeline JSON (VEDORA_TIMELINE=timeline.json), normally written by build_story_reel.py:
  {"duration": 40.0,
   "warmth": [[0, 0], [12, 0], [13, 1], ...],            # 0 = cold/dark, 1 = warm Vedora maroon + golden glow
   "elements": [{"style": "hook|sub|ref|shloka|meaning|check|take|end", "lines": [...],
                 "t_in": 0.2, "t_out": 3.5, "slot": 0}, ...]}
Usage: python3 story_reel.py still 5 12 30   |   python3 story_reel.py render 0 600 out.mp4
"""
import json, math, os, random, subprocess, sys

W, H, FPS = 1080, 1920, 30
DEV = 'font-family="FreeSans"'
SANS = 'font-family="Inter, sans-serif"'
SERIF = 'font-family="GFS Baskerville, Caladea, serif"'
CREAM, SOFT, GOLDC = "#F3DDB0", "#E2C27E", "#F6D27A"

TL = json.load(open(os.environ["VEDORA_TIMELINE"], encoding="utf-8")) if os.environ.get("VEDORA_TIMELINE") else {
    "duration": 10, "warmth": [[0, 0], [10, 1]], "elements": []}

DEFS = '''<defs>
<radialGradient id="bgw" cx="50%" cy="42%" r="72%"><stop offset="0" stop-color="#761428"/><stop offset="1" stop-color="#22050C"/></radialGradient>
<radialGradient id="bgc" cx="50%" cy="42%" r="72%"><stop offset="0" stop-color="#2B1E2A"/><stop offset="1" stop-color="#07060A"/></radialGradient>
<linearGradient id="gold" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FBE3A0"/><stop offset="0.55" stop-color="#E8B04B"/><stop offset="1" stop-color="#C08530"/></linearGradient>
<radialGradient id="halo"><stop offset="0" stop-color="#FFC861" stop-opacity="0.5"/><stop offset="0.45" stop-color="#E8B04B" stop-opacity="0.16"/><stop offset="1" stop-color="#E8B04B" stop-opacity="0"/></radialGradient>
</defs>'''

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)
def eo(x): return 1 - (1 - x) ** 3

random.seed(5)
PARTS = [(random.uniform(40, 1040), random.uniform(0, H), random.uniform(18, 55), random.uniform(1.5, 3.6),
          random.uniform(0, 6.28), random.uniform(0.2, 0.6)) for _ in range(50)]

def warmth(t):
    k = TL["warmth"]
    if t <= k[0][0]: return k[0][1]
    for (t0, w0), (t1, w1) in zip(k, k[1:]):
        if t <= t1: return w0 + (w1 - w0) * (0.5 - 0.5 * math.cos(math.pi * prog(t, t0, t1)))
    return k[-1][1]

def T(x, y, s, size, fam, fill, op, weight="normal", anchor="middle", ls=0, style="normal"):
    return (f'<text x="{x}" y="{y:.1f}" text-anchor="{anchor}" {fam} font-size="{size}" font-weight="{weight}" '
            f'font-style="{style}" letter-spacing="{ls}" fill="{fill}" opacity="{op:.3f}">{s}</text>')

def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def draw(e, t):
    a = eo(prog(t, e["t_in"], e["t_in"] + 0.35)) * (1 - eo(prog(t, e["t_out"] - 0.3, e["t_out"])))
    if a <= 0.002: return ""
    dy = 16 * (1 - eo(prog(t, e["t_in"], e["t_in"] + 0.45)))
    L = [esc(x) for x in e["lines"]]; st = e["style"]; o = []
    if st == "hook":
        y0 = 880 - 42 * (len(L) - 1)
        def block(op, fill_last="url(#gold)"):
            return "".join(T(540, y0 + 84 * i + dy, s, 56, SANS, fill_last if i == len(L) - 1 else CREAM, op, "700") for i, s in enumerate(L))
        for k in range(3):                      # echo rings: the line "goonjti" outward
            ph = ((t - e["t_in"]) / 1.6 + k / 3) % 1
            sc = 1 + 0.07 * ph
            o.append(f'<g transform="translate(540,{y0 + 42 * (len(L) - 1):.1f}) scale({sc:.4f}) translate(-540,{-(y0 + 42 * (len(L) - 1)):.1f})">'
                     + block(a * 0.16 * (1 - ph), CREAM) + '</g>')
        o.append(block(a))
    elif st in ("sub", "meaning"):
        size, y0, gap = (54, 900, 76) if st == "sub" else (46, 1080, 64)
        y0 -= gap / 2 * (len(L) - 1) if st == "sub" else 0
        for i, s in enumerate(L):
            fill = "url(#gold)" if s.startswith("\"") or s.startswith("&quot;") else CREAM
            o.append(T(540, y0 + gap * i + dy, s, size, SANS, fill, a, "600"))
    elif st == "ref":
        o.append(T(540, 610 + dy, L[0], 38, DEV, CREAM, a * 0.9, "bold", ls=1))
        o.append(f'<line x1="440" y1="{640 + dy:.1f}" x2="640" y2="{640 + dy:.1f}" stroke="#E8B04B" stroke-width="2" opacity="{0.6 * a:.3f}"/>')
    elif st == "shloka":
        for i, s in enumerate(L):
            o.append(T(540, 740 + 88 * i + dy, s, 54, DEV, "url(#gold)", a, "bold"))
    elif st == "check":
        y = 760 + 160 * e.get("slot", 0)
        o.append(f'<path d="M150,{y - 30 + dy:.1f} l14,14 l-14,14 l-14,-14 Z" fill="#E8B04B" opacity="{a:.3f}"/>')
        for i, s in enumerate(L):
            o.append(T(195, y + 60 * i + dy, s, 44, SANS, CREAM if i == 0 else SOFT, a, "600", anchor="start"))
    elif st == "take":
        y = 840 + 120 * e.get("slot", 0)
        o.append(T(540, y + dy, L[0], 64, SERIF, "url(#gold)", a))
    elif st == "end":
        for i, s in enumerate(L):
            o.append(T(540, 1190 + 50 * i + dy, s, 34, SANS, SOFT, a, "400", style="italic"))
        o.append(f'<g opacity="{a:.3f}"><rect x="290" y="{1330 + dy:.1f}" width="500" height="92" rx="46" fill="none" stroke="#E8B04B" stroke-width="2.5"/>'
                 + T(540, 1390 + dy, "Follow @the_vedora", 40, SANS, "#FBE3A0", 1, "600") + '</g>')
    return "".join(o)

def frame(t):
    w = warmth(t)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">', DEFS,
         f'<rect width="{W}" height="{H}" fill="url(#bgc)"/>',
         f'<rect width="{W}" height="{H}" fill="url(#bgw)" opacity="{w:.3f}"/>',
         f'<circle cx="540" cy="820" r="{560 + 60 * math.sin(t * 0.9):.1f}" fill="url(#halo)" opacity="{0.75 * w:.3f}"/>']
    for x0, y0, sp, r, ph, al in PARTS:
        y = (y0 - sp * t) % H
        x = x0 + 12 * math.sin(t * 0.7 + ph)
        op = al * (0.25 + 0.75 * w) * (0.55 + 0.45 * math.sin(t * 2.0 + ph))
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{GOLDC if w > 0.3 else "#C9B9A6"}" opacity="{op:.3f}"/>')
    o.append(T(540, 250, "@the_vedora", 30, SANS, SOFT, 0.85 * eo(prog(t, 0, 1.0)), "500", ls=6))
    for e in TL["elements"]:
        o.append(draw(e, t))
    D = TL["duration"]
    fb = max(1 - eo(prog(t, 0, 0.4)), prog(t, D - 0.6, D))
    if fb > 0: o.append(f'<rect width="{W}" height="{H}" fill="#000" opacity="{fb:.3f}"/>')
    o.append("</svg>")
    return "".join(o)

def png(t):
    return subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H)], input=frame(t).encode(), capture_output=True, check=True).stdout

if __name__ == "__main__":
    if sys.argv[1] == "still":
        for tt in sys.argv[2:]:
            open(f"story_still_{tt}.png", "wb").write(png(float(tt)))
    else:
        f0, f1, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "image2pipe", "-framerate", str(FPS), "-i", "-",
                               "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for i in range(f0, f1):
            ff.stdin.write(png(i / FPS))
        ff.stdin.close()
        sys.exit(ff.wait())
