# PacTec — Onboarding Accreditation, Item 2

**Accreditation:** Onboarding (Wave 1 — QBS priority)
**Submission item covered:** Item 2 (Integration Documentation — two use cases)
**Reuse rule:** May be a different customer from items 1 and 3, **but the same
Pro-or-above subscription rule applies**.
**Status:** Draft — content strong, **blocked on the Sales Hub subscription gate**

> **Why PacTec fits item 2 specifically.** Item 2 requires *two* use cases: a
> **Salesforce integration** (mandatory for US and UK partners) **plus** one additional
> use case using a **marketplace integration or iPaaS**. PacTec delivers both inside a
> single customer — Salesforce and ZoomInfo. HubSpot is explicit that *"turning an
> integration on does not count"*; the PacTec work is diagnosis, remediation, custom
> field architecture and cross-system workflow design, which is exactly the distinction
> the item is testing for.

---

## 0. Gate check

| Gate | Status | Source |
|---|---|---|
| Marketing Hub Professional or above | ✅ **Professional** | Confirmed by Shawn 2026-08-12 |
| Sales Hub Professional or above | ❌ **UNCONFIRMED — BLOCKING** | `sales_hub_tier` is null. PacTec runs **Salesforce as system of record**, so a Sales Hub subscription cannot be assumed. |
| Salesforce integration use case | ✅ | §2 |
| Marketplace integration / iPaaS use case | ✅ | ZoomInfo — §3 |
| Excluded app categories (Ads, Social, video hosting) | ✅ Not applicable | Neither use case is in an excluded category |
| Engagement within last 12 months | ✅ | May–Sep 2026 |

**If PacTec has no Sales Hub Professional licence, this engagement cannot serve item 2.**
Resolving this is the single highest-priority question in the Onboarding submission.
Fallback options are listed in `../README.md`.

---

## 1. Engagement metadata

| Field | Value |
|---|---|
| Customer | PacTec (`pactecinc.com`) |
| Industry | Business Supplies & Equipment — nuclear and industrial waste packaging |
| Company size | 200 employees |
| Location | Clinton, Louisiana |
| HubSpot Portal ID | **[NEEDED]** — PacTec's own portal ID |
| QBS portal record | `3bb7fb52-ec7e-468f-9fe9-99180a91175b` |
| HubSpot company record (QBS CRM) | `53419639405` |
| Scope of record | *HubSpot, ZoomInfo & Salesforce Integration* — 50 hours |
| Plan | `c6c742c9-092c-4050-aec9-dd6247bdb846` — **70 of 71 tasks complete (98.6%)** |
| QBS team | Shawn Peterson, Marko Ajder, Barb Peterson, Patrick Dodge |
| Client stakeholders | Katie Lanoix, Christina Reckard, Kristen White, Martin, Maggie |

---

## 2. Use case 1 — Salesforce integration *(mandatory US requirement)*

### 2.1 Business Use Case

PacTec runs **Salesforce as CRM of record** and **HubSpot** for marketing and demand
generation. Three concrete failures defined the problem:

1. **The sync was dead.** Salesforce → HubSpot activity data had stopped flowing on
   **2026-02-05** and nobody had established why. Five months of activity history was
   not reaching HubSpot.
2. **Deal sync had never been configured at all**, so marketing had no visibility of
   revenue outcomes and no way to attribute anything.
3. **Fourteen standard Salesforce integration properties were missing** from HubSpot,
   silently breaking mapping and reporting.

Consequence: marketing could not see what closed, sales could not see marketing context,
and neither system could be trusted for reporting.

### 2.2 Solution Description

The HubSpot–Salesforce connector, configured under a strict **Salesforce-remains-system-
of-record** constraint. The design question was not "how much can we sync" but "what must
*not* sync" — protecting Salesforce from HubSpot-side noise while giving marketing the
revenue visibility it lacked.

**Alternatives considered.** A middleware/iPaaS layer was assessed and rejected for this
use case: the native connector met the object and directional requirements, and adding
middleware would have introduced a failure point between two systems that already had a
reliability problem. Separately, an **upgrade to Salesforce integration v2** was
researched and the **duplicate-record exposure** assessed before any move — the upgrade
was not taken blind.

A deliberate custom design decision sits at the centre of this build: rather than
replicating 400+ ZoomInfo intent fields into Salesforce, QBS built a single condensed
**"HubSpot Summary"** field, mapped bidirectionally, carrying the intent narrative into
the Salesforce record where the seller actually works. This traded field sprawl for
usable context.

