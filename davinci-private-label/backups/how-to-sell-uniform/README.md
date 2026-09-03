# The step sections on /how-to-sell-supplements

Mindy, via Shawn: the five steps look different from each other instead of uniform.

## What was actually wrong

There are **six** step sections, not five, and they were numbered:

    STEP 01, STEP 02, STEP 03, STEP 04, STEP 06, STEP 07

**There was no step 05**, and the sequence ran to 07 for six steps. Beyond the numbering,
three of them broke the pattern:

| Row | Was | Others |
|---|---|---|
| STEP 04 SOURCE | navy `#012638`, light text | white, dark text |
| STEP 04 SOURCE | eyebrow `STEP 04 / SOURCE` with a slash | no slash |
| STEP 07 MEASURE | grey `#F7F7F6` | white |

## Fixed

Renumbered 01 to 06 in sequence, slash removed, all six on white with dark text. Published.

## Not fixed - needs a design decision

**Step 04 is a different module.** The other five are `218940115771`, a centred text block
(eyebrow, headline, subhead). Step 04 is `218939846527`, an image-and-text split with
`image`, `image_side`, `ratio` and `content`.

It now shares the others' colours, so it reads far closer, but it is structurally a different
layout and always will be until someone decides between:

- converting it to the plain section header, which **loses its image**, or
- accepting it as deliberate emphasis - it is the "source from us" step, i.e. the pitch.

That is a content call, so it was left as is.

## Also spotted

A rich-text block on the page contains a hardcoded `STEP 05` in body copy. The section
eyebrows are now correct, but that inline reference should be checked against the new
numbering.
