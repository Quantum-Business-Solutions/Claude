# ZoomInfo Demo Portal — Webinar Runbook

**Portal:** 5234298 (NA2, US/Eastern, Standard)
**Prepared:** 2026-07-29

---

## 1. Portal snapshot

| | |
|---|---|
| Contacts | 1,419 |
| Companies | 901 |
| Deals | 1 (`Derbs Test`) |
| Custom objects | 0 |
| Lists | 12 (10 dynamic — **at ceiling**) |
| Owners | 19 (mostly @zoominfo.com) |

### Data that demos well as-is

Core enrichment is strong and needs no prep:

| Object | Property | Fill |
|---|---|---|
| Contact | First / last name | 100% |
| Contact | Job title | 100% |
| Contact | Phone | 100% |
| Contact | Company | 100% |
| Contact | Country | 100% |
| Company | Domain | 100% |
| Company | Phone | 100% |
| Company | Employee count | 99% |
| Company | Annual revenue | 99% |
| Company | Industry | 96% |
| Company | Description | 97% |

### Thin spots — avoid or pre-fill

Portal-wide counts (not samples):

| Object.Property | Records with a value |
|---|---|
| `contacts.intent__person_level` | 0 of 1,419 |
| `contacts.zi_contact_id` | 4 |
| `contacts.person_has_moved` | 2 |
| `contacts.enrich_status` | 1,076 |
| `companies.zi_ims` | 33 |
| `companies.zi_funnel_stage` | 33 |
| `companies.intent_crm_automation` | 7 |
| `companies.crm_automation___intent_audience_strength` | 2 |
| `companies.zi_audience_name` | 0 |

Only **7 ZoomInfo properties exist** (4 contact + 3 company). The QBS standard set is 81.

---

## 2. Intent - Person Level

**Property created 2026-07-29 13:40 ET.**

| Field | Value |
|---|---|
| Internal name | `intent__person_level` |
| Label | Intent - Person Level |
| Type | `string` / fieldType `text` (single-line text) |
| Group | Contact Information |
| Options | none |

### Risk: free-text, not a dropdown

The list filter must match the pushed string **exactly**. If the push sends
`high`, `HIGH`, or `High Intent`, the "= High" list can read empty on stage.

**Mitigation — pick one before the webinar:**
1. Confirm the exact literal values with whoever is pushing the data, or
2. Convert the property to a dropdown (enumeration) with fixed options
   High / Medium / Low. This guarantees consistency and gives a cleaner
   picklist on the record.

---

## 3. Lists created

| List | id | Filter | Type |
|---|---|---|---|
| `Intent - Person Level (Known)` | 39 | `intent__person_level` IS_KNOWN | Dynamic |
| `Intent - Person Level = High` | 40 | `intent__person_level` IS_EQUAL_TO `High` | Dynamic |

Both dynamic — they self-populate once values are pushed. Both verified via
`GET /crm/v3/lists/{id}?includeFilters=true`.

### Slots freed to make room

Portal was at the hard ceiling: `Portal 5234298 has exceeded its dynamic list
limit of 10`. Deleted two **zero-member** lists (recoverable in HubSpot for 90
days):

| Deleted | id | Members lost |
|---|---|---|
| `date test` | 34 | 0 |
| `Ryan and Will` | 27 | 0 |

**Now at 10/10 dynamic lists — no headroom remaining.** If another list is
needed, a candidate is `Unnamed list 7/24/2025 2:46:06 PM` (id 31), whose 1,377
count is identical to `Records From ZoomInfo` (id 3) and looks like an
accidental duplicate. Not touched.

---

## 4. Workflow

### Key point: the workflow does not need a list

A workflow enrollment trigger can filter on the property directly, which avoids
spending a dynamic list slot:

- **Trigger:** `Intent - Person Level` *is known* — or *is equal to* `High`
- **Action 1:** Enroll in sequence, **or** Send marketing email

Keep lists 39/40 for what they are good at on stage: a visible, countable
audience. Let the workflow trigger off the property.

### Blocked on scope

`GET /automation/v4/flows` returns:

```
403 MISSING_SCOPES — requiredGranularScopes: ["automation"]
```

**Fix:** Settings → Integrations → Private Apps → app → Scopes →
**Automation → Workflows** (Read + Write) → **Commit changes**.
The existing PAT keeps working; no regeneration needed.

Do **not** chase the legacy `/automation/v3/workflows` endpoint — it requires
`workflows-access-public-api`, which is not grantable to private apps. v4 is the
only path.

> If the `automation` toggle is not present in the scope list, the portal lacks
> the tier for workflows (Marketing Hub Pro+ / Ops Hub). The 10-dynamic-list cap
> is a low-tier signal. **Confirm in Settings → Account & Billing →
> Subscriptions before building the demo around this.**

### Step-1 action requirements

| Action | Requires | Gotcha |
|---|---|---|
| Enroll in sequence | Sales Hub **Pro/Enterprise** | Needs a designated sender with a paid seat **and** connected inbox. Commonly unset in demo portals. |
| Send marketing email | Marketing Hub **Pro+** | Email must be created as type **Automated** or it will not appear as a workflow action. |

### UI click path (fallback if scope stays blocked)

1. Automation → Workflows → **Create workflow** → *From scratch* →
   **Contact-based** → Blank workflow
2. **Set enrollment triggers** → *Contact properties* →
   `Intent - Person Level` → **is known** (or **is equal to** `High`)
3. Leave re-enrollment **off** for a clean demo
4. **+** → choose either:
   - *Enroll in a sequence* → pick sequence → set sender
   - *Send email* → pick the **Automated** marketing email
5. **Review and publish**

---

## 5. PAT scope status

Verified against portal 5234298.

| Area | Status |
|---|---|
| Contacts / Companies / Deals | OK |
| Properties (contacts, companies) | OK |
| Pipelines, Owners, Schemas | OK |
| Lists (read + write + delete) | OK |
| **Workflows / Automation** | **403 — needs `automation`** |
| Forms | 403 MISSING_SCOPES |
| Landing pages / Site pages / Blog | 403 MISSING_SCOPES |
| Campaigns | 403 MISSING_SCOPES |
| Marketing email | 403 MISSING_SCOPES |
| Tickets | 403 — scope not available for public use |

## 6. Live ZoomInfo MCP

Confirmed working — usable live on the call with no portal changes:
search contacts, enrich companies, intent signals, scoops/news.
Test query returned VP-level contacts at HubSpot with current accuracy scores
and July 2026 update dates.

---

## 7. Open items before the webinar

- [ ] Add `automation` scope to the private app, or confirm the tier blocks it
- [ ] Decide step 1: **sequence** vs **marketing email**
- [ ] Confirm the exact literal values being pushed to `intent__person_level`
      (or convert the property to a dropdown)
- [ ] Confirm hub subscriptions support workflows and sequences
- [ ] Rotate the PAT after the webinar — it was shared in chat
