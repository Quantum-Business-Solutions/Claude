# CalcFocus — Onboarding Accreditation, Items 1 & 3

**Accreditation:** Onboarding (Wave 1 — QBS priority)
**Submission items covered:** Item 1 (Objectives-Based Onboarding Project Plan) and
Item 3 (Project Review)
**Reuse rule:** Items 1 and 3 **must be the same engagement**. This document serves both.
**Status:** Draft — subscription gate CLEARED; blocked on OBO confirmation + actual metrics

---

## 0. Gate check

| Gate | Status | Source |
|---|---|---|
| Marketing Hub Professional or above | ✅ **Professional** | `portal_accreditation_eligibility`, confirmed by Shawn 2026-08-12 |
| Sales Hub Professional or above | ✅ **Professional** | Same |
| Engagement within last 12 months | ✅ | Apr–Jul 2026 |
| Customer meaningfully using HubSpot within 90 days of kickoff | ✅ | Kickoff 2026-04-27; hub configuration confirmed and full team training delivered 2026-07-16/17 — **day 80–81** |
| Delivered under Objectives-Based Onboarding methodology | ⚠️ **[CONFIRM]** | Substantively yes (see §2); needs an explicit yes from Shawn/Marko and `onboarded_via_obo` set in the DB |
| Success metrics tracked with real numbers | ❌ **[BLOCKING]** | Item 3 requires actuals against the item 1 KPIs. Not currently captured. See §7. |

---

## 1. Engagement metadata (required by item 1)

| Field | Value |
|---|---|
| Customer | CalcFocus (`calcfocus.com`) |
| HubSpot Portal ID | **[NEEDED]** — CalcFocus's own portal ID, not QBS 20682069 |
| QBS portal record | `d4d36cc1-7b87-49ff-a4ef-4f61e2c0d960` |
| HubSpot company record (QBS CRM) | `52746451314` |
| Industry | Computer Software |
| Company size | 58 employees |
| Location | Philadelphia, Pennsylvania |
| Engagement start | 2026-04-22 (portal) / 2026-04-27 (plan of record) |
| Onboarding completion | 2026-07-17 (client-confirmed) |
| Hubs onboarded | Marketing Hub, Sales Hub |
| Subscription levels | Marketing Hub **Professional**, Sales Hub **Professional** |
| Users onboarded | **[NEEDED]** — exact count; 10 attended the 2026-07-17 training |
| Plan of record | *Calcfocus Master Plan* `ed0038fe-70b3-4507-8b1b-a7f3d3f1d6b8` |

---

## 2. Item 1 — Objectives-Based Onboarding Project Plan

The eight requirements HubSpot asks for, mapped to what QBS actually delivered.

### 2.1 Objectives & Scope

CalcFocus, a 58-person software business, had bought HubSpot and not implemented it.
There was no trustworthy CRM baseline: contacts sat in spreadsheets and disconnected
lists, pipeline data sat with individual sellers, sales stage nomenclature did not match
how the business forecast, and there was no lifecycle model, segmentation, marketing
infrastructure or reporting layer.

**In scope:** two-hub implementation (Marketing + Sales), data migration into HubSpot,
lifecycle and segmentation architecture, routing, attribution, dashboards, and team
enablement.

**Out of scope — and tracked as such.** The plan carries a dedicated
*Wish List — Items Identified Out of Scope During Onboarding* phase, so scope discovered
mid-engagement was captured and parked rather than silently absorbed or dropped. This is
direct evidence of scope discipline for item 3.

### 2.2 Key Roles & Responsibilities

| Side | People |
|---|---|
| QBS | Shawn Peterson, Marko Ajder, Patrick Dodge, Barb Peterson, Jelena Andric |
| CalcFocus | Lucy, Christine Peart, Nate, Steve Meade, Alex Terruso, Kristin Wheeler, Pam Doggett, Lori Baca, MacKenzie Braun |

Responsibilities were assigned at task level, not just named. Of the 75 onboarding tasks,
a distinct set is flagged `client_action` — brand assets, M365 admin consent, DNS access,
WordPress admin, internal IPs for tracking exclusion, contact spreadsheet, ad and social
account connections, and three configuration questionnaires (Email Type, Email Settings,
Forms Settings). Client dependencies were gated **before** kickoff rather than chased
afterwards.

### 2.3 Onboarding Journey / Timeline

Eight phases. **75 of 75 onboarding tasks complete (100%).**

