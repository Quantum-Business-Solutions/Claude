# Feature Utilization Matrix — Master Catalog

The foundational reference for feature-by-feature audit. Every HubSpot feature the skill audits is catalogued here with: tier availability, detection method, usage threshold, and scoring weight.

The matrix drives three things:
1. **What gets audited** — filtered by tier to skip features the portal doesn't license
2. **How it gets scored** — high-signal features contribute directly to dimension scores
3. **What appears in the Feature Utilization section** of the deliverable

## Feature weight classification

**Scored (high-signal).** Directly contributes to dimension score via deduction rubric. ~30 features.

**Visibility (low-signal).** Appears in the matrix for completeness but doesn't move the score. ~70 features.

**Rule of thumb:** a feature is Scored if its non-use directly costs revenue, compliance, or forecast reliability. A feature is Visibility if its non-use is a missed opportunity but not an active harm.

## Status values

For each feature, the audit produces one of:

- **In tier** (Yes / No / Unknown)
- **Configured** (Yes / Partial / No / N/A)
- **Actively used** (Yes / Partial / No / N/A) — usage evidence in last 30–90 days
- **Used well** (Yes / Partial / No / N/A) — meets the "healthy" threshold for that feature

Add a free-text **Notes** column for per-finding context (e.g., "1 call logged in 30 days against 95 emails").

---

## Sales Hub

### Scored features (contribute to Adoption / Automation / Integrations scores)

**SH-01 — HubSpot Calling (native)**
- Tier: Sales Starter+
- Detect config: check owners for `hs_calling_user_id`, call setup in settings (via settings API), provisioned numbers via /crm/v3/schemas on calls
- Detect usage: engagements (calls) count in last 30 days, group by user
- Used well: calling reps average >40 calls/week; <4 hr avg time-to-first-touch on inbound
- Weight: Critical auto-trigger if <40% of sales reps log any call in 30d

**SH-02 — Dialer integration (3rd party)**
- Tier: any (via marketplace)
- Detect config: presence of Aircall / RingCentral / Kixie / Orum / Five9 / ConnectAndSell / Dialpad / JustCall / PhoneBurner in installed apps
- Detect usage: same as SH-01 (calls logged)
- Used well: if native calling disabled AND dialer present → check dialer is the source
- Weight: counts toward SH-01 calling score (either native or 3rd party satisfies)

**SH-03 — Deal pipelines and stage design**
- Tier: Sales Starter+ (1 pipeline on Starter, multi-pipeline on Pro+)
- Detect config: `/crm/v3/pipelines/deals` — count pipelines, stages, probabilities
- Detect usage: deal distribution across stages in last 365d
- Used well: <4 pipelines, each stage has deals in last 180d, probabilities set and monotonic, explicit stalled/lost/won stages
- Weight: High (architecture dimension)

**SH-04 — Buying roles on deal-contact associations**
- Tier: Sales Pro+
- Detect config: check association labels on deal-contact associations via `/crm/v4/associations/definitions/deals/contacts`
- Detect usage: % of open deals with any non-Primary label set
- Used well: >70% of open deals above qualification have a Decision Maker
- Weight: Critical auto-trigger if <40% coverage on open deals (Data Health dimension)

**SH-05 — Sequences**
- Tier: Sales Pro+
- Detect config: `/automation/v3/sequences` list
- Detect usage: sequences with enrollments in last 90d
- Used well: >70% of active sequences have enrollments in 90d; reply rate >2%; unsubscribe rate <0.5%
- Weight: Scored (Adoption)

**SH-06 — Playbooks**
- Tier: Sales Pro+
- Detect config: `/crm/v3/objects/playbooks` or similar endpoint; count playbooks
- Detect usage: playbook views/completions in last 90d (via timeline events)
- Used well: at least 2 active playbooks, each used in 20+ deals in 90d
- Weight: Scored (Adoption)

