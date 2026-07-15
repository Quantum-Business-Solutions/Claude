/**
 * docx_templates.js
 * ==================
 *
 * Reusable Word document formatting helpers for HubSpot audit deliverables.
 * Ensures visual consistency across every audit run.
 *
 * Import in your build script:
 *   const T = require('./docx_templates');
 *   const doc = new Document({ ... sections: [ { children: [ T.H1("Section"), ... ] } ] });
 *
 * Or use build_audit_docx.js which consumes a standardized JSON input and
 * produces the canonical v3-shaped audit document using these helpers.
 */

const {
    Paragraph, TextRun, Table, TableRow, TableCell, TabStopType, Footer,
    AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
    VerticalAlign, PageNumber, PageBreak
} = require('docx');

// ============================================================================
// BRAND TOKENS (from assets/brand.md)
// ============================================================================

const BRAND = {
    NAVY: "0A1F44",        // Primary headers, accents
    GOLD: "C9A227",        // Rule lines, accent elements
    BODY: "1A1A1A",        // Body text
    SLATE: "5A6470",       // Secondary text
    RULE_GRAY: "D8DDE3",   // Table borders
    LIGHT_BG: "F4F5F7",    // Light backgrounds (total rows, etc.)
    // Severity palette
    CRITICAL_RED: "8B1E1E",
    HIGH_AMBER: "B5761F",
    MEDIUM_GOLD: "C9A227",
    LOW_SLATE: "5A6470",
    // Status palette (feature matrix cells)
    GREEN_OK: "2D5F2D",
    AMBER_PARTIAL: "B5761F",
    RED_NO: "8B1E1E",
    GRAY_UNKNOWN: "A0A0A0",
    // Band palette (scoreboard)
    BAND_HEALTHY: "2D5F2D",   // 85-100
    BAND_GOOD: "5A7A2D",      // 70-84
    BAND_DEGRADED: "B5761F",  // 50-69
    BAND_POOR: "A84545",      // 30-49
    BAND_CRITICAL: "8B1E1E",  // 0-29
    FONT: "Calibri"
};

// Default border spec for tables
const border = { style: BorderStyle.SINGLE, size: 4, color: BRAND.RULE_GRAY };
const borders = { top: border, bottom: border, left: border, right: border };

// ============================================================================
// TEXT / PARAGRAPH HELPERS
// ============================================================================

/** Simple paragraph with a single text run. */
function P(text, opts = {}) {
    return new Paragraph({
        spacing: { before: opts.before || 0, after: opts.after || 120, line: 276 },
        alignment: opts.align || AlignmentType.LEFT,
        children: [new TextRun({
            text, font: BRAND.FONT, size: opts.size || 22,
            color: opts.color || BRAND.BODY,
            bold: opts.bold || false, italics: opts.italic || false
        })]
    });
}

/** Paragraph with multiple text runs (for inline emphasis). */
function Pmulti(runs, opts = {}) {
    return new Paragraph({
        spacing: { before: opts.before || 0, after: opts.after || 120, line: 276 },
        alignment: opts.align || AlignmentType.LEFT,
        children: runs
    });
}

/** Single text run with styling. */
function Run(text, opts = {}) {
    return new TextRun({
        text, font: BRAND.FONT, size: opts.size || 22,
        color: opts.color || BRAND.BODY,
        bold: opts.bold || false, italics: opts.italic || false
    });
}

/** H1 section header. */
function H1(text) {
    return new Paragraph({
        spacing: { before: 360, after: 200 }, heading: HeadingLevel.HEADING_1,
        children: [new TextRun({ text, font: BRAND.FONT, size: 36, bold: true, color: BRAND.NAVY })]
    });
}

/** H2 subsection header. */
function H2(text) {
    return new Paragraph({
        spacing: { before: 240, after: 120 }, heading: HeadingLevel.HEADING_2,
        children: [new TextRun({ text, font: BRAND.FONT, size: 28, bold: true, color: BRAND.NAVY })]
    });
}

/** H3 sub-subsection header. */
function H3(text) {
    return new Paragraph({
        spacing: { before: 180, after: 80 },
        children: [new TextRun({ text, font: BRAND.FONT, size: 22, bold: true, color: BRAND.NAVY })]
    });
}

/** Page break paragraph. */
function Pbreak() {
    return new Paragraph({ children: [new PageBreak()] });
}

/** Gold rule line (appears under H1s). */
function GoldRule() {
    return new Paragraph({
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BRAND.GOLD, space: 1 } },
        spacing: { before: 40, after: 120 },
        children: [new TextRun({ text: "" })]
    });
}

