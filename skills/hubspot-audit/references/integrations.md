# Dimension 5: Integrations

Assesses app marketplace and native integration health. Most integration problems are silent and compound over time.

## Checks to run

### 5.1 Integration inventory

**Query:** List all installed apps and native integrations from Phase 1 scoping. For each:

- Active / Inactive / Errored status
- Install date (age)
- Last data sync timestamp
- Write access to which objects
- User who installed (ownership)

### 5.2 Dual-write conflicts (engagement sources)

**CRITICAL CHECK** — this is the Zoom + Read AI pattern Shawn has fixed before.

**Query:** Enumerate integrations that write to the `engagements` API (meetings, calls, notes). Common culprits:

- Zoom + Read AI (both log meetings)
- Gong + Chorus
- Zoom + Gong
- Otter.ai + Fireflies + native meeting tool
- Outreach/Salesloft + HubSpot native email logging
- Multiple dialer integrations (Aircall, RingCentral, Kixie)

**Finding:** If two or more integrations write to the same engagement type without explicit de-dupe logic, flag as critical. Recommend standardizing on one source (Shawn's pattern: Zoom AI Companion as single source, disable Read AI CRM write).

**Impact:** Doubled activity counts inflate rep metrics. Doubled meeting notes confuse search. Doubled notifications to reps.

### 5.3 Disconnected apps still referenced

**Query:** Apps with authentication errors, disconnected status, or expired tokens — but with workflows or forms still referencing their data.

**Finding:** Silent breakage. Fix = either reconnect or remove references.

### 5.4 API call volume and health

**Query:** If accessible via organization-level API, check:
- Daily API calls vs. tier limit
- Apps hitting rate limits
- Failed API calls spike

**Threshold:** API usage >70% of daily limit is a flag; >90% is critical.

### 5.5 Contact creation source attribution

**Query:** Count contacts created in last 90 days by integration source (`hs_object_source_label`).

**Finding:** If one integration is creating 40%+ of contacts, that's your attribution dependency. If the integration has data quality issues (garbage names, bad emails), those flow directly into contact data.

### 5.6 Form-to-CRM integrations

**Query:** Non-HubSpot forms (marketing automation from a prior system, third-party chat tools, etc.) feeding CRM. For each:

- Mapping completeness (all fields land in expected properties)
- Duplicate creation risk
- Source attribution preserved

### 5.7 Email integration (Gmail / Outlook)

**Query:** Users with connected inbox integration, users without. Logging preferences per user.

**Findings:**
- Users without integration are creating email blind spots
- Users with "log all" when they should have "log selected" are polluting records with personal emails

### 5.8 Calendar integration

**Query:** Users with calendar sync. Meeting types created, meeting types with bookings.

**Finding:** Users without calendar sync have meeting tool disabled — adoption gap feeds back to Dimension 3.

### 5.9 Data sync integrations (Ops Hub)

If Ops Hub:
- Two-way syncs active (Salesforce, NetSuite, Mailchimp, HubSpot-to-HubSpot)
- Sync errors and volume
- Bidirectional field conflict resolution rules

### 5.10 Payment / e-commerce integrations

If applicable (Commerce Hub, Stripe, Shopify, etc.):
- Order sync status
- Refund/cancellation sync
- Customer record deduplication with CRM contacts

### 5.11 Zoom AI Companion configuration

Given Shawn's standardization on Zoom AI Companion:

- Is AI Companion enabled for the account?
- Are summaries being auto-logged to HubSpot engagement records?
- Is the association to contact/deal happening correctly?
- Is any other meeting transcription tool still writing (see 5.2)?

### 5.12 Webhook integrations

**Query:** Custom webhooks and private apps.

**Findings:**
- Private apps with overbroad scopes (admin permission when read-only would do)
- Webhooks with high failure rates
- Webhooks pointing at URLs owned by no one (former employee's ngrok tunnel)

### 5.13 Marketing tool integrations

- LinkedIn Sales Navigator: connected? syncing InMail activity?
- Facebook / Google Ads: connected, attribution flowing?
- SEMrush / SEO tools: if connected, used?
- ZoomInfo: enrichment rules, Webhook setup, duplicate handling

### 5.14 Sales engagement tool integrations

- Orum / ConnectAndSell / Drop Cowboy: calls logging correctly?
- Chorus: meeting integration — does it conflict with Zoom (see 5.2)?
- Outreach / Salesloft: email logging, sequence conflict with HubSpot sequences?

### 5.15 Per-user engagement capture coverage

**Critical check** — this one is often missed because standard integration audits look portal-level, not per-user.

**Query:** Build a coverage matrix for every active sales/service user. For each user, check whether each engagement-source tool is connected:

| Tool | Why it matters | Applies to |
|------|---------------|------------|
| Inbox (Gmail or Outlook) | Emails auto-logged | All reps |
| Calendar (Google or Microsoft) | Meetings auto-created from invites | All reps |
| Meeting scheduler (HubSpot Meetings) | Prospects can self-book; meeting tool usage | All reps |
| Dialer (HubSpot Calling OR Aircall/RingCentral/Kixie/Orum) | Calls captured with recordings and dispositions | Reps who call |
| Meeting transcription (Zoom AI Companion, Gong, Chorus) | Call/meeting notes auto-logged | Reps who run meetings |
| LinkedIn Sales Navigator | InMail and connection activity visible | Outbound reps, AEs |
| Video messaging (Loom, Vidyard) | Video touches tracked | Reps who send video |
| Mobile app | Field activity capture | Field/territory reps |

Produce a per-user coverage score (integrations connected ÷ integrations expected for their role). Then aggregate:

- % of reps with **full coverage** (all role-appropriate tools connected)
- % of reps missing **inbox** (critical — creates email blind spot)
- % of reps missing **calendar** (critical — creates meeting blind spot)
- % of reps missing **dialer** (critical for calling roles — creates call blind spot; ties to Adoption 3.15)
- Specific users with 0 engagement sources connected (rep fully off-platform)

**Thresholds:**
- Healthy: >90% of reps at full role-appropriate coverage; 0 reps with zero tools connected
- Flag: 70–90% full coverage; any rep missing inbox or calendar
- Critical: <70% full coverage, OR any rep missing inbox/calendar, OR calling reps missing dialer integration (ties directly to the Call Black Hole finding)

**Impact:** Every missing integration per user = a specific type of engagement that isn't flowing to the CRM for that person. A BDR without a dialer has invisible calls. An AE without calendar sync has invisible meetings. An outbound rep without LinkedIn Sales Nav has invisible InMail. The gaps are specific and quantifiable: "7 of 18 sales reps are missing dialer integration; their calls are not captured in engagement records, which makes coaching, forecasting, and activity-based reporting unreliable for 39% of the sales team."

**Recommendation:** Per-user remediation checklist in the deliverable appendix, grouped by rep role. Include this matrix as a table so the client can assign it to their ops team.

## Dealer-channel-specific checks

- **ECI / e-automate integration:** if present, field mapping health
- **ConnectWise / Autotask (managed IT PSA) integration:** ticket sync, customer sync, bidirectional conflict
- **Printer fleet management tools (Printanista, PrintFleet, FMAudit):** if syncing, meter-read accuracy
- **QuoteWerks / ConnectBooster / other quoting tools:** line item and deal sync

## Output format

```yaml
- id: integrations_02_dual_engagement_logging
  dimension: integrations
  severity: critical
  title: "Zoom and Read AI both logging meetings, creating duplicate engagements"
  evidence: "Meeting engagements in last 30 days: 1,240 from Zoom, 1,180 from Read AI. ~950 are same-meeting duplicates based on attendee + timestamp match."
  impact: "Rep activity metrics inflated ~45%. Deal timelines show duplicate entries. Engagement reports unreliable. Likely contributing to the notification fatigue reported in Dimension 3."
  recommendation: "Standardize on Zoom AI Companion as single source of truth. Disable Read AI CRM write integration OR set Read AI to notes-only with no engagement create. Backfill-cleanup script to remove existing Read AI engagements older than retention window."
  effort: hours
  tier_requirement: none
```
