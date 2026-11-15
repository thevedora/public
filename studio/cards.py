"""Vedora post templates: shloka card + festival card (1080x1350, Instagram 4:5)."""
import pathlib, subprocess

EMBLEM = pathlib.Path(__file__).with_name("emblem.svgfrag").read_text()
W, H = 1080, 1350
DEV = 'font-family="FreeSans"'                       # Devanagari (proper conjuncts)
SERIF = 'font-family="GFS Baskerville, Caladea, serif"'
SANS = 'font-family="Inter, sans-serif"'
GOLD, CREAM, SOFT = "url(#gold)", "#F3DDB0", "#E2C27E"

DEFS = '''<defs>
<radialGradient id="bg" cx="50%" cy="40%" r="75%"><stop offset="0" stop-color="#761428"/><stop offset="1" stop-color="#26060E"/></radialGradient>
<linearGradient id="gold" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FBE3A0"/><stop offset="0.55" stop-color="#E8B04B"/><stop offset="1" stop-color="#C08530"/></linearGradient>
<linearGradient id="flame" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFD25E"/><stop offset="1" stop-color="#F07A1A"/></linearGradient>
<radialGradient id="glow"><stop offset="0" stop-color="#FFB347" stop-opacity="0.35"/><stop offset="1" stop-color="#FFB347" stop-opacity="0"/></radialGradient>
</defs>'''

def T(x, y, s, size, fam, fill, ls=0, weight="normal", anchor="middle", style="normal"):
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" {fam} font-size="{size}" font-weight="{weight}" '
            f'font-style="{style}" letter-spacing="{ls}" fill="{fill}">{s}</text>')

def emblem(cx, cy, s):
    return (f'<circle cx="{cx}" cy="{cy - 40 * s}" r="{330 * s}" fill="url(#glow)"/>'
            f'<g transform="translate({cx},{cy}) scale({s}) translate(-540,-600)">{EMBLEM}</g>')

def divider(y, half=170):
    return (f'<line x1="{540 - half}" y1="{y}" x2="{530}" y2="{y}" stroke="#E8B04B" stroke-width="2" opacity="0.7"/>'
            f'<line x1="550" y1="{y}" x2="{540 + half}" y2="{y}" stroke="#E8B04B" stroke-width="2" opacity="0.7"/>'
            f'<path d="M540,{y - 9} L549,{y} L540,{y + 9} L531,{y} Z" fill="#E8B04B"/>')

def frame():
    return (f'<rect width="{W}" height="{H}" fill="url(#bg)"/>'
            f'<rect x="34" y="34" width="{W - 68}" height="{H - 68}" rx="26" fill="none" stroke="#E8B04B" stroke-width="2" opacity="0.55"/>'
            f'<rect x="46" y="46" width="{W - 92}" height="{H - 92}" rx="20" fill="none" stroke="#E8B04B" stroke-width="1" opacity="0.25"/>')

def footer():
    return T(540, 1268, "@the_vedora", 28, SANS, SOFT, 6, "500")

