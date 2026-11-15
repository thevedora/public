import math, pathlib, random, subprocess, sys

W, H, FPS, DUR = 1080, 1920, 30, 15.0

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, t0, t1): return clamp((t - t0) / (t1 - t0))
def eo(x): return 1 - (1 - x) ** 3                      # ease-out cubic
def eio(x): return 4*x**3 if x < .5 else 1 - (-2*x + 2)**3 / 2
def eback(x, s=1.7):
    x -= 1
    return 1 + (s + 1) * x**3 + s * x**2
def lerp(a, b, x): return a + (b - a) * x

DEFS = '''<defs>
<radialGradient id="bg" cx="50%" cy="45%" r="70%"><stop offset="0" stop-color="#6E1224"/><stop offset="1" stop-color="#22050C"/></radialGradient>
<linearGradient id="gold" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FBE3A0"/><stop offset="0.55" stop-color="#E8B04B"/><stop offset="1" stop-color="#B9782A"/></linearGradient>
<linearGradient id="flame" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFE07A"/><stop offset="1" stop-color="#F07A1A"/></linearGradient>
<radialGradient id="glowG"><stop offset="0" stop-color="#FFC861" stop-opacity="0.55"/><stop offset="0.5" stop-color="#E8B04B" stop-opacity="0.18"/><stop offset="1" stop-color="#E8B04B" stop-opacity="0"/></radialGradient>
<radialGradient id="fireG"><stop offset="0" stop-color="#FFE9A8" stop-opacity="0.9"/><stop offset="0.35" stop-color="#FF9A2E" stop-opacity="0.35"/><stop offset="1" stop-color="#FF7A1A" stop-opacity="0"/></radialGradient>
<filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="24"/></filter>
</defs>'''

EMBLEM_FILE = pathlib.Path(__file__).with_name("emblem.svgfrag")
P_OUT_L = "M520,780 C430,760 300,690 215,540 C330,560 450,640 520,780 Z"
P_OUT_R = "M560,780 C650,760 780,690 865,540 C750,560 630,640 560,780 Z"
P_V_L = "M540,790 C440,720 335,560 330,315 C430,410 525,590 540,790 Z"
P_V_R = "M540,790 C640,720 745,560 750,315 C650,410 555,590 540,790 Z"
FLAME = "M540,300 C585,400 618,470 618,540 C618,598 583,635 540,635 C497,635 462,598 462,540 C462,470 495,400 540,300 Z"
FLAME_IN = "M540,430 C560,480 575,515 575,552 C575,582 559,600 540,600 C521,600 505,582 505,552 C505,515 520,480 540,430 Z"

random.seed(7)
PARTS = [(random.uniform(60, 1020), random.uniform(0, H), random.uniform(25, 70),
          random.uniform(1.5, 4.0), random.uniform(0, 6.28), random.uniform(0.2, 0.6)) for _ in range(46)]

SERIF = 'font-family="GFS Baskerville, Caladea, serif"'
SANS = 'font-family="Inter, sans-serif"'

def text(x, y, s, size, fam, fill, ls, op, weight="normal", dy=0):
    return (f'<text x="{x}" y="{y + dy}" text-anchor="middle" {fam} font-size="{size}" '
            f'letter-spacing="{ls}" font-weight="{weight}" fill="{fill}" opacity="{op:.3f}">{s}</text>')

