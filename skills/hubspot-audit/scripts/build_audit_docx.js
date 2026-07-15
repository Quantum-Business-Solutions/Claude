#!/usr/bin/env node
/**
 * build_audit_docx.js
 * ====================
 *
 * Canonical HubSpot audit document generator.
 *
 * Takes a JSON audit input and produces the full client-mode Word document
 * in the canonical section order specified in references/deliverable.md.
 *
 * Usage:
 *   node build_audit_docx.js <input.json> <output.docx>
 *
 * Input JSON shape: see scripts/audit_input_example.json
 *
 * Canonical section order:
 *   1. Cover
 *   2. Executive Summary (with dual health score)
 *   3. How to Read
 *   4. Health Scoreboard (6 dimensions)        ← universal audit
 *   5. RevOps Maturity (5 capabilities)        ← universal audit
 *   6. Findings by Dimension                    ← universal audit CORE
 *   7. Feature Utilization Matrix (all hubs)   ← universal audit
 *   8. Revenue Efficiency Model Assessment      ← cross-cutting analysis
 *   9. Prioritized Roadmap
 *  10. Appendix A: Methodology
 *  11. Appendix D: Score Calculation Detail
 *  12. Appendix E: Features Available with Tier Upgrades
 */

const fs = require('fs');
const path = require('path');
const { Document, Packer, AlignmentType, Table, TableRow, WidthType } = require('docx');
const T = require('./docx_templates');

// ============================================================================
// SECTION BUILDERS
// ============================================================================

function buildExecSummary(input) {
    const s = input.executive_summary;
    const overall = input.overall_health_score;
    const overallBand = input.overall_health_band || _bandLabel(overall);
    const limiting = input.overall_health_limiting_dimension;
    const reScore = input.revefficiency_overall_score;
    const reLimiting = input.revefficiency_limiting_tier;

    const out = [
        T.H1("Executive Summary"),
        T.GoldRule(),
        T.P(s.portal_profile, { after: 180 }),
        T.H2("Two views of portal health"),
        T.P("This audit reports portal health along two complementary dimensions:", { after: 60 }),
        T.Pmulti([
            T.Run(`Overall portal health: ${overall} of 100 — ${overallBand}. `, { bold: true, color: T.BRAND.NAVY }),
            T.Run(`Limited by the ${limiting} dimension. The traditional dimensional audit view.`)
        ], { after: 80 }),
        T.Pmulti([
            T.Run(`RevEfficiency execution score: ${reScore} of 100 — ${_bandLabel(reScore)}. `, { bold: true, color: T.BRAND.NAVY }),
            T.Run(`Limited by the ${reLimiting} tier. Measures structural readiness to execute Quantum's 5-tier RevEfficiency Model.`)
        ], { after: 180 }),
    ];

    if (s.narrative) out.push(T.P(s.narrative, { after: 180 }));

    out.push(T.H2("Top three risks"));
    (s.top_risks || []).slice(0, 3).forEach((r, i) => {
        out.push(T.Pmulti([
            T.Run(`${i + 1}. ${r.title}. `, { bold: true, color: T.BRAND.NAVY }),
            T.Run(r.detail)
        ], { after: 100 }));
    });

    out.push(T.P(" ", { after: 60 }));
    out.push(T.H2("Top three opportunities"));
    (s.top_opportunities || []).slice(0, 3).forEach((r, i) => {
        out.push(T.Pmulti([
            T.Run(`${i + 1}. ${r.title}. `, { bold: true, color: T.BRAND.NAVY }),
            T.Run(r.detail)
        ], { after: 100 }));
    });

    if (s.next_step) {
        out.push(T.P(" ", { after: 60 }));
        out.push(T.H2("What we recommend doing next"));
        out.push(T.P(s.next_step, { after: 180 }));
    }
    out.push(T.Pbreak());
    return out;
}

