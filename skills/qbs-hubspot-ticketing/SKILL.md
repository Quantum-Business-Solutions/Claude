---
name: qbs-hubspot-ticketing
description: Use this skill whenever Marko needs to log, create, import, or manage HubSpot tickets for time tracking at Quantum Business Solutions. This includes creating individual tickets or bulk batches, generating import spreadsheets, pushing tickets via the HubSpot API, correcting ticket dates/timestamps, associating tickets with companies and projects, and any task involving QBS client codes, company record IDs, project record IDs, pipeline/stage selection, billable hour tracking, or ticket category assignment. Trigger this skill whenever you see references to client 3-letter codes (like CEL, DVL, KPI, etc.), weekly meetings, BackOffice tickets, billable/non-billable time entries, or any mention of logging hours to HubSpot. Also use when troubleshooting timezone issues between Belgrade (GMT+1) and Chicago (UTC-6) for HubSpot date fields.
---

# Quantum Business Solutions — HubSpot Ticketing System Instructions

## Overview

This document describes the complete ticketing/time-tracking process used by Marko Ajder at Quantum Business Solutions (QBS). Tickets are logged in HubSpot (Hub ID: 20682069) as time entries representing work performed for clients and internal operations.

---

## Owner Information

- **Name:** Marko Ajder
- **Email:** marko@thequantumleap.business
- **HubSpot Owner ID:** 466155664
- **Location:** Belgrade, Serbia (GMT+1)
- **HubSpot Portal Timezone:** America/Chicago (UTC-6)

---

## Timezone Handling (CRITICAL)

Marko is in Serbia (GMT+1) but the HubSpot portal runs on Chicago time (UTC-6). This creates a 7-hour gap that can cause tickets to appear on the wrong day.

**Rule: Always use noon UTC (`T12:00:00.000Z`) for all date/datetime fields.**

This ensures the date lands correctly in both timezones:
- Noon UTC = 6:00 AM Chicago (same calendar day)
- Noon UTC = 1:00 PM Belgrade (same calendar day)

Using midnight UTC (`T00:00:00.000Z`) causes tickets to roll back to the previous day in Chicago time (midnight UTC = 6:00 PM previous day in Chicago).

**Applies to these fields:** `createdate`, `closed_date`, `ticket_due_date_`

**Example:** For a ticket on March 5, 2026, set all three date fields to `2026-03-05T12:00:00.000Z`

---

## Pipelines and Stages

| Pipeline | Pipeline ID (`hs_pipeline`) | Closed Stage ID (`hs_pipeline_stage`) | Use For |
|----------|---------------------------|--------------------------------------|---------|
| Support Pipeline | `0` | `4` | All client work (meetings, HubSpot work, etc.) |
| Quantum Internal Pipeline | `11057532` | `32751023` | Internal QBS operations (BackOffice, sales meetings, webinars, internal syncs) |

**Default:** All tickets are created as **Closed** unless specified otherwise.

---

## Ticket Field Mapping

### Standard Fields

| Field | HubSpot Property | Description |
|-------|-----------------|-------------|
| Ticket Name | `subject` | Format: `[CODE] - [Description]` |
| Description | `content` | Brief description of the work |
| Client | `company` | The **internal name** from the CLIENTS dropdown (note: some have leading spaces) |
| Pipeline | `hs_pipeline` | `0` (Support) or `11057532` (Internal) |
| Stage | `hs_pipeline_stage` | `4` (Closed Support) or `32751023` (Closed Internal) |
| Category | `hs_ticket_category` | See Categories section below |
| Owner | `hubspot_owner_id` | `466155664` (Marko) |
| Create Date | `createdate` | Always noon UTC: `YYYY-MM-DDT12:00:00.000Z` |
| Close Date | `closed_date` | Same as create date |
| Due Date | `ticket_due_date_` | Same as create date |

### Custom Time Fields

| Field | HubSpot Property | Description |
|-------|-----------------|-------------|
| Estimated Time | `ticket___estimated_execution_time` | Hours (decimal), always equals execution time |
| Execution Time | `ticket_execution_time` | Actual hours worked (decimal) |
| Billable Hours | `fulfillment_hours_` | For Billable tickets: same as execution time. For Non-Billable: leave **blank/empty** |
| Billable Status | `billable_` | `Billable` or `Non-Billable` |

