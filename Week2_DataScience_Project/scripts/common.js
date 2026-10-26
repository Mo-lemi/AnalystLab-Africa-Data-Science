// Shared styles and helpers for the Week 2 Word reports (docx-js).
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, LevelFormat, Header, Footer, PageNumber, ImageRun,
} = require("docx");

const ACCENT = "1F4E79";
const PAGE_WIDTH = 9026; // A4 width minus 1-inch margins, in DXA

const styles = {
  default: { document: { run: { font: "Calibri", size: 22 }, paragraph: { spacing: { after: 120, line: 276 } } } },
  paragraphStyles: [
    { id: "Title", name: "Title", basedOn: "Normal", run: { size: 40, bold: true, color: ACCENT },
      paragraph: { spacing: { after: 60 } } },
    { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { size: 28, bold: true, color: ACCENT }, paragraph: { spacing: { before: 240, after: 100 }, outlineLevel: 0, keepNext: true, keepLines: true } },
    { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { size: 24, bold: true, color: "2E2E2E" }, paragraph: { spacing: { before: 180, after: 80 }, outlineLevel: 1, keepNext: true, keepLines: true } },
  ],
};

const numbering = {
  config: [
    { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] },
    { reference: "numbers", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 540, hanging: 360 } } } }] },
  ],
};

// Inline **bold** support: "plain **bold** plain"
function runs(text, opts = {}) {
  return text.split(/(\*\*[^*]+\*\*)/).filter(Boolean).map((part) =>
    part.startsWith("**") ? new TextRun({ text: part.slice(2, -2), bold: true, ...opts }) : new TextRun({ text: part, ...opts }));
}

const p = (text, opts = {}) => new Paragraph({ children: runs(text), ...opts });
const h1 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(text)] });
const h2 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(text)] });
const bullet = (text) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: runs(text), spacing: { after: 60 } });
const numbered = (text) => new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: runs(text), spacing: { after: 60 } });

const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const borders = { top: border, bottom: border, left: border, right: border };

// rows: array of arrays of strings; first row is the header. widths: fractions summing to 1.
function table(rows, widths) {
  const cols = widths.map((w) => Math.round(w * PAGE_WIDTH));
  cols[cols.length - 1] = PAGE_WIDTH - cols.slice(0, -1).reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: PAGE_WIDTH, type: WidthType.DXA },
    columnWidths: cols,
    rows: rows.map((row, r) => new TableRow({
      tableHeader: r === 0,
      children: row.map((cell, c) => new TableCell({
        borders,
        width: { size: cols[c], type: WidthType.DXA },
        shading: r === 0 ? { fill: ACCENT, type: ShadingType.CLEAR, color: "auto" } : undefined,
        margins: { top: 60, bottom: 60, left: 100, right: 100 },
        children: [new Paragraph({ spacing: { after: 0 },
          children: runs(cell, r === 0 ? { bold: true, color: "FFFFFF", size: 20 } : { size: 20 }) })],
      })),
    })),
  });
}

// Image scaled to the page width, keeping its aspect ratio (PNG width/height read from the header).
function image(path, maxWidthPx = 600) {
  const data = fs.readFileSync(path);
  const w = data.readUInt32BE(16), h = data.readUInt32BE(20);
  const width = Math.min(maxWidthPx, w);
  return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 40 },
    children: [new ImageRun({ type: "png", data, transformation: { width, height: Math.round((h * width) / w) } })] });
}

const caption = (text) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
  children: [new TextRun({ text, italics: true, size: 18, color: "595959" })] });

const spacer = () => new Paragraph({ spacing: { after: 0 }, children: [] });

function titleBlock(title, subtitle) {
  return [
    new Paragraph({ children: [new TextRun({ text: "ANALYSTLAB AFRICA · DATA SCIENCE INTERNSHIP · WEEK 2", size: 18, bold: true, color: "808080" })], spacing: { after: 60 } }),
    new Paragraph({ style: "Title", children: [new TextRun(title)] }),
    new Paragraph({ children: [new TextRun({ text: subtitle, size: 24, color: "404040" })], spacing: { after: 60 } }),
    new Paragraph({
      border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: ACCENT, space: 4 } },
      children: [new TextRun({ text: "Author: Molemi Molokoane  ·  Dataset: Heart Failure Prediction (fedesoriano, Kaggle)  ·  October 2026", size: 18, color: "595959" })],
      spacing: { after: 200 },
    }),
  ];
}

function build(children, outPath, headerText) {
  const doc = new Document({
    creator: "Molemi Molokoane",
    title: headerText,
    styles, numbering,
    sections: [{
      properties: { page: { margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
      headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
        children: [new TextRun({ text: headerText, size: 16, color: "808080" })] })] }) },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
        children: [new TextRun({ children: ["Page ", PageNumber.CURRENT, " of ", PageNumber.TOTAL_PAGES], size: 16, color: "808080" })] })] }) },
      children,
    }],
  });
  return Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(outPath, buf); console.log("wrote", outPath); });
}

module.exports = { p, h1, h2, bullet, numbered, table, image, caption, spacer, titleBlock, build };
