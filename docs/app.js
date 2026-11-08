"use strict";

const BANK = window.BANK;
const QS = new Map(BANK.questions.map((q) => [q.id, q]));
const UNITS = new Map(BANK.units.map((u) => [u.id, u]));
const SUBS = new Map(BANK.units.flatMap((u) => u.subtopics.map((s) => [s.id, s])));
const TAGS = new Map(BANK.tags.map((t) => [t.id, t.name]));
const SHOWN_TAGS = ["intro", "old", "online"]; // תגית 'interactive' היא פנימית לעיבוד
const STORE_KEY = "bagrut-bank-v1";
const THEME_KEY = "bagrut-theme";

const state = {
  view: null, // null = לוח הנושאים; אחרת { unit, sub }
  cart: [], // [{id, items: [labels] | null, points: number | null}]
  showSource: true,
  hideOnline: false,
  header: {}, // שדות כותרת המבחן לייצוא: school, exam, cls, date, duration, instructions
  msg: {}, // הודעה זמנית לכל שאלה בסל
  query: "", // חיפוש חופשי
  type: "", // סינון לפי סוג שאלה: "" | open | mc | tf
  year: "", // סינון לפי שנת בחינה
};

/* ---------- עזרים ---------- */

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const parts = (q) => q.items || [q];
const TYPE_NAMES = { mc: "שאלה אמריקאית", tf: "נכון / לא נכון", open: "שאלה פתוחה" };
const TYPE_PLURAL = { mc: "אמריקאיות", tf: "נכון / לא נכון", open: "פתוחות" };
const subName = (id) => (id ? SUBS.get(id).name : "");
const isOnline = (q) => q.all_tags.includes("online");
const inCart = (id) => state.cart.some((c) => c.id === id);
/** בחינת בגרות מזוהה בשנה; מקור אחר (למשל שאלות הפיקוח) – בשם משלו */
const examLabel = (exam) => exam.label || `בגרות ${exam.year}`;
const srcRef = (q) => `(${examLabel(BANK.exams[q.exam])}, שאלה ${q.number})`;
const YEARS = [...new Set(BANK.questions.map((q) => BANK.exams[q.exam].year))].filter(Boolean).sort((a, b) => b - a);
const OTHER_SOURCES = Object.entries(BANK.exams).filter(([, e]) => !e.year);

/** "חיתוך DNA – אנזימי הגבלה, ..." → כותרת + פירוט */
function splitName(name) {
  const i = name.indexOf(" – ");
  return i < 0 ? [name, ""] : [name.slice(0, i), name.slice(i + 3)];
}

/** שם קצר לתת-נושא (בלי הפירוט) – אלא אם הכותרת לבדה חוזרת ביחידה (למשל "תאי צמחים") */
const SHORT = new Map(BANK.units.flatMap((u) => {
  const titles = u.subtopics.map((s) => splitName(s.name)[0]);
  return u.subtopics.map((s, i) => [s.id, titles.filter((t) => t === titles[i]).length > 1 ? s.name : titles[i]]);
}));
const shortName = (id) => (id ? SHORT.get(id) : "");

function load() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORE_KEY) || "null");
    if (saved) {
      state.cart = (saved.cart || []).filter((c) => QS.has(c.id));
      state.showSource = saved.showSource ?? true;
      state.hideOnline = saved.hideOnline ?? false;
      state.header = saved.header || {};
    }
  } catch (e) { /* אחסון חסום – ממשיכים בלי */ }
}

function save() {
  try {
    localStorage.setItem(STORE_KEY, JSON.stringify({
      cart: state.cart, showSource: state.showSource, hideOnline: state.hideOnline, header: state.header,
    }));
  } catch (e) { /* אחסון חסום – ממשיכים בלי */ }
}

/* ---------- חיפוש וסינון ---------- */

/** השוואה סלחנית: בלי ניקוד, מקפים אחידים, אותיות קטנות */
const norm = (s) => String(s ?? "").toLowerCase().replace(/[֑-ׇ]/g, "").replace(/[–—‑־]/g, "-");

const SEARCH_TEXT = new Map(BANK.questions.map((q) => {
  const bits = [q.stem, ...(q.options || []), subName(q.main), UNITS.get(q.unit).name, srcRef(q)];
  if (q.passage) bits.push(q.passage.title, q.passage.intro, q.passage.text, q.passage.text_after);
  for (const p of q.items || []) {
    bits.push(p.intro, p.text, ...(p.options || []), ...((p.interactive || {}).options || []));
    if (p.table) bits.push(...p.table.headers, ...p.table.rows.flat());
  }
  return [q.id, norm(bits.filter(Boolean).join("\n"))];
}));