function buildHowToRead(input) {
    return [
        T.H1("How to read this document"),
        T.GoldRule(),
        T.P("This audit applies a structured framework developed across more than 55 HubSpot portals and produces two complementary views of portal health:", { after: 120 }),
        T.Pmulti([
            T.Run("Dimension health (0-100 per dimension). ", { bold: true, color: T.BRAND.NAVY }),
            T.Run("Six operational dimensions: Data Health, Architecture, Adoption, Automation, Integrations, Reporting. Overall score = minimum of the six. This is the traditional audit view and the spine of this document.")
        ], { after: 100 }),
        T.Pmulti([
            T.Run("RevEfficiency execution (0-100 per tier). ", { bold: true, color: T.BRAND.NAVY }),
            T.Run("Five revenue tiers: KEEP, GROW, MULTIPLY, CONVERT, EXPAND. Overall = minimum of the five. This cross-cutting view reframes the dimensional findings in terms of Quantum's RevEfficiency Model and appears after the findings section.")
        ], { after: 180 }),
        T.H2("How scores are computed"),
        T.P("Every score is computed, not asserted. Each dimension and each tier starts at 100 and deducts specific point values for findings (Critical −15, High −8, Medium −3, Low −1) and for features the portal's tier makes available but that are not being used well. The full math appears in Appendix D.", { after: 120 }),
        T.H2("Severity definitions"),
        T.P("Critical: direct threat to revenue, compliance, or continuity. Address first.", { after: 60 }),
        T.P("High: meaningful drag on operations. Address in first engagement phase.", { after: 60 }),
        T.P("Medium: erodes efficiency over time. Address in subsequent phase.", { after: 60 }),
        T.P("Low: cosmetic cleanup. Address as time permits.", { after: 180 }),
        T.Pbreak(),
    ];
}

function buildScoreboard(input) {
    const out = [
        T.H1("Health scoreboard"),
        T.GoldRule(),
        T.P("Dimension health across six operational areas. Overall = minimum, not average — weakness in any dimension undermines the others. Full deduction detail in Appendix D.", { after: 180 }),
    ];
    const dims = input.dimension_scores || {};
    const dimOrder = ["data_health", "architecture", "adoption", "automation", "integrations", "reporting"];
    const labels = {
        data_health: "Data Health", architecture: "Architecture", adoption: "Adoption",
        automation: "Automation", integrations: "Integrations", reporting: "Reporting"
    };
    for (const key of dimOrder) {
        const entry = dims[key];
        if (entry === undefined || entry === null) {
            out.push(T.scoreBar(labels[key], 0, "Not audited"));
        } else if (typeof entry === "object") {
            out.push(T.scoreBar(labels[key], entry.score, entry.band));
        } else {
            out.push(T.scoreBar(labels[key], entry));
        }
    }
    out.push(T.P(" ", { after: 180 }));
    out.push(T.Pmulti([
        T.Run(`Overall: ${input.overall_health_score} of 100 — ${input.overall_health_band || _bandLabel(input.overall_health_score)}.`, { bold: true, color: T.BRAND.NAVY, size: 24 }),
        T.Run(`  Limiting dimension: ${input.overall_health_limiting_dimension}.`)
    ], { after: 120 }));

    if (input.dimension_narratives) {
        out.push(T.H2("Narrative per dimension"));
        for (const key of dimOrder) {
            const narr = input.dimension_narratives[key];
            if (narr) {
                out.push(T.Pmulti([
                    T.Run(`${labels[key]}: `, { bold: true, color: T.BRAND.NAVY }),
                    T.Run(narr)
                ], { after: 120 }));
            }
        }
    }
    out.push(T.P(" ", { after: 240 }));
    out.push(T.Pbreak());
    return out;
}

function buildMaturity(input) {
    if (!input.maturity || !input.maturity.stages) return [];
    const m = input.maturity;
    
    const headerRow = new TableRow({
        tableHeader: true,
        children: ["Capability", "Stage", "Observation"].map(h =>
            T.headerCell(h, h === "Capability" ? 3000 : h === "Stage" ? 1360 : 5000))
    });
    const rows = m.stages.map(s => T.maturityStageRow(s.capability, s.stage, s.observation));
    return [
        T.H1("RevOps maturity positioning"),
        T.GoldRule(),
        T.P("Beyond operational health, we assess strategic maturity across five capabilities on a 1-5 scale. Overall stage = minimum of the five.", { after: 180 }),
        new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [3000, 1360, 5000], rows: [headerRow, ...rows] }),
        T.P(" ", { after: 180 }),
        T.H2(`Overall stage: ${m.overall_stage} — ${m.overall_label}`),
        T.P(m.overall_narrative, { after: 240 }),
        T.Pbreak(),
    ];
}

