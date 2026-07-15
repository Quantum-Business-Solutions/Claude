# Reconciliation Report Template

The structure to use for Phase 6 output. Keep it concise — this is for Shawn or the account owner to scan in 2 minutes and act on, not a formal deliverable.

## Report structure

```markdown
# [Client] Reconciliation — [Date]

## Summary

- **Close candidates:** [N] tickets verified done in portal
- **Done-on-call candidates:** [N] tickets completed during meetings but never closed
- **Real open work:** [N] tickets (excluding [M] blocked)
- **Blocked:** [N] tickets waiting on [client action / tier upgrade / external dep]
- **Gap findings:** [N] items — portal artifacts without tickets, data shells, missed action items, attribution issues
- **Recommended next action:** [one-line direction for user]

---

## Hour Burn Snapshot

| Metric | Value |
|---|---|
| SOW monthly commitment | [X] hrs |
| Engagement duration | [Y] months |
| Expected consumption | [X × Y] hrs |
| Actual logged fulfillment hours | [Z] hrs |
| Variance | [Z - X×Y] hrs ([+/-N]%) |
| 75% burn threshold | [crossed / not crossed / would cross if proposed closes executed] |

**Read:** [over-burning / healthy / under-burning — 1 line]. [If over-burning: recommend change order discussion, reference gap findings. If under-burning: recommend check-in with client re: demand.]

---

## 1. Close Candidates ([N])

For each:

### Ticket [ID] — [Subject]
**Owner:** [Name] · **Hrs logged:** [X] · **Due:** [date]
**Verified:** [specific portal evidence — property IDs, list IDs, list sizes, workflow IDs]
**Attribution:** [QBS seat name — Owner ID on QBS side or User ID on client side]
**Artifact createdAt:** [timestamp] — within engagement window ✓
**Meeting origin:** [Meeting title, date] — "[direct quote from transcript where work was requested]"
**Proposed close:**
- `hs_pipeline_stage`: [this ticket's pipeline's closed stage — looked up by label, see mode-close.md]
- `closed_date`: [intended date at 12:00 UTC]
- `hs_resolution`: Work Completed
- `fulfillment_hours_`: [hours if applicable]
- `content` addendum: [proposed close note with createdById, artifact timestamp]

---

## 2. Done-on-Call Candidates ([N])

These are tickets where the work was completed during a meeting but the ticket was never closed afterward. This is the highest-yield category for banking hours — typically 0.25 hr each, but they add up.

### Ticket [ID] — [Subject]
**Meeting:** [title, date, Client Command KB ID]
**Transcript snippet:**
> [Speaker]: "[line 1]"
> [Speaker]: "[line 2 — the completion signal]"
> [Speaker]: "[line 3 — confirmation]"

**Portal evidence:** [artifact, created at timestamp, within meeting window ✓]
**Attribution:** [QBS seat]
**Proposed close:** 0.25 hrs, "Work Completed", content notes meeting snippet

---

## 3. Real Open Work ([N])

Grouped by owner. For each owner:

### [Owner Name] ([N] tickets, est [X] hrs)

| Ticket ID | Subject | Due | Days Overdue | Status | Blocker |
|-----------|---------|-----|--------------|--------|---------|
| 44462734161 | Reconcile QB product library | 4/21 | 2 | 🔴 OPEN | — |
| 43141859718 | Create competitive contract tracking | 3/31 | 23 | 🟡 PARTIAL | Fields exist, no data flowing |

Below the table, for each 🟡 PARTIAL or ⛔ BLOCKED ticket, a short paragraph:

**Ticket [ID]:** [what's missing and what would unblock]

---

## 4. Blocked ([N])

Broken out separately because these need comms, not execution:

### Ticket [ID] — [Subject]
**Blocker:** [specific]
**Blocking party:** [client / QBS / external vendor]
**Last touch:** [date of last update or ping — from meeting notes if available]
**Meetings where this came up:** [count and dates]
**Suggested next touch:** [who should ping whom, escalate to Patrick if raised 3+ times]

---

## 5. Gap Findings

### Portal artifacts without matching tickets ([N])
[Property / workflow / list name, created date, createdById, estimated effort — either rolled into larger ticket, scope creep, or team working off-ticket]

### Tickets with hours logged but no portal artifact ([N])
[Flag for review — billed work that can't be verified — each row: ticket ID, hours logged, subject, status]

### Data-less shells ([N])
[Properties/workflows/lists that exist but are empty — either filter logic broken or data load pending. Check with Marko.]

### Attribution issues ([N])
[Artifacts created by non-QBS seats during the engagement window that are currently being credited to QBS work. Could be client-built (should be excluded from close evidence) or mystery seats needing resolution.]

### Missed meeting action items ([N])
[Items discussed in meetings with no ticket created — candidate for retroactive ticketing or scope discussion]

### Recurring client concerns without deliverable ([N])
[Themes raised in 3+ meetings that have no corresponding ticket.]

---

## 6. Next Actions

Prioritized list:

1. **Execute closes** — approve the [N] close candidates above. Banks [X] hours cleanly and reduces open count by [%].
2. **Execute done-on-call closes** — approve the [N] done-on-call candidates. Banks [Y] hours that are sitting unclaimed.
3. **Chase blockers** — [specific next pings]
4. **Decide on gap findings** — [specific asks, usually around scope creep / change order]
5. **Burn notice decision** — if 75% threshold crossed or crossing: [recommendation]
6. **Follow-up reconciliation** — [date suggestion for next cycle, typically quarterly or before QBR]
```

## Tone and length

- Plain language, no jargon beyond what's on the tickets themselves
- Evidence is specific (IDs, counts, dates, `createdAt` timestamps, `createdById` attribution), never hand-wavy
- Direct quotes from meeting transcripts are 1–3 sentences max — pull the most incriminating/clarifying line, not the full exchange
- Keep the full report under 3 screens of scrolling for most engagements

## When to append a portal-side deliverable

If the user is going into a QBR or client meeting based on this reconciliation, offer (but don't assume) to generate a client-facing status document:

- **Internal reconciliation** (this report) — raw truth for Shawn/Marko/Patrick
- **Client status doc** — polished version with just completed work, what's in flight, and what needs the client's input. Drops gap findings and blockers that reflect QBS-side issues.

Suggest using the `sow-creator` skill or a similar polished output for the client-facing version.
