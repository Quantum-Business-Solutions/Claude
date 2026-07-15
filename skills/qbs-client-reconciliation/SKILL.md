---
name: qbs-client-reconciliation
description: Reconcile QBS's internal ticket and time-tracking records against a client's actual HubSpot portal state, with meeting notes as the source-of-truth trail. Use this skill whenever the user wants to audit delivery status for a client, verify what's actually been built vs. what tickets claim, find close-candidate tickets, surface scope creep that wasn't billed, or do a quarterly reality check on an active engagement. Also trigger on phrases like "how far along are we with [client]", "what's actually done in [client's] portal", "close out [client]'s open tickets", "bank the hours for [client]", "reconcile [client]", "where are we with [client]", "is [client]'s work actually done", "catch up on [client] before QBR", or any time the user is trying to bridge the gap between QBS ticket status and client portal reality. This skill protects revenue — every ticket closed on evidence is hours banked cleanly, and every untracked build surfaced is a change-order candidate instead of free work.
---

# QBS Client Reconciliation

A structured skill for reconciling QBS's delivery records (tickets, hours, meeting action items in the QBS HubSpot portal + Client Command) against the live state of a client's HubSpot portal. Produces an evidence-backed report with close-candidate tickets, gap findings, and a clean next-actions list per owner.

## Core principles

These are non-negotiable:

1. **Evidence beats claim.** A ticket marked "done" means nothing without a matching artifact in the client's portal. A property exists, a workflow is enabled, a list has >0 members. No artifact, no close.
2. **Data without usage is a gap.** Properties, workflows, and lists that exist but have zero populated records or zero fires are empty shells — surface them, don't let them masquerade as complete work.
3. **Untracked work is unbilled work.** Portal changes without a matching QBS ticket are either scope creep to document for a change order, or team members working off-ticket. Surface both.
4. **Meeting notes are the source of truth.** When a ticket's content disagrees with what the meeting actually discussed, the meeting wins. Always trace tickets back to their originating discussion.
5. **Same-call completions are common and silent.** Many tickets — especially action items and small roadmap tasks — are completed during the meeting where they were raised, but the ticket never gets closed because the implementer was still on the call. Actively hunt for these. They are the fastest hours to bank cleanly. See `references/same_call_completion.md`.
6. **Timestamp every artifact.** An artifact's `createdAt` must fall within the engagement window to cleanly tie to the ticket. Pre-existing artifacts (built by the client before engagement) must not be counted as QBS work.
7. **Attribution matters.** Verify the QBS seat that created the artifact (`createdById`). Client-built artifacts during the engagement are useful data but not billable QBS deliverables. Known QBS seat IDs are listed in `references/qbs_seats.md`.

## The workflow

Run in six phases. Later phases depend on earlier ones — don't skip ahead.

### Phase 1 — Identify the engagement (required first)

Before pulling anything, establish these five IDs:

| ID | Where it lives | Example |
|---|---|---|
| **QBS Company Record ID** | QBS HubSpot portal 20682069 | `8600659034` |
| **Client HubSpot Portal ID** | Client's own HubSpot | `852584` |
| **Client HubSpot PAT** | User provides | `pat-na1-...` |
| **Client Command Portal UUID** | QBS Client Command | `0ae7e893-c6a2-4dd7-94cc-adb5f0601f86` |
| **Engagement start date** | First ticket createdate or SOW start | `2026-02-26` |

If the user only gives a client name, search `search_crm_objects` on the QBS portal for the company first, then ask for the remaining IDs. Do not guess.

**PAT scope check:** Before running any portal verification queries, test the PAT against `/account-info/v3/details`. If that fails, the PAT is invalid. Request scopes needed for verification: `crm.objects.companies.read`, `crm.objects.contacts.read`, `crm.objects.deals.read`, `crm.schemas.companies.read`, `crm.schemas.contacts.read`, `crm.schemas.deals.read`, `crm.lists.read`, `automation.read`. Missing scopes produce vague 403s — better to enumerate them up front.

### Phase 2 — Inventory QBS tickets

Pull ALL tickets associated to the QBS company record (use `search_crm_objects` with `objectType: tickets`, filter by association to the company record ID, no status filter). Classify each into one of four buckets — see `references/ticket_classification.md` for the decision tree:

- **Recurring meeting placeholders** — weekly/biweekly meeting slots with future due dates. Exclude from work counts.
- **Roadmap tickets** — work scoped from kickoff or discovery. The meat of the engagement.
- **Meeting action items** — tasks spawned from specific calls. Usually small (0.5 hr), time-sensitive, and the first to go stale.
- **BackOffice / admin** — internal time-tracking not tied to client work.

Output: a table with ticket ID, subject, owner (resolved from owner ID via `search_owners`), status, category, due date, estimated hours, and days overdue.