def frame(t):
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">', DEFS,
         f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']

    # floating sparks
    pin = eo(prog(t, 0, 1.5))
    for x0, y0, sp, r, ph, a in PARTS:
        y = (y0 - sp * t) % H
        x = x0 + 14 * math.sin(t * 0.8 + ph)
        op = pin * a * (0.55 + 0.45 * math.sin(t * 2.2 + ph))
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#F6D27A" opacity="{op:.3f}"/>')

    # emblem placement: centered, then moves up for the text
    mv = eio(prog(t, 9.0, 10.3))
    cy, sc = lerp(1000, 660, mv), lerp(1.1, 0.62, mv)

    bloom = eo(prog(t, 0.6, 4.2))
    pulse = 0.5 + 0.5 * math.sin(t * 2.4)
    glow = bloom * (0.65 + 0.35 * pulse)

    ign = prog(t, 5.0, 6.2)               # flame grows
    burst = math.exp(-((t - 5.7) / 0.55) ** 2)
    flicker = math.sin(t * 17) * 0.025 + math.sin(t * 29 + 1) * 0.015

    o.append(f'<g transform="translate(540,{cy:.1f}) scale({sc:.4f}) translate(-540,-600)">')
    # aura behind flower
    o.append(f'<circle cx="540" cy="560" r="{lerp(250, 470, bloom):.1f}" fill="url(#glowG)" opacity="{glow:.3f}"/>')
    # fire light once lit
    fire_op = clamp(eo(ign) * 0.75 + burst * 0.9, 0, 1) * (0.9 + 0.1 * math.sin(t * 9))
    if fire_op > 0.01:
        o.append(f'<circle cx="540" cy="480" r="{380 + 160 * burst:.1f}" fill="url(#fireG)" opacity="{fire_op:.3f}"/>')

    # petals open from a closed bud
    aV, aO = lerp(19, 0, bloom), lerp(42, 0, bloom)
    s_in = lerp(0.82, 1.0, bloom)
    o_out = eo(prog(t, 1.4, 4.0))
    petals = (f'<g transform="translate(540,790) scale({s_in:.4f}) translate(-540,-790)">'
              f'<path d="{P_OUT_L}" transform="rotate({aO:.2f},530,780)" fill="url(#gold)" opacity="{0.55 * o_out:.3f}"/>'
              f'<path d="{P_OUT_R}" transform="rotate({-aO:.2f},550,780)" fill="url(#gold)" opacity="{0.55 * o_out:.3f}"/>'
              f'<path d="{P_V_L}" transform="rotate({aV:.2f},540,790)" fill="url(#gold)"/>'
              f'<path d="{P_V_R}" transform="rotate({-aV:.2f},540,790)" fill="url(#gold)"/></g>')
    po = eo(prog(t, 0.3, 1.6))
    # glow halo of petals
    o.append(f'<g filter="url(#blur)" opacity="{0.85 * glow * po:.3f}">'
             + petals.replace('fill="url(#gold)"', 'fill="#FFC861"') + '</g>')
    o.append(f'<g opacity="{po:.3f}">{petals}</g>')

    # flame ignites (anchored at its base)
    if ign > 0:
        fs = eback(ign, 2.2)
        sx, sy = fs * (1 - flicker), fs * (1 + flicker * 1.6)
        o.append(f'<g transform="translate(540,635) scale({sx:.4f},{sy:.4f}) translate(-540,-635)">'
                 f'<path d="{FLAME}" fill="url(#flame)" filter="url(#blur)" opacity="{0.6:.2f}"/>'
                 f'<path d="{FLAME}" fill="url(#flame)"/><path d="{FLAME_IN}" fill="#FFF6DE"/></g>')
    # spark before ignition
    sp = math.exp(-((t - 4.9) / 0.25) ** 2)
    if sp > 0.02 and t < 5.6:
        o.append(f'<circle cx="540" cy="600" r="{10 + 30 * sp:.1f}" fill="#FFF3C4" opacity="{sp:.3f}" filter="url(#blur)"/>'
                 f'<circle cx="540" cy="600" r="{4 + 6 * sp:.1f}" fill="#FFFFFF" opacity="{sp:.3f}"/>')

    # base arc + dot
    bo = eo(prog(t, 3.0, 4.5))
    o.append(f'<path d="M400,825 Q540,880 680,825" fill="none" stroke="url(#gold)" stroke-width="14" stroke-linecap="round" opacity="{bo:.3f}"/>'
             f'<circle cx="540" cy="900" r="9" fill="#E8B04B" opacity="{bo:.3f}"/>')

    # ring draws around the logo after it lights
    rg = eio(prog(t, 6.0, 8.2))
    if rg > 0:
        C = 2 * math.pi * 430
        o.append(f'<circle cx="540" cy="600" r="430" fill="none" stroke="#E8B04B" stroke-width="5" opacity="0.55" '
                 f'stroke-dasharray="{C:.1f}" stroke-dashoffset="{C * (1 - rg):.1f}" transform="rotate(-90,540,600)"/>')
    o.append('</g>')

    # text
    def tin(t0, d=0.8): return eo(prog(t, t0, t0 + d))
    a = tin(9.9);  o.append(text(540, 1080, "WELCOME TO", 38, SANS, "#F3DDB0", 12, a, "300", 20 * (1 - a)))
    a = tin(10.3, 1.2); o.append(text(540, 1240, "VEDORA", 150, SERIF, "url(#gold)", lerp(60, 26, a), a, dy=20 * (1 - a)))
    ln = eio(prog(t, 10.9, 11.7))
    if ln > 0: o.append(f'<line x1="{540 - 180 * ln:.1f}" y1="1300" x2="{540 + 180 * ln:.1f}" y2="1300" stroke="#E8B04B" stroke-width="2" opacity="0.75"/>')
    a = tin(11.3); o.append(text(540, 1370, "DISCOVER THE WISDOM WITHIN", 40, SANS, "#F3DDB0", 8, a, "300", 20 * (1 - a)))
    a = tin(12.4)
    if a > 0:
        o.append(f'<g opacity="{a:.3f}" transform="translate(0,{20 * (1 - a):.1f})">'
                 f'<rect x="250" y="1490" width="580" height="104" rx="52" fill="none" stroke="#E8B04B" stroke-width="3"/>'
                 + text(540, 1558, "Follow @the_vedora", 46, SANS, "#FBE3A0", 1, 1, "500") + '</g>')
    a = tin(13.0); o.append(text(540, 1700, "and begin your journey", 50, SERIF, "url(#gold)", 1, a, dy=20 * (1 - a)))

    # fade from / to black
    fb = max(1 - eo(prog(t, 0, 0.8)), prog(t, DUR - 0.6, DUR))
    if fb > 0: o.append(f'<rect width="{W}" height="{H}" fill="#000" opacity="{fb:.3f}"/>')
    o.append('</svg>')
    return "".join(o)

def png(t):
    return subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H)], input=frame(t).encode(),
                          capture_output=True, check=True).stdout

if __name__ == "__main__":
    if sys.argv[1] == "still":
        for tt in sys.argv[2:]:
            open(f"still_{tt}.png", "wb").write(png(float(tt)))
    else:
        f0, f1, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "image2pipe", "-framerate", str(FPS), "-i", "-",
                               "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p", out],
                              stdin=subprocess.PIPE)
        for i in range(f0, f1):
            ff.stdin.write(png(i / FPS))
        ff.stdin.close()
        sys.exit(ff.wait())