// ============================================================================
// SEVERITY BADGE (inline pill on findings)
// ============================================================================

function severityBadge(sev) {
    const pal = {
        CRITICAL: BRAND.CRITICAL_RED, HIGH: BRAND.HIGH_AMBER,
        MEDIUM: BRAND.MEDIUM_GOLD, LOW: BRAND.LOW_SLATE
    };
    return new Table({
        width: { size: 1400, type: WidthType.DXA }, columnWidths: [1400],
        rows: [new TableRow({ children: [new TableCell({
            borders: {
                top: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
                bottom: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
                left: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
                right: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" }
            },
            width: { size: 1400, type: WidthType.DXA },
            shading: { fill: pal[sev] || BRAND.SLATE, type: ShadingType.CLEAR },
            margins: { top: 40, bottom: 40, left: 100, right: 100 },
            children: [new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [new TextRun({ text: sev, font: BRAND.FONT, size: 18, bold: true, color: "FFFFFF" })]
            })]
        })]})]
    });
}

// ============================================================================
// SCOREBOARD BAR (dimension/tier scores)
// ============================================================================

function _bandColorForScore(score) {
    if (score >= 85) return BRAND.BAND_HEALTHY;
    if (score >= 70) return BRAND.BAND_GOOD;
    if (score >= 50) return BRAND.BAND_DEGRADED;
    if (score >= 30) return BRAND.BAND_POOR;
    return BRAND.BAND_CRITICAL;
}

function _bandLabelForScore(score) {
    if (score >= 85) return "Healthy";
    if (score >= 70) return "Good";
    if (score >= 50) return "Degraded";
    if (score >= 30) return "Poor";
    return "Critical";
}

/** Score bar row (label + bar + score + band). Use in scoreboard sections. */
function scoreBar(label, score, bandOverride) {
    const limit = 15;
    const filled = Math.max(0, Math.min(limit, Math.round((score / 100) * limit)));
    const bar = "█".repeat(filled) + "░".repeat(limit - filled);
    const band = bandOverride || _bandLabelForScore(score);
    const bandColor = _bandColorForScore(score);
    return new Paragraph({
        spacing: { before: 60, after: 60, line: 240 },
        children: [
            new TextRun({ text: label.padEnd(28, " "), font: "Consolas", size: 20, color: BRAND.BODY }),
            new TextRun({ text: bar + "  ", font: "Consolas", size: 20, color: BRAND.NAVY }),
            new TextRun({ text: (score + "/100").padEnd(8, " "), font: "Consolas", size: 20, color: BRAND.BODY, bold: true }),
            new TextRun({ text: "  " + band, font: "Consolas", size: 20, color: bandColor, bold: true }),
        ]
    });
}

// ============================================================================
// TABLE CELL HELPERS
// ============================================================================

/** Navy-filled header cell for table headers. */
function headerCell(text, width) {
    return new TableCell({
        borders, width: { size: width, type: WidthType.DXA },
        shading: { fill: BRAND.NAVY, type: ShadingType.CLEAR },
        margins: { top: 80, bottom: 80, left: 100, right: 100 },
        children: [new Paragraph({
            children: [new TextRun({ text, font: BRAND.FONT, size: 18, bold: true, color: "FFFFFF" })]
        })]
    });
}

/** Generic body cell (optional fill color). */
function bodyCell(text, width, opts = {}) {
    return new TableCell({
        borders, width: { size: width, type: WidthType.DXA },
        shading: opts.fill ? { fill: opts.fill, type: ShadingType.CLEAR } : undefined,
        margins: { top: 60, bottom: 60, left: 100, right: 100 },
        children: [new Paragraph({
            alignment: opts.align || AlignmentType.LEFT,
            children: [new TextRun({
                text, font: BRAND.FONT, size: opts.size || 18,
                color: opts.color || BRAND.BODY, bold: opts.bold || false
            })]
        })]
    });
}

/** Colored status cell (green/amber/red/gray) for feature matrix rows. */
function statusCell(status, width) {
    const color = status === "yes" ? BRAND.GREEN_OK
        : status === "partial" ? BRAND.AMBER_PARTIAL
        : status === "no" ? BRAND.RED_NO
        : BRAND.GRAY_UNKNOWN;
    const label = status === "yes" ? "Yes"
        : status === "partial" ? "Partial"
        : status === "no" ? "No"
        : status === "n/a" ? "N/A"
        : "?";
    return new TableCell({
        borders, width: { size: width, type: WidthType.DXA },
        shading: { fill: color, type: ShadingType.CLEAR },
        margins: { top: 60, bottom: 60, left: 80, right: 80 },
        children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: label, font: BRAND.FONT, size: 16, bold: true, color: "FFFFFF" })]
        })]
    });
}