### Phase 3 — Live portal verification

For each non-placeholder open ticket, verify its status against the client's portal. This is the core of the skill. See `references/portal_queries.md` for the full query reference per ticket type.

**Three-check rule.** Every artifact match must pass all three:

1. **Existence** — the property/workflow/list exists in the portal (matching subject keywords)
2. **Timestamp** — `createdAt` is within the engagement window AND not suspiciously far from the ticket's `createdate`. If the artifact pre-dates engagement start, it's pre-existing client work, not QBS delivery. If it post-dates engagement end, something's wrong.
3. **Attribution** — `createdById` matches a known QBS seat (see `references/qbs_seats.md`). If a client seat created it, it's client work even if it happened during engagement.

Any match that fails timestamp or attribution checks gets flagged, not counted.

Verification rules per ticket type:

- **"Create [X] property"** → `GET /crm/v3/properties/{objectType}/{property_name}`. Then three-check. Check population rate on a sample. Zero population = gap.
- **"Build [X] workflow"** → query workflows for matching name. Enabled? Last execution date? Three-check. Zero fires since creation = gap.
- **"Build [X] list"** → query lists, find by name or matching filter. Three-check. Size > 0? Zero = filter logic may be broken or data missing.
- **"Implement [X] integration"** → check the receiving fields on real records, not just that the field exists. E.g., QuickBooks integration is "done" only if `qbo_invoice_id` is populated on actual deals. Three-check the receiving fields.
- **"Scrape / audit / clean [X]"** → these are diagnostic, not buildable. Check for deliverable artifacts (docs in project, notes on company record) rather than portal state.
- **Blocked tickets** → if status hinges on a tier upgrade (Service Hub Pro, Sales Enterprise) or client action (file from client, decision from client), mark BLOCKED with the blocker stated — do not try to verify.

Every verified ticket gets one of five outcomes:
- `✅ DONE` — work shows in portal, passes three-check, close candidate with evidence attached
- `🟢 DONE-ON-CALL` — completed during a meeting, never closed. See Phase 3.5.
- `🟡 PARTIAL` — some artifacts present but gaps (property exists, workflow exists, but no data flowing OR fails timestamp/attribution)
- `🔴 OPEN` — no artifacts found
- `⛔ BLOCKED` — external dependency

### Phase 3.5 — Same-call completion hunt

Many tickets get completed on the call itself and never closed because the implementer was still live on the meeting. This is the single highest-yield category for banking clean hours. See `references/same_call_completion.md` for the full pattern catalog.

For every 🔴 OPEN ticket from Phase 3, run this check:

