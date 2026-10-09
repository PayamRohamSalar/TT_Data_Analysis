// Build reports/phase1_final_report_v2.docx (Persian RTL) from .cache/report_blocks.json
// Run: node scripts/report_build/build_docx.js   (after parse_md.py)
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell, WidthType,
  BorderStyle, ImageRun, TableOfContents, Footer, PageNumber, ShadingType, Math: DocxMath, MathRun, MathFraction,
} = require("docx");

const ROOT = path.resolve(__dirname, "..", "..");
const blocks = JSON.parse(fs.readFileSync(path.join(__dirname, ".cache", "report_blocks.json"), "utf8"));
const FIG_DIR = path.join(ROOT, "reports", "figures", "phase1_market_overview");

const FONT = "B Nazanin";
const fnt = (latin, cs) => ({ ascii: latin, hAnsi: latin, cs, eastAsia: cs });
// MainText: Latin Cambria 11, Complex B Nazanin 13 ; tables/figures: B Nazanin 11 ; H1 B Titr 15 blue ; H2 B Titr 13 black
const KIND = {
  main:  { font: fnt("Cambria", "B Nazanin"), size: 22, cs: 26 },
  table: { font: fnt("B Nazanin", "B Nazanin"), size: 22, cs: 22 },
  h1:    { font: fnt("B Titr", "B Titr"), size: 30, cs: 30 },
  h2:    { font: fnt("B Titr", "B Titr"), size: 26, cs: 26 },
  h3:    { font: fnt("B Titr", "B Titr"), size: 26, cs: 26 },
};
const CODE_FONT = "Consolas";
const TABLE_WIDTH = 9350;
const BLUE = "1F4E79";
const OUT = process.argv[2] || path.join(ROOT, "reports", "phase1_final_report_v2.docx");

const run = (r, opts = {}) => {
  const k = KIND[opts.kind || "main"];
  return r.code
    ? new TextRun({ text: r.text, font: fnt("Cambria", "B Nazanin"), size: k.size, sizeComplexScript: k.cs, bold: r.bold, color: "000000" })
    : new TextRun({ text: r.text, font: k.font, size: k.size, sizeComplexScript: k.cs, bold: r.bold || opts.bold, italics: opts.italics, color: opts.color || "000000", rightToLeft: true });
};
const runs = (rs, opts) => rs.map(r => run(r, opts));
const plain = rs => rs.map(r => r.text).join("");

const body = (rs, extra = {}) => new Paragraph({
  bidirectional: true, alignment: AlignmentType.RIGHT, spacing: { after: 160, line: 312 }, children: runs(rs), ...extra,
});

const HEAD = { 1: HeadingLevel.HEADING_1, 2: HeadingLevel.HEADING_2, 3: HeadingLevel.HEADING_3 };
const heading = (level, rs, pageBreak) => new Paragraph({
  heading: HEAD[level], bidirectional: true, alignment: AlignmentType.RIGHT, pageBreakBefore: !!pageBreak, keepNext: true,
  spacing: { before: level === 1 ? 0 : 300, after: 160 },
  children: rs.map(r => new TextRun({
    text: r.text, font: KIND["h" + level].font, size: KIND["h" + level].size, sizeComplexScript: KIND["h" + level].cs, bold: false,
    color: level === 1 ? BLUE : "000000", rightToLeft: true,
  })),
});

const hr = () => new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "BBBBBB" } }, spacing: { before: 100, after: 100 }, children: [] });

const quote = rs => new Paragraph({
  bidirectional: true, alignment: AlignmentType.RIGHT, indent: { start: 400 },
  shading: { type: ShadingType.CLEAR, fill: "F2F2F2" }, border: { right: { style: BorderStyle.SINGLE, size: 18, color: "808080" } },
  spacing: { before: 100, after: 160 }, children: runs(rs, { italics: true }),
});

const listItem = b => new Paragraph({
  bidirectional: true, alignment: AlignmentType.RIGHT, indent: { start: 300 }, spacing: { after: 120, line: 300 },
  children: [new TextRun({ text: b.ordered ? b.marker + ". " : "• ", font: KIND.main.font, size: KIND.main.size, sizeComplexScript: KIND.main.cs, color: "000000", rightToLeft: true })].concat(runs(b.runs)),
});

function image(b) {
  const full = path.join(FIG_DIR, path.basename(b.src));
  if (!b.exists) return [body([{ text: `[تصویر یافت نشد: ${path.basename(b.src)}]`, bold: true }])];
  const MAXW = 600, MAXH = 640;
  const scale = Math.min(1, MAXW / b.w, MAXH / b.h);
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 160, after: 60 },
      children: [new ImageRun({ type: "png", data: fs.readFileSync(full), transformation: { width: Math.round(b.w * scale), height: Math.round(b.h * scale) } })],
    }),
    new Paragraph({
      bidirectional: true, alignment: AlignmentType.CENTER, spacing: { after: 240 },
      children: [new TextRun({ text: b.alt, font: KIND.table.font, size: 22, sizeComplexScript: 22, bold: true, color: "000000", rightToLeft: true })],
    }),
  ];
}