### Associations

Each ticket is associated with:
1. **COMPANY** (always) — via company record ID
2. **PROJECT** (when applicable) — via project record ID

When using the HubSpot API (`manage_crm_objects`), associations use:
```
{"targetObjectId": <record_id>, "targetObjectType": "COMPANY"}
{"targetObjectId": <record_id>, "targetObjectType": "PROJECTS"}
```

---

## Ticket Naming Conventions

| Type | Format | Example |
|------|--------|---------|
| Weekly meeting | `[CODE] - Weekly Client Success Call MM/DD/YYYY` | `DVL - Weekly Client Success Call 03/05/2026` |
| Project meeting | `[CODE] - [Meeting description]` | `CEL - Commissions project meeting` |
| Work ticket | `[CODE] - [Task description]` | `OPT - Overhauling customer survey process` |
| Internal weekly | `QBS - Weekly Internal Client Success Call MM/DD/YYYY` | `QBS - Weekly Internal Client Success Call 03/06/2026` |
| BackOffice | `QBS - BackOffice (Client Email Support, Ticket Entry, Team Huddles)` | (Same every day) |
| Prospect meeting | `QBS - Meeting with prospect [Name] from [Company]` | `QBS - Meeting with prospect Jim Agri from Connect The Office` |

---

## Categories (hs_ticket_category)

| Display Name | Internal Value (what you send to HubSpot) |
|-------------|------------------------------------------|
| Client Meeting | `Client - Meeting` |
| Client HubSpot Support | `Client - HubSpot On-Going` |
| Client Internal Tasks | `Client - Internal Tasks` |
| Client Marketing | `Client - Marketing` |
| Client Website | `Client - Website` |
| Client ZoomInfo | `Client - ZoomInfo` |
| Client Strategic Planning | `Client - Road Map` |
| Client Misc | `Client - Misc.` |
| Client Action Item from Meeting | `Action Item from Meeting` |
| Client Saas/SBaaS Support | `Client - Sales as a Service` |
| Client Q2 | `Client - Q2` |
| Quantum Internal Operations | `Quantum Internal Operations` |
| Quantum Internal Sales | `Quantum Internal - Sales` |
| Quantum Internal Marketing | `Quantum Internal - Marketing` |
| Quantum Internal Finance | `Quantum - Finance` |

**Common usage:**
- Client meetings → `Client - Meeting`
- Client HubSpot work (development, configuration, data cleanup, etc.) → `Client - HubSpot On-Going`
- QBS BackOffice, internal syncs, webinars, HubSpot specialist meetings → `Quantum Internal Operations`
- Prospect/sales meetings → `Quantum Internal - Sales`

---

## Billable vs Non-Billable Rules

| Type | Billable? | fulfillment_hours_ |
|------|-----------|-------------------|
| Client meetings | Billable | = execution time |
| Client HubSpot work | Billable | = execution time |
| QBS BackOffice | Non-Billable | blank |
| QBS Internal syncs | Non-Billable | blank |
| QBS Internal weekly call | Non-Billable | blank |
| Prospect/sales meetings | Non-Billable | blank |
| QBS Webinars | Non-Billable | blank |
| QBS HubSpot specialist meetings | Non-Billable | blank |

**Rule:** If `billable_` = `Non-Billable`, then `fulfillment_hours_` must be **empty/blank** (not zero).

---

## Active Clients — Company Record IDs and 3-Letter Codes