1. **Find the closest meeting** — use `list_meetings` with the client's Client Command portal UUID, filtered to the ticket's `createdate` ± 14 days. Usually one call will be within 24 hours of ticket creation.
2. **Grep the transcript** for completion phrases (see the reference file's phrase library). Examples: "just did that", "already built", "let me do that now", "taken care of", "already in place", "I'll handle it now", "give me a sec, I'll set that up".
3. **Cross-check against portal state** — if the transcript shows completion language tied to the ticket's subject keywords, AND a matching artifact exists in the portal with a `createdAt` within the meeting window (± 1 day from meeting end), AND attribution is a QBS seat → promote to `🟢 DONE-ON-CALL`.
4. **Note the ambiguous ones** — if completion language appears in the transcript but no matching portal artifact exists, don't close. Flag as "completion claimed in meeting but no portal evidence" — this is either a false-positive claim or the implementer said they'd do it and never did.

The `evidence_found` field in Client Command is known to be unreliable for same-call completions — always run the transcript search yourself, don't rely on the flag alone.

### Phase 4 — Meeting note trace

For every ticket being recommended for close and every open ticket that's overdue, pull the originating meeting from Client Command (`list_meetings` with the portal UUID, then filter by date proximity to ticket creation). The ticket's `createdate` is usually within 24 hours of the meeting that spawned it.

Use `search_knowledge_base` for targeted content searches when a ticket subject is terse. Capture:

- The 2–3 sentences from the transcript where the work was originally requested or agreed to
- Who was on the call (attendee list)
- Any commitments or constraints the client gave that affect scope

Paste these snippets into the reconciliation report for every close candidate — Marko or whoever picks up the ticket needs to see the original context, not just "closed, verified".

### Phase 5 — Gap analysis (inverse check)

This is the step most people skip. Go the other direction:

- **Portal artifacts without tickets** — scan the client's portal for custom properties, workflows, and lists created during the engagement window (use `createdate` on property/list metadata). For each, check if there's a matching QBS ticket. Any that don't match are either (a) already rolled into a larger ticket, (b) scope creep, or (c) team members working off-ticket.
- **Meeting action items that never became tickets** — scan meeting summaries for the engagement window, extract explicit action items, cross-check against ticket subjects. Missed tickets = missed billable work.
- **Recurring themes in meeting notes that have no deliverable** — if the client has raised the same concern in 3+ meetings and no ticket addresses it, surface it.

### Phase 5.5 — Hour burn reconciliation

Pull total `fulfillment_hours_` logged across all tickets for the engagement (including closed ones), plus the prepaid-hours commitment from the SOW. Compute:

- **Total hours consumed** — sum of `fulfillment_hours_` on all engagement tickets
- **SOW commitment** — monthly prepaid hours from the Q2 SOW (typically 40/60/80 depending on tier)
- **Engagement duration** — months elapsed from kickoff to today
- **Expected consumption** — commitment × months elapsed
- **Variance** — consumed minus expected. Positive = over-burning. Negative = under-burning.

Flag levels:

- **>110% of expected** — over-burning. Change order conversation warranted if not already happening. Check gap findings (Phase 5) for untracked work that could explain the excess.
- **75–110%** — healthy pace
- **<75%** — under-burning. Either the client has lower demand than scoped (renewal risk), OR work is being done off-ticket (tickets closed missing hours). Check if fulfillment hours are matching effort expended.

The Q2 Platinum SOW includes a Scope Burn Notice at 75% consumption. If the engagement hit that threshold, verify the notice was sent (check Client Command for the commitment / notification).

Do not close tickets in a way that would trip the burn math — if closing a batch of same-call-completion tickets with 0.25 hr each totals enough to push past 75%, flag that before execution so Shawn can decide whether to trigger the burn notice.

### Phase 6 — Produce the report

See `references/output_template.md` for the exact structure. The report has seven sections:

1. **Reconciliation summary** — counts of close-candidates, done-on-call candidates, real open work, gap findings, BLOCKED tickets
2. **Hour burn snapshot** — SOW commitment vs. consumed, variance, whether the 75% burn notice threshold has been crossed
3. **Close candidates** — per-ticket evidence, meeting quote, proposed close action
4. **Done-on-call candidates** — tickets where the work happened live on a call but never got closed. Highest-yield category for banking hours.
5. **Real open work** — grouped by owner, with live portal status per ticket
6. **Gap findings** — portal artifacts without tickets, tickets without artifacts, data-less shells, missed action items, client-built artifacts mistaken for QBS work
7. **Next actions** — prioritized list for the user (usually: execute the closes, chase the BLOCKED deps, scope the gap findings)

## Executing the closes

After the user reviews the report and approves closes:

- Use HubSpot MCP `manage_crm_objects` against the QBS portal (20682069), not the client portal
- Required fields: `hs_pipeline_stage: "4"` (Closed), `closed_date: <today>`, `hs_resolution: "Work Completed"`
- Always update the `content` field with a structured note: what was verified, list/property/workflow IDs, meeting reference, hours logged, artifact `createdById` (to prove QBS attribution)
- For `🟢 DONE-ON-CALL` closes: the `content` note MUST include the meeting date, participant list, and the transcript snippet showing completion. Also include the portal artifact's `createdAt` timestamp to prove the timing aligned with the call.
- If `fulfillment_hours_` needs to be set:
  - Same-call completions: use the actual build time referenced in the meeting (often 5–15 minutes = 0.25 hr)
  - Verify-only closes (work pre-dated this session): leave `fulfillment_hours_` as-is, don't inflate

For BLOCKED tickets, do NOT close. Update the `content` to document the blocker and the date/owner of the last ping. These need to be followed up, not resolved.

## Safety rails

- **Never** modify the client's portal during reconciliation unless the user explicitly requests a fix. Reconciliation is read-only on the client side.
- **Never** bulk-close tickets without showing the evidence per-ticket and getting user confirmation.
- **Never** propose a close on an artifact whose `createdById` is a client seat — this would misattribute client work as QBS delivery.
- **Never** propose a close on an artifact whose `createdAt` pre-dates the engagement start — this is pre-existing client work.
- If a ticket has `fulfillment_hours_` already logged that disagrees with reconciled evidence (hours billed for work that can't be verified), flag it — don't quietly close.
- If the PAT is missing a scope needed for verification, stop and tell the user to add it — don't silently skip that ticket type.
- If the hour burn (Phase 5.5) crosses the 75% SOW threshold as a result of proposed closes, flag it before execution so the user can decide about the Scope Burn Notice.

## When to suggest a follow-up skill

- If reconciliation surfaces 5+ gap findings that need building → suggest `hubspot-audit` for a structured client-facing deliverable
- If the missed action items came from a specific meeting series → suggest spinning up a weekly ticket-creation cadence review
- If the client has untracked scope creep → suggest a change order conversation using the Q2 SOW change order process