// ============================================================================
// FEATURE UTILIZATION MATRIX
// ============================================================================

/**
 * Feature matrix table. `features` is an array of objects:
 *   { id, name, in_tier, configured, actively_used, used_well, notes }
 */
function featureMatrixTable(features) {
    const colWidths = [2800, 900, 900, 900, 900, 2960];
    const header = new TableRow({
        tableHeader: true,
        children: [
            headerCell("Feature", colWidths[0]),
            headerCell("In tier", colWidths[1]),
            headerCell("Configured", colWidths[2]),
            headerCell("Used", colWidths[3]),
            headerCell("Used well", colWidths[4]),
            headerCell("Notes", colWidths[5]),
        ]
    });
    const rows = features.map(f => new TableRow({
        children: [
            bodyCell(`${f.id} — ${f.name}`, colWidths[0]),
            statusCell(f.in_tier === true ? "yes" : f.in_tier === false ? "no" : "unknown", colWidths[1]),
            statusCell(f.configured || "unknown", colWidths[2]),
            statusCell(f.actively_used || "unknown", colWidths[3]),
            statusCell(f.used_well || "unknown", colWidths[4]),
            bodyCell(f.notes || "—", colWidths[5], { size: 16 }),
        ]
    }));
    return new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: colWidths, rows: [header, ...rows] });
}

// ============================================================================
// DEDUCTION TABLE (Appendix D — dimension or tier score calculation)
// ============================================================================

/**
 * Deduction table. `rows` is an array of:
 *   { source, reason, amount }
 * Auto-computes total and final score (starting at 100). Renders a total row
 * in a light-gray band at the bottom.
 */
function deductionTable(rows) {
    const colWidths = [2000, 5360, 2000];
    const header = new TableRow({
        tableHeader: true,
        children: [
            headerCell("Source", colWidths[0]),
            headerCell("Reason", colWidths[1]),
            headerCell("Deduction", colWidths[2]),
        ]
    });
    const rowObjs = rows.map(r => new TableRow({
        children: [
            bodyCell(r.source, colWidths[0], { size: 18 }),
            bodyCell(r.reason, colWidths[1], { size: 18 }),
            bodyCell(r.amount > 0 ? "+" + r.amount : "" + r.amount, colWidths[2], {
                size: 18, align: AlignmentType.CENTER, bold: true,
                color: r.amount < 0 ? BRAND.CRITICAL_RED : BRAND.BODY
            }),
        ]
    }));
    const total = rows.reduce((a, r) => a + r.amount, 0);
    const final_score = Math.max(0, 100 + total);
    const totalRow = new TableRow({
        children: [
            new TableCell({
                borders, width: { size: colWidths[0], type: WidthType.DXA },
                shading: { fill: BRAND.LIGHT_BG, type: ShadingType.CLEAR },
                margins: { top: 80, bottom: 80, left: 100, right: 100 },
                children: [new Paragraph({
                    children: [new TextRun({ text: "Starting: 100", font: BRAND.FONT, size: 18, bold: true, color: BRAND.NAVY })]
                })]
            }),
            new TableCell({
                borders, width: { size: colWidths[1], type: WidthType.DXA },
                shading: { fill: BRAND.LIGHT_BG, type: ShadingType.CLEAR },
                margins: { top: 80, bottom: 80, left: 100, right: 100 },
                children: [new Paragraph({
                    children: [new TextRun({ text: `Total deductions: ${total}   |   Final score: ${final_score}`, font: BRAND.FONT, size: 18, bold: true, color: BRAND.NAVY })]
                })]
            }),
            new TableCell({
                borders, width: { size: colWidths[2], type: WidthType.DXA },
                shading: { fill: BRAND.LIGHT_BG, type: ShadingType.CLEAR },
                margins: { top: 80, bottom: 80, left: 100, right: 100 },
                children: [new Paragraph({
                    alignment: AlignmentType.CENTER,
                    children: [new TextRun({ text: String(final_score), font: BRAND.FONT, size: 22, bold: true, color: BRAND.NAVY })]
                })]
            }),
        ]
    });
    return new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: colWidths, rows: [header, ...rowObjs, totalRow] });
}

// ============================================================================
// RevEfficiency TIER ROW (for the tier scoreboard table)
// ============================================================================

