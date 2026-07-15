# Build Activity Digest

A separate capability from the audit itself. Produces a time-bounded view of what's been created, modified, or touched in the portal — useful for:

- QBS team tracking their own work across client portals (weekly/monthly reviews)
- Client-facing "here's what we built this period" reports
- Handoff/takeover documentation when starting or ending an engagement
- Detecting drift: things that were built without sanction

## When to use the activity digest

The digest is a standalone mode, NOT a phase of the audit. Trigger it when the user asks:

- "What's been built in {portal} in the last 30 days?"
- "Show me recent activity in {client}'s portal"
- "What did we change last week?"
- "Give me a monthly report of work done in {portal}"
- "What's new in HubSpot since {date}?"
- "Track what our team has been building"

If the user asks for an audit AND a digest together, run them as separate outputs — don't conflate them.

## Time windows

Standard windows the digest supports:
- **Last 7 days** — weekly team review
- **Last 30 days** — monthly client report or internal ops review
- **Last 90 days** — quarterly engagement summary
- **Last 365 days** — annual retrospective
- **Custom range** — if user specifies start/end dates (for engagement reporting aligned to SOW dates, for example)

Default to 30 days if the user doesn't specify.

## What to capture

For each asset type, pull items where `createdAt`, `updatedAt`, or equivalent timestamp falls within the window. Capture who made the change when available (createdByUserId, updatedByUserId).

### Core assets

**Workflows:**
- New workflows created
- Workflows activated or deactivated
- Workflows modified (structure change, not just enrollment counts)
- Creator and last modifier per workflow

**Properties:**
- New custom properties created (by object: Contact, Company, Deal, Ticket, custom objects)
- Properties modified (picklist values changed, requirement toggled, type changed)
- Properties archived or deleted
- Property owner if derivable

**Lists:**
- New lists created (active and static, separately)
- Lists modified (criteria changed)
- Lists archived
- Owner of each

**Deal stages, pipelines, lifecycle stages:**
- New pipelines created
- New stages added to existing pipelines
- Stage probability changes
- Lifecycle stage additions (Pro+)

**Reports and dashboards:**
- New reports created
- Reports modified
- New dashboards
- Dashboards modified (widgets added/removed)
- Ownership

**Forms and landing pages:**
- New forms
- Forms modified (fields added/removed/reordered)
- New landing pages published
- Landing page edits

**Emails:**
- New marketing email drafts created
- Emails sent during the window (not just created — actually sent)
- A/B tests launched

**Sequences:**
- New sequences
- Sequences modified (steps added/removed, templates changed)
- Sequences activated or deactivated

**Playbooks (Sales Pro+):**
- New playbooks
- Playbook edits

**Snippets, templates, documents:**
- New sales templates
- New snippets
- New documents uploaded to Sales Documents

**Custom objects and schemas:**
- New custom objects defined
- Custom object schema changes
- New association labels

**Integrations:**
- New apps installed
- Apps uninstalled
- Integration re-authentications (where detectable)

**User and team changes:**
- New users invited/activated
- Users deactivated
- Team structure changes
- Permission set changes

### Data-volume signals (context for the above)

Include these as context metrics, not individually enumerated:

- New contacts created in window (count and top sources)
- New companies created in window
- New deals created in window (count and total $ value)
- New tickets created in window

These help frame whether a quiet "no workflows built" week was actually quiet (low activity portal) or suspicious (high activity, no build response).

## Output structure

### Mode A: QBS internal digest (markdown)

For team tracking across portals. Tight, scannable.

```markdown
# {Client} — Build Activity Digest
**Window:** {start_date} to {end_date} ({N} days)
**Generated:** {today}

## Summary
- {X} new workflows, {Y} modified
- {X} new properties, {Y} archived
- {X} new reports, {Y} new dashboards
- {X} new lists, {Y} archived
- {X} new forms/landing pages
- {X} sequences created or modified
- {X} integration changes

Top contributors:
- {user}: {count} total changes — {brief description of type of work}
- {user}: {count} total changes — ...

## Workflows
**New ({count}):**
- {name} — created by {user} on {date} — purpose: {if derivable}
- ...

**Modified ({count}):**
- {name} — last edited by {user} on {date}
- ...

**Activated/Deactivated ({count}):**
- {name} — {status change} by {user} on {date}

## Properties
**New ({count}):**
- Contact.{property_name} — {type} — created by {user} on {date}
- Deal.{property_name} — ...

**Modified ({count}):**
- ...

**Archived ({count}):**
- ...

## Lists
...

## Reports & Dashboards
...

## Forms & Landing Pages
...

## Sequences & Templates
...

## Integrations
...

## Users & Teams
...

## Data volume context
- {N} new contacts (top sources: ...)
- {N} new deals totaling ${X}
- {N} new tickets

## Drift flags
{Anything built that looks unsanctioned or off-process:}
- Workflow {name} created by {user} with no associated ticket/task reference
- Property added without governance process
- Integration installed without documented approval
```

### Mode B: Client-facing progress report (Word doc, optional)

For monthly or quarterly client reports showing QBS's work. Uses QBS branding from `assets/brand.md`.

Structure:
1. **Cover page** — "Build Progress Report" / client / period
2. **Executive summary** — count summary, headline deliverables
3. **What we built this period** — organized by theme (data architecture, automation, reporting, adoption enablement) not by asset type
4. **By the numbers** — summary metrics from the digest
5. **Upcoming** — what's planned next (if the user provides it — don't invent)

## Implementation notes

**Source identification:** Where possible, identify whether the changes were made by:
- QBS team members (match against known QBS HubSpot user emails if the user provides them)
- Client team members
- Other contractors/agencies
- Integration-based (API user, marketplace app making changes)

This attribution is gold for the "what did QBS do this month" use case. If you can't resolve users to categories, just list them by name.

**Purpose inference:** For workflows, properties, and lists, infer purpose from naming conventions, descriptions, and enrollment criteria. If a workflow is named "30-day renewal reminder" that's self-documenting. If it's named "Test 5" flag it as unclear purpose. Don't fabricate purposes that aren't evident.

**Drift detection:** Flag anything that looks like it was built outside normal process:
- New properties with no description
- Workflows named "test" / "copy of" / "untitled"
- Lists owned by deactivated users (also covered in Architecture 2.17)
- Integrations installed by users who aren't admins
- Sequences created by users with no send history
- Dashboards with only one viewer (the creator)

**Growth tracking over time:** If the client has an accumulating set of these digests, the skill can eventually show build velocity trends (averaging X workflows per month, property creation slowing, etc.). Not critical for v1 but worth designing for.

## Cross-reference with audit

If both an audit and a digest are being produced in the same session:
- Don't duplicate content — the digest is about recency, the audit is about state
- Use the digest to inform audit findings (a workflow built 5 days ago is less likely to be "orphan" than one built 2 years ago)
- Use the audit to flag concerning digest items (a new property added this week to a portal that already has 287 contact properties is a governance flag)

## Recommended delivery cadence

- **Weekly digest** → posted to QBS internal Slack / logged in Client Command as meeting intelligence
- **Monthly digest** → shared with client account owner, basis for the monthly check-in
- **Quarterly digest** → client-facing Word doc, part of QBR deliverable stack
- **Custom window digest** → ad hoc, e.g., end of an engagement for final handoff report
