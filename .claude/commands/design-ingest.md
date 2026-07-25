---
description: Process design/inbox.md into measured references — batches the whole queue
argument-hint: "[optional URL to ingest directly instead of reading the inbox]"
allowed-tools: Read, Write, Edit, Glob, Bash, mcp__Firecrawl__firecrawl_scrape
---

Ingest design references. Deterministic pipeline — follow it exactly; do not improvise the shape of
the output. `$ARGUMENTS`, if present, is a URL to ingest directly; otherwise process the queue.

## 1. Read the contract, then the queue

Read `design/SCHEMA.md` first. It defines the slug rule, the token-file key order, the reference
entry shape, and the failure rule. Everything below depends on it.

Then read `design/inbox.md` and collect the queue: every line below the `<!-- queue starts below -->`
marker that isn't blank, isn't a `#` comment, and isn't inside a fenced code block. Each line is
`<url>` or `<url> | <why>`.

If the queue is empty and no `$ARGUMENTS` was given, say so and stop. Don't invent work.

## 2. Skip what's already there

Read `design/references.md`. For each queued URL, derive its slug per the schema and check both:
- an existing `## ` entry with that `url:`
- an existing `design/tokens/<slug>.json`

Already present → report it as skipped and drop it from the batch. Re-measuring is only correct when
the user asked for a refresh or the file's `measuredAt` is over a year old.

## 3. Measure each remaining URL

Per URL, call `mcp__Firecrawl__firecrawl_scrape` with `formats: ["branding"]`.

Batch these calls in parallel — multiple tool calls in one block. This is what makes a 40-URL queue
cost roughly what a 4-URL queue costs in wall time. Don't loop them one at a time.

## 4. Write outputs

For each URL that returned usable branding data:

**a.** Write `design/tokens/<slug>.json` conforming to the schema — key order as specified, omit
keys the extractor didn't return, `measuredAt` as today's plain date, `confidence` from the
extractor's `overall`. Copy values verbatim. Never fill a gap with a plausible-looking value; an
absent key is information.

**b.** Append an entry to `design/references.md` in the schema's exact shape, inserted before the
`## Candidates not yet adopted` section. Write the prose from what the tokens plus the queue line's
`| why` actually support — name the specific move. If `confidence` is below 0.7, say the read was
low-confidence in the prose rather than presenting the numbers as settled fact.

**c.** If the site implies a rule that generalizes beyond itself, add it to the matching section of
`design/guardrails.md`. Deduplicate against what's there — a near-restatement of an existing rule is
noise. Site-specific observations belong in the entry prose, not here.

## 5. Clear the queue and report

Remove successfully-ingested lines from `design/inbox.md`. Per the schema's failure rule, **leave
failed URLs in the inbox** with `# failed: <reason>` appended to the line — no partial token file,
no invented values.

Report a compact table: URL, slug, confidence, and outcome (added / skipped / failed-with-reason).
State the failure count explicitly even when it's zero, so a silent partial run can't read as a
clean one.
