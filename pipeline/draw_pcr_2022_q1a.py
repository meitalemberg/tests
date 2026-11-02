"""איור מקורי לשאלה 2022-Q1 סעיף א: שלושת שלבי ה-PCR, במקום הסרטונים שבבחינה המקוונת.

בכל שורה: מצב ההתחלה מימין, חץ, והמצב בסוף השלב משמאל. אין באיור שמות שלבים או טמפרטורות –
אלה התשובה לסעיף.

שימוש:
    .venv/bin/python -I pipeline/draw_pcr_2022_q1a.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import ROOT  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

OUT = ROOT / "data/exams/2022/figures/2022-q1a-illustration.png"

W, ROW_H = 1200, 250
INK, PRIMER, GRID = "#111", "#c8102e", "#d8d8d8"
STRAND_W = 440  # אורך גדיל
N = 16          # מספר בסיסים בגדיל
GAP = 46        # מרחק בין גדילים מזווגים
STEP = STRAND_W / (N - 1)
PRIMER_N = 5    # מספר הבסיסים בתחל


def line(x1, y1, x2, y2, color=INK, w=3):
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>'


def label(x, y, text):
    return f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="27" fill="{INK}">{text}</text>'


def ends(x1, x2, y, left, right, above):
    """תוויות 5'/3' בקצות הגדיל – מעליו או מתחתיו."""
    ty = y - 14 if above else y + 34
    return label(x1, ty, left) + label(x2, ty, right)


def strand(x1, x2, y, color=INK):
    return line(x1, y, x2, y, color, 6)


def ticks(x0, first, count, y, length):
    """קווים קצרים המייצגים בסיסים; length שלילי פונה כלפי מעלה."""
    return "".join(line(x0 + i * STEP, y, x0 + i * STEP, y + length) for i in range(first, first + count))


def template(x0, y):
    """הגדיל המשמש תבנית, עם בסיסים פונים כלפי מטה."""
    return strand(x0, x0 + STRAND_W, y) + ticks(x0, 0, N, y, 18) + ends(x0, x0 + STRAND_W, y, "5′", "3′", True)


def primer_x(x0):
    return x0 + (N - PRIMER_N) * STEP


def nucleotide(x, y, angle):
    return (f'<g transform="translate({x:.1f} {y:.1f}) rotate({angle})">'
            + line(-11, 0, 11, 0, INK, 6) + line(-11, 0, -11, -16) + "</g>")


def duplex(x0, y):
    """מולקולה דו-גדילית שלמה."""
    return (strand(x0, x0 + STRAND_W, y) + strand(x0, x0 + STRAND_W, y + GAP)
            + ticks(x0, 0, N, y, GAP)
            + ends(x0, x0 + STRAND_W, y, "5′", "3′", True)
            + ends(x0, x0 + STRAND_W, y + GAP, "3′", "5′", False))


def separated(x0, y):
    """שני גדילים נפרדים."""
    top, bottom = y - 34, y + GAP + 34
    return (strand(x0, x0 + STRAND_W, top) + ticks(x0, 0, N, top, 18)
            + ends(x0, x0 + STRAND_W, top, "5′", "3′", True)
            + strand(x0, x0 + STRAND_W, bottom) + ticks(x0, 0, N, bottom, -18)
            + ends(x0, x0 + STRAND_W, bottom, "3′", "5′", False))


def primer_apart(x0, y):
    """תבנית ותחל שעדיין אינו קשור אליה."""
    px, py = primer_x(x0), y + GAP + 44
    return (template(x0, y) + strand(px, x0 + STRAND_W, py, PRIMER) + ticks(px, 0, PRIMER_N, py, -18)
            + ends(px, x0 + STRAND_W, py, "3′", "5′", False))


def primer_bound(x0, y):
    """תחל קשור לקצה 3′ של התבנית."""
    px = primer_x(x0)
    return (template(x0, y) + ticks(px, 0, PRIMER_N, y, GAP) + strand(px, x0 + STRAND_W, y + GAP, PRIMER)
            + ends(px, x0 + STRAND_W, y + GAP, "3′", "5′", False))


def primer_with_free(x0, y):
    """תחל קשור ונוקלאוטידים חופשיים בתמיסה."""
    spots = [(0.10, 72, 20), (0.27, 112, -25), (0.42, 66, 35), (0.57, 108, -10), (0.03, 128, -35), (0.34, 138, 15)]
    free = "".join(nucleotide(x0 + fx * STRAND_W, y + dy, a) for fx, dy, a in spots)
    return primer_bound(x0, y) + free


def extended(x0, y):
    """גדיל חדש שהתארך מהתחל לאורך התבנית."""
    px = primer_x(x0)
    start = x0 + 2 * STEP
    return (template(x0, y) + ticks(x0, 2, N - 2, y, GAP)
            + strand(start, px, y + GAP) + strand(px, x0 + STRAND_W, y + GAP, PRIMER)
            + ends(start, x0 + STRAND_W, y + GAP, "3′", "5′", False))


ROWS = [(duplex, separated), (primer_apart, primer_bound), (primer_with_free, extended)]


def row_svg(i, draw_start, draw_end):
    top = i * ROW_H
    y = top + 92
    out = ""
    if i:
        out += line(30, top, W - 30, top, GRID, 2)
    cx, cy = W - 44, top + ROW_H / 2
    out += f'<circle cx="{cx}" cy="{cy}" r="27" fill="none" stroke="{INK}" stroke-width="3"/>'
    out += label(cx, cy + 10, str(i + 1))
    out += draw_start(650, y) + draw_end(70, y)
    ax1, ax2, ay = 615, 540, top + ROW_H / 2
    out += line(ax1, ay, ax2 + 6, ay, INK, 5)
    out += f'<path d="M{ax2} {ay} l20 -13 v26 z" fill="{INK}"/>'
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
        page.set_content(f'<!DOCTYPE html><body style="margin:0">{svg()}</body>')
        page.screenshot(path=str(OUT))
        browser.close()
    print(f"-> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