### 2.3 Data Flow Diagram

> 📌 **[TO PRODUCE]** Item 2 requires a **data flow diagram** with relevant data-model
> components plus a written explanation. See `../README.md` §Deliverables to produce.
> The diagram must cover: ZoomInfo → HubSpot (intent + prospect), HubSpot ↔ Salesforce
> (contacts, leads, deals, tasks, activities, HubSpot Summary), and HubSpot → Salesforce
> task creation on intent trigger.

Objects and directions to depict:

| Object | HubSpot → Salesforce | Salesforce → HubSpot |
|---|---|---|
| Contacts / Leads | ✅ | ✅ |
| Deals / Opportunities | — | ✅ (newly wired) |
| Tasks | ✅ (intent-triggered, dual routing) | — |
| Activities | — | ✅ (restored) |
| HubSpot Summary (custom) | ✅ | — |

### 2.4 How the Integration Was Used

- Connector installed; **object alignment** defined across contacts, leads, deals, tasks
  and activities
- **Field mapping, sync rules and inclusion criteria** configured
- **Selective sync** — explicit decisions on what not to sync
- **Pipeline stage alignment** between the two systems
- **Salesforce-sourced HubSpot properties** created
- **14 missing standard Salesforce integration properties** gap-filled
- **Root-caused the 2026-02-05 sync failure** and **restored Salesforce → HubSpot
  activity sync**
- **Wired Salesforce → Deal sync** for the first time
- **Imported historical Salesforce activity data into HubSpot**
- **HubSpot → Salesforce task creation** investigated, remediated and extended to dual
  routing for intent triggers
- Custom **HubSpot Summary** field mapped and validated with live test contacts
- Historical Salesforce activity data imported to backfill the gap

### 2.5 Results & Achieved Benefits

Qualitatively: a five-month sync outage closed, deal sync established where none existed,
14 property gaps filled, and a working bidirectional path across five object types.

> ❌ **[BLOCKING GAP]** Item 2 requirement 5 asks for **quantified** improvements —
> efficiency, data accuracy, conversion rates, cost savings. None are captured. Needed:
> records/activities backfilled, sync error rate before vs. after, deals now visible in
> HubSpot that previously were not, seller response time to intent-triggered tasks.

---

## 3. Use case 2 — ZoomInfo *(marketplace integration)*

### 3.1 Business Use Case

PacTec was paying for ZoomInfo buyer intent data that could not reach a seller. There was
no property model to receive the signals, no segmentation to act on them, no alerting,
and no path from an intent spike to a Salesforce opportunity. The spend could not be
justified because nothing tied a signal to revenue.

### 3.2 Solution Description

The ZoomInfo marketplace integration, plus a purpose-built HubSpot property and workflow
architecture to make intent operationally usable — and a clustering model so sellers
received themes rather than 47 separate signal types.

### 3.3 How the Integration Was Used

- **ZoomInfo Intent Topic Property Deployment: 47 topics → 423 HubSpot properties** —
  five intent properties for each of 48 contact-level intent signals, plus four
  company-level intent properties
- Automated ZoomInfo → HubSpot export configured
- ZoomInfo-sourced properties created and mapped, then the same model replicated into
  Salesforce alongside PacTec's admin
- ZoomInfo **saved searches aligned to the defined ICP**
- **Intent signal → HubSpot workflow → real-time sales alert** chain
- **ZoomInfo Prospect → HubSpot Lead → Salesforce Opportunity** workflow — the full
  cross-system path, end-to-end tested with dummy contacts before go-live
- **Five buyer personas** built with properties, segments and workflows: Head of
  Organization, Head of Operations, Head of Procurement, Industrial Waste Management,
  Nuclear Waste Management
- **30 intent cluster lists** — 15 marketing email + 15 master; Facilities Management
  cluster activated as pilot
- ZoomInfo subscription audited (seats vs. bulk credits)
- Escalated to ZoomInfo support to resolve account-level intent not reaching HubSpot
- **Intent data dashboard** (customers vs. non-customers, volume, clusters) and an
  **intent-to-revenue attribution process**

### 3.4 Results & Achieved Benefits

> ❌ **[BLOCKING GAP]** Same as §2.5. Needed: intent-sourced pipeline value, alerts
> generated, opportunities attributed to intent triggers, seller response time.

