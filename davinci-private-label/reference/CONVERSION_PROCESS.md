# Converting a Private Label page to drag-and-drop

The process below is what the first 23 pages taught us, reordered so the
expensive mistakes cannot happen again. The single most important change is
step 6: **the page is verified against V1 while V1 is still V1.** Everything
else follows from that.

## Why the order matters

A promoted page no longer holds its original markup. If verification happens
after promotion, the reference for "what did this look like before" is gone —
recoverable only from a snapshot, and only if one was taken. That is what
happened to Home and the six dosage pages: they were promoted first, and the
regressions found later had to be measured against replica pages rebuilt from
snapshots.

Verifying first inverts the risk. A page that fails is simply never promoted,
and V1 is never touched.

---

## The ten steps

### 1. Snapshot V1

`GET /cms/v3/pages/site-pages/<id>` to `snapshots/v1-pre-promotion/<id>.json`,
committed. This is the only durable record of the page's original markup, and
every later step can fall back to it. Never skip it, even for a page that looks
trivial.

### 2. Classify and build the V3 draft

`auto/build.py <V1_ID>` reads each section's markup, decides what kind of
section it is, extracts it, and writes a **new draft page at `<slug>-v3`**.
V1 is not touched. Run with `--dry` first to read the classification back:

```
pl-demo-testing   8 modules  hero richtext cardgrid cta global heritage faq global
```

If that sequence does not describe the page, stop and fix the classifier — do
not hand-patch the output, or the next page repeats the fault.

### 3. Content gate

`fam16/check.py <V1_ID> <V3_ID>` — mechanical, no judgement:

- section count matches
- **zero words lost**, compared after decoding entities and stripping comments
- **zero words invented** (this is what catches a module default eyebrow
  rendering `READY TO START` on a page that never said it)
- exactly one `<h1>`
- no markup debris in card bodies

### 4. Visual gate

`vis/pairs.py` — render V1 and the V3 draft in a real browser at 1440px,
match elements **by their text**, and compare computed font-size, weight,
colour and width. Report separates:

- **real** — a size, weight or colour a visitor would see
- **width-only** — the same glyphs in the same place inside a wider invisible
  box, which happens where V1 shrink-wraps a flex child and a module gives it
  the full row

The gate is **0 real differences**. Not "close", not "explainable".

### 5. Fix generally, not locally

When the gate reports a difference, fix the reader or the module field — never
the single page. Nine of the ten defects found in the category family were
one-line reader bugs that affected all sixteen pages. If a module cannot
express what V1 does, **add the field**: `subhead_size`, `label_weight`,
`content_color` and six others were added this way, each emitted only when a
page departs from the standard so no already-correct page moves.

Rebuild, re-measure, repeat until step 4 reads 0.

### 6. Promote in place

`tools/promote.py <V3_ID> <V1_ID>` — two PATCHes against the V1 record:

1. template → `Page - DND.html`, plus the draft's `layoutSections`
2. `widgetContainers` → tombstoned (`{"widgets": [], "deleted_at": ...}`)

Both are required. A page holding **both** populated `layoutSections` and
`widgetContainers` freezes the HubSpot editor, and the promotion is not atomic —
that state exists for about 0.6s between the two calls.

The slug never changes. The `-v3` draft is kept, not deleted.

### 7. Post-promotion verification

The harness re-reads the page and checks module count, row keys, `w`/`x` at
every depth, publish state, and that the rendered text still matches the
snapshot. **Any failure auto-restores from the snapshot and halts**, and the
restore is itself verified.

### 8. Re-measure the promoted page

Cheap, and it proves the promotion copied faithfully rather than that the draft
was good. Always re-render — never reuse a cached capture. A stale render once
made four correct pages look broken and sent a day's work chasing regressions
that did not exist.

### 9. Record it

Commit the PRE/POST snapshots and update `reference/promotion-map.json`. Between
that, the June snapshots, and HubSpot's own version history, every page has at
least three independent recovery paths.

### 10. Leave it unpublished

Conversion never publishes. Publishing is a separate decision that needs the
brand name, the logo, and the outstanding asset gaps resolved.

---

## Quality checking

### Three gates, and what each one is actually good for

| gate | catches | blind to |
|---|---|---|
| content | lost copy, invented copy, broken heading structure | anything visual |
| visual | type scale, weight, colour, measure | copy that is present but wrong |
| structural | editor-freeze state, module count, publish state | appearance and wording |

All three are needed. For about ten hours every check on this project was
text-only, and every report ended "could not verify visually." The browser diff
found real regressions in ninety seconds that thirteen review passes and every
text gate had missed.

### Reading the visual report honestly

A raw difference count is not a verdict. Separate what a visitor can see from
what only a measurement can see:

- **real** — font-size, weight or colour on an element that paints its own text
- **artifact** — width-only, or a computed colour on a wrapper whose every glyph
  is drawn by a child that sets its own colour

Report both. Never quote the raw number as if it were all regression, and never
quietly drop the artifacts as if they were nothing.

### Order of work

Regular families first, so a fault in the shared tooling is found on a cheap
page rather than an expensive one:

1. one pilot page, end to end
2. the 13 near-identical standard pages
3. the 4 ads pages
4. the 4 thank-you pages
5. the 2 legal pages (pure prose)
6. chewables — with the **dosage** tooling; its structure matches the other
   seven dosage pages exactly
7. the 15 one-offs, individually gated

Four to five pages per cycle. Promote only the pages that pass, never a batch on
the strength of a sample.

### Standing rules

- **Never delete a V1**, and never delete a `-v3` draft.
- **Never cache a render.** Re-render the page under test every time. Only the
  pre-promotion V1 captures are kept, because they cannot be regenerated.
- **Read every size, weight and colour from V1.** Inheriting a module default is
  how a type scale tuned for one family silently restyled another.
- **Never use a global module unless the page's copy already matches it.** A
  global renders from its shared definition and discards page-level parameters;
  used on a page whose wording differs, it replaces that wording silently.
- **Fix the generator, not the page.**