| Phase | Tasks | Complete |
|---|---|---|
| Pre-Kickoff | 7 | 7 (100%) |
| HubSpot Kick-Off | 9 | 9 (100%) |
| HubSpot Foundational Configuration | 21 | 21 (100%) |
| HubSpot Marketing Hub Configuration | 25 | 25 (100%) |
| HubSpot Sales Hub Set-Up | 12 | 12 (100%) |
| HubSpot Onboarding Wrap-Up | 1 | 1 (100%) |
| **Onboarding total** | **75** | **75 (100%)** |
| Ongoing client success (post-onboarding) | 76 | 45 |
| Wish List — explicitly out of scope | 1 | 0 |

**90-day proof:** kickoff 2026-04-27 → full team training on live migrated data
2026-07-16/17, **day 80–81**. Hub-level client confirmations closed in the same window.
The customer was meaningfully using HubSpot inside the 90-day bar.

### 2.4 Communication Plan

- **Weekly** client success meeting (standing recurring Zoom, `81797746091`)
- **Monthly** strategic review, scheduled through December 2026
- Ad-hoc working sessions on demand (e.g. HubSpot Working Session 2026-07-16)
- Formal recap emails after key sessions, listing action items, owners and next steps
- Session recordings supplied to the client for their own archives
- All correspondence logged to the CRM: **19 calls · ~230 emails · 36 meetings ·
  30 transcripts**

### 2.5 Success Metrics & Hand-off Criteria

**Hand-off criteria — evidenced.** Three formal confirmation gates, all closed:
1. *Client Confirmation of Marketing Hub Configuration*
2. *Client Confirmation of Sales Hub Configuration*
3. *Client Confirmation of HubSpot On-Boarding Completion*

Hand-off to ongoing support is evidenced by the transition from the onboarding phases to
the retained client-success cadence (weekly + monthly, booked through Dec 2026).

> ⚠️ **KPIs — [BLOCKING GAP].** The plan evidences *completion* gates but not *numeric
> KPIs*. Item 1 asks for "KPIs defining success" and item 3 requires **actual numbers
> against them**. Kickoff did cover goals and KPIs; they need retrieving from the kickoff
> record and restating here. See §7.

### 2.6 Risk Management

Risks visible in the delivery record and how they were handled:

| Risk | Mitigation as delivered |
|---|---|
| Client-side dependencies stalling the build | Gated as explicit pre-kickoff tasks with named owners before kickoff |
| Migrating unreliable data | Joint client/QBS *Verification of Baseline Data Imported into HubSpot*; deal data routed to Nate for review **before** final import |
| Training landing on sample data | Training deliberately scheduled *after* migration completed, so the team trained on their own live records |
| Scope creep | *Wish List — Out of Scope* phase maintained throughout |
| Forecast model mismatch | Sales stage nomenclature and probabilities rebuilt to match the business's own model, as specified by Steve Meade and Nate |
| Tier-capability mismatch | Enterprise-only churn reporting identified as unavailable on Professional; Marko built calculated-property workarounds instead of a licence upsell |

### 2.7 Training Strategy

- **HubSpot Training Session, 2026-07-17** — 10 attendees, recorded with transcript
- **HubSpot Sales Training Session, 2026-07-17** — sales and marketing teams
- **HubSpot Working Session, 2026-07-16**
- Dedicated 1-hour email/marketing setup session
- **Quantum Academy** enrolment for named client staff
- Embedded enablement across the plan — 20+ explicit "Educate on…" tasks covering
  workflows, lead statuses, record creation forms, uploading records, brand guidelines,
  campaigns, nurture content, lead scoring, blog settings, CTAs, forms, chatbot, custom
  ad audiences, source data, Google Analytics, sequences, meeting links, meeting/call
  outcomes and sales collateral

> ⚠️ **[GAP]** Item 1 asks the training strategy to **name the documentation delivered** —
> admin guides, integration documentation, troubleshooting FAQs. Recordings and live
> sessions are evidenced; written artefacts are not. Confirm what exists (the CalcFocus
> Outlook integration overview doc is one) and attach it.

### 2.8 Feedback Mechanisms

- Weekly client success meeting as the standing feedback loop
- Three client questionnaires feeding configuration decisions
- Client review gate on deal data before final import
- *Provide ongoing support for dashboard/report adjustments as feedback is received* —
  a standing task, i.e. feedback-driven iteration was planned, not incidental
- Three formal client confirmation gates

---

## 3. What was built (supporting detail)

**Foundational** — Q2 Lifecycle Stage Workflows; "Former Customer" lifecycle workflow
remediated; **Q2 Universal List Library, 111 new lists**; persona properties + buyer
persona workflow; round-robin lead assignment workflow; Q2 Attribution & Sequence Package
via Supered; HubSpot Portal Recon & Q2 Framework strategic mapping; LinkedIn Sales
Navigator and M365 integrations; brand settings.

**Marketing Hub** — email sending domain with DKIM/SPF/DMARC; 4 form templates
(Contact Us, eBook, Webinar, Quote); nurture campaign framework templates; marketing
dashboard; WordPress tracking code.

