# Praxera Blog Fix — Execution Safety Plan

**Date:** 2026-09-27
**Scope:** The confirmed, in-scope findings in the live tracker (https://claude.ai/artifact/1baexHiPfD2Tmdird2Birx) — currently 45 grammar/copy fixes verified still-live against Kenzie's 36-post review, 1 theme-level fix, plus 5 house-style rulings and 3 earlier policy decisions still open.
**Goal:** Get through the backlog without breaking anything that currently works, and without re-applying a fix someone (Kenzie/Jelena's team) has already made by hand.

## What's explicitly out of scope (per Shawn's rule)

- Any link, image, or reference that was **already broken on the original DaVinci blog**. We alert on these (tracked as `flagged_external`), we don't fix them. Only `healthcenter.uga.edu` confirmed pre-existing so far — everything else we checked was confirmed **migration-caused** (worked on DaVinci, broken now) and is fair game.
- Kenzie's "REWRITE-tier" items (full sentence restructures) and her text-size/color design notes — these need individual judgment, not a find-replace, and are a later pass.
- Anything outside Kenzie's 36 reviewed posts or the master QA crawl — we're not going looking for new problems mid-execution.

## Sequencing (why this order)

1. **House-style rulings first (5 questions, tracker Phase 0).** Blind find-replace on "wrong→right" pairs risks fighting Kenzie's own team if they're mid-edit on the same sentence, and risks applying a style nobody actually confirmed (e.g. hyphenating "private-label" everywhere if Shawn actually wants it unhyphenated). One click per question in the tracker records the ruling; nothing gets touched live until that's answered.
2. **Phase 1 — theme fix (FAQ heading → real `<h2>`).** Zero content risk: one file, one theme, fixes the broken `#faq` anchor on all 65 posts with an FAQ at once. Do this before anything else since it's the highest-leverage, lowest-risk item outstanding.
3. **Phase 2 — the 45 confirmed mechanical/grammar fixes.** Small batches (see below), each one individually verified immediately before writing.
4. **Style-conforming edits**, once #1 lands — apply the ruled style consistently across the affected posts (same small-batch pattern).
5. **Phase 3 — blocked items** (custom-formulation posts, "guarantee" wording) — wait for the 3 original Phase-0 decisions before touching these.
6. **Phase 4 — link color cleanup.** Lowest priority, visual-only, separate pass since it needs a screenshot check per post rather than a text diff.

## The per-item safety pattern (applies to every live edit)

For every single fix, no exceptions:

1. **Re-read the live post immediately before writing** — never rely on a read from earlier in the session. Someone may have hand-edited it since (this already happened: 4 of Kenzie's 49 items and were already fixed by the time we checked).
2. **Verify the exact `wrong_text` string is still present, verbatim**, in the live `article_body`/`faq` widget content. If it's not there anymore — skip it, mark the tracker finding `not_needed` with a note ("already fixed upstream"), do not write.
3. **Back up the full live widget JSON** to `backups/` before touching anything (matches the pattern already used for the heading-CSS and dead-image fixes this session).
4. **PATCH the full `widgets` map**, changing only the one field — HubSpot's PATCH replaces the whole map, so a partial payload silently deletes every other widget.
5. **Re-read after the write** to confirm the exact text landed and nothing else shifted.
6. **Update the tracker status**: `not_started` → `fixed` once the write is confirmed, → `verified` after a quick Playwright re-check of that post's live page.

## Batching

- Work in batches of **5–8 posts** at a time, not all 45 findings in one pass.
- After each batch: re-run the relevant slice of the Playwright QA (byline/FAQ/heading/link checks already built in `master_qa.js`) against just those posts, confirm nothing regressed, *then* move to the next batch.
- If anything in a batch looks off, stop and flag it before continuing — don't push through the rest of the queue on autopilot.

## Rollback

Every live edit has a `backups/` copy of the pre-change widget JSON from step 3 above. If a change needs to be undone, restore that JSON and PATCH it back — same mechanism as the fix itself, in reverse.

## What Shawn needs to do before Phase 2/3 can fully proceed

- Click the 5 style-decision buttons in the tracker (Phase 0 section) — hyphenation, apostrophes, Oxford comma, e-commerce spelling, heading case.
- Click the 3 original Phase-0 decisions (format standardization, the 2 custom-formulation posts, and the "guarantee" word ban) — these gate Phase 3.

Everything in Phase 1 and Phase 2 (the 45 confirmed items) can start executing now, independent of those decisions.
