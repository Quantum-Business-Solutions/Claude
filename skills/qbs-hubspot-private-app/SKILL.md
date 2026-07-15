---
name: qbs-hubspot-private-app
description: Use this skill when the QBS team operates on a HubSpot portal via a private app token (PAT) — for client portals OR the QBS internal portal (`20682069`) when the OAuth MCP lacks scope (CMS blog posts, landing pages, site pages, campaigns, marketing events, Automation v4, bulk Properties API, anything returning `REQUIRES_REAUTHORIZATION`). Trigger on `pat-na1-...` / `pat-na2-...` / `pat-eu1-...` tokens, mentions of "private app", "client portal", "their HubSpot", "Quantum's PAT", "QBS PAT", `CLIENT_HUBSPOT_TOKEN`, or `QBS_HUBSPOT_TOKEN`. For atlas-theme page work use `qbs-atlas-page-builder` — that skill depends on this for tokens. For pure CRM work on QBS (contacts, companies, deals, tickets, calls, meetings, emails, notes, tasks), the OAuth MCP is the default — only use this when the MCP is missing scope. For ANY client portal work this skill is mandatory; the MCP connector is bound to QBS portal `20682069` and will silently corrupt analysis if used against a client.
---

# QBS HubSpot Private App Toolkit

## What this skill does

Lets Claude operate against any HubSpot portal via a private app token (PAT) using direct REST API calls — for two scenarios:

1. **Any client portal** — bypasses the HubSpot MCP connector (which is bound to QBS portal `20682069` and would silently corrupt analysis if used against a client).
2. **QBS internal portal (`20682069`) when the OAuth MCP isn't enough** — the OAuth connector only exposes CRM objects. For CMS, marketing, Automation v4, and bulk Properties API operations, the connector returns `REQUIRES_REAUTHORIZATION` or doesn't expose the endpoint at all. Use this skill instead of asking the user to reauth.

Standardizes the cold-start sequence — verify → scope sweep → ready to work — so every connection takes about 15 seconds instead of a back-and-forth.

## When to use vs. when not to use

**USE this skill when:**
- A `pat-na1-...` / `pat-na2-...` / `pat-eu1-...` token appears in chat
- The user mentions a client portal, private app, or any HubSpot work in a non-QBS portal
- The user says things like "connect to Gallaway's HubSpot," "audit CCi's portal," "check what's in TAG's instance"
- The user is working in the QBS portal (`20682069`) AND needs CMS / blog / landing page / site page / campaign / marketing event data — the OAuth MCP returns `REQUIRES_REAUTHORIZATION` for these
- The user is working in the QBS portal AND needs Automation v4 (`/automation/v4/...`), bulk Properties API, or another endpoint not exposed by the OAuth MCP
- The user references `QBS_HUBSPOT_TOKEN` or "Quantum's PAT" / "QBS PAT"

**DO NOT use this skill when:**
- The user is doing pure CRM work on the QBS portal (contacts, companies, deals, tickets, calls, meetings, emails, notes, tasks) AND the OAuth HubSpot MCP connector is sufficient — use the MCP for that, it's faster
- No token is available and none can be generated — escalate, don't fake calls

**MCP-vs-PAT decision rule for QBS portal:** Default to the MCP. Reach for the PAT the moment the MCP returns `REQUIRES_REAUTHORIZATION`, the endpoint isn't exposed as an MCP tool, or the user is asking for CMS / marketing / Automation v4 / bulk operations.

## Critical rules

**Never use the HubSpot MCP connector for client portals.** It's bound to QBS portal `20682069`. Every call against a client portal goes through `bash_tool` + `curl` + the PAT instead. If you find yourself reaching for `hubspot:*` tools while a client PAT is in scope, stop.

**For the QBS portal, default to MCP — fall back to PAT when the MCP can't.** Pure CRM work on QBS goes through the MCP. The moment you hit `REQUIRES_REAUTHORIZATION`, an unexposed endpoint, or a CMS/marketing/Automation v4/bulk-operations need, switch to this skill. Don't ask the user to reauth the connector if a PAT is available.