const terms = () => norm(state.query).split(/\s+/).filter(Boolean);
const filtersOn = () => Boolean(state.type || state.year);

/** בסיס: מה שמוסתר תמיד (כלים מקוונים לפי בחירה) */
const baseVisible = (q) => !(state.hideOnline && isOnline(q));

function visible(q) {
  if (!baseVisible(q)) return false;
  if (state.type && q.type !== state.type) return false;
  if (state.year && String(BANK.exams[q.exam].year ?? q.exam) !== state.year) return false;
  const t = terms();
  if (t.length) {
    const text = SEARCH_TEXT.get(q.id);
    if (!t.every((w) => text.includes(w))) return false;
  }
  return true;
}

let HL = null; // ביטוי להדגשת מילות החיפוש, מתעדכן בכל ציור

/** esc + הדגשת מילות החיפוש */
function hl(s) {
  const e = esc(s);
  return HL ? e.replace(HL, "<mark>$&</mark>") : e;
}

function updateHighlighter() {
  const t = state.query.trim().split(/\s+/).filter(Boolean).map((w) => esc(w).replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  HL = t.length ? new RegExp(t.join("|"), "gi") : null;
}

/* ---------- ניווט: הכתובת קובעת את התצוגה (#GE, #GE.3, ריק = לוח הנושאים) ---------- */

const SUB_UNIT = new Map(BANK.units.flatMap((u) => u.subtopics.map((s) => [s.id, u.id])));

function viewFromHash() {
  const key = decodeURIComponent(location.hash.slice(1));
  if (SUB_UNIT.has(key)) return { unit: SUB_UNIT.get(key), sub: key };
  if (UNITS.has(key)) return { unit: key, sub: null };
  return null;
}

const viewHash = (v) => (v ? `#${v.sub || v.unit}` : "#");

const unitQuestions = (unitId, pred = visible) => BANK.questions.filter((q) => q.unit === unitId && pred(q));

/* ---------- לוח נושאים (דף הבית) ---------- */

const HELIX = `<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
  <path d="M9 3c0 7 14 7 14 13S9 22 9 29"/><path d="M23 3c0 7-14 7-14 13s14 6 14 13"/>
  <path d="M11.5 8h9M11.5 24h9M13 12.5h6M13 19.5h6" stroke-width="1.8"/></svg>`;


function renderDashboard() {
  const qs = BANK.questions.filter(baseVisible);
  const years = [...new Set(qs.map((q) => BANK.exams[q.exam].year))].filter(Boolean).sort();
  $("results-head").hidden = true;
  let n = 0;
  const cards = BANK.units.map((u) => {
    const unitQs = unitQuestions(u.id, baseVisible);
    const rows = u.subtopics.map((s) => {
      const count = unitQs.filter((q) => q.main === s.id).length;
      const [title, detail] = splitName(s.name);
      return `<li><a class="srow${count ? "" : " empty"}" href="#${s.id}">
        <span class="stext"><span class="stitle">${esc(title)}</span>${detail ? `<span class="sdetail">${esc(detail)}</span>` : ""}</span>
        <span class="pill">${count}</span></a></li>`;
    }).join("");
    return `<section class="ucard u-${u.id}${u.folder ? " folder" : ""}">
      <a class="ucard-head" href="#${u.id}">
        <span class="unum">${u.folder ? "🗂" : ++n}</span>
        <span class="uname">${esc(u.name)}</span>
        <span class="ucount">${unitQs.length}</span>
      </a>
      ${u.folder ? `<p class="unote">נושאים שאינם בתוכנית הנוכחית</p>` : ""}
      <ul class="slist">${rows}</ul>
    </section>`;
  }).join("");
  $("results").innerHTML = `
    <section class="hero">
      <h1>מאגר שאלות בגרות בביוטכנולוגיה</h1>
      <p>שאלות מבחינות הבגרות במערכות ביוטכנולוגיות ושאלות שנכתבו על ידי הפיקוח, ממוינות לפי נושאי הלימוד. בוחרים שאלות, מתאימים סעיפים וניקוד – ומקבלים מבחן מוכן בוורד.</p>
      <div class="stats">
        <div class="stat"><b>${qs.length}</b><span>שאלות</span></div>
        <div class="stat"><b>${years.length}</b><span>בחינות בגרות</span></div>
        <div class="stat"><b>${years[0]}–${years[years.length - 1]}</b><span>שנים</span></div>
      </div>
      <span class="helix" aria-hidden="true">${HELIX}</span>
    </section>
    <ol class="steps">
      <li><div><b>בוחרים נושא</b><span>יחידה ותת-נושא, או חיפוש חופשי בכל השאלות</span></div></li>
      <li><div><b>מוסיפים שאלות למבחן</b><span>בוחרים סעיפים, מעדכנים ניקוד ומסדרים</span></div></li>
      <li><div><b>מייצאים לוורד</b><span>קובץ מוכן להדפסה, וגם טור ב׳ בסדר מעורבב</span></div></li>
    </ol>
    <h2 class="section-title">נושאי הלימוד</h2>
    <div class="dash-grid">${cards}</div>`;
}

/* ---------- עץ נושאים (בצד, בתצוגת שאלות) ---------- */

function renderTopics() {
  const html = BANK.units.map((u) => {
    const unitQs = unitQuestions(u.id);
    const v = state.view;
    const open = v && v.unit === u.id;
    const unitActive = open && !v.sub && !state.query;
    const subs = u.subtopics.map((s) => {
      const n = unitQs.filter((q) => q.main === s.id).length;
      const active = v && v.sub === s.id && !state.query;
      return `<button type="button" class="topic-btn sub-btn${active ? " active" : ""}${n ? "" : " empty"}"
        data-unit="${u.id}" data-sub="${s.id}" ${active ? 'aria-current="page"' : ""}>
        <span class="label">${esc(shortName(s.id))}</span><span class="n">${n}</span></button>`;
    }).join("");
    return `<div class="unit u-${u.id}${u.folder ? " folder" : ""}${open ? " open" : ""}">
      <button type="button" class="topic-btn unit-btn${unitActive ? " active" : ""}" data-unit="${u.id}" aria-expanded="${open}">
        <span class="dot"></span><span class="label">${esc(u.name)}</span><span class="n">${unitQs.length}</span>
        <span class="chev" aria-hidden="true">▾</span></button>
      <div class="subs">${subs}</div></div>`;
  }).join("");
  $("topics").innerHTML = html;
}

/* ---------- כרטיס שאלה ---------- */

function figs(q, list) {
  const alts = BANK.exams[q.exam].figure_alt || {};
  return (list || []).map((f) => `<img class="fig" src="figures/${q.exam}/${esc(f)}" alt="${esc(alts[f] || "איור לשאלה")} – לחצו להגדלה" loading="lazy">`).join("");
}

function table(t) {
  if (!t) return "";
  const head = `<tr>${t.headers.map((h) => `<th>${hl(h)}</th>`).join("")}</tr>`;
  const rows = t.rows.map((r) => `<tr>${r.map((c) => `<td>${hl(c)}</td>`).join("")}</tr>`).join("");
  return `<div class="tablewrap"><table class="qt">${head}${rows}</table></div>`;
}

function options(q, opts) {
  if (!opts) return "";
  const style = BANK.exams[q.exam].option_style || "hebrew";
  return `<ol class="opts ${style}">${opts.map((o) => `<li><bdi>${hl(o)}</bdi></li>`).join("")}</ol>`;
}

function bank(inter) {
  if (!inter) return "";
  if (inter.kind === "true_false") return `<div class="bank">לכל היגד: <b>נכון / לא נכון</b></div>`;
  if (!inter.options) {
    return `<div class="notice warn">בבחינה המקוונת זו רשימה נפתחת – רשימת האפשרויות עוד לא הוזנה למאגר.</div>`;
  }
  return `<div class="wordbank"><b>מחסן היגדים – בחרו מתוך:</b>
    <ul>${inter.options.map((o) => `<li><bdi>${hl(o)}</bdi></li>`).join("")}</ul></div>`;
}

function tagChips(tags) {
  return tags.filter((t) => SHOWN_TAGS.includes(t))
    .map((t) => `<span class="chip tag-${t}">${esc(TAGS.get(t))}</span>`).join("");
}

/** סדר החלקים בסעיף כמו במקור: בלי מבוא, או כשהטקסט מציג את הטבלה – הטקסט קודם לטבלה */
function itemOrder(p) {
  if (!p.intro) return ["text", "figures", "table"].filter((k) => k === "text" || p[k]);
  const order = p.table_after_text ? ["intro", "figures", "text", "table"] : ["intro", "figures", "table", "text"];
  return order.filter((k) => k === "text" || p[k]);
}

/** סעיף שהמדיה המקוונת שלו הוחלפה באיור מקורי – הערה למורה, עם קישור למקור */
function adaptedNote(q, p) {
  if (!p.adapted_note) return "";
  const url = BANK.exams[q.exam].source_url;
  const link = url ? ` <a href="${esc(url)}" target="_blank" rel="noopener">לשאלה בבחינה המקורית ב-testbox</a>.` : "";
  return `<div class="notice info"><span>${esc(p.adapted_note)}${link}</span></div>`;
}

function itemHtml(q, p) {
  const showSub = p.subtopic && p.subtopic !== q.main;
  const meta = (showSub ? `<span class="sub">${esc(shortName(p.subtopic))}</span>` : "") + tagChips(p.tags || []);
  return `<div class="item">
    <span class="item-label${p.label.length > 1 ? " long" : ""}" aria-label="סעיף ${esc(p.label)}">${esc(p.label)}</span>
    <div>
      ${meta ? `<div class="item-meta">${meta}</div>` : ""}
      ${itemOrder(p).map((part) => ({
        intro: () => `<p class="intro">${hl(p.intro)}</p>`,
        figures: () => figs(q, p.figures),
        table: () => table(p.table),
        text: () => `<p class="text">${hl(p.text)}</p>`,
      })[part]()).join("")}
      ${options(q, p.options)}
      ${bank(p.interactive)}
      ${adaptedNote(q, p)}
    </div>
  </div>`;
}

function passageHtml(q) {
  const ps = q.passage;
  return `<div class="passage">
    <div class="pkicker">קטע לקריאה</div>
    <h3>${hl(ps.title)}</h3>
    ${ps.intro ? `<p class="intro">${hl(ps.intro)}</p>` : ""}
    <p class="ptext">${hl(ps.text)}</p>
    ${figs(q, ps.figures)}
    ${ps.text_after ? `<p class="ptext">${hl(ps.text_after)}</p>` : ""}
    ${adaptedNote(q, ps)}
    ${ps.credit ? `<p class="credit">${esc(ps.credit)}</p>` : ""}
  </div>`;
}

function addLabel(added) {
  return added
    ? `<span class="when-added">✓ במבחן</span><span class="when-hover">✕ הסרה</span>`
    : `+ הוספה למבחן`;
}

function questionCard(q) {
  const exam = BANK.exams[q.exam];
  const unit = UNITS.get(q.unit);
  const added = inCart(q.id);
  let body = "";
  if (q.passage) body += passageHtml(q);
  if (q.stem) body += `<p class="stem">${hl(q.stem)}</p>`;
  body += figs(q, q.stem_figures);
  if (q.type === "mc") {
    body += figs(q, q.figures) + options(q, q.options);
  } else if (q.items) {
    body += q.items.map((p) => itemHtml(q, p)).join("");
  }
  if (exam.notice) body += `<div class="notice info"><span>${esc(exam.notice)}</span></div>`;
  if (isOnline(q)) {
    const link = exam.source_url
      ? ` <a href="${esc(exam.source_url)}" target="_blank" rel="noopener">לשאלה בבחינה המקורית ב-testbox</a>.` : "";
    body += `<div class="notice info"><span>שאלה זו דורשת עבודה בכלים מקוונים (Entrez / BLAST).${link}
      לבניית מבחן עם כלים דיגיטליים – השתמשו ב-MyTestBox.
      תוצאות החיפוש במאגרים מתעדכנות עם הזמן, לכן מומלץ להריץ את החיפוש מחדש לפני המבחן ולבדוק את התשובה הצפויה.</span></div>`;
  }
  return `<article class="qcard u-${q.unit}${added ? " in-cart" : ""}" id="card-${q.id}">
    <div class="qhead">
      <div>
        <div class="qpath"><b>${esc(unit.name)}</b>${q.main ? ` › ${esc(shortName(q.main))}` : ""}</div>
        <div class="chips">
          <span class="chip">${TYPE_NAMES[q.type]}</span>
          ${q.points != null ? `<span class="chip pts">${q.points} נק'</span>` : ""}
          <span class="chip src srcref">${esc(examLabel(exam))} · שאלה ${q.number}</span>
          ${tagChips(q.all_tags)}
        </div>
      </div>
      <button type="button" class="add-btn${added ? " added" : ""}" data-add="${q.id}" aria-pressed="${added}">${addLabel(added)}</button>
    </div>
    ${body}
  </article>`;
}

/* ---------- תוצאות ---------- */

function filterSummary() {
  const bits = [];
  if (state.type) bits.push(TYPE_PLURAL[state.type]);
  if (state.year) bits.push(examLabel(BANK.exams[state.year] || { year: state.year }));
  return bits.length ? ` · ${bits.join(" · ")}` : "";
}

function emptyState() {
  const canClear = filtersOn() || state.query;
  return `<div class="empty-state"><div class="empty-ico" aria-hidden="true">🔍</div>
    <b>לא נמצאו שאלות</b>
    <p>${state.query ? "נסו מילה אחרת או חיפוש קצר יותר." : "אין שאלות שמתאימות לסינון שנבחר."}</p>
    ${canClear ? `<button type="button" class="btn" data-clear>ניקוי ${state.query ? "החיפוש והסינון" : "הסינון"}</button>` : ""}</div>`;
}

function renderResults() {
  $("results-head").hidden = false;
  let html, count, title, crumbs;
  if (state.query) {
    const hits = BANK.questions.filter(visible);
    count = hits.length;
    title = `חיפוש: "${state.query.trim()}"`;
    crumbs = `<a href="#">כל הנושאים</a> › `;
    html = hits.map(questionCard).join("");
  } else {
    const { unit, sub } = state.view;
    const u = UNITS.get(unit);
    const unitQs = unitQuestions(unit);
    crumbs = `<a href="#">כל הנושאים</a> › ` + (sub ? `<a href="#${unit}">${esc(u.name)}</a> › ` : "");
    if (!sub) {
      count = unitQs.length;
      html = unitQs.map(questionCard).join("");
      title = u.name;
    } else {
      const primary = unitQs.filter((q) => q.main === sub);
      const secondary = unitQs.filter((q) => q.main !== sub && q.subs.includes(sub));
      count = primary.length;
      html = primary.map(questionCard).join("");
      if (secondary.length) {
        html += `<h2 class="group-title">הנושא מופיע גם בסעיפים של שאלות אלו (${secondary.length})</h2>`
          + secondary.map(questionCard).join("");
      }
      title = subName(sub);
    }
  }
  $("crumbs").innerHTML = crumbs;
  $("results-title").textContent = title;
  const u = state.view && UNITS.get(state.view.unit);
  $("results-sub").textContent = `${count} ${state.query ? "תוצאות" : "שאלות"}${filterSummary()}`
    + (!state.query && u && u.folder ? " · נושאים שאינם בתוכנית הנוכחית" : "");
  $("results").innerHTML = html || emptyState();
}

function renderFilters() {
  for (const b of $("f-type").querySelectorAll("button")) b.setAttribute("aria-checked", String(b.dataset.type === state.type));
  $("f-year").value = state.year;
  $("f-clear").hidden = !filtersOn();
}

/* ---------- סל (המבחן שלי) ---------- */

function allLabels(q) {
  return q.items ? q.items.map((p) => p.label) : null;
}

function depsOf(q, label) {
  return (q.items.find((p) => p.label === label) || {}).depends_on || [];
}

/** סגירה טרנזיטיבית: הסעיף + כל הסעיפים שהוא נשען עליהם */
function withDeps(q, label, acc = new Set()) {
  if (acc.has(label)) return acc;
  acc.add(label);
  depsOf(q, label).forEach((d) => withDeps(q, d, acc));
  return acc;
}

/** הסעיף + כל הסעיפים שנשענים עליו (במישרין או בעקיפין) */
function dependents(q, label) {
  const out = new Set([label]);
  let grew = true;
  while (grew) {
    grew = false;
    for (const p of q.items) {
      if (!out.has(p.label) && (p.depends_on || []).some((d) => out.has(d))) {
        out.add(p.label);
        grew = true;
      }
    }
  }
  return out;
}

function toggleItem(entry, label, on) {
  const q = QS.get(entry.id);
  const order = allLabels(q);
  const cur = new Set(entry.items);
  if (on) {
    const add = withDeps(q, label);
    const extra = [...add].filter((l) => l !== label && !cur.has(l));
    add.forEach((l) => cur.add(l));
    state.msg[entry.id] = extra.length ? `נוסף גם סעיף ${extra.join(", ")} – סעיף ${label} נשען עליו.` : "";
  } else {
    const remove = dependents(q, label);
    const next = [...cur].filter((l) => !remove.has(l));
    if (!next.length) {
      state.msg[entry.id] = "חייב להישאר לפחות סעיף אחד. להסרת השאלה כולה לחצו ✕.";
      return;
    }
    const extra = [...remove].filter((l) => l !== label && cur.has(l));
    remove.forEach((l) => cur.delete(l));
    state.msg[entry.id] = extra.length ? `הוסר גם סעיף ${extra.join(", ")} – הוא נשען על סעיף ${label}.` : "";
  }
  entry.items = order.filter((l) => cur.has(l));
  entry.points = null;
}

/** ניקוד ברירת מחדל: כל השאלה – הניקוד המקורי; חלק מהסעיפים – סכום הסעיפים הראשיים שנבחרו */
function defaultPoints(entry) {
  const q = QS.get(entry.id);
  if (!entry.items || entry.items.length === q.items.length) return q.points ?? null;
  if (!q.part_points) return null;
  const letters = new Set(entry.items.map((l) => l[0]));
  return [...letters].reduce((s, l) => s + (q.part_points[l] || 0), 0);
}

const effectivePoints = (entry) => entry.points ?? defaultPoints(entry);

function cartTotals() {
  const known = state.cart.map(effectivePoints);
  return { total: known.reduce((s, p) => s + (p || 0), 0), missing: known.some((p) => p == null) };
}

function renderCart() {
  const list = $("cart-list");
  const n = state.cart.length;
  $("cart-count").textContent = n;
  $("cart-empty").hidden = n > 0;
  list.innerHTML = state.cart.map((entry, i) => {
    const q = QS.get(entry.id);
    const items = q.items ? `<div class="cart-items" role="group" aria-label="סעיפים">${q.items.map((p) => `
      <label title="סעיף ${esc(p.label)}"><input type="checkbox" data-item="${q.id}" value="${esc(p.label)}"
        ${entry.items.includes(p.label) ? "checked" : ""}><span>${esc(p.label)}</span></label>`).join("")}</div>` : "";
    const pts = effectivePoints(entry);
    const msg = state.msg[q.id] ? `<div class="cart-msg">${esc(state.msg[q.id])}</div>` : "";
    return `<li class="cart-q u-${q.unit}">
      <div class="cart-q-head">
        <span class="cart-q-num" aria-hidden="true"></span>
        <span class="cart-q-title"><a href="#card-${q.id}" data-goto="${q.id}">${esc(shortName(q.main) || UNITS.get(q.unit).name)}</a>
          <small>${esc(TYPE_NAMES[q.type])} · ${esc(examLabel(BANK.exams[q.exam]))}, שאלה ${q.number}</small></span>
        <span class="cart-q-tools">
          <button type="button" class="mini" data-move="${i}" data-dir="-1" aria-label="הזזה למעלה" title="הזזה למעלה" ${i === 0 ? "disabled" : ""}>▲</button>
          <button type="button" class="mini" data-move="${i}" data-dir="1" aria-label="הזזה למטה" title="הזזה למטה" ${i === n - 1 ? "disabled" : ""}>▼</button>
          <button type="button" class="mini rm" data-remove="${q.id}" aria-label="הסרה מהמבחן" title="הסרה">✕</button>
        </span>
      </div>
      <div class="cart-q-row">
        ${items}
        <label class="cart-pts">ניקוד <input type="number" min="0" step="0.5" data-points="${q.id}"
          value="${pts ?? ""}" placeholder="—"></label>
      </div>
      ${msg}
    </li>`;
  }).join("");
  const { total, missing } = cartTotals();
  $("cart-total").innerHTML = n
    ? `<b>${n}</b> שאלות · <b>${total}</b> נק'${missing ? ` <span class="warn">(יש שאלות בלי ניקוד)</span>`
      : total === 100 ? "" : ` <span class="mute">(${total < 100 ? `חסרות ${100 - total} נק' ל-100` : `${total - 100} נק' מעל 100`})</span>`}` : "";
  $("export-a").disabled = !n;
  $("export-b").disabled = !n;
  $("export-moodle").disabled = !n;
  $("export-forms").disabled = !n;
  $("export-mytestbox").disabled = !n;
  $("cart-clear").hidden = !n;
  $("cartbar").hidden = !n;
  $("cartbar-text").innerHTML = `<b>${n}</b> ${n === 1 ? "שאלה" : "שאלות"} במבחן · <b>${total}</b> נק'`;
}