---

## 4. Supporting delivery record

**Plan:** 8 phases, 71 tasks, 70 complete (98.6%).

| Phase | Tasks | Complete |
|---|---|---|
| Phase 0 — Kick-Off & Discovery | 19 | 19 (100%) |
| Phase 1 — HubSpot Foundational Configuration | 8 | 8 (100%) |
| Phase 2 — Contact & List Import + Lifecycle/MQL/SQL | 7 | 7 (100%) |
| Phase 3 — Marketing Hub Configuration | 12 | 12 (100%) |
| Phase 4 — ZoomInfo–HubSpot Integration & Optimization | 7 | 7 (100%) |
| Phase 5 — Salesforce–HubSpot Integration | 9 | 9 (100%) |
| Phase 6 — Revenue Efficiency Model Build | 4 | 4 (100%) |
| Phase 7 — Training & Wrap-Up | 5 | 4 (80%) |

Outstanding: *QA & Go-Live Readiness Review*. A parallel PacTec Master Plan tracks
ongoing client success at 107/138.

Discovery included a genuine technical audit — website, email, HubSpot, ZoomInfo and
Salesforce — with PacTec's Salesforce admin exporting a full field inventory before any
mapping began.

**Also delivered:** Revenue Efficiency Model (five lists — Keep, Grow, Multiply, Convert,
Expand) with purchase-readiness notifications; email subdomain `mail.pactecinc.com` with
DKIM/SPF/DMARC; AEO analysis in HubSpot plus a full AEO/SEO audit of `pactecinc.com`;
master suppression list with automated bounce/unsubscribe removal; lead scoring and
MQL/SQL handoff; form audit, archive and embed-coverage verification; print campaign
click/QR tracking diagnosed and fixed.

**Engagement record:** 28 calls · ~115 emails · 22 tickets · 37 meetings · 21 transcripts.

---

## 5. Other accreditations — assessment

### Custom Integration — ❌ does **not** qualify

The hard gate explicitly **rejects marketplace and native connectors**. PacTec's build is
the native HubSpot–Salesforce connector plus the native ZoomInfo integration, expertly
configured and remediated — but configuration is not custom development, serverless
functions, or non-Zapier iPaaS. The gate also rejects one-time migrations and
in-development work.

The nearest qualifying assets are the **XPRT Premium API integration feasibility
assessment with an n8n recommendation** (n8n *is* qualifying non-Zapier iPaaS) and
research into **batch Salesforce property creation via API/MCP server** — both research,
not shipped builds.

**Action:** either ship the n8n/XPRT build as a follow-on and re-evaluate, or source
Custom Integration evidence elsewhere. Do not submit PacTec.

### Data Migration — weak

*Import Historical Salesforce Activity Data into HubSpot* has a qualifying source
(Salesforce) and date, but it is an activity backfill inside an integration engagement,
not a standalone migration project — and the gate warns that native-import-only
experience is insufficient. Treat as a fallback, not a lead candidate.

### Onboarding items 1 & 3 — ❌ not suitable

The plan is typed "HubSpot Onboarding" and delivers Marketing Hub configuration, but
there is **no Sales Hub phase** — PacTec runs Salesforce as CRM of record. Items 1 and 3
belong to CalcFocus. PacTec's role in this submission is item 2 only.

---

## 6. Open items before submission

**Blocking**
- [ ] **Confirm PacTec's Sales Hub tier.** If it is not Professional or above, PacTec
      cannot serve item 2 and a replacement customer is required.
- [ ] Produce the **data flow diagram** (§2.3)
- [ ] Capture **quantified results** for both use cases (§2.5, §3.4)

**Non-blocking**
- [ ] Close the outstanding *QA & Go-Live Readiness Review* task
- [ ] Obtain PacTec's HubSpot Portal ID
- [ ] Confirm the PacTec MSA permits sharing engagement documents with HubSpot
- [ ] Client reference from Katie Lanoix

---

*Sources: ClientCommand Supabase `zjtgesaiemlveuoymubo` — `accreditation_items`,
`accreditation_item_requirements`, `accreditations.hard_gates`,
`portal_accreditation_eligibility`; QBS portal `3bb7fb52-ec7e-468f-9fe9-99180a91175b`;
plan `c6c742c9-092c-4050-aec9-dd6247bdb846`; HubSpot portal 20682069 company
`53419639405`; Zoom recordings May–September 2026.*