**Always verify the portal before doing anything else.** Step 1 is non-negotiable. The portal ID returned by `/account-info/v3/details` must match the expected target — either the client the user named, or `20682069` for QBS internal work. If it doesn't match expectation, stop and confirm — wrong-portal analysis is worse than no analysis.

**Never write without explicit confirmation.** Read operations are fine to run on instruction. Write operations (POST/PATCH/DELETE) require the propose-table-then-wait pattern documented in `references/write-protocol.md`. No exceptions. This applies equally to QBS portal and client portals.

**Flag the rotation reminder once.** When a token is pasted directly in chat (not via env var), remind the user once that it should be rotated after the session. Don't nag on every turn.

## The standard sequence

### Step 0 — Locate the token

The skill accepts the token from these sources, in priority order:

1. **Client env var** — `$CLIENT_HUBSPOT_TOKEN` if set (use for client portal work)
2. **QBS env var** — `$QBS_HUBSPOT_TOKEN` if set (use for QBS internal portal work)
3. **Pasted in chat** — extract the `pat-na1-...` / `pat-na2-...` / `pat-eu1-...` string

If multiple are present, use the one matching the user's stated target (client portal vs. QBS internal). If a token is pasted in chat, use it but flag the rotation reminder once.

### Step 1 — Verify (always run first)

```bash
bash /mnt/skills/user/qbs-hubspot-private-app/scripts/verify.sh "$TOKEN"
```

Returns portal ID, data center, time zone, account type (STANDARD / PROFESSIONAL / ENTERPRISE), currency. Report these to the user as a small table and **ask them to confirm the portal ID matches the expected target** before proceeding.