function toggleCart(id) {
  if (inCart(id)) {
    state.cart = state.cart.filter((c) => c.id !== id);
  } else {
    state.cart.push({ id, items: allLabels(QS.get(id)), points: null });
  }
  delete state.msg[id];
}

/* ---------- מגירת המבחן ---------- */

const cartEl = $("cart");

function openCart() {
  cartEl.classList.add("open");
  cartEl.setAttribute("aria-hidden", "false");
  $("backdrop").hidden = false;
  document.body.classList.add("cart-open");
  $("cart-close").focus();
}

function closeCart() {
  if (!cartEl.classList.contains("open")) return;
  cartEl.classList.remove("open");
  cartEl.setAttribute("aria-hidden", "true");
  $("backdrop").hidden = true;
  document.body.classList.remove("cart-open");
  $("cart-toggle").focus({ preventScroll: true });
}

let toastTimer = null;
function toast(text) {
  const t = $("toast");
  t.textContent = text;
  t.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove("show"), 1800);
}

/* ---------- ציור ---------- */

function renderAll() {
  updateHighlighter();
  document.body.classList.toggle("hide-source", !state.showSource);
  document.body.classList.toggle("dash", !state.view && !state.query);
  if (state.view || state.query) {
    renderTopics();
    renderFilters();
    renderResults();
  } else {
    renderDashboard();
  }
  renderCart();
  save();
}

