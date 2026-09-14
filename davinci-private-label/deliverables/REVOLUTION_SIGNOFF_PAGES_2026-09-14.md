# Revolution Office sign-off — the pages are now acceptable, not just the revisions

**14 Sep 2026 · portal `b483aef1…` · sheet `revolution-website-signoff`**

## What was wrong

The sheet was only usable for the change requests. Every one of the 34 HOME-xxx rows had a Live
link and a HubSpot editor link, all 32 live ones marked Implemented ✓ and waiting on Tom. But the
rows for the pages themselves had **no links at all**:

| Group | Rows | Had a Live link | Had an editor link |
|---|---|---|---|
| Change requests | 34 | 34 | 34 |
| Website pages | 29 | **0** | **0** |
| Landing pages | 15 | **0** | **0** |
| Global elements | 3 | **0** | **0** |

So Tom could verify a revision, but he could not accept a page — there was nothing to open. The
sheet's own global note already promised otherwise: *"Every row's Live link opens the page there;
the HubSpot link opens it in the editor."*

## What was done

Read Revolution's own HubSpot (portal 47019673, via their stored credential — `exists: true`,
`will_fallback_to_qbs_global: false`, so no risk of reading QBS's portal by mistake) and matched
every row to its real page:

- 29 site pages → **29 of 29 rows matched**, no page on the sheet missing from HubSpot and none in
  HubSpot missing from the sheet
- 15 landing pages → **15 of 15 matched**
- 3 global elements → Header and Footer point at the home page where they are seen; Insights
  points at the blog listing (`/blog`, blog id 182771230361) and its post manager

Every row now carries a Live link to the draft site and a HubSpot link to the editor. Nothing was
guessed: each `hubspot_url` uses the page id returned by their API.

## Nothing else moved

`add_signoff_rows` edits in place rather than rebuilding the sheet, and a before/after diff of
every row confirms it:

```
totals before: 79 assets, 33 qbs_approved, 0 client_approved, 51 open_comments
totals after : 79 assets, 33 qbs_approved, 0 client_approved, 51 open_comments
rows lost: none      status changes: none
QBS marks altered: none      comment counts changed: none
added: []   changed: 47
```

`added` is empty, so no row was duplicated. The activity log still ends at Shawn's 10 September
entries — this did not write history.

## Still open on this sheet

- **44 pages and 15 landing pages are QBS-unreviewed.** The links now exist, but nobody at QBS has
  marked Implemented ✓ on a page row, so Tom has nothing to verify against on the page side yet.
  That is a work item, not a defect.
- **Global elements**: Footer and Insights are still unreviewed; Header / Navigation is the only
  one QBS has marked.
- Tom has a real portal account, so the who-is-reviewing box only appears if he uses the
  no-login share link rather than signing in.
