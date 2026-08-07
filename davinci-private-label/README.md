# DaVinci Labs — Private Label rebuild (HubSpot portal 4087538)

Rollback and reference material for the Private Label module rebuild. Committed because the
working copies lived only in an ephemeral session scratchpad, and these snapshots are the entire
recovery path for seven customer-approved pages.

**Nothing in the Private Label site is published.** Every page is DRAFT. None of this is live.

## What happened

The Private Label pages were originally 63 pages of hand-written rich text — one giant HTML blob
per section, not editable in any structured way and not reusable. They were rebuilt as HubSpot
drag-and-drop pages built from ~50 purpose-built `PL - *` modules, matching the V1 visual design
numerically (see `reference/STYLE_SPEC.md`).

Each rebuild first lived on a separate `-v3` page. Those were then **promoted in place** onto the
original page records, so each page kept its id, name and slug and no slug surgery was needed.

## Promotion mechanics

Two PATCHes per page:

1. `templatePath` → `Private Label/Templates/Page - DND.html`, `layoutSections` ← the V3 body
2. `widgetContainers` → `{"main_content":{"widgets":[],"deleted_at":1786126404643}}`

Step 2 matters: a page with **both** `layoutSections` and a populated `widgetContainers` freezes
the HubSpot editor. The tombstone retires the legacy flexible-column container.

## Pages promoted

| Page | Record id | slug | modules |
|---|---|---|---|
| Capsules  | 216186379314 | `pl-demo-capsules`  | 17 |
| Liquids   | 216188835866 | `pl-demo-liquids`   | 17 |
| Powders   | 216192983382 | `pl-demo-powders`   | 17 |
| Soft Gels | 216192983363 | `pl-demo-soft-gels` | 17 |
| Tablets   | 216192983343 | `pl-demo-tablets`   | 17 |
| Gummies   | 216192983401 | `pl-demo-gummies`   | 17 |
| Home      | 216189433405 | `en/pl-demo-pillar` | 21 |

## Directories

| Path | What it is |
|---|---|
| `snapshots/v1-june/` | Original pristine V1 pages, all 63. Predates the global-block migration, so it is the only place the three global-block widgets' original copy survives. |
| `snapshots/v1-pre-promotion/` | Re-snapshot of every page taken immediately before the promotions. |
| `snapshots/promoted/` | Per page: `<id>.PRE.json` (state before promotion — **the rollback point**), `<id>.POST.json` (state after), `<v3id>.V3.json` (the source body). |
| `tools/promote.py` | The gated promotion harness. |
| `reference/STYLE_SPEC.md` | V1 style values measured from the original markup. |
| `reference/icon_map.json` | Which icons belong on which page, in order. |
| `reference/promotion-map.json` | V3 → V1 id/slug mapping. |
| `reference/PROMOTE_QA_BRIEF.md` | Brief given to the QA agents. |

## To roll a page back

```bash
export TOKEN="<HubSpot private app token for portal 4087538>"
python3 - <<'PY'
import json, urllib.request, os
pid = "216186379314"                       # the page to restore
pre = json.load(open(f"snapshots/promoted/{pid}.PRE.json"))
body = {"templatePath": pre["templatePath"],
        "layoutSections": pre.get("layoutSections") or {},
        "widgetContainers": pre["widgetContainers"]}
r = urllib.request.Request(
    f"https://api.hubapi.com/cms/v3/pages/site-pages/{pid}",
    data=json.dumps(body).encode(), method="PATCH",
    headers={"Authorization": "Bearer " + os.environ["TOKEN"],
             "Content-Type": "application/json"})
print(urllib.request.urlopen(r).status)
PY
```

## Verifying a page without changing it

```bash
export TOKEN="..."
python3 tools/promote.py <V3_ID> <V1_ID> --verify-only
```

Exit 0 means every gate passed. Run it against a deliberately mismatched pair first — it should
exit 1. The gates cover structure, identity, draft state, render integrity and content loss.
**They do not cover visual properties** — colours, button styles, font sizes and image geometry
are not gated, and real regressions in those were caught by review rather than by the harness.

## Known open items

- The `PL - Global Guide Offer` block's image and alt text are wrong (`PL-Bottle-50-years`, a
  filename used as alt). Lives in global content, editable only in the HubSpot UI.
- `[BRAND_TBD]` appears in draft `htmlTitle` portal-wide, pending brand lock.
- All 12 global-header links are `href=""` — template-level.
- Pre-existing V1 link rot to `/pl-demo-*` and `/private-label-*` pages that were never built.
- `&amp;amp;` stored raw in some plain-text module fields (renders correctly, looks wrong in the
  editor sidebar).
- Card Grid section headlines render 32px where V1 used 34px.
- Decorative icons carry `alt` text duplicating the adjacent heading; should be `alt=""`.