- If the user named a client, the portal ID should match that client (and the data-center prefix `pat-na1-...` should be consistent with what's expected).
- If the work is QBS internal, the portal ID should be `20682069`. Call this out explicitly — "Confirmed: QBS internal portal" — so it's clear we're not in a client portal.
- If the portal ID doesn't match expectation in either case, stop and confirm before any further action.

### Step 2 — Scope sweep

```bash
bash /mnt/skills/user/qbs-hubspot-private-app/scripts/scope-sweep.sh "$TOKEN"
```

Probes a standard set of read endpoints. Returns a table of `[OK]` / `[FAIL]` per endpoint with the missing-scope error message extracted from any 403s. Translate the 403s into specific scope toggles using `references/scope-map.md` so the user has a clean ask-list for the client.

After scope sweep, **stop and wait for the next instruction** unless the user gave an explicit follow-up request in the same turn.

### Step 3 — Source the helpers (when running follow-up calls)

```bash
source /mnt/skills/user/qbs-hubspot-private-app/scripts/helpers.sh
export TOKEN="$TOKEN"
hs_get "/crm/v3/properties/contacts" | jq '.results | length'
```

The helpers (`hs_get`, `hs_post`, `hs_patch`, `hs_delete`) wrap the bearer-token boilerplate so follow-up commands are one-liners. They also auto-format JSON responses and surface non-200 status codes prominently.

### Step 4 — Run the recipe

For common audit tasks (property counts, workflow inventory, list inventory, pipeline mapping, automation usage, deal stage breakdown, etc.), see `references/audit-recipes.md`. Each recipe is a copy-pasteable bash block using `hs_get`. Don't reinvent — check the recipe file first.

### Step 5 — Write operations (only on explicit instruction)

Read `references/write-protocol.md` before performing any POST/PATCH/DELETE. The protocol is non-negotiable: propose the change as a markdown table, wait for explicit "yes," then execute and confirm. Never batch writes without per-batch confirmation.

## QBS internal portal (`20682069`) — when to reach for the PAT

The OAuth HubSpot MCP connector exposes only CRM objects on the QBS portal. For everything below, use this skill instead — don't ask the user to reauth the connector.

| Need | PAT endpoint | MCP status |
|---|---|---|
| Blog posts | `/cms/v3/blogs/posts` | `REQUIRES_REAUTHORIZATION` |
| Blog authors | `/cms/v3/blogs/authors` | not exposed |
| Blog tags | `/cms/v3/blogs/tags` | not exposed |
| Landing pages | `/cms/v3/pages/landing-pages` | `REQUIRES_REAUTHORIZATION` |
| Site pages | `/cms/v3/pages/site-pages` | `REQUIRES_REAUTHORIZATION` |
| Campaigns | `/marketing/v3/campaigns` | `REQUIRES_REAUTHORIZATION` |
| Marketing events | `/marketing/v3/marketing-events` | `REQUIRES_REAUTHORIZATION` |
| Workflows / Automation v4 | `/automation/v4/flows` | not exposed |
| Bulk Properties API | `/crm/v3/properties/{objectType}/batch/*` | not exposed |
| HubDB tables | `/cms/v3/hubdb/tables` | not exposed |
| Files / file manager | `/files/v3/files` | not exposed |
| Email templates | `/cms/v3/source-code/...` | not exposed |
| Email events / opens / clicks | `/email/public/v1/events` | not exposed |

**Rule of thumb:** if the QBS MCP returns `REQUIRES_REAUTHORIZATION`, or if you need an endpoint the MCP doesn't expose at all, switch to this skill rather than asking the user to reauth.

For atlas-theme page creation, migration, or any operation on `layoutSections` (website pages and landing pages on the QBS portal), use the `qbs-atlas-page-builder` skill — it encodes the clone-and-mutate pattern, the `dnd_area`-name rule, the dual-href CTA structure, and the atomic publish flow specific to atlas page work. That skill depends on this one for token setup, then layers the page-specific safety rules on top.

## File map

```
qbs-hubspot-private-app/
├── SKILL.md                     ← you are here
├── scripts/
│   ├── verify.sh                ← Step 1: portal verification
│   ├── scope-sweep.sh           ← Step 2: endpoint probe
│   └── helpers.sh               ← Step 3: hs_get/hs_post/hs_patch/hs_delete
└── references/
    ├── scope-map.md             ← endpoint → scope → UI toggle name
    ├── audit-recipes.md         ← property counts, workflow inventory, etc.
    └── write-protocol.md        ← propose → confirm → execute pattern
```

## Quick-reference: most common one-liners

After `source helpers.sh; export TOKEN="..."`:

```bash
# Property counts across standard objects
for obj in contacts companies deals tickets; do
  echo "$obj: $(hs_get "/crm/v3/properties/$obj" | jq '.results | length')"
done

# Workflow count
hs_get "/automation/v4/flows" | jq '.results | length'

# Pipeline stages for deals
hs_get "/crm/v3/pipelines/deals" | jq '.results[] | {label, stages: [.stages[].label]}'

# List count
hs_get "/crm/v3/lists?count=500" | jq '.lists | length'
```

For longer or more complex queries, go to `references/audit-recipes.md`.

## Token hygiene

- **Don't echo tokens in command output.** Use `"$TOKEN"` in scripts, never embed the literal value.
- **Remind the user once** if the token came from chat paste, not env var: "Please rotate this PAT in HubSpot → Settings → Integrations → Private Apps after we're done — it's now in chat history."
- **Never write a token to disk.** Helpers and scripts read from env or argv only.

## When something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `401 Unauthorized` on every call | Token revoked, expired, or wrong format | Have user generate a new PAT; check it starts with `pat-` |
| `403` on a specific endpoint | Missing scope | Look up the endpoint in `references/scope-map.md`; tell user which scope to add |
| `403` with "scope isn't available for public use" | Tier/beta limitation, not a scope toggle | Check account type from Step 1; may require Marketing/Service Hub tier upgrade |
| Portal ID doesn't match expected client | Wrong PAT given | STOP. Confirm with user before any further action. |
| `429 Rate Limited` | Burst on Standard account (100/10s) | Add `sleep 1` between calls, or use the recipe's pagination helper |
