# Dimension 2: Architecture

Assesses whether the portal's structural decisions — object model, properties, pipelines, teams — scale or break under real use.

## Checks to run

### 2.1 Property sprawl (Contact)

**Query:** Total contact properties, count of custom properties, count with non-null values on <1% of records.

**Thresholds:**
- Healthy: <150 total contact properties, <80 custom
- Flag: 150–300 total, 80–180 custom
- Critical: >300 total OR >180 custom

**Also flag:** Any custom property with 0 fills on all records. Those are dead weight.

**Impact:** Property sprawl kills form design, list building, workflow enrollment logic, and reporting. Every admin adds properties, rarely removes them.

### 2.2 Property sprawl (Company)

**Thresholds:**
- Healthy: <100 total, <60 custom
- Flag: 100–200 total, 60–130 custom
- Critical: >200 total OR >130 custom

### 2.3 Property sprawl (Deal)

**Thresholds:**
- Healthy: <80 total, <40 custom
- Flag: 80–150 total, 40–90 custom
- Critical: >150 total OR >90 custom

### 2.4 Orphaned properties

**Query:** For each custom property, check whether it's referenced by any:
- Workflow (enrollment trigger or action)
- Active list (filter)
- Form field
- Saved report/dashboard
- Sequence

**Threshold:** Any custom property not referenced by any of the above AND with >10% fill rate is a candidate for deprecation. Any custom property with 0 fills AND no references should be deleted.

**Impact:** Dead properties pollute autocomplete in every admin surface. Slows down new admins, increases error rate.

### 2.5 Property naming consistency

**Query:** Sample custom properties, check for:

- Mixed case conventions (camelCase vs snake_case vs Title Case)
- Duplicate semantics (`customer_type`, `Customer Type`, `customerType`, `account_type`)
- Internal names exposed to users (properties with `_c_` or `temp_` prefixes in UI)
- HubSpot-reserved field names being shadowed by custom properties

**Threshold:** Any count of semantic duplicates is a finding. Report as list.

### 2.6 Pipeline fragmentation (Deal)

**Query:** Count deal pipelines, stages per pipeline, deals per pipeline.

**Thresholds:**
- Healthy: 2–4 pipelines, 5–8 stages each, >100 deals per pipeline in last 365d
- Flag: 5–7 pipelines OR any pipeline with <50 deals in 365d
- Critical: >7 pipelines OR pipelines with <10 deals (ghost pipelines)

**Anti-pattern:** One pipeline per rep. Instant red flag.

**Impact:** More than 4 pipelines is almost always broken reporting. Executives can't run one consolidated forecast.

### 2.7 Stage design (Deal)

**Query:** For each pipeline:
- Are stage probabilities set sensibly (monotonically increasing)?
- Any stages with 0 deals in last 180 days?
- Any stages with deals stuck >90 days on average?
- Ratio between stages — are there 1000 leads at Stage 1 and 5 at Stage 2? Broken stage definition.

**Threshold:** Report all anomalies.

### 2.8 Stage design (Ticket)

**Query:** Ticket pipelines and stages. Flag:
- Tickets routinely skipping stages (closure without progression)
- Stages with no SLA defined (Service Pro+)

### 2.9 Lifecycle stage definition

**Query:** Inspect the 10 standard lifecycle stages. Determine:
- Which are actually used (have >10 contacts)?
- Is there a custom lifecycle stage (Pro+)? If so, what's the logic for entry?
- Is there a documented definition for each stage?

**Finding:** If stages are in use but undefined/undocumented, that's a critical architecture gap — reps assign stages inconsistently.

### 2.10 Custom object design (if present)

**Query:** For each custom object:
- Primary display property set sensibly?
- Required properties defined?
- Associations to standard objects set up?
- Property count reasonable (<50)?

### 2.11 Team and permissions structure

**Query:** Fetch teams (Enterprise) or user permission sets.

**Flag:**
- Flat structure on a 30+ seat portal (missing team hierarchies)
- Super admin count >5
- Users with admin access who shouldn't have it (sales reps as super admin)
- Deactivated users still owning active records

### 2.12 Record ownership distribution

**Query:** Count of active records by owner, across Contacts, Companies, Deals.

**Flag:**
- Bulk ownership concentration (one user owns >40% of contacts) — departure risk
- Deactivated users still owning records
- Records with no owner

### 2.13 Custom properties not surfaced in records

**Query:** Custom properties that exist but aren't on the default record card or any record sidebar layout.

**Finding:** Properties admins can't see without clicking into property settings. Usually indicates half-finished integration or migration.

### 2.14 Association labels usage

**Query:** On Contact↔Company and Deal↔Contact associations, are custom association labels defined (Pro+)?