**SH-07 — Meeting scheduler and meeting links**
- Tier: Sales Starter+
- Detect config: `/crm/v3/objects/meeting_links` or scheduler tool check
- Detect usage: meeting bookings via links in last 90d
- Used well: >50% of reps have active meeting link with bookings
- Weight: Scored (Adoption)

**SH-08 — Forecast tool**
- Tier: Sales Pro+
- Detect config: forecast submissions API (`/forecast/v1`)
- Detect usage: forecasts submitted per rep per month
- Used well: submissions monthly, accuracy measured, multi-category (Commit/Best Case/Pipeline)
- Weight: Scored (Reporting)

**SH-09 — Coaching playlists and call recording**
- Tier: Sales Pro+ (Calling required, playlists Sales Enterprise)
- Detect config: coaching tool setup; playlist count
- Detect usage: calls added to playlists; coaching notes on calls
- Used well: weekly coaching cadence with >5 calls reviewed per rep per month
- Weight: Scored (Adoption) — only if calling is active first

**SH-10 — Deal priority / deal score**
- Tier: Sales Pro+ (AI deal score is Pro)
- Detect config: `hs_priority` or `hs_deal_score` property present and populated
- Detect usage: property fill rate on open deals
- Used well: >50% of open deals have priority set
- Weight: Visibility

### Visibility features (Sales Hub)

- **SH-11 Templates** (Pro+): email templates count, templates with sends in 90d, % shared vs private
- **SH-12 Snippets** (all tiers): snippets count, snippets used in 90d
- **SH-13 Documents** (Pro+): documents uploaded, documents with engagements
- **SH-14 Quotes** (Starter+): quotes created in 90d, e-signature enabled
- **SH-15 Products / line items** (Starter+): product library count, line items on deals
- **SH-16 Custom properties on Deal** (Starter+): count, fill rate
- **SH-17 Meeting types** (Starter+): types defined, types used
- **SH-18 Goals** (Pro+): goals set, goal completion tracked
- **SH-19 Prospecting workspace** (Pro+): workspace active, daily workflow adoption
- **SH-20 AI guidance / Sales Intelligence** (Pro+): Breeze Sales Intelligence enabled, insights reviewed

---

## Marketing Hub

### Scored features

**MH-01 — Marketing emails**
- Tier: Starter+ (limited), Pro+ (A/B, automation)
- Detect config: marketing email tool; branded email templates set; sender addresses verified
- Detect usage: emails sent in last 30/90d; recent campaign cadence
- Used well: regular sending cadence, <1% unsubscribe rate, branded templates
- Weight: Scored (Adoption)

**MH-02 — Forms**
- Tier: Free+
- Detect config: `/marketing/v3/forms`; forms count; field standardization
- Detect usage: submissions per form in last 90d
- Used well: every form with submissions; forms scoped to specific campaigns/pages
- Weight: Scored (Data Health — source attribution dependency)

**MH-03 — Landing pages**
- Tier: Starter+
- Detect config: pages in content tool; page count
- Detect usage: page visits in 90d; conversions on page
- Used well: active landing pages with conversion rate >2%
- Weight: Scored (Adoption)

**MH-04 — Workflows**
- Tier: Pro+
- See Automation dimension for detail
- Weight: Scored (Automation)

**MH-05 — Lists**
- Tier: Starter+
- See Architecture dimension (list inventory check 2.17) for detail
- Weight: Scored (Architecture)

**MH-06 — Campaigns tool**
- Tier: Pro+
- Detect config: campaigns defined; assets tied to campaigns
- Detect usage: campaigns with activity in 90d
- Used well: every marketing email/landing page/social post tagged to campaign
- Weight: Scored (Reporting)

**MH-07 — Attribution reports**
- Tier: Pro+ (multi-touch Enterprise)
- Detect config: attribution reports created
- Detect usage: reports viewed; model selected
- Used well: model matches sales cycle length (multi-touch for long B2B)
- Weight: Scored (Reporting) — missing attribution is critical auto-trigger

