"use strict";
/* ייצוא המבחן למודל (Moodle XML) ולגוגל פורמס (סקריפט Apps Script שיוצר טופס).
   משתמש בעזרים של app.js: QS, state, effectivePoints, itemOrder, srcRef, isOnline, esc, BANK. */
(() => {

const HEB_LETTERS = "אבגדהוזחטי";
const ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"];
const optLabel = (style, i) => (style === "upper-roman" ? ROMAN[i] : HEB_LETTERS[i]);
const ONLINE_NOTE = "שאלה זו דורשת עבודה בכלים מקוונים (Entrez / BLAST) – יש לפתור אותה מול מחשב.";
const MC_PLACEHOLDER = "⚠ למורה: סמנו את התשובה הנכונה (100%) ומחקו אפשרות זו";

/* ---------- מודל משותף: המבחן כרשימת שאלות וסעיפים ---------- */

/** חלוקת ניקוד לפי משקלות, בצעדים של step, כך שהסכום שווה בדיוק ל-total */
function allocate(weights, total, step) {
  const sum = weights.reduce((s, w) => s + w, 0);
  if (!weights.length) return [];
  if (!sum || total == null) return weights.map(() => (total == null ? 1 : 0));
  const units = Math.round(total / step);
  const raw = weights.map((w) => (w / sum) * units);
  const out = raw.map(Math.floor);
  let left = units - out.reduce((s, x) => s + x, 0);
  raw.map((r, i) => [r - Math.floor(r), i]).sort((a, b) => b[0] - a[0])
    .forEach(([, i]) => { if (left > 0) { out[i]++; left--; } });
  return out.map((u) => +(u * step).toFixed(2));
}

function wordBank(inter) {
  if (!inter) return "";
  if (inter.kind === "true_false") return "לכל היגד כתבו: נכון / לא נכון";
  if (!inter.options) return "";
  return "מחסן היגדים – בחרו מתוך:\n" + inter.options.map((o) => `• ${o}`).join("\n");
}

/** המבחן שבסל כמבנה אחד: לכל שאלה – הקשר משותף וסעיפים עם ניקוד */
function examModel(step) {
  return state.cart.map((entry, i) => {
    const q = QS.get(entry.id);
    const style = BANK.exams[q.exam].option_style || "hebrew";
    const total = effectivePoints(entry);
    let parts;
    if (q.items) {
      const items = q.items.filter((p) => entry.items.includes(p.label));
      const count = (l) => items.filter((p) => p.label[0] === l).length;
      const weights = items.map((p) => (q.part_points ? (q.part_points[p.label[0]] || 0) / count(p.label[0]) : 1));
      const pts = allocate(weights, total, step);
      parts = items.map((p, k) => ({
        label: p.label, order: itemOrder(p), intro: p.intro, figures: p.figures || [], table: p.table, text: p.text,
        options: p.options, bank: wordBank(p.interactive), points: pts[k],
      }));
    } else {
      // שאלה בלי סעיפים (אמריקאית / נכון–לא נכון / פתוחה קצרה): הגוף הוא טקסט השאלה
      parts = [{ label: "", order: ["text", "figures"], text: q.stem, figures: [...(q.figures || []), ...(q.stem_figures || [])],
        options: q.type === "mc" ? q.options : null, bank: "", points: allocate([1], total, step)[0] }];
    }
    return {
      n: i + 1, q, style, points: total, ref: srcRef(q), online: isOnline(q),
      passage: q.passage || null,
      stem: q.items ? q.stem : "", stemFigures: q.items ? (q.stem_figures || []) : [],
      parts,
    };
  });
}

const figUrl = (q, f) => new URL(`figures/${q.exam}/${f}`, location.href).href;
const figAlt = (q, f) => BANK.exams[q.exam].figure_alt?.[f] || "איור לשאלה";

function examTitle() {
  return (state.header.exam || "מבחן").trim();
}

function headerText() {
  const h = state.header;
  const info = [["כיתה", h.cls], ["תאריך", h.date], ["משך", h.duration]].filter(([, v]) => v).map(([k, v]) => `${k}: ${v}`);
  return [h.school, info.join("   "), h.instructions].filter(Boolean).join("\n");
}

function save(blob, name) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 10000);
}

