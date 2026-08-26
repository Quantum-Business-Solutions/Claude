---
name: qbs-ai-lead-finder
description: Mine a copier/office-equipment dealer's HubSpot engagement history for competitive lease intelligence — when a prospect's current lease ends, who their incumbent provider is, and the evidence behind both — then write structured findings onto engagement and company records. Use whenever a copier dealer, MPS provider, or office-technology client wants their CRM history turned into a prioritized outreach list. Trigger on "AI lead finder", "lease end dates", "competitive lease intel", "who are they with", "mine our call notes for leases", "lease expiration mining", "find prospects whose lease is ending", or any request to extract contract/lease timing from unstructured CRM activity. Requires a client HubSpot PAT (see qbs-hubspot-private-app).
---

# QBS AI Lead Finder

Turns a dealer's unstructured CRM history — call notes, AI call summaries, tasks, notes, inbound emails — into a dated, evidence-backed list of prospects whose competitive lease is ending.

The premise: reps write lease intel into free text and never into a structured field. TCO-tab adoption at these dealers runs 5–15%. The intel exists; it is trapped. This process untraps it.

## Non-negotiables

**Never trust a keyword match as a finding.** Keyword filters are a recall net with roughly a 3% true yield. Everything must survive extraction and classification before it is written.

**Never write a computed date into a structured date property without the client vetting it first.** Text evidence fields are safe — nothing downstream automates off them. Date fields drive views, workflows, and rep task queues. Write text first, dates only after sign-off.

**Never write to a client portal without explicit approval for that specific write.** Scope creeps across a session. "Run the process" is not approval to populate every field you can reach.

**Always carry provenance.** Every value written must name the source engagement, its record ID, the date logged, and how the date was derived. A rep who cannot trace a claim will not act on it.

## Prerequisites

- Client HubSpot PAT — load `qbs-hubspot-private-app` for token handling
- Verify the portal first: `GET /account-info/v3/details` returns `portalId`. Confirm it matches the intended client before touching anything.
- The reported scope list under-reports. Probe empirically rather than trusting it.

### Probing effective permissions

A bogus property name distinguishes permission from validation with zero mutation:

```
PATCH /crm/v3/objects/calls/<id>  {"properties":{"zzz_probe":"x"}}
  400 → write allowed (property just doesn't exist)
  403 → no write scope
```

Commonly blocked on dealer PATs: `automation` (workflows), `crm.lists.*` (lists/views), `crm.objects.deals.read`, `crm.objects.owners.read`. Engagement objects usually work even when unlisted. If the engagement is scoped to build a segmented view or an auto-task workflow, confirm those scopes **before** promising them.

## Step 1 — Inventory and feasibility

Count every engagement object and how many carry text:

```
POST /crm/v3/objects/{calls,notes,tasks,emails,meetings}/search
  {"limit":1,"filterGroups":[{"filters":[{"propertyName":"<body_prop>","operator":"HAS_PROPERTY"}]}]}
```

Body properties: `hs_call_body`, `hs_call_summary`, `hs_note_body`, `hs_task_body`, `hs_task_subject`, `hs_email_text`, `hs_meeting_body`.

Two things to establish before quoting scope:

**Dialer noise.** Auto-dialers (Orum and similar) stamp stub bodies like `[Orum] MF 8/26 @ 1:54 PM (power)` onto every attempt. At UBEO that was 789,471 of 1,019,360 call bodies — 77% pure noise. Filter stubs by length (`startswith("[Orum]") and len(body) < 60`), **not** by the dialer prefix: the same dialer's `----- AI Generated Notes -----` blocks are the single richest source in the portal.

**Email bodies are not searchable.** `hs_email_text` and `hs_email_html` reject search filters; only `hs_email_subject` accepts them. Filter emails on `hs_email_direction` instead and read bodies back from the search result properties.

## Step 2 — Build the candidate pool

Union these terms across every text property, deduplicating by record ID. Search per-term and merge — HubSpot caps `filterGroups` at 5, so a single OR query cannot hold the set.

**Timing:** `years left` `yrs left` `left on` `remaining` `expires` `expiration` `expiring` `expire` `comes due` `coming due` `comes up in` `comes up` `up for renewal` `renews` `end of term` `term end` `buyout` `few years`

**Duration in months** — reps write months as often as years: `months left` `months remaining` `months to go` `months on` `18 months` `24 months` `36 months`

**Term lengths** — a length plus a start date yields an end date: `60 month` `60 mo` `36 month` `48 month` `39 month` `63 month` `66 month`

