# Ticket Classification

A decision tree for bucketing every QBS ticket found on a client's company record.

## The four buckets

### 1. Recurring meeting placeholders

**Signals:**
- Subject follows a pattern like `[CLIENT] - Weekly Client Success Call`, `[CLIENT] - Biweekly Strategy`
- `hs_ticket_category`: `Client - Meeting`
- `source_type`: `Client Meeting`
- `ticket___estimated_execution_time`: 0.5 (half-hour slots)
- Due dates spaced at regular intervals in the future (7-day, 14-day cadence)
- Owner typically a non-delivery seat (account manager, Patrick Dodge, the account owner)

**What to do:** Exclude from all work counts. These close naturally as the meetings occur. Flag ONLY if a placeholder is past due and not yet closed — that means a meeting was missed or not recapped.

### 2. Roadmap tickets

**Signals:**
- Created at or near kickoff, usually within 2 weeks of engagement start
- `hs_ticket_category`: `Client - HubSpot On-Going` (or similar ongoing category)
- Specific technical scope in the subject: "Create X property", "Build Y workflow", "Implement Z integration"
- Due dates cluster on month-ends or quarter-ends
- Owner is typically the primary implementer (Marko Ajder for HubSpot builds)

**What to do:** These are the core of the engagement. Every single one should be verified against live portal state in Phase 3. Expect to find a mix of DONE / PARTIAL / OPEN / BLOCKED.

### 3. Meeting action items

**Signals:**
- `hs_ticket_category`: `Action Item from Meeting`
- Subject often prefixed with `[CLIENT] -` and describes a specific task
- Created within hours of a specific meeting
- Small `ticket___estimated_execution_time` (0.25 – 1.0 hours)
- Due dates are typically 5–7 days after creation (time-sensitive)
- Owner is whoever committed to the task on the call

**What to do:** These go stale fastest. Any action item >14 days overdue warrants a direct conversation with the owner. Verify exactly as roadmap tickets, but flag staleness prominently.

### 4. BackOffice / admin

**Signals:**
- Subject references internal work: "Time tracking", "BackOffice", "Hours review", "Weekly hours"
- `hs_ticket_category`: `Quantum Internal Operations` (the canonical internal category — subjects say "BackOffice" but the category value does not)
- `billable_`: Non-Billable
- No direct connection to a client deliverable

**What to do:** Exclude from work verification. Mention in the report only if there's an anomaly (e.g., excessive non-billable hours logged against a billable engagement).

## Edge cases

### The ambiguous ticket

Sometimes a ticket doesn't fit cleanly — a meeting action item that's been rolled into roadmap work, or a roadmap ticket that's actually just an admin task. When in doubt:

- If it has a specific technical deliverable → treat as roadmap
- If it's time-sensitive and came from a specific call → treat as action item
- If it has no client-facing artifact → treat as admin

### The placeholder that became real work

Occasionally a "weekly meeting" ticket gets repurposed — Marko logs actual build hours against it because the meeting turned into a working session. Signal: `fulfillment_hours_` > 0.5 on a meeting-category ticket, or a long `content` field describing real work. Treat as a roadmap ticket for verification purposes, but note the miscategorization.

### The zombie ticket

A ticket created months ago, no hours logged, no meeting note reference, owner has left the company or rolled off the account. These accumulate and pollute open counts. Flag for archival/reassignment, don't try to verify.

## Output of this phase

A classification table like this:

```
| Ticket ID | Subject | Category | Owner | Due | Hrs Est | Days Overdue | Bucket |
|-----------|---------|----------|-------|-----|---------|--------------|--------|
| 44462734161 | Reconcile QB product library | Action Item | Marko Ajder | 4/21 | 0.5 | 2 | MeetingAction |
| 43141859718 | Create competitive contract tracking | Roadmap | Marko Ajder | 3/31 | — | 23 | Roadmap |
| 42593957394 | SMP - Weekly Client Success Call | Meeting | Patrick Dodge | 8/12 | 0.5 | -111 | Placeholder |
```

Run work-verification on Roadmap and MeetingAction buckets only.
