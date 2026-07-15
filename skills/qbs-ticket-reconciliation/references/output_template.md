# Reconciliation Report Template

The structure for report output (Flag summaries use the top sections; Full
Reconciliation uses all of it). Keep it concise — this is for Shawn or the
account owner to scan in 2 minutes and act on, not a formal deliverable.
Inclusion test: if Shawn read a line aloud to the client, could he back it
with an ID, a timestamp, or a quote? If not, it doesn't go in.

## Report structure

```markdown
# [Client] Reconciliation — [Date] (dry run — no closes executed)

## Calibration
Last pass ([date]): [N] Yes → [a] accepted, [o] overturned, [p] pending.
Overturn [x]% → [normal / tightened] rules this pass.
Per-cell hit rate: [e.g. 12/12 Yes/T1 closed by human; 3/7 Yes/T3].
[One line per overturn: root cause + adjustment.]

## State of the Queue (vs. last [mode] run, [date], [N] days ago)
| Metric | Now | Last | Δ |
|---|---|---|---|
| Open tickets (scoped) | | | |
| Flagged Yes awaiting approval | | | |
| Flagged Needs Review | | | |
| Oldest open work ticket (days, by createdate) | | | |
| Action items >14d overdue | | | |
| Blocked on client | | | |
| Previously decided (honored rulings) | | | |

One-line read: [improving / holding / degrading — and why]. First tracked
run → say so and baseline; never fake a delta. (Full dashboard + snapshot
mechanics: memory.md)

## Verdict × tier grid (how to work this report)
| | T1 | T2 | T3/T4 |
|---|---|---|---|
| **Yes** | Review list, then approve — double-bill and billing-review items still need individual sign-off | Skim reason, then decide | (must be 0 — doctrine) |
| **Needs Review** | — | Human decides | Human decides |
| **No** | Safely ignore | Ignore | Sanity-check |

Counts per cell here; work top-left first. Even Yes/T1 is never
"batch-close on sight" — the double-bill/billing-review carve-outs and the
arm step (mode-close.md) always apply.

- **Close candidates:** [N] tickets verified done ([N] T1 / [N] T2)
- **Done-on-call candidates:** [N] tickets completed during meetings but never closed
- **Real open work:** [N] tickets (excluding [M] blocked)
- **Blocked:** [N] tickets waiting on [client action / tier upgrade / external dep]
- **Gap findings:** [N] items — portal artifacts without tickets, data shells, missed action items, attribution issues
- **Double-bill catches:** [N] — routed to Shawn, excluded from bulk approval
- **Recommended next action:** [one-line direction for user]

Counts must cross-foot: Yes + Needs Review + No = tickets evaluated = flags written.

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

### Ticket [ID] — [Subject]                                   [tier badge, e.g. T1-portal]
**Owner:** [Name] · **Hrs logged:** [X] · **Due:** [date]
**Verified:** [specific portal evidence — property IDs, list IDs, list sizes, workflow IDs — queried this pass]
**Attribution:** [seat name — client-portal user ID resolved by email domain this pass, per qbs-facts.md]
**Artifact createdAt:** [timestamp] — within engagement window ✓
**Meeting origin:** [Meeting title, date] — "[direct quote from transcript where work was requested]"
**Double-bill:** [no closed-ticket overlap (searched N) | "delivered under closed ticket [ID] — do not re-bill."]
**Proposed close:**
- `hs_pipeline_stage`: [this ticket's pipeline's closed stage — looked up by label, see mode-close.md]
- `closed_date`: [intended date, noon UTC per doctrine]
- `hs_resolution`: Work Completed
- `fulfillment_hours_`: [hours if applicable]
- `content` addendum: [proposed close note with createdById, artifact timestamp]

---

## 2. Done-on-Call Candidates ([N])

Tickets where the work was completed during a meeting but never closed — the
highest-yield category for banking hours (typically 0.25 hr each).

### Ticket [ID] — [Subject]                                   [T1 / T2 badge]
**Meeting:** [title, date, Zoom meeting ID or Client Command KB ID]
**Transcript snippet:**
> [Speaker]: "[line 1]"
> [Speaker]: "[line 2 — the completion signal]"
> [Speaker]: "[line 3 — confirmation]"

**Portal evidence:** [artifact, created at timestamp, within the canonical same-call window ✓ (evidence-standards.md)]
**Attribution:** [QBS seat, resolved in the client portal]
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
**Suggested next touch:** [who should ping whom; escalate to Shawn if raised 3+ runs — cadences.md]

---

## 5. Gap Findings

### Portal artifacts without matching tickets ([N])
[Property / workflow / list name, created date, createdById, estimated effort — either rolled into larger ticket, scope creep, or team working off-ticket]

### Tickets with hours logged but no portal artifact ([N])
[Flag for review — billed work that can't be verified — each row: ticket ID, hours logged, subject, status]

### Data-less shells ([N])
[Properties/workflows/lists that exist but are empty — either filter logic broken or data load pending. Check with Marko.]

### Attribution issues ([N])
[Artifacts created by non-QBS seats during the engagement window that are currently being credited to QBS work. Could be client-built (excluded from close evidence) or mystery seats needing resolution — verify with Shawn.]

### Missed meeting action items ([N])
[Items discussed in meetings with no ticket created — candidate for retroactive ticketing or scope discussion]

### Recurring client concerns without deliverable ([N])
[Themes raised in 3+ meetings that have no corresponding ticket.]

---

## 6. Could Not Verify ([N]) — the honesty section

[Per item: which source was unreachable (no credential / no transcript / API
error), what was NOT concluded as a result, and the unblock action. This
section always exists if anything was skipped — silent gaps are the legacy
failure mode this skill replaces.]

---

## 7. Next Actions

Prioritized list:

1. **Approve closes** — the [N] close candidates above, per bucket/ticket (arm protocol in mode-close.md). Banks [X] hours cleanly and reduces open count by [%].
2. **Approve done-on-call closes** — the [N] done-on-call candidates. Banks [Y] hours sitting unclaimed.
3. **Chase blockers** — [specific next pings]
4. **Decide on gap findings** — [specific asks, usually around scope creep / change order]
5. **Burn notice decision** — if 75% threshold crossed or crossing: [recommendation]
6. **Follow-up reconciliation** — [date suggestion for next cycle, typically quarterly or before QBR]
```

## Tone and length

- Plain language, no jargon beyond what's on the tickets themselves
- Evidence is specific (IDs, counts, dates, `createdAt` timestamps, resolved
  attribution), never hand-wavy; every reason carries its tier prefix
- Direct quotes from meeting transcripts are 1–3 sentences max — pull the most
  incriminating/clarifying line, not the full exchange
- Keep the full report under 3 screens of scrolling for most engagements
- Defensibility over completeness: one wrong number costs the trust of all the
  others

## After execution

If Close mode ran, append the execution addendum: requested vs. confirmed
table, per-failure detail, sample-audit result, and confirmation that the
audit note was posted to the company record (`references/mode-close.md`).

## When to append a portal-side deliverable

If the user is going into a QBR or client meeting based on this
reconciliation, offer (but don't assume) to generate a client-facing status
document:

- **Internal reconciliation** (this report) — raw truth for Shawn/Marko/Patrick
- **Client status doc** — polished version with just completed work, what's in
  flight, and what needs the client's input. Drops gap findings, calibration,
  billing flags, and blockers that reflect QBS-side issues.

Suggest using the `sow-creator` skill or a similar polished output for the
client-facing version.
