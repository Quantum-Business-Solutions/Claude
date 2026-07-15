# QBS SOW Section Structure Guide

This file defines every section of a QBS Statement of Work, including:
- What goes in each section
- Default / boilerplate language to use
- Variables to fill in (shown in [BRACKETS])
- QBS voice and tone guidelines per section

---

## DOCUMENT HEADER

```
STATEMENT OF WORK (SOW)
[Project Title — e.g., "HubSpot Onboarding & Q2™ Revenue Operations Framework"]

This Statement of Work ("SOW") is entered into pursuant to the applicable Master Services
Agreement ("MSA") between Quantum Business Solutions ("Quantum") and [CLIENT LEGAL NAME]
("Client"), or, if no MSA exists, this SOW constitutes a standalone agreement between
the parties (collectively, the "Parties").
```

---

## SECTION 1 — PURPOSE & OVERVIEW

**Goal:** Set context. Establish what this engagement is, why it exists, and what it covers at a high level.

**Boilerplate:**
```
The purpose of this SOW is to define, in detail, the scope, deliverables, responsibilities,
estimated execution effort, timeline, limitations, and commercial terms for [SERVICE DESCRIPTION]
services to be provided by Quantum to Client.

[If Q2™ applies: This engagement includes Quantum's proprietary Q2™ Office Equipment Revenue
Operations Framework, a standardized HubSpot-based framework purpose-built for office equipment
and technology dealers.]

This SOW is intentionally comprehensive to:
- Clearly define what is included in the quoted price
- Explicitly define what is not included
- Establish scope boundaries using estimated execution time
- Prevent scope creep and pricing ambiguity
- Ensure alignment between sales, delivery, finance, legal, and Client expectations
```

---

## SECTION 2 — SCOPE OF SERVICES

**Goal:** Name the products and service categories in scope.

**Boilerplate:**
```
Quantum shall provide [onboarding / configuration / strategy / automation / development] services
for the following [products / service areas], provided Client maintains all required licenses
directly with applicable vendors:

- [List each product or service area, e.g.:]
- Foundational HubSpot Configuration
- Sales Hub Enterprise
- Marketing Hub Professional
- Q2™ Office Equipment Revenue Operations Framework (Proprietary to Quantum)
- [ZoomInfo Integration (If Licensed)]
- [n8n Automation Workflows]

Services include a combination of:
- Hands-on system configuration
- Strategic [revenue / marketing / operations] process mapping
- Training and enablement
- Guided education and best-practice instruction

Only the services expressly described in this SOW and its exhibits are included.
```

---

## SECTION 3 — FRAMEWORK/PRODUCT DESCRIPTION (If Applicable)

**Use when:** Q2™ framework is in scope, OR any proprietary Quantum methodology is being delivered.

### 3.1 Framework Description
Describe the proprietary framework at a high level. For Q2™:
```
Q2™ is Quantum's proprietary HubSpot revenue operations framework developed specifically for
office equipment and technology dealers. Q2 extends HubSpot's native CRM functionality through
standardized custom objects, properties, workflows, automation, dashboards, reporting, and
enablement assets.
```

### 3.2 Standardized Framework Notice (CRITICAL — Always Include)
```
[FRAMEWORK NAME] is delivered as a standardized framework utilizing pre-built templates,
configurations, workflows, lists, dashboards, and automation developed by Quantum.

Customization beyond the standard [FRAMEWORK NAME] framework is explicitly excluded and
requires a written Change Order. This includes, but is not limited to, custom workflows,
dashboards, reports, object structures, data models, or automation logic.
```

### 3.3 Intellectual Property
```
[FRAMEWORK NAME], including all methodologies, templates, configurations, documentation,
and design patterns, is and shall remain the exclusive intellectual property of Quantum
Business Solutions.

Configuration of [FRAMEWORK NAME] within Client's [platform] environment does not transfer
ownership rights. Quantum reserves the right to remove proprietary assets from Client's
environment in the event of non-payment, including any future seat-based fees.
```

---

## SECTION 4 — PROJECT TIMELINE

**Goal:** Set duration, start trigger, and delay policy.

**Boilerplate:**
```
The engagement shall be delivered over a [NUMBER]-week period commencing on the project
kickoff date, subject to timely Client participation, approvals, data delivery, and system access.

A detailed [NUMBER]-Week Onboarding Schedule with task-level responsibilities is attached
as Exhibit A and incorporated by reference.

Delays caused by Client may extend the timeline without penalty to Quantum.
```

**Default timelines by project type:**
- HubSpot Full Onboarding: 8 weeks
- HubSpot Sales Hub Only: 4–6 weeks
- ZoomInfo Onboarding: 2–4 weeks
- Marketing Engagement: defined per engagement
- Consulting: defined per engagement
- n8n / Automation: 2–6 weeks
- Custom Dev: milestone-based

---

## SECTION 5 — MEETING ALLOCATION & LIMITS

**Goal:** Cap live meeting time. This is a critical scope protection section.