const safeName = (s) => s.replace(/[\\/:*?"<>|]/g, " ").trim();

/* ---------- מודל (Moodle XML) ---------- */

const pad2 = (n) => String(n).padStart(2, "0");
const cdata = (s) => `<![CDATA[${String(s).replaceAll("]]>", "]]]]><![CDATA[>")}]]>`;
const xmlEsc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const htmlLines = (text, tag = "p") => String(text ?? "").split("\n").filter((l) => l.trim())
  .map((l) => `<${tag}>${esc(l)}</${tag}>`).join("");

function htmlTable(t) {
  const cell = (c, h) => `<${h} style="border:1px solid #999;padding:4px 8px;text-align:right${h === "th" ? ";background:#eee" : ""}">${esc(c).replaceAll("\n", "<br>")}</${h}>`;
  return `<table dir="rtl" style="border-collapse:collapse;margin:8px 0">`
    + `<tr>${t.headers.map((c) => cell(c, "th")).join("")}</tr>`
    + t.rows.map((r) => `<tr>${r.map((c) => cell(c, "td")).join("")}</tr>`).join("") + `</table>`;
}

async function base64Of(url) {
  const buf = new Uint8Array(await (await fetch(url)).arrayBuffer());
  let s = "";
  for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode(...buf.subarray(i, i + 0x8000));
  return btoa(s);
}

/** איור בתוך שאלת מודל: תגית img + קובץ מוטמע */
async function moodleFig(q, f, files) {
  const name = `${q.exam}-${f}`.replace(/[^\w.-]/g, "_");
  if (!files.has(name)) files.set(name, await base64Of(figUrl(q, f)));
  return `<p style="text-align:center"><img src="@@PLUGINFILE@@/${encodeURIComponent(name)}" alt="${esc(figAlt(q, f))}" style="max-width:100%"></p>`;
}

async function moodleQuestion(m, part, k) {
  const { q } = m;
  const files = new Map();
  let html = "";
  if (k === 0) {
    // ההקשר המשותף (קטע, פתיח, איורי פתיח) נכנס לסעיף הראשון שנבחר
    html += `<p><b>שאלה ${m.n}${m.points != null ? ` (${m.points} נקודות)` : ""}</b>${state.showSource ? ` <span style="color:#666">${esc(m.ref)}</span>` : ""}</p>`;
    if (m.passage) {
      const ps = m.passage;
      html += `<p style="text-align:center"><b>${esc(ps.title)}</b></p>` + htmlLines(ps.intro) + htmlLines(ps.text);
      for (const f of ps.figures || []) html += await moodleFig(q, f, files);
      html += htmlLines(ps.text_after) + (ps.credit ? `<p style="color:#666">${esc(ps.credit)}</p>` : "");
    }
    html += htmlLines(m.stem);
    for (const f of m.stemFigures) html += await moodleFig(q, f, files);
    if (m.online) html += `<p><i>${esc(ONLINE_NOTE)}</i></p>`;
    if (part.label) html += "<hr>";
  }
  for (const [i, piece] of part.order.entries()) {
    const label = i === 0 && part.label ? `<b>${esc(part.label)}.</b> ` : "";
    if (piece === "intro") html += htmlLines(part.intro).replace("<p>", `<p>${label}`);
    if (piece === "figures") for (const f of part.figures) html += await moodleFig(q, f, files);
    if (piece === "table") html += htmlTable(part.table);
    if (piece === "text") html += htmlLines(part.text).replace("<p>", `<p>${label}`);
  }
  if (part.bank) html += `<div style="border:1px solid #999;padding:6px 10px;margin-top:8px">${htmlLines(part.bank)}</div>`;

  const isMc = !!part.options;
  const name = `${pad2(m.n)}.${pad2(k + 1)} שאלה ${m.n}${part.label ? ` סעיף ${part.label}` : ""}`
    + ` – ${m.ref.replace(/[()]/g, "")}${isMc ? " – לסמן תשובה נכונה" : ""}`;
  const fileXml = [...files].map(([n, b64]) => `<file name="${xmlEsc(n)}" path="/" encoding="base64">${b64}</file>`).join("");
  const head = `<question type="${isMc ? "multichoice" : "essay"}">
<name><text>${xmlEsc(name)}</text></name>
<questiontext format="html"><text>${cdata(`<div dir="rtl" style="text-align:right">${html}</div>`)}</text>${fileXml}</questiontext>
<generalfeedback format="html"><text></text></generalfeedback>
<defaultgrade>${part.points}</defaultgrade><penalty>0</penalty><hidden>0</hidden><idnumber></idnumber>`;
  if (!isMc) {
    return `${head}
<responseformat>editor</responseformat><responserequired>1</responserequired><responsefieldlines>10</responsefieldlines>
<minwordlimit></minwordlimit><maxwordlimit></maxwordlimit>
<attachments>0</attachments><attachmentsrequired>0</attachmentsrequired><maxbytes>0</maxbytes><filetypeslist></filetypeslist>
<graderinfo format="html"><text></text></graderinfo><responsetemplate format="html"><text></text></responsetemplate>
</question>`;
  }
  // אין במאגר תשובות נכונות. מודל מחייב תשובה של 100%, לכן נוספת אפשרות-ממלאת-מקום בולטת שהמורה מוחקת
  const roman = m.style === "upper-roman";
  const answers = part.options.map((o, i) => [roman ? o : `${optLabel(m.style, i)}. ${o}`, 0]);
  answers.push([MC_PLACEHOLDER, 100]);
  return `${head}
<single>true</single><shuffleanswers>0</shuffleanswers><answernumbering>${roman ? "IIII" : "none"}</answernumbering>
<showstandardinstruction>0</showstandardinstruction>
<correctfeedback format="html"><text></text></correctfeedback>
<partiallycorrectfeedback format="html"><text></text></partiallycorrectfeedback>
<incorrectfeedback format="html"><text></text></incorrectfeedback>
${answers.map(([t, fr]) => `<answer fraction="${fr}" format="html"><text>${cdata(`<span dir="rtl">${esc(t).replaceAll("\n", "<br>")}</span>`)}</text><feedback format="html"><text></text></feedback></answer>`).join("\n")}
</question>`;
}

async function moodleXml() {
  const model = examModel(0.5);
  const out = [`<?xml version="1.0" encoding="UTF-8"?>\n<quiz>`,
    `<question type="category"><category><text>${xmlEsc(`$course$/top/${examTitle()}`)}</text></category><info format="html"><text></text></info></question>`];
  for (const m of model) {
    for (const [k, part] of m.parts.entries()) out.push(await moodleQuestion(m, part, k));
  }
  out.push("</quiz>\n");
  return { xml: out.join("\n"), mc: model.reduce((s, m) => s + m.parts.filter((p) => p.options).length, 0),
    count: model.reduce((s, m) => s + m.parts.length, 0) };
}

/* ---------- גוגל פורמס (Apps Script) ---------- */

/** טבלה כתמונת PNG (base64) – בטופס גוגל אין טבלאות */
function tablePng(t) {
  const S = 2, FONT = 15, PAD = 8, LH = 21, MAXW = 210;
  const c = document.createElement("canvas");
  const x = c.getContext("2d");
  const font = (b) => `${b ? "bold " : ""}${FONT}px Arial, sans-serif`;
  const wrap = (text, bold) => {
    x.font = font(bold);
    return String(text ?? "").split("\n").flatMap((seg) => {
      const words = seg.split(" ");
      const lines = [];
      let cur = "";
      for (const w of words) {
        const next = cur ? `${cur} ${w}` : w;
        if (cur && x.measureText(next).width > MAXW) { lines.push(cur); cur = w; } else cur = next;
      }
      return [...lines, cur];
    });
  };
  const rows = [t.headers, ...t.rows].map((r, ri) => r.map((cell) => wrap(cell, ri === 0)));
  const n = t.headers.length;
  const colW = [...Array(n)].map((_, j) => Math.max(40, ...rows.map((r, ri) => {
    x.font = font(ri === 0);
    return Math.max(...r[j].map((l) => x.measureText(l).width));
  })) + 2 * PAD);
  const rowH = rows.map((r) => Math.max(...r.map((ls) => ls.length)) * LH + 2 * PAD);
  const W = colW.reduce((s, w) => s + w, 0) + 2, H = rowH.reduce((s, h) => s + h, 0) + 2;
  c.width = W * S; c.height = H * S;
  x.scale(S, S);
  x.fillStyle = "#fff"; x.fillRect(0, 0, W, H);
  x.strokeStyle = "#888"; x.lineWidth = 1; x.direction = "rtl"; x.textAlign = "right"; x.textBaseline = "top";
  let y = 1;
  rows.forEach((r, ri) => {
    let right = W - 1;
    r.forEach((ls, j) => {
      if (ri === 0) { x.fillStyle = "#eee"; x.fillRect(right - colW[j], y, colW[j], rowH[ri]); }
      x.strokeRect(right - colW[j], y, colW[j], rowH[ri]);
      x.fillStyle = "#111"; x.font = font(ri === 0);
      ls.forEach((l, li) => x.fillText(l, right - PAD, y + PAD + li * LH + 2));
      right -= colW[j];
    });
    y += rowH[ri];
  });
  return c.toDataURL("image/png").split(",")[1];
}

/** רצף פריטים לטופס: text (כותרת+הסבר), image (url או base64), open, mc */
function formBlocks() {
  const blocks = [];
  for (const m of examModel(1)) {
    const { q } = m;
    const ctx = [];
    if (m.passage) {
      const ps = m.passage;
      ctx.push([ps.title, ps.intro, ps.text].filter(Boolean).join("\n"));
    }
    blocks.push({ t: "section", title: `שאלה ${m.n}${m.points != null ? ` (${m.points} נקודות)` : ""}`
      + (state.showSource ? ` ${m.ref}` : ""), help: [...ctx, m.stem, m.online ? ONLINE_NOTE : ""].filter(Boolean).join("\n\n") });
    if (m.passage) {
      for (const f of m.passage.figures || []) blocks.push({ t: "image", url: figUrl(q, f), alt: figAlt(q, f) });
      if (m.passage.text_after) blocks.push({ t: "text", title: "", help: m.passage.text_after });
    }
    for (const f of m.stemFigures) blocks.push({ t: "image", url: figUrl(q, f), alt: figAlt(q, f) });
    for (const part of m.parts) {
      const name = part.label ? `${part.label}. ` : "";
      for (const piece of part.order) {
        if (piece === "intro") blocks.push({ t: "text", title: `סעיף ${part.label}`, help: part.intro });
        if (piece === "figures") for (const f of part.figures) blocks.push({ t: "image", url: figUrl(q, f), alt: figAlt(q, f) });
        if (piece === "table") blocks.push({ t: "image", b64: tablePng(part.table), alt: "טבלה" });
      }
      const pts = part.points;
      if (part.options) {
        blocks.push({ t: "mc", title: name + part.text, help: part.bank, points: pts,
          choices: part.options.map((o, i) => (m.style === "upper-roman" ? `${ROMAN[i]}. ${o}` : `${optLabel(m.style, i)}. ${o}`)) });
      } else {
        blocks.push({ t: "open", title: name + part.text, help: part.bank, points: pts });
      }
    }
  }
  return blocks;
}

function formsScript() {
  const exam = { title: examTitle(), description: headerText(), blocks: formBlocks() };
  return `/**
 * יצירת טופס גוגל (בוחן) מהמבחן "${exam.title.replace(/\*\//g, "")}" – מאגר בגרות ביוטכנולוגיה.
 *
 * איך מפעילים:
 * 1. נכנסים ל-https://script.google.com ולוחצים "פרויקט חדש".
 * 2. מוחקים את מה שכתוב בעורך ומדביקים את כל תוכן הקובץ הזה.
 * 3. שומרים (Ctrl+S), בוחרים למעלה את הפונקציה createExam ולוחצים "הפעלה".
 * 4. בפעם הראשונה גוגל מבקש אישור גישה: בוחרים את החשבון → "מתקדם" → "מעבר אל..." → "אישור".
 * 5. בסיום מופיעים ב"יומן ביצוע" הקישורים לעריכת הטופס ולשליחה לתלמידים. הטופס נשמר גם ב-Drive.
 *
 * במאגר אין תשובות נכונות: בשאלות האמריקאיות יש לסמן "מפתח תשובות" בעריכת הטופס.
 * השאלות הפתוחות נבדקות ידנית בלשונית "תגובות".
 */
const EXAM = ${JSON.stringify(exam, null, 1)};

function createExam() {
  const form = FormApp.create(EXAM.title);
  form.setIsQuiz(true);
  form.setDescription(EXAM.description);
  form.addTextItem().setTitle("שם מלא").setRequired(true);
  for (const b of EXAM.blocks) {
    if (b.t === "section" || b.t === "text") {
      form.addSectionHeaderItem().setTitle(b.title || " ").setHelpText(b.help || "");
    } else if (b.t === "image") {
      const blob = b.url ? UrlFetchApp.fetch(b.url).getBlob()
        : Utilities.newBlob(Utilities.base64Decode(b.b64), "image/png", "table.png");
      form.addImageItem().setImage(blob).setTitle("").setHelpText(b.alt || "").setAlignment(FormApp.Alignment.CENTER);
    } else if (b.t === "open") {
      form.addParagraphTextItem().setTitle(b.title).setHelpText(b.help || "").setPoints(b.points);
    } else if (b.t === "mc") {
      const item = form.addMultipleChoiceItem();
      item.setTitle(b.title).setHelpText(b.help || "")
        .setChoices(b.choices.map((c) => item.createChoice(c, false))).setPoints(b.points);
    }
  }
  Logger.log("עריכת הטופס: " + form.getEditUrl());
  Logger.log("קישור לתלמידים: " + form.getPublishedUrl());
}
`;
}

/* ---------- הורדה + הוראות ---------- */

const HELP = {
  moodle: (r) => `<b>ייבוא למודל:</b> בקורס → בנק שאלות → <b>ייבוא</b> → פורמט <b>Moodle XML</b> → גוררים את הקובץ → ייבוא.
    השאלות (${r.count}) ייכנסו לקטגוריה בשם המבחן. בהוספה לבוחן ממיינים לפי <b>שם השאלה</b> כדי לשמור על הסדר.
    ${r.mc ? `<br>⚠ ב-${r.mc} שאלות אמריקאיות יש לסמן את התשובה הנכונה ולמחוק את האפשרות "למורה: סמנו את התשובה הנכונה" (בשם השאלה כתוב "לסמן תשובה נכונה").` : ""}`,
  forms: () => `<b>יצירת טופס גוגל:</b> ב-<a href="https://script.google.com" target="_blank" rel="noopener">script.google.com</a> → פרויקט חדש →
    מדביקים את תוכן הקובץ → שמירה → בוחרים <b>createExam</b> → הפעלה → מאשרים גישה. הקישורים לטופס יופיעו ביומן הביצוע.
    טבלאות מופיעות בטופס כתמונות. בשאלות אמריקאיות יש לסמן מפתח תשובות בעריכת הטופס.`,
};

async function run(kind) {
  const status = document.getElementById("export-status");
  const help = document.getElementById("export-help");
  status.textContent = "מכין את הקובץ…";
  help.hidden = true;
  try {
    const base = safeName(examTitle());
    if (kind === "moodle") {
      const r = await moodleXml();
      save(new Blob([r.xml], { type: "application/xml" }), `${base} - מודל.xml`);
      help.innerHTML = HELP.moodle(r);
    } else {
      save(new Blob([formsScript()], { type: "text/plain" }), `${base} - גוגל פורמס.gs.txt`);
      help.innerHTML = HELP.forms();
    }
    help.hidden = false;
    status.textContent = "הקובץ ירד.";
  } catch (e) {
    console.error(e);
    status.textContent = `שגיאה בייצוא: ${e.message}`;
  }
}

document.getElementById("export-moodle").addEventListener("click", () => run("moodle"));
document.getElementById("export-forms").addEventListener("click", () => run("forms"));
Object.assign(window, { moodleXml, formsScript, examModel });

})();
