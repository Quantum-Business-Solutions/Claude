# Mode: Full Reconciliation

The engagement-level audit: reconcile QBS's tickets, hours, and meeting trail
against the client's live portal. Produces the evidence-backed report in
`references/output_template.md`, writes the four flag properties on every
evaluated ticket, and hands close execution to `references/mode-close.md`
after review. Run quarterly, before QBRs, or whenever "where are we with
[client]" needs a real answer (cadence checklist: `references/cadences.md`).

Core principles (in addition to the doctrine in SKILL.md):

1. **Evidence beats claim** — a ticket marked done means nothing without a
   matching portal artifact.
2. **Data without usage is a gap** — empty properties/workflows/lists are
   shells, not completed work.
3. **Untracked work is unbilled work** — portal changes with no ticket are
   change-order candidates or off-ticket work. Surface both.
4. **Same-call completions are common and silent** — hunt them; they're the
   fastest hours to bank cleanly.

## Phase 1 — Identify the engagement (required first)

Establish before pulling anything:

| ID | Where it lives |
|---|---|
| QBS Company Record ID | QBS portal 20682069 (search by company name — `references/client-discovery.md`) |
| Client HubSpot Portal ID | client's portal |
| Portal access | Client Command stored credential (preferred) or `CLIENT_HUBSPOT_TOKEN` env var — see SKILL.md doctrine |
| Client Command Portal UUID | Client Command portal record |
| Engagement start date | first ticket createdate or SOW start |

Verify access with a harmless read (`/account-info/v3/details` via
`call_hubspot_as_client` or the PAT). Confirm the portal ID matches the
expected client — wrong portal = stop (`references/failure-modes.md`). If
scopes are missing, list which ticket types can't be verified and flag those
`Needs Review` rather than skipping silently. Scopes needed for full
verification: `crm.objects.{companies,contacts,deals}.read`,
`crm.schemas.{companies,contacts,deals}.read`, `crm.lists.read`,
`automation.read`.

Then load memory (snapshot + decision log, `references/memory.md`) and run
the calibration readback (`references/calibration.md`).

## Phase 2 — Inventory QBS tickets

Pull ALL tickets associated to the QBS company record (no status filter).
Classify per `references/ticket_classification.md` (placeholders / roadmap /
action items / admin). Resolve owners and pipeline stages by label. Output:
table of ID, subject, owner, stage label, category, due date, est. hours,
days overdue.

## Phase 3 — Live portal verification

For each non-placeholder open ticket, verify against the client's portal
(read-only). Queries per ticket type: `references/portal_queries.md`.
Evidence bar: the tiers and three-check rule in
`references/evidence-standards.md`.

Outcomes: `✅ DONE` (close candidate w/ T1 evidence) · `🟢 DONE-ON-CALL`
(Phase 3.5) · `🟡 PARTIAL` (artifact exists, gaps remain) · `🔴 OPEN` ·
`⛔ BLOCKED` (external dependency — record the blocker, don't verify further).

## Phase 3.5 — Same-call completion hunt

For every 🔴 OPEN ticket: find the meeting nearest its `createdate` (±14
days) via Zoom `search_meetings` / Client Command `list_meetings`, search the
transcript for completion phrases, and cross-check the portal for a matching
artifact inside the canonical same-call window (defined once, in
`references/evidence-standards.md`). All three signals + QBS attribution →
promote to 🟢 DONE-ON-CALL. Completion language with no artifact → "claimed
on call, no portal evidence" — review, not close. Full phrase library and
false-positive guards: `references/same_call_completion.md`. Don't trust
Client Command's `evidence_found` flag — run the transcript search yourself.

## Phase 4 — Meeting note trace

For every close candidate and overdue open ticket, pull the originating
meeting (ticket `createdate` is usually within 24h of it). Capture the 2–3
transcript sentences where the work was requested, the attendee list, and any
scope constraints. These quotes go in the report — reviewers need original
context, not just "verified."

## Phase 5 — Gap analysis (the step everyone skips)

Go the other direction:
- **Portal artifacts without tickets** — custom properties/workflows/lists
  created in the engagement window with no matching ticket → rolled into a
  bigger ticket, scope creep, or off-ticket work.
- **Meeting action items that never became tickets** — extract from summaries,
  cross-check subjects. Missed tickets = missed billable work.
- **Recurring themes with no deliverable** — same concern in 3+ meetings, no
  ticket → surface it.

## Phase 5.5 — Hour burn reconciliation

Sum `fulfillment_hours_` across ALL engagement tickets (incl. closed). Get
the monthly prepaid commitment from the CURRENT SOW (pull it from Client
Command / the SOW doc — don't assume a quarter or a tier).

- Expected = commitment × months elapsed; variance = consumed − expected.
- **>110%** over-burning → change-order conversation; check Phase 5 gaps for
  unbilled work explaining the excess. **75–110%** healthy. **<75%**
  under-burning → renewal risk or off-ticket work; check both.
- If the SOW has a Scope Burn Notice threshold (Platinum: 75%), check whether
  it was crossed and whether the notice went out — and if proposed closes
  would push past it, flag BEFORE execution (also enforced in mode-close's
  burn-notice check).

## Phase 6 — Produce the report

Structure: `references/output_template.md`. Also write the four flag
properties on every evaluated ticket (rules: `references/mode-flag.md`) so
the review can happen in HubSpot as well as in the report, and write the
snapshot note + any decision-log entries (`references/memory.md`). Then stop —
closes go through `references/mode-close.md` after the user approves.