**MH-08 — Ad accounts connected (Google / LinkedIn / Meta)**
- Tier: Pro+ for ad tracking
- Detect config: `/marketing/v3/ads/accounts` or equivalent
- Detect usage: spend tracked, conversions attributed
- Used well: all ad channels connected, attribution flowing to deals
- Weight: Scored (Integrations)

**MH-09 — Social accounts connected (LinkedIn, Facebook, Instagram, Twitter/X, YouTube)**
- Tier: Pro+
- Detect config: social account connections
- Detect usage: posts published in 30d; social inbox activity
- Used well: 3+ channels connected, consistent publishing cadence
- Weight: Scored (Integrations)

**MH-10 — Marketing Contacts configuration**
- Tier: all (impacts billing)
- Detect config: marketing contact flag on contacts
- Detect usage: marketing contact count vs tier limit
- Used well: suppression workflow in place, stale contact cleanup
- Weight: Critical auto-trigger if approaching tier ceiling

### Visibility features (Marketing Hub)

- **MH-11 Blog** (Starter+): posts in 90d, traffic trends
- **MH-12 SEO recommendations** (Pro+): recommendations addressed
- **MH-13 Custom events** (Enterprise): events defined, events firing
- **MH-14 Smart content / CTAs** (Pro+): count, personalization usage
- **MH-15 A/B testing** (Pro+): tests run in 90d
- **MH-16 Popups / banners** (Pro+): popups configured, conversion tracking
- **MH-17 Chat flows** (Starter+): flows configured, routing to reps
- **MH-18 Subscription types** (Starter+): types defined, alignment with actual sends
- **MH-19 UTM builder** (Free): consistent UTM usage, documentation
- **MH-20 Email health and sender reputation** (Starter+): deliverability score, authentication (SPF/DKIM)
- **MH-21 Segmentation (dynamic lists)** — covered in Architecture 2.17
- **MH-22 File manager** (Free+): file count, broken links
- **MH-23 Breeze Content Agent** (Pro+): content agent in use
- **MH-24 Breeze Content Remix** (Pro+): remix feature usage
- **MH-25 Marketing SMS** (add-on): configured and sending
- **MH-26 Webinars / events** (integrations): webinar tool connected

---

## Service Hub

### Scored features

**SVH-01 — Tickets and ticket pipelines**
- Tier: Free+ (tickets), Pro+ (multi-pipeline)
- Detect config: `/crm/v3/pipelines/tickets`; ticket record count
- Detect usage: tickets created in 30/90d; tickets resolved; avg time-to-resolution
- Used well: active ticket volume, consistent stage progression, SLA on Pro+
- Weight: Scored (Adoption)

**SVH-02 — SLAs**
- Tier: Pro+
- Detect config: SLA definitions per pipeline
- Detect usage: SLA breach rate; % of tickets covered by an SLA
- Used well: <10% SLA breach rate, every ticket covered
- Weight: Scored (Automation)

**SVH-03 — Knowledge base**
- Tier: Pro+
- Detect config: KB articles published
- Detect usage: article views in 30d; articles updated in 180d
- Used well: >20 articles, recency <180d, deflection metric tracked
- Weight: Scored (Adoption)

**SVH-04 — Customer portal**
- Tier: Pro+
- Detect config: portal enabled, branded
- Detect usage: portal logins / activity
- Used well: active portal with regular customer engagement
- Weight: Visibility

**SVH-05 — Feedback surveys (NPS, CSAT, CES)**
- Tier: Pro+ (NPS Starter)
- Detect config: surveys configured
- Detect usage: survey sends and response rates in 90d
- Used well: quarterly NPS, CSAT on ticket resolution, trended over time
- Weight: Scored (Reporting)