/** ציור מחדש של כרטיס אחד בלבד – כדי שהוספה למבחן לא תקפיץ את הדף */
function refreshCard(id) {
  const old = document.getElementById(`card-${id}`);
  if (!old) return;
  const tmp = document.createElement("div");
  tmp.innerHTML = questionCard(QS.get(id));
  old.replaceWith(tmp.firstElementChild);
}

/* ---------- אירועים ---------- */

$("topics").addEventListener("click", (e) => {
  const b = e.target.closest(".topic-btn");
  if (!b) return;
  clearSearch();
  $("topics").classList.remove("show");
  $("topics-toggle").setAttribute("aria-expanded", "false");
  const hash = viewHash({ unit: b.dataset.unit, sub: b.dataset.sub || null });
  if (location.hash === hash) renderAll();
  else location.hash = hash;
});

let pendingScroll = null; // כרטיס לגלול אליו אחרי מעבר תצוגה מהסל

window.addEventListener("hashchange", () => {
  if (location.hash.startsWith("#card-")) return;
  state.view = viewFromHash();
  clearSearch();
  renderAll();
  const card = pendingScroll && document.getElementById(`card-${pendingScroll}`);
  if (card) card.scrollIntoView({ block: "start" });
  else window.scrollTo({ top: 0 });
  pendingScroll = null;
});

