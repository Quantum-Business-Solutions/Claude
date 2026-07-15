---
name: sow-creator
description: >
  Use this skill whenever the QBS team needs to create, draft, or generate a Statement of Work (SOW)
  for a client. Triggers include any mention of "SOW", "statement of work", "client agreement",
  "project scope document", "engagement letter", or requests like "draft a scope for [client]",
  "write up what we're doing for [client]", "create a contract for [project]", or "put together
  an SOW for [service type]". Also trigger when the user describes project details (services,
  deliverables, pricing, timeline) and wants to formalize them into a document. Always use this
  skill for HubSpot onboarding, ZoomInfo onboarding, Marketing engagements, Consulting projects,
  n8n automation, or any other QBS service agreement — even if the user doesn't explicitly say "SOW".
  Output is always a professional Word (.docx) file.
---

# QBS Statement of Work Creator

Quantum Business Solutions (QBS) SOW skill. Produces client-ready, legally protective, scope-enforcing
Statements of Work as downloadable Word (.docx) documents, matching the established QBS SOW format.

---

## Step 0 — Check for Project Information

Before doing anything, check whether the user has already provided client/project details:

- **If YES** (client name, services, deliverables, pricing mentioned): Go directly to **Step 2 — Build the SOW**.
- **If NO** (vague request like "create an SOW" with no details): Go to **Step 1 — Interview**.

---

## Step 1 — Client Interview

Read `references/interview-guide.md` and ask the user the questions for the relevant project type.
Do NOT ask all questions at once. Group them into 2-3 natural conversation rounds.

**Round 1 — Project Basics:**
1. Client company name
2. Primary contact name at client
3. Project type(s) — see service types below
4. Estimated project start date / kickoff

**Round 2 — Scope & Deliverables:**
Questions vary by project type. See `references/interview-guide.md`.

**Round 3 — Pricing & Timeline:**
1. Fixed project fee (from quote)
2. Number of HubSpot Sales Hub seats (for seat-based fee)
3. Overage rate (default: $250/hour)
4. Seat-based fee per seat (default: $50/seat/month)
5. Engagement length in weeks (default: 8 weeks for HubSpot onboarding)

---

## Step 2 — Build the SOW

### 2a. Read Reference Files

Based on the project type(s), read the appropriate references:

| Project Type | Reference Files to Read |
|---|---|
| HubSpot Implementation | `references/sow-structure.md`, `references/deliverables-library.md` (HubSpot section) |
| ZoomInfo Onboarding | `references/sow-structure.md`, `references/deliverables-library.md` (ZoomInfo section) |
| Marketing Engagement | `references/sow-structure.md`, `references/deliverables-library.md` (Marketing section) |
| Consulting / Strategy | `references/sow-structure.md`, `references/deliverables-library.md` (Consulting section) |
| n8n / Automation | `references/sow-structure.md`, `references/deliverables-library.md` (Automation section) |
| Custom Dev / Lovable | `references/sow-structure.md`, `references/deliverables-library.md` (Custom Dev section) |
| Multi-service | Read all relevant sections |

Also always read `references/legal-boilerplate.md` for the confidentiality, IP, and liability sections.

### 2b. Write the SOW Content

Follow the section order in `references/sow-structure.md` exactly. Key rules:

**Voice & Tone:**
- Authoritative, clear, protective
- Use "Quantum" for QBS and "Client" for the client throughout
- Always distinguish what IS included vs what IS NOT
- Repeat scope enforcement language — it protects both parties

**Scope Language Rules:**
- Always use "Estimated Execution Time" — never "prepaid hours" or "banked hours"
- Always note that estimated time defines scope boundaries, not entitlements
- Always include a "Common Customizations Not Included" table
- Always require a written Change Order for anything outside scope
- Call out "Standard" vs "Non-Standard" on all deliverables

**Required Sections (in order):**
1. SOW Header (title, parties, MSA reference)
2. Purpose & Overview
3. Scope of Services
4. [Framework/Product Description — if proprietary framework like Q2™ applies]
5. Project Timeline
6. Meeting Allocation & Limits
7. Deliverables & Estimated Execution Time
   - Per service area subsections
   - Deliverables table (Deliverable | Standard | Description | Est. Hours)
   - Common Customizations Not Included table
   - Estimated Execution Time Disclaimer
   - Included Scope & Pricing Confirmation
8. Responsibilities (Quantum vs. Client)
9. Education vs. Execution (when applicable)
10. Out of Scope
11. Change Management
12. Fees & Payment Terms
13. Confidentiality (full section — see legal-boilerplate.md)
14. Limitation of Liability
15. FAQ
16. Acceptance
17. Exhibit A (project schedule / timeline)

### 2c. Generate the .docx File

Use the docx skill to produce a properly formatted Word document.

```bash
# Install dependency
npm install -g docx

# Then write and execute a Node.js script that produces the .docx
```

**DOCX Formatting Standards for QBS SOWs:**
- **Page size:** US Letter (12240 x 15840 DXA), 1-inch margins
- **Font:** Arial, 12pt body
- **Heading 1:** Arial 16pt bold — major section numbers (1. PURPOSE & OVERVIEW)
- **Heading 2:** Arial 13pt bold — subsections (1.1 Framework Description)
- **Tables:** Full-width (9360 DXA), light gray header fill (#2E4057 text on #D5E8F0), single borders
- **Deliverables tables:** 4 columns — Deliverable | Standard | Description | Est. Execution Time (Hours)
- **Customizations tables:** 4 columns — Customization Area | Description | Typical Effort (Hours) | Notes
- **Bold key phrases** throughout, especially scope warnings and exclusions
- **Page numbers** in footer
- **"STATEMENT OF WORK" title** centered, bold, large (20pt) at top
- **Party block** below title: Client name, Quantum Business Solutions, date

**Output path:** `/mnt/user-data/outputs/[ClientName]_SOW_[Date].docx`

---

## Step 3 — Present & Offer Revisions

After generating:
1. Use `present_files` to deliver the .docx
2. Give a 3-4 sentence summary: what's in scope, timeline, pricing structure
3. Offer to adjust any section, add/remove deliverables, or update pricing

---

## Service Type Quick Reference

| Service | Typical Duration | Key Deliverables | Pricing Model |
|---|---|---|---|
| HubSpot Full Onboarding (Q2™) | 8 weeks | Q2 lists, custom objects, workflows, dashboards | Fixed fee + seat-based |
| HubSpot Sales Hub Only | 4–6 weeks | Pipeline, sequences, dashboards, training | Fixed fee + seat-based |
| ZoomInfo Onboarding | 2–4 weeks | Integration setup, list config, training | Fixed fee |
| Marketing Engagement | 4–12 weeks | Campaigns, forms, email, analytics | Fixed fee or retainer |
| Consulting / Strategy | 1–8 weeks | Process mapping, recommendations, roadmap | Fixed fee or hourly |
| n8n Automation | 2–6 weeks | Workflow builds, triggers, integrations | Fixed fee |
| Custom Dev / Lovable | Variable | App/tool build, QA, handoff | Fixed fee + milestones |
