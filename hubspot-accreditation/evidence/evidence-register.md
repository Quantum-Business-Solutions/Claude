# Evidence Register

Source-of-truth index for the accreditation casework, plus alternative customer
candidates if a primary falls through.

---

## Primary sources

| Source | Identifier |
|---|---|
| Accreditation Hub (criteria, items, eligibility) | Supabase `zjtgesaiemlveuoymubo` |
| QBS HubSpot portal | `20682069` |
| CalcFocus portal (Client Command) | `d4d36cc1-7b87-49ff-a4ef-4f61e2c0d960` |
| CalcFocus master plan | `ed0038fe-70b3-4507-8b1b-a7f3d3f1d6b8` |
| CalcFocus HubSpot company record | `52746451314` |
| PacTec portal (Client Command) | `3bb7fb52-ec7e-468f-9fe9-99180a91175b` |
| PacTec integration plan (50 hrs) | `c6c742c9-092c-4050-aec9-dd6247bdb846` |
| PacTec HubSpot company record | `53419639405` |

---

## Portal eligibility rows

Only **2 of 45 active portals** have an eligibility row. Per the Accreditation Hub
handoff: **an unpopulated row reads `false` but means *unknown*, not *disqualified*.**
The 43 portals with no row have never been screened.

| Portal | Marketing Hub | Sales Hub | Employees | Salesforce | Notes |
|---|---|---|---|---|---|
| CalcFocus | **Professional** ✅ | **Professional** ✅ | 58 | — | Clears the subscription gate. Items 1 + 3 candidate. |
| PacTec | **Professional** ✅ | **null** ⚠️ | 200 | ✅ delivered | Item 2 candidate. Sales Hub tier is the open risk. |

**Recommended follow-on:** the handoff (§7) proposes a scheduled job to refresh
`portal_accreditation_eligibility` from HubSpot.
`client_portals.hubspot_cache->'company'->'properties'->>'hubspot_hubs_in_use_'` already
carries hub data for ~7 portals. Until that exists, the other 43 portals are invisible to
`list_qualifying_portals` and the qualification hunt has to be redone by hand.

---

## Delivery evidence held

### CalcFocus
- Master plan: 8 phases, 152 tasks, **75/75 onboarding tasks complete**
- Three closed client confirmation gates (Marketing Hub, Sales Hub, overall onboarding)
- 19 calls · ~230 emails · 20 tickets · 36 meetings · **30 transcripts**
- Recorded training sessions 2026-07-16 and 2026-07-17 (10 attendees)
- Zoom meeting `82312160838` — HubSpot Training Session, transcript available

### PacTec
- Integration plan: 8 phases, **70/71 tasks complete**
- Master plan: 107/138
- 28 calls · ~115 emails · 22 tickets · 37 meetings · **21 transcripts**
- Salesforce field inventory exported by client admin at discovery

---

## Alternative candidates if a primary falls through

Surfaced from Zoom meeting history — **none have been screened against the gates.**
Screen before relying on any of them.

### If PacTec fails the Sales Hub gate (Onboarding item 2)
Item 2 needs a customer with Marketing **and** Sales Hub Pro+ who received both a
Salesforce integration and a marketplace/iPaaS integration. Candidates seen delivering
ZoomInfo–HubSpot work in 2026:

| Candidate | Evidence | Screened? |
|---|---|---|
| ScyllaDB | *ZoomInfo-HubSpot-Salesforce* Sessions 1 & 2, Jun 2026 — **carries both required use cases** | ❌ |
| IT Solutions | *ZoomInfo-HubSpot*, Jul 2026 | ❌ |
| Astor Group | *ZoomInfo-HubSpot Kickoff*, Jun 2026 | ❌ |
| Milrose | *ZoomInfo-HubSpot*, Aug 2026 | ❌ |
| BTX Logistics | *ZoomInfo-HubSpot*, Aug 2026 | ❌ |
| Rancho Bioscience | *ZoomInfo-HubSpot Optimization*, Jun 2026 | ❌ |
| Tucker Freight | *ZoomInfo-HubSpot Consult*, Aug 2026 | ❌ |

**ScyllaDB is the strongest fallback** — it is the only one whose meeting title names
ZoomInfo, HubSpot **and** Salesforce together, matching item 2's two-use-case structure.

### Data Migration (needs two projects, leading CRM/MAP/helpdesk → HubSpot)
Stronger candidates than either primary:

| Candidate | Evidence | Source system | Screened? |
|---|---|---|---|
| A.N. Deringer | *Infor-to-HubSpot Migration Sync*, recurring Jun 2026 | Infor — **[VERIFY]** it counts as a leading CRM | ❌ |
| Ricova | *Data Migration*, Jul 2026 | Unknown | ❌ |
| DMP | *HubSpot Data Sync*, Aug 2026 | Unknown. Tier known: Sales Starter / Service Pro / Marketing Starter | ❌ |

⚠️ *HubSpot to GoHighLevel Migration* (Jul 2026) is **out of** HubSpot and does not count.

### Onboarding items 1 & 3 alternatives
Other 2026 onboarding kickoffs, unscreened: SIE, Ackerman (Marketing Hub), IMS Tech
(Sales Hub), GPP. Note Ackerman and IMS Tech each appear to be **single-hub** engagements,
which would fail the both-hubs gate.

---

## Known data hygiene issues

Carried from the Accreditation Hub handoff — these inflate holder counts:
- **Patrick Dodge counts twice** (records on both QBS domains)
- **`openflow@thequantumleap.business`** is a shared inbox counted as a person
- **Every `expires_at` is NULL** — the renewal watch is blind. Certifications must be
  active *at the moment of application*, so this is a live submission risk, not just a
  reporting gap.
