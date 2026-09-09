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
| app       | 23,663 | Google Fonts link + stylesheet + `<div id="root">` |
| data1–4   | 71,787 | row islands (`script.rowdata`), 270 rows |
| metadata  |  9,505 | `#meta` — title, groups, link templates, interned labels/types, share URL |
| boot      | 28,235 | the app (minified from `src/signoff.js`) — must stay LAST |

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

## ClientCommand side (merged to main 9 Sep: 478fec7, 36376b8, 83027fa)

PortalDocumentViewer: full-screen overlay + button, `whoami` identity message, `download` hand-off,
taller frame for interactive pages; PortalDocumentPage: 1800px width for interactive pages.
83027fa fixes a real data-loss bug: the host kept ONE pending save for all keys, so two keys saved
inside 600 ms (a group + the activity log) lost the first. Saves are now coalesced per key.

## v2.1 design pass (9 Sep, afternoon)

Stylesheet moved to `src/signoff.css` (review.css is left for the older artifact ledger). Real
typefaces (Newsreader / IBM Plex) via a Google Fonts link in the app section; stat tiles and a
segmented progress bar in the header; sticky group nav carrying the save indicator; frozen first two
columns (checkbox + asset); drag-to-resize column handles in the table header (per viewer, in memory);
each table scrolls inside its own box (max 78 vh) with a sticky header row, so the horizontal
scrollbar is always reachable; two-column detail panel (comments | findings + history), pinned so
it never scrolls off with the wide table. Approval buttons are no longer disabled before a side is
picked — clicking one jumps to the "Who are you?" bar and highlights it. The Full screen button
only appears once the host answers `whoami` (new ClientCommand viewer build).

## v2.2 (9 Sep, evening) — revisions, global notes, Excel, compact

Rev 1 / Rev 2 / Rev 3 ticks per row (seeded from Melinda's Design Approval Sheet v6: 34 ✓, TY Sell
Sheets "NEED INFO", Ingredient Sourcing "In Progress"); Global notes & rules section (pseudo row
`GEN`, key `assets:general`) seeded from `reference/general_comments.json`; 50 seeded page comments
from HubSpot + the sheet, with Justin's replies; double-click inline editing of name/type/note/detail;
fold icons on every section; formatted XLSX export (xlsx-js-style, 7 sheets, CSV fallback); compact
density so the sheet fits the window; live "old asset" link in the redirect column.

## v2.3 (9 Sep, late morning ET) — history, resolved counts, true originals, QA pass

- **Blank page fix.** data2–4 were still the 13:44 build while metadata's interned label table had
  been replaced, so indices pointed past the table and the app threw before rendering. Re-uploaded
  all three. The build now seeds its label/type tables from the last deployed metadata, so a rebuild
  only changes the sections whose bytes actually changed (upload metadata first — it is a superset).
- **"Redirects from at cutover" now shows the real public DaVinci URLs** from
  `reference/compare_pairs.json`, mapped to today's slugs through `snapshots/v1-pre-promotion`
  (the v1 `pl-demo` pages are the same HubSpot records as today's Praxera pages, re-slugged; the
  `-v3` pages were QBS working copies, now archived — neither was ever public). 13 pages have
  originals (about ×3, ty-consultation ×3, how-to-sell ×2, definitive-guide-ty ×2 …); 50 are new
  pages — chip "nothing redirects here". Finding: `reference/redirects.json` (the 134-row cutover
  table) still lists the v3 URLs as sources for pages and needs the same correction before the 301s
  are configured.
- **8 Sep call + Patrick's 9 Sep email seeded**: 10 new global notes (® on Daily Best, Women's Health
  subheader standard, Developed-by-Us block, approved copy source for placeholder subheaders, sticky
  nav, Regulatory one-week window, email reply-to/footer rules, Definitive Guide passages stay,
  Patrick's MVP list) and 19 page-level items (fitness ×3, aging, gummies, home "and more",
  how-to-sell numbers/icons, definitive-guide, dropshipping unpublish, 9 placeholder category pages).
- **Activity is now the first section**, open by default, newest first, latest 10 with "Show all";
  the counter reads "N actions · everyone, every change". History is rebuilt from the saved stamps
  (approvals, revs, comments, replies, resolves, edits, adds, deletes, cleared chips) merged with the
  log, so nothing is missing even if a log write was ever lost (Shawn's 15:49–15:56 actions were).
- **Resolved / Open comments tiles** in the header (8 tiles). Resolved comments show a ✓ Resolved
  pill, strike-through, and "resolved by <name> <time>".
- **Make global** on any row comment copies it into Global notes as "[From <row> — <author>] …" and
  marks the source "In Global notes".
- **Collapse all / Expand all** in the sticky bar. Double-clicking a link no longer opens an editor.
- **Saves are serialised** (one state:set in flight, next on `saved` ack or 2.5 s), belt-and-braces
  with the host fix.
- QA harness `scratchpad/qa.js`: identity → approve → comment → resolve → make global → reload as
  the client → client approve → reload with the log key deleted → collapse/expand. 22 checks pass
  against the stored page. Two-user merge (`run2.js`) passes.
- Sizes: app 29,254 · data1 29,910 · data2 28,300 · data3 11,163 · data4 12,318 · metadata 18,251 ·
  boot 41,405.

Open: screenshot attachments on comments (needs a host upload path — page state is capped at
256 KB per key), Hindsight retain, rotate the PAT and Fal key pasted in chat.
