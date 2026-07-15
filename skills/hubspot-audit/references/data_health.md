# Dimension 1: Data Health

Assesses the integrity, completeness, and freshness of CRM data. Most audits find the highest density of critical findings here.

## Checks to run

### 1.1 Duplicate contacts (by email)

**Query:** Group contacts by `email` where email is not null, count groups with 2+ records.

**Thresholds:**
- Healthy: <1% of contact base
- Flag: 1–3%
- Critical: >3%

**Anti-pattern to detect:** Duplicates concentrated in records created by imports or specific integrations (LinkedIn Sales Nav, ZoomInfo sync, webform submissions). If so, the problem is upstream, not the existing duplicates.

**Impact framing:** At 3% dupe rate on 100K contacts = 3,000 duplicate records. Assuming 10% are active leads, that's ~300 reps working the same person. At 30 min of rep time per duplicate lead, that's 150 hours of wasted capacity.

### 1.2 Duplicate companies (by domain)

**Query:** Group companies by `domain` where domain is not null, count groups with 2+ records.

**Thresholds:**
- Healthy: <2%
- Flag: 2–5%
- Critical: >5%

**Special case:** Subsidiaries and multi-location parents legitimately share domains. Do not treat as dupes if the company records have different `name` values AND one has a parent-child association.

### 1.3 Duplicate companies (fuzzy name match)

**Query:** Sample 1,000 companies, apply Levenshtein or normalized-token comparison on `name` field (strip "Inc", "LLC", "Corporation", etc.).

**Thresholds:** Report as list, not percentage. Any portal with >50 fuzzy matches at 85%+ similarity is a flag.

**Note:** This is the POA/OMD-style problem Shawn has handled with Python fuzzy matching — may warrant a separate dedupe project rather than inline fix.

### 1.4 Lifecycle stage completeness

**Query:** Count contacts where `lifecyclestage` is null or empty.

**Thresholds:**
- Healthy: <10%
- Flag: 10–25%
- Critical: >25%

**Impact:** Null lifecycle stage breaks the entire funnel report. Every null contact is invisible in lead → MQL → SQL conversion metrics.

### 1.5 Original Source completeness

