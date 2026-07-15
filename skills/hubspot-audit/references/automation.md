# Dimension 4: Automation

Assesses workflow and sequence health. Automation is where silent failures accumulate — a workflow can be broken for a year without anyone noticing.

## Checks to run

### 4.1 Workflow inventory

**Query:** Total workflows, active vs. inactive, by type (contact, company, deal, ticket, quote, custom object).

**Baseline:** Any portal with >100 active workflows needs governance. Any portal with >300 active workflows is almost certainly carrying dead weight.

### 4.2 Workflows in error state

**Query:** Workflows with errored actions in last 30 days. Fetch error count per workflow.

**Thresholds:**
- Healthy: 0 workflows with persistent errors
- Flag: 1–3 workflows with errors older than 7 days
- Critical: >3 workflows erroring for >30 days (especially if producing side effects)

**Impact:** A workflow sending internal notifications that silently errors for a month means dozens of missed alerts. Quantify in human-readable terms.

### 4.3 Orphaned workflows

**Query:** Active workflows with zero enrollments in last 90 days.

**Finding:** List them. They're candidates for deletion. Note which are seasonal (annual reminders, end-of-year campaigns) vs. truly dead.

### 4.4 Re-enrollment + goal mismatch

**Query:** Workflows with re-enrollment enabled, where the re-enrollment trigger property is also used as the goal property.

**Finding:** Classic anti-pattern. Causes contacts to re-enter the workflow immediately after completing the goal. Always flag.

### 4.5 Workflows without exit criteria

**Query:** Workflows that enroll contacts on a filter but have no suppression list, no goal, and no unenrollment condition.

**Finding:** Contacts pile up "inside" these workflows. Hard to remove without breaking in-flight automation.

### 4.6 Notification spam risk

**Query:** Count internal-notification actions across all active workflows per owner/role.

**Threshold:** If a specific rep is likely receiving >50 workflow-triggered notifications/day, flag. Reps will start filtering = all notifications ignored.

### 4.7 Email sends from workflows

**Query:** For workflows sending emails:
- Is the email a one-off or a workflow-specific email?
- Is suppression list applied (unsubscribed, bounced, non-marketing)?
- Is send-time optimization or smart-send enabled?
- Is there frequency capping?

**Finding:** Workflow emails without frequency capping are the #1 cause of unexpected unsubscribe spikes.

### 4.8 Lifecycle stage workflows

**Query:** Workflows that SET lifecycle stage. There should typically be few of these, with clear ownership.

**Flag:**
- Multiple workflows setting the same lifecycle stage with different criteria (fighting each other)
- Workflows that SET a lifecycle stage EARLIER than the current stage (forces regression — see Data Health 1.6)
- Manual lifecycle stage override by specific users defeating the workflows

### 4.9 Lead routing

**Query:** Workflows or routing logic that assigns contact/deal owners.

**Flag:**
- Round-robin with inactive users in rotation
- Territory logic not updated in last 180 days
- No fallback rule for records matching no territory
- Weighted routing without documented weights

**Impact:** Leads assigned to a deactivated rep sit unassigned. Directly costs pipeline.

### 4.10 Data quality workflows

**Query:** Are there workflows doing data hygiene? Examples:

- Capitalize name fields
- Standardize country/state
- Phone number formatting
- Lifecycle stage inference
- Missing-field notifications to data owners

**Finding:** A portal with 0 data hygiene workflows will always have the data health issues flagged in Dimension 1. Recommend this as a foundational package.

### 4.11 Sequence health (separate from workflows)

**Query:**
- Total sequences, sequences with 0 enrollments in 90 days
- Sequences with steps >8 (usually too long)
- Sequences with unsubscribe rate >0.5% (high)
- Sequences with reply rate <2% (low, questionable value)
- Sequences that have no exit condition for "received reply"

**Finding:** Long sequences + no exit = the classic anti-pattern causing unsubscribes.

### 4.12 Chatflow/bot health

**Query:** Chatflows with errors or broken integrations. Chatbots routing to inactive users.

### 4.13 Integration workflow dependencies

**Query:** Workflows that trigger based on properties set by integrations. List the integration → property → workflow dependency chain.

**Finding:** If an integration is disconnected or changes behavior, these workflows silently stop working. Document them explicitly.

### 4.14 Custom code actions (Ops Hub Pro+)

**Query:** Workflows with custom code actions. Check for:
- Hardcoded API keys (huge security issue)
- Calls to deprecated API endpoints
- No error handling
- No logging

### 4.15 Data sync and Ops Hub workflows

If Ops Hub:
- Data sync health
- Failed syncs in last 30 days
- Data quality automations (format phone, dedupe logic, etc.) — present? functioning?

### 4.16 Follow-up cadence automation

Check whether the portal has automation that catches lead follow-up failure before it becomes leakage.

**Queries:**

- Workflows that enroll new MQLs into a sequence or task cadence automatically
- Workflows that reassign leads on no-response after N hours/days
- Workflows that alert a manager when a rep's queue contains leads older than SLA
- Workflows that auto-close out contacts/deals with extended inactivity (graveyard workflow)
- Sequence templates specifically designed for new inbound vs. outbound vs. re-engagement

**Thresholds:**
- Healthy: MQL-to-sequence auto-enrollment exists; no-response reassignment exists; manager alert for SLA breach exists
- Flag: some auto-enrollment but no reassignment or alerts
- Critical: No automated follow-up safety net at all — lead follow-up is purely rep-driven, which means it's rep-variable

**Impact:** Automation is what makes SLA enforceable. Without it, following up depends on every rep remembering every lead. They won't. The lead leakage finding in Data Health 1.17 is a consequence of this automation gap.

### 4.17 Deal progression safety nets

Companion automation check to Data Health 1.16 (deal progression).

**Queries:**

- Workflows that auto-create tasks when deals go N days without activity
- Workflows that alert managers when deals are pushed >N times or stall >N days
- Workflows that force a `next_step` text property to be filled when moving between stages
- Workflows that flag deals as "at risk" based on stage duration, push count, or activity gap
- Does the portal have a deal-health scoring mechanism (manual property or HubSpot AI-based)?

**Thresholds:**
- Healthy: at least one "stalled deal" safety net workflow, manager alerts on excessive push, deal-health visibility somewhere
- Flag: one of the above present, others missing
- Critical: no deal-progression automation — reps and managers find out about stalled deals too late

**Impact:** Without automation, stalled deals rot silently. Manager catches them at end-of-quarter review, by which time it's too late to do anything. Automation moves the intervention point from "after the miss" to "before the miss."

## Dealer-channel-specific checks

- **Service contract renewal workflows:** 30/60/90 day pre-renewal automation present?
- **Equipment lifecycle workflows:** equipment approaching end-of-life → replacement opportunity creation?
- **Meter-read escalation workflows:** anomalous reads → service ticket?

## Output format

```yaml
- id: automation_04_reenroll_goal_conflict
  dimension: automation
  severity: critical
  title: "Workflow 'Re-engage Dormant Leads' has re-enrollment + goal collision"
  evidence: "Workflow enrolls on property X change, goal is property X matches Y. 1,240 contacts re-enrolled in last 30 days causing ~3,400 duplicate emails."
  impact: "Unsubscribe spike in last 30 days (0.8% vs 0.3% baseline). ~18 hard-to-recover leads lost. Email sender reputation at risk."
  recommendation: "Change goal property to separate 'Engagement Achieved' boolean set by a sub-workflow OR disable re-enrollment."
  effort: hours
  tier_requirement: none
```