**Finding:** Portals using generic "Primary" / no labels when they have multi-stakeholder B2B deals are missing a foundational reporting capability.

### 2.15 Target Accounts configuration (ABM)

**Query:** HubSpot's Target Accounts feature (Sales Pro+) flags specific Company records as target accounts with buying roles, tier, and account-based workflows. Check:

- Is Target Accounts enabled in the portal?
- How many companies are flagged as Target Accounts?
- Is a target account tier property in use (Strategic / Core / Stretch, or Tier 1/2/3)?
- Are buying roles being applied at the account level on target accounts?
- Do target accounts have documented account plans or notes?
- Is there an "Open and target accounts without activity" dashboard or workflow?

**Thresholds:**
- Healthy: Target Accounts enabled, 50–300 flagged accounts (not too few, not the whole database), tiering used, buying roles populated on 60%+ of target account contacts
- Flag: Enabled but underused — <50 flagged, no tiering, no buying roles
- Critical: Enabled but >1000 companies flagged (no discipline = not target accounts, just a list), OR enabled with <10 flagged (paying for feature that's dormant)

**Finding variants:**
- "Target Accounts feature is disabled" → tier-upgrade opportunity or enablement gap
- "Target Accounts enabled but every company is flagged" → ABM theater, no actual discipline (see anti-pattern AP-17)
- "Target Accounts enabled, 120 flagged, but no dashboards or workflows reference them" → configured but not operationalized

### 2.16 ICP definition and structural integration

**Query:** Beyond the ICP property fill check (Data Health 1.15), assess whether ICP is *structurally* integrated:

- Is ICP defined as a formal custom property with enumerated tier values, or is it informal (text field, picklist abuse)?
- Does the ICP definition have a documented rubric (revenue band, industry, employee count, tech stack signals)?
- Is ICP tier auto-calculated via a workflow based on firmographic properties, or set manually?
- Does HubSpot's Fit Score (AI-based, Pro+) exist and how does it correlate with the client's ICP property?
- Is there an "ICP + Target Account" intersection view/list?

**Thresholds:**
- Healthy: formal ICP property with 3–4 tiers, documented rubric, automated tier assignment via workflow using firmographics, ICP referenced in lead scoring and routing
- Flag: ICP property exists but manually maintained, no rubric, or inconsistent with Fit Score
- Critical: No ICP concept in the portal at all, OR ICP property exists but definitions are tribal knowledge only

**Impact:** Without structural ICP, marketing spends on the wrong accounts, reps work unqualified leads, and leadership can't report revenue by ICP fit. This is upstream of almost every sales/marketing efficiency metric.

### 2.17 Lists audit

Lists are where HubSpot portals quietly accumulate chaos. Every marketer, SDR, and admin builds them; almost no one retires them. A mature portal has list discipline; an immature portal has hundreds of lists with unknown owners and unknown purposes.

**Query:**

- Total lists (active + static), split
- Lists by age: created last 30d / 90d / 365d / older
- Lists used as workflow enrollment triggers (active dependency)
- Lists used as email recipients in last 90 days (active dependency)
- Lists used as report filters (active dependency)
- Lists with zero dependencies (orphan candidates)
- Lists with zero records (empty and irrelevant)
- Active lists with filter logic that hasn't re-evaluated in 30+ days (broken criteria)
- Lists named with unhelpful/ambiguous names ("Test", "copy of copy", "Untitled", "Brad's list", dates with no context)
- Lists owned by deactivated users
- Nested list reference chains >3 levels deep (hard to maintain)
- Contact list sizes approaching list-size tier limits

**Thresholds:**
- Healthy: <150 total lists, <15% orphans, naming conventions visible, owners active, zero empty lists older than 90 days
- Flag: 150–500 lists OR 15–35% orphans OR unclear naming
- Critical: >500 lists OR >35% orphans OR >50 lists owned by deactivated users (ghost ownership)

**Anti-patterns specific to lists:**

1. **Naming cemetery:** lists named "list 1", "list copy", "Copy of Active Customers (3)", "brad test 5/12" → nobody knows what they do
2. **Stale static lists used as active segmentation:** marketer created a static list in January, emails every contact on it monthly, list is never refreshed → dead contacts, bounced emails, reputation hit
3. **List-of-lists workflows:** workflows enroll based on "member of list A and member of list B and not member of list C" where those lists are themselves built on lists → impossible to trace
4. **Ghost owner lists:** former employees own dozens of lists that were never reassigned; when the user was deactivated, the lists silently stopped being maintained
5. **List duplication:** five lists that all try to mean "active customers" with slightly different criteria; reports built on any one of them disagree with each other

**Impact:** List sprawl silently corrupts segmentation logic, breaks marketing emails, bloats suppression complexity, and makes it impossible to answer "who are we emailing today." A 500-list portal is a portal where marketing execution is a guess. Also costs admin time — every new campaign requires navigating the graveyard.

**Recommendation format:**

- Archive all lists with zero dependencies AND zero records → 30-day retention → delete
- Archive lists owned by deactivated users → reassign or delete
- Rename all active lists to follow convention: `{purpose}_{audience}_{owner-initials}_{YYYY-MM}`
- Consolidate duplicate lists; update dependent workflows/emails/reports
- Establish quarterly list review cadence

**Effort:** Days for cleanup, hours per quarter for ongoing governance. Effort scales linearly with list count; a 1000-list portal is a multi-week project.

### 2.18 Sales methodology structural embedding

**Query:** Determine which sales methodology the client claims to run (MEDDIC, MEDDPICC, BANT, SPIN, Sandler, Challenger, Value Selling, or a custom framework like QBS 5 C's), then check whether it's actually embedded in the portal's structure.

Signals of embedded methodology:
- Custom properties on Deal object matching methodology fields (e.g., `metrics`, `economic_buyer`, `decision_criteria`, `decision_process`, `identified_pain`, `champion`, `competition` for MEDDIC; `budget`, `authority`, `need`, `timeline` for BANT; `spin_situation`, `spin_problem`, `spin_implication`, `spin_need_payoff` for SPIN)
- Deal stage gating that references methodology criteria (e.g., can't move to "Proposal" without Economic Buyer identified)
- Playbooks in HubSpot (Sales Pro+) explicitly referencing the methodology
- Deal scoring that uses methodology field completeness
- Manager review views filtered by methodology field completeness
- Training artifacts in the portal referencing the methodology

**Thresholds:**
- Healthy: Methodology named by leadership, embedded as required Deal properties, referenced in playbooks, stage gating enforces capture
- Flag: Methodology named but partially embedded (some properties exist, not used consistently)
- Critical: Methodology claimed by leadership but zero structural evidence in the portal — reps run it "in their head" if at all

**Impact:** A sales methodology that isn't embedded in the CRM is a slogan, not a practice. Manager coaching becomes opinion-based. New rep ramp time doubles because there's no structural scaffolding. Deal reviews surface gaps too late. If leadership says "we sell with MEDDIC" but HubSpot has no Economic Buyer field, it's not being done.

**Recommendation:** Embed methodology as required Deal properties with stage gating. Add fields to the record sidebar default layout so reps see them. Build a "Deal Health" view filtering on methodology completeness. Require methodology fields to be filled before stage progression past qualification.

### 2.19 Sales-marketing alignment structures

**Query:** Look for structural evidence of sales-marketing alignment (or its absence):

- Documented MQL criteria in a knowledge base article or pinned document
- SLA agreement captured somewhere in the portal (document, note on a specific "SLA" record, wiki)
- Shared dashboard explicitly titled as joint sales/marketing
- Recurring meeting invites for sales-marketing sync (calendar integration artifacts)
- A lead recycling / return-to-marketing workflow (sales can reject MQLs back to marketing)
- Marketing-sourced pipeline reported distinct from sales-sourced
- Lead status property distinct from lifecycle stage (MQL → "Contacted" → "Qualified" → "Disqualified" with reason codes)

**Thresholds:**
- Healthy: MQL definition documented, SLA exists, joint dashboard reviewed by both teams, lead recycling motion active
- Flag: Some structural evidence but partial (definition exists but no SLA, or joint dashboard but no recycling)
- Critical: Zero structural evidence of alignment — marketing throws leads over the wall, sales complains about quality, neither has shared data

**Impact:** Without structural alignment, sales and marketing fight. Marketing delivers MQLs sales rejects as garbage. Sales closes deals marketing gets no credit for. Leadership receives contradictory reports. Finding resolves itself only when the CRM enforces shared definitions.

## Dealer-channel-specific checks

- **Service contract → Company association:** should be 1:N (one company, many contracts). Flag if association is reversed or missing.
- **Equipment → Service contract association:** should exist. Flag orphan equipment.
- **Location/Site object present?** Multi-location dealers without a Location object can't do per-site reporting.

## Output format

Same structure as Data Health. Specific example:

```yaml
- id: architecture_01_contact_property_sprawl
  dimension: architecture
  severity: high
  title: "Contact property sprawl with 47% dead weight"
  evidence: "287 contact properties total, 184 custom; 86 custom properties have 0 fills and no workflow/list/form/report references"
  impact: "Slows form and workflow building; increases admin error rate; makes new rep onboarding harder"
  recommendation: "Deprecate 86 orphan properties in 30-day archive → delete cycle. Establish property governance process before adding new properties."
  effort: days
  tier_requirement: none
```
