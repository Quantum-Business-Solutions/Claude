# RevOps Maturity Model

The capstone output of the audit. Rolls up findings across the six dimensions into a 5-stage maturity positioning. Unlike the dimension scores (operational health), the maturity model is strategic — where is this client on the RevOps journey, and what does "next stage" require?

This is what transforms the deliverable from "list of problems" into "positioning on a journey," which is the hook for ongoing engagement.

## Structure: 5 capabilities × 5 stages

### The five capabilities

1. **Process & Operating Rhythm** — SLAs, pipeline reviews, forecast process, stage definitions, deal progression discipline
2. **Data Architecture & Hygiene** — object model, property governance, deduplication, ICP definition and enforcement, attribution setup
3. **Technology & Integration Coverage** — tool coverage per user, integration health, dual-write resolution, engagement capture completeness
4. **People & Adoption** — rep usage, manager adoption, training signals, logging discipline, lead follow-up behavior
5. **Strategy, Measurement & Optimization** — revenue efficiency metrics, ICP-based reporting, ABM motion, attribution quality, exec dashboards

### The five stages

| Stage | Name | Diagnosis |
|-------|------|-----------|
| 1 | Ad Hoc / Reactive | HubSpot is a Rolodex. No process discipline. Decisions made outside the system. |
| 2 | Managed / Developing | Process exists but inconsistent. Some reporting. Integration gaps. Leadership wants more. |
| 3 | Defined / Operational | Documented process, consistent data capture, revenue reporting exists, ICP defined and used. |
| 4 | Measured / Analytical | Efficiency metrics tracked, attribution configured, ABM motion operational, coaching grounded in data. |
| 5 | Optimized / Strategic | Predictive forecasting, multi-touch attribution, closed-loop ABM, continuous optimization, HubSpot is a strategic asset. |

## Stage criteria per capability

### Capability 1: Process & Operating Rhythm

**Stage 1 — Ad Hoc:**
- No documented lead routing SLA
- No regular pipeline review cadence (or it happens in spreadsheets)
- Forecast is a gut-feel email from leadership
- Deal stages undefined; reps use them inconsistently
- Deals sit in stages for 90+ days with no action

**Stage 2 — Managed:**
- SLA exists in a doc somewhere but not enforced
- Weekly pipeline review happens but runs in an exported spreadsheet
- Forecast submitted by reps but not consistently
- Stages have names but not formal entry/exit criteria
- Stalled deals are acknowledged but not worked

**Stage 3 — Defined:**
- Documented lead routing SLA with measurable time-to-first-touch
- Pipeline review uses HubSpot views; reps prepare beforehand
- Forecast submitted in HubSpot Forecast tool on a regular cadence
- Deal stages have documented entry/exit criteria
- Deals with no activity >14 days are flagged weekly

**Stage 4 — Measured:**
- SLA adherence reported weekly; outliers addressed
- Multi-level pipeline reviews (rep, team, org); predictive flags on at-risk deals
- Forecast accuracy measured and improving quarter over quarter
- Deal push rate tracked (how often is close date moved?); stage velocity reported
- Stalled deals auto-surface; deal push reasons captured

**Stage 5 — Optimized:**
- AI-assisted SLA prediction; proactive intervention before breach
- Pipeline reviews driven by AI risk scoring; deal coaching plans in HubSpot
- Forecast accuracy >85%; multiple models reconciled
- Deal progression continuously optimized; benchmark data across portfolio
- Zero tolerance for deals without next steps; culture of discipline

### Capability 2: Data Architecture & Hygiene

**Stage 1 — Ad Hoc:**
- Duplicate contacts/companies unaddressed (>5% dupe rate)
- No ICP concept in the portal
- Properties added ad hoc; no governance
- Attribution fields mostly null; tracking inconsistent
- Lists proliferating; most are stale

**Stage 2 — Managed:**
- One-time dedupe done but no prevention
- ICP discussed in meetings but not defined as a property
- Someone asks about new properties, sometimes
- Some attribution captured; UTMs inconsistent
- Active lists outnumber static; some cleanup happens

**Stage 3 — Defined:**
- Dedupe automation in place; <2% dupe rate maintained
- Formal ICP property with documented rubric; tiers enforced
- Property governance process exists; orphan property quarterly review
- Attribution model selected and applied; UTM builder in use
- Lists categorized and reviewed quarterly; naming conventions

**Stage 4 — Measured:**
- Data quality SLA tracked; hygiene workflows report on their own effectiveness
- ICP auto-tiered via workflow; ICP fit correlates with win rate
- Property usage reported; dead properties retired on schedule
- Multi-touch attribution configured; marketing ROI reportable
- List sprawl under control; active list count plateaued

**Stage 5 — Optimized:**
- Predictive dedupe; data quality monitored in real time
- ML-enhanced ICP scoring; ICP refined quarterly from won/lost data
- Zero-orphan property discipline; property requests reviewed
- Closed-loop attribution; offline sources captured; revenue traced to first touch
- Lists as code; automated lifecycle management

### Capability 3: Technology & Integration Coverage

**Stage 1 — Ad Hoc:**
- Reps using personal email, not HubSpot email tool
- Calendar not synced for most users
- Calls happen on cell phones; never logged
- Meetings captured only if a rep remembers to log them
- LinkedIn Sales Nav owned but rarely connected to HubSpot

**Stage 2 — Managed:**
- Some reps have inbox + calendar connected
- HubSpot Calling or a dialer exists but used sporadically
- Meeting transcription tool (Zoom AI, Gong) present but not for everyone
- Dual-write conflicts (e.g., Zoom + Read AI) causing duplicate engagements
- Integration errors go unnoticed for weeks