$("results").addEventListener("click", (e) => {
  const add = e.target.closest("[data-add]");
  if (add) {
    const id = add.dataset.add;
    toggleCart(id);
    refreshCard(id);
    renderCart();
    save();
    const now = inCart(id);
    toast(now ? `השאלה נוספה למבחן (${state.cart.length})` : "השאלה הוסרה מהמבחן");
    const btn = $("cart-toggle");
    btn.classList.remove("bump");
    void btn.offsetWidth;
    btn.classList.add("bump");
    return;
  }
  if (e.target.closest("[data-clear]")) {
    clearFilters();
    clearSearch();
    renderAll();
    return;
  }
  if (e.target.matches(".fig")) openLightbox(e.target.src);
});

cartEl.addEventListener("click", (e) => {
  const t = e.target.closest("[data-remove], [data-move], [data-goto]");
  if (!t) return;
  if (t.dataset.remove) {
    toggleCart(t.dataset.remove);
    refreshCard(t.dataset.remove);
  } else if (t.dataset.move) {
    const i = Number(t.dataset.move);
    const j = i + Number(t.dataset.dir);
    [state.cart[i], state.cart[j]] = [state.cart[j], state.cart[i]];
  } else if (t.dataset.goto) {
    e.preventDefault();
    const q = QS.get(t.dataset.goto);
    const hash = viewHash({ unit: q.unit, sub: q.main });
    closeCart();
    if (location.hash === hash && !state.query) {
      document.getElementById(`card-${q.id}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
    } else {
      pendingScroll = q.id;
      clearFilters();
      if (location.hash === hash) {
        clearSearch();
        renderAll();
        document.getElementById(`card-${q.id}`)?.scrollIntoView({ block: "start" });
        pendingScroll = null;
      } else {
        location.hash = hash;
      }
    }
    return;
  }
  renderCart();
  save();
});

cartEl.addEventListener("change", (e) => {
  const t = e.target;
  if (t.dataset.item) {
    toggleItem(state.cart.find((c) => c.id === t.dataset.item), t.value, t.checked);
  } else if (t.dataset.points) {
    const entry = state.cart.find((c) => c.id === t.dataset.points);
    entry.points = t.value === "" ? null : Number(t.value);
  } else {
    return;
  }
  renderCart();
  save();
});

$("cart-toggle").addEventListener("click", () => (cartEl.classList.contains("open") ? closeCart() : openCart()));
$("cartbar-open").addEventListener("click", openCart);
$("cart-close").addEventListener("click", closeCart);
$("backdrop").addEventListener("click", closeCart);
$("cart-clear").addEventListener("click", () => {
  if (!confirm("להסיר את כל השאלות מהמבחן?")) return;
  state.cart = [];
  state.msg = {};
  $("convert").innerHTML = "";
  renderAll();
});
document.addEventListener("keydown", (e) => {
  if (e.key !== "Escape") return;
  if (document.querySelector(".lightbox")) closeLightbox();
  else closeCart();
});

/* חיפוש */
const searchEl = $("search");
let searchTimer = null;
searchEl.addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    state.query = searchEl.value;
    renderAll();
    window.scrollTo({ top: 0 });
  }, 180);
});
searchEl.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && searchEl.value) {
    e.stopPropagation();
    clearSearch();
    renderAll();
  }
});

function clearSearch() {
  state.query = "";
  searchEl.value = "";
}

/* סינון */
function clearFilters() {
  state.type = "";
  state.year = "";
}
$("f-year").innerHTML += OTHER_SOURCES.map(([id, e]) => `<option value="${id}">${esc(e.label)}</option>`).join("")
  + YEARS.map((y) => `<option value="${y}">בגרות ${y}</option>`).join("");
$("f-type").addEventListener("click", (e) => {
  const b = e.target.closest("[data-type]");
  if (!b) return;
  state.type = b.dataset.type;
  renderAll();
});
$("f-year").addEventListener("change", (e) => { state.year = e.target.value; renderAll(); });
$("f-clear").addEventListener("click", () => { clearFilters(); renderAll(); });

const optSource = $("opt-source");
const optOnline = $("opt-online");
optSource.addEventListener("change", () => { state.showSource = optSource.checked; renderAll(); });
optOnline.addEventListener("change", () => { state.hideOnline = optOnline.checked; renderAll(); });

$("topics-toggle").addEventListener("click", (e) => {
  const open = $("topics").classList.toggle("show");
  e.currentTarget.setAttribute("aria-expanded", String(open));
});

/* מצב כהה / בהיר */
$("theme-toggle").addEventListener("click", () => {
  const root = document.documentElement;
  const dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  root.dataset.theme = dark ? "light" : "dark";
  try { localStorage.setItem(THEME_KEY, root.dataset.theme); } catch (e) { /* אחסון חסום */ }
});

/* איור בגדול */
function openLightbox(src) {
  const box = document.createElement("div");
  box.className = "lightbox";
  box.innerHTML = `<img src="${esc(src)}" alt="איור מוגדל">`;
  box.addEventListener("click", closeLightbox);
  document.body.appendChild(box);
}
function closeLightbox() {
  document.querySelector(".lightbox")?.remove();
}

/* חזרה למעלה */
const toTop = $("to-top");
window.addEventListener("scroll", () => { toTop.hidden = window.scrollY < 900; }, { passive: true });
toTop.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));

const headerForm = $("header-form");
headerForm.addEventListener("input", (e) => {
  state.header[e.target.name] = e.target.value;
  save();
});

load();
state.view = viewFromHash();
for (const el of headerForm.elements) el.value = state.header[el.name] || "";
if (Object.values(state.header).some(Boolean)) $("exam-details").open = true;
optSource.checked = state.showSource;
optOnline.checked = state.hideOnline;
renderAll();
