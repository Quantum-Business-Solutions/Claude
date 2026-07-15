# Portal Verification Queries

How to verify each ticket type against a live client HubSpot portal. Use these patterns when running Phase 3 of the reconciliation.

## Authentication

Preferred: Client Command's `call_hubspot_as_client` — pass the portal UUID,
the API `path`, and a truthful `reason` (audit-logged, mandatory). It uses the
client's stored credential without exposing it.

Fallback: a client PAT already present in the `CLIENT_HUBSPOT_TOKEN` env var:

```bash
curl -H "Authorization: Bearer $CLIENT_HUBSPOT_TOKEN" "https://api.hubapi.com/..."
```

Never ask the user to paste a raw PAT into chat, and never use the HubSpot MCP
connector for a client's portal — it's bound to QBS's portal (20682069) and is
only for QBS-side ticket reads/writes. The curl examples below show the
fallback form; when going through Client Command, use the same paths via
`call_hubspot_as_client`.

## Verification patterns by ticket type

### "Create [X] property"

**Query:**
```bash
# Check existence
curl -H "Authorization: Bearer $CLIENT_HUBSPOT_TOKEN" \
  "https://api.hubapi.com/crm/v3/properties/{objectType}/{property_name}"
```

- `{objectType}`: `companies`, `contacts`, `deals`, `tickets`
- `{property_name}`: the internal name (not label)

**Grading:**
- 404 → 🔴 OPEN (property doesn't exist)
- 200 with matching fieldType → ✅ exists, now check population
- Population check: search records filtered by `IS_KNOWN` for this property, get `total`. Divide by total record count.
  - 0% populated → 🟡 PARTIAL (exists but unused)
  - <10% populated → 🟡 PARTIAL (data quality gap)
  - ≥10% populated → ✅ DONE

**Example evidence to capture:**
> `qbo_invoice_id` property exists (created 2026-03-15) but populated on 0/1,268 deals — integration not writing back.

### "Build [X] workflow"

**Query:**
```bash
# List workflows and filter
curl -H "Authorization: Bearer $CLIENT_HUBSPOT_TOKEN" \
  "https://api.hubapi.com/automation/v3/workflows" | jq '.workflows[] | select(.name | contains("X"))'
```

v4 workflow engine uses a different endpoint — try v3 first, fall back to inspecting via the lists API if the workflow is actually a list-driven automation.

**Grading:**
- No matching workflow → 🔴 OPEN
- Workflow exists, `enabled: false` → 🟡 PARTIAL (built but not live)
- Workflow exists, enabled, no executions since creation → 🟡 PARTIAL (not triggering)
- Workflow exists, enabled, firing regularly → ✅ DONE

Include the workflow ID in evidence so it's traceable.

### "Build [X] list"

**Query:**
```bash
# Search by name
curl -H "Authorization: Bearer $CLIENT_HUBSPOT_TOKEN" \
  "https://api.hubapi.com/crm/v3/lists/search" \
  -H "Content-Type: application/json" \
  -d '{"count":10,"query":"X"}'

# Get size + filter details
curl -H "Authorization: Bearer $CLIENT_HUBSPOT_TOKEN" \
  "https://api.hubapi.com/crm/v3/lists/{listId}?includeFilters=true"
```

**Grading:**
- No matching list → 🔴 OPEN
- List exists, size 0 → 🟡 PARTIAL (filter logic may be broken OR data not yet loaded — inspect filter structure to decide which)
- List exists, size > 0 → ✅ DONE

### "Implement [X] integration"

**Query:** Don't just check that the receiving fields exist — check that data is flowing.

For QuickBooks integration:
```bash
# Are deal records actually getting QBO IDs?
curl -H "Authorization: Bearer $CLIENT_HUBSPOT_TOKEN" \
  "https://api.hubapi.com/crm/v3/objects/deals/search" \
  -H "Content-Type: application/json" \
  -d '{"filterGroups":[{"filters":[{"propertyName":"qbo_invoice_id","operator":"HAS_PROPERTY"}]}],"limit":1}'
```

**Grading:** Check `total` in response:
- `total: 0` on a live integration → 🟡 PARTIAL or 🔴 OPEN (fields ready, data not flowing)
- `total: N` where N > 0 → ✅ DONE

### "Scrape / audit / clean [X]"

These are diagnostic tickets, not buildable. Look for:
- A document, spreadsheet, or note produced (check linked files on the company record)
- A summary note in meeting records or the ticket's `content` field
- A data cleanup pass (e.g., bulk deduplication) visible in modification timestamps

**Grading:**
- Deliverable artifact found → ✅ DONE
- `fulfillment_hours_` logged but no artifact → 🟡 PARTIAL (work happened, no deliverable captured)
- Nothing → 🔴 OPEN

### "Align / coordinate / discuss [X]"

Conversational tickets. These are "done" when the conversation happened and was documented. Look in meeting notes for the topic.

**Grading:**
- Meeting note covers the topic → ✅ DONE (attach the quote as evidence)
- No record of discussion → 🟡 PARTIAL
- Client-blocked → ⛔ BLOCKED

## Portal-wide context queries

Run these once at the start of Phase 3 to avoid repeating:

```bash
# Total record counts (search endpoint returns "total"; plain list GETs do not)
curl -H "Authorization: Bearer $CLIENT_HUBSPOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"limit":1}' \
  "https://api.hubapi.com/crm/v3/objects/companies/search" | jq '.total' 

# All custom properties created during engagement window
curl -H "Authorization: Bearer $CLIENT_HUBSPOT_TOKEN" \
  "https://api.hubapi.com/crm/v3/properties/companies?archived=false" | \
  jq '.results[] | select(.createdAt > "<ENGAGEMENT_START_DATE>") | {name, label, createdAt}'

# All custom lists
curl -H "Authorization: Bearer $CLIENT_HUBSPOT_TOKEN" \
  "https://api.hubapi.com/crm/v3/lists/search" \
  -H "Content-Type: application/json" \
  -d '{"count":200}' | jq '.lists[] | {listId, name, objectTypeId, size}'
```

Cache these results in the working directory so multiple ticket verifications don't re-query.

## Rate limiting

HubSpot PAT-based rate limit is typically 100 req/10s. On a reconciliation with 20+ tickets, add `sleep 1` between verification calls or batch-search for multiple properties at once. A failed 429 response will not be retried automatically — catch and wait.

## Common gotchas

- **Property internal name vs label** — users describe tickets by label ("Prospect Contract End Date") but the API needs the internal name (`prospect_contract_end_date`). Convert: lowercase, spaces → underscores, strip punctuation.
- **Workflow endpoints** — HubSpot has v3 and v4 automation APIs with different payloads. Some tiers only expose v4. If v3 returns empty, try `/automation/v4/flows`.
- **List filter complexity** — inspecting a list's filter via API returns deeply nested JSON. For the reconciliation report, don't paste the raw JSON — summarize in plain English: "Filter: contact's associated company is in list 224".
- **Deleted artifacts** — a property/workflow/list that was deleted may still appear in ticket history as "created". Check archival timestamps before concluding work wasn't done.
