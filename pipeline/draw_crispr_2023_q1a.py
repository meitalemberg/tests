"""איור מקורי לשאלה 2023-Q1 סעיף א: שתי שיטות העריכה בקריספר, במקום האנימציות שבבחינה המקוונת.

בכל שורה שלושה שלבים מימין לשמאל. התוויות הן אלו שמופיעות באנימציות המקוריות; השימוש
העיקרי של כל שיטה הוא התשובה לסעיף ולכן אינו כתוב באיור.

שימוש:
    .venv/bin/python -I pipeline/draw_crispr_2023_q1a.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import ROOT  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

OUT = ROOT / "data/exams/2023/figures/2023-q1a-illustration.png"

W, ROW_H = 1480, 340
INK, DNA, CAS, GUIDE, INSERT, GRID = "#111", "#444", "#bfe6e2", "#1f7a70", "#0b5fa5", "#d8d8d8"
PANEL_W = 430
PANELS = (1020, 520, 20)  # x של כל שלב, מימין לשמאל
DNA_Y = 190   # הגדיל העליון, יחסית לראש השורה
GAP = 42      # מרחק בין הגדילים
STEP = 20     # מרחק בין בסיסים
CUT = 70      # מחצית רוחב אזור החיתוך


def line(x1, y1, x2, y2, color=DNA, w=3):
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>'


def text(x, y, s, size=36, anchor="middle", weight=400):
    return (f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" direction="rtl" font-weight="{weight}" '
            f'font-family="Arial, Helvetica, sans-serif" font-size="{size}" fill="{INK}">{s}</text>')


def callout(x, y, tx, ty, s, side="left"):
    """תווית עם קו מוביל מהנקודה (x, y) לטקסט, שנמצא משמאל או מימין לקצה הקו."""
    if side == "left":
        return line(x, y, tx, ty, INK, 2) + text(tx - 8, ty + 12, s, anchor="start")
    return line(x, y, tx, ty, INK, 2) + text(tx + 8, ty + 12, s, anchor="end")


def ladder(x1, x2, y, skip=None):
    """מקטע DNA דו-גדילי; skip = תחום x שבו הבסיסים אינם משוכים (נחתך)."""
    out = line(x1, y, x2, y, DNA, 5) + line(x1, y + GAP, x2, y + GAP, DNA, 5)
    x = x1 + STEP / 2
    while x < x2:
        if not (skip and skip[0] <= x <= skip[1]):
            out += line(x, y, x, y + GAP, DNA, 3)
        x += STEP
    return out


def cut_dna(x0, y):
    """מולקולה חתוכה: שני קצוות ורווח ביניהם."""
    mid = x0 + PANEL_W / 2
    return ladder(x0, mid - CUT, y) + ladder(mid + CUT, x0 + PANEL_W, y)


def nucleotide(x, y, angle, color=DNA, w=5):
    return (f'<g transform="translate({x:.1f} {y:.1f}) rotate({angle})">'
            + line(-11, 0, 11, 0, color, w) + line(-11, 0, -11, -15, color, 3) + "</g>")


def cas9_on_dna(x0, y):
    """Cas-9 ו-RNA מדריך על מולקולת DNA שלמה."""
    mid = x0 + PANEL_W / 2
    gy = y - 34  # הגדיל של ה-RNA המדריך
    blob = f'<ellipse cx="{mid}" cy="{y - 8}" rx="150" ry="92" fill="{CAS}"/>'
    guide = line(mid - 70, gy, mid + 95, gy, GUIDE, 5)
    x = mid - 60
    while x <= mid + 90:
        guide += line(x, gy, x, y - 2, GUIDE, 2)
        x += STEP
    guide += line(mid - 70, gy, mid - 70, gy - 22, GUIDE, 4)
    guide += f'<circle cx="{mid - 70}" cy="{gy - 40}" r="18" fill="none" stroke="{GUIDE}" stroke-width="4"/>'
    labels = (callout(mid + 70, y - 75, mid + 120, y - 128, "Cas-9", "right")
              + callout(mid - 86, gy - 48, mid - 140, y - 128, "RNA מדריך"))
    return blob + ladder(x0, x0 + PANEL_W, y) + guide + labels


def cut_with_nucleotides(x0, y):
    """שיטה 1: לאחר החיתוך נוקלאוטידים חופשיים מתקרבים לרווח."""
    mid = x0 + PANEL_W / 2
    spots = [(-48, -48, 20), (-10, -78, -25), (38, -44, 30), (-34, 92, -20), (6, 112, 25), (46, 88, -30)]
    return cut_dna(x0, y) + "".join(nucleotide(mid + dx, y + dy, a) for dx, dy, a in spots)


def mutated(x0, y):
    """שיטה 1: הרווח נסגר, ובאזור החיתוך יש בסיסים שונים."""
    mid = x0 + PANEL_W / 2
    bx = mid
    marks = line(bx, y, bx, y + GAP, INK, 9)
    return ladder(x0, x0 + PANEL_W, y) + marks + callout(bx, y - 4, mid - 70, y - 70, "מוטציה")


def template_strand(mid, y):
    """תבנית התיקון: גדיל קצר עם בסיסים פונים מטה."""
    out = line(mid - CUT + 8, y, mid + CUT - 8, y, INSERT, 7)
    x = mid - CUT + 16
    while x < mid + CUT - 8:
        out += line(x, y, x, y + 18, INSERT, 3)
        x += STEP
    return out


def cut_with_template(x0, y):
    """שיטה 2: לאחר החיתוך תבנית תיקון נמצאת מעל הרווח."""
    mid = x0 + PANEL_W / 2
    ty = y - 62
    return (cut_dna(x0, y) + template_strand(mid, ty)
            + callout(mid - CUT + 6, ty - 3, mid - 110, ty - 50, "תבנית תיקון"))


def repaired(x0, y):
    """שיטה 2: המקטע מתבנית התיקון שולב במולקולה."""
    mid = x0 + PANEL_W / 2
    return (ladder(x0, mid - CUT, y) + ladder(mid + CUT, x0 + PANEL_W, y)
            + line(mid - CUT, y, mid + CUT, y, INSERT, 7) + line(mid - CUT, y + GAP, mid + CUT, y + GAP, INSERT, 7)
            + "".join(line(mid - CUT + 10 + i * STEP, y, mid - CUT + 10 + i * STEP, y + GAP, INSERT, 3) for i in range(7)))


ROWS = [
    ("שיטה 1", (cas9_on_dna, cut_with_nucleotides, mutated)),
    ("שיטה 2", (cas9_on_dna, cut_with_template, repaired)),
]


def row_svg(i, title, stages):
    top = i * ROW_H
    y = top + DNA_Y
    out = line(30, top, W - 30, top, GRID, 2) if i else ""
    out += text(W - 30, top + 36, title, size=38, anchor="start", weight=700)
    for x0, draw in zip(PANELS, stages):
        out += draw(x0, y)
    ay = y + GAP / 2
    for ax in (PANELS[0] - 18, PANELS[1] - 18):
        out += line(ax, ay, ax - 28, ay, INK, 5) + f'<path d="M{ax - 44} {ay} l20 -13 v26 z" fill="{INK}"/>'
    return out


def svg():
    h = ROW_H * len(ROWS)
    body = "".join(row_svg(i, *r) for i, r in enumerate(ROWS))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}">'
            f'<rect width="{W}" height="{h}" fill="#fff"/>{body}</svg>')


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": ROW_H * len(ROWS)}, device_scale_factor=2)
        page.set_content(f'<!DOCTYPE html><html><head><meta charset="utf-8"></head><body style="margin:0">{svg()}</body></html>')
        page.screenshot(path=str(OUT))
        browser.close()
    print(f"-> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