### 5.1 Live Meetings
```
This engagement includes an estimated execution time of up to [NUMBER] total hours of live
meetings during the [NUMBER]-week period. Meetings may include:
- Kickoff and onboarding planning
- Status and strategy meetings
- Training and enablement sessions
- Review, QA, and go-live readiness meetings
```
Default: 12 hours for HubSpot full onboarding.

### 5.2 Meeting Preparation & Follow-Up
```
This engagement includes an estimated execution time of up to [NUMBER] hours for meeting
preparation, documentation, and follow-up.
```
Default: 6 hours.

### 5.3 Scope Enforcement
```
Meeting or preparation time exceeding these estimates — particularly due to delayed inputs,
missed approvals, rescheduling, or rework — is out of scope and requires a written Change
Order or may be billed at Quantum's standard hourly rate of $[OVERAGE RATE]/hour.
```

---

## SECTION 6 — DELIVERABLES & ESTIMATED EXECUTION TIME

**Goal:** Define every included deliverable with estimated effort. This is the core of the SOW.

### Opening Paragraph (Always Include)
```
All deliverables listed below:
- Represent standard [Q2™ / HubSpot / project] components
- Include estimated execution time, not prepaid or guaranteed hours
- Serve as scope boundaries, not entitlements

Estimated execution time reflects anticipated effort required to deliver the standard framework
and does not obligate Quantum to exhaust all estimated hours.
```

### Deliverables Table Format

| Deliverable | Standard | Description | Estimated Execution Time (Hours) |
|---|---|---|---|
| [Name] | Yes / No | [Brief description] | [Number] |

**Column definitions:**
- **Standard = Yes**: Included in quoted price
- **Standard = No**: Not included; listed for transparency (like Data Cleanup)
- **Description**: One-line description. For time-limited items, note the limit inline (e.g., "Quantum will invest up to 2 hours...")
- **Estimated Execution Time**: Hours estimate for scope boundary purposes only

### Common Customizations Not Included Table (Always Include)

Title this subsection: **"Common Customizations (Not Included Unless Explicitly Added)"**

Opening text:
```
The following items represent frequently requested customizations that are not included in
the standard scope unless explicitly identified as included in this SOW. All customization
requires a written Change Order prior to execution.
```

Table format:
| Customization Area | Description | Typical Estimated Effort (Hours) | Dependencies / Notes |
|---|---|---|---|

**Standard exclusions to always list:**
- Custom Workflow Logic: 4–20 hrs
- Custom Dashboards: 4–16 hrs per dashboard
- Custom Reports: 2–8 hrs per report
- Custom Properties: 1–6 hrs
- Advanced Lead Scoring: 6–16 hrs
- Data Migration (Complex): 10–40 hrs
- Integration Customization: 6–25 hrs
- Additional Training Sessions: 1–3 hrs per session
- Ongoing Admin Support: Ongoing (separate agreement required)
- Email / Content Copywriting: 4–20 hrs

Adapt this list based on project type.

### 6.X Estimated Execution Time Disclaimer (Always Include)
```
- Estimated execution time is not prepaid, not banked, and not transferable
- Time estimates define maximum included scope
- Work beyond estimates due to customization, change requests, or Client delays is out of scope
```

### 6.X Included Scope & Pricing Confirmation (Always Include)
```
The professional services price quoted to and paid by Client includes:
- All deliverables marked Standard = Yes
- All estimated execution effort associated with those standard deliverables
- Any customization or non-standard work explicitly identified as included within this SOW

Any work not expressly listed as included in this SOW is excluded from the quoted price
and requires a written Change Order.
```

---

## SECTION 7 — RESPONSIBILITIES

### 7.1 Quantum Responsibilities
```
- Project management and coordination
- [Platform] configuration per scope
- Training and enablement delivery
- QA and readiness support
```

### 7.2 Client Responsibilities
```
- Assign a primary Point of Contact with decision-making authority
- Provide timely data, system access, and approvals
- Attend scheduled meetings and training sessions
- Complete assigned tasks, decisions, and reviews on schedule

Failure to meet Client responsibilities may result in timeline delays or additional fees.
```

---

## SECTION 8 — EDUCATION VS. EXECUTION (When Applicable)

**Use when:** Some tasks require client execution (DNS, tracking codes, third-party portals, etc.)

```
Tasks designated as Education Only mean Quantum provides guidance and best-practice instruction
while Client performs the actual execution (e.g., DNS configuration, tracking code installation,
third-party platform connections, data entry).

Quantum is not responsible for outcomes dependent on Client execution, and delays caused by
Client inability or unwillingness to execute will not extend Quantum's timeline obligations.
```

---

## SECTION 9 — OUT OF SCOPE

**Goal:** Explicitly list what is NOT included. Always be comprehensive here.

**Standard exclusions (adapt per project):**
```
The following are explicitly excluded from this SOW unless added via written Change Order:
- Ongoing managed services, system administration, or post-onboarding support
- Custom development, API development, or webhook configuration beyond standard integrations
- Website development, DNS execution, or hosting management
- Manual data entry or historical data rebuilds
- Sales execution, marketing execution, or content creation / copywriting
- Custom Q2™ template or framework development
- Additional business units, brands, or locations beyond the primary entity
- Any deliverables marked Standard = No in Section 6
```

