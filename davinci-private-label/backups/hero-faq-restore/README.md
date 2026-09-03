# Praxera blog — hero / FAQ widget restore (2026-09-03)

## What was broken

On 2026-08-29 between 18:09 and 18:14 UTC a single bulk operation set a
`deleted_at` timestamp on per-post module overrides in the Praxera
Supplements Blog (content group `220598739286`). 43 of the 75 posts were
hit; the remaining 32 were untouched.

Per affected post the flagged widgets were `hero`, `faq` (where present)
and `disclaimer`, all carrying the *same* timestamp — one operation per
post, not three. This lines up with Justin's report that a theme change
reset his earlier QA work.

A widget carrying `deleted_at` is ignored at render time and HubSpot falls
back to the module's field defaults. The visible symptoms were:

| widget     | posts | live symptom |
|------------|-------|--------------|
| hero       | 42    | H1 replaced by the module default "Your brand. Our formulations.", byline and CTA gone |
| faq        | 22    | real Q&As replaced by 3× "Question goes here? / Answer goes here." |
| disclaimer | 43    | none — `PL - Global FDA Disclaimer` is a global module, identical output either way |

## The fix

Setting `deleted_at` to `None` via `PUT /content/api/v2/blog-posts/{id}`
removes the key entirely; the override is then honoured again. Published
posts were then republished with `publish-action: schedule-publish`, which
preserves the existing `publish_date`.

Gotcha worth remembering: **CDN propagation runs several minutes behind the
publish.** A live check immediately after publishing shows the old page and
looks like the fix failed. `published_at` on the API object is the reliable
signal that the write landed.

Scripts: `/tmp/hero_scan.py`, `/tmp/hero_fix.py`, `/tmp/liveqa.py`.

## Scope and verification

Files here:
- `before.json` — full widget JSON of all 43 posts prior to the change
- `control-clean-32.json` — widget hashes of the 32 untouched posts
- `live-qa.json` — post-change live sweep of all 71 published posts

Pre-change QA established that the 32 clean posts render correctly and that
the disclaimer is a global module, so restoring its flag is a no-op.

Post-change QA:

- 75 posts still present; 0 `deleted_at` flags remain anywhere in the blog
- 0 `publish_date` drift, 0 state drift — the 4 drafts stayed drafts
- 0 widget-body drift against `before.json`; the 32 control posts hash
  byte-identical, so nothing but the flag changed
- every other blog untouched: DaVinci (534), DaVinci PL (75), Pet Tech Labs
  (67), VetriScience (243 + 1), Protocol Guide (5), Learning Center (1) —
  no post in any of them updated during the work window
- live sweep of all 71 published posts: 0 fallback H1s, all 19 published
  formerly-broken FAQs rendering their real questions

## Still open — pre-existing, NOT caused by this change

29 published posts render 3× "Question goes here?" because they have no FAQ
content at all. The cause is the `items` field in
`Private Label/Modules/PL - FAQ.module/fields.json`, which ships a default
of three placeholder Q&As (`occurrence.default: 3`). Any render without an
override picks them up.

This also affected clean posts before this work, so it is independent of the
2026-08-29 incident. The count was ~51 before this restore and is 29 now.

Fix is a two-line theme change — empty the `items` default and set
`occurrence.default` to 0. `module.html` already guards the list with
`{% if module.items %}`, though the section wrapper and headline would still
render, so the guard should be moved to wrap the whole module. Held pending
sign-off: a theme edit is what caused the incident above, and no page
legitimately wants the placeholder text.
