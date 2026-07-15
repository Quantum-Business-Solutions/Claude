# Cross-Dimension Anti-Pattern Catalog

These patterns recur across portals and often span multiple dimensions. After running dimension-specific checks, scan for these holistic issues. Each one typically maps to a single root cause that creates symptoms in 2+ dimensions.

## AP-01: Dual-engagement logging

**Symptom in Data Health:** Duplicate meeting/call engagements  
**Symptom in Integrations:** Two meeting tools (Zoom + Read AI, Gong + Chorus, etc.)  
**Symptom in Adoption:** Reps reporting "my activity counts are weird"  
**Symptom in Reporting:** Rep-level activity metrics inflated  

**Root cause:** Two integrations writing to the same engagement type.  
**Fix:** Standardize on one, disable the other's CRM-write, run cleanup script.  
**Priority:** Always critical.

## AP-02: Property sprawl → form/workflow fragility

**Symptom in Architecture:** 300+ contact properties, most unused  
**Symptom in Automation:** Workflows using inconsistent properties for the same concept  
**Symptom in Data Health:** Low fill rates across custom properties  
**Symptom in Reporting:** Can't build clean reports because the "right" field isn't obvious  

**Root cause:** No property governance. Every admin adds, none remove.  
**Fix:** Deprecation cycle (archive → 30 days → delete); establish governance RFC for new properties.

## AP-03: Lifecycle stage chaos

**Symptom in Data Health:** Regression events, null stages  
**Symptom in Architecture:** No definition doc for stages  
**Symptom in Automation:** Multiple workflows setting the same stage with different logic  
**Symptom in Reporting:** Funnel conversion reports unreliable  

**Root cause:** Undocumented, overlapping lifecycle stage logic.  
**Fix:** Document each stage's entry/exit criteria; consolidate stage-setting logic into ONE workflow; eliminate manual stage changes via permissions.

## AP-04: Marketing contacts bloat

**Symptom in Data Health:** High stale contact rate in Marketing=true population  
**Symptom in Architecture:** No suppression workflow  
**Symptom in Reporting:** Marketing email metrics denominator wrong  

**Root cause:** No lifecycle for moving stale contacts to non-marketing.  
**Fix:** Build "Suppress Stale" workflow; set tier headroom alert; communicate to finance.  
**Urgency:** If approaching tier ceiling, do this in week 1 of any engagement.

## AP-05: Sequence graveyard

**Symptom in Adoption:** Many inactive sequences  
**Symptom in Automation:** High unsubscribe rate, stale sequence templates  
**Symptom in Architecture:** No naming convention for sequences  

**Root cause:** Every rep/manager builds their own, none are retired.  
**Fix:** Audit and archive (not delete) sequences with 0 enrollments in 90d; establish sequence review cadence.

## AP-06: Pipeline-per-rep

**Symptom in Architecture:** 8+ deal pipelines  
**Symptom in Reporting:** Consolidated forecasting impossible  
**Symptom in Adoption:** Reps confused about which pipeline to use  

**Root cause:** Someone asked for "my own pipeline" and no one said no.  
**Fix:** Consolidate to 2–4 pipelines max (typically New Business, Expansion, Renewal); migrate deals; update reports.  
**Effort:** Days, not hours — migration needs care.

## AP-07: Lead routing black hole

**Symptom in Automation:** Round-robin includes deactivated users OR no fallback rule  
**Symptom in Data Health:** Orphan contacts/deals (no owner)  
**Symptom in Reporting:** "Unassigned" bucket accumulating  
**Symptom in Adoption:** Complaints that "good leads are going missing"  

**Root cause:** Routing logic not maintained as team changes.  
**Fix:** Active-users-only routing; default "Round Robin Unassigned" queue reviewed weekly; ownership audit.

## AP-08: Dashboard cemetery

**Symptom in Reporting:** Dozens of dashboards, most with no views  
**Symptom in Adoption:** "We don't really use HubSpot reports"  

**Root cause:** Dashboards built for one-time questions, never retired; private dashboards that leavers owned.  
**Fix:** Archive all dashboards with 0 views in 60 days; build ONE exec dashboard with clear owner; quarterly cleanup cadence.

## AP-09: Workflow dark age

**Symptom in Automation:** Workflows in error for months, many with 0 enrollments  
**Symptom in Data Health:** Expected data hygiene not happening (stale values)  
**Symptom in Reporting:** Reports depending on workflow-set properties are wrong  

