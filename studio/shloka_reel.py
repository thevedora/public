"""Vedora shloka Reel (9:16): verse reveal with @the_vedora mark.
Content can be overridden with a JSON file: VEDORA_CONTENT=content.json (keys: ref, sanskrit[2], hindi[2], english[2], takeaway).
Usage: python3 shloka_reel.py still 9   |   python3 shloka_reel.py render 0 360 out.mp4"""
import json, math, os, subprocess, sys
import anim
from anim import W, H, FPS, clamp, prog, eo, eio, lerp, DEFS, PARTS, P_OUT_L, P_OUT_R, P_V_L, P_V_R, FLAME, FLAME_IN

INTRO = 0.0
SCENE = 12.0
# When each element starts to appear (seconds). Override with "times" (and "duration") in VEDORA_CONTENT
# to sync with a narration track.
TIMES = dict(hook_in=0.2, hook_sub=1.5, hook_out=3.0, ref=0.3, s1=0.8, s2=1.4, divider=2.2, h1=2.6, h2=2.9, e1=3.8, e2=4.1, take=5.2)
DUR = INTRO + SCENE
DEV = 'font-family="FreeSans"'
SANS = 'font-family="Inter, sans-serif"'

CONTENT = dict(
    ref="श्रीमद्भगवद्गीता · 2.47",
    sanskrit=["कर्मण्येवाधिकारस्ते मा फलेषु कदाचन ।", "मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि ॥"],
    hindi=["तुम्हारा अधिकार केवल कर्म करने में है,", "उसके फलों में कभी नहीं।"],
    english=["Your right is to your actions alone,", "never to their fruits."],
    takeaway="Effort पर ध्यान दो, result Krishna पर छोड़ दो",
)

if os.environ.get("VEDORA_CONTENT"):
    CONTENT.update(json.load(open(os.environ["VEDORA_CONTENT"], encoding="utf-8")))
    TIMES.update(CONTENT.get("times", {}))
    SCENE = float(CONTENT.get("duration", SCENE))
    DUR = INTRO + SCENE

def lit_emblem(ta, cy, sc):
    """Fully bloomed, lit emblem with ring, as at the end of the intro. ta = animation clock."""
    pulse = 0.5 + 0.5 * math.sin(ta * 2.4)
    glow = 0.65 + 0.35 * pulse
    flicker = math.sin(ta * 17) * 0.025 + math.sin(ta * 29 + 1) * 0.015
    fire_op = 0.75 * (0.9 + 0.1 * math.sin(ta * 9))
    petals = (f'<path d="{P_OUT_L}" fill="url(#gold)" opacity="0.55"/><path d="{P_OUT_R}" fill="url(#gold)" opacity="0.55"/>'
              f'<path d="{P_V_L}" fill="url(#gold)"/><path d="{P_V_R}" fill="url(#gold)"/>')
    C = 2 * math.pi * 430
    return (f'<g transform="translate(540,{cy:.1f}) scale({sc:.4f}) translate(-540,-600)">'
            f'<circle cx="540" cy="560" r="470" fill="url(#glowG)" opacity="{glow:.3f}"/>'
            f'<circle cx="540" cy="480" r="380" fill="url(#fireG)" opacity="{fire_op:.3f}"/>'
            f'<g filter="url(#blur)" opacity="{0.85 * glow:.3f}">{petals.replace("url(#gold)", "#FFC861")}</g>{petals}'
            f'<g transform="translate(540,635) scale({1 - flicker:.4f},{1 + flicker * 1.6:.4f}) translate(-540,-635)">'
            f'<path d="{FLAME}" fill="url(#flame)" filter="url(#blur)" opacity="0.6"/><path d="{FLAME}" fill="url(#flame)"/>'
            f'<path d="{FLAME_IN}" fill="#FFF6DE"/></g>'
            f'<path d="M400,825 Q540,880 680,825" fill="none" stroke="url(#gold)" stroke-width="14" stroke-linecap="round"/>'
            f'<circle cx="540" cy="900" r="9" fill="#E8B04B"/>'
            f'<circle cx="540" cy="600" r="430" fill="none" stroke="#E8B04B" stroke-width="5" opacity="0.55" '
            f'stroke-dasharray="{C:.1f}" stroke-dashoffset="0"/></g>')

