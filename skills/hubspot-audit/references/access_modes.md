# Access Modes: MCP vs. Private App Token (Service Key)

The skill supports two ways to reach a HubSpot portal. Most audits use both.

## The two modes

### Mode 1: HubSpot MCP

The connected HubSpot MCP server. Claude calls tools like `HubSpot:search_crm_objects`, `HubSpot:get_properties`, etc. directly. Authentication is handled by the user's MCP connection — no token needed.

**Best for:**
- Interactive lookups ("find this one company," "show me this deal's associations")
- User details, organization details, seat info
- Property definitions
- Ad-hoc small sample queries
- Phase 1 scope detection

**Limits:**
- Response size caps — large result sets truncate
- No direct access to workflows, lists inventory, engagement aggregations, audit logs
- Rate-throttled for interactive, not bulk
- Best for <1000 records per operation

### Mode 2: Private App Token (a.k.a. Service Key)

A read-only token created in the client's HubSpot portal (Settings → Integrations → Private Apps). The user provides it to the skill, which uses it to hit the HubSpot REST API directly via Python. Also called a "service key" by some teams — same thing.

**Best for:**
- Full workflow inventory (names, JSON, enrollment counts, error state, last-run)
- Full lists inventory with dependency mapping
- Property fill rate across the full record base
- Engagement aggregations (calls per user per month, etc.)
- Audit log / timeline history
- Anything that needs to page through 10K+ records
- Export-style queries

**Limits:**
- Requires the client to grant a token — adds a step
- Daily API call limits by tier (Starter 250K/day, Pro 500K/day, Enterprise 1M/day)
- Some scopes (audit log) require Enterprise
- Not all objects available to all tiers

## Which mode for which checks

Rough mapping — consult each dimension reference for details:

| Check area | Recommended mode |
|------------|------------------|
| Portal profile (hubs, tiers, seats) | MCP |
| Property inventory and definitions | MCP for definitions; Private App for fill rates at scale |
| Duplicate detection (contact, company) | Private App (needs full base) |
| Lifecycle stage completeness at scale | Private App |
| Attribution source null rates | Private App |
| Workflow inventory, errors, orphans | Private App (MCP can't reach workflow inventory) |
| List inventory with dependencies | Private App |
| Engagement activity aggregation per user | Private App |
| Sequence metrics | Private App |
| Buying role completeness on open deals | Private App (needs to enumerate open deals + their contact associations) |
| ICP fill rate on active customers | Private App |
| Target Accounts configuration | Private App |
| Dashboard and report inventory | Private App |
| Form inventory | Private App |
| User last-login inventory | Private App |
| Audit log (who built what when) | Private App (Enterprise only) |
| Integration inventory | Partial — MCP surfaces some; Private App covers installed apps listing |

## Decision tree for a given audit

**Starting any audit:**
1. Always start with MCP for Phase 1 scope detection — quick, no setup, establishes tier and portal shape
2. After Phase 1, ask: "Do we have a Private App token for this portal, or should we create one?"
3. If yes, switch to Private App for the volume-heavy checks in Phases 3–6
4. If no, run the audit in MCP-only mode and flag which checks couldn't run at full depth

**For QBS internal portals:** Always use Private App. QBS should maintain its own Private App tokens across client portals as part of standard engagement setup.

**For client portals during discovery / pre-engagement:** Use MCP only. Flag the gaps in the deliverable as "additional depth available post-engagement." This is a legitimate scoping motion — the MCP-only audit surfaces enough to recommend an engagement; the Private App audit happens as Week 1 of the engagement.

**For a portal where the client just gave us a token:** Use Private App for everything except interactive clarifications (which MCP handles fine).

## Creating a Private App Token (client instructions)

When you need a token from a client, here's the instruction set to give them:

```
1. In HubSpot, go to Settings (gear icon, top right)
2. Integrations → Private Apps → Create a private app
3. Name it something like "QBS Audit — Read Only"
4. On the "Scopes" tab, grant the following READ scopes (no write):
   - crm.objects.contacts.read
   - crm.objects.companies.read
   - crm.objects.deals.read
   - crm.objects.line_items.read
   - crm.objects.quotes.read
   - crm.objects.custom.read
   - crm.schemas.custom.read
   - crm.objects.owners.read
   - crm.lists.read
   - tickets
   - automation (read workflows)
   - forms
   - forms-uploaded-files
   - sales-email-read
   - conversations.read
   - reports
   - files
   - timeline (engagements)
   - settings.users.read
   - settings.users.teams.read
   - e-commerce (if Commerce Hub)
   - marketing-email (if Marketing Hub)
5. Click "Create app"
6. Copy the access token on the confirmation screen — you won't see it again
7. Send the token to QBS via secure channel (1Password, etc.) — NOT email
```

## Security and handling

**Never log, echo, or save a Private App token in:**
- Claude conversation logs (redact if accidentally shown)
- Internal QBS Slack (use 1Password)
- Git commits
- Plain-text files
- Client deliverables (even in methodology appendices)

**Within the audit run:**
- Take the token as a parameter to the Python helper
- Never include it in output the user sees
- Treat expired/revoked tokens as an error, not a prompt to re-request — ask the user to provide a new one

**Token lifecycle:**
- QBS should rotate audit tokens quarterly
- Tokens should be revoked at engagement end or when the responsible QBS person leaves
- For one-off audits (discovery), revoke the token within 48 hours of audit completion
- Document every active token in a QBS-internal registry (portal name, creation date, created by, last used, scheduled revocation)

## Using the Python helper

The skill includes `scripts/hs_client.py` — a reusable client for audit-volume queries. Usage:

```python
from hs_client import HubSpotAuditClient

hs = HubSpotAuditClient(token="pat-na1-...")

# Workflow inventory
workflows = hs.list_all_workflows()

# List inventory with dependency map
lists = hs.list_all_lists_with_dependencies()

# Property fill rate
fill = hs.property_fill_rate(object_type="contacts", property_name="lifecyclestage")

# Engagement activity per user, last 30 days
activity = hs.engagement_activity_by_user(since_days=30)

# Open deals with buying role completeness check
deal_roles = hs.open_deals_buying_role_coverage(min_deal_amount=10000)
```

See `scripts/hs_client.py` docstrings for the full method list.

## Common failure modes

**"Invalid token" error:** Token revoked, expired, or incorrect. Ask the user to regenerate.

**"Missing scope" error:** Token doesn't have the scope the check requires. Tell the user which scope is needed; they can edit the Private App and add it without creating a new token.

**Rate limit (HTTP 429):** Back off per the `Retry-After` header. The client handles this automatically with exponential backoff.

**Daily limit exceeded:** Portal hit its daily API ceiling. Pause the audit and resume tomorrow, or escalate to HubSpot for a temporary increase.

**Partial-access portal:** Token has some scopes but not others. Run what you can; in the deliverable's Appendix A (Methodology), explicitly list which checks were skipped and why.
