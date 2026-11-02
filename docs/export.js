"use strict";
/* ייצוא המבחן לוורד (docx): טור א׳ לפי סדר הסל, טור ב׳ מערבב שאלות ואפשרויות.
   עטוף בפונקציה כדי לא להתנגש בשמות של app.js. */
(() => {

const D = window.docx;
const HEB_LETTERS = "אבגדהוזחטי";
const ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"];
const FIG_MAX_W = 600; // פיקסלים של docx (1/96 אינץ')
const FIG_MAX_H = 420;
const GRAY = "666666";
const FONT_SIZE = 24; // חצאי נקודה: 12pt
const LINE_15 = 360; // רווח שורות 1.5 (240 = שורה אחת)

const optLabel = (style, i) => (style === "upper-roman" ? ROMAN[i] : HEB_LETTERS[i]);

/* ---------- אבני בניין ---------- */

const HEBREW = /[֐-׿]/;
const LRM = "‎";
const RLM = "‏";

/** קטע בלי עברית (רצף DNA, מספר רומי) נעטף בסימני LRM כדי שהגרשים והנקודות לא יקפצו לצד הלא נכון */
function run(text, o = {}) {
  const hebrew = HEBREW.test(text);
  const t = !hebrew && /[A-Za-z0-9]/.test(text) ? `${LRM}${text}${LRM}` : text;
  return new D.TextRun({ size: FONT_SIZE, font: "Arial", text: t, rightToLeft: hebrew, bold: o.bold, italics: o.italics, color: o.color });
}

function para(children, o = {}) {
  return new D.Paragraph({
    bidirectional: true,
    children: [new D.TextRun({ size: FONT_SIZE, font: "Arial", text: RLM, rightToLeft: true }), ...[].concat(children).filter(Boolean)],
    alignment: o.center ? D.AlignmentType.CENTER : undefined,
    spacing: { before: o.before ?? 0, after: o.after ?? 80, line: LINE_15 },
    keepNext: o.keepNext,
    border: o.border,
  });
}

/** טקסט עם ירידות שורה → פסקה לכל שורה; prefix (למשל אות הסעיף) נכנס לשורה הראשונה */
function lines(text, o = {}, prefix = null) {
  return String(text ?? "").split("\n").map((line, i) =>
    para([i === 0 ? prefix : null, run(line, o)], o));
}

async function figure(q, f) {
  const buf = await (await fetch(`figures/${q.exam}/${f}`)).arrayBuffer();
  const bmp = await createImageBitmap(new Blob([buf]));
  const k = Math.min(1, FIG_MAX_W / bmp.width, FIG_MAX_H / bmp.height);
  return para(new D.ImageRun({
    type: "png", data: buf,
    altText: { name: f, title: f, description: BANK.exams[q.exam].figure_alt?.[f] || "איור לשאלה" },
    transformation: { width: Math.round(bmp.width * k), height: Math.round(bmp.height * k) },
  }), { center: true, after: 120 });
}

const figures = (q, list) => Promise.all((list || []).map((f) => figure(q, f)));

function table(t) {
  const n = t.headers.length;
  const cell = (text, head) => new D.TableCell({
    children: lines(text, { bold: head, after: 0 }),
    shading: head ? { fill: "EEEEEE", type: D.ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 40, bottom: 40, left: 100, right: 100 },
  });
  return [
    new D.Table({
      visuallyRightToLeft: true,
      width: { size: 9000, type: D.WidthType.DXA },
      columnWidths: Array(n).fill(Math.floor(9000 / n)),
      rows: [
        new D.TableRow({ tableHeader: true, children: t.headers.map((h) => cell(h, true)) }),
        ...t.rows.map((r) => new D.TableRow({ children: r.map((c) => cell(c, false)) })),
      ],
    }),
    para(run(""), { after: 60 }),
  ];
}

/** אפשרויות לשאלה אמריקאית; perm = סדר ההצגה (בטור ב׳ – מעורבב) */
function optionParas(opts, style, perm) {
  // RLM אחרי התווית מפריד בין "I." לבין מילה לועזית שאחריה, כך שהתווית נשארת בצד ימין
  const sep = () => new D.TextRun({ size: FONT_SIZE, font: "Arial", text: `${RLM}  `, rightToLeft: true });
  return perm.flatMap((src, i) => opts[src].split("\n").map((line, j) =>
    para([j === 0 ? run(`${optLabel(style, i)}.`) : run("      "), sep(), run(line)], { after: 40 })));
}

/** רשימה נפתחת → מחסן היגדים במסגרת, כדי שהתלמיד יידע מתוך מה לבחור */
function bank(inter) {
  if (!inter) return [];
  if (inter.kind === "true_false") return [para(run("לכל היגד כתבו: נכון / לא נכון", { bold: true }))];
  if (!inter.options) return [];
  const bullet = (o) => para([run("•"), new D.TextRun({ size: FONT_SIZE, font: "Arial", text: `${RLM}  `, rightToLeft: true }), run(o)], { after: 0 });
  const cell = new D.TableCell({
    children: [para(run("מחסן היגדים – בחרו מתוך:", { bold: true }), { after: 40 }), ...inter.options.map(bullet)],
    margins: { top: 80, bottom: 80, left: 160, right: 160 },
  });
  return [
    new D.Table({
      visuallyRightToLeft: true,
      width: { size: 9000, type: D.WidthType.DXA },
      columnWidths: [9000],
      rows: [new D.TableRow({ children: [cell] })],
    }),
    para(run(""), { after: 60 }),
  ];
}

const box = { style: D.BorderStyle.SINGLE, color: "999999", space: 4 };

/* ---------- שאלה ---------- */

async function questionBlocks(entry, n, perms) {
  const q = QS.get(entry.id);
  const style = BANK.exams[q.exam].option_style || "hebrew";
  const pts = effectivePoints(entry);
  const out = [para([
    run(`שאלה ${n}`, { bold: true }),
    pts != null ? run(` (${pts} נקודות)`, { bold: true }) : null,
    state.showSource ? run(`   ${srcRef(q)}`, { color: GRAY }) : null,
  ], { before: 320, after: 120, keepNext: true })];

  if (q.passage) {
    const ps = q.passage;
    out.push(para(run(ps.title, { bold: true }), { center: true, after: 100 }));
    if (ps.intro) out.push(...lines(ps.intro, { italics: true }));
    out.push(...lines(ps.text, { after: 100 }));
    out.push(...await figures(q, ps.figures));
    if (ps.text_after) out.push(...lines(ps.text_after, { after: 100 }));
    if (ps.credit) out.push(...lines(ps.credit, { color: GRAY }));
  }
  if (q.stem) out.push(...lines(q.stem));
  out.push(...await figures(q, q.stem_figures));

  if (q.type === "mc") {
    out.push(...await figures(q, q.figures));
    out.push(...optionParas(q.options, style, perms[`${q.id}|`] || q.options.map((_, i) => i)));
  } else if (q.items) {
    for (const p of q.items.filter((it) => entry.items.includes(it.label))) {
      out.push(para(run(""), { after: 0 }));
      for (const [i, part] of itemOrder(p).entries()) {
        const label = i === 0 ? run(`${p.label}.  `, { bold: true }) : null;
        if (part === "intro") out.push(...lines(p.intro, {}, label));
        if (part === "figures") out.push(...await figures(q, p.figures));
        if (part === "table") out.push(...table(p.table));
        if (part === "text") out.push(...lines(p.text, {}, label));
      }
      if (p.options) {
        out.push(...optionParas(p.options, style, perms[`${q.id}|${p.label}`] || p.options.map((_, i) => i)));
      }
      out.push(...bank(p.interactive));
    }
  }
  if (isOnline(q)) {
    out.push(para(run("שאלה זו דורשת עבודה בכלים מקוונים (Entrez / BLAST) – יש לפתור אותה מול מחשב.",
      { italics: true }), { border: { top: box, bottom: box, left: box, right: box }, before: 120 }));
  }
  return out;
}

/* ---------- מסמך ---------- */

function headerBlocks(version) {
  const h = state.header;
  const out = [];
  if (h.school) out.push(para(run(h.school, { bold: true }), { center: true }));
  if (h.exam) out.push(para(run(h.exam, { bold: true }), { center: true }));
  if (version === "B") out.push(para(run("טור ב׳", { bold: true }), { center: true }));
  const info = [["כיתה", h.cls], ["תאריך", h.date], ["משך", h.duration]]
    .filter(([, v]) => v).map(([k, v]) => `${k}: ${v}`).join("        ");
  if (info) out.push(para(run(info), { center: true }));
  if (h.instructions) {
    out.push(para(run("הוראות:", { bold: true }), { before: 160, after: 40 }));
    out.push(...lines(h.instructions));
  }
  if (out.length) {
    out.push(para(run(""), { border: { bottom: { style: D.BorderStyle.SINGLE, color: "999999", space: 1 } } }));
  }
  return out;
}

async function buildDoc(version, entries, perms) {
  const children = headerBlocks(version);
  for (const [i, entry] of entries.entries()) children.push(...await questionBlocks(entry, i + 1, perms));
  return new D.Document({
    styles: { default: { document: { run: { font: "Arial" } } } },
    sections: [{
      properties: { page: { size: { width: 11906, height: 16838 },
        margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
      footers: { default: new D.Footer({ children: [new D.Paragraph({
        alignment: D.AlignmentType.CENTER, children: [new D.TextRun({ size: FONT_SIZE, font: "Arial", children: [D.PageNumber.CURRENT] })] })] }) },
      children,
    }],
  });
}

/* ---------- טור ב׳ ---------- */

function shuffled(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

/** ערבוב ששונה מהסדר המקורי (כשיש יותר מפריט אחד) */
function shuffleDifferent(arr) {
  if (arr.length < 2) return [...arr];
  let a;
  do { a = shuffled(arr); } while (a.every((x, i) => x === arr[i]));
  return a;
}

/** סדר מעורבב לכל קבוצת אפשרויות במבחן: מפתח "שאלה|סעיף" → אינדקסים מקוריים לפי סדר ההצגה */
function optionPerms(entries) {
  const perms = {};
  for (const entry of entries) {
    const q = QS.get(entry.id);
    if (q.type === "mc") perms[`${q.id}|`] = shuffleDifferent(q.options.map((_, i) => i));
    for (const p of (q.items || []).filter((it) => it.options && entry.items.includes(it.label))) {
      perms[`${q.id}|${p.label}`] = shuffleDifferent(p.options.map((_, i) => i));
    }
  }
  return perms;
}

/** טבלת המרה למורה (מוצגת בסל, לא נכנסת לקובץ): מיקום כל שאלה וכל אפשרות בטור ב׳ */
function renderConversion(entriesB, perms) {
  const rows = state.cart.map((entry, i) => {
    const q = QS.get(entry.id);
    const style = BANK.exams[q.exam].option_style || "hebrew";
    const opts = Object.entries(perms).filter(([k]) => k.startsWith(`${q.id}|`)).map(([k, perm]) => {
      const part = k.split("|")[1];
      const map = perm.map((src, to) => [src, to]).sort((a, b) => a[0] - b[0])
        .map(([src, to]) => `${optLabel(style, src)}→${optLabel(style, to)}`).join(", ");
      return `${part ? `סעיף ${part}: ` : ""}${map}`;
    });
    return `<tr><td>${i + 1}</td><td>${entriesB.indexOf(entry) + 1}</td><td>${opts.map(esc).join("<br>") || "—"}</td></tr>`;
  }).join("");
  document.getElementById("convert").innerHTML = `<b>טבלת המרה לטור ב׳</b> (למורה – לא נכנסת לקובץ)
    <table><tr><th>טור א׳</th><th>טור ב׳</th><th>אפשרויות (א׳→ב׳)</th></tr>${rows}</table>`;
}

/* ---------- הורדה ---------- */

function fileName(version) {
  const base = (state.header.exam || "מבחן").replace(/[\\/:*?"<>|]/g, " ").trim();
  return `${base}${version === "B" ? " - טור ב" : ""}.docx`;
}

/** בונה את הקובץ ומחזיר Blob (גם לבדיקות) */
async function examBlob(version) {
  let entries = state.cart;
  let perms = {};
  if (version === "B") {
    entries = shuffleDifferent(state.cart);
    perms = optionPerms(entries);
    renderConversion(entries, perms);
  }
  return D.Packer.toBlob(await buildDoc(version, entries, perms));
}

async function download(version) {
  const status = document.getElementById("export-status");
  status.textContent = "מכין את הקובץ…";
  try {
    const blob = await examBlob(version);
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = fileName(version);
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 10000);
    status.textContent = `הקובץ "${a.download}" ירד.`;
  } catch (e) {
    console.error(e);
    status.textContent = `שגיאה בייצוא: ${e.message}`;
  }
}

document.getElementById("export-a").addEventListener("click", () => download("A"));
document.getElementById("export-b").addEventListener("click", () => download("B"));
window.examBlob = examBlob;

})();