**Stage 3 — Defined:**
- Role-based integration requirements documented; new reps onboarded with full stack
- All calling reps have a dialer with auto-logging
- Meeting transcription standardized to one source; no dual-write
- Integration errors reviewed weekly
- Mobile app adopted by field-based reps

**Stage 4 — Measured:**
- Per-user integration coverage reported; gaps addressed within 30 days
- Integration ROI assessed (e.g., time saved via auto-log)
- API usage monitored; tier planning informed by usage trends
- Integration changes follow a change management process
- Strategic consolidation (retire redundant tools)

**Stage 5 — Optimized:**
- Automated integration health alerts
- Integration stack reviewed annually; ROI-driven tool rationalization
- AI-driven engagement enrichment (call summary, meeting notes, signal detection)
- Custom integrations built where off-the-shelf insufficient
- Stack flexibility treated as a strategic capability

### Capability 4: People & Adoption

**Stage 1 — Ad Hoc:**
- <60% of seats with monthly login
- Reps treat HubSpot as a data-entry chore
- No training beyond initial onboarding
- Managers don't use dashboards; decisions made in spreadsheets
- Calls rarely logged; activity metrics meaningless

**Stage 2 — Managed:**
- 70–85% active user rate
- Informal training; some reps power-user, others bypass
- A few managers use dashboards sometimes
- Some activity logging but inconsistent
- Leads get worked but without SLA enforcement

**Stage 3 — Defined:**
- >85% active user rate; deactivated seats removed
- Formal onboarding includes HubSpot training; HubSpot Champion or admin designated
- Managers use dashboards weekly
- Activity logging is a cultural norm
- Lead follow-up tracked to SLA

**Stage 4 — Measured:**
- Adoption metrics in every QBR; rep performance tied to CRM usage
- HubSpot Academy certifications encouraged
- Managers coach from HubSpot data (call recordings, pipeline views)
- Activity-to-outcome ratios reported per rep
- Lead follow-up SLA breaches trigger manager alerts

**Stage 5 — Optimized:**
- Continuous enablement; learning paths per role
- HubSpot Champions program with internal career path
- AI-assisted coaching for managers
- Predictive adoption risk scoring per user
- Self-service enablement; rep-driven improvement suggestions

### Capability 5: Strategy, Measurement & Optimization

**Stage 1 — Ad Hoc:**
- Pipeline dashboard only; no attribution; no ICP segmentation
- Revenue metrics calculated manually
- No ABM motion
- Marketing ROI unknowable
- Forecasts are gut-feel

**Stage 2 — Managed:**
- Basic revenue dashboards (pipeline, closed won) exist
- First-touch attribution captured but not trusted
- Target Accounts flagged but not worked differently
- Some rep-level reporting; no ICP dimension
- Forecast submitted but accuracy not measured

**Stage 3 — Defined:**
- Revenue Core 8 dashboard exists and is used by leadership
- Attribution model selected (first-touch or last-touch) and applied
- ICP segmentation in core reports
- Target Accounts operational with differentiated sequences
- Forecast accuracy tracked

**Stage 4 — Measured:**
- Revenue efficiency tracked: pipeline coverage, win rate, velocity, CAC payback
- Multi-touch attribution configured; marketing-sourced vs. marketing-influenced distinct
- ABM motion measured (target account win rate > non-target)
- ICP tier × source × revenue reporting; allocation decisions data-driven
- Forecast accuracy >80%

**Stage 5 — Optimized:**
- Predictive forecasting with AI-assisted risk scoring
- Multi-touch attribution with custom models; revenue closed-loop to first touch
- Closed-loop ABM with quarterly target account refresh
- Strategic allocation reviewed based on ICP × source × channel efficiency
- Continuous optimization; HubSpot is a strategic asset driving EBITDA

## How to assign a stage

For each capability, evaluate the portal against the criteria above. A capability's stage is the **highest stage where all Stage N criteria are met** (not the highest where *some* are met — all).

If findings in the audit contradict a stage assignment, the contradictory findings win. Example: if Process & Operating Rhythm looks Stage 3 but the audit found that 40% of open deals have no activity in 14+ days (deal progression gap), the capability is Stage 2, not 3.

## Overall maturity designation

Like the dimension scores, **overall maturity = minimum of the five capabilities**. A portal can't be at Stage 4 strategically with Stage 1 data hygiene — the strategic layer collapses without the foundation.

Report as: "**Stage N — {Name}**, limited by {Capability}."

Example: "Stage 2 — Managed, limited by Technology & Integration Coverage."

## Upgrade path (the sales hook)

For each capability scored below overall target (typically Stage 3 or 4), produce a "next stage" delta:

```
Current:  Stage 2 — Managed
Target:   Stage 3 — Defined
Gap:      {2-5 specific findings from the audit that block Stage 3}
Effort:   {Weeks estimate}
Value:    {Business impact of moving up one stage}
```

This is the natural engagement scope. QBS sells "get to Stage 3" as a concrete SOW, not a vague "improve your HubSpot."

## Presentation in the deliverable

In client mode, the maturity assessment gets its own section after the dimension scoreboard and before the findings. Visual treatment:

- Maturity stair-step diagram showing current stage per capability
- One-sentence narrative per capability
- Overall stage call-out
- Upgrade path as a summary table

In internal recon mode, just the stage designations per capability plus overall, in a single block.

## Portfolio benchmarking (QBS-specific)

After running the audit on multiple portals, QBS can maintain a portfolio average stage per capability. Deliverables can reference: "Your Data Architecture & Hygiene is at Stage 2; the QBS dealer-channel portfolio median is Stage 3." This is the data moat made visible.

Do not include benchmarking in the first few audits — only once a credible baseline exists (n>10 portals audited with this skill).