| Code | Company Name | Company Record ID | Client Value (Internal Name) |
|------|-------------|-------------------|------------------------------|
| ALT | Altrum | 18153325572 | Altrum |
| AND | A.N. Deringer | 21355233123 | A.N. Derringer |
| BBM | Brandon Business Machines | 14774512560 | Brandon Business Machines |
| CCI | CCi Voice | 49404735778 | CCi Voice |
| CEL | Celerant Technology | 20647524683 | Celerant |
| CTO | Connected Office Technology | 41932322614 | Connected Office Technology |
| DCS | DCS Technologies Corp | 9364909073 | DCS Technologies |
| DOV | Dove Print Solutions | 36650994842 | Dove Technologies |
| DVL | DaVinci Laboratories | 27862292650 | DaVinci |
| EAK | Eakes Office Solutions | 7675951997 | Eakes Office Solutions |
| FIS | Fisher's Technology | 50775981182 | Fisher Technology |
| GLW | Gallaway Commercial | 37553377566 | Gallaway Commerical |
| GTS | GreenTrail Solutions | 40717246312 | GreenTrail Solutions |
| HIL | Hilyard's Business Solutions | 7552832400 | Hilyard's Business Solutions |
| IMG | Image 2000 | 17496061850 | Image 2000 |
| ITG | Imagine Technology Group | 7335058278 | Imagine Technology |
| JLO | Johnson Law Office | 21525973340 | Johnson Law Office |
| KOS | Kelly Office Solutions | 49265282105 | Kelly Office Solutions |
| KPI | Keypoint Intelligence | 39895365522 | Keypoint Intelligence |
| NBM | NBM | 9931623170 | NBM |
| NEX | Nexus Network Technologies | 49265224068 | Nexus NT |
| NLB | Next Level Business Strategies | 49740974206 | Next Level Business |
| OEM | OEM Connect | 7588299672 | OEM |
| OPT | Optima Office | 9573851690 | Optima |
| PBT | Power Business Technology | 7679276916 | Power Business Technology |
| PHC | Pilcher Hamilton Corporation | 34362206328 | Pilcher Hamilton |
| PTL | Pet Tech Labs | 27971005794 | Pet Tech |
| PUL | Pulse Technology | 7536446274 | Pulse |
| QBS | Quantum Business Solutions | 7311932261 | Quantum - Internal |
| REV | Revolution Office | 7658242624 | Revolution Office |
| SIO | Sioux Corporation | 8507272254 | Sioux Corporation |
| SMP | SMP Security | 8600659034 | SMP Security |
| SPT | Spectrum Technologies | 17654198542 | Spectrum Technologies |
| TAG | Tag Solutions | 17616090919 | TAG Solutions |
| TOM | Tascosa Office Machines | 45364485023 | Tascoso Office Machines |
| TSG | The Swenson Group | 50095418769 | Swenson |
| UTE | UTEC | 9931494545 | UTEC |
| XSE | XSE Group Inc | 28767453953 | XSE Group |

**Note on Client Values:** HubSpot's `company` field uses internal names which sometimes have a leading space and may differ from the display name. Always use the **Internal Name** exactly as shown. For example, Fisher's Technology display name is "Fishers Technology" but the internal value is `Fisher Technology`.

---

## Active Projects — Record IDs

Projects are time-bound. When a project expires, a new one is created. Always confirm which project is currently active for a client.

| Client | Project Name | Project Record ID | Notes |
|--------|-------------|-------------------|-------|
| AND | Infor to HubSpot Migration 2026 | 523954791474 | Active migration project |
| BBM | Q2 Brandon Business Machines | 527798342559 | |
| CCI | Data Cleanup | 495438275931 | Current active project (replaced Helpdesk) |
| CCI | Help Desk Build & Onboarding | 495438274564 | Completed — use Data Cleanup now |
| CEL | Q1 2026 Block of 50 Hours | 525419361954 | |
| DVL | Monthly Hours - February 2026 | 525016040069 | Feb only |
| DVL | Monthly Hours - March 2026 | 537876465553 | March onward |
| EAK | Q2 HubSpot Optimization 145 Hours | 516743899972 | |
| FIS | Q2 Marketing Hub Onboarding | 514207067490 | |
| KPI | Revenue Recognition & Project Object | 496798265608 | |
| NBM | February HubSpot Hours | 530249640627 | |
| NEX | Sales Enterprise OB, CAS, Sequences | 519213828415 | |
| NLB | Q2 HubSpot Implementation | 529053172135 | |
| OPT | HubSpot Support Q1 2026 | 525418940264 | |
| PHC | 100 hrs HubSpot Support | 504981902419 | |
| POA | 2026 Monthly Project | 513174392922 | |
| PTL | Monthly Hours - February 2026 | 525016041245 | Feb only |
| PTL | Monthly Hours - March 2026 | 537676675221 | March onward |
| QBS | AI Project | 459238884513 | Internal AI/app development |
| QBS | Weekly Internal Meetings 2026 | 521136743522 | For weekly internal calls |
| REV | 50 Hours HubSpot Support | 510384930177 | |
| SIO | Sioux Corp Project | 530710759241 | |
| TAG | TAG Solutions 01/2026 | 515293455748 | |
| TSG | Swenson Active Engagement | 516734719811 | |
| XSE | 20 Hours HubSpot Support | 512004863747 | |