**Root cause:** No workflow monitoring. No one owns "all workflows healthy" as a responsibility.  
**Fix:** Weekly workflow health review; error notification digest; orphan workflow audit.

## AP-10: Record owner rot

**Symptom in Architecture:** Deactivated users still own records  
**Symptom in Automation:** Routing sends to deactivated users  
**Symptom in Reporting:** Rep-level reports include ghosts  

**Root cause:** Offboarding process doesn't reassign records.  
**Fix:** Offboarding checklist mandates reassignment; workflow to catch new orphans; one-time sweep of existing.

## AP-11: Form overwrite damage

**Symptom in Data Health:** Contact properties silently reverting to stale values  
**Symptom in Architecture:** Forms with many hidden fields  
**Symptom in Reporting:** Segmentation fields inconsistent over time  

**Root cause:** Forms with hidden fields set to default values, overwriting updated contact data on resubmit.  
**Fix:** Audit forms; remove unnecessary hidden fields; use "update existing contact value" = "don't overwrite" on sensitive properties.

## AP-12: Attribution blind spot

**Symptom in Data Health:** High null rate on Original Source  
**Symptom in Integrations:** Tracking code not installed site-wide  
**Symptom in Reporting:** Marketing ROI unknowable  

**Root cause:** Tracking code only on some pages, or offline sources not having UTM templates, or integrations not preserving source.  
**Fix:** Tracking code audit; UTM builder deployed; source-preservation review on each form/integration.

## AP-13: Reported data vs. reality

**Symptom in Adoption:** Reps bypassing CRM (sending email externally, logging manually)  
**Symptom in Data Health:** Activity counts don't match real-world activity  
**Symptom in Reporting:** Reports "look right" but leadership distrusts them  

**Root cause:** Rep adoption gap OR integration logging gap OR both.  
**Fix:** Activity sampling (shadow a rep for a day vs. their HubSpot); fix integration gaps; address adoption with manager enforcement + process design.

## AP-14: Dealer channel-specific: service contract → opportunity gap

**Symptom in Architecture:** Service contracts exist but don't trigger opportunities  
**Symptom in Automation:** No renewal workflow  
**Symptom in Reporting:** Can't forecast renewal revenue  

**Root cause:** Contract object exists as a record-keeping artifact, not an active pipeline driver.  
**Fix:** Build renewal workflow (180/90/60/30 days pre-expiry → task/deal/email); tie SC records to deal records explicitly; build renewal pipeline.

## AP-15: Dealer channel-specific: equipment placement → service attach

**Symptom in Architecture:** Equipment records exist but no service attach logic  
**Symptom in Reporting:** No visibility into service attach rate  
**Symptom in Automation:** No post-placement follow-up workflow  

**Root cause:** Equipment data imported from e-automate/ECI, never connected to service/supply sales motion.  
**Fix:** Build post-placement workflow (30/60/90-day service upsell touchpoints); dashboards for attach rate; align with service contract architecture (AP-14).

## AP-16: Engagement capture gap

**Symptom in Integrations:** Reps missing inbox, calendar, dialer, or meeting transcription tools  
**Symptom in Adoption:** Low call count, low email count, or huge email-to-call imbalance per rep  
**Symptom in Data Health:** Contact/deal activity timelines sparse on active deals  
**Symptom in Reporting:** Can't compute activity-to-pipeline ratio reliably; coaching conversations have no data to ground them  

**Root cause:** Reps onboarded without a complete tool stack, or tools connected once and disconnected later (token expiry, device change, personal account vs. work account). Not a user fault — a provisioning/governance gap.

**Fix:** (1) Build the per-user coverage matrix (Integrations 5.15). (2) For each missing connection, trigger a user-specific remediation task to the rep and their manager. (3) Establish a monthly "integration health check" where the ops team verifies every active user's connected integrations. (4) Add an onboarding checklist so new reps leave their first week with 100% coverage.

**Severity:** Almost always critical when present at >20% of the sales team. Directly undermines every revenue report that cites activity.

## AP-17: ABM theater

**Symptom in Architecture:** Target Accounts enabled but thousands of accounts flagged (or conversely, 2 accounts flagged)  
**Symptom in Adoption:** Reps not logging differentiated activity against target accounts  
**Symptom in Automation:** No target-account-specific sequences or workflows  
**Symptom in Reporting:** No target-account penetration or win-rate-vs-non-target reports  

**Root cause:** Someone turned on Target Accounts (often during onboarding or a "let's do ABM" kickoff) but the organization never built the discipline around it. Flagging is indiscriminate; reps treat target and non-target accounts identically; win rate on targets is same or worse than non-targets.

