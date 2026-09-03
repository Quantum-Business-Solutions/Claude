# Praxera blog — FAQ authoring for the 30 posts that had none (2026-09-03)

## Why

The Praxera blog template renders a `PL - FAQ` section on every post. 42 of
the 75 posts had real Q&As written; 30 had none, so the module fell back to
its field default and published three literal placeholders:

> Question goes here? Answer goes here. (×3)

This was live on 29 published posts. It was not caused by the 2026-08-29
widget-deletion incident — but it is ours, not inherited: the originals in
the DaVinci PL blog have zero FAQ items too, and their old template had no
FAQ module, so they render clean. The FAQ section arrived with our rebrand
template and exposed the gap publicly.

Checked before writing anything: all 30 matching originals in the DaVinci PL
blog also have zero FAQ items, so nothing was lost in the clone. The content
simply had never been written.

## What was written

3 Q&As per post, 90 total, grounded in each article's own headings and body
rather than generic filler. Client asked for 3 per page (the existing 42
carry 6-8; that difference is deliberate, not an oversight).

Structure copies the existing 42 exactly — same module path, same
`section_headline`, `max_width` 820, sizes 32/17/15, `#f7f7f6` background,
80px padding, answers wrapped in `<p>`.

Copy lives in `content/praxera_faqs.json` so it can be reviewed or reused
without reading it back out of the portal.

## Compliance

`tools/faq_lint.py` encodes the client's standing rules and was run before
anything was written to the portal. **0 blocking violations.**

Blocked patterns include: any first-person manufacturing or facility claim,
Praxera described as manufacturing or formulating, custom formulation
offered as a Praxera service, other-brand mentions (DaVinci, VetriScience,
PetTech), legacy product trademark names, and disease claims.

Per Mindy: Praxera must never be marketed as manufacturing — "I don't want
us ever marketing that we manufacture" — but "manufactured in the U.S." and
"manufactured in a cGMP facility" are approved, "because that's all true".
The copy uses only the approved forms, and always about a supplier or
facility, never about Praxera.

4 non-blocking warnings, all on `custom-supplements-vs.-private-label-supplements`
— the post whose subject *is* custom formulation. The copy describes it as an
industry concept and never as something Praxera offers.

## Verification

Post-change, across all 75 posts:

- 0 posts left without FAQ items, 0 placeholder strings stored
- 0 `deleted_at` flags
- 0 collateral changes — every non-FAQ widget byte-identical to `before.json`,
  no publish_date drift, no state drift (the draft stayed a draft)
- every other blog untouched: DaVinci (534), DaVinci PL (75), Pet Tech Labs
  (67), VetriScience (243 + 1), Protocol Guide (5), Learning Center (1)
- live sweep of all 71 published posts: **0 pages showing "Question goes
  here"**, all 29 new FAQ sets confirmed rendering

## Open

Copy is client-facing and should still get a Tammy/Mindy read. It is
compliant by the rules we hold, but they own final wording.

Separately noted, not touched: a few posts carry legacy product trademark
names in their body copy (Tri-Mag 300, DIMPRO, Collagen Bright, Mega
Probiotics, Mito-Fuel and others) and one references 2024 in a 2026-titled
post. Pre-existing body-copy issues, out of scope here.