function tierRow(tierName, score, bandOverride, note) {
    const colWidths = [2000, 1200, 1200, 4960];
    const band = bandOverride || _bandLabelForScore(score);
    const bandColor = _bandColorForScore(score);
    return new TableRow({
        children: [
            bodyCell(tierName, colWidths[0], { bold: true, color: BRAND.NAVY, fill: BRAND.LIGHT_BG }),
            new TableCell({
                borders, width: { size: colWidths[1], type: WidthType.DXA },
                shading: { fill: bandColor, type: ShadingType.CLEAR },
                margins: { top: 80, bottom: 80, left: 120, right: 120 },
                children: [new Paragraph({
                    alignment: AlignmentType.CENTER,
                    children: [new TextRun({ text: score + "/100", font: BRAND.FONT, size: 20, bold: true, color: "FFFFFF" })]
                })]
            }),
            bodyCell(band, colWidths[2], { size: 20, align: AlignmentType.CENTER, bold: true }),
            bodyCell(note, colWidths[3], { size: 20 }),
        ]
    });
}

// ============================================================================
// MATURITY STAGE ROW (for the RevOps maturity table)
// ============================================================================

function maturityStageRow(capability, stage, note) {
    const colWidths = [3000, 1360, 5000];
    const stageColor = stage <= 1 ? BRAND.CRITICAL_RED
        : stage == 2 ? BRAND.HIGH_AMBER
        : stage == 3 ? BRAND.BAND_GOOD
        : stage == 4 ? BRAND.BAND_HEALTHY
        : "1C4D1C";
    return new TableRow({
        children: [
            bodyCell(capability, colWidths[0], { bold: true, color: BRAND.NAVY, fill: BRAND.LIGHT_BG }),
            new TableCell({
                borders, width: { size: colWidths[1], type: WidthType.DXA },
                shading: { fill: stageColor, type: ShadingType.CLEAR },
                margins: { top: 80, bottom: 80, left: 120, right: 120 },
                children: [new Paragraph({
                    alignment: AlignmentType.CENTER,
                    children: [new TextRun({ text: "Stage " + stage, font: BRAND.FONT, size: 20, bold: true, color: "FFFFFF" })]
                })]
            }),
            bodyCell(note, colWidths[2], { size: 20 }),
        ]
    });
}

// ============================================================================
// ROADMAP TABLE
// ============================================================================

/**
 * Roadmap table. `items` is an array of 4-element arrays:
 *   [item, effort, impact, tier_requirement]
 */
function roadmapTable(items) {
    const colWidths = [4200, 1560, 1800, 1800];
    const header = new TableRow({
        tableHeader: true,
        children: [
            headerCell("Item", colWidths[0]),
            headerCell("Effort", colWidths[1]),
            headerCell("Impact", colWidths[2]),
            headerCell("Tier requirement", colWidths[3]),
        ]
    });
    const rows = items.map(r => new TableRow({
        children: [
            bodyCell(r[0], colWidths[0], { size: 20 }),
            bodyCell(r[1], colWidths[1], { size: 20 }),
            bodyCell(r[2], colWidths[2], { size: 20 }),
            bodyCell(r[3], colWidths[3], { size: 20 }),
        ]
    }));
    return new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: colWidths, rows: [header, ...rows] });
}

// ============================================================================
// LOCKED FEATURE TABLE (Appendix E — upgrade opportunities)
// ============================================================================

/**
 * Locked feature table. `rows` is an array of 3-element arrays:
 *   [feature, required_tier, value_unlock]
 */
function lockedFeatureTable(rows) {
    const colWidths = [2800, 2000, 4560];
    const header = new TableRow({
        tableHeader: true,
        children: [
            headerCell("Feature", colWidths[0]),
            headerCell("Required tier", colWidths[1]),
            headerCell("What it unlocks", colWidths[2]),
        ]
    });
    const rowObjs = rows.map(r => new TableRow({
        children: [
            bodyCell(r[0], colWidths[0], { size: 20, bold: true, color: BRAND.NAVY }),
            bodyCell(r[1], colWidths[1], { size: 20 }),
            bodyCell(r[2], colWidths[2], { size: 20 }),
        ]
    }));
    return new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: colWidths, rows: [header, ...rowObjs] });
}

// ============================================================================
// FINDING BLOCK (structured finding in dimension audit section)
// ============================================================================

/**
 * Produces an array of paragraphs/tables for a single finding.
 * sev = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
 */