**SVH-06 — Conversations inbox**
- Tier: Starter+
- Detect config: channels connected (email, chat, forms, social)
- Detect usage: messages received and routed
- Used well: <1hr avg response time, routed to correct team
- Weight: Scored (Adoption)

### Visibility features (Service Hub)

- **SVH-07 Help desk workspace** (Pro+)
- **SVH-08 Service playbooks** (Pro+)
- **SVH-09 Service meeting links** (Starter+)
- **SVH-10 Live chat** (Starter+)
- **SVH-11 Breeze Customer Agent** (Enterprise)
- **SVH-12 Service automation / routing**
- **SVH-13 Service dashboards**
- **SVH-14 Calling for service** (same as SH-01)
- **SVH-15 Custom properties on Ticket**

---

## Operations Hub

### Scored features

**OH-01 — Data sync (two-way)**
- Tier: Starter+
- Detect config: active data sync connections (Salesforce, NetSuite, Mailchimp, etc.)
- Detect usage: sync health, error rate, record volume
- Used well: all active syncs error-free in 30d
- Weight: Scored (Integrations)

**OH-02 — Data quality automations**
- Tier: Pro+
- Detect config: data formatting workflows (phone format, capitalization, country standard)
- Detect usage: workflows running; records touched
- Used well: >5 data quality workflows covering core fields
- Weight: Scored (Data Health)

**OH-03 — Programmable automation (custom code)**
- Tier: Pro+
- Detect config: workflows with custom code action
- Detect usage: custom code actions executing
- Used well: code actions well-tested, no errors, documented
- Weight: Scored (Automation)

**OH-04 — Datasets**
- Tier: Enterprise
- Detect config: datasets created
- Detect usage: reports built on datasets
- Used well: datasets exist for cross-object reporting needs
- Weight: Scored (Reporting)

### Visibility features (Operations Hub)

- **OH-05 Webhooks** — webhooks configured, success rate
- **OH-06 Data health tools** — data health dashboard usage
- **OH-07 Field mappings** — custom mappings for integrations
- **OH-08 HubSpot AI / Breeze for Ops** — AI-assisted automations

---

## Content Hub (formerly CMS Hub)

### Scored features

**CH-01 — Website pages**
- Tier: Starter+
- Detect config: pages published
- Detect usage: page views, form conversions
- Used well: active site with regular content updates
- Weight: Scored (Adoption)

**CH-02 — Blog**
- Tier: Starter+
- Detect config: blog enabled, posts published
- Detect usage: posts in 30/90d, traffic
- Used well: consistent publishing cadence, SEO performance
- Weight: Scored (Adoption)

### Visibility features (Content Hub)

- **CH-03 Podcasts** (Pro+)
- **CH-04 Case studies / Memberships** (Enterprise)
- **CH-05 AI content generation** (Pro+)
- **CH-06 Content remix** (Pro+)
- **CH-07 Brand voice** (Pro+)
- **CH-08 Multilingual content** (Enterprise)
- **CH-09 SEO recommendations** (overlap with MH-12)
- **CH-10 Design manager / HubL templates**

---

## Commerce Hub

### Scored features (if Commerce is in tier)

**CMH-01 — Invoices**
- Detect config: invoice tool enabled, branding set
- Detect usage: invoices created / paid in 30d
- Weight: Scored if Commerce licensed

**CMH-02 — Payments / Stripe**
- Detect config: payment processor connected
- Detect usage: payments processed
- Weight: Scored if Commerce licensed

**CMH-03 — Subscriptions**
- Detect config: subscription products
- Detect usage: active subscriptions, MRR
- Weight: Scored if Commerce licensed

### Visibility features (Commerce Hub)

- **CMH-04 Quotes** (overlap with SH-14)
- **CMH-05 Products / line items** (overlap with SH-15)
- **CMH-06 Payment links**
- **CMH-07 Revenue tracking**

---

## Breeze / AI (cross-hub)

### Scored features