**Important note on seat-based fee:**
```
Client will be subject to an ongoing seat-based fee as agreed upon in the applicable Quote.
This fee is non-cancellable for as long as Client maintains the relevant platform in active use.
This is not a managed services fee — it is a product fee designed to allow Quantum to recoup
investment in up-front build, configuration, and proprietary framework development.
```

---

## SECTION 10 — CHANGE MANAGEMENT

```
All work outside the scope of this SOW requires a written Change Order agreed upon in writing
by both Parties prior to execution. Verbal agreements, email approvals, or implied scope changes
do not constitute authorization for out-of-scope work.

Quantum reserves the right to pause delivery on in-scope work pending Change Order execution
if out-of-scope requests would materially affect project timeline or resource allocation.
```

---

## SECTION 11 — FEES & PAYMENT TERMS

```
Fees for this engagement are based upon Quantum's official quote accepted by Client.

Fixed Project Fee: $[AMOUNT] (as quoted)

Overage Rate: Out-of-scope and overage work will be billed at $[RATE]/hour (default: $250/hour).

Ongoing Seat-Based Fee: Quantum charges an ongoing seat-based fee of $[AMOUNT] per HubSpot
Sales Hub seat per month (default: $50/seat). This fee:
- Is a product fee, not a managed services fee
- Is non-cancellable for the duration of Client's active HubSpot usage
- Allows Quantum to recoup investment in proprietary framework development
- Does not include ongoing services unless explicitly stated in the applicable Quote

Payment Terms: [Net 30 / Due upon invoice / Per quote terms]

Fees exclude HubSpot licensing costs, ZoomInfo licensing costs, and any third-party software fees.
```

---

## SECTION 12 — CONFIDENTIALITY

See `references/legal-boilerplate.md` for the complete confidentiality section.
This section is standard across all QBS SOWs and should be reproduced in full.

---

## SECTION 13 — LIMITATION OF LIABILITY

```
Quantum's total liability arising under or related to this SOW shall not exceed the total
fees paid by Client to Quantum under this SOW. In no event shall either Party be liable
for indirect, incidental, consequential, or punitive damages, regardless of the theory
of liability or whether such damages were foreseeable.

Quantum provides configuration and enablement services. Business results, revenue outcomes,
pipeline generation, and system performance are not guaranteed.
```

---

## SECTION 14 — FREQUENTLY ASKED QUESTIONS (FAQ)

Always include an FAQ. Adapt questions to the project type, but include these standards:

```
What does the price we paid include?
All standard deliverables and any explicitly included customization listed in this SOW.

Are hours prepaid?
No. Hours are estimates used to define maximum included scope, not entitlements or banked time.

Is ongoing support included?
No. This SOW covers [onboarding / implementation / the engagement] only. Ongoing support
requires a separate agreement.

Are business results guaranteed?
No. Quantum provides configuration and enablement, not revenue or outcome guarantees.

What happens if we need something outside this SOW?
Any out-of-scope work requires a written Change Order and will be quoted at Quantum's
standard rate of $[OVERAGE RATE]/hour.

Who owns the [Q2™ / proprietary framework / configurations] in our system?
Quantum retains all intellectual property rights to proprietary frameworks and methodologies.
Quantum reserves the right to remove proprietary assets from Client's environment in the
event of non-payment.

[Add 2-3 project-type-specific FAQs as appropriate]
```

---

## SECTION 15 — ACCEPTANCE

```
This SOW constitutes the entire agreement regarding the services described herein and
supersedes all prior discussions, representations, or understandings relating to the
subject matter hereof.

This SOW becomes effective upon execution by both Parties.

QUANTUM BUSINESS SOLUTIONS                    CLIENT: [CLIENT LEGAL NAME]

Signature: ____________________              Signature: ____________________

Name: ________________________              Name: ________________________

Title: ________________________              Title: ________________________

Date: ________________________              Date: ________________________
```

---

## EXHIBIT A — PROJECT SCHEDULE

Include a timeline table with week-by-week phases. Adapt to project type.

**Standard 8-Week HubSpot Onboarding Schedule:**

| Week | Phase | Key Activities | Quantum | Client |
|---|---|---|---|---|
| Week 1 | Kickoff & Discovery | Kickoff call, system access, data audit | Lead | Participate, provide access |
| Week 2 | Foundation Setup | CRM config, users, roles, permissions | Execute | Review & approve |
| Week 3 | Core Configuration | Pipelines, lifecycle stages, properties | Execute | Review |
| Week 4 | Q2™ Framework Deployment | Custom objects, lists, workflows | Execute | Review |
| Week 5 | Advanced Features | Sequences, dashboards, integrations | Execute | Provide data |
| Week 6 | Training & Enablement | Sales Hub training, Marketing training | Lead | Attend & complete |
| Week 7 | QA & Review | Testing, bug fixes, refinements | Execute | UAT, approvals |
| Week 8 | Go-Live | Go-live readiness review, handoff | Support | Execute go-live |

Adapt phases and weeks for other project types.
