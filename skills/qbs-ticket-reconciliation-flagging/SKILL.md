---
name: qbs-ticket-reconciliation-flagging
description: Use this skill whenever the QBS team wants to reconcile or clean up a client's open HubSpot tickets by FLAGGING them for closure review (not closing them directly). Trigger when someone says "reconcile [client]", "clean up [client]'s tickets", "which tickets can we close for [client]", "flag [client] tickets", "go through [client]'s open queue", "what's actually done for [client]", or any request to evaluate open Marko-owned tickets against evidence. This skill writes the four AI cleanup properties (ai__ticket_should_be_closed, ai__ticket_should_be_closed_reason, ai__ticket_clean_up_source_to_check, completed_on_client_call) so a human reviews and closes. It NEVER closes, deletes, or reassigns tickets itself. For the older direct-close workflow see qbs-marko-ticket-cleanup; for full delivery reconciliation against a client portal see qbs-client-reconciliation. This skill is the SAFE, flag-only front end to those.
---

# QBS Ticket Reconciliation — Flag-for-Review

## What this skill does (and does NOT do)

This skill evaluates a client's **open, Marko-owned work tickets** and writes a **recommendation** into four HubSpot ticket properties. A human then filters on the flags and closes tickets themselves.

**This skill NEVER:**
- Closes, archives, or deletes a ticket
- Reassigns a ticket or changes its pipeline/stage
- Touches tickets owned by anyone other than the person being reconciled (e.g. Barb, Shawn) — those are surfaced in a list for the human, never modified
- Sets `billable_` / `fulfillment_hours_` (closing + billing is the human's call after review)

**This skill ONLY:** reads tickets, gathers evidence, and writes the four flag fields below.

> Why flag-only: direct closing/deleting has caused real damage (mass-deleting 341 distinct tickets that looked like duplicates; deleting other owners' tickets). Flagging keeps every destructive decision with a human.

---

## The four flag properties (QBS HubSpot portal 20682069, TICKET object)

| Property (internal name) | Label | Type | Allowed values |
|---|---|---|---|
| `ai__ticket_should_be_closed` | AI - Ticket Should be Closed: | single-select | `Yes` / `No` / `Needs Review` |
| `ai__ticket_should_be_closed_reason` | AI - Ticket Should be Closed Reason | free text | (evidence-based explanation) |
| `ai__ticket_clean_up_source_to_check` | AI - Ticket Clean Up Source to Check: | **multi**-select checkbox | `Email` / `Meeting` / `Client HubSpot Portal` / `Manually` / `Other` |
| `completed_on_client_call` | Completed on Client Call: | single-select | `Yes` / `No` |

Multi-select (`source_to_check`) is written as a semicolon-joined string, e.g. `"Client HubSpot Portal;Meeting"`.

**Always write all four** on every ticket evaluated. `should_be_closed` is the verdict, `reason` is the why, `source_to_check` is where the evidence came from, `completed_on_client_call` is Yes only when a meeting summary's "Items Completed on Call" confirms it.

---

## Core heuristic: the VERB in the subject tells you which source to check

Parse the leading verb/intent of the ticket subject, then check that evidence source. This is the heart of the skill.

| Ticket language (verb) | What "done" means | Source to check | source_to_check value(s) |
|---|---|---|---|
| **build, create, configure, set up, automate, import, backfill, clean up, update [in HubSpot], add property/report/dashboard/workflow/object** | The artifact exists in the client's portal | Live client HubSpot portal | `Client HubSpot Portal` |
| **send, notify, nudge, email, deliver, share, reach out, follow up, provide [to a person]** | The message/email actually went out | Outlook email (QBS-side logged engagements) | `Email` (+ `Meeting` if it was a verbal commit) |
| **test, review, validate, walk through, demo, present** | It happened on a call / in the portal | Meeting transcript + portal | `Meeting`, often `Client HubSpot Portal` |
| **investigate, scope, explore, research, evaluate, recommend, propose** | A finding/recommendation was delivered | Meeting or email deliverable trail | `Meeting` or `Email` |
| **discuss, sync, meet, call, kickoff** | The meeting occurred | Meeting transcript | `Meeting` |
| **schedule, update invite, reschedule** | Calendar/admin action | Calendar/email | `Email` or `Manually` |
| **monitor, watch, keep an eye on, continue to track** | Open-ended; rarely closeable | — | `Manually` → usually `No` or `Needs Review` |

When a subject has multiple verbs (e.g. "Build the object **and** notify Haley"), check **all** relevant sources and mark `should_be_closed=Yes` only if every component is satisfied; otherwise `Needs Review` with a reason naming the missing piece.

---

## Meeting-completion detection (the hard part — do this well)

A single meeting summary lists **promises**, not completions. Completion lives in the structure of the summary and across meetings. Client Command meeting summaries (via `get_meeting_intelligence`) contain distinct sections — read them differently:

1. **"✅ Items Completed on Call"** → these were finished/agreed live. For a matching ticket: set `completed_on_client_call = Yes`, `should_be_closed = Yes`, `source_to_check = Meeting`. **Caveat:** "agreed in principle" or "proposed and agreed" is NOT a build completion — it means the *decision* was made on call, but a follow-on build ticket may still be open. Only mark the *decision/discussion* ticket complete, not the *build* ticket.
2. **"🎯 Action Items / Potential Tickets"** → forward promises. These are the open tickets. Do not mark complete from this section alone.
3. **"📅 Expected Agenda for Next Meeting"** → carry-forward list. If a task appears here, it's still open → `should_be_closed = No`, `source_to_check = Meeting`.
4. **`commitments[].status` and `commitments[].evidence_found`** → each commitment carries `status` (open/pending/completed) and an `evidence_found` boolean. `evidence_found=false` means Client Command itself has NOT confirmed it — do not treat as done without checking another source.

**The reliable completion test = cross-meeting + portal:**
- A promise in meeting N that is **acknowledged as done in meeting N+1**, OR **appears under "Items Completed on Call"**, OR is **verifiable in the live portal** → `Yes`.
- A promise that **reappears in the next meeting's agenda/action items** → still open → `No`.
- A "build" promise marked completed-on-call but with no portal artifact → `Needs Review` (the call may have agreed it without it being built).

Always prefer the **most recent** meeting's view, and when meeting evidence conflicts with the live portal, **the portal wins** (it's ground truth for built artifacts).

---

## CRITICAL guardrails (learned the hard way)

1. **Scope to the person being reconciled.** Default owner = Marko Ajder (`466155664`). Tickets owned by Barb, Shawn, or anyone else → list them for the human, never write flags or close them. Confirm owner via `hubspot_owner_id` on every ticket before flagging.
2. **Group/identify clients by ASSOCIATED COMPANY, not the subject prefix.** Subjects can be mis-prefixed or unprefixed (e.g. Spectrum's `1.1`–`8.5` WBS block had no `SPT -` prefix but were all associated to Spectrum Imaging Systems). Pull the ticket→company association to know the true client.
3. **Cross-check CLOSED tickets first — the double-bill trap.** Before flagging an open ticket `Yes`, search the client's **closed** tickets for the same work. Auto-created meeting action-items often sit open while the actual work was executed and billed under a differently-worded closed ticket. If already done+billed elsewhere → flag `Yes` but note in `reason`: "delivered under closed ticket [ID] — do not re-bill." (This protects against double-billing; it happened on Fisher's where 8 reporting tickets were already billed under separate closed tickets.)
4. **Real duplicates match on the FULL subject (prefix + description + date), never a normalized version.** Stripping the client code collapses every client's "Weekly Client Success Meeting" into one false cluster. (This caused a 341-ticket wrongful mass-delete.) Even then, this skill only *flags* suspected dupes (`should_be_closed=Yes`, reason "duplicate of [ID]") — it never deletes.
5. **Verify before flagging Yes.** Never flag `Yes` on inference alone. If you cannot reach the evidence source (e.g. no client portal PAT), flag `Needs Review` with `source_to_check` set to what *should* be checked, and say so in the reason.
6. **Future-dated meeting shells** ("[CODE] - Weekly Client Success Meeting MM/DD/YYYY" with a future date) are working-as-designed → leave alone (no flag, or `should_be_closed=No`).
7. **Exclude the Quantum Internal pipeline** (`11057532`) and closed stages from the open-work set.

---

## Accessing the client's HubSpot portal (Client Command MCP — preferred path)

Do NOT ask the user to paste a raw client PAT. Client Command stores client credentials and exposes them through three audited tools. Use these to verify "build" tickets against the live client portal.

1. **`list_client_credentials`** — `{ portal_id (UUID) }` → lists which external services have stored credentials for a portal. Returns **metadata only**: service name, `automation_enabled` (true/false), and a token **mask** (e.g. `****28dc`). Never the full PAT. Use this first to see what's available.
2. **`check_client_credential`** — `{ portal_id (UUID), service (e.g. "hubspot") }` → returns `exists: true/false` and `automation_enabled: true/false`. Use to confirm a specific client has a usable HubSpot credential before attempting portal verification.
3. **`call_hubspot_as_client`** — `{ portal_id, path (e.g. "/crm/v3/objects/companies"), method, reason (REQUIRED) }` → makes the HubSpot call on the client's behalf. Automatically uses the client's stored PAT when present, falls back to QBS's global token when not, and **logs every call**. The `reason` parameter is **mandatory** on every call — it's the audit-trail field stating why the data was needed (e.g. `reason: "Verify form_leads custom object exists for Fisher's ticket 45278610991 reconciliation"`).

**Rules for credential use:**
- Always pass a specific, truthful `reason` on every `call_hubspot_as_client` — it's audit-logged.
- Prefer `check_client_credential` before portal verification; if `exists: false`, you cannot verify "build" tickets against the portal → flag those `Needs Review` with `source_to_check = Client HubSpot Portal` and note the missing credential in the reason.
- The portal_id here is the Client Command **portal UUID**, not the numeric HubSpot portal ID. Resolve it from the portal record / executive dashboard.
- Reads only for verification (GET). Never use `call_hubspot_as_client` to mutate a client's portal during a reconciliation flag pass.

---

## Procedure

1. **Identify the client's real ticket set** by associated company (resolve company ID from a sibling ticket or the skill table in `qbs-hubspot-ticketing`). Pull all Marko-owned open tickets associated to that company.
2. **Split** into: work tickets vs. meeting shells; Marko-owned vs. other-owned (set the latter aside in a list for the human).
3. **Confirm portal access + pull closed tickets.** Run `check_client_credential(portal_id, "hubspot")`. If `exists: true`, you can verify "build" tickets via `call_hubspot_as_client` (always with a `reason`). Pull the client's closed tickets (for the double-bill cross-check) and recent meeting intelligence (`get_meeting_intelligence` / `list_meetings`).
4. **For each open Marko work ticket:**
   a. Read the verb → pick the evidence source(s).
   b. Check that source (portal artifact / Outlook email / meeting section).
   c. Cross-check closed tickets for prior completion.
   d. Write all four flag fields with a specific, evidence-citing reason.
5. **Summarize** for the human: counts by `should_be_closed` value, the list of other-owners' tickets you did NOT touch, any double-bill catches, and what still needs a portal PAT to verify.
6. **Stop.** The human filters on `ai__ticket_should_be_closed = Yes` in HubSpot, reviews reasons/sources, and closes.

---

## Writing the fields (HubSpot API)

Batch update (≤100/call) to `POST /crm/v3/objects/tickets/batch/update`. Example per-ticket payload:

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

Multi-source example: `"ai__ticket_clean_up_source_to_check": "Client HubSpot Portal;Meeting"`.

Never include `hs_pipeline_stage`, `closed_date`, `billable_`, or `fulfillment_hours_` in a flag write — those belong to the human's close action.

---

## Worked example (Fisher's Technology)

- **"FIS - Create and configure a custom lead object"** → verb *create* → check portal → `form_leads` object found, 430 records → `should_be_closed=Yes`, source=`Client HubSpot Portal`, completed_on_call=`No`, reason cites the object + record count.
- **"FIS - Notify Haley when reports are available"** → verb *notify* → check email → if no sent email found → `should_be_closed=Needs Review`, source=`Email`, reason "no sent email to Haley located; confirm delivery."
- **"FIS - Build custom reports showing lead sources"** → verb *build* → check portal AND closed tickets → reporting work already billed under closed ticket "Begin building reports/contact views for Haley" (5/11, 1.17h) → `should_be_closed=Yes`, source=`Client HubSpot Portal;Manually`, reason "delivered under closed ticket [ID] — do not re-bill."
- **"FIS - Monitor for HubSpot betas (zip-to-state)"** → verb *monitor* → `should_be_closed=No`, source=`Manually`, reason "open-ended monitoring task; no completion criteria."