function buildFindingsByDimension(input) {
    const out = [
        T.H1("Findings by dimension"),
        T.GoldRule(),
        T.P("Findings are organized by dimension and ranked by severity. Each finding includes documented evidence, business impact, a specific recommendation, and an effort/tier note.", { after: 180 }),
        T.P("Every dimension is evaluated in every audit. If a dimension was not audited in this pass, that is stated explicitly rather than skipped silently.", { after: 240 }),
    ];

    const dimensions = [
        { key: "data_health", label: "Data Health" },
        { key: "architecture", label: "Architecture" },
        { key: "adoption", label: "Adoption" },
        { key: "automation", label: "Automation" },
        { key: "integrations", label: "Integrations" },
        { key: "reporting", label: "Reporting" },
    ];

    for (const dim of dimensions) {
        out.push(T.H2(dim.label));
        const findings = (input.findings_by_dimension || {})[dim.key] || [];
        if (findings.length === 0) {
            const dimScore = (input.dimension_scores || {})[dim.key];
            if (dimScore === undefined || dimScore === null || dimScore === 0) {
                out.push(T.P(`The ${dim.label} dimension was not audited in this pass. It will be added in a subsequent phase or on request.`, { after: 180 }));
            } else {
                out.push(T.P(`No significant findings in ${dim.label}. Scored ${typeof dimScore === 'object' ? dimScore.score : dimScore}/100.`, { after: 180 }));
            }
            continue;
        }
        for (const f of findings) {
            out.push(...T.findingBlock(f.severity, f.title, f.evidence, f.impact, f.recommendation, f.effort_tier));
        }
    }
    out.push(T.Pbreak());
    return out;
}

function buildFeatureMatrix(input) {
    const fm = input.feature_matrix || {};
    const out = [
        T.H1("Feature utilization matrix"),
        T.GoldRule(),
        T.P("For each feature the portal's licensed tier makes available, the audit records whether it is configured, actively used, and used well. Green indicates healthy use; amber indicates partial use; red indicates available but unused; gray indicates an unknown status requiring manual confirmation.", { after: 120 }),
        T.P("This matrix directly translates to: here is what you are paying for that you are not yet getting.", { after: 240 }),
    ];

    const sections = [
        { key: "sales", label: "Sales Hub", headline_key: "sales_headline" },
        { key: "marketing", label: "Marketing Hub", headline_key: "marketing_headline" },
        { key: "service", label: "Service Hub", headline_key: "service_headline" },
        { key: "ops", label: "Operations Hub", headline_key: "ops_headline" },
        { key: "content", label: "Content Hub", headline_key: "content_headline" },
        { key: "commerce", label: "Commerce Hub", headline_key: "commerce_headline" },
        { key: "ai_breeze", label: "AI & Breeze features", headline_key: "ai_breeze_headline" },
        { key: "third_party_ai", label: "Third-party AI integrations", headline_key: "third_party_ai_headline" },
        { key: "conversation_intel", label: "Conversation & meeting intelligence", headline_key: "conversation_intel_headline" },
    ];

    let first = true;
    for (const sec of sections) {
        const features = fm[sec.key];
        if (!features || features.length === 0) continue;
        if (!first) out.push(T.Pbreak());
        out.push(T.H2(sec.label));
        out.push(T.featureMatrixTable(features));
        out.push(T.P(" ", { after: 120 }));
        const headline = (input.feature_matrix_headlines || {})[sec.key];
        if (headline) out.push(T.P(headline, { after: 240 }));
        first = false;
    }
    out.push(T.Pbreak());
    return out;
}

