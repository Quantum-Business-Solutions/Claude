# Dimension 6: Reporting & Attribution

Assesses whether the portal produces decision-quality reporting. Most portals have 50+ dashboards and 0 business decisions coming from them.

## Checks to run

### 6.1 Dashboard inventory

**Query:** Total dashboards, private vs. shared, with views in last 30 days.

**Thresholds:**
- Healthy: 5–15 active dashboards, all with weekly views, clear ownership
- Flag: 15–40 dashboards OR >30% with no views in 30d
- Critical: >40 dashboards OR >60% with no views in 30d

**Finding:** Dashboard sprawl is nearly universal. The fix isn't "make more dashboards" — it's retire and consolidate.

### 6.2 Report inventory

**Query:** Total custom reports, reports not attached to any dashboard, reports with zero references.

**Finding:** Orphan reports are usually someone's one-off analysis that never got cleaned up. Archive candidates.

### 6.3 Revenue reporting core metrics

**Critical check** — these metrics should exist as reports in any Sales Hub Pro+ portal:

- Pipeline by stage (current snapshot)
- Pipeline by stage over time (weekly or monthly)
- Closed won revenue (MTD, QTD, YTD, by rep, by source)
- Win rate (by rep, by source, by deal size)
- Average sales cycle length
- Average deal size / ACV
- Forecast accuracy (committed vs. actual)
- Rep-level activity-to-outcome (calls/emails/meetings → pipeline created)

**Finding:** List which of these are missing. A portal missing 3+ is flagged as critical — leadership is flying blind.

### 6.4 Marketing reporting core metrics

If Marketing Hub:
- Contacts created by source (first-touch attribution)
- MQL → SQL conversion rate by source/campaign
- Email performance (open/click/reply trends)
- Landing page conversion rate
- Ad campaign attribution (if ads connected)
- Content performance (blog, pillar pages)

**Finding:** Same as 6.3 — count the gaps, not the artifacts.

### 6.5 Attribution model configuration and quality

**Query:** Assess attribution setup at three layers:

**Layer 1 — Model selection:** Attribution reports built? Model selected (first-touch, last-touch, linear, U-shaped, W-shaped, time-decay)?

**Layer 2 — Data capture quality:**

- UTM hygiene: is the UTM builder tool in use? Are campaign/source/medium/content/term values consistent across campaigns (not free-text chaos)?
- Tracking code deployed on all web properties (main site, blog, landing pages, microsites)?
- Cross-domain tracking configured where needed?
- Offline source capture: are events, trade shows, referrals, direct outreach captured with UTM-equivalent structured data?
- Form source preservation: do form submissions preserve the original source even when contacts already exist?
- Paid ads connected (Google Ads, LinkedIn, Facebook) with auto-attribution?
- Dark social / untraceable referrals accounted for (self-reported attribution field)?

**Layer 3 — Business integration:**

- Marketing-sourced vs. marketing-influenced revenue distinct and reported?
- Attribution rollup to revenue (not just MQLs or SQLs)?
- Attribution reports reviewed by leadership regularly (dashboard with views)?

**Thresholds:**
- Healthy: attribution model selected appropriate to sales cycle length, UTM builder in use, offline capture structured, tracking code fully deployed, marketing-sourced revenue reported
- Flag: any two of the following — default first-touch on long-cycle B2B, UTM inconsistency, offline sources uncaptured, sparse tracking code coverage
- Critical: no attribution model configured, OR UTM is free-text chaos, OR tracking code coverage <50%, OR attribution exists but leadership doesn't reference it

**Findings:**
- "No attribution model" → critical gap (marketing ROI unknowable)
- "Default first-touch on a B2B portal with 9-month average sales cycle" → likely wrong model (multi-touch more appropriate)
- "UTM values are free-text with 47 variations of 'linkedin' captured" → critical hygiene issue; every marketing report has bad data
- "Multi-touch attribution (Enterprise) available but not used" → opportunity, not critical

**Impact:** Weak attribution makes every dollar of marketing spend a guess. The gap compounds: without attribution, you can't identify winning channels, so you can't double down, so growth is linear when it should be compounding.

### 6.6 Custom report adoption

**Query:** Of custom reports built in last 180 days, % that are attached to a dashboard with views.

**Finding:** If 70% of custom reports aren't surfaced anywhere, the portal has a "build report, forget report" pattern. Cultural issue, not technical.

### 6.7 Forecast tool usage (Sales Pro+)

**Query:** Forecast tool enabled. Forecasts submitted per rep per month. Forecast accuracy (if history available).

**Finding:** Forecast tool available but unused is a common paid-feature waste.

### 6.8 Goals tool usage

**Query:** Goals set per user/team. Goal completion rate.

**Finding:** Goals tool is free — any portal not using it is leaving the monitoring capability on the table.

### 6.9 Executive dashboard presence

**Query:** Is there a designated "executive dashboard" used by leadership? Who views it? How often?

**Finding:** Portal with no exec-level dashboard means the C-suite isn't using HubSpot for decision support. Advocacy risk.

