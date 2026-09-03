# Barb is editing the Praxera drafts live — do not write to these pages

Found 3 September 2026, ~14:43 UTC, while verifying whether Custom Formulation
was still on the pages.

## What is happening

Every one of the 63 Praxera drafts carries an edit dated 3 September, all by
`barb@thequantumleap.business` (HubSpot user `51139136`). The most recent was
14:42:49, one minute before the scan that found it.

She is sweeping Custom Formulation out of the page copy. Revision history for
two sample pages:

| page | time | mentions before | after |
|---|---|---|---|
| `sleep` | 2 Sep 22:00 -> 3 Sep 13:28 | 4 | 2 |
| `faq` | 2 Sep 22:00 -> 3 Sep 14:24 | 6 | 3 |

Measured live, the total fell from **24 mentions across 11 pages at 14:16** to
**22 across 9 pages at 14:43**. `testing` and `ingredient-sourcing` cleared inside
that window.

## Why it matters

`PATCH /cms/v3/pages/site-pages/{id}/draft` replaces the draft buffer. It does not
detect that someone has the page open in the editor and it does not warn. If we
write to a page Barb is working in, whichever save lands last silently discards the
other. With eight manufacturing rewrites queued against `home`, `about`,
`certifications`, `chewables` and `ty-consultation`, that is a live collision risk.

**Hold all writes to Praxera pages until Barb's pass is finished.** Confirm with her
whether the sweep covers only Custom Formulation or also the first-person
manufacturing claims.

## A correction to an earlier note

`MINDY_REVIEW_INSTANCES.md` and the 2 September findings describe the category-page
sweep in the past tense. It is not finished; it is in progress today. Any count of
Custom Formulation or manufacturing mentions taken before Barb stops is stale on
arrival, including the "23 sentences" figure currently on the ClientCommand
`praxera-launch-status` page.

## Method note

Page-level `updatedAt` was not enough to establish this: a first `GET` of a draft can
itself move the timestamp, so a fresh date is not proof of a human edit. The proof came
from `GET /cms/v3/pages/site-pages/{id}/revisions`, where each revision carries
`object.updatedById` and the full page body, so the mention count can be compared
revision to revision. Use revisions, not `updatedAt`, to answer "did someone change this".
