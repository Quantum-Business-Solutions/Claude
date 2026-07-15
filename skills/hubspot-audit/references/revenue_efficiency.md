# Revenue Efficiency Model Audit

A comprehensive evaluation of the portal's structural readiness to execute Quantum's 5-tier RevEfficiency Model: KEEP → GROW → MULTIPLY → CONVERT → EXPAND.

## Why this audit exists

The RevEfficiency Model is Quantum's philosophical foundation for revenue operations: **maximize revenue from the warmest sources first** (existing customers), then work outward to colder opportunities. A HubSpot portal that scores well on Data Health and Architecture but cannot execute the 5 tiers is a filing cabinet, not a revenue engine.

This audit evaluates whether the portal has the **structural ingredients** — lists, properties, workflows, custom objects, integrations, and dashboards — required to systematically execute each tier. It complements the existing dimensions (Data Health, Architecture, Adoption, Automation, Integrations, Reporting) with a **motion-focused** evaluation.

## Scoring

Each of the 5 tiers is scored 0–100 using the same computed rubric as other dimensions. Overall RevEfficiency score = **minimum** of the five tiers (the weakest tier caps the framework, consistent with the RevEfficiency philosophy — you can't skip tiers).

### Deduction structure

Starting 100 per tier. For each required structural element:

- **Not present (Critical)** — element entirely absent → −15
- **Partially present (High)** — element exists but incomplete → −8
- **Present but unpopulated** (Medium) — structure exists, no data → −5
- **Present and populated but unused** (Medium) → −3

Feature matrix entries that support a given tier inherit into that tier's score via the same "in-tier but not used well" rule.

---

## Tier 1 — KEEP (Retain current clients)

**Purpose.** Protect existing revenue. The foundation of RevEfficiency.

### Required structural elements

| Element | Detect via | Deduction if missing |
|---|---|---|
| QBR tracking (date property, next QBR date, QBR dashboard) | Property scan for `qbr_`, `next_review_date`, or similar | High (−8) |
| Upcoming lease-end / contract-end dates on Company or Deal | Custom property scan | Critical (−15) for dealer channel |
| NPS / CSAT / CES surveys active | Feature matrix SVH-05 | High (−8) if Service Pro+ |
| Check-in call cadence visible | List for "Customer, no activity in 90d" | High (−8) |
| Dormant customer detection | List for "Customer, no activity in 90+/180+ days" | Medium (−3) |
| Customer lifecycle stage distinct from Prospect stages | Lifecycle stage inventory | High (−8) |
| Renewal workflow triggered off lease-end date | Workflow scan | Critical (−15) if lease-end properties exist but no workflow |

### Per-vertical calibration

- **Office equipment dealers**: Lease-end date tracking is Critical, not High. Contract-end workflow is a baseline expectation.
- **MSPs**: Same logic with Contract renewal dates.
- **Professional services**: Dormant customer detection matters most.

### Quantum's Q2 KEEP packages to verify

- `[QBS] Company - Dormant Customer (90+ / 180+ days no activity)` — baseline
- `[QBS] Company - Customer with Open Deal / No Open Deal` — baseline
- QBR tracking properties on Company
- Lease-end / Contract-end custom object or properties

---

## Tier 2 — GROW (Expand inside current accounts)

**Purpose.** Increase wallet share. Cross-sell, upsell, re-sell motions.

### Required structural elements

| Element | Detect via | Deduction if missing |
|---|---|---|
| Cross-sell segmentation lists (by service line) | List name scan for "cross-sell", "upsell" | High (−8) |
| Product / service adoption property per customer | Property scan for product/service ownership fields | High (−8) |
| Upsell opportunity property (expansion-ready flag) | Property scan | Medium (−3) |
| Service-line associations on deals (multi-product visibility) | Deal property scan | Medium (−3) |
| Renewal → upsell conversion workflow | Workflow scan | High (−8) |
| GROW dashboard (cross-sell pipeline, expansion revenue) | Dashboard scan (manual) | Medium (−3) |

### Quantum's Q2 GROW-adjacent elements to verify

- Cross-sell lists by product line
- Upsell deal pipeline stages or dedicated pipeline
- Expansion Revenue tag on dealtype

---

## Tier 3 — MULTIPLY (Turn clients into multipliers)

**Purpose.** Leverage relationships for referral-driven growth.

### Required structural elements

| Element | Detect via | Deduction if missing |
|---|---|---|
| Referral source property (where did this lead come from a specific customer?) | Property scan | High (−8) |
| Former customer tracking (flagged when contact changes jobs) | Property scan for job-change tracking | Medium (−3) |
| LinkedIn integration (Sales Navigator) | Installed apps scan | Medium (−3) |
| Referral program list or property | List scan for "referral" | High (−8) |
| Referral source → deal attribution reporting | Reports scan | Medium (−3) |
| Champion / Promoter identification on contacts | Contact property scan | Medium (−3) |

---

## Tier 4 — CONVERT (Re-engage warm/missed opportunities)

**Purpose.** The largest tier. Recapture spend already invested in lead gen.

This tier has the highest weight in the RevEfficiency audit because it's where most portals leak the most revenue. The Sales Blitz playbook lists 17 discrete list types that should exist to execute this tier systematically.

### Required lists (presence check)

Weight: −2 per missing list, capped at −20. Plus auto-criticals for the most important ones.

| List | Weight | Notes |
|---|---|---|
| Stalled Deals (no activity 30/60/90d) | Auto-crit (−15) | Single most valuable list |
| Former Clients (win-back candidates) | High (−8) | |
| Past Meetings — No Deal | High (−8) | |
| Lost Deals (by reason, by competitor) | High (−8) | |
| Past Deals (all historical) | Medium (−3) | |
| MQLs (recent, not worked) | High (−8) | |
| SQLs (not yet converted) | Medium (−3) | |
| Form submissions (last 30/60/90d) | Medium (−3) | |
| Webinar attendees | Low (−1) | If webinars exist |
| Webinar registrants (didn't attend) | Low (−1) | If webinars exist |
| Contact Us inquiries | Medium (−3) | |
| Leads not contacted in 30/60/90 days | Auto-crit (−15) | Lead leakage indicator |
| Open Deals (active review) | High (−8) | |
| No follow-up 30/60/90 days | High (−8) | |
| Website visitor leads (intent) | Medium (−3) | Requires tracking code / ZoomInfo / Leadfeeder |
| Trade show attendees | Low (−1) | |
| Follow-ups (task-based) | Medium (−3) | |
| No-shows | Medium (−3) | |

### Workflow requirements

| Workflow | Weight | Notes |
|---|---|---|
| MQL → SQL handoff automation | High (−8) | |
| Lead reassignment on no-response | High (−8) | |
| Stalled deal alert to owner | High (−8) | |
| No-show re-engagement cadence | Medium (−3) | |
| Lost deal revisit (after 6 months) | Medium (−3) | |

### Quantum's Q2 CONVERT packages to verify

- `[QBS] Contact - No Activity 30/60/90 Days`
- `[QBS] Contact - Never Contacted, No Next Activity Scheduled`
- `[QBS] Deal - Past Due Close Date, Aged in Stage 30/60+ Days`
- `[QBS] Contact - Stuck in MQL 30+ Days, Stuck in SQL 60+ Days`
- `[QBS] Contact - Auto-advance Lifecycle on Form Submit` workflow

---

## Tier 5 — EXPAND (Go after net-new clients)

**Purpose.** Net-new logos matching ICP. The outermost tier.

### Required structural elements

| Element | Detect via | Deduction if missing |
|---|---|---|
| ICP property defined AND populated on >40% of customers | Property fill rate check | Critical (−15) if missing entirely |
| ICP Persona property (C-Suite, Facilities, IT, etc.) | Property scan | High (−8) |
| Buyer Persona property | Property scan | High (−8) |
| Target Accounts flag (ABM) | `hs_is_target_account` fill rate | High (−8) if not used |
| ZoomInfo integration (intent, scoops) | Installed apps | Medium (−3) if dealer channel without ZoomInfo |
| Net New Prospect pipeline stage | Pipeline stage scan | Medium (−3) |
| Net New dashboard | Dashboard scan (manual) | Medium (−3) |
| Persona trigger lists | List scan | High (−8) if personas defined but no lists |
| Intent-based lists (ZoomInfo intent topics) | List scan | Medium (−3) if ZoomInfo present |

### Quantum's Q2 EXPAND packages to verify

- Persona trigger lists (C-Suite, Facilities/Plant, HR/Safety, IT, Operations)
- ICP Fit Score workflows
- Target Accounts configuration
- ZoomInfo intent / scoops integration

---

## Aggregate RevEfficiency scoring

The final RevEfficiency assessment aggregates:

- **5 tier scores** (0–100 each)
- **Overall RevEfficiency score** = minimum of the five tiers
- **Limiting tier** = explicitly named
- **Tier completeness percentage** = number of required elements present / total required elements, per tier

### Presentation in the deliverable

A dedicated section appears right after the RevOps Maturity page and before the Feature Utilization Matrix. It includes:

1. **Overall RevEfficiency score** with one-sentence diagnosis
2. **Per-tier score bars** (similar to dimension scoreboard)
3. **Tier-by-tier structural check tables** — per tier, three columns: Element | Present? | Notes
4. **Quantum Q2 opportunity overlay** — where Q2 packages would fill gaps, annotated for tier
5. **Vertical calibration note** — for dealer-channel clients, calls out the specific elements that matter most for their vertical

### Why this produces client value

The RevEfficiency audit directly answers the question clients are really asking: **"Is my CRM set up to make me money?"** Traditional HubSpot audits answer "is your CRM healthy?" — a different (and less interesting) question.

By mapping every structural finding back to one of the 5 revenue tiers, the audit becomes a revenue-operations roadmap. Every recommendation is tied to a specific revenue motion — which makes it easier for the client to prioritize, to justify investment, and to measure results.

## Integration with existing audit

Findings in the RevEfficiency audit are **not separate** from findings in Data Health, Adoption, etc. They are **cross-referenced**:

- A missing "Stalled Deals list" is both a CONVERT tier gap AND an Architecture finding.
- Call Black Hole is both an Adoption finding AND a degradation of all 5 tiers (no calling = no execution).
- Missing buying roles affects Adoption AND every tier that involves deals (KEEP renewal calls, GROW cross-sell, CONVERT stalled deal recovery, EXPAND net-new pursuit).

Each finding is tagged with **all** relevant dimensions, and the calculation appendix shows the finding appearing in multiple rubrics — but **each finding is counted only once toward the overall score** (using the double-counting prevention rule).

---

## Implementation notes

### Detection flow

1. Run dimension audits as before (Phase 3)
2. In a new phase 3.5, after all dimension findings are collected:
   - For each of the 5 tiers, walk the required elements table
   - Mark each element as Present / Partial / Missing based on:
     - Feature matrix results (for tier-applicable features)
     - List presence checks (for required lists)
     - Property presence + fill rate checks (for required properties)
     - Workflow name/logic checks (for required workflows)
   - Compute per-tier score via deduction rubric
3. Render the RevEfficiency section in the deliverable

### API calls added

- `list_lists()` with full metadata (dynamic vs static, name patterns, membership counts) — already exists
- Property fill rate checks for tier-specific properties — already exists
- Workflow name pattern matching for tier-specific workflows — already exists (via `list_all_workflows()`)
- Installed apps scan (LinkedIn, ZoomInfo, Salesloft etc.) — NEW method needed

### Quantum-specific detection

If the portal has Quantum's Q2 framework deployed (indicated by `[QBS]` list name prefix and `[QBS]` workflow name prefix), the audit recognizes it and **credits the client for Q2 deployment** — presented as a strength rather than a missing element. Unique selling point: a Q2-deployed portal should score 90+ on RevEfficiency because the framework is designed exactly for this motion.

This creates an interesting secondary output: **which Q2 packages are deployed vs missing**, which is actionable for both existing Q2 clients (upgrade path) and new clients (what Q2 would unlock).