### 6.10 Dealer-channel reporting gaps

Specific metrics dealer-channel clients need but often don't have:

- **Service contract revenue** — MRR/ARR from SC object, renewal rate, churn rate
- **Equipment placement to service opportunity attach rate**
- **Cost per lead by source, cost per opportunity, cost per closed deal**
- **Rep-level MRR attribution**
- **Territory performance**
- **Meter-read revenue forecasting** (if meter-based billing)

### 6.11 Report performance and load

**Query:** Any reports timing out or slow-loading? Often indicates a report scanning too many records or using too many properties.

### 6.12 Data freshness in reports

**Query:** Reports pulling from stale data (workflows that haven't run, cached calculations, out-of-date manual entries).

**Finding:** List specifically which reports rely on fields that data health (Dimension 1) flagged as unreliable. This connects findings across dimensions.

### 6.13 Cross-object reporting (Pro+)

**Query:** Custom reports using cross-object fields (Pro+), datasets (Ops Hub Enterprise).

**Finding:** Portal paying for Pro but not using cross-object reporting is missing core value.

### 6.14 Scheduled/emailed reports

**Query:** Scheduled email digests. Are they being opened? Bounced recipients?

**Finding:** Dashboards emailed daily to distribution lists where 80% of recipients haven't opened in 60 days = noise. Unsubscribe and consolidate.

### 6.15 Target Accounts / ABM reporting

**Query:** If Target Accounts is enabled (see Architecture 2.15), check for:

- A dedicated Target Accounts dashboard
- Target account penetration report (accounts with active contact/activity vs. flagged accounts)
- Target account pipeline (open deals on flagged accounts vs. other)
- Target account win rate vs. non-target win rate
- Time-to-first-meeting on newly flagged target accounts
- Target account coverage by rep (are all target accounts covered?)

**Thresholds:**
- Healthy: Target Accounts enabled AND a dedicated dashboard exists AND leadership views it AND win rate is higher on targets (validating the ABM hypothesis)
- Flag: Target Accounts enabled but no dashboard, or dashboard with no views
- Critical: Target Accounts enabled but win rate on targets is NOT higher than non-targets (the ABM motion is not working — or targets aren't actually better accounts)

**Impact:** Target Accounts without reporting is an empty feature flag. The whole point is to prove the motion: target accounts close more, faster, at higher value. If that's not being measured, no one knows if ABM is paying off.

### 6.16 ICP-based reporting

**Query:** If an ICP property exists (Architecture 2.16, Data Health 1.15), check for reports segmenting revenue/pipeline/activity by ICP tier:

- Closed won by ICP tier (last 4 quarters)
- Pipeline $ by ICP tier
- Win rate by ICP tier
- Avg deal size by ICP tier
- Avg sales cycle by ICP tier
- Source-to-closed conversion by ICP tier (which marketing channels bring Tier 1 vs. Tier 3)

**Thresholds:**
- Healthy: ICP tier is a dimension in at least 3 revenue reports; executive dashboard includes an ICP-tier view
- Flag: ICP property exists and some reports use it but ICP view is buried
- Critical: ICP property exists but zero reports segment by it — leadership can't answer "are we winning in our ICP?"

**Impact:** Without ICP-segmented reporting, revenue leaders make allocation decisions blind to fit. Marketing budget goes to whatever channel produces the most MQLs, even if those MQLs don't fit the ICP. Sales capacity gets deployed against the wrong accounts. The cost is strategic misallocation, which is bigger than any tactical finding in the audit.

### 6.17 Revenue efficiency framework adherence

Beyond the "Revenue Core 8" (6.3), a mature revops function measures efficiency metrics that drive capital allocation and GTM investment decisions.

**Query:** Check for the presence of each of the following metrics as a report, dashboard tile, or documented calculation. For each, note whether it's computed, trusted, and reviewed by leadership:

**Pipeline efficiency:**
- Pipeline coverage ratio (open pipeline ÷ next-quarter quota) — healthy B2B benchmark 3–4×
- Pipeline velocity: (Opportunities × Win rate × Avg deal size) ÷ Sales cycle length
- Deal slippage rate (% of deals pushed past their original close date)
- Bookings vs. forecast accuracy (forecast accuracy tracked quarter over quarter)

**Go-to-market efficiency:**
- Customer Acquisition Cost (CAC) — requires marketing spend + sales cost data
- CAC Payback period
- Lead-to-customer conversion rate by source
- MQL-to-SQL, SQL-to-opportunity, opportunity-to-close conversion rates
- Cost per lead, cost per opportunity, cost per closed deal by source

**Revenue quality:**
- Net Revenue Retention (NRR) / Gross Revenue Retention (GRR) — for clients with recurring revenue
- Logo retention rate
- Expansion revenue attribution
- Average revenue per account, per customer cohort

**For dealer-channel clients specifically:**
- MRR from managed services contracts
- ARR from service contracts (renewals baseline)
- Service attach rate on new equipment placements
- Average revenue per serviced device
- Supply/consumables attach rate
- Meter-read revenue forecasting (if meter-based billing)
- Renewal rate (service contracts expiring vs. renewed)

**Thresholds:**
- Healthy: 6+ of the relevant metrics above are reported, dashboards leadership uses monthly or quarterly, metrics trend over time rather than point-in-time only
- Flag: 3–5 metrics reported but not all; some gaps on conversion rates or cost-per metrics
- Critical: <3 of these metrics exist; pipeline coverage not measured; no forecast accuracy; no conversion rate tracking

**Impact:** The gap between "we have revenue reports" and "we run on revenue efficiency" is the gap between Stage 3 and Stage 4 of the RevOps maturity model. Without efficiency metrics, leadership can't answer: are we growing profitably? Which channels deserve more investment? Where's the bottleneck in the funnel? These are the questions that drive business decisions, and they can't be answered from a pipeline dashboard alone.

**Recommendation:** Build an "Efficiency Core 10" dashboard: pipeline coverage, pipeline velocity, deal slippage rate, forecast accuracy, CAC payback, MQL-to-close conversion, cost-per-closed-deal by source, NRR/GRR, expansion revenue %, and industry-specific (for dealers: service attach rate or renewal rate). One consolidated view; reviewed monthly by leadership. This is the foundation of a true RevOps operating cadence.

### 6.18 Win/loss reporting and feedback loop

Companion to Data Health 1.18. If close-reason capture is happening, is it being used?

**Query:**

- Is there a Win/Loss Review dashboard or equivalent report set?
- Reports segment losses by: reason, competitor, source, ICP tier, deal size, segment, rep
- Reports segment wins by: reason, source, ICP tier
- Evidence of win/loss review cadence (meeting on calendar, notes referencing "win/loss review," recurring meeting template)
- Insights from win/loss analysis flowing back into: marketing messaging updates, product roadmap items, sales playbook revisions

**Thresholds:**
- Healthy: Win/loss dashboard exists, reviewed monthly by Sales + Marketing + Product, documented action items from reviews
- Flag: Dashboard exists but no visible review cadence
- Critical: No win/loss dashboard, OR reason data exists but is never aggregated or reviewed

**Impact:** The gap between "capturing close reasons" and "acting on close reasons" is where most organizations leak competitive intelligence. A portal with a year of loss data sitting unused is an asset worth $millions in unrealized insight — better messaging, better positioning, better product decisions, better rep training.

### 6.19 Forecast cadence and process maturity

Forecasting was covered at a health level in 6.7; this check assesses the reporting and process maturity around forecast.

**Query:**

- Forecast snapshots over time: can the portal show forecast at week 1 vs. week 4 of a quarter vs. actual?
- Forecast accuracy report: gap between committed forecast and actual closed, per rep and per team, over time
- Forecast categories in use (Commit, Best Case, Pipeline, Omitted) or just a single number?
- Are forecasts discussed in recurring meetings (calendar evidence)?
- Is there a forecast call script or playbook (document/note)?
- Are forecast trends reviewed (is accuracy improving quarter over quarter)?
- Scenario planning: upside/downside/worst-case breakdowns?

**Thresholds:**
- Healthy: Forecast snapshots captured, accuracy tracked over time, multiple categories used, weekly forecast call cadence evident, accuracy trending positive
- Flag: Single-number forecast, no snapshots, accuracy not tracked
- Critical: No forecast process or accuracy measurement — leadership is flying blind on quarterly results

**Impact:** Forecast maturity separates the companies that consistently hit number from those that surprise themselves. Without snapshot history, nobody learns why forecasts miss. Without category discipline, the forecast is a single number with no texture. Without accuracy tracking, coaching has nothing to coach against.

## Interpretation note

Reporting findings often **diagnose issues in other dimensions**. If a portal "can't track win rate," it's usually because:
- Deal stages are misconfigured (Architecture 2.7)
- Deals are being closed without proper disposition (Data Health 1.11)
- Deal owner assignment is broken (Automation 4.9)

When writing the deliverable, cross-reference these connections explicitly.

## Output format

```yaml
- id: reporting_03_missing_revenue_metrics
  dimension: reporting
  severity: critical
  title: "Core revenue reporting absent"
  evidence: "No dashboards contain pipeline-by-stage-over-time, win-rate-by-rep, or forecast-accuracy reports. 37 custom dashboards exist; none address executive revenue questions."
  impact: "Leadership cannot answer 'how is the business doing' from HubSpot. Decisions are made in spreadsheets sourced from exports, creating a second source of truth. Forecasting is guesswork."
  recommendation: "Build the 'Revenue Core 8' dashboard: pipeline snapshot, pipeline trend, closed won MTD/QTD/YTD, win rate by rep, win rate by source, avg cycle length, avg deal size, forecast accuracy. 1 consolidated dashboard; retire 10-15 of the existing orphan dashboards in the same engagement."
  effort: days
  tier_requirement: "Forecast accuracy requires Sales Pro; rest work on Starter"
```