**Fix:** Reset the Target Account list down to the count the sales team can realistically work (typically 10–25 per rep). Define tiering. Build target-account-specific cadence and cheerleading rituals. Add the ABM reporting dashboard (Reporting 6.15). Review quarterly — demote targets that get no activity, promote overlooked accounts that do.

**Severity:** High when Target Accounts is enabled but unused. Critical when leadership claims an ABM strategy but evidence shows no differentiation.

## AP-18: ICP shelfware

**Symptom in Architecture:** ICP property exists but has no documented rubric  
**Symptom in Data Health:** ICP fill rate low on active customers; distribution skewed to one tier  
**Symptom in Adoption:** Reps don't filter views by ICP; no ICP-based routing  
**Symptom in Reporting:** Zero reports segment by ICP tier  

**Root cause:** ICP was defined in a marketing offsite, entered HubSpot as a custom property, and then the organization failed to integrate ICP into operational workflows. The property is a vestige of a strategy, not a live input to decisions.

**Fix:** Three steps, in order: (1) Rewrite the ICP rubric as measurable firmographic rules (industry, revenue band, employee count, tech stack, geography). (2) Build a workflow that auto-tiers companies based on the rubric so ICP isn't dependent on rep discipline. (3) Surface ICP everywhere — views, routing SLA, sequences, dashboards — until it drives real decisions. Only then does the property become valuable.

**Severity:** High at minimum. Critical if the portal also has low-quality leads driving wasted rep time, because ICP enforcement is the lever that would fix it.

## AP-19: List graveyard

**Symptom in Architecture:** Hundreds of lists; many orphaned, empty, or owned by deactivated users  
**Symptom in Automation:** Workflows enroll based on lists that no longer mean what they meant when built  
**Symptom in Data Health:** Marketing sends to static lists never refreshed; bounce rates creeping up  
**Symptom in Reporting:** Segmentation inconsistent across reports (each report uses a different "active customers" list)  

**Root cause:** Every marketer/SDR/admin who ever built a list left their artifacts behind. No list governance. No retirement cadence. No naming convention. Lists treated as disposable when they're actually load-bearing for emails and workflows.

**Fix:** (1) Archive all lists with zero dependencies AND zero records; 30-day retention; delete. (2) Reassign or delete lists owned by deactivated users. (3) Enforce a naming convention: `{purpose}_{audience}_{owner}_{YYYY-MM}`. (4) Consolidate duplicate-semantic lists. (5) Establish quarterly list review as part of ops cadence.

**Severity:** Medium for cosmetic sprawl; high when marketing emails are going to stale static lists; critical when list-based workflows have silently broken due to list changes.

## AP-20: Lead leakage

**Symptom in Data Health:** MQLs created but never touched; high time-to-first-touch on inbound leads  
**Symptom in Adoption:** Reps closing leads as "not interested" with no activity logged  
**Symptom in Automation:** No auto-enrollment into follow-up cadence; no reassignment on no-response  
**Symptom in Reporting:** Marketing-sourced pipeline conversion rate far below industry benchmark  

**Root cause:** Lead SLA either doesn't exist, isn't enforced, or has no automation safety net. Lead follow-up depends entirely on rep discipline, which varies wildly across reps. The worst reps drag the aggregate.

