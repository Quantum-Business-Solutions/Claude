---
name: hubspot-audit
description: Conduct a structured audit of a HubSpot portal across six dimensions (data health, architecture, adoption, automation, integrations, reporting) using live HubSpot MCP queries, OR produce a time-bounded build activity digest showing what was created/modified in the last 7/30/90 days. Use for audits whenever the user wants to audit, assess, review, score, benchmark, or evaluate a HubSpot portal — for QBS clients, new prospects, or internal portals. Also use for activity digests — phrases like "what's been built recently," "monthly build report," "track our team's work," "what changed since a date," "weekly activity summary," or "quarterly digest." Also trigger on "run diagnostics," "what's wrong with this HubSpot," "health check," "taking over a new portal," "scope the cleanup work," duplicates, property sprawl, workflow errors, adoption gaps. Produces internal recon brief, polished QBS-branded Word deliverable, or time-scoped activity digest.
---

# HubSpot Portal Audit

A structured, opinionated audit skill for QBS. Two top-level capabilities:

1. **Audit mode** — 7-phase assessment producing a scored diagnosis across six dimensions plus RevOps maturity staging. Use when the goal is "what's the state of this portal."
2. **Activity digest mode** — time-bounded view of what's been built/modified in the portal. Use when the goal is "what's changed recently" (weekly team reviews, monthly client reports, engagement handoff docs).

Decide which mode applies from the user's request before doing anything else. If both are requested, run them as separate outputs.

For audit mode, continue reading below. For digest mode, go directly to `references/activity_digest.md`.

## Core principles

Three things separate this audit from a generic checklist. All three are non-negotiable:

1. **Quantitative thresholds, not vibes.** Every finding is backed by a specific query result and a specific threshold. "42% of contacts missing source attribution" — not "lots of contacts look bad."
2. **Business-impact translation.** Every finding has a mandatory *so-what* field: revenue leakage, rep time wasted, marketing spend inefficiency, or compliance risk. Technical findings without business framing are deleted before delivery.
3. **Portal-aware scoping.** Do not audit a Starter portal with Enterprise criteria. The audit adapts to hubs, tiers, object model, and portal age detected in Step 1.

## The workflow

The audit runs in seven phases. Always execute them in order — later phases depend on scoping data from Phase 1.

### Phase 1 — Scope detection (required first)

Before auditing anything, introspect the portal to establish context. Read `references/scoping.md` for the full query list. At minimum, determine:

- Hubs present and their tiers (Sales/Marketing/Service/Ops/Content/Commerce × Starter/Pro/Enterprise)
- Seat counts and user distribution across teams
- Object model: standard objects plus any custom objects, and rough record counts for each
- Portal age and growth trajectory (creation date, records created last 90d)
- Connected integrations (app marketplace + native)
- For dealer-channel clients: check for custom objects like `service_contracts`, `equipment`, `meter_reads`, or `opportunities` that signal their ops model

Output of this phase is a **Portal Profile** used to calibrate every downstream threshold. Do not proceed without it.

**Access mode selection** — also part of Phase 1. See `references/access_modes.md`. The skill supports two ways to reach a portal:

1. **HubSpot MCP** — quick, no setup, best for Phase 1 scoping and any interactive queries
2. **Private App token (a.k.a. service key)** — required for volume-heavy checks in Phases 3–6 (full workflow inventory, property fill rates at scale, list inventory with dependencies, engagement aggregations, audit log access)

Before moving to Phase 3, ask: "Do we have a Private App token for this portal, or should we create one?" If yes, use the Python helper at `scripts/hs_client.py` for volume queries. If no, run in MCP-only mode and flag which checks couldn't run at full depth — document the gaps in the deliverable's Appendix A.

### Phase 2 — Confirm mode and scope with user

Two modes:

- **Internal recon** — markdown brief, ~30 min of work, no branding, findings in bullet form. For sizing a new portal before a sales call or scoping cleanup work.
- **Client deliverable** — QBS-branded Word doc (navy/gold), ~2 hrs of work, full executive summary, per-dimension findings, prioritized roadmap, appendix. For delivery to a paying client.

Also confirm scope: all six dimensions, or a subset? If the user hasn't specified, default to all six for client mode, and ask for confirmation for internal mode.

### Phase 2.5 — Feature Utilization Discovery (required for comprehensive audits)