**Monthly projects (DVL, PTL):** These rotate monthly. Always check which month's project to use based on the ticket date. For example, a DVL ticket in February uses `525016040069`, but March uses `537876465553`.

---

## BackOffice Ticket (Daily Mandatory)

Every workday gets a BackOffice ticket:

- **Subject:** `QBS - BackOffice (Client Email Support, Ticket Entry, Team Huddles)`
- **Description:** `Daily back office operations including client email support, ticket entry, and team huddles`
- **Pipeline:** Quantum Internal (`11057532`)
- **Stage:** Closed (`32751023`)
- **Category:** `Quantum Internal Operations`
- **Billable:** `Non-Billable`
- **Default Hours:** 2.5 hours (unless specified otherwise)
- **Company:** QBS (`7311932261`)
- **Project:** None (leave blank)

---

## Project Association Logic

- **Always associate** when the ticket clearly relates to an active project (e.g., commissions work for CEL goes to CEL Q1 project)
- **Weekly meetings** for clients with active projects → associate to their project
- **Weekly meetings** for clients without projects → company only, no project
- **Revolution Office special rule:** Weekly meetings and biweekly training calls are NOT associated to the 50hr project. Only specific project syncs, ZoomInfo meetings, and dedicated HubSpot work are project-associated.
- **CCI Voice:** Helpdesk project is completed. New project is Data Cleanup (`495438275931`). Weekly data cleanup calls go to this project. General weekly calls are not project-associated.
- **Internal QBS meetings:** Weekly internal client success call → associate to QBS Weekly Meetings project (`521136743522`). All other internal work (BackOffice, syncs) → no project.
- **When unsure:** Ask Marko before assuming.

---

## How to Submit Tickets to Marko/Claude

When providing ticket data, include:
1. **Date** (close date)
2. **Client name** (common name is fine, e.g., "DaVinci", "Fisher's", "Celerant")
3. **What the ticket is** (meeting, HubSpot work, training, etc.)
4. **Hours** (decimal format: 0.25 = 15 min, 0.5 = 30 min, 0.75 = 45 min, 1.25 = 1hr 15min)
5. **Any special context** (project-specific work, prospect meeting, etc.)

Claude/Cowork will handle all field mapping, pipeline selection, category assignment, billable status, company/project associations, and timestamp formatting.

---

## API-Specific Notes

When creating tickets via the HubSpot API (`manage_crm_objects` tool):

- **Batch creation:** Up to 10 tickets per API call
- **Date format:** ISO 8601 with noon UTC: `2026-03-05T12:00:00.000Z`
- **Associations array:** Include both COMPANY and PROJECTS (when applicable)
- **Stage values:** Use numeric IDs (`4` for Support Closed, `32751023` for Internal Closed)
- **Pipeline values:** Use string IDs (`"0"` for Support, `"11057532"` for Internal)
- **Client field quirk:** The `company` property uses the internal dropdown value, which sometimes has a leading space (e.g., ` Celerant` not `Celerant`). When using the API, the leading space should be included. When using import, it maps automatically.

---

## Import File Format

When creating .xlsx files for HubSpot import, use these column headers:

`Ticket name | Ticket Description | Client | Pipeline | Pipeline Stage | Category | Billable | Owner | Estimated Time | Execution Time | Fulfillment Hours | Create Date | Close Date | Due Date | Company Record ID | Project Record ID`

- Company Record ID and Project Record ID columns allow association during import
- Owner should be `Marko Ajder` (display name) for imports
- Pipeline should be the display name: `Support Pipeline` or `Quantum Internal Pipeline`
- Pipeline Stage should be `4` (Support Closed) or `32751023` (Internal Closed)

---

*Last updated: March 27, 2026*
