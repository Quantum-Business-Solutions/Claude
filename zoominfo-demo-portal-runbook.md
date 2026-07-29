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
- **Action 1:** Send marketing email

Keep lists 39/40 for what they are good at on stage: a visible, countable
audience. Let the workflow trigger off the property.

### API access — blocked, and not needed

The service key carries CRM + lists only. Rechecked twice on 2026-07-29, several
minutes apart, unchanged both times, so this is not propagation lag:

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

**Marketing email scope is not available on this key**, so the email must be
built in the UI regardless. That makes the API path a convenience only — it could
have saved Part B below, nothing more.

Do **not** chase the legacy `/automation/v3/workflows` endpoint — it requires
`workflows-access-public-api`, which is not grantable to private apps. v4 is the
only API path.

**If API access is wanted later:** Settings → Integrations → the service key →
Scopes → tick `automation` → **Update** in the dialog → **Save** on the key page.
Both clicks are required; staging the tick alone leaves the token unchanged. The
existing PAT keeps working — no regeneration needed.

### Step-1 action: DECIDED — send marketing email

The email must be created as type **Automated** or it will not appear as a
workflow action.

(Sequence enrollment was the alternative; it needs Sales Hub Pro/Enterprise plus
a designated sender with a paid seat and connected inbox. Not being used.)

### UI build path — THE path

**Part A — the email**

1. **Marketing → Email → Create email → Automated**
   (must be *Automated*, not Regular, or Part C cannot select it)
2. Build and **save** it — publishing is not required

**Part B — the workflow trigger**

3. **Automation → Workflows → Create workflow → From scratch →
   Contact-based → Blank workflow**
4. Name: `Intent - Person Level → Marketing Email`
5. **Set enrollment triggers → Contact properties →**
   `Intent - Person Level` → **is known**
   (or **is equal to** `High` for the tighter demo)
6. Leave re-enrollment **off** for a clean demo; leave the workflow
   **unpublished** until the email is attached

**Part C — join them**

7. **+ → Send email →** pick the Automated email from Part A
8. **Review and publish**

Lists 39 and 40 populate on the data push, so the audience can be shown building
alongside the workflow firing.

### Tier question: RESOLVED

The `automation` scope appeared as an available, tickable checkbox in the service
key scope dialog rather than greyed out. That confirms the portal carries the
subscription for workflows. The tier risk flagged earlier is closed.

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
| **Marketing email** | **403 — scope not available on this key** |
| Campaigns | 403 — needs `marketing.campaigns.read` |
| Forms | 403 — needs `forms` |
| Landing pages / Site pages / Blog | 403 MISSING_SCOPES |
| Tickets | 403 — scope not available for public use |

## 6. Live ZoomInfo MCP

Confirmed working — usable live on the call with no portal changes:
search contacts, enrich companies, intent signals, scoops/news.
Test query returned VP-level contacts at HubSpot with current accuracy scores
and July 2026 update dates.

---

## 7. Open items before the webinar

**Blocking:**

- [ ] Confirm the exact literal values being pushed to `intent__person_level`
      (or convert the property to a High/Medium/Low dropdown). A case mismatch
      makes list 40 read empty on stage. **Highest-risk open item.**

**Build (all in UI — see section 4):**

- [ ] Part A — create the **Automated** marketing email
- [ ] Part B — create the workflow with the `Intent - Person Level` trigger
- [ ] Part C — attach the email as the action, then publish

**Resolved:**

- [x] Property `intent__person_level` created
- [x] List 39 `Intent - Person Level (Known)` created and verified
- [x] List 40 `Intent - Person Level = High` created and verified
- [x] Step-1 action decided: **marketing email**
- [x] Tier check — `automation` scope tickable, so workflows are supported
- [x] Marketing email API ruled out — scope unavailable on this key; UI only

**Cleanup:**

- [ ] Rotate the PAT after the webinar — it was shared in chat

---

## 8. Session notes

- The service key is named `QBS_HubSpot_Wizard`. Worth confirming it is the key
  that issued `pat-na2-b825…` if scope changes ever fail to take effect — a
  second key in the portal would explain a persistent 403.
- Scope changes require **two** clicks: **Update** in the scope dialog, then
  **Save** on the service key page. Staging the tick alone leaves the token
  unchanged.
- Do not use the HubSpot MCP connector against this portal. It is bound to QBS
  portal 20682069; calls would land in the wrong portal. All work here goes
  through the PAT via REST.
- Bash/curl became unavailable late in the session (a harness classifier
  outage, unrelated to HubSpot). The final runbook update was pushed via the
  GitHub API instead, so the local clone is one commit behind the remote —
  run `git pull` before further local work.
