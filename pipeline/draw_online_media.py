"""איורים מקוריים במקום מדיה שמופיעה רק בבחינה המקוונת:
    2017-Q12 סעיף ג  – ניסוי הפלסמידים (סרטון)
    2017-Q15 סעיף ב  – יצירת צמח עגבנייה מהונדס (מצגת)
    2021-Q9          – ערכת ROSALIND לזיהוי קדמיום (סרטון)

שימוש:
    .venv/bin/python -I pipeline/draw_online_media.py
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import ROOT  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

INK, GRID, BROTH, AGAR, ACCENT = "#111", "#cfcfcf", "#e7d9b0", "#e9dfc0", "#1677b8"
LEAF, LEAF_D, CALLUS = "#7cc58a", "#2f7d44", "#dfe9f5"
FONT = 'font-family="Arial, Helvetica, sans-serif"'
CAP = 34  # גודל הכיתוב: הייצוא לוורד מקטין את האיור לרוחב 600


def line(x1, y1, x2, y2, color=INK, w=3):
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>'


def text(x, y, lines, size=30, anchor="middle", weight=400, lh=None):
    """טקסט בעברית; lines – מחרוזת או רשימת שורות."""
    if isinstance(lines, str):
        lines = [lines]
    lh = lh or size * 1.22
    return "".join(
        f'<text x="{x:.1f}" y="{y + i * lh:.1f}" text-anchor="{anchor}" direction="rtl" font-weight="{weight}" '
        f'{FONT} font-size="{size}" fill="{INK}">{s}</text>' for i, s in enumerate(lines))


def arrow(x1, y1, x2, y2, color=ACCENT, w=8):
    """חץ ישר מ-(x1,y1) אל (x2,y2)."""
    a = math.atan2(y2 - y1, x2 - x1)
    bx, by = x2 - 22 * math.cos(a), y2 - 22 * math.sin(a)
    px, py = 13 * math.sin(a), -13 * math.cos(a)
    return (line(x1, y1, bx, by, color, w)
            + f'<path d="M{x2:.1f} {y2:.1f} L{bx + px:.1f} {by + py:.1f} L{bx - px:.1f} {by - py:.1f} z" fill="{color}"/>')


def step_badge(x, y, n):
    return (f'<circle cx="{x}" cy="{y}" r="24" fill="#fff" stroke="{INK}" stroke-width="3"/>'
            + text(x, y + 11, str(n), size=31, weight=700))


def tube(x, y, label=None, fill=BROTH, h=170, w=52, dots=False):
    """מבחנה; (x, y) – מרכז הפתח."""
    r = w / 2
    out = (f'<path d="M{x - r} {y + 26} V{y + h - r} a{r} {r} 0 0 0 {w} 0 V{y + 26} z" fill="{fill}"/>'
           f'<path d="M{x - r} {y} V{y + h - r} a{r} {r} 0 0 0 {w} 0 V{y}" fill="none" stroke="{INK}" stroke-width="3"/>')
    if dots:
        rnd = random.Random(int(x))
        for _ in range(26):
            out += f'<circle cx="{x + rnd.uniform(-r + 6, r - 6):.1f}" cy="{y + rnd.uniform(38, h - 12):.1f}" r="2.6" fill="#6b5a2c"/>'
    if label:
        out += text(x, y - 12, label, size=34, weight=700)
    return out


def plate(x, y, rx=118, ry=30, colonies=0, seed=4, contents=""):
    """צלחת גידול; (x, y) – מרכז."""
    out = (f'<ellipse cx="{x}" cy="{y + 12}" rx="{rx}" ry="{ry}" fill="#d9d9d9" stroke="{INK}" stroke-width="3"/>'
           f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{AGAR}" stroke="{INK}" stroke-width="3"/>')
    rnd = random.Random(seed)
    for _ in range(colonies):
        a, d = rnd.uniform(0, 6.28), rnd.uniform(0.1, 0.86) ** 0.5
        out += (f'<circle cx="{x + rx * .9 * d * math.cos(a):.1f}" cy="{y + ry * .85 * d * math.sin(a):.1f}" r="4.5" '
                f'fill="#fff" stroke="{INK}" stroke-width="1.5"/>')
    return out + contents


def pipette(x, y, drop=ACCENT):
    """פיפטה שקצה שלה ב-(x, y)."""
    return (f'<path d="M{x - 12} {y - 112} h24 v66 l-8 12 l-3 34 h-2 l-3 -34 l-8 -12 z" fill="#bcbcbc" stroke="{INK}" stroke-width="2.5"/>'
            f'<circle cx="{x}" cy="{y + 14}" r="4.5" fill="{drop}"/><circle cx="{x}" cy="{y + 30}" r="4.5" fill="{drop}"/>')


def ring(x, y, r, color="#8f8fc7", w=11):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{color}" stroke-width="{w}"/>'


def arc(x, y, r, a1, a2, color, w=13):
    """קשת על טבעת; זוויות במעלות, 0 למעלה ועם כיוון השעון."""
    p1 = (x + r * math.sin(math.radians(a1)), y - r * math.cos(math.radians(a1)))
    p2 = (x + r * math.sin(math.radians(a2)), y - r * math.cos(math.radians(a2)))
    large = 1 if (a2 - a1) % 360 > 180 else 0
    return f'<path d="M{p1[0]:.1f} {p1[1]:.1f} A{r} {r} 0 {large} 1 {p2[0]:.1f} {p2[1]:.1f}" fill="none" stroke="{color}" stroke-width="{w}"/>'


def canvas(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<rect width="{w}" height="{h}" fill="#fff"/>{body}</svg>')


# ---------- 2017-Q12: ניסוי הפלסמידים ----------

def plasmid(x, y, with_insert):
    out = ring(x, y, 62) + arc(x, y, 62, 150, 210, "#e0964a")
    out += text(x, y + 9, "פלסמיד", size=26)
    out += line(x, y + 68, x, y + 82, INK, 2) + text(x, y + 108, ["גן לעמידות", "לאמפיצילין"], size=28, lh=31)
    if with_insert:
        out += arc(x, y, 62, -60, -15, "#3c9b4a")
        out += line(x - 36, y - 56, x - 52, y - 76, INK, 2) + text(x - 60, y - 84, "מחדר", size=28)
    return out


def add_plasmid(c, letter, with_insert, caption):
    return (plasmid(c - 75, 205, with_insert) + arrow(c - 5, 205, c + 68, 205, w=6)
            + tube(c + 105, 120, letter, dots=True) + text(c, 395, caption, size=CAP))


def q12():
    W, H, top = 1500, 970, 500
    out = line(W / 2, 20, W / 2, H - 20, GRID, 2) + line(20, top, W - 20, top, GRID, 2)
    # שלב 1
    out += step_badge(W - 44, 44, 1)
    out += tube(1330, 110, dots=True) + tube(1120, 110, "א") + tube(960, 110, "ב")
    out += arrow(1290, 190, 1160, 190)
    out += f'<path d="M1290 150 C1210 40 1080 35 1020 82" fill="none" stroke="{ACCENT}" stroke-width="8"/>' + arrow(1020, 82, 992, 106)
    out += text(1330, 335, ["מבחנה המכילה מצע", "מזון נוזלי וחיידקים"], size=CAP)
    out += text(1040, 335, ["מבחנות המכילות", "מצע מזון נוזלי"], size=CAP)
    # שלב 2
    out += step_badge(W / 2 - 44, 44, 2)
    out += add_plasmid(560, "א", True, ["מוסיפים למבחנה א'", "תמיסה שיש בה פלסמידים", "שמכילים מחדר"])
    out += add_plasmid(190, "ב", False, ["מוסיפים למבחנה ב'", "תמיסה שיש בה פלסמידים", "שאינם מכילים מחדר"])
    # שלב 3
    out += step_badge(W - 44, top + 44, 3)
    out += tube(1370, top + 70, "א", h=140, dots=True) + tube(1270, top + 70, "ב", h=140, dots=True)
    out += pipette(1130, top + 190) + pipette(900, top + 190)
    out += plate(1130, top + 262, rx=100) + plate(900, top + 262, rx=100)
    out += text(1130, top + 345, "א", size=34, weight=700) + text(900, top + 345, "ב", size=34, weight=700)
    out += text(1015, top + 395, ["צלחות ובהן מצע מזון", "המכיל אמפיצילין"], size=CAP)
    # שלב 4
    out += step_badge(W / 2 - 44, top + 44, 4)
    out += text(375, top + 110, ["הצלחות מודגרות למשך 24 שעות", "באינקובטור, בטמפרטורה של 37ºC"], size=CAP)
    out += plate(530, top + 265, rx=125, ry=34) + plate(215, top + 265, rx=125, ry=34, colonies=30)
    out += text(530, top + 350, "א", size=34, weight=700) + text(215, top + 350, "ב", size=34, weight=700)
    return canvas(W, H, out), "data/exams/2017/figures/2017-q12c-illustration.png", (W, H)


# ---------- 2017-Q15: צמח עגבנייה מהונדס ----------

def plant(x, y, s=1.0):
    """צמח; (x, y) – תחתית הגבעול."""
    out = line(x, y, x, y - 190 * s, LEAF_D, 6)
    for dy, side in ((40, -1), (75, 1), (110, -1), (140, 1), (168, -1)):
        lx, ly = x + side * 42 * s, y - dy * s - 12 * s
        out += (f'<ellipse cx="{lx:.1f}" cy="{ly:.1f}" rx="{38 * s:.1f}" ry="{17 * s:.1f}" fill="{LEAF}" stroke="{LEAF_D}" stroke-width="3" '
                f'transform="rotate({-side * 24} {lx:.1f} {ly:.1f})"/>')
    return out


def disc(x, y):
    return f'<ellipse cx="{x}" cy="{y}" rx="17" ry="7" fill="{LEAF}" stroke="{LEAF_D}" stroke-width="2.5"/>'


def callus(x, y, r=13):
    return "".join(f'<circle cx="{x + dx * r / 13:.1f}" cy="{y + dy * r / 13:.1f}" r="{r}" fill="{CALLUS}" stroke="#3f6a9b" stroke-width="2.5"/>'
                   for dx, dy in ((-11, -2), (11, -2), (0, -13)))


def plate_with(x, y, sizes):
    """צלחת עם שלוש דסקיות; sizes – גודל הקאלוס על כל דסקית (0 = ללא)."""
    items = ""
    for dx, r in zip((-68, 0, 68), sizes):
        items += disc(x + dx, y + 4)
        if r:
            items += callus(x + dx, y - 6, r)
    return plate(x, y, contents=items)


def q15():
    W, H, top = 1500, 1000, 570
    out = line(W / 2, 20, W / 2, H - 20, GRID, 2) + line(20, top, W - 20, top, GRID, 2)
    # שלב 1
    out += step_badge(W - 44, 44, 1)
    out += plant(1390, 345) + text(1390, 387, "צמח עגבנייה", size=CAP)
    out += (f'<ellipse cx="1075" cy="140" rx="74" ry="40" fill="{LEAF}" stroke="{LEAF_D}" stroke-width="3" transform="rotate(-18 1075 140)"/>'
            + "".join(f'<circle cx="{x}" cy="{y}" r="11" fill="#fff" stroke="{LEAF_D}" stroke-width="2.5"/>' for x, y in ((1045, 148), (1078, 128), (1105, 145))))
    out += arrow(1295, 150, 1170, 150)
    out += text(1175, 250, ["מחוררים עלה", "ומוציאים דסקיות"], size=CAP)
    out += arrow(1040, 205, 985, 268)
    out += plate(925, 325, contents=disc(863, 328) + disc(925, 328) + disc(987, 328))
    out += text(925, 405, ["מניחים את דסקיות", "העלים על-גבי מצע גידול"], size=CAP)
    # שלב 2 – החיידק בהגדלה
    out += step_badge(W / 2 - 44, 44, 2)
    bx, by = 322, 195
    out += f'<rect x="{bx - 275}" y="{by - 130}" width="550" height="260" rx="120" fill="#d7e6f3" stroke="#2f6d9e" stroke-width="7"/>'
    out += (f'<path d="M{bx + 182} {by - 62} c-55 -50 -70 25 -15 28 c50 4 40 -68 -14 -40 c-44 22 2 90 42 50 c26 -28 -40 -60 -56 -12 c-14 44 62 60 72 8" '
            f'fill="none" stroke="#5b6b7b" stroke-width="5"/>')
    out += text(bx + 178, by + 58, ["כרומוזום", "חיידקי"], size=28, lh=31)
    tx, ty = bx + 2, by
    out += ring(tx, ty, 82, "#1f5f8f", 7)
    out += arc(tx, ty, 82, 125, 165, "#b08a3c") + arc(tx, ty, 82, 172, 232, "#29a8df")
    out += arc(tx, ty, 82, 112, 120, INK, 16) + arc(tx, ty, 82, 237, 245, INK, 16)
    out += text(tx, ty - 8, "מיני Ti", size=30, weight=700) + text(tx, ty + 24, "(פלסמיד מעביר)", size=22)
    px, py = bx - 170, by
    out += ring(px, py, 72, "#1f5f8f", 7) + arc(px, py, 72, -35, 35, "#8a8a8a", 12)
    out += text(px, py - 2, "pVIR", size=30, weight=700) + text(px, py + 28, "(פלסמיד עוזר)", size=22)
    out += line(tx + 47, ty + 67, tx + 96, ty + 150, INK, 2)
    out += f'<text x="{tx + 100}" y="{ty + 184}" {FONT} font-size="30" text-anchor="middle" fill="{INK}">kan<tspan dy="-10" font-size="20">R</tspan></text>'
    out += line(tx - 28, ty + 77, tx - 92, ty + 150, INK, 2) + text(tx - 105, ty + 184, "גן המקודד לאנטיפורטר", size=28)
    out += plate(610, 462, rx=100, ry=26, contents=disc(556, 464) + disc(610, 464) + disc(664, 464))
    out += text(265, 440, ["מדביקים את דסקיות העלים", "בחיידקי אגרובקטריום מהונדסים"], size=CAP)
    out += text(265, 530, "(בהגדלה: חיידק אגרובקטריום מהונדס)", size=26)
    # שלב 3
    out += step_badge(W - 44, top + 44, 3)
    out += plate_with(1290, top + 215, (13, 13, 13)) + arrow(1150, top + 215, 1085, top + 215)
    out += pipette(945, top + 135, "#3f6a9b") + plate_with(945, top + 215, (0, 21, 0))
    out += text(1290, top + 305, ["מגדלים את דסקיות העלים", "עד קבלת תרביות קאלוס"], size=CAP)
    out += text(945, top + 305, ["מוסיפים למצע הגידול", "את האנטיביוטיקה", "קנמיצין"], size=CAP)
    # שלב 4
    out += step_badge(W / 2 - 44, top + 44, 4)
    out += pipette(555, top + 135, "#e0964a") + plate_with(555, top + 215, (0, 21, 0))
    out += text(555, top + 305, ["מוסיפים למצע", "הגידול הורמונים"], size=CAP)
    out += arrow(410, top + 215, 300, top + 215)
    out += plant(180, top + 265, 1.05)
    out += text(180, top + 305, ["מתקבל צמח עגבנייה", "טרנסגני המסוגל לגדול", "על קרקע מלוחה"], size=CAP)
    return canvas(W, H, out), "data/exams/2017/figures/2017-q15b-illustration.png", (W, H)


# ---------- 2021-Q9: ערכת ROSALIND ----------

CAD, ENZ, CD, BINDER, BOUND = "#d8f06a", "#d79ad9", "#e4575c", "#f2b45f", "#3ec92f"


def wave(x1, x2, y, color="#1677b8", amp=16, period=58):
    d = f"M{x1} {y}"
    x, up = x1, True
    while x < x2:
        nx = min(x + period / 2, x2)
        d += f" Q{(x + nx) / 2:.1f} {y + (-amp * 2 if up else amp * 2)} {nx:.1f} {y}"
        x, up = nx, not up
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="7" stroke-linecap="round"/>'


def dna(x0, y):
    """מקטע DNA עם אזור הבקרה במרכזו."""
    rx, ry, rw, rh = x0 + 165, y - 34, 180, 68
    return (wave(x0, x0 + 510, y)
            + f'<rect x="{rx}" y="{ry}" width="{rw}" height="{rh}" fill="#efe3f0" stroke="{INK}" stroke-width="2.5"/>'
            + text(rx + rw / 2, y + 11, "אזור בקרה", size=30, weight=700))


def cadc(x, y, cd=False):
    """גורם התעתוק: חריץ עליון לקדמיום וחריץ תחתון לקישור ל-DNA. (x, y) – מרכז."""
    out = (f'<path d="M{x - 60} {y - 40} H{x - 20} a20 20 0 0 0 40 0 H{x + 60} V{y + 40} H{x + 22} l-10 -14 h-24 l-10 14 H{x - 60} z" '
           f'fill="{CAD}" stroke="{INK}" stroke-width="3"/>')
    out += text(x, y + 16, "CadC", size=30, weight=700)
    if cd:
        out += cadmium(x, y - 38)
    return out


def enzyme(x, y):
    return (f'<path d="M{x - 62} {y + 34} V{y} q0 -34 62 -34 q62 0 62 34 V{y + 34} z" fill="{ENZ}" stroke="{INK}" stroke-width="3"/>'
            + text(x, y - 1, "אנזים", size=27, weight=700) + text(x, y + 27, "מתעתק", size=27, weight=700))


def cadmium(x, y, r=19):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{CD}" stroke="{INK}" stroke-width="2.5"/>'


def dot(x, y, color, r=14):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}" stroke="{INK}" stroke-width="2"/>'


def mrna(x, y, bound=False):
    d = wave(x, x + 150, y, "#555", amp=11, period=46)
    if not bound:
        return d
    return d + dot(x + 3, y, BOUND, 13) + dot(x + 52, y - 12, BOUND, 13) + dot(x + 100, y + 2, BOUND, 13) + dot(x + 146, y, BOUND, 13)


def small_tube(x, y, fill, label):
    return (f'<path d="M{x - 42} {y} V{y + 40} L{x} {y + 130} L{x + 42} {y + 40} V{y}" fill="none" stroke="{INK}" stroke-width="3"/>'
            f'<path d="M{x - 42} {y + 34} V{y + 40} L{x} {y + 130} L{x + 42} {y + 40} V{y + 34} z" fill="{fill}" stroke="{INK}" stroke-width="2"/>'
            + text(x, y + 170, label, size=30))


def q9():
    W, H, LEG = 1500, 880, 100
    pw, ph = W / 2, (H - LEG) / 2
    out = line(pw, 20, pw, H - LEG - 10, GRID, 2) + line(20, ph, W - 20, ph, GRID, 2) + line(20, H - LEG, W - 20, H - LEG, GRID, 2)
    # 1: גורם התעתוק קשור לאזור הבקרה והקדמיום בתמיסה
    x0, y = pw + 10, 280
    out += step_badge(W - 44, 44, 1)
    out += small_tube(1385, 80, "#cfe7ee", ["דגימת מים", "שהוסיפו לערכה"])
    out += dna(x0, y) + cadc(x0 + 255, y - 62) + enzyme(x0 + 395, y - 72)
    out += cadmium(x0 + 90, y - 215) + cadmium(x0 + 255, y - 195)
    out += text(x0 + 80, y + 72, "מקטע DNA", size=30)
    # 2: קדמיום נקשר לגורם התעתוק
    x0, y = 100, 280
    out += step_badge(pw - 44, 44, 2)
    out += dna(x0, y) + cadc(x0 + 255, y - 62, True) + enzyme(x0 + 395, y - 72)
    # 3: גורם התעתוק משתחרר ונוצר mRNA
    x0, y = pw + 30, ph + 280
    out += step_badge(W - 44, ph + 44, 3)
    out += dna(x0, y) + enzyme(x0 + 90, y - 72)
    out += mrna(x0 + 60, y - 140) + text(x0 + 135, y - 178, "mRNA", size=30)
    cx, cy = x0 + 410, y - 170
    out += cadc(cx, cy, True)
    out += line(cx + 19, cy - 40, cx + 75, cy - 40, INK, 2) + text(cx + 135, cy - 44, ["אתר קישור", "לקדמיום"], size=26, lh=29)
    out += line(cx + 12, cy + 30, cx + 75, cy + 50, INK, 2) + text(cx + 135, cy + 50, ["אתר קישור", "ל-DNA"], size=26, lh=29)
    # 4: חומר קושר RNA נקשר ל-mRNA והמבחנה זוהרת
    y = ph + 170
    out += step_badge(pw - 44, ph + 44, 4)
    out += dot(620, y - 70, BINDER) + dot(370, y + 25, BINDER) + dot(585, y + 45, BINDER)
    out += mrna(430, y - 20, True) + mrna(385, y + 100, True)
    out += arrow(345, y + 45, 235, y + 45)
    out += small_tube(130, ph + 55, BOUND, ["אור בתוך", "המבחנה"])
    # מקרא
    ly = H - 40
    out += cadmium(1420, ly - 10, 16) + text(1395, ly, "קדמיום", size=32, anchor="start")
    out += dot(1200, ly - 10, BINDER) + text(1175, ly, "חומר קושר RNA", size=32, anchor="start")
    out += dot(700, ly - 10, BOUND) + text(675, ly, "חומר קושר RNA לאחר הקישור ל-RNA", size=32, anchor="start")
    return canvas(W, H, out), "data/exams/2021/figures/2021-q9-illustration.png", (W, H)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for build in (q12, q15, q9):
            markup, rel, (w, h) = build()
            page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=2)
            page.set_content(f'<!DOCTYPE html><html><head><meta charset="utf-8"></head><body style="margin:0">{markup}</body></html>')
            page.screenshot(path=str(ROOT / rel))
            page.close()
            print(f"-> {rel}")
        browser.close()


if __name__ == "__main__":
    main()
