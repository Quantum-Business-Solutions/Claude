# Deliverable Structure

Two modes. Pick based on Phase 2 decision.

## Guiding principle

This is a **universal HubSpot audit** covering data health, architecture, adoption, automation, integrations, and reporting. Every audit evaluates all six dimensions, catalogues feature utilization across every licensed hub, and assesses strategic maturity.

The Revenue Efficiency Model assessment is **one component** of the universal audit, not its centerpiece. It appears as a cross-cutting analysis that reframes the dimensional findings in terms of Quantum's 5-tier revenue motion model (KEEP → GROW → MULTIPLY → CONVERT → EXPAND). It supplements the dimensional audit, it does not replace it.

AI / Automation utilization is similarly a cross-cutting analysis layered into the Feature Utilization Matrix. It is comprehensive (Breeze + third-party + conversation intelligence) but does not dominate the document.

The spine of the document is the traditional six-dimension audit. Everything else supports it.

---

## Mode A: Internal Reconnaissance Brief

**Format:** Markdown, saved as `{client}_audit_recon_{YYYY-MM-DD}.md`.
**Audience:** Internal QBS (Shawn, delivery team, account owner).
**Tone:** Tight, blunt, honest. No client-softening language.
**Length:** 2–4 pages.

### Required sections

```markdown
# {Client Name} — HubSpot Recon
**Audited:** {date} | **Auditor:** Claude (via QBS skill)

## Portal at a glance
{one-paragraph Portal Profile: tier, scale, age, hubs}

## Health scorecard
{six-dimension scoreboard from scoring.md}
**Overall:** {score} — {band}. Limiting dimension: {name}.

## RevEfficiency snapshot
{five-tier scorecard: KEEP / GROW / MULTIPLY / CONVERT / EXPAND}
**Overall RevEfficiency:** {score}. Limiting tier: {name}.

## What's broken
**Critical:** {list of critical findings — title + one-line evidence}
**High:** {same, brief}

## Quick wins we should pitch
{3–5 items from the prioritization, framed as QBS service hooks}

## Strategic opportunities
{2–3 larger engagements worth a scoped proposal}

## Gotchas / blockers
{anything that would complicate cleanup: tier limits, dependencies, political issues}

## Tier upgrade analysis
{if applicable — what Hub/Tier upgrade unlocks what value}

## Recommended next step
{one of: scope cleanup SOW / discovery call / decline / propose retainer}
```

---

## Mode B: Client Deliverable (Word Doc)

**Format:** Word (.docx), branded, saved as `{client}_hubspot_audit_{YYYY-MM-DD}.docx`.
**Audience:** Client executive sponsor + operations owner.
**Tone:** Confident, specific, understated. No jargon without definition. No exclamation marks.
**Length:** 22–28 pages typical.

### Canonical section order

The order below is intentional. Universal audit content (scoreboard, maturity, findings, feature matrix) appears before cross-cutting analyses (RevEfficiency). The reader should finish the document understanding the portal's health first, and the revenue-motion lens second.

1. **Cover page** — Title, client name, date, "Prepared by Quantum Business Solutions"

2. **Executive Summary** (max 1 page)
   - Portal profile (one paragraph: contacts, companies, deals, tickets; tier; key hubs)
   - **Overall portal health score** (from dimension minimum) — the headline number
   - **RevEfficiency score** — the secondary number with limiting tier named
   - Top 3 risks (with business impact — drawn from Critical findings)
   - Top 3 opportunities (quick wins framed as business outcomes)
   - "What we recommend doing next" (one paragraph, one recommendation — usually: cleanup engagement sized at XX–XX hours)

3. **How to read this document** (half to one page)
   - Two views of portal health: dimensional (traditional audit) and RevEfficiency (motion-based)
   - How scores are computed (every score traceable to deductions in Appendix D)
   - Severity definitions (Critical / High / Medium / Low)
   - How the audit was conducted (Private App token, sampling, query dates)

4. **Health scoreboard** (1 page) — *dimensional view, the headline*
   - Six-dimension visual scoreboard (Data Health, Architecture, Adoption, Automation, Integrations, Reporting)
   - Overall = minimum; limiting dimension named
   - Brief narrative per dimension (3–4 sentences each with specific numbers)

5. **RevOps maturity positioning** (1–2 pages)
   - 5-capability stage table: Process & Operating Rhythm, Data Architecture & Hygiene, Technology & Integration Coverage, People & Adoption, Strategy / Measurement / Optimization
   - Overall stage = minimum; limiting capability named
   - One-sentence observation per capability