def text(y, s, size, fam, fill, a, weight="normal", style="normal", ls=0):
    return (f'<text x="540" y="{y + 18 * (1 - a):.1f}" text-anchor="middle" {fam} font-size="{size}" font-weight="{weight}" '
            f'font-style="{style}" letter-spacing="{ls}" fill="{fill}" opacity="{a:.3f}">{s}</text>')

def scene_frame(s):
    ta = 9.0 + s
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">', DEFS,
         f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    for x0, y0, sp, r, ph, a in PARTS:
        y = (y0 - sp * ta) % H
        x = x0 + 14 * math.sin(ta * 0.8 + ph)
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#F6D27A" opacity="{a * (0.55 + 0.45 * math.sin(ta * 2.2 + ph)):.3f}"/>')
    o.append(f'<text x="540" y="250" text-anchor="middle" {SANS} font-size="30" font-weight="500" letter-spacing="6" fill="#E2C27E" opacity="{0.85 * eo(prog(s, 0.0, 1.0)):.3f}">@the_vedora</text>')
    tin = lambda key, d=0.6: eo(prog(s, TIMES[key], TIMES[key] + d))
    c = CONTENT
    if c.get("hook"):                     # opening hook: big centred question, fades out before the shloka
        out = 1 - eo(prog(s, TIMES["hook_out"], TIMES["hook_out"] + 0.5))
        if out > 0:
            hl = c["hook"]; y0 = 900 - 45 * (len(hl) - 1)
            for i, line in enumerate(hl):
                fill = "url(#gold)" if i == len(hl) - 1 else "#F3DDB0"
                o.append(text(y0 + 92 * i, line, 62, DEV, fill, tin("hook_in", 0.7) * out, "bold"))
            if c.get("hook_sub"):
                o.append(text(y0 + 92 * len(hl) + 40, c["hook_sub"], 40, DEV, "#E2C27E", tin("hook_sub") * out))
    o.append(text(640, c["ref"], 40, DEV, "#F3DDB0", tin("ref"), "bold", ls=1))
    o.append(text(770, c["sanskrit"][0], 54, DEV, "url(#gold)", tin("s1"), "bold"))
    o.append(text(855, c["sanskrit"][1], 54, DEV, "url(#gold)", tin("s2"), "bold"))
    ln = eio(prog(s, TIMES["divider"], TIMES["divider"] + 0.7))
    if ln > 0:
        o.append(f'<line x1="{540 - 170 * ln:.1f}" y1="930" x2="{540 + 170 * ln:.1f}" y2="930" stroke="#E8B04B" stroke-width="2" opacity="0.7"/>'
                 f'<path d="M540,921 L549,930 L540,939 L531,930 Z" fill="#E8B04B" opacity="{ln:.3f}"/>')
    o.append(text(1030, c["hindi"][0], 42, DEV, "#F3DDB0", tin("h1")))
    o.append(text(1092, c["hindi"][1], 42, DEV, "#F3DDB0", tin("h2")))
    o.append(text(1190, c["english"][0], 34, SANS, "#E2C27E", tin("e1"), "300", "italic"))
    o.append(text(1240, c["english"][1], 34, SANS, "#E2C27E", tin("e2"), "300", "italic"))
    a = tin("take")
    if a > 0:
        o.append(f'<g opacity="{a:.3f}" transform="translate(0,{18 * (1 - a):.1f})">'
                 f'<rect x="120" y="1320" width="840" height="96" rx="48" fill="#E8B04B" fill-opacity="0.12" stroke="#E8B04B" stroke-width="2" stroke-opacity="0.7"/>'
                 f'<text x="540" y="1381" text-anchor="middle" {DEV} font-size="36" font-weight="bold" fill="#FBE3A0">{c["takeaway"]}</text></g>')
    fb = max(1 - eo(prog(s, 0, 0.5)), prog(s, SCENE - 0.5, SCENE))
    if fb > 0: o.append(f'<rect width="{W}" height="{H}" fill="#000" opacity="{fb:.3f}"/>')
    o.append('</svg>')
    return "".join(o)

def frame(t):
    return scene_frame(t)

def png(t):
    return subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H)], input=frame(t).encode(), capture_output=True, check=True).stdout

if __name__ == "__main__":
    if sys.argv[1] == "still":
        for tt in sys.argv[2:]:
            open(f"sr_still_{tt}.png", "wb").write(png(float(tt)))
    else:
        f0, f1, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "image2pipe", "-framerate", str(FPS), "-i", "-",
                               "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for i in range(f0, f1):
            ff.stdin.write(png(i / FPS))
        ff.stdin.close()
        sys.exit(ff.wait())
