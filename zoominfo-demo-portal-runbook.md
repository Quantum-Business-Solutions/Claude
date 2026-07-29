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

### API is blocked on scopes (rechecked 2026-07-29, twice, minutes apart)

The PAT carries CRM + lists only. Every marketing/automation scope is absent:

| Endpoint | HTTP | Scope HubSpot reports as required |
|---|---|---|
| `/automation/v4/flows` | 403 | `automation` |
| `/marketing/v3/emails` | 403 | `marketing.email.read`, `marketing.email.write`, `content` |
| `/marketing/v3/campaigns` | 403 | `marketing.campaigns.read` |
| `/marketing/v3/forms` | 403 | `forms` |
| `/crm/v3/objects/contacts` *(control)* | **200** | — |
| `/crm/v3/lists/39` *(control)* | **200** | — |

Controls passing proves the token is valid and hitting portal 5234298 — it simply
holds no marketing or automation scope. Token introspection is unavailable for
private-app tokens (`/oauth/v2/private-apps/get/access-token-info` → 404,
`/oauth/v1/access-tokens/{token}` → 400 bad format), so scopes cannot be
enumerated via API; the 403 payloads are the authoritative signal.

**Three causes, most likely first:**

1. **Ticked but not committed.** HubSpot requires **Commit changes** (top-right)
   after checking scope boxes. Navigating away discards them.
2. **Wrong private app edited.** The portal may host several. The correct app is
   whichever issued the token starting `pat-na2-b825…` — verify by matching the
   token prefix, not the app name.
3. **Tier gate.** If the **Workflows** checkbox under Automation is greyed out or
   absent, the portal lacks Marketing Hub Pro+ / Ops Hub and toggling cannot fix
   it.

**Five-second tier test:** check the HubSpot left nav. If **Automation →
Workflows** and **Marketing → Email** are missing or show an upgrade prompt, this
demo cannot run in this portal and needs replanning.

Do **not** chase the legacy `/automation/v3/workflows` endpoint — it requires
`workflows-access-public-api`, which is not grantable to private apps. v4 is the
only API path.

**If API access is wanted anyway,** add at Settings → Integrations → Private Apps
→ the app → Scopes: `automation`, `marketing.email.read`,
`marketing.email.write`, `content` → **Commit changes**. The existing PAT keeps
working; no regeneration needed. The UI build path below does not need any of
this.

### Step-1 action: DECIDED — send marketing email

Requires Marketing Hub **Pro+**. The email must be created as type **Automated**
or it will not appear as a workflow action.

(Sequence enrollment was the alternative; it needs Sales Hub Pro/Enterprise plus
a designated sender with a paid seat and connected inbox. Not being used.)

### UI build path — RECOMMENDED, needs no API scope

This is the primary path. It works today and is the safer choice for a live
webinar.

1. **Marketing → Email → Create email → Automated**
   (must be *Automated*, not Regular, or step 6 cannot select it)
2. Build and **save** it — publishing is not required
3. **Automation → Workflows → Create workflow → From scratch →
   Contact-based → Blank**
4. **Set enrollment triggers → Contact properties →**
   `Intent - Person Level` → **is known** (or **is equal to** `High`)
5. Leave re-enrollment **off** for a clean demo
6. **+ → Send email →** pick the Automated email from step 1
7. **Review and publish**

Lists 39 and 40 populate on the data push, so the audience can be shown building
alongside the workflow firing.

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
| **Marketing email** | **403 — needs `marketing.email.read` / `.write` / `content`** |
| Campaigns | 403 — needs `marketing.campaigns.read` |
| Forms | 403 — needs `forms` |
| Landing pages / Site pages / Blog | 403 MISSING_SCOPES |
| Tickets | 403 — scope not available for public use |

Rechecked twice on 2026-07-29, several minutes apart — unchanged both times, so
this is not propagation lag.

## 6. Live ZoomInfo MCP

Confirmed working — usable live on the call with no portal changes:
search contacts, enrich companies, intent signals, scoops/news.
Test query returned VP-level contacts at HubSpot with current accuracy scores
and July 2026 update dates.

---

## 7. Open items before the webinar

**Blocking:**

- [ ] **Tier check** — confirm HubSpot left nav shows *Automation → Workflows*
      and *Marketing → Email*. If either is missing or prompts an upgrade, this
      demo cannot run in this portal.
- [ ] Confirm the exact literal values being pushed to `intent__person_level`
      (or convert the property to a High/Medium/Low dropdown). A case mismatch
      makes list 40 read empty on stage.

**Build:**

- [ ] Create the **Automated** marketing email
- [ ] Build the workflow via the UI path in section 4

**Resolved:**

- [x] Property `intent__person_level` created
- [x] List 39 `Intent - Person Level (Known)` created and verified
- [x] List 40 `Intent - Person Level = High` created and verified
- [x] Step-1 action decided: **marketing email**

**Optional / cleanup:**

- [ ] Add marketing + automation scopes if API access is wanted (not required
      for the UI build path)
- [ ] Rotate the PAT after the webinar — it was shared in chat
