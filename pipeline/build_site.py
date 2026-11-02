"""אריזת המאגר לאתר: docs/data.js + העתקת האיורים ל-docs/figures/<בחינה>/.

שימוש:
    .venv/bin/python -I pipeline/build_site.py            (כל הבחינות ב-data/exams)
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import ROOT, TOPICS, exam_dirs, main_subtopic, parts, validate  # noqa: E402

SITE = ROOT / "docs"


def figures_of(q, passages):
    figs = list(q.get("figures", [])) + list(q.get("stem_figures", []))
    figs += passages.get(q.get("passage"), {}).get("figures", [])
    for p in q.get("items", []):
        figs += p.get("figures", [])
    return figs


def main(dirs):
    exams, questions = {}, []
    for d in dirs:
        data = json.loads((d / "questions.json").read_text(encoding="utf-8"))
        exam = data["exam"]
        exams[exam["id"]] = {k: exam.get(k) for k in
                             ("year", "title", "label", "notice", "questionnaire", "source", "source_url", "option_style", "figure_alt")}
        passages = {p["id"]: p for p in data["passages"]}
        fig_dir = SITE / "figures" / exam["id"]
        fig_dir.mkdir(parents=True, exist_ok=True)
        for q in data["questions"]:
            for problem in validate(q, d):
                print(f"  {q['id']}: {problem}")
            for f in figures_of(q, passages):
                shutil.copy2(d / "figures" / f, fig_dir / f)
            out = dict(q)
            out["exam"] = exam["id"]
            out["main"] = main_subtopic(q)
            out["subs"] = sorted({p["subtopic"] for p in parts(q) if p.get("subtopic")})
            out["all_tags"] = sorted({t for p in parts(q) for t in p.get("tags", [])})
            if q.get("passage"):
                out["passage"] = passages[q["passage"]]
            questions.append(out)
    questions.sort(key=lambda q: (-(exams[q["exam"]]["year"] or 0), q["number"]))
    bank = {"units": TOPICS["units"], "tags": TOPICS["tags"], "exams": exams, "questions": questions}
    (SITE / "data.js").write_text(
        "window.BANK = " + json.dumps(bank, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"-> docs/data.js: {len(questions)} שאלות מ-{len(exams)} בחינות")


if __name__ == "__main__":
    main(exam_dirs(sys.argv[1:]))