**Sales Hub** — standard sales dashboard; deals pipeline and active lists; task queues;
custom call outcomes, meeting types and meeting outcomes; calendar connections confirmed.

**Data migrated into HubSpot** — contact migration; Nate's pipeline/deals with company
associations and stages; Steve Meade carrier contact set with custom account properties
matching the master accounts spreadsheet; product library (template + worked example);
event/list sourcing with an origin property per contact; portal-wide domain backfill;
company-name cross-check to recover missing domains.

---

## 4. Item 3 — Project Review

### 4.1 Executive Summary

CalcFocus moved from an unimplemented HubSpot instance to a live two-hub revenue system
inside 90 days: migrated data, a 111-list segmentation library, lifecycle and persona
automation, round-robin routing, attribution, marketing and sales dashboards, and a
trained team — confirmed complete by the client at three separate gates.

The engagement converted from project to retained relationship, with weekly client
success meetings and monthly strategic reviews booked through December 2026.

### 4.2 Key Achievements & Deliverables

75/75 onboarding tasks complete; 111 lists; 4 form templates; 2 dashboards; both hubs
configured and client-confirmed; 4 data sets migrated (contacts, deals/pipeline, carrier
accounts, product library); 3 training sessions delivered on live data.

> ❌ **[BLOCKING]** This section must carry **actual numbers against the item 1 success
> metrics**. Deliverable counts are not KPI actuals. Until real before/after figures land
> here, item 3 is not submittable. See §7.

### 4.3 Challenges, Issues & Lessons Learned

- **No trustworthy baseline.** Data was spread across spreadsheets and individual
  sellers. Resolved by gating a joint verification step and a client review cycle on
  deal data before final import.
- **Forecast model mismatch.** Out-of-the-box stages did not match how CalcFocus
  forecast. Rebuilt to the client's own nomenclature and probabilities rather than
  asking the business to adapt to the tool.
- **Tier limitation on churn reporting.** Native churn reports require Enterprise.
  Rather than pushing an upgrade, workarounds were built with calculated properties —
  adaptive problem-solving within the customer's licence.
- **Sequencing training after migration.** Training on sample data would have wasted the
  session; it was deliberately held until migration completed.
- **Scope discovered mid-flight.** Handled via a standing out-of-scope wish list.

### 4.4 Post-Onboarding Strategy

Retained client success: weekly meetings and monthly strategic reviews through December
2026, with 45 of 76 post-onboarding tickets already closed. Immediate next steps in the
backlog include KPI-driven dashboard and report builds and continued data hygiene.

---

## 5. Other accreditations — assessment

**Data Migration:** ⚠️ Unlikely to qualify. The hard gate requires migration from a
**leading CRM, marketing automation platform, or helpdesk**, and states that
"experience exclusively with native import tools is explicitly insufficient". The
CalcFocus work is spreadsheet and list based via native import. Unless a qualifying
source system is confirmed, do not use this engagement for Data Migration.

**CRM Implementation:** Possible on substance, but the prep guide has not been obtained
and the upmarket complexity bar is unknown. At 58 employees, CalcFocus may sit below it.

---

## 6. Reference requirement

Onboarding requires **two customer references**, complete **before** the application
opens; each has 10 days to respond or eligibility restarts. CalcFocus is a strong
reference candidate (Lucy or Christine Peart).

---

## 7. Open items before submission

**Blocking**
- [ ] Retrieve the KPIs agreed at kickoff and restate them in §2.5
- [ ] Capture **actual numbers** against those KPIs for §4.2 — pipeline visibility,
      forecast accuracy, records migrated by object, lead response time,
      marketing-sourced pipeline, user adoption/logins
- [ ] Obtain CalcFocus's **HubSpot Portal ID**
- [ ] Confirm the engagement is formally classed as Objectives-Based Onboarding, and set
      `onboarded_via_obo` + `success_metrics_tracked` in `portal_accreditation_eligibility`

**Non-blocking**
- [ ] Exact count of users onboarded
- [ ] Name and attach written training documentation (admin guides, FAQs)
- [ ] Exact migrated record counts by object
- [ ] Confirm the CalcFocus MSA permits sharing engagement documents with HubSpot
- [ ] Secure client reference commitment

---

*Sources: ClientCommand Supabase `zjtgesaiemlveuoymubo` — `accreditation_items`,
`accreditation_item_requirements`, `portal_accreditation_eligibility`; QBS portal
`d4d36cc1-7b87-49ff-a4ef-4f61e2c0d960`; plan `ed0038fe-70b3-4507-8b1b-a7f3d3f1d6b8`;
HubSpot portal 20682069 company `52746451314`; Zoom recordings April–July 2026.*
