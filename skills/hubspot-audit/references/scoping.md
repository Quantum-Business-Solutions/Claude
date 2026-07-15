# Phase 1: Scope Detection

Before any audit work, establish the Portal Profile. Every downstream threshold is calibrated against this.

**Access mode:** Phase 1 is the one phase that always uses MCP, because it's interactive and lightweight. After Phase 1 completes, decide whether to continue in MCP-only mode or switch to the Private App token helper for volume queries — see `references/access_modes.md`.

## Required data points

Use the HubSpot MCP tools to fetch each of the following. If a tool fails for a given portal (permission issue, tier restriction), note it but continue — do not abort the audit.

### A. Hubs and tiers

Use `HubSpot:get_user_details` and `HubSpot:get_organization_details` to determine:

- Which hubs are active: Sales, Marketing, Service, Ops, Content, Commerce
- Tier for each: Free, Starter, Professional, Enterprise
- Seat allocation per hub
- Account admin structure

**Why this matters:** A "Professional" Marketing portal has workflows but not datasets. An "Enterprise" Ops Hub has custom code actions and hierarchical teams. Mis-scoping findings to the wrong tier is the fastest way to lose client credibility.

### B. User and seat inventory

Use `HubSpot:search_owners` and `HubSpot:get_organization_details` to fetch:

- Total seats purchased per hub
- Active vs. deactivated users
- Team structure (flat vs. hierarchical; Enterprise feature)
- Super admin count (flag if >5 for security review)
- SSO status if discoverable

### C. Object model inventory

For each standard object (Contact, Company, Deal, Ticket, Line Item, Product, Quote, Feedback Submission, Call, Email, Meeting, Note, Task):

- Total record count
- Records created in last 90 days
- Records created in last 365 days
- Records last modified in last 30 days (activity signal)

Then enumerate **custom objects**: name, record count, and associations. For dealer-channel portals specifically, check for:

- `service_contract` or `contract` custom object
- `equipment` or `device` custom object (copiers, MFPs, hardware)
- `meter_read` or `meter` custom object
- `parts_order` or `supply_order` custom object
- `location` or `site` custom object

Their presence is a strong signal the portal is actively used for dealer ops vs. just marketing.

### D. Property inventory

Use `HubSpot:get_properties` for each major object (Contact, Company, Deal, Ticket). Capture:

- Total property count
- Count of custom (not HubSpot-default) properties
- Properties with `fillPercent` data if available

Store this for Dimension 2 (Architecture) — specifically for the property-sprawl check.

### E. Portal age and trajectory

- Portal creation date (`get_organization_details`)
- Contact/Deal creation volume by month for the last 12 months (from sampling)
- Identify growth pattern: steady, spiky, decelerating, or dormant

### F. Connected integrations

Enumerate installed marketplace apps and native integrations. For each, capture:

- App name
- Install date if available
- Active/inactive status
- Whether it has write access to CRM objects

Store this for Dimension 5 (Integrations) — especially for dual-write conflict detection.

## Sampling strategy

For portals exceeding these thresholds, use stratified sampling rather than full enumeration:

| Object | Full audit threshold | Sample approach above threshold |
|--------|----------------------|---------------------------------|
| Contacts | ≤50,000 | 2,000 records stratified by lifecycle stage (equal bucket size); 500 random from last 90d |
| Companies | ≤10,000 | 1,000 records stratified by lifecycle stage |
| Deals | ≤5,000 | All open deals + 500 random closed from last 365d |
| Tickets | ≤5,000 | All open + 500 random closed from last 180d |
| Engagements | N/A | Last 30 days only |

For very large portals (Shawn has audited 154K+ contact portals), stratify by:

1. Lifecycle stage bucket
2. Marketing contact status
3. Creation year (old records rot differently than new ones)

Pull ~500 per stratum. Note the sampling method in the appendix.

## Portal Profile template

Produce this structured output before proceeding to Phase 2:

```yaml
portal_profile:
  hub_id: <id>
  name: <company name>
  created: <YYYY-MM-DD>
  age_years: <number>
  
  hubs:
    sales: { tier: Enterprise, seats: 25, active_users: 18 }
    marketing: { tier: Professional, seats: N/A, contact_tier: 10000 }
    service: { tier: Professional, seats: 10, active_users: 8 }
    ops: { tier: Starter, seats: N/A }
    content: { tier: Professional }
    commerce: { tier: none }
  
  objects:
    contacts: { total: 154230, last_90d: 8420, last_30d_activity: 12500 }
    companies: { total: 64250, last_90d: 980 }
    deals: { total: 4120, open: 340, closed_365d: 1800 }
    tickets: { total: 2400 }
    custom_objects:
      - { name: service_contract, total: 2150 }
      - { name: equipment, total: 8900 }
  
  properties:
    contact: { total: 287, custom: 184 }
    company: { total: 156, custom: 98 }
    deal: { total: 94, custom: 52 }
  
  integrations:
    - { name: Zoom, active: true, writes_engagements: true }
    - { name: Read AI, active: true, writes_engagements: true }  # dual-write risk!
    - { name: LinkedIn Sales Nav, active: true }
    - { name: ZoomInfo, active: true }
  
  dealer_channel_signals:
    has_service_contracts: true
    has_equipment_object: true
    has_meter_reads: false
  
  sampling_applied: true
  sampling_notes: "Contacts stratified by lifecycle stage, 2000 records sampled"
```

This profile is referenced throughout the audit. Update it if new information surfaces during dimension audits.