6. **Findings by dimension** (6 subsections, ~1–4 pages each) — *the core audit content*
   - One subsection per dimension, with all Critical/High/Medium findings under each
   - **Every dimension must be present in every audit:**
     - 6.1 Data Health findings (fill rates, duplicates, lifecycle hygiene, buying roles)
     - 6.2 Architecture findings (property sprawl, pipeline design, custom objects, tenancy)
     - 6.3 Adoption findings (active users, call logging, sequence use, workflow adoption, mobile)
     - 6.4 Automation findings (workflow inventory, error states, data hygiene automation, orphan workflows)
     - 6.5 Integrations findings (connected apps, data sync health, calling, inbox/calendar, AI stack)
     - 6.6 Reporting findings (dashboard inventory, Revenue Core 8 metrics, forecast accuracy, attribution model)
   - Each finding in structured format:
     - **Title** (bold)
     - **Severity** tag (Critical / High / Medium / Low)
     - **What we found** (evidence in plain language with specific numbers)
     - **Why it matters** (business impact)
     - **What we recommend** (specific fix)
     - **Effort and tier** (hours + tier requirement)

7. **Feature utilization matrix** (4–6 pages) — *the "what you're paying for vs. using" view*
   - Per-hub matrix tables, in this order:
     - 7.1 Sales Hub (SH-01 through SH-20 as applicable)
     - 7.2 Marketing Hub (MH-01 through MH-26 as applicable)
     - 7.3 Service Hub (SVH-01 through SVH-15 as applicable)
     - 7.4 Operations Hub (OH-01 through OH-08 as applicable)
     - 7.5 Content Hub (CH-01 through CH-10 as applicable, if Content licensed)
     - 7.6 Commerce Hub (CMH-01 through CMH-07 as applicable, if Commerce licensed)
     - 7.7 AI & Breeze features (BR-01 through BR-08)
     - 7.8 Third-party AI integrations (AI-01 Claude, AI-02 ChatGPT, etc.)
     - 7.9 Conversation & meeting intelligence (CI-01 Gong, CI-02 Chorus, CI-04 Zoom AI, etc.)
   - Each row: Feature | In your tier | Configured | Actively used | Used well | Notes
   - Color-coded status cells (green = yes, amber = partial, red = no, gray = unknown)
   - Short headline paragraph after each hub summarizing the utilization story

8. **Revenue Efficiency Model Assessment** (3–4 pages) — *cross-cutting analysis on top of findings*
   - Introductory paragraph explaining that this section reframes the dimensional findings through the lens of Quantum's 5-tier RevEfficiency Model
   - Five-tier scoreboard (KEEP / GROW / MULTIPLY / CONVERT / EXPAND)
   - Overall RevEfficiency = minimum; limiting tier named
   - Per-tier narrative (typically 1 paragraph per tier, longer for the limiting tier)
   - **Q2 package overlay** — for each tier gap, name the Q2 package that addresses it (Sales Activity Hygiene, Deal Pipeline Health, Lead Quality & Intent, Customer Lifecycle, etc.)
   - This section should feel like "here's another way to look at what we already told you" — not "here's new information"

9. **Prioritized roadmap** (2–3 pages)
   - **Week 1 — Quick wins** (table: item | effort | impact | tier requirement)
   - **Month 1 — High-impact fixes** (same table)
   - **Quarter 1 — Strategic investments** (same table)
   - Dependencies called out inline (e.g., "requires call capture activation first")

10. **Tier and investment analysis** (1–2 pages, only if recommending upgrades)
    - Current tier costs (approximate)
    - Recommended tier changes (per hub, per function)
    - Value unlock per upgrade

11. **Appendix A: Methodology** (1 page)
    - What was audited
    - Sampling strategy (500-record samples on fill rates, 2000 on duplicates, etc.)
    - What was not audited (e.g., Reporting deep dive, workflow action-level inspection, etc.)
    - RevEfficiency audit methodology note

12. **Appendix B: Query detail** (1–2 pages, optional)
    - Every finding citing a number traceable to a query
    - Date of query execution

13. **Appendix C: Glossary** (half page, optional, only if client is non-technical)

14. **Appendix D: Score calculation detail** (3–4 pages) — *required*
    - Per-dimension deduction tables (Data Health, Architecture, Adoption, Automation, Integrations, Reporting)
    - Per-tier deduction tables (KEEP, GROW, MULTIPLY, CONVERT, EXPAND)
    - Every score in the document traces to a row in this appendix
    - Source | Reason | Amount — with running total and final score per table