**Just-signed** — see Step 3, this is the highest-value class: `just signed` `just renewed` `recently signed` `signed a new` `renewed their` `renewed our` `went with`

**Auto-renewal traps** — missing the notice window costs the whole cycle: `auto renew` `automatic renew` `evergreen` `90 day` `notice`

**Incumbent OEMs** — dealers routinely omit these from their own filters: `Ricoh` `Xerox` `Canon` `Konica` `Minolta` `Sharp` `Toshiba` `Kyocera` `Lanier` `Savin` `Muratec` `Lexmark`

**Ownership (exclude, don't chase):** `own their` `we own` `purchased` `outright` — these accounts bought rather than leased. No lease date will ever exist. Tag and drop them.

**Contract/lease nouns:** `lease` `leases` `leasing` `leased` `contract` `contracts` `contracting`

## Step 3 — Extract, in priority order

For each record, take the **first** source that resolves:

**1. Explicit stated date.** `lease expires 1/2026`, `contract does not end until 2029`. Highest confidence. Use verbatim.

**2. Remaining term + engagement date.** `2 years left`, `3 years into a 5 year`, `eighteen months remaining`. Add the remainder to the engagement timestamp.

**3. Just-signed + term + engagement date.** `just signed a 5 year lease with Xerox` → engagement date + 5 years.

> Source 3 is the one most people discard as a rejection. It is the best material in the corpus. Someone who has just signed volunteers **who they signed with** — so you get signing date, term length, and incumbent from one sentence. At UBEO, 886 just-signed records yielded 223 computable future end dates, against a 142-of-266 unknown-provider rate in the rest of the set. A rejection in 2021 is a lead in 2026.

Handle backdating: `signed last year`, `back in 2023`, `2 years ago` shift the start before adding the term.

## Step 4 — Classify and exclude

Flag every record. These exclusions matter more than the extraction:

| Flag | Pattern | Why |
|---|---|---|
| `UBEO_INCUMBENT` | `lease with us`, `through us`, `from us`, `current customer`, `we sold`, `off lease` | The dealer already holds this lease. Retention, not competitive. Pitching them looks incompetent. |
| `DNC` | `XDNC`, `DO NOT CALL`, `stop calling` | Will carry clean lease signal and sail onto a call list otherwise. |
| `OWNS_EQUIPMENT` | ownership terms, absent any lease mention | No lease will ever exist. |
| `AUTO_RENEW` | `auto renew`, `evergreen` | Not an exclusion — an escalation. Surface the notice window. |

Incumbent phrasing varies more than any regex covers. Read the residue by hand before a portal-wide run.

## Step 5 — Deduplicate

Two distinct problems:

**Legacy CRM boilerplate.** Migrated dealers stamp a `SalesStrategy` / `SalesChainID` blob onto every task for an account. At UBEO one such string appeared on 178 separate task records. Normalize by stripping `SalesChainID:`, `Federal ID Number:`, `SICCode:`, `Annual Revenue:`, `Toll Free:` before hashing, then dedupe on the first ~150 characters. Raw 4,718 matches collapsed to 626 unique statements.

**Stale dates.** Legacy blobs carry long-expired dates (`Toshiba Lease Expires 2023`). Bucket past-dated separately — they are a **win-back list**, not waste: that account went to market without you.

## Step 6 — Confidence tiers

Precision is inherited from phrasing. `2 years left` gives a month at best, anchored to the engagement date — call it ±3 months. Never present a computed date as exact.

| Tier | Rule |
|---|---|
| High | Explicit date, or a statement within ~12 months |
| Medium | Computed from term, engagement 1–2 years old |
| Low | Engagement 2+ years old |

Check for **conflicting durations within one record** — `two years remaining` and `end of their contract in about eighteen months` in the same note. Rare (1 in 266 at UBEO) but silently picking the first match is wrong. Flag both and let a human resolve.

## Step 7 — Write engagement-level evidence

Create `ai__lease_information` (string/textarea) on each engagement object carrying signal. Note the naming inconsistency to check for: at UBEO the call object used `ai__lease_information` (double underscore) while the company object used `ai_lease_information` (single). Always read the existing schema rather than assuming.

Format:

```
MM/YYYY - <Provider or "Provider unknown"> - <evidence excerpt>
  [source: <type> <id>, logged MM/DD/YYYY, <derivation>: "<basis phrase>"]
  ** FLAGS: <flags>
```

**Center the evidence excerpt on the basis phrase** — roughly 150 characters either side. Do not slice the first N characters of the body: the phrase justifying the date frequently sits past the cut, leaving a field that asserts a date with nothing visible to support it. Verify after building that every value contains its own basis phrase.

Write via `POST /crm/v3/objects/{obj}/batch/update`, 100 per batch.

## Step 8 — Roll up to companies

Resolve associations (`POST /crm/v4/associations/{obj}/companies/batch/read`), then batch-read companies for `lifecyclestage` and the existing value.

**Gate on lifecycle stage.** Skip `customer` — and check for dealer-specific stages (UBEO had a custom `Team UBEO` stage). Ask which stages are in scope; do not assume.

**Rank when a company has several signals.** Best wins:
1. Stated date > remaining term > just-signed
2. Provider known > unknown
3. More recent engagement

**Never downgrade an existing value.** If the field holds a value with no `[source:` tag, a human wrote it — skip. Only overwrite machine-written values, and only with a higher-ranked signal.

Note the supporting count (`+3 other engagements with lease signal`) so a rep sees corroboration.

**Cross-object merge fills gaps.** One call names the OEM, a task carries the date, an email names the decision maker. Merging on company recovers provider for records that would otherwise read "Provider unknown" — the single largest quality gap in the output.

**Sanity-check associations.** Engagements are sometimes associated to the wrong company; the evidence string will visibly reference a different organization. Spot-check before a large write.

## Step 9 — Structured dates, only after vetting

Once the client signs off, populate the date properties (`potential_prospect__lease_end_date` or equivalent). Keep the confidence tier alongside so a rep sees `~2yrs left, stated 9/2024` rather than false precision.

## Order of operations

Run sources in this order — it is descending signal density, measured:

1. **Tasks** — densest by a wide margin. At UBEO `expires` appeared 3,234 times in task bodies versus 112 in call bodies, ~8x the lease density. Task records also pack more per record: date, OEM, lessor, model, and payment in one line.
2. **Calls** — body *and* `hs_call_summary`. Summary is not a duplicate; it carries content where the body is an empty dialer stub. 369,946 populated at UBEO.
3. **Inbound emails** — `hs_email_direction = INCOMING_EMAIL` only. Outbound scores *higher* on keywords and is worthless: the hits are the dealer's own templates repeating verbatim. Inbound is the prospect speaking.
4. **Notes**
5. **Meetings**

## The ceiling is regex, not sources

Roughly 70% of keyword-matched records state no parseable term. Pattern matching only fires on anticipated phrasings and misses everything said sideways — *"they're locked in for a while"*, *"not until after the new year"*, *"when the current one is up in the spring"*, *"budget cycle is July"*.

Reading those records semantically is where the remaining yield is. It also catches what patterns get **backwards**: at UBEO, reading recovered 16 providers regex could not see (`Ameritel`, `Les Olson`, `CopyPro`, `WIZX`), corrected *"they are **not** with Centric"* which regex had scored as provider = Centric, produced junk like provider = "very low volume" from *"using very low volume"*, and surfaced two do-not-call records carrying perfectly good lease dates.

Budget for a read pass over the no-term residue. It is slower than regex and it is the difference between matching patterns and understanding notes.

## Reference: UBEO funnel

Portal 516382, ~3.9M engagements. Real numbers from the first pass, useful for scoping:

| Stage | Count |
|---|---|
| Engagements total | ~3.92M |
| Calls with a body | 1,019,360 |
| ...minus dialer stubs | ~230,000 |
| Group 1 keyword union (calls) | 8,869 |
| Unique after dedup | 8,629 |
| Keyword matched, no term stated | 6,001 |
| Negative/suppression | 1,646 |
| Dealer is incumbent | 445 |
| Already expired | 267 |
| **Actionable, prospect-stated, future** | **270** |

Expanded pass (calls body + summary + notes, plus just-signed and the wider term set): **579 clean**, of which 163 named an incumbent and 166 expire within 12 months. Company rollup after the customer gate: **452 companies**.

Expect roughly **3% true yield** from a keyword pool. Set that expectation before the engagement starts, not after.

## Pitfalls

- Trusting the reported scope list — probe instead
- Reading dialer stubs as junk and filtering out the AI-notes blocks with them
- Slicing evidence from the start of the body instead of around the basis phrase
- Treating just-signed as a rejection
- Writing dates before the client has vetted the calculation
- Assuming property naming is consistent across objects in the same portal
- Counting duplicated legacy CRM blobs as distinct findings
- Letting a do-not-call record onto an outreach list because its lease signal looked clean
