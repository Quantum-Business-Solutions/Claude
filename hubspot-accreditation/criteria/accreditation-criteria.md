# HubSpot Partner Accreditation — Criteria Reference

**Authoritative source:** ClientCommand Supabase `zjtgesaiemlveuoymubo`, Accreditation Hub
schema (`accreditations`, `accreditation_items`, `accreditation_item_requirements`).
Built from HubSpot's own preparation guides; live in production since 2026-08-12.

This file is a **read-only mirror** for case-study authoring. The database is the source
of truth — if the two disagree, the database wins.

---

## 1. The six open accreditations

| Wave | Accreditation | Prep guide | Practical exercise | Unlocks |
|---|---|---|---|---|
| 1 | **Onboarding** | ✅ | No | Partner Scaled Onboarding (HubSpot sells, you deliver) + Partner Assisted Deals |
| 2 | **CRM Implementation** | ❌ **not obtained** | Yes | Upmarket Referral Programme — 10% commission for a year + Co-Delivery + PAD. **Widest benefit set of the six.** |
| 3 | **Custom Integration** | ✅ | Yes | Co-Delivery + PAD |
| 4 | **Data Migration** | ✅ | Yes | Co-Delivery + PAD |
| 5 | **Solutions Architect Design** | ✅ | Yes | Co-Delivery + PAD |
| 6 | **Service Implementation** | ✅ | No | PAD + upmarket consideration only — **not** on the Co-Delivery list |

*Content Experience* is seeded `closed` — its Academy playlist is live but the
accreditation is not open. Exclude from readiness views.

Process is one round, rolling since 2025-09-15.

---

## 2. Certification requirements

- **Essential certifications: 3 active holders each. Add-on certifications: 2.**
  The count is **per-accreditation** (`accreditation_certifications.holders_required`),
  never read off the `certifications` table.
- Holders must have an email on a **QBS partner domain** that counts toward
  accreditation. Open Flow domains (`openflow.inc`, `openflowdigital.com`) are excluded.
- Certifications must be **active at the moment of application**. Expired certs
  disqualify the entry.
- **Gaps are not additive across accreditations.** *Integrating With HubSpot I* serves
  three accreditations; *Architecture I* serves two. A holder earned once counts
  everywhere. Never sum `total_gap` across rows.
- The **"team of five" cap no longer exists** — any full-time employee counts.

### Current standing (as at 2026-08-12)

| Accreditation | Certification gap |
|---|---|
| **Onboarding** | **0 — complete** |
| Custom Integration | 2 |
| Data Migration | 2 |
| CRM Implementation | 3 |
| Service Implementation | 4 |
| Solutions Architect Design | 6 |

**The Essential Pack is complete.** Kenzie Braun, Marko Ajder and Shawn Peterson each
hold all nine. **Onboarding is certification-ready; only casework is outstanding.**

⚠️ **Every `expires_at` is NULL.** The renewal watch is blind until expiry dates are
captured. Known hygiene issues: Patrick Dodge counts twice (records on both QBS domains),
and `openflow@thequantumleap.business` is a shared inbox counted as a person.

---

## 3. References and clocks

- **Two customer references per accreditation**, complete **before** the application
  opens. Each reference has **10 days** to respond or eligibility restarts.
- **Re-evaluation every 6 months** from award.
- **Reapplication blocked for 6 months** after a decline.

---

## 4. Hard gates by accreditation

### Onboarding
> Profiled customer must hold **BOTH Marketing Hub AND Sales Hub at Professional or
> higher** — Starter is rejected. Item 2 requires a **Salesforce Integration** use case
> for US and UK partners.

**Items:**

| # | Item | Reuse rule |
|---|---|---|
| 1 | **Objectives-Based Onboarding Project Plan** — project plan + HubSpot Portal ID. Best submissions show value realised within **90 days** of kickoff. Metadata: engagement start/end, Hubs onboarded, subscription levels, users onboarded, customer company size. | **Same engagement as item 3** |
| 2 | **Integration Documentation (two use cases)** — a Salesforce integration use case **plus** one additional use case using a marketplace integration or iPaaS. *Turning an integration on does not count.* Ads, Social and video-hosting apps excluded. | May be a different customer, **same Pro-or-above rule applies** |
| 3 | **Project Review** — recap of the item 1 engagement showing strategic oversight, execution and adaptive problem-solving beyond technical setup. | **Same engagement as item 1** |