**BR-01 — Breeze Copilot**
- Tier: all (basic), Pro+ (full)
- Detect config: Copilot enabled
- Detect usage: usage events / chat sessions
- Used well: regular use across the team
- Weight: Scored (Adoption) — AI adoption signal

**BR-02 — Breeze Prospecting Agent**
- Tier: Sales Pro+
- Detect config: agent configured, target accounts set
- Detect usage: prospects generated and worked
- Used well: prospects created, accepted, moved to opportunity
- Weight: Scored (Adoption)

**BR-03 — Fit Score (AI lead fit)**
- Tier: Marketing Pro+
- Detect config: fit score enabled
- Detect usage: scores generated; workflows keyed off score
- Used well: correlation with win rate validated quarterly
- Weight: Scored (Reporting)

**BR-04 — Engagement Score**
- Tier: Marketing Pro+
- Detect config/usage: similar to Fit Score
- Weight: Scored (Reporting)

**BR-05 — Predictive lead scoring**
- Tier: Enterprise
- Detect config: predictive score configured
- Detect usage: scores populated; thresholds set for action
- Weight: Scored (Reporting)

### Visibility features (Breeze / AI)

- **BR-06 Breeze Content Agent** (overlap with MH-23)
- **BR-07 Breeze Customer Agent** (overlap with SVH-11)
- **BR-08 Breeze Knowledge Base Agent**
- **BR-09 AI meeting summarization** (Zoom AI Companion / native)
- **BR-10 ChatSpot / Breeze Chat** (inline assistant)

---

## Detection method index

Quick reference for which `HubSpotAuditClient` method handles which features:

| Feature category | Helper method |
|---|---|
| Pipelines, stages | `list_pipelines(object_type)` |
| Custom properties, fill rates | `list_properties`, `property_fill_rate` |
| Workflows | `list_all_workflows` |
| Lists | `list_all_lists` |
| Owners, users | `list_all_owners`, `list_active_users` |
| Engagement activity | `engagement_activity_by_user` |
| Buying roles | `open_deals_buying_role_coverage` |
| Forms | `list_all_forms` |
| Sequences | *NEW — `list_sequences()` to be added* |
| Playbooks | *NEW — `list_playbooks()` to be added* |
| Calling config | *NEW — `get_calling_config()` to be added* |
| Forecast | *NEW — `get_forecast_submissions()` to be added* |
| Meeting links | *NEW — `list_meeting_links()` to be added* |
| Marketing emails | *NEW — `list_marketing_emails()` to be added* |
| Ad accounts | *NEW — `list_ad_accounts()` to be added* |
| Social accounts | *NEW — `list_social_accounts()` to be added* |
| Campaigns | *NEW — `list_campaigns()` to be added* |
| Tickets, SLA | *NEW — extend pipelines for tickets* |
| Knowledge base | *NEW — `list_kb_articles()` to be added* |
| Feedback surveys | *NEW — `list_feedback_surveys()` to be added* |
| Data sync | *NEW — `list_data_sync_connections()` to be added* |
| Integration inventory | *NEW — `list_installed_apps()` to be added* |
| Custom objects | `list_custom_object_schemas` |

## Audit flow

1. **Phase 1 (scoping):** detect tier per hub
2. **Phase 2 (tier-aware filtering):** build the applicable feature set based on tier
3. **Phase 2.5 (feature utilization pass):** run detection + usage checks for each applicable feature
4. **Phase 3+ (dimension audits):** use feature matrix results to calibrate findings and scoring
5. **Scoring:** apply rubric where each scored feature contributes to the relevant dimension
6. **Deliverable:** surface the full matrix by hub; locked features in Appendix E

## Locked features handling

For features *not* in the portal's tier:

- Don't include in the main matrix (keeps focus on actionable)
- Summarize in an Appendix E: Locked Features subsection
- For each locked feature: "Available on [tier] — typical value unlock: [brief]"
- Purpose: give leadership visibility into upgrade opportunities without cluttering the main deliverable