**Query:** Count contacts created in last 365 days where `hs_analytics_source` is null, "OFFLINE" with no sub-source, or "DIRECT_TRAFFIC" (often means tracking wasn't loaded).

**Thresholds:**
- Healthy: <15% unknown
- Flag: 15–30%
- Critical: >30%

**Impact:** Unattributable contacts break marketing ROI. If 40% of contacts can't be traced to a source, 40% of marketing spend can't be justified.

### 1.6 Lifecycle stage regression

**Query:** Fetch `lifecycle_stage_history` property (if available) or scan last 90 days of lifecycle stage changes. Flag any contact that moved from a later stage to an earlier stage (e.g., SQL → MQL, Opportunity → Lead).

**Thresholds:** Any count >0 gets flagged; >50 events/month is critical.

**Impact:** Reps manually reverting stages to hide their funnel leakage. Breaks conversion reporting and indicates process/training gaps.

### 1.7 Stale marketing contacts

**Query:** Contacts marked as Marketing = true, with no engagement (email open, click, form submit, page view) in last 365 days.

**Thresholds:**
- Healthy: <15%
- Flag: 15–35%
- Critical: >35%

**Impact:** Directly costs money. Marketing Contact tier billing. Quantify the dollar impact by multiplying stale count × per-contact cost at current tier.

### 1.8 Marketing contact tier headroom

**Query:** Current marketing contact count vs. tier limit.

**Thresholds:**
- Healthy: <75% of limit
- Flag: 75–90%
- Critical: >90% (risk of auto-billing to next tier)

**Recommendation:** If critical, immediately suppress stale contacts (Check 1.7) before next billing sync.

### 1.9 Missing required fields on recent records

**Query:** Contacts created in last 90 days where key properties are null. Key properties vary by portal — typical set:

- `firstname`
- `lastname`
- `email`
- `phone` OR `mobilephone`
- `company` or `associated_company`
- `jobtitle`
- Portal-specific: `industry`, `number_of_employees`, `lifecyclestage`, `lead_source`

**Thresholds per property:** Flag if >20% of recent records missing; critical if >40%.

### 1.10 Invalid email formats

**Query:** Sample 1,000 contacts, check email against RFC-5322 regex. Also check for bounced/hard-bounced flag.

**Thresholds:**
- Invalid format: >2% is a flag; indicates form validation gap
- Hard-bounced and still Marketing: any count is a finding (should be excluded)

### 1.11 Deal/Ticket stage rot

**Query:**
- Open deals in same stage >90 days (excluding "Closed Won"/"Closed Lost")
- Open tickets >30 days in non-resolved stage

**Thresholds:**
- Deals: Flag if >25% of open pipeline is rotting; critical if >40%
- Tickets: Flag any >90 day open ticket unless explicitly configured as long-cycle

**Impact:** Inflates pipeline dashboards. Makes forecasting useless.

### 1.12 Associations health

**Query:** Contacts with no associated company (when they have a business-domain email). Deals with no associated contact. Deals with no associated company.

**Thresholds:**
- Orphan deals: >5% is a flag; critical if >15%
- Contacts with business email but no company: >20% is a flag

**Impact:** Breaks company-level reporting, ABM segmentation, and revenue attribution.

### 1.13 Subscription/consent integrity

**Query:** Contacts marked as subscribed to a subscription type they unsubscribed from. GDPR/CASL consent flags present for EU/CA contacts.

**Impact:** Compliance risk. CAN-SPAM, CASL, GDPR fines.

### 1.14 Buying role completeness on active opportunities

**Query:** HubSpot's buying role is a contact-to-deal association property (`hs_buying_role`) with standard values: Decision Maker, Budget Holder, Executive Sponsor, Champion, Influencer, End User, Power User, Blocker, Legal and Compliance. For every open deal above the portal's deal-size floor (typically $10K or whatever threshold the client uses to qualify pipeline), enumerate the associated contacts and count:

- Open deals with **zero** buying roles set on any associated contact
- Open deals with **no Decision Maker** identified (even if other roles are set)
- Open deals with **no Budget Holder or Executive Sponsor** identified
- Open deals with **only one** associated contact (single-threaded risk)
- Distribution of roles overall — if >80% of filled roles are "Decision Maker," reps are defaulting the field rather than actually multi-threading

**Thresholds:**
- Healthy: >70% of qualifying open deals have a Decision Maker identified; >50% have 3+ contacts with roles
- Flag: 40–70% with Decision Maker; many single-threaded deals
- Critical: <40% of open deals have a Decision Maker identified, OR >30% of open deals have zero buying roles set

**Impact:** Deals without an identified Decision Maker are unforecastable. Reps can't run a real close plan. The "deal you thought was closing" usually has no Decision Maker in HubSpot six months before it dies. Quantify: open pipeline $ with no Decision Maker = pipeline dollars the business thinks it has but effectively doesn't.

**Tier requirement:** Buying roles are Sales Pro+. If portal is on Starter, mark as a tier-upgrade opportunity with the pipeline-at-risk dollar value as justification.

### 1.15 ICP property fill rate on companies

**Query:** Check for the presence of an ICP tier property on Company (typical naming: `icp_tier`, `ideal_customer_profile`, `icp`, `customer_fit_tier`, `account_tier`). Usually values like Tier 1 / Tier 2 / Tier 3, or A/B/C, or Strategic/Target/Other.

If present, check:
- % of companies with ICP tier set (overall)
- % of active customer companies (with open deals or closed won in last 365d) with ICP tier set
- Distribution across tiers (if 90% are Tier 1, the tier is meaningless)
- Whether the property is used in any active list, workflow, or report

If absent entirely, that's a finding in its own right — no defined ICP.

**Thresholds:**
- Healthy: ICP property exists, documented, >80% fill on active customers, meaningful tier distribution, referenced by workflows/lists
- Flag: ICP exists but fill rate 40–80%, or tier distribution skewed, or unused by workflows
- Critical: No ICP property exists, OR <40% fill on active customers, OR 100% of companies are in one tier (not actually being used)

**Impact:** Without an ICP signal on the Company record, every downstream decision (lead scoring, routing, sequence assignment, reporting, quota setting) is generic. Sales and marketing can't align on "who are we selling to" if the CRM doesn't know the answer.

### 1.16 Deal progression — stalled deals and push rate

Deals that don't move are the leading indicator of forecast risk. This check is different from the basic "stage rot" check (1.11) because it looks at behavior over time, not just current state.

**Queries:**

- **Stalled deals:** Open deals with no engagement (call, email, meeting, note) in last 14 days. Also compute the 30-day variant.
- **Deal push rate:** Of open deals with a close date more than 30 days old originally, how many have had their close date moved to a later month 1x / 2x / 3+ times? A deal pushed 3+ times is nearly dead but still on the forecast.
- **No next step:** Open deals with no open task associated, no scheduled meeting, no scheduled activity. Reps have no documented next action.
- **Close date slippage distribution:** For open deals, compute (current close date − original close date) in days. Histogram it.
- **Stage velocity:** Average days in each stage, per pipeline. Compare against a healthy benchmark (shorter = better for most stages; very short = deals skipping stages).
- **Deals with no primary contact:** open deals where no associated contact has a buying role or is marked primary — usually means the deal is a placeholder, not a real opportunity.

**Thresholds:**
- Stalled deals (no activity >14d) as % of open pipeline: Healthy <15%, Flag 15–35%, Critical >35%
- Open deals pushed 2+ times: Healthy <10%, Flag 10–25%, Critical >25%
- Open deals with no next step: Healthy <10%, Flag 10–30%, Critical >30%
- Average stage velocity deviation from benchmark: Flag if any stage >2x benchmark

**Impact:** Each stalled or pushed deal in the open pipeline corrupts the forecast. If 30% of an $8M pipeline has been pushed twice or more, the realistic pipeline is more like $5.6M, and leadership is planning around a number that isn't real. Push rate is the single best leading indicator of missed quarterly number.

**Recommendation:** (1) Build a "deals requiring attention" dashboard: stalled >14d, pushed 2+ times, no next step. Review it weekly. (2) Set workflow to auto-create a "next step required" task when a deal has no open task. (3) Institute a "push accountability" process — every push requires a reason captured in a custom `push_reason` property so patterns become visible. (4) For deals pushed 3+ times, force a decision: progress or close-lost.

### 1.17 Lead response behavior and follow-up discipline

This check sits at the intersection of data health and adoption, but the measurable signal is in the data. See Adoption 3.18 for the rep-behavior framing.

**Queries:**

- **Time-to-first-touch (TTFT) for inbound MQLs:** For contacts created in last 90 days with lifecycle = MQL or source = form submission, measure time from MQL creation to first logged activity.
- **Lead leakage:** MQLs created in last 90 days with zero activity (no task, call, email, or meeting) after N days. Measure at 1d, 3d, 7d, 30d.
- **Follow-up cadence adherence:** Sequences or workflows designed to engage new MQLs — are they enrolling as expected? What's the delta between MQLs created and sequences enrolled?
- **Reassignment on no-response:** Are MQLs that the assigned rep never touched getting reassigned? Or do they sit forever in the original rep's queue?

**Thresholds:**
- TTFT median for inbound MQLs: Healthy <5 minutes, Flag 5–60 minutes, Critical >60 minutes (or >1 hour; the classic Harvard Business Review study: odds of qualifying a lead drop 6x if you wait 60+ minutes)
- Lead leakage at 7 days (MQLs with zero activity): Healthy <10%, Flag 10–25%, Critical >25%
- Lead leakage at 30 days: Healthy <5%, Flag 5–15%, Critical >15% (these are effectively lost leads)

**Impact:** Every ignored MQL is a paid marketing lead that generated zero return. Quantify: (MQLs with zero activity in 7d) × (cost per MQL) = direct wasted spend. Add to that the indirect cost of a marketing team that over-invests in top-of-funnel to compensate for bottom-of-funnel leakage.

**Recommendation:** (1) Define and enforce a lead SLA (e.g., inbound MQL touched within 15 minutes during business hours). (2) Build routing that reassigns to a backup rep if the primary doesn't respond within SLA. (3) Surface TTFT and leakage metrics in a lead ops dashboard reviewed weekly. (4) Use Workflow-based auto-enrollment into a sequence for any MQL not touched within X hours — at minimum they get the automated cadence.

### 1.18 Win/loss analysis integrity

Most portals close deals; few learn from them. Check whether closed-lost and closed-won deals carry the structured data needed for win/loss analysis.

**Queries:**

- **Close reason capture:** % of closed deals (last 365 days) with a structured `closed_lost_reason` / `closed_won_reason` property filled (not "Other" or free-text chaos)
- **Reason taxonomy:** If a reason property exists, is it an enumerated picklist (5–12 clean values) or free-text that's never aggregated?
- **Disposition discipline:** % of closed-lost deals with `closed_lost_reason` = "Unknown," null, or "Other"
- **Competitor capture:** On closed-lost deals, is the winning competitor captured (as a property, associated Company, or in the notes)?
- **Decision criteria capture:** Did the deal capture what the customer prioritized (price, features, relationship, timing)?
- **Post-close review cadence:** Any evidence of win/loss reviews happening (notes with "win/loss review" title, recurring meetings, a win/loss dashboard)?

**Thresholds:**
- Healthy: >80% of closed deals have structured close reason; enumerated picklist with <12 values; competitor captured on >50% of losses; win/loss review dashboard exists and is viewed
- Flag: 50–80% fill rate, or free-text reasons with low aggregation usefulness
- Critical: <50% fill rate, OR reasons are "Other" / free-text only, OR no competitor capture — the organization is closing deals without learning from them

**Impact:** A portal with 1,200 closed-lost deals in the last year and no structured reasons is a portal that's wasted $millions in product insight, marketing positioning opportunity, and competitive intelligence. Win/loss data is how marketing improves messaging, product fixes gaps, and sales trains on real objection handling. Without it, these functions operate on anecdote.

**Recommendation:** (1) Define an enumerated close-reason picklist with 6–10 values per outcome (won and lost). (2) Make the close-reason property required to move to "Closed" stage (via workflow). (3) Build a "Win/Loss Review" dashboard: loss reasons by count/$, losses by competitor, losses by segment, win reasons. (4) Institute monthly win/loss review meeting with Sales, Marketing, Product. (5) For enterprise clients, consider a structured win/loss interview process for deals above a $ threshold.

### 1.19 Commission and compensation data readiness

Relevant for any client evaluating commission automation (QBS's Commission Command positioning) or simply trying to pay reps accurately. The data quality requirements for commission calculation are strict.

**Queries:**

- **Deal owner stability:** How often does deal owner change during an open deal's lifetime? Multiple owner changes on a single deal corrupt commission attribution. Sample last 90 days of won deals and count ownership changes.
- **Deal split tracking:** Is there a structured deal-split mechanism (HubSpot's native deal-splits feature, Pro+) or is it tracked informally? Are split percentages summing to 100%?
- **Credit attribution clarity:** Can the portal answer "who gets credit for this deal and why" for every closed-won deal without ambiguity?
- **Close date integrity:** Close date changes on closed deals (which shouldn't happen but does) corrupt period-based commission calculations. Count closed deals where close date changed after the close.
- **Deal amount integrity:** Deal amount changes after close (revisions, discounts applied late) — count and flag.
- **Line-item / product attribution:** If commissions are product-based, are line items / products properly captured on deals with accurate amounts?
- **Recurring revenue treatment:** For SaaS/MRR clients, is ACV/MRR/TCV clearly distinguished on deals, or is it all in one "Amount" field?
- **Bookings vs. revenue timing:** Is there a distinct property for when a deal becomes commissionable (contract signed, go-live, first payment) vs. close date?

**Thresholds:**
- Healthy: Owner stability >95% on closed deals, split mechanism in place with 100% sums, close date immutable after close, line items accurate, recurring revenue properly segmented
- Flag: Owner changes on 5–15% of deals, splits informal, close date drift on some deals
- Critical: Owner changes on >15% of deals, no split mechanism, close date drifts commonly, line items missing or wrong — commission calculation cannot be trusted

**Impact:** Rep trust in commission is foundational to rep retention. Every commission dispute erodes trust. Every commission error (under or over) creates administrative burden and — for overpayments — clawback conflict. Before a client automates commission, these data quality prerequisites have to be met. This check both validates readiness AND flags the engagement hook.

**Recommendation:** (1) Lock owner changes on closed deals via workflow. (2) Require split percentages to sum to 100% before close (workflow validation). (3) Make close date immutable after a deal is closed (permission or workflow-based). (4) Standardize on HubSpot's line items / products if using amount tiers. (5) Segment recurring revenue into distinct properties (MRR, ACV, one-time). (6) Add a distinct `commissionable_date` property if the trigger differs from close. (7) Once data integrity is solid, Commission Command (or equivalent) becomes a natural next-phase engagement.

## Dealer-channel-specific checks

If scoping detected dealer-channel signals, add these:

- **Service contracts with no associated company:** orphan SC records
- **Equipment records with no associated company:** orphan equipment
- **Equipment with expired service contracts still marked active**
- **Contacts with no location association** (for multi-site accounts)

## Output format

For each finding, produce:

```yaml
- id: data_health_01_dupe_contacts
  dimension: data_health
  severity: critical
  title: "High duplicate contact rate"
  evidence: "4,820 duplicate groups across 154,230 contacts (3.1%)"
  impact: "~300 active duplicate leads; ~150 hrs/yr rep time at 30 min per dupe handling"
  recommendation: "Enable HubSpot AI dedupe for Contacts; build Ops Hub workflow to prevent new dupes from import"
  effort: days
  tier_requirement: "Dedupe tool is Pro+; prevention workflow is Ops Starter+"
```