const cellBorder = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
function table(b) {
  const nc = b.header.length;
  const maxlen = new Array(nc).fill(4);
  [b.header, ...b.rows].forEach(r => r.forEach((c, i) => { if (i < nc) maxlen[i] = Math.max(maxlen[i], Math.min(34, plain(c).length)); }));
  const weights = maxlen.map(l => Math.sqrt(l) + 1.2);
  const sum = weights.reduce((a, x) => a + x, 0);
  const widths = weights.map(w => Math.floor(TABLE_WIDTH * w / sum));
  widths[widths.length - 1] += TABLE_WIDTH - widths.reduce((a, x) => a + x, 0);
  const cell = (rs, hdr, w) => new TableCell({
    width: { size: w, type: WidthType.DXA },
    shading: hdr ? { type: ShadingType.CLEAR, fill: "DCE6F1" } : undefined,
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    borders: { top: cellBorder, bottom: cellBorder, left: cellBorder, right: cellBorder },
    children: [new Paragraph({
      bidirectional: true, alignment: AlignmentType.RIGHT, spacing: { after: 0 },
      children: rs.length ? runs(rs, { kind: "table", bold: hdr }) : [new TextRun({ text: "", font: KIND.table.font, size: 22 })],
    })],
  });
  const rows = [new TableRow({ tableHeader: true, cantSplit: true, children: b.header.map((c, i) => cell(c, true, widths[i])) })]
    .concat(b.rows.map(r => new TableRow({ cantSplit: true, children: Array.from({ length: nc }, (_, i) => cell(r[i] || [], false, widths[i])) })));
  return new Table({ width: { size: TABLE_WIDTH, type: WidthType.DXA }, columnWidths: widths, visuallyRightToLeft: true, rows });
}

// ---- equations: "A = B ، C = D" ; fractions written as [ num // den ] ----
function mathChildren(text) {
  const out = [];
  const fracRe = /\[\s*(.+?)\s*\/\/\s*(.+?)\s*\]/g;
  let pos = 0, m;
  const pushText = t => t.split(/(\s[=+×÷-]\s)/).forEach(tok => { if (tok.trim() !== "") out.push(new MathRun(tok.trim())); else if (tok) out.push(new MathRun(" ")); });
  while ((m = fracRe.exec(text)) !== null) {
    pushText(text.slice(pos, m.index));
    out.push(new MathFraction({ numerator: [new MathRun(m[1])], denominator: [new MathRun(m[2])] }));
    pos = m.index + m[0].length;
  }
  pushText(text.slice(pos));
  return out;
}
function equation(b) {
  const parts = b.text.split("،");
  const children = [];
  parts.forEach((p, i) => {
    if (i > 0) children.push(new MathRun("      ؛      "));
    children.push(...mathChildren(p.trim()));
  });
  return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 160 }, children: [new DocxMath({ children })] });
}

const isCaption = b => b.type === "para" && b.runs.length && b.runs[0].bold && /^جدول /.test(b.runs[0].text);

const children = [];
let seenFirstH1 = false, tocDone = false, titleDone = 0;
for (const b of blocks) {
  if (b.type === "heading") {
    const t = plain(b.runs);
    if (b.level === 1 && !seenFirstH1) {                       // title page
      seenFirstH1 = true;
      children.push(new Paragraph({ bidirectional: true, alignment: AlignmentType.CENTER, spacing: { before: 1200, after: 240 },
        children: [new TextRun({ text: t, font: KIND.h1.font, size: 52, bold: false, color: BLUE, rightToLeft: true })] }));
      continue;
    }
    if (b.level === 2 && titleDone === 0 && seenFirstH1 && !tocDone) {
      titleDone = 1;
      children.push(new Paragraph({ bidirectional: true, alignment: AlignmentType.CENTER, spacing: { after: 400 },
        children: [new TextRun({ text: t, font: FONT, size: 30, color: "404040", rightToLeft: true })] }));
      continue;
    }
    if (b.level === 1 && !tocDone && t.startsWith("خلاصه‌ی مدیریتی")) {
      tocDone = true;
      children.push(new Paragraph({ bidirectional: true, alignment: AlignmentType.RIGHT, pageBreakBefore: true, spacing: { after: 300 },
        children: [new TextRun({ text: "فهرست مطالب", font: FONT, size: 32, bold: true, color: BLUE, rightToLeft: true })] }));
      children.push(new TableOfContents("فهرست مطالب", { hyperlink: true, headingStyleRange: "1-2" }));
      children.push(heading(1, b.runs, true));
      continue;
    }
    children.push(heading(b.level, b.runs, b.level === 1));
  } else if (b.type === "para") {
    if (b.runs.length === 1 && b.runs[0].text.trim() === "") continue;
    children.push(isCaption(b)
      ? new Paragraph({ bidirectional: true, alignment: AlignmentType.RIGHT, keepNext: true, spacing: { before: 200, after: 100 }, children: runs(b.runs, { kind: "table" }) })
      : body(b.runs));
  } else if (b.type === "hr") {
    children.push(hr());
  } else if (b.type === "blockquote") {
    children.push(quote(b.runs));
  } else if (b.type === "list_item") {
    children.push(listItem(b));
  } else if (b.type === "image") {
    children.push(...image(b));
  } else if (b.type === "equation") {
    children.push(equation(b));
  } else if (b.type === "table") {
    children.push(table(b));
    children.push(new Paragraph({ spacing: { after: 200 }, children: [] }));
  }
}

const doc = new Document({
  creator: "TT Data Analysis", title: "گزارش نهایی فاز ۱",
  styles: { default: { document: { run: { font: KIND.main.font, size: 22, sizeComplexScript: 26, rightToLeft: true }, paragraph: { bidirectional: true } } } },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18 })] })] }) },
    children,
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(OUT, buf);
  console.log("WROTE", OUT, buf.length, "bytes; blocks:", blocks.length);
});
