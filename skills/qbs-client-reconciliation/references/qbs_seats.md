# QBS Seat IDs

These are the HubSpot user IDs that map to QBS staff. Use these for attribution checks in Phase 3.

## Known QBS seats

Note: `createdById` on portal artifacts (properties, lists, workflows, records) uses the HubSpot user ID. This is NOT the same as the owner ID — user IDs come back from the API as the `createdById` on creation metadata.

| QBS Staff Member | Owner ID (QBS portal 20682069) | Role |
|---|---|---|
| Shawn Peterson | 103243559 | Principal / decision-maker |
| Marko Ajder | 466155664 | Primary implementer (HubSpot builds) |
| Patrick Dodge | 316713255 | Client success / account owner |
| Barb Peterson | 390820388 | Implementation support |

## Mapping QBS owner IDs to client-portal user IDs

QBS staff have DIFFERENT user IDs in each client's HubSpot portal (every portal issues its own user IDs when QBS is invited as a collaborator). The IDs above are the owner IDs in QBS's own portal (20682069).

To verify attribution in a CLIENT portal:

1. Pull the list of users in the client portal:
   ```bash
   curl -H "Authorization: Bearer $HS_TOKEN" \
     "https://api.hubapi.com/crm/v3/owners?limit=100" | jq '.results[] | {id, email, firstName, lastName}'
   ```
2. Find the entries whose emails match QBS domains:
   - `@thequantumleap.business`
   - `@quantumbusinesssolutions.com`
   - Known personal emails on file
3. Cache the client-specific user IDs for this engagement

Alternatively, inspect a known QBS-built artifact's `createdById` field and match by first/last name via the owners endpoint.

## The "mystery seat" case

Sometimes an artifact's `createdById` resolves to a user ID that isn't QBS staff and isn't a current client employee. This can mean:

- **Former client employee** — person has left but their user record persists
- **Integration seat** — automated integrations (Zapier, Make, HubSpot AI) create artifacts under their own seat
- **HubSpot Bot / System** — some changes are attributed to HubSpot itself
- **Former QBS contractor** — someone who worked on the portal in a prior engagement

When you hit a mystery seat:

1. Resolve the user details via the owners API
2. If it matches a known integration email (e.g., `zapier-integration@...`) → treat as QBS work if the integration was set up by QBS, client work otherwise
3. If it's a historical user → timestamp-check. If created within QBS engagement window, probably still QBS-built by a former contractor. If pre-engagement, client legacy.
4. Flag the artifact in the report as "attribution uncertain, verify with Shawn"

Never close a ticket on an uncertain attribution — these need a human decision.

## Future: Teams

If QBS adds more staff (or loses some), update this file. The skill should never hardcode specific IDs — always pull the current owner list from the QBS portal and match by email domain.

Simplest refresh pattern:

```bash
# From QBS portal
curl -H "Authorization: Bearer $QBS_TOKEN" \
  "https://api.hubapi.com/crm/v3/owners?limit=100" | \
  jq '.results[] | select(.email | test("@thequantumleap\\.business|@quantumbusinesssolutions\\.com")) | {id, email, firstName, lastName}'
```