15. **Appendix E: Features available with tier upgrades** (1–2 pages) — *required*
    - Features NOT in the portal's current tier, by hub
    - Per feature: required tier, approximate cost, what it unlocks
    - Framed as "available when you're ready" — not aggressive upsell

### Writing style rules for client mode

- **Specific, not hedged:** "3.1% of contacts are duplicates" not "there are some duplicates."
- **Numbers, not adjectives:** "28 of 35 paid seats" not "most seats."
- **Active voice, second person:** "Your portal has..." not "The portal is found to have..."
- **Business language in impact:** "costs approximately $13K/year" not "is suboptimal."
- **No blame:** findings describe state, not who caused it. Even if obvious.
- **No ALL CAPS. No exclamation marks. No emoji.** QBS brand is understated.
- **Bullet points sparingly:** use prose where 2–3 sentences will do; reserve bullets for lists where 4+ parallel items exist.
- **One section per page-break-worthy unit:** prefer clear section starts over cramming.

### Branding requirements (see assets/brand.md)

- QBS dark navy (`#0A1F44`) for all headers
- QBS gold (`#C9A227`) for accent elements (rule lines, scoreboard bars)
- Sans-serif body (Calibri or similar)
- Footer on every page: "Quantum Business Solutions | Confidential" + page number
- No stock photography; no clipart

---

## Generating the Word file

The skill ships with reusable building blocks to ensure every audit output has the same shape:

- **`scripts/docx_templates.js`** — reusable Node module with all the visual helpers: `severityBadge()`, `scoreBar()`, `featureMatrixTable()`, `deductionTable()`, `tierRow()`, `maturityStageRow()`, `roadmapTable()`, `lockedFeatureTable()`, `findingBlock()`. Use these to guarantee visual consistency across audits.

- **`scripts/build_audit_docx.js`** — canonical audit generator. Takes a JSON audit input blob, produces the full Word doc in the canonical section order. This is the preferred path. Invoke as `node build_audit_docx.js <input.json> <output.docx>`.

- **`scripts/audit_input_example.json`** — example input blob demonstrating the JSON shape. Use as the starting point for a new audit — fill in the fields, run the generator.

### Workflow

1. Run all dimension audits (`references/data_health.md`, etc.) and collect findings
2. Run Phase 2.5 feature matrix detection (`scripts/hs_feature_detect.py` + `scripts/hs_extended_detect.py`)
3. Run Phase 3.5 RevEfficiency Model audit (`audit_revenue_efficiency()` in `hs_extended_detect.py`)
4. Populate the audit input JSON with all collected data
5. Run `build_audit_docx.js` against the JSON to produce the final Word file
6. Save to `/mnt/user-data/outputs/{client}_hubspot_audit_{YYYY-MM-DD}.docx`
7. Present with `present_files`

Custom sections or client-specific additions can be added by modifying the input JSON (e.g., adding extra findings) — the build script supports optional extension fields.

---

## What NOT to include

- HubSpot tool screenshots (they go stale; the data is in the queries)
- Long lectures on HubSpot best practices (reference links in appendix if needed)
- Recommendations that require software the client doesn't have (those go in Appendix E)
- Internal QBS pricing/SOW language (separate document via `sow-creator` skill)
- Any opinion stated without evidence
- "Supered" or any mention of QBS's internal deployment platform

---

## Sanity check before delivery

Before saving the final file, verify:

- [ ] All six dimensions are audited — none is empty or skipped (if reporting can't be audited, say so explicitly)
- [ ] Every finding has: evidence, impact, recommendation, effort, tier requirement
- [ ] Every number in the exec summary is traceable to a finding or feature matrix entry
- [ ] Overall health score and RevEfficiency score both appear in the exec summary
- [ ] Feature matrix includes all licensed hubs plus AI/Breeze + third-party AI + CI subsections
- [ ] RevEfficiency section includes all 5 tiers with per-tier narrative
- [ ] Quick wins in roadmap total <40 hours combined
- [ ] Critical findings appear in both the exec summary AND Findings section
- [ ] Appendix D has a deduction table for every dimension and every tier
- [ ] Appendix E has locked-feature tables for every hub not fully licensed
- [ ] No recommendation violates the portal's current tier without explicit upgrade note
- [ ] "Supered" appears nowhere
- [ ] Nothing reads as condescending or blaming
- [ ] The document reads as an audit with RevEfficiency inside it — not as a RevEfficiency report