Before running the dimension audits, produce the **feature utilization matrix** — one row per HubSpot feature the portal's licensed tier makes available. For each feature, capture: in-tier / configured / actively used / used well / notes.

Driven by `references/feature_matrix.md` and implemented via `scripts/hs_feature_detect.py`. The matrix is then used for two purposes:

1. **Visibility asset** — the client sees a per-hub grid of every feature they're paying for vs. using, with utilization status. This is the most valuable single artifact of the audit for most portfolios.
2. **Scoring input** — "Scored" features from the matrix contribute to dimension scores via the rubric in `references/scoring.md`. "Visibility" features do not contribute to scoring but appear in the matrix.

**Locked features** (features NOT in the portal's tier) are documented separately and surfaced in Appendix E of the deliverable as upgrade opportunities — subtle, not cluttering the main matrix.

### Phase 3 — Run the six dimension audits

Run through Data Health, Architecture, Adoption, Automation, Integrations, Reporting — each guided by its respective reference file. Each dimension audit produces a list of findings with evidence and severity.

### Phase 3.5 — Revenue Efficiency Model tier audit (cross-cutting analysis)

After dimension findings are collected, run the 5-tier RevEfficiency audit guided by `references/revenue_efficiency.md`. This evaluates whether the portal is structurally ready to execute each tier of Quantum's RevEfficiency Model (KEEP → GROW → MULTIPLY → CONVERT → EXPAND). Use `scripts/hs_extended_detect.py` `audit_revenue_efficiency()` to run the checks programmatically.

**Important:** the RevEfficiency Model is a cross-cutting analysis layered on top of the traditional six-dimension audit — it is **not a replacement for the dimensional audit**. In the final deliverable, RevEfficiency appears *after* the Findings by Dimension section and the Feature Utilization Matrix. The universal audit (data health, architecture, adoption, automation, integrations, reporting) is the spine of the document; RevEfficiency supplements it.

For Q2-deployed portals, this audit doubles as a Q2 package gap analysis — the Q2 overlay subsection in the deliverable maps each RevEfficiency gap to the Q2 package that addresses it.

### Phase 5 — Generate the deliverable

The skill ships with a canonical document generator (`scripts/build_audit_docx.js`) that consumes a standardized JSON input and produces a consistently-shaped Word doc. Using this generator is the **preferred path** — it guarantees every audit has the same sections in the same order with the same formatting.

Workflow:
1. Collect all audit data (dimension findings, feature matrix, RevEfficiency tiers, roadmap, appendices)
2. Populate the audit input JSON following the shape in `scripts/audit_input_example.json`
3. Run: `node scripts/build_audit_docx.js <your_input.json> /mnt/user-data/outputs/{client}_hubspot_audit_{date}.docx`
4. Validate the output via the docx validator
5. Present the file using the `present_files` tool

Custom per-client additions (extra findings, client-specific observations) can be added directly to the JSON input — the build script is data-driven, so the shape stays consistent while content varies per audit.

Each dimension has its own reference file with queries, thresholds, and anti-pattern checks. Run them in this order — earlier dimensions inform later ones (e.g., property sprawl affects workflow audit interpretation):

1. **Data health** → `references/data_health.md`
2. **Architecture** → `references/architecture.md`
3. **Adoption** → `references/adoption.md`
4. **Automation** → `references/automation.md`
5. **Integrations** → `references/integrations.md`
6. **Reporting & attribution** → `references/reporting.md`

For each dimension, produce a structured findings list. Each finding must have:

```
- id: short-slug
- dimension: data_health | architecture | ...
- severity: critical | high | medium | low
- title: one line
- evidence: the specific query result or count
- impact: the so-what (revenue, time, risk)
- recommendation: what to fix
- effort: hours | days | weeks
- tier_requirement: none | Pro | Enterprise | Ops Hub | etc.
```

**Sampling:** On large portals (>50K contacts or >10K companies), do not enumerate every record. See `references/scoping.md` for the stratified sampling approach.

**Anti-pattern catalog:** After running dimension-specific checks, cross-reference `references/anti_patterns.md` for known multi-dimension issues (e.g., the Zoom + Read AI engagement duplication pattern spans integrations and data health).

### Phase 4 — Score each dimension (computed, not asserted)

For each of the six dimensions, score 0–100 using the **computed rubric** in `references/scoring.md`. Scores are NOT assigned by judgment — they are calculated by:

1. Starting at 100
2. Deducting per finding severity (Critical −15, High −8, Medium −3, Low −1)
3. Deducting per feature matrix non-use (Scored features only; Critical −12, High −5, Medium −2, Low −1)
4. Capping total deductions at −100, flooring score at 0

Every deduction must be logged with its source (finding ID or feature ID) so Appendix D of the deliverable can display the full calculation detail. This is what makes scores defensible under client scrutiny.

Overall score = **minimum** of the six dimension scores (not average). Explicitly name the limiting dimension.

### Phase 5 — Prioritize findings

Rank all findings on a 2×2 of impact × effort. Produce three explicit lists:

- **Quick wins** — high impact, hours of effort (include these in week 1 of any engagement)
- **High-impact fixes** — high impact, days to a week of effort
- **Strategic rebuilds** — high impact, multi-week — architecture or tier-upgrade dependent

Low-impact items go in the appendix but are not promoted to the summary.

### Phase 6 — Synthesize executive summary

The exec summary has four required elements:

1. **Portal profile** — one sentence of what was audited (tier, scale, age).
2. **Overall health** — the minimum dimension score, with a one-sentence diagnosis.
3. **Top 3 risks** — from the critical/high findings, pick the three that most threaten revenue or compliance.
4. **Top 3 opportunities** — from quick wins, pick the three with highest impact-per-hour.

Keep it to one page. Every sentence earns its space.

### Phase 6.5 — RevOps Maturity Assessment

After scoring and prioritizing, assign a **RevOps maturity stage** (1–5) to each of five capabilities: Process & Operating Rhythm, Data Architecture & Hygiene, Technology & Integration Coverage, People & Adoption, and Strategy & Measurement.

See `references/revops_maturity.md` for the full 5×5 stage criteria.

Overall maturity = minimum of the five capability stages (same philosophy as dimension scoring — the weakest link determines the strategic level).

Produce an **upgrade path** for each capability below the target stage (typically Stage 3 or 4): what findings block the next stage, what effort is required, what business value unlocks. This transforms the deliverable from a findings report into a positioning document with a natural engagement scope.

### Phase 7 — Produce the deliverable

See `references/deliverable.md` for the output structure of each mode. For client mode, use the `docx` skill (located at `/mnt/skills/public/docx/SKILL.md`) to produce the Word file, following QBS brand guidelines in `assets/brand.md`.

Save all artifacts to `/mnt/user-data/outputs/` and present with `present_files`.

## Known anti-patterns to always check

Across 55+ portals, certain issues recur. Always check for these regardless of dimension:

- **Dual-engagement logging** — Zoom + Read AI (or Gong + Chorus, or any two meeting tools) both writing engagement records → duplicate activities inflating rep stats
- **Engagement capture gap** — reps missing inbox/calendar/dialer/meeting-transcription integrations, creating silent logging blind spots that undermine every activity-based report
- **ABM theater** — Target Accounts feature enabled but no differentiated activity, sequences, or reporting; looks like ABM, isn't
- **ICP shelfware** — ICP property defined but not operationalized into routing, sequences, views, or reports
- **Methodology theater** — sales methodology (MEDDIC, Challenger, etc.) claimed by leadership but structurally absent from the CRM; reps "run it in their heads" at best
- **Win/loss amnesia** — deals closing without structured reasons or competitor capture; year of loss data sitting unused; no feedback loop to marketing/product
- **Commission data gap** — owner instability, split informality, close-date drift, or missing revenue segmentation that would break commission calculation if automated
- **List graveyard** — hundreds of lists with no governance, many orphaned or owned by deactivated users, breaking marketing segmentation and workflow enrollment
- **Lead leakage** — MQLs untouched at 7+ days, slow time-to-first-touch, no reassignment automation, reps disposing leads without activity
- **Deal push syndrome** — open deals pushed 2+ times, stalled with no activity 14+ days, no next step, forecast unreliability
- **Call black hole** — calls happening on personal cell phones or unintegrated dialers, never reaching HubSpot; coaching and forecasting impossible
- **Single-threaded deals** — open pipeline with no Decision Maker identified via buying role, especially at deal sizes where multi-threading is mandatory
- **Lifecycle stage regression** — reps manually moving stages backward, breaking funnel reporting
- **Sequence enrollment without exit criteria** — contacts stuck in sequences after conversion, causing email spam and unsubscribes
- **Workflow re-enrollment loops** — especially on property-change triggers with goal properties that fire on re-enroll
- **Property sprawl on contacts** — portals with 300+ contact properties where <40 are actually used
- **Marketing contacts bloat** — tier ceiling approaching or breached, driving unexpected invoice spikes
- **Orphaned dashboards** — dozens of custom reports with zero views in 30 days
- **Pipeline fragmentation** — 8+ deal pipelines where 2–3 would suffice, killing reporting
- **Form hidden-field overwrites** — forms silently overwriting contact properties with stale defaults
- **No source attribution** — "Original Source" null for 15%+ of recent contacts

Full catalog with queries in `references/anti_patterns.md`.

## Output conventions

- Every number in the deliverable must be traceable to a specific query. Keep the queries in the appendix.
- Never recommend a feature the portal's tier doesn't support. If a finding requires a tier upgrade, say so explicitly and quantify the cost/benefit.
- For dealer-channel clients (office equipment, managed IT), frame findings in their language: deals = opportunities, service contracts, MRR/ARR for managed services, meter reads, parts/supplies attach rate.
- Do not use ALL-CAPS headers or exclamation marks in client deliverables. QBS voice is confident, specific, and understated.

## When things are ambiguous

- If a dimension can't be audited (e.g., no access to a specific hub), note it explicitly in findings as a gap rather than skipping silently.
- If a finding's severity is unclear, err toward lower severity — over-calling severity erodes credibility.
- If the user's portal looks fundamentally healthy, say so. A clean audit is a legitimate outcome and worth charging for.

## Reference files

- `references/access_modes.md` — MCP vs. Private App token (service key): when to use each, scopes, security
- `references/scoping.md` — Phase 1 portal detection queries and sampling strategy
- `references/feature_matrix.md` — Phase 2.5 master catalog of ~100 features across 7 hubs with tier/detection/scoring weight
- `references/data_health.md` — Dimension 1 audit
- `references/architecture.md` — Dimension 2 audit
- `references/adoption.md` — Dimension 3 audit
- `references/automation.md` — Dimension 4 audit
- `references/integrations.md` — Dimension 5 audit
- `references/reporting.md` — Dimension 6 audit
- `references/anti_patterns.md` — Cross-dimension anti-pattern catalog
- `references/scoring.md` — Computed 0–100 rubric per dimension, with traceable deduction detail
- `references/revops_maturity.md` — 5-stage RevOps maturity model (capstone)
- `references/revenue_efficiency.md` — RevEfficiency Model 5-tier audit (KEEP/GROW/MULTIPLY/CONVERT/EXPAND) based on Quantum's Sales Blitz playbook
- `references/ai_utilization.md` — Comprehensive AI & Automation audit catalog (Breeze, Claude, ChatGPT, Gong, Fireflies, Zoom AI, conversation intelligence)
- `references/deliverable.md` — Output structure for both audit modes
- `references/activity_digest.md` — Standalone mode: time-bounded build activity digest (7/30/90 days)
- `scripts/hs_client.py` — Python client for Private App token queries (import as `from hs_client import HubSpotAuditClient`)
- `scripts/hs_feature_detect.py` — Feature matrix detection module (import as `from hs_feature_detect import detect_all_features, compute_feature_deductions`)
- `scripts/hs_extended_detect.py` — Extended detection: sequences, playbooks, forecast, templates, marketing emails, landing pages, KB, social posts, ad campaigns, AI/Breeze features, conversation intelligence, plus the 5-tier RevEfficiency audit (import as `from hs_extended_detect import run_extended_detection`)
- `scripts/docx_templates.js` — Reusable Word document formatting helpers (Node.js module). Exports `severityBadge`, `scoreBar`, `featureMatrixTable`, `deductionTable`, `tierRow`, `maturityStageRow`, `roadmapTable`, `lockedFeatureTable`, `findingBlock`, `buildCover`, and all brand tokens. Guarantees visual consistency across every audit run.
- `scripts/build_audit_docx.js` — Canonical audit document generator. Takes a JSON audit input and produces the full Word doc in the canonical section order. Invoke as `node build_audit_docx.js <input.json> <output.docx>`. This is the preferred path for producing the client deliverable.
- `scripts/audit_input_example.json` — Example input blob (SMP Security audit, v4). Use as starting point for new audits — copy, fill in the fields, run the generator.
- `assets/brand.md` — QBS brand guidelines for Word output