def svg(body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{DEFS}{frame()}{body}{footer()}</svg>'

# ---------------- 1. Shloka card ----------------
def shloka_card(ref_hi, ref_en, sanskrit, hindi, english, takeaway):
    b = [emblem(540, 175, 0.2),
         T(540, 330, ref_hi, 34, DEV, CREAM, 1, "bold"),
         T(540, 372, ref_en, 24, SANS, SOFT, 6, "500")]
    y = 480
    for line in sanskrit:
        b.append(T(540, y, line, 50, DEV, GOLD, 0, "bold")); y += 76
    y += 4; b.append(divider(y)); y += 80
    for line in hindi:
        b.append(T(540, y, line, 37, DEV, CREAM)); y += 56
    y += 22
    for line in english:
        b.append(T(540, y, line, 30, SANS, SOFT, 0.5, "300", style="italic")); y += 44
    # takeaway pill
    y = max(y + 40, 1110)
    b.append(f'<rect x="150" y="{y - 52}" width="780" height="78" rx="39" fill="#E8B04B" fill-opacity="0.12" stroke="#E8B04B" stroke-width="1.5" stroke-opacity="0.6"/>')
    b.append(T(540, y - 2, takeaway, 30, DEV, "#FBE3A0", 0, "bold"))
    return svg("".join(b))

# ---------------- 2. Festival card ----------------
def festival_card(title_hi, title_en, date_line, steps, note):
    b = [emblem(540, 150, 0.17),
         T(540, 300, title_hi, 78, DEV, GOLD, 0, "bold"),
         T(540, 352, title_en, 30, SANS, SOFT, 8, "500"),
         f'<rect x="200" y="388" width="680" height="66" rx="33" fill="none" stroke="#E8B04B" stroke-width="2"/>',
         T(540, 432, date_line, 29, DEV, "#FBE3A0", 0.5, "bold"),
         T(540, 530, "पूजा विधि · PUJA VIDHI", 30, DEV, CREAM, 3, "bold"),
         divider(560, 150)]
    y = 640
    for i, (hi, en) in enumerate(steps, 1):
        b.append(f'<circle cx="150" cy="{y + 4}" r="30" fill="none" stroke="#E8B04B" stroke-width="2"/>')
        b.append(T(150, y + 15, str(i), 30, SANS, "#F6D27A", 0, "500"))
        b.append(T(205, y, hi, 34, DEV, CREAM, anchor="start"))
        b.append(T(205, y + 42, en, 25, SANS, SOFT, 0.3, "300", anchor="start", style="italic"))
        y += 110
    b.append(T(540, 1205, note, 22, SANS, "#C9A66B", 0.5, "300"))
    return svg("".join(b))

def render(name, content):
    p = pathlib.Path(name)
    p.with_suffix(".svg").write_text(content)
    subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H), str(p.with_suffix(".svg")), "-o", str(p.with_suffix(".png"))], check=True)
    subprocess.run(["convert", str(p.with_suffix(".png")), "-quality", "93", str(p.with_suffix(".jpg"))], check=True)

if __name__ == "__main__":
    render("sample_shloka_card", shloka_card(
        "श्रीमद्भगवद्गीता · अध्याय 2, श्लोक 47", "BHAGAVAD GITA · 2.47",
        ["कर्मण्येवाधिकारस्ते मा फलेषु कदाचन ।", "मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि ॥"],
        ["तुम्हारा अधिकार केवल कर्म करने में है,", "उसके फलों में कभी नहीं। कर्मफल को अपना",
         "उद्देश्य मत बनाओ, और कर्म न करने में", "भी तुम्हारी आसक्ति न हो।"],
        ["You have a right to your actions, never to their fruits.",
         "Don't let results be your motive, nor cling to inaction."],
        "आज का संदेश: Effort पर ध्यान दो, result Krishna पर छोड़ दो 🙏".replace(" 🙏", "")))
    render("sample_festival_card", festival_card(
        "देव उठनी एकादशी", "DEV UTHANI EKADASHI",
        "शुक्रवार, 20 नवंबर 2026 · Friday, 20 Nov",
        [("प्रातः स्नान और व्रत का संकल्प", "Early morning bath and the vow (sankalp) of the fast"),
         ("विष्णु जी की पूजा: तुलसी, पुष्प और दीप", "Worship Lord Vishnu with tulsi, flowers and a diya"),
         ("शंख-घंटी बजाकर भगवान को जगाएँ", "Ring bells and blow the shankh to awaken the Lord"),
         ("संध्या को घर और मंदिर में दीपदान", "In the evening, light diyas at home and in the temple"),
         ("तुलसी-शालिग्राम विवाह · शनिवार, 21 नवंबर", "Tulsi Vivah, the sacred wedding of Tulsi and Shaligram")],
        "Vaishnava Ekadashi: Sat, 21 Nov · Check your local Panchang for exact timings"))
