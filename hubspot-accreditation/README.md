# HubSpot Partner Accreditation — Casework

Case study documents for QBS's HubSpot Solutions Partner accreditation submissions.

**Target: Onboarding accreditation (Wave 1).** Certifications are already complete —
gap 0. Casework is the only thing standing between QBS and the application.

---

## Contents

| File | Purpose |
|---|---|
| `criteria/accreditation-criteria.md` | Mirror of the real criteria from the Accreditation Hub database |
| `case-studies/calcfocus-onboarding.md` | **Onboarding items 1 + 3** — OBO Project Plan & Project Review |
| `case-studies/pactec-integration.md` | **Onboarding item 2** — Integration Documentation, two use cases |
| `evidence/evidence-register.md` | Source-of-truth index and alternative customer candidates |

---

## The Onboarding submission at a glance

| Item | Customer | Status | Blocker |
|---|---|---|---|
| 1 — OBO Project Plan | **CalcFocus** | Draft complete | KPI actuals; HubSpot Portal ID; OBO confirmation |
| 2 — Integration Documentation | **PacTec** | Draft complete | **Sales Hub tier unconfirmed**; data flow diagram; quantified results |
| 3 — Project Review | **CalcFocus** | Draft complete | Actual numbers against item 1 KPIs |

Items 1 and 3 must be the same engagement — CalcFocus serves both. Item 2 may be a
different customer, and PacTec is the natural fit because it carries **both** required
use cases (Salesforce + ZoomInfo marketplace) in one account.

---

## Blocking items, in priority order

### 1. Confirm PacTec's Sales Hub tier 🔴
Item 2 restates the Marketing **and** Sales Pro-or-above rule for its customer. PacTec's
`sales_hub_tier` is null and PacTec runs **Salesforce as system of record**, so a Sales
Hub subscription cannot be assumed. If PacTec has no Sales Hub Professional licence,
item 2 needs a different customer — see the alternatives in the evidence register.

*This is the single question that most changes the shape of the submission. Answer it first.*

### 2. Capture real outcome numbers 🔴
Three separate requirements demand quantified results:
- Item 1 §5 — KPIs defining success
- Item 3 §2 — **actual numbers against those KPIs**
- Item 2 §5 — quantified improvements (efficiency, data accuracy, conversion, cost)

Both case studies currently evidence *scope, completion and client confirmation*
thoroughly, and *business results* not at all. This is the largest content gap in the set
and cannot be inferred from the delivery record — it needs a client conversation.

Best route: the monthly strategic reviews already booked with both accounts.

### 3. Produce the data flow diagram 🔴
Item 2 requires a diagram of the customer's data model around HubSpot plus a written
explanation. Objects and directions are already specified in
`case-studies/pactec-integration.md` §2.3 — the diagram just needs drawing.

### 4. Obtain both customers' HubSpot Portal IDs 🟠
Item 1 requires the customer's own portal ID, not QBS's 20682069.

### 5. Confirm OBO classification 🟠
Set `onboarded_via_obo` and `success_metrics_tracked` on CalcFocus's
`portal_accreditation_eligibility` row once confirmed.

### 6. MSA clearance 🟠
Verify both client MSAs permit sharing engagement documents with HubSpot. Standing
compliance item on every accreditation submission.

---

## Deliverables still to produce

- [ ] Data flow diagram — PacTec (HubSpot ↔ Salesforce ↔ ZoomInfo)
- [ ] Two customer references (10-day response clock; must complete **before** the
      application opens)
- [ ] Written training documentation named in item 1 §7 — admin guides, integration
      documentation, troubleshooting FAQs

---

## Assessments recorded here (so they are not re-litigated)

**PacTec is not a Custom Integration candidate.** The hard gate explicitly rejects
marketplace and native connectors. PacTec's build is the native HubSpot–Salesforce
connector plus the native ZoomInfo integration — expertly configured and remediated, but
configuration is not custom development, serverless functions, or non-Zapier iPaaS. The
nearest qualifying asset is the XPRT/n8n work, which is research, not a shipped build.

**CalcFocus is not a strong Data Migration candidate.** The gate requires a leading CRM,
MAP or helpdesk as source, and states native-import-only experience is insufficient. The
CalcFocus work is spreadsheet and list based.

**CRM Implementation cannot be scoped yet.** The prep guide has never been obtained and
no items or requirements exist in the database. Obtain the guide first. It carries the
widest benefit set of all six, so this is worth doing.

---

## Where the data comes from

- **Criteria:** ClientCommand Supabase `zjtgesaiemlveuoymubo` — the Accreditation Hub,
  live in production since 2026-08-12
- **Delivery record:** Client Command portals, master plans and ticket history
- **Engagement history:** HubSpot portal 20682069; Zoom recordings and transcripts
- **Programme context:** Hindsight memory bank

Nothing in these case studies is invented. Every gap is marked `[VERIFY]`, `[NEEDED]`,
`[TO PRODUCE]` or `[BLOCKING]` rather than filled with a plausible number.
