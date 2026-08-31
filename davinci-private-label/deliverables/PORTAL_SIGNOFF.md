# Praxera Asset Sign-off — portal page

Portal: DaVinci Labs Portal (`6d797a44-e010-410f-b532-64ac42627d64`)
Page:   slug `praxera-asset-signoff`, id `94f31f00-08a7-4f9c-905e-fe4a5e6b8c7d`
Live:   client-visible since 31 Aug 2026

## Why the portal and not a Claude artifact

An artifact needs a Claude account to open, and its state never reaches
ClientCommand -- 272 approvals would have been unrecoverable. The portal page
writes into `portal_document_state`, which the team can read back.

## Page shape

Six sections, in order. The renderer wraps each in `<section id="KEY">` and
injects `<h2>{label}</h2>` as its first child, so the stylesheet carries
`section>h2:first-child{display:none}` to suppress all six headings.

| block_key | chars  | what it is                              |
|-----------|--------|-----------------------------------------|
| app       | 10,502 | stylesheet + `<div id="root">`          |
| data1     |  8,772 | row island: pages, first blog posts     |
| data2     | 22,460 | row island: blog posts                  |
| data3     |  9,682 | row island: last post, emails           |
| data4     | 10,639 | row island: emails, forms, workflows    |
| boot      | 14,243 | `<script id="meta">` + the application  |

`boot` must stay last: it reads `#meta`, every `script.rowdata` island and
`#root`, all of which are earlier in the document.

The page was created with `allow_scripts: true`. `upsert_document_section`
does not reset page-level flags, so section edits keep it.

## Stored bytes differ from the emitted chunk, and that is correct

The store decodes `\uXXXX` escapes: `…` (6 chars) lands as `…` (1).
Every delta between `signoff_chunks.json` and the stored `body_chars` is
exactly 5 per escape -- data2 68 ellipses = 340, data3 2 = 10, data4 13 = 65,
data1 6 = 30. JSON semantics are unchanged, so the islands still parse.

## State model

One `state_key` per asset group -- `assets:website-pages`, `assets:blog-posts`,
`assets:emails`, `assets:forms`, `assets:workflows`.

The bridge row is shared, not per-viewer (`UNIQUE (document_id, state_key)`),
and attributed per ROW via `auth.uid()`. Partitioning by group means two
reviewers working different groups cannot overwrite each other; inside a group
last-write-wins still applies, which the page says out loud. Because
attribution is per row and not per item, each decision carries its own
reviewer name in the value.

localStorage is NOT a fallback here: the portal iframe has no
allow-same-origin, so touching it throws, and a try/catch hides that as a
save that never happened.