function buildRevEfficiency(input) {
    const re = input.revefficiency || {};
    const out = [
        T.H1("Revenue Efficiency Model — Cross-cutting analysis"),
        T.GoldRule(),
        T.P("This section reframes the dimensional findings already documented through the lens of Quantum's RevEfficiency Model — a philosophical ordering of revenue sources from warmest to coldest: KEEP your current clients first, then GROW inside those accounts, MULTIPLY through referrals, CONVERT warm leads, and finally EXPAND to net-new.", { after: 120 }),
        T.P("The analysis below uses the same findings reflected in the dimension scoreboard and feature matrix, reorganized by revenue motion. Each tier is scored 0-100 using the same computed rubric. Overall RevEfficiency = minimum of the five tiers.", { after: 240 }),

        T.H2("RevEfficiency scoreboard"),
    ];

    
    const tierHeader = new TableRow({
        tableHeader: true,
        children: [
            T.headerCell("Tier", 2000),
            T.headerCell("Score", 1200),
            T.headerCell("Band", 1200),
            T.headerCell("Observation", 4960),
        ]
    });
    const tierRows = ["KEEP", "GROW", "MULTIPLY", "CONVERT", "EXPAND"]
        .filter(t => re.tier_scores && re.tier_scores[t] !== undefined)
        .map(t => T.tierRow(t, re.tier_scores[t], null, (re.tier_observations || {})[t] || ""));
    out.push(new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [2000, 1200, 1200, 4960], rows: [tierHeader, ...tierRows] }));

    out.push(T.P(" ", { after: 180 }));
    out.push(T.Pmulti([
        T.Run(`Overall RevEfficiency: ${re.overall_score} of 100 — ${_bandLabel(re.overall_score)}.`, { bold: true, color: T.BRAND.NAVY, size: 24 }),
        T.Run(`  Limiting tier: ${re.limiting_tier}.`)
    ], { after: 180 }));

    if (re.interpretation) {
        out.push(T.P(re.interpretation, { after: 240 }));
    }

    // Per-tier narratives
    for (const tier of ["KEEP", "GROW", "MULTIPLY", "CONVERT", "EXPAND"]) {
        const narr = (re.tier_narratives || {})[tier];
        if (!narr) continue;
        out.push(T.Pbreak());
        out.push(T.H2(`${tier} tier — ${narr.heading || ""}`));
        if (narr.summary) out.push(T.P(narr.summary, { after: 120 }));
        for (const p of narr.paragraphs || []) {
            if (p.subheading) out.push(T.H3(p.subheading));
            if (p.body) out.push(T.P(p.body, { after: 180 }));
        }
    }

    if (re.q2_overlay) {
        out.push(T.Pbreak());
        out.push(T.H2("Quantum Q2 opportunity overlay"));
        out.push(T.P(re.q2_overlay.intro || "For clients who deploy the Q2 framework, the following Q2 packages directly address the RevEfficiency gaps identified above:", { after: 120 }));
        for (const entry of re.q2_overlay.packages || []) {
            out.push(T.Pmulti([
                T.Run(`${entry.name}: `, { bold: true, color: T.BRAND.NAVY }),
                T.Run(entry.addresses)
            ], { after: 100 }));
        }
        out.push(T.P(" ", { after: 240 }));
    }
    out.push(T.Pbreak());
    return out;
}

function buildRoadmap(input) {
    const r = input.roadmap || {};
    const out = [
        T.H1("Prioritized roadmap"),
        T.GoldRule(),
        T.P("Recommendations grouped into three horizons. Week 1 addresses quick wins resolving critical findings with minimal effort. Month 1 tackles high-impact enablers requiring a week or more. Quarter 1 scopes strategic investments.", { after: 240 }),
    ];
    if (r.week_1 && r.week_1.length) {
        out.push(T.H2("Week 1 — Quick wins"));
        out.push(T.roadmapTable(r.week_1));
        out.push(T.P(" ", { after: 180 }));
    }
    if (r.month_1 && r.month_1.length) {
        out.push(T.H2("Month 1 — High-impact fixes"));
        out.push(T.roadmapTable(r.month_1));
        out.push(T.P(" ", { after: 180 }));
    }
    if (r.quarter_1 && r.quarter_1.length) {
        out.push(T.H2("Quarter 1 — Strategic investments"));
        out.push(T.roadmapTable(r.quarter_1));
    }
    out.push(T.Pbreak());
    return out;
}

function buildAppendixA(input) {
    const a = input.appendix_a || {};
    return [
        T.H1("Appendix A: Methodology"),
        T.GoldRule(),
        T.P(a.overview || "Audit performed using read-only access to the portal. Queries ran against the HubSpot REST API. A list of what was audited and what was not appears below.", { after: 180 }),
        T.H2("What was audited"),
        T.P(a.audited || "", { after: 240 }),
        T.H2("What was not audited"),
        T.P(a.not_audited || "", { after: 240 }),
        T.H2("RevEfficiency Model audit methodology"),
        T.P(a.revefficiency_note || "For each of the 5 tiers (KEEP, GROW, MULTIPLY, CONVERT, EXPAND), the audit checks the presence of required structural elements: lists, properties, workflows, and integrations. Each missing element produces a deduction from a starting score of 100. Overall RevEfficiency = minimum of the five tier scores.", { after: 120 }),
        T.Pbreak(),
    ];
}