function findingBlock(sev, title, evidence, impact, rec, effortTier) {
    return [
        new Paragraph({
            spacing: { before: 180, after: 80 },
            children: [new TextRun({ text: title, font: BRAND.FONT, size: 24, bold: true, color: BRAND.NAVY })]
        }),
        severityBadge(sev),
        Pmulti([Run("What we found. ", { bold: true, color: BRAND.NAVY }), Run(evidence)], { before: 60, after: 60 }),
        Pmulti([Run("Why it matters. ", { bold: true, color: BRAND.NAVY }), Run(impact)], { after: 60 }),
        Pmulti([Run("What we recommend. ", { bold: true, color: BRAND.NAVY }), Run(rec)], { after: 60 }),
        Pmulti([Run("Effort and tier. ", { bold: true, color: BRAND.NAVY }), Run(effortTier)], { after: 180 }),
    ];
}

// ============================================================================
// STANDARD FOOTER (appears on every page)
// ============================================================================

function standardFooter() {
    return new Footer({
        children: [new Paragraph({
            border: { top: { style: BorderStyle.SINGLE, size: 4, color: BRAND.GOLD, space: 4 } },
            tabStops: [{ type: TabStopType.RIGHT, position: 9360 }],
            children: [
                new TextRun({ text: "Quantum Business Solutions  |  Confidential", font: BRAND.FONT, size: 18, color: BRAND.SLATE }),
                new TextRun({ text: "\t", font: BRAND.FONT, size: 18 }),
                new TextRun({ children: ["Page ", PageNumber.CURRENT], font: BRAND.FONT, size: 18, color: BRAND.SLATE }),
            ]
        })]
    });
}

// ============================================================================
// STANDARD DOCUMENT STYLES (paragraph styles for Word)
// ============================================================================

const STANDARD_STYLES = {
    default: { document: { run: { font: BRAND.FONT, size: 22 } } },
    paragraphStyles: [
        {
            id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
            run: { size: 36, bold: true, font: BRAND.FONT, color: BRAND.NAVY },
            paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 }
        },
        {
            id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
            run: { size: 28, bold: true, font: BRAND.FONT, color: BRAND.NAVY },
            paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 }
        },
    ]
};

// ============================================================================
// PAGE SETTINGS (US Letter, 0.9in margins)
// ============================================================================

const STANDARD_PAGE = {
    size: { width: 12240, height: 15840 },      // US Letter
    margin: { top: 1440, right: 1296, bottom: 1440, left: 1296 }
};

// ============================================================================
// COVER PAGE BUILDER
// ============================================================================

function buildCover(clientName, auditDate) {
    return [
        new Paragraph({
            spacing: { before: 1800, after: 240 }, alignment: AlignmentType.CENTER,
            children: [new TextRun({
                text: "QUANTUM BUSINESS SOLUTIONS",
                font: BRAND.FONT, size: 22, bold: true, color: BRAND.NAVY, characterSpacing: 120
            })]
        }),
        new Paragraph({
            border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: BRAND.GOLD, space: 12 } },
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: "", font: BRAND.FONT, size: 18 })]
        }),
        new Paragraph({
            spacing: { before: 2800, after: 240 }, alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: "HubSpot Portal Audit", font: BRAND.FONT, size: 52, bold: true, color: BRAND.NAVY })]
        }),
        new Paragraph({
            spacing: { before: 240, after: 240 }, alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: clientName, font: BRAND.FONT, size: 36, color: BRAND.NAVY })]
        }),
        new Paragraph({
            spacing: { before: 240, after: 240 }, alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: auditDate, font: BRAND.FONT, size: 24, color: BRAND.SLATE })]
        }),
        new Paragraph({
            spacing: { before: 3200, after: 0 }, alignment: AlignmentType.CENTER,
            children: [new TextRun({
                text: "Prepared by Quantum Business Solutions",
                font: BRAND.FONT, size: 20, color: BRAND.SLATE, italics: true
            })]
        }),
        Pbreak(),
    ];
}

// ============================================================================
// EXPORTS
// ============================================================================

module.exports = {
    BRAND,
    borders, border,
    // text helpers
    P, Pmulti, Run, H1, H2, H3, Pbreak, GoldRule,
    // visual elements
    severityBadge, scoreBar,
    // cells
    headerCell, bodyCell, statusCell,
    // tables
    featureMatrixTable, deductionTable, tierRow, maturityStageRow, roadmapTable, lockedFeatureTable,
    // finding block
    findingBlock,
    // document scaffolding
    standardFooter, STANDARD_STYLES, STANDARD_PAGE, buildCover,
};