**Item 1 requirements:** Objectives & Scope · Key Roles & Responsibilities · Onboarding
Journey/Timeline (usable HubSpot within 90 days) · Communication Plan · Success Metrics &
Hand-off Criteria · Risk Management · Training Strategy (must **name documentation
delivered**) · Feedback Mechanisms.

**Item 2 requirements:** Business Use Case · Solution Description (incl. alternatives
considered) · **Data Flow Diagram** + written explanation · How the Integration Was Used ·
**Results & Achieved Benefits (quantified)**.

**Item 3 requirements:** Executive Summary · Key Achievements & Deliverables **with
actual numbers against the item 1 success metrics** · Challenges, Issues & Lessons
Learned · Post-Onboarding Strategy.

### Custom Integration
> Must be multi-object and/or bidirectional via **custom development, serverless
> functions, or non-Zapier iPaaS**. **Rejected:** marketplace/native connectors, Zapier,
> Ops Hub alone unless efficiency unattainable otherwise, one-time migrations,
> in-development work, multiple customers. Integration in item 2 must be currently ACTIVE.

| # | Item | Reuse rule | Max files |
|---|---|---|---|
| 1 | Documented Integration Plan — ideal: multi-object **and** bidirectional; sufficient: either. Project must have concluded. | One customer only | 3 |
| 2 | Integration Diagram — deployed and currently **active** in a customer portal | Same engagement as item 1 | 3 |
| 3 | Practical Exercise — **ShopSpot** (hypothetical: HubSpot Enterprise e-commerce, homegrown platform, registrations→contacts with profile sync, purchases→deals with value/items/date, encrypted; 1M+ orders/yr, 10,000+ in a 30-min Black Friday window) | No customer needed | 3 |

### Data Migration
> **Two separate projects in the last 12 months** migrating from a **leading CRM,
> marketing automation platform, or helpdesk INTO HubSpot**. Experience **exclusively
> with native import tools is explicitly insufficient** — must show standard objects
> plus contextual data.

| # | Item | Reuse rule | Max files |
|---|---|---|---|
| 1 | Migration Plan — methodology and delivery approach for a single migration | One of the two required projects | 4 |
| 2 | Mapping Documentation — visual mapping proving source data relationships and complexities survive | Same or different customer from item 1 | 3 |
| 3 | Practical Exercise — **SolutionSpot** (hypothetical: large B2C moving CRM and CPQ to HubSpot, data across a warehouse and a subscription system; role-based access by lifecycle, flagged records, goal tracking, lead handoff) | No customer needed | 3 |

### Solutions Architect Design
> **HARD BUILD REQUIREMENT** — must customise the CRM via **one** of: UI extensibility
> features (CRM Development tab projects), custom CRM cards through an OAuth integrated
> application, or a custom-coded workflow extension driving a CRM process with external
> data. **Items 1 and 2 must profile DIFFERENT customers.**

### CRM Implementation
> Upmarket complexity bar defined in the prep guide, **which has not been obtained**.
> Applications accepted in English, Spanish, French.

⚠️ No items or requirements exist in the database. **Obtain the prep guide before
scoping any CRM Implementation casework.** Do not scaffold placeholder items.

### Service Implementation
> **STOP-GATE, all mandatory:** 200+ full-time employees · 75+ assigned paid Service
> Enterprise seats · Service Hub Enterprise · teams distributed nationally or globally.
> Prior decline must be 6+ months old.
> Also expected: major process redesign plus system migration (Zendesk preferred),
> 2+ custom integrations, 2+ business units or regions, 2+ languages, stakeholders from
> 2+ departments.

---

## 5. Standing compliance item

**Client MSAs must permit sharing engagement documents with HubSpot.** Verify per client
before submitting any case study. Tracked in `../README.md`.

---

## 6. Academy prerequisite playlists

| Track | Playlist ID |
|---|---|
| CRM Implementation | 143855 |
| Custom Integration | 143856 |
| Data Migration | 143857 |
| Onboarding | 143858 |
| Solutions Architecture Design | 143862 |
| Service Implementation | 178506 |
| Content Experience (closed) | 77740 |
