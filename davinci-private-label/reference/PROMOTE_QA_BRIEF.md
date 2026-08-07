# QA brief — in-place promotions (DaVinci Labs portal 4087538)

## Auth
```bash
export TOKEN="<HubSpot private app token for portal 4087538 — do not commit>"
```

## ⛔ READ-ONLY TASK
Make **zero** write calls. GET only. No PATCH/POST/PUT/DELETE against any page, module, or
source-code path. If something needs changing, report it — do not do it.

## What happened

Each rebuilt page previously lived on a **separate** V3 page with a `-v3` slug, leaving the
original V1 page untouched. That would have required slug surgery later, so the finished V3 body
was **promoted onto the original V1 page record**, keeping its id, name and slug.

Two PATCHes per page:
1. `templatePath` → `Private Label/Templates/Page - DND.html`, and `layoutSections` set to a
   verbatim copy of the V3 page's `layoutSections`.
2. `widgetContainers` → `{"main_content":{"widgets":[],"deleted_at":1786126404643}}` — the legacy
   flexible-column container is retired so the editor doesn't see two competing structures.
   That combination previously froze the HubSpot editor.

All seven pages passed an automated gate harness (`scratchpad/promote/promote.py`). **Do not treat
those gates as proof.** They were written by the same person who did the promotion, and three of
their early versions produced false failures. Your job is independent verification.

## Page map

| Page | Promoted V1 record | V3 source | slug |
|---|---|---|---|
| Capsules  | 216186379314 | 218936720462 | `pl-demo-capsules` |
| Liquids   | 216188835866 | 218946510259 | `pl-demo-liquids` |
| Powders   | 216192983382 | 218946510230 | `pl-demo-powders` |
| Soft Gels | 216192983363 | 218946632248 | `pl-demo-soft-gels` |
| Tablets   | 216192983343 | 218946510195 | `pl-demo-tablets` |
| Gummies   | 216192983401 | 218946510174 | `pl-demo-gummies` |
| Home      | 216189433405 | 218936720512 | `en/pl-demo-pillar` |

## Files

| Thing | Path (under `scratchpad/`) |
|---|---|
| Pre-promotion snapshot (rollback point) | `promote/<V1_ID>.PRE.json` |
| Post-promotion state | `promote/<V1_ID>.POST.json` |
| V3 source state | `promote/<V3_ID>.V3.json` |
| June pristine V1 snapshot | `backup_v1/<V1_ID>.json` |
| Pre-promotion re-snapshot of all pages | `backup_v1_2026-08-07/<V1_ID>.json` |
| Measured V1 style values | `STYLE_SPEC.md` |
| Icon inventory | `icon_map.json` |
| The gate harness (read it, audit it) | `promote/promote.py` |

Preview URL for any page:
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.hubapi.com/content/api/v2/pages/<PAGE_ID>" \
  | python3 -c "import sys,json;p=json.load(sys.stdin);print(p['slug'],p['preview_key'])"
# → https://info.davincilabs.com/<slug>?hs_preview=<key>-<PAGE_ID>
```

## Context you need

- **Nothing in the Private Label site is published.** Every page is DRAFT. Confirm this still
  holds — a page that became published is a blocker.
- **The `PRE.json` snapshots are not pure rich text.** Three widgets (indices 12, 14, 16 on the
  dosage pages) are already global blocks — `type:"module"` with `module_id` 218942529660 /
  218944099153 / 218942529652 — and their `body.html` is empty **by design**. Their copy comes
  from the global module at render time. To reconstruct V1's original text for those three, fall
  back to `backup_v1/<id>.json`, which predates that migration. Empty bodies there are NOT loss.
- Several module CSS/field changes shipped shortly before the promotions: Stat Band gained
  `icon_badge`/`icon_badge_color` (56×56 `#c9dbe2`, radius 12, margin `0 0 18px`) and moved to
  card padding 32×26, description 14px `#555`, label letter-spacing 1px; Card Grid moved to body
  15px, `--title-heading` 19px, boxed body padding 34×30, header max-width 900px, and gained an
  `icon_style` field with a `ring` option (72px white circle, 3px accent border); Section Header
  moved to h2 34px, gained `max_width`, and caps its centred subhead at 760px; Tile Grid gained
  `max_width`, `label_size`, `row_gap`, `image_radius`, plus `accent_glyph`/`sublabel`/`tile_bg`/
  `tile_text_color` for V1's "+ AND MORE" tiles. Judge styling against `STYLE_SPEC.md` and the V1
  markup — **not** against older QA reports, which predate these.
- **Known and accepted, do NOT report as new defects:** brand green `#6BA644` fails WCAG AA on
  light backgrounds (inherited verbatim from V1); the Guide Offer global block's image and alt
  text are wrong and are being fixed by hand in HubSpot's global content editor; `[BRAND_TBD]`
  appears in draft `htmlTitle` portal-wide; all 12 global-header links are `href=""`;
  pre-existing V1 link rot to `/pl-demo-*` and `/private-label-*` pages that were never built.

## Report back

A findings table, then a prioritised list. For each finding give severity
(blocker / major / minor / info), the evidence (exact strings, values, URLs, HTTP codes), and the
suggested fix. **Separate regressions introduced by the promotion from pre-existing issues**, and
show how you determined which — e.g. by checking an untouched sibling page.

End with an explicit statement of what you could NOT verify.
