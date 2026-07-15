# QBS facts — verify live, never trust a table

Load at scope-lock when you need concrete IDs (owners, pipelines, portals) or
credential paths. Hardcoded rosters killed the legacy skills: a 38-client code
table went stale within months, timezone offsets were winter-only, "Q2 SOW"
logic ran in Q3. Rule for this file: **everything here is a starting hint with
an as-of date; anything that can be fetched live, is fetched live.**
As-of: 2026-07-15.

## Portals and credentials

- **QBS portal**: `20682069`. The HubSpot MCP connector is bound to this portal ONLY.
  All ticket reads, flag writes, closes, snapshot notes happen here.
- **Client portals**: via Client Command's audited tools (`check_client_credential`,
  `call_hubspot_as_client` with mandatory `reason`) keyed by the Client Command portal
  UUID — not the numeric HubSpot ID (resolve via `list_portals` / `get_portal`).
  Fallback: `CLIENT_HUBSPOT_TOKEN` env var; verify which portal it hits via
  `GET /account-info/v3/details` before trusting results — in BOTH directions (a client
  read must not land on 20682069; a flag/close write must). Never ask for a PAT in
  chat. Client portals are read-only during reconciliation.

Client identity itself (which companies are active, code↔company mapping) is derived
live every run — see `references/client-discovery.md`. No roster lives here.

## People (owner IDs in QBS portal 20682069 — refresh live)

| Person | Owner ID (hint) | Role in this skill |
|---|---|---|
| Marko Ajder | 466155664 | Default reconciliation subject (implementer) |
| Shawn Peterson | 103243559 | Billing/money escalations; the approver who arms closes |
| Patrick Dodge | 316713255 | Client success — blocked-on-client chases |
| Barb Peterson | 390820388 | Implementation support — list, never modify |

Refresh: `GET /crm/v3/owners?limit=100`, filter emails on `@thequantumleap.business` /
`@quantumbusinesssolutions.com`. If a name here doesn't resolve live, trust the live
pull and note the drift. **Recycled-ID check:** before scoping a pass to an owner ID,
confirm the live owner record for that ID still matches the person's email — owner IDs
can be recycled, and flagging on a stale ID would hit a stranger's queue. If it doesn't
match, stop and tell the user.

**Owner ID ≠ createdById.** Owner IDs identify ticket ownership in the QBS portal.
`createdById` on artifacts is a *user* ID in whichever portal the artifact lives — and
every client portal issues its own user IDs. For client-portal attribution, pull that
portal's `GET /crm/v3/owners?limit=100`, match by QBS email domain, cache the mapping
for the run. Never present a QBS owner ID as client-portal attribution evidence.

**Mystery seats** (a `createdById` that is neither QBS nor a current client employee):
resolve the user details via the owners API. Known integration emails
(`zapier-integration@...`, HubSpot bot) → QBS work if QBS configured the integration,
client work otherwise. Historical users → timestamp-check against the engagement
window (in-window = possibly a former QBS contractor; pre-window = client legacy).
Anything unresolvable → "attribution uncertain, verify with Shawn" — never a close
basis.

## Pipelines (map by label, always)

`GET /crm/v3/pipelines/tickets` at the start of every run — if this lookup fails, the
pass aborts (`references/failure-modes.md`). Known landscape (hint only): Support,
On-Boarding for HubSpot, Quantum Internal (`11057532` as-of above), Sales as a Service.
Exclusion rule: any pipeline whose label contains "internal" (case-insensitive) is out
of cleanup scope — the label fragment is the mechanism, the ID is only a hint.
Closed-stage detection is by label ("Closed", "Completed Tickets", …), never by
numeric ID.

## Ticket properties in play

- Flag properties: `ai__ticket_should_be_closed`, `ai__ticket_should_be_closed_reason`,
  `ai__ticket_clean_up_source_to_check` (multi-select, semicolon-joined),
  `completed_on_client_call`.
- Close-action properties (human-approved writes only): `hs_pipeline_stage` (by label
  lookup), `closed_date` (noon UTC — SKILL.md doctrine), `hs_resolution`, optionally
  `fulfillment_hours_`.
- Classification hints: `hs_ticket_category` (Action Item from Meeting / Client -
  Meeting / Quantum Internal Operations…), `source_type`,
  `ticket___estimated_execution_time`, `billable_`.
- Staleness/age: `createdate` only. `hs_lastmodifieddate` is workflow-churned noise.

## Time

All HubSpot date-property writes use noon UTC — the rule and its DST incident history
live in SKILL.md doctrine; don't restate the math here, point there.