function buildAppendixD(input) {
    const d = input.appendix_d || {};
    const out = [
        T.H1("Appendix D: Score calculation detail"),
        T.GoldRule(),
        T.P("Every score traces to deductions from a starting score of 100. Rubric: Critical −15, High −8, Medium −3, Low −1 for findings; Critical −12, High −5, Medium −2, Low −1 for feature non-use (if Scored). Double-counting prevention: when a finding and a feature describe the same issue, only the finding deducts.", { after: 240 }),
        T.H2("Dimension scores"),
    ];

    const dimOrder = [
        { key: "data_health", label: "Data Health" },
        { key: "architecture", label: "Architecture" },
        { key: "adoption", label: "Adoption" },
        { key: "automation", label: "Automation" },
        { key: "integrations", label: "Integrations" },
        { key: "reporting", label: "Reporting" },
    ];
    let pageEscape = 0;
    for (const dim of dimOrder) {
        const rows = (d.dimension_deductions || {})[dim.key];
        if (!rows || rows.length === 0) continue;
        out.push(T.H3(dim.label));
        out.push(T.deductionTable(rows));
        out.push(T.P(" ", { after: 180 }));
        pageEscape++;
        if (pageEscape % 2 === 0) out.push(T.Pbreak());
    }

    out.push(T.H2("RevEfficiency Model tier scores"));
    const tierOrder = ["KEEP", "GROW", "MULTIPLY", "CONVERT", "EXPAND"];
    pageEscape = 0;
    for (const t of tierOrder) {
        const rows = (d.tier_deductions || {})[t];
        if (!rows || rows.length === 0) continue;
        out.push(T.H3(`${t} tier`));
        out.push(T.deductionTable(rows));
        out.push(T.P(" ", { after: 180 }));
        pageEscape++;
        if (pageEscape % 2 === 0) out.push(T.Pbreak());
    }
    return out;
}

function buildAppendixE(input) {
    const e = input.appendix_e || {};
    const out = [
        T.H1("Appendix E: Features available with tier upgrades"),
        T.GoldRule(),
        T.P("The following features are NOT in your current tier. They are documented here as upgrade opportunities — not as recommendations. Evaluate them against your business needs, not against QBS or HubSpot pressure.", { after: 240 }),
    ];
    for (const group of e.groups || []) {
        out.push(T.H2(group.title));
        out.push(T.lockedFeatureTable(group.rows));
        out.push(T.P(" ", { after: 180 }));
    }
    if (e.footer_note) {
        out.push(T.P(e.footer_note, { after: 120 }));
    }
    return out;
}

// ============================================================================
// HELPERS
// ============================================================================

function _bandLabel(score) {
    if (score >= 85) return "Healthy";
    if (score >= 70) return "Good";
    if (score >= 50) return "Degraded";
    if (score >= 30) return "Poor";
    return "Critical";
}

// ============================================================================
// MAIN
// ============================================================================

function buildAuditDoc(input) {
    const children = [
        ...buildExecSummary(input),
        ...buildHowToRead(input),
        ...buildScoreboard(input),
        ...buildMaturity(input),
        ...buildFindingsByDimension(input),
        ...buildFeatureMatrix(input),
        ...buildRevEfficiency(input),
        ...buildRoadmap(input),
        ...buildAppendixA(input),
        ...buildAppendixD(input),
        ...buildAppendixE(input),
    ];

    const doc = new Document({
        creator: "Quantum Business Solutions",
        title: `${input.client_name} — HubSpot Portal Audit`,
        description: "HubSpot Portal Audit by QBS",
        styles: T.STANDARD_STYLES,
        sections: [
            { properties: { page: T.STANDARD_PAGE }, children: T.buildCover(input.client_name, input.audit_date) },
            { properties: { page: T.STANDARD_PAGE }, footers: { default: T.standardFooter() }, children },
        ]
    });
    return doc;
}

async function main() {
    const inputPath = process.argv[2];
    const outputPath = process.argv[3];
    if (!inputPath || !outputPath) {
        console.error("Usage: node build_audit_docx.js <input.json> <output.docx>");
        process.exit(1);
    }
    const input = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
    const doc = buildAuditDoc(input);
    const buf = await Packer.toBuffer(doc);
    fs.writeFileSync(outputPath, buf);
    console.log(`Wrote: ${outputPath} (${buf.length} bytes)`);
}

if (require.main === module) {
    main().catch(e => { console.error(e); process.exit(1); });
}

module.exports = { buildAuditDoc };
