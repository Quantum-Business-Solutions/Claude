# Mode: Flag

The default pass. Evaluates a client's open, in-scope tickets and writes the
four flag properties so a human can filter, review, and approve closes in
HubSpot. Writes flags ONLY — never stage, dates, billing, or hours.

## Procedure

1. **Resolve the client's real ticket set** by associated company (resolve
   the company ID from a sibling ticket or `qbs-hubspot-ticketing`'s client
   table). Pull all open tickets for the target owner (default Marko,
   `466155664`) associated to that company. Look up pipeline stages by label
   first (doctrine #2); exclude internal pipelines and closed stages.
2. **Split** into work tickets vs. meeting shells, and target-owner vs.
   other-owner (set the latter aside in a list for the human — never flag
   them).
3. **Confirm evidence access.** `check_client_credential(portal_uuid,
   "hubspot")` for portal verification; pull the client's closed tickets (for
   the double-bill check) and recent meeting intelligence
   (`get_meeting_intelligence` / `list_meetings`).
4. **Evaluate each open work ticket** per `references/evidence-standards.md`:
   verb → source(s) → check → cross-check closed tickets → write all four
   flags with a citing reason.
5. **Summarize for the human:** counts by verdict, other-owner tickets not
   touched, double-bill catches, anything unverifiable and why.
6. **Stop.** The human filters `ai__ticket_should_be_closed = Yes`, reviews,
   and either closes in the UI or comes back and asks for Close mode.

## Writing the flags

Batch update, ≤100 per call: `POST /crm/v3/objects/tickets/batch/update`
(QBS portal 20682069).

```json
{
  "id": "45278610991",
  "properties": {
    "ai__ticket_should_be_closed": "Yes",
    "ai__ticket_should_be_closed_reason": "Custom lead object 'form_leads' (2-230043398) exists in portal 243570690 with 430 records + 40 props. Verified live; no prior closed ticket covers it.",
    "ai__ticket_clean_up_source_to_check": "Client HubSpot Portal",
    "completed_on_client_call": "No"
  }
}
```

Multi-source: `"Client HubSpot Portal;Meeting"` (semicolon-joined).

## Worked examples (Fisher's Technology)

- **"FIS - Create and configure a custom lead object"** → verb *create* →
  portal → `form_leads` object found, 430 records → `Yes`,
  source `Client HubSpot Portal`, on-call `No`, reason cites object + count.
- **"FIS - Notify Haley when reports are available"** → verb *notify* →
  email → no sent email found → `Needs Review`, source `Email`, reason "no
  sent email to Haley located; confirm delivery."
- **"FIS - Build custom reports showing lead sources"** → verb *build* →
  portal AND closed tickets → already billed under closed ticket "Begin
  building reports/contact views for Haley" → `Yes`, source
  `Client HubSpot Portal;Manually`, reason "delivered under closed ticket
  [ID] — do not re-bill."
- **"FIS - Monitor for HubSpot betas"** → verb *monitor* → `No`, source
  `Manually`, reason "open-ended monitoring task; no completion criteria."

## What this mode never does

Close, archive, delete, reassign, change pipeline/stage, or set
`billable_`/`fulfillment_hours_`. Those live in Close mode, after human
review. Future-dated meeting shells are working-as-designed — leave them
alone (`No` or no flag).
