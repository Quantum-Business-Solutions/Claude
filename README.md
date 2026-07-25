# Design library

Design references for QBS website and client work — the taste that Claude Code builds against, so
output is grounded in decisions we've actually made rather than in whatever's average.

There is no app, server, or database. Everything is flat files, hand-editable, read directly by
Claude. That's deliberate: the value is in the references and rules, and every layer between them
and Claude was overhead.

## Layout

| Path | What it is |
|---|---|
| `design/guardrails.md` | The always/never list. Read before generating any design work. |
| `design/references.md` | Reference entries — url, tags, category, and why each one is here. |
| `design/tokens/<slug>.json` | Values **measured** off a live page. Only measured, never hand-written. |
| `design/inbox.md` | Drop zone for URLs awaiting ingest. |
| `design/SCHEMA.md` | The ingest contract — slug rule, file shapes, failure handling. |

## Adding references

The intake is the point: structured, repeatable, batched.

1. **Capture.** Append a URL to `design/inbox.md`, one per line — optionally `<url> | why`. That's
   the whole gesture. Editable from a phone via the GitHub app.
2. **Process.** Run `/design-ingest`. It measures every queued URL in parallel via Firecrawl's
   `branding` extractor, writes token files and reference entries conforming to `design/SCHEMA.md`,
   adds any generalizable rules to the guardrails, and clears the queue. One URL or forty — same
   command, roughly the same wall time.
3. **One-off.** `/design-ingest <url>` skips the inbox.

Failed URLs stay in the inbox annotated with the reason. No partial token files, no invented values.

### Why measured tokens

`branding` reads the rendered page: exact hexes by role, font families, real `px` type sizes,
spacing base unit, border radius, per-component background/text/radius. Those port straight into a
Tailwind config. Vocabulary inferred from a screenshot ("looks like a large serif headline") does
not, which is why `design/tokens/` holds only measured values and everything judged lives in prose.

Measured doesn't mean infallible — extractors mislabel state colors as base colors and report
browser-computed artifacts. See the "Reading measured tokens" section of `design/guardrails.md`, and
check `measuredAt`: a token file over a year old may describe a site since redesigned.

## Sourcing

Ingest **live sites**, not gallery images. A shipped site has survived real content, long copy, and
responsive breakpoints; a concept shot hasn't.

Don't store scraped Dribbble content here. Their API can't serve it — every read endpoint is scoped
to the authenticated user's own shots, with no search or browse — and their terms are explicit:
*"Scraping, copying, saving, or storing our data is strictly prohibited."* This library backs
commercial client work, so treat that as binding. Browse galleries to **discover**, then ingest the
real site.

## Skills

Three skills work together, installed in this repo:

- **`design-library`** (`.claude/skills/`) — this library: when to read it, how to add to it.
- **`impeccable`** ([pbakaus/impeccable](https://github.com/pbakaus/impeccable), submodule at
  `.impeccable`) — 23 commands for craft and anti-slop critique: `/impeccable critique`, `bolder`,
  `quieter`, `polish`, `audit`, and a live browser tweak mode.
- **`design-taste-frontend`** ([Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill)) —
  reads the brief, states a design read, steers away from LLM default aesthetics.

The split: the two installed skills supply craft and anti-slop discipline; this library supplies the
*specific* taste they should be executing against.

Updating them:

```bash
git submodule update --remote .impeccable      # then re-run: npx impeccable link --source=.impeccable --providers=claude,cursor
npx skills add https://github.com/Leonxlnx/taste-skill --skill "design-taste-frontend"
```