**Fix:** (1) Define a lead SLA (e.g., inbound MQL touched within 15 minutes during business hours). (2) Build automation: auto-enroll MQLs into a sequence if not touched within SLA; reassign to a backup rep if no activity within 24 hours; alert manager when queue contains old MQLs. (3) Surface per-rep TTFT and leakage metrics; use in coaching conversations. (4) Require activity-based disposition (can't close a lead without at least one touch logged).

**Severity:** Always critical when present. Leakage is measurable, directly costs money (wasted marketing spend + lost pipeline), and is fixable. It's the highest-ROI area to address in most portals.

## AP-21: Deal push syndrome

**Symptom in Data Health:** High % of open pipeline with close date pushed 2+ times; stalled deals with no activity 14+ days; deals with no next step  
**Symptom in Automation:** No deal safety nets (no stalled-deal workflow, no manager alert on excessive push)  
**Symptom in Adoption:** Reps keep deals open past their natural close date because "closing lost" hurts their number  
**Symptom in Reporting:** Forecast accuracy poor; executive leadership consistently surprised by quarterly results  

**Root cause:** Cultural. Reps optimize for keeping pipeline inflated rather than reflecting reality. Managers don't see push patterns until QBR. The portal has no mechanism to force decisions on stalled deals.

**Fix:** (1) Capture push reasons in a mandatory `push_reason` property whenever close date moves. (2) Build workflow: after 3 pushes, force a decision — progress or close-lost. (3) Dashboard showing push rate per rep, per pipeline, reviewed weekly. (4) Stalled-deal automation: no activity 14+ days triggers a task for the rep and notification for the manager. (5) Culturally: "closing lost cleanly" needs to be celebrated as much as "closing won" — reps need permission to honestly kill deals.

**Severity:** Critical when push rate >25% of open pipeline or forecast accuracy is unknown. High when push rate is 10–25%. The cost is forecast unreliability, which ripples into every business decision.

## AP-22: Methodology theater

**Symptom in Architecture:** Leadership names a methodology (MEDDIC, Challenger, etc.) but structural fields are missing or half-built  
**Symptom in Adoption:** Methodology fields exist but fill rate is low; high variance across reps  
**Symptom in Automation:** No stage gating enforcing methodology capture  
**Symptom in Reporting:** Can't correlate methodology completeness with win rate because the data isn't there  

**Root cause:** Someone attended a sales methodology training, the organization claimed to adopt it, but the CRM never enforced it. Methodology lives in a playbook nobody reads, not in the tool reps use daily.

**Fix:** (1) Embed methodology as required Deal properties with defined picklists where appropriate. (2) Add methodology fields to the default Deal sidebar layout. (3) Use stage gating via workflows — can't move to Proposal without Economic Buyer identified. (4) Build a Deal Health view filtering on methodology completeness; managers review weekly. (5) Correlate methodology completeness with win rate to prove the ROI and build rep buy-in.

**Severity:** High if methodology is claimed but absent. Critical if leadership forecasts based on methodology assumptions that have no data backing them.

## AP-23: Win/loss amnesia

**Symptom in Data Health:** Close reasons unstructured or missing; no competitor capture; "Other" overused  
**Symptom in Reporting:** No win/loss dashboard; aggregate loss reasons unknown  
**Symptom in Adoption:** No evidence of post-close review cadence  
**Symptom in Strategy:** Marketing messaging, product roadmap, and sales playbook evolve on anecdote, not data  

**Root cause:** Closing a deal feels like completion; analyzing the close feels like homework. No one owns the feedback loop. Reasons are captured (if at all) with whatever text happens to be top-of-mind.

**Fix:** (1) Enumerated close-reason picklist, 6–10 values per outcome, with clear definitions. (2) Required property for stage transition to Closed (workflow-enforced). (3) Competitor capture on all closed-lost, via property or association. (4) Monthly win/loss review with Sales, Marketing, Product; documented action items. (5) Decision-makers and champions captured on wins for future reference accounts. (6) For enterprise clients, structured win/loss interviews on deals above a $ threshold.

**Severity:** High when close reason fill rate is <50% or unstructured. The organization is making strategic decisions without the feedback data that would inform them — unglamorous finding, but compounds over time.

## AP-24: Commission data gap

**Symptom in Data Health:** Deal owner changes during open deals; close dates drift post-close; informal or missing deal splits; amount changes after close  
**Symptom in Architecture:** No distinct MRR/ACV/TCV segmentation; no commissionable_date property  
**Symptom in Automation:** No validation workflows locking down closed deals  
**Symptom in Reporting:** Commission payouts can't be tied back to HubSpot cleanly; finance runs parallel spreadsheets  

**Root cause:** Deal records were designed for pipeline management, not commission calculation. The data integrity required for accurate commission is a superset of what's needed for reporting. Without intentional design, the gaps are invisible until commission disputes start.

**Fix:** (1) Lock owner changes on closed deals via permission or workflow. (2) Validate split percentages sum to 100%. (3) Make close date immutable after close. (4) Standardize on line items/products where commissionable amounts vary. (5) Segment recurring revenue into MRR/ACV/TCV properties. (6) Add `commissionable_date` if different from close date. (7) Once data integrity is solid, commission automation (Commission Command or equivalent) becomes a natural engagement phase.

**Severity:** High for any client running commission off HubSpot data without these safeguards. Critical for clients already having commission disputes — the data issue is the root cause. This is a natural QBS Commission Command upsell hook when found.

---

When building the deliverable, cite these anti-patterns by ID when multiple findings share a root cause. Reduces finding count, increases clarity.
