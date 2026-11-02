"""איורים מקוריים במקום מדיה שמופיעה רק בבחינה המקוונת:
    2017-Q12 סעיף ג  – ניסוי הפלסמידים (סרטון)
    2017-Q15 סעיף ב  – יצירת צמח עגבנייה מהונדס (מצגת)
    2021-Q9          – ערכת ROSALIND לזיהוי קדמיום (סרטון)
    2017-Q16         – מחזור החיים של נגיף ה-HIV (מצגת)
    2019-Q5          – הכנת תאי CAR T ופעולתם (מצגת)

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


# ---------- 2017-Q16: מחזור החיים של נגיף ה-HIV ----------

MEMBRANE, CYTO, NUCLEUS, CD4_C, CCR5_C = "#4f8197", "#dcdff5", "#b4b9e0", "#f0953a", "#8f8a2b"
VRNA, VDNA, CELL_DNA = "#1f6fc4", "#a0349f", "#1f9aa0"
CELL = (720, 620, 560, 380)  # מרכז ורדיוסים של התא


def on_cell(deg):
    cx, cy, rx, ry = CELL
    a = math.radians(deg)
    return cx + rx * math.cos(a), cy + ry * math.sin(a), math.degrees(math.atan2(ry * math.sin(a) / ry ** 2, rx * math.cos(a) / rx ** 2))


def strand(x, y, length, color, amp=8, period=26, w=5):
    return wave(x, x + length, y, color, amp, period).replace('stroke-width="7"', f'stroke-width="{w}"')


def capsid(x, y, s=1.0, angle=0):
    return (f'<g transform="translate({x} {y}) rotate({angle}) scale({s})">'
            '<path d="M-20 -32 H20 L13 32 H-13 z" fill="#d9ac55" stroke="#a97f2d" stroke-width="4" stroke-linejoin="round"/>'
            + "".join(f'<path d="M{dx} -22 q7 7 0 14 q-7 7 0 14 q7 7 0 14 q-7 7 0 12" fill="none" stroke="{VRNA}" stroke-width="3"/>' for dx in (-5, 5))
            + f'<circle cx="-10" cy="-24" r="5" fill="{CD}"/><circle cx="9" cy="23" r="5" fill="{CD}"/></g>')


def spike(x, y, deg, r, s=1.0):
    a = math.radians(deg)
    x1, y1 = x + r * math.cos(a), y + r * math.sin(a)
    x2, y2 = x + (r + 24 * s) * math.cos(a), y + (r + 24 * s) * math.sin(a)
    return line(x1, y1, x2, y2, "#46609e", 4) + f'<circle cx="{x2:.1f}" cy="{y2:.1f}" r="{8 * s:.1f}" fill="#6079bd"/>'


def inner_dots(x, y, r, start=0, stop=360, n=26):
    return "".join(f'<circle cx="{x + r * math.cos(math.radians(start + (stop - start) * i / n)):.1f}" '
                   f'cy="{y + r * math.sin(math.radians(start + (stop - start) * i / n)):.1f}" r="4" fill="#1f9d94"/>' for i in range(n + 1))


def virus(x, y, r=70, spikes=(0, 45, 90, 135, 180, 225, 270, 315)):
    return ("".join(spike(x, y, d, r) for d in spikes)
            + f'<circle cx="{x}" cy="{y}" r="{r}" fill="#a9d6d3" stroke="{MEMBRANE}" stroke-width="9"/>'
            + inner_dots(x, y, r - 13) + capsid(x, y, r / 62))


def cd4(deg):
    x, y, n = on_cell(deg)
    return (f'<g transform="translate({x:.1f} {y:.1f}) rotate({n:.1f})">' + line(-4, 0, 16, 0, "#b95f18", 7)
            + "".join(f'<circle cx="{22 + i * 17}" cy="0" r="10" fill="{CD4_C}" stroke="#b95f18" stroke-width="2"/>' for i in range(4)) + "</g>")


def ccr5(deg):
    x, y, n = on_cell(deg)
    return (f'<g transform="translate({x:.1f} {y:.1f}) rotate({n + 90:.1f})">'
            f'<path d="M-24 0 c4 -28 10 -28 12 0 c2 28 8 28 12 0 c2 -28 8 -28 12 0 c2 28 8 28 12 0" fill="none" stroke="{CCR5_C}" stroke-width="6"/></g>')


def budding(x, y, deg, neck):
    """בליטה בקרום התא; neck – זווית הצוואר הפונה אל תוך התא."""
    r = 62
    nx, ny = x + (r - 3) * math.cos(math.radians(neck)), y + (r - 3) * math.sin(math.radians(neck))
    px, py = -math.sin(math.radians(neck)) * 26, math.cos(math.radians(neck)) * 26
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{CYTO}" stroke="{MEMBRANE}" stroke-width="12"/>'
            + inner_dots(x, y, r - 15, neck + 50, neck + 310, 16)
            + "".join(spike(x, y, neck + d, r + 4) for d in (75, 125, 180, 235, 285))
            + line(nx - px, ny - py, nx + px, ny + py, CYTO, 24) + capsid(x, y, 0.95, deg))


def q16():
    W, H = 1500, 1040
    cx, cy, rx, ry = CELL
    out = f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{CYTO}" stroke="{MEMBRANE}" stroke-width="14"/>'
    for deg in (10, 130, 150, 190, 300):
        out += cd4(deg)
    for deg in (0, 28, 75, 105, 160, 205, 290, 322):
        out += ccr5(deg)
    out += f'<ellipse cx="760" cy="680" rx="240" ry="190" fill="{NUCLEUS}"/>'
    # הנגיף והיצמדותו
    out += virus(1335, 130) + text(1150, 62, "נגיף HIV", size=CAP, weight=700)
    out += line(1341, 125, 1400, 245, INK, 2) + text(1405, 278, "RNA נגיפי", size=30)
    out += line(1345, 158, 1320, 325, INK, 2) + text(1320, 365, ["אנזים מתעתק", "במהופך (RT)"], size=30)
    out += arrow(1235, 150, 1045, 170, INK, 5) + text(1140, 135, "היצמדות", size=CAP)
    # הנגיף על קרום התא
    out += virus(940, 195, 64, (0, 45, 135, 180, 225, 270, 315))
    # התאחות וחדירה
    out += arrow(860, 165, 545, 200, INK, 5) + text(705, 150, "התאחות וחדירה", size=CAP)
    out += budding(470, 237, 0, 90)
    # יצירת DNA מ-RNA
    out += arrow(470, 320, 470, 372, INK, 5)
    out += strand(405, 400, 130, VRNA) + f'<circle cx="403" cy="400" r="7" fill="{CD}"/><circle cx="537" cy="400" r="7" fill="{CD}"/>'
    out += text(335, 412, "RNA", size=CAP)
    out += text(650, 425, ["יצירת DNA", "מ-RNA"], size=30)
    out += arrow(470, 425, 470, 482, INK, 5)
    out += strand(405, 505, 130, VRNA) + strand(405, 530, 130, VDNA) + f'<circle cx="537" cy="505" r="7" fill="{CD}"/>'
    out += arrow(470, 550, 470, 600, INK, 5)
    out += strand(405, 625, 130, VDNA) + strand(405, 650, 130, VDNA)
    out += text(335, 650, "DNA", size=CAP)
    out += arrow(475, 672, 610, 760, INK, 5)
    # DNA התא בגרעין ותעתוק
    out += wave(555, 680, 790, CELL_DNA, 9, 28).replace('stroke-width="7"', 'stroke-width="6"')
    out += wave(680, 810, 790, VDNA, 9, 28).replace('stroke-width="7"', 'stroke-width="6"')
    out += wave(810, 950, 790, CELL_DNA, 9, 28).replace('stroke-width="7"', 'stroke-width="6"')
    out += text(755, 845, "DNA תאי", size=30)
    out += arrow(745, 765, 745, 690, INK, 5)
    out += strand(690, 665, 110, VRNA, w=5) + text(850, 677, "RNA", size=CAP)
    # ייצור חלבונים ויציאת נגיף חדש
    out += f'<path d="M790 625 C860 480 1000 460 1085 545" fill="none" stroke="{INK}" stroke-width="5"/>' + arrow(1075, 533, 1105, 565, INK, 5)
    out += text(1085, 450, ["ייצור חלבוני", "נגיף"], size=CAP)
    out += strand(1090, 605, 80, VRNA) + "".join(f'<circle cx="{a}" cy="{b}" r="{c}" fill="{d}"/>' for a, b, c, d in
                                                  ((1075, 585, 8, CD), (1120, 575, 6, "#7a5fc0"), (1185, 590, 9, CD), (1190, 625, 6, "#7a5fc0"), (1100, 635, 7, CD)))
    out += arrow(1130, 650, 1130, 835, INK, 5)
    out += budding(1160, 925, 0, -120)
    out += arrow(1228, 945, 1295, 935, INK, 5)
    out += virus(1395, 925, 66) + text(1395, 768, ["נגיף HIV", "חדש"], size=CAP, weight=700)
    # קולטנים
    out += line(205, 440, 190, 335, INK, 2) + text(165, 318, "קולטן CCR5", size=30)
    out += line(112, 520, 100, 475, INK, 2) + text(100, 460, "קולטן CD4", size=30)
    return canvas(W, H, out), "data/exams/2017/figures/2017-q16-illustration.png", (W, H)


# ---------- 2019-Q5: הכנת תאי CAR T ----------

CELL_T, CELL_B, CELL_EDGE, NUC_T, NUC_B, CAR_C, CD19_C = "#bccbeb", "#b9c48f", "#8c8c8c", "#909fbb", "#94a577", "#e0764a", "#c94fb4"
GENE_OLD, GENE_CAR = "#6a64c9", "#ee6c1c"


def vector(x, y, colors, r=70):
    """נגיף שבקופסית שלו מקטעים בצבעים הנתונים."""
    out = "".join(spike(x, y, d, r) for d in range(0, 360, 36))
    out += f'<circle cx="{x}" cy="{y}" r="{r}" fill="#a9d6d3" stroke="{MEMBRANE}" stroke-width="8"/>' + inner_dots(x, y, r - 13)
    out += f'<path d="M{x - 30} {y - 28} H{x + 30} L{x + 22} {y + 28} H{x - 22} z" fill="#d9ac55" stroke="#a97f2d" stroke-width="3" stroke-linejoin="round"/>'
    step = 40 / max(len(colors), 1)
    for i, c in enumerate(colors):
        out += wave(x - 20 + i * step, x - 20 + (i + 1) * step, y, c, 6, 12).replace('stroke-width="7"', 'stroke-width="4"')
    return out


def cell(x, y, r, fill, nucleus, marks=""):
    return (f'<ellipse cx="{x}" cy="{y}" rx="{r}" ry="{r * .92:.1f}" fill="{fill}" stroke="{CELL_EDGE}" stroke-width="8"/>'
            f'<ellipse cx="{x - r * .18:.1f}" cy="{y + r * .08:.1f}" rx="{r * .55:.1f}" ry="{r * .55:.1f}" fill="{nucleus}"/>' + marks)


def rim(x, y, r, deg, d=0):
    a = math.radians(deg)
    return x + (r + d) * math.cos(a), y + (r + d) * r * .92 / r * math.sin(a)


def car(x, y, r, deg):
    x1, y1 = rim(x, y, r, deg)
    x2, y2 = rim(x, y, r, deg, 28)
    return line(x1, y1, x2, y2, "#46606f", 6) + f'<circle cx="{x2:.1f}" cy="{y2:.1f}" r="11" fill="{CAR_C}"/>'


def cd19(x, y, r, deg):
    x1, y1 = rim(x, y, r, deg)
    x2, y2 = rim(x, y, r, deg, 16)
    return (line(x1, y1, x2, y2, CD19_C, 5)
            + line(x2, y2, *rim(x, y, r, deg - 7, 32), CD19_C, 5) + line(x2, y2, *rim(x, y, r, deg + 7, 32), CD19_C, 5))


def car_t(x, y, r, degs=range(20, 380, 45)):
    return cell(x, y, r, CELL_T, NUC_T, "".join(car(x, y, r, d) for d in degs))


def title(x, y, s):
    return text(x, y, s, size=CAP, anchor="start", weight=700)


def q5():
    W, PH = 1500, 450
    H = PH * 2
    out = line(W / 2, 20, W / 2, H - 20, GRID, 2) + line(20, PH, W - 20, PH, GRID, 2)
    # שלב 1: הכנת הנשא
    out += step_badge(W - 44, 44, 1) + title(W - 84, 56, "הכנת הנשא")
    out += vector(1270, 265, [GENE_OLD, GENE_OLD]) + text(1270, 410, "נגיף", size=CAP)
    out += line(1270, 262, 1370, 165, INK, 2) + text(1370, 118, ["גנים המקודדים", 'לגורמי "אלימות"'], size=30)
    out += wave(1020, 1090, 215, GENE_CAR, 8, 22).replace('stroke-width="7"', 'stroke-width="5"')
    out += arrow(1165, 265, 960, 265)
    out += text(1055, 315, ["מקטע המכיל גנים", "המקודדים ל-CAR"], size=30)
    out += vector(860, 265, [GENE_OLD, GENE_CAR, GENE_OLD]) + text(860, 410, "נגיף מהונדס", size=CAP)
    # שלב 2: הדבקה
    out += step_badge(W / 2 - 44, 44, 2) + title(W / 2 - 84, 56, "הדבקת תאי T בנגיף המהונדס")
    out += cell(285, 245, 145, CELL_T, NUC_T)
    out += wave(355, 415, 245, GENE_OLD, 6, 14).replace('stroke-width="7"', 'stroke-width="4"')
    out += wave(372, 398, 245, GENE_CAR, 6, 14).replace('stroke-width="7"', 'stroke-width="4"')
    out += vector(510, 245, [], 58)
    out += text(285, 425, "תא T", size=CAP) + text(510, 370, "נגיף מהונדס", size=CAP)
    # שלב 3: ביטוי הקולטן
    out += step_badge(W - 44, PH + 44, 3) + title(W - 84, PH + 56, "ביטוי הקולטן CAR על-גבי תאי ה-T")
    cx3, cy3 = 1130, PH + 265
    out += car_t(cx3, cy3, 135)
    bx, by = rim(cx3, cy3, 135, 335, 40)
    out += line(bx + 8, by - 6, 1370, PH + 165, INK, 2) + text(1385, PH + 150, "הקולטן CAR", size=30)
    out += text(cx3 - 235, cy3 + 11, "תא CAR T", size=CAP)
    # שלב 4: חיסול תאים סרטניים
    out += step_badge(W / 2 - 44, PH + 44, 4) + title(W / 2 - 84, PH + 56, "חיסול תאים סרטניים על-ידי תאי CAR T")
    y4 = PH + 255
    out += car_t(640, y4, 72, (45, 90, 135, 180, 225, 270, 315))
    out += cell(430, y4, 72, CELL_B, NUC_B, "".join(cd19(430, y4, 72, d) for d in (0, 50, 95, 140, 180, 225, 270, 315)))
    out += text(640, y4 + 150, "תא CAR T", size=30) + text(430, y4 + 150, "תא B סרטני", size=30)
    out += line(430, y4 - 100, 430, y4 - 120, INK, 2) + text(430, y4 - 128, "CD19", size=30)
    out += arrow(318, y4, 250, y4)
    out += car_t(120, y4, 62, (0, 60, 120, 180, 240, 300))
    rnd = random.Random(3)
    for _ in range(14):
        ang, d = rnd.uniform(0, 6.28), rnd.uniform(92, 108)
        out += f'<circle cx="{120 + d * math.cos(ang):.1f}" cy="{y4 + d * math.sin(ang):.1f}" r="4" fill="{NUC_B}"/>'
    return canvas(W, H, out), "data/exams/2019/figures/2019-q5-illustration.png", (W, H)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for build in (q12, q15, q9, q16, q5):
            markup, rel, (w, h) = build()
            page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=2)
            page.set_content(f'<!DOCTYPE html><html><head><meta charset="utf-8"></head><body style="margin:0">{markup}</body></html>')
            page.screenshot(path=str(ROOT / rel))
            page.close()
            print(f"-> {rel}")
        browser.close()


if __name__ == "__main__":
    main()
