# Mode: Flag

The default pass. Evaluates a client's open, in-scope tickets and writes the
four flag properties so a human can filter, review, and approve closes in
HubSpot. Writes flags ONLY — never stage, dates, billing, or hours.

## Procedure

1. **Resolve the client's real ticket set** by associated company — resolve
   the company live per `references/client-discovery.md` (search companies by
   name, confirm via ticket associations; never trust a static roster or a
   subject prefix). Pull all open tickets for the target owner (default
   Marko — confirm the ID live, `references/qbs-facts.md`) associated to that
   company. Look up pipeline stages by label first (doctrine); exclude
   internal pipelines (by label fragment) and closed stages.
2. **Load memory + calibration.** Read the latest snapshot note and decision
   log for this scope (`references/memory.md`) — tickets with a `RULING` line
   are honored, not re-litigated. Score the previous pass and set this pass's
   posture (`references/calibration.md`).
3. **Split** into work tickets vs. meeting shells, and target-owner vs.
   other-owner (set the latter aside in a list for the human — never flag
   them).
4. **Confirm evidence access.** `check_client_credential(portal_uuid,
   "hubspot")` for portal verification; pull the client's closed tickets (for
   the double-bill check) and meeting evidence (Zoom `search_meetings` +
   Client Command `get_meeting_intelligence` / `list_meetings`).
5. **Evaluate each open work ticket** per
   `references/evidence-standards.md`: verb → source(s) → check → cross-check
   closed tickets → assign the tier → write all four flags with a
   tier-prefixed, citing reason.
6. **Summarize for the human:** verdict × tier grid, other-owner tickets not
   touched, double-bill catches, anything unverifiable and why
   (`references/output_template.md`), then the snapshot note
   (`references/memory.md`).
7. **Stop.** The human filters `ai__ticket_should_be_closed = Yes`, reviews,
   and either closes in the UI or comes back and asks for Close mode.

## Writing the flags

Before the first write of a pass, confirm the four properties exist
(`GET /crm/v3/properties/tickets/ai__ticket_should_be_closed` etc.). If any
is missing or its options changed, stop and report — do not create properties
or invent option values (`references/failure-modes.md`).

Read each ticket's current flag values first and record them in the pass
audit log (before → after) — this makes every flag write reversible and lets
the calibration readback distinguish "human overturned my flag" from "I
overwrote my own flag."

Batch update, ≤100 per call: `POST /crm/v3/objects/tickets/batch/update`
(QBS portal 20682069, via the QBS-side connection — never
`call_hubspot_as_client`).

```json
{
  "id": "45278610991",
  "properties": {
    "ai__ticket_should_be_closed": "Yes",
    "ai__ticket_should_be_closed_reason": "[T1-portal] Custom lead object 'form_leads' (2-230043398) exists in portal 243570690 with 430 records + 40 props, created 2026-03-02 by QBS seat (M. Ajder, client-portal user 12048713). No closed ticket covers this work (searched 41 closed). [2026-07-15 run]",
    "ai__ticket_clean_up_source_to_check": "Client HubSpot Portal",
    "completed_on_client_call": "No"
  }
}
```

Multi-source: `"Client HubSpot Portal;Meeting"` (semicolon-joined).

Reason style: `[tier-source] verdict basis; evidence with IDs/dates/counts;
caveats; billing note if any.` 1–3 sentences, every sentence defensible.
Always name what was checked AND what was not; include the double-bill result
on every `Yes`; state uncertainty plainly ("claimed but unverified") — no raw
JSON, no adjectives doing the work of evidence.

**A flag write NEVER includes `hs_pipeline_stage`, `closed_date`,
`hs_resolution`, `billable_`, or `fulfillment_hours_`.** Those belong
exclusively to the approved close action — bundling them into a flag write is
how "flagging" becomes silent closing.

## Approval carve-outs

When the human starts approving from this pass's output: double-bill catches
and anything routed to Shawn's billing review are EXCLUDED from bulk
approval, even if flagged `Yes` — each needs individual confirmation
(execution rules: `references/mode-close.md`).

## Worked examples (Fisher's Technology)

- **"FIS - Create and configure a custom lead object"** → verb *create* →
  portal → `form_leads` object found, 430 records, QBS attribution, in-window
  → `Yes`, reason prefixed `[T1-portal]`, source `Client HubSpot Portal`,
  on-call `No`.
- **"FIS - Build custom reports showing lead sources"** → verb *build* →
  portal AND closed tickets → already billed under closed ticket "Begin
  building reports/contact views for Haley" → `Yes`, `[T1-closed-ticket]`,
  source `Client HubSpot Portal;Manually`, reason carries "delivered under
  closed ticket [ID] — do not re-bill."
- **"FIS - Notify Haley when reports are available"** → verb *notify* →
  email → no sent email found → `Needs Review`, `[T3]`, source `Email`,
  reason "no sent-email engagement to Haley located; confirm delivery."
- **"SPT - Set up lifecycle sync"** (claimed done on 6/3 call) →
  `Needs Review`, `[T3-claim-only]`, "'already built' on 6/3 transcript, but
  no matching workflow in portal (checked v3+v4)." Source
  `Client HubSpot Portal;Meeting`.
- **"FIS - Monitor for HubSpot betas"** → verb *monitor* → `No`, `[T4]`,
  source `Manually`, reason "open-ended monitoring task; no completion
  criteria."
- **"KPI - Weekly Client Success Meeting 09/12/2026"** (future-dated) → `No`,
  working-as-designed future meeting shell — leave it alone.

## What this mode never does

Close, delete, reassign, change pipeline/stage, or set
`billable_`/`fulfillment_hours_`. Those live in Close mode, after human
review. Future-dated meeting shells are working-as-designed — leave them
alone (`No` or no flag).
