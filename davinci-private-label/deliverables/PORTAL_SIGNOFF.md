# Praxera Asset Sign-off — portal page (v2, 9 Sep 2026)

Portal: DaVinci Labs Portal (`6d797a44-e010-410f-b532-64ac42627d64`)
Page:   slug `praxera-asset-signoff`, id `94f31f00-08a7-4f9c-905e-fe4a5e6b8c7d`
Team:   https://clientcommand.thequantumleap.business/pages/94f31f00-08a7-4f9c-905e-fe4a5e6b8c7d
Client share link (no login): https://clientcommand.thequantumleap.business/portal/2a5c361066202d71fa47ee598d2bcb95/pages/94f31f00-08a7-4f9c-905e-fe4a5e6b8c7d

## What v2 does (built for Shawn's asks of 9 Sep)

- **Two approvals per item**: QBS ✓ (build) and Client ✓ (content), each stamped with who and when.
  Needs work clears both. Fully approved = both ticks.
- **Who you are**: when the ClientCommand host is on the new viewer build, the page knows the
  signed-in user and their side (team / client) and only enables that side's button. Until then,
  and always on the share link, the reviewer types a name and picks "I am QBS" / "I am the client".
- **Comments are first-class**: each comment has Reply and Resolve/Reopen; resolved comments show who
  resolved and when. 32 client comments are pre-loaded — 4 notes from Melinda's Design Approval Sheet
  v6 and 28 HubSpot in-editor comments (Melinda, Sarah) — and can be replied to or resolved.
- **Editable**: Edit any row (name, type, live link, HubSpot link, detail, note), Add a row per
  group, Remove (two-step) and Restore. Findings chips can be cleared with ×.
- **Links**: Live ↗ for every page and post, HubSpot ↗ (editor) for every page, post, email, form and
  workflow.
- **Findings with detail**: open a row to see *where* — the DaVinci URLs linked, the exact
  first-person production phrases, the placeholder text. Scan re-run 9 Sep (`verify_content.py`).
- **Multi-select + bulk**: tick rows (or select-all shown) → QBS approve / Client approve / Needs work /
  Clear / Remove. Filters: status, type, search across names, notes, findings and comments.
- **Activity log**: every action recorded (who, side, what, when); per-item history in the thread.
- **Shared-doc behaviour**: facts carry timestamps and merge item-by-item; the page re-reads the
  portal every 25 s and reads-before-it-writes, so two people working at once keep both changes.
- **CSV**: Download CSV (needs the new viewer build; otherwise the CSV text is shown to copy).
- **Full screen**: button posts to the host (new viewer build) — the host also has its own button.

## Page shape (7 sections)

| block_key | chars  | what it is |
|-----------|--------|------------|
| app       | 17,814 | stylesheet + `<div id="root">` |
| data1–4   | 71,787 | row islands (`script.rowdata`), 270 rows |
| meta      |  9,505 | `#meta` — title, groups, link templates, interned labels/types, share URL |
| boot      | 25,599 | the app (minified from `src/signoff.js`) — must stay LAST |

Rows: 63 pages (61 paired + top-10-products, learning/ty-ingredients-testing, ty-contact),
72 posts (3 deleted Amazon duplicates dropped), 111 emails, 12 forms, 12 workflows. Two pages that
were deliberately deleted (custom-formulation, alp/ads-custom) are no longer rows.
Not rows on purpose: pl-module-library, pl-global-blocks (internal reference pages), a stray
temporary-slug blog draft.

## State (portal_document_state)

`assets:website-pages|blog-posts|emails|forms|workflows` — `{itemId:{q,c,f,cm[],sr{}}}`
(`q`/`c`/`f` = `{by,at}` or `{by,at,x:1}` when cleared; `cm` = comments; `sr` = replies/resolution
on seeded comments). `assets:edits` — `{mod,add,del,chips}` per group. `assets:log` — `{e:[…]}`,
capped at 800 entries. Size cap per key 256 KB (checked client-side at 250 KB).

## Rebuild

```
python3 tools/build_signoff_v2.py        # reads reference/*.json, writes chunks + preview
```
then `upsert_document_section` × 7 (boot last). Verify with `list_document_sections` body_chars
against the build's printed sizes; render locally with the mock host in the scratchpad
(`host.html` + `run.js`, Playwright + bundled Chromium) before pushing.

## ClientCommand side (branch `claude/signoff-viewer-fullscreen`, not yet merged)

PortalDocumentViewer: full-screen overlay + button, `whoami` identity message, `download` hand-off,
taller frame for interactive pages; PortalDocumentPage: 1800px width for interactive pages.
Until merged, the page works but: no full screen, no auto identity (type your name), CSV shows as
text to copy.
