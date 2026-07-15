---
name: qbs-zoominfo-property-deployer
description: Deploy the full QBS standard ZoomInfo property set (81 properties: 42 contact + 39 company) into any HubSpot client portal via PAT. Use this skill whenever a client gets ZoomInfo, whenever setting up a new HubSpot portal that will integrate with ZoomInfo, or whenever someone asks to "create ZoomInfo properties", "set up ZoomInfo fields", "deploy ZoomInfo to HubSpot", "add ZoomInfo properties", or "map ZoomInfo to HubSpot". Covers the full enrichment property set (no intent signal properties — those are handled separately). Always use this skill before configuring the ZoomInfo ↔ HubSpot native integration field mapping. Requires a valid client HubSpot PAT (pat-na1-... or pat-na2-... or pat-eu1-...) and the qbs-hubspot-private-app skill for portal verification.
---

# QBS ZoomInfo Property Deployer

Deploys the full QBS standard ZoomInfo enrichment property set into a client HubSpot portal. Matches the Sierra Structures / PacTec reference build exactly — 42 contact properties + 39 company properties = 81 total.

**Does NOT deploy intent signal properties.** Intent properties (zi_*_intent_signal_score etc.) are client-specific and handled separately based on the client's configured ZoomInfo intent topics.

## Prerequisites

1. Valid client PAT already verified via `qbs-hubspot-private-app` skill
2. Portal ID confirmed (not QBS portal 20682069)
3. TOKEN exported as `$CLIENT_HUBSPOT_TOKEN` in the bash environment

If the PAT hasn't been verified yet, run the verify step first:
```bash
python3 -c "
import requests, os
token = os.environ['CLIENT_HUBSPOT_TOKEN']
r = requests.get('https://api.hubapi.com/account-info/v3/details', headers={'Authorization': f'Bearer {token}'})
d = r.json()
print(f'Portal ID: {d.get(\"portalId\")} | DC: {d.get(\"dataCenter\")} | Type: {d.get(\"accountType\")}')
"
```

## Deployment Steps

### Step 1 — Check what already exists
```bash
bash /home/claude/qbs-zoominfo-property-deployer/scripts/check_existing.sh
```
Prints counts of existing ZoomInfo properties on contacts and companies. Any `[EXISTS]` results during deploy are safe — idempotent.

### Step 2 — Deploy
```bash
python3 /home/claude/qbs-zoominfo-property-deployer/scripts/deploy.py
```
Creates all 81 properties. Skips any that already exist (409 = safe). Reports final counts.

### Step 3 — Verify parity
```bash
python3 /home/claude/qbs-zoominfo-property-deployer/scripts/verify_parity.py
```
Checks Astor/Sierra parity — confirms 42/42 contact and 39/39 company.

## Property Groups

ZoomInfo properties land in these HubSpot groups:
- `zoominfo` — created automatically if missing (most ZI properties)
- `contactinformation` — `management_level`, `person_linkedin_url` (standard contact group)
- `companyinformation` — `company_zoominfo_url` (standard company group)

## What's in the full set

See `references/property-list.md` for the complete 81-property inventory with internal names, labels, types, and group assignments.

## After deployment

Once properties are created:
1. Go to ZoomInfo → Integrations → HubSpot → Field Mapping
2. Map each ZoomInfo field to its corresponding HubSpot property
3. Enable suppression sync (protects credit allocation)
4. Test with a single export before enabling automated workflows

## Notes

- `zoominfo_workflow_name` exists on BOTH contacts and companies — this is intentional
- `management_level` and `zoominfo_management_level` are both created — ZoomInfo native integration uses `zoominfo_management_level`; `management_level` is a legacy field some clients use
- Revenue range and employee range are string fields (not numbers) — ZoomInfo pushes ranges like "$10M-$50M" not raw numbers
- All date fields use HubSpot `date` type with `date` fieldType
