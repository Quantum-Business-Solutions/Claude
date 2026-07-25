---
name: design-library
description: Use this skill whenever doing website, landing page, proposal, or product design work — for QBS client work or personal projects — to ground the output in the saved design library instead of guessing. Also use it whenever the user shares a design they like ("save this", "I like this style", a screenshot, a Dribbble/Pinterest/site link) so it gets captured for future work. Trigger on "design inspiration", "taste library", "style guide", "what do we like", "design references", "guardrails", or before generating any new UI/website/landing-page design.
---

# Design library

Flat files in `design/`. No app, no server, no database — read them directly with Read/Glob/Grep.

| File | What it is |
|---|---|
| `design/guardrails.md` | The always/never list. **Read before generating any design work.** |
| `design/references.md` | The reference entries — url, tags, category, and why each is here. |
| `design/tokens/<slug>.json` | Values **measured** off a live page. Only measured; never hand-written. |
| `design/inbox.md` | Drop zone for URLs awaiting ingest. |
| `design/SCHEMA.md` | The ingest contract — slug rule, file shapes, failure rule. |

## Before generating design work

1. Read `design/guardrails.md`. Treat it as hard constraints, not suggestions — it encodes decisions
   already made, and re-litigating them per project is how a house style fails to accumulate.
2. Read `design/references.md`. If the task maps to a category or tag present there (pricing page,
   professional services, dark product marketing…), read that entry's `design/tokens/*.json` too —
   the measured values are the point, and they port directly into a Tailwind config or CSS custom
   properties.
3. Distinguish measured from judged when you use it. A hex from `design/tokens/` is fact; the prose
   in `references.md` is opinion. Don't quote the second with the confidence of the first, and check
   `measuredAt` — a token file over a year old may describe a site that has since been redesigned.
4. If nothing in the library is relevant, **say so plainly** rather than inventing a "typical" style
   for the category. The library exists to replace guessing, not to launder it.

Pair this with the `impeccable` and `design-taste-frontend` skills, which handle craft and
anti-slop execution. This skill supplies the specific taste those two should be executing against.

## Adding references

Structured, repeatable, batchable — that's the whole design of it:

- **Capture:** append URLs to `design/inbox.md`, one per line, optionally `<url> | why`.
- **Process:** run `/design-ingest`. It measures each URL via Firecrawl's `branding` extractor in
  parallel, writes token files and reference entries per `design/SCHEMA.md`, updates guardrails, and
  clears the queue. Same command for one URL or forty.
- **Direct:** `/design-ingest <url>` skips the inbox for a one-off.

When the user shows you something they like mid-conversation, add it to the inbox (or ingest it
directly) rather than only replying about it. Capture is the point.

## Sourcing rules

Ingest **live sites**, not gallery images — a shipped site has survived real content and responsive
breakpoints; a concept shot hasn't.

Do not store scraped Dribbble content in this repo. Their API cannot serve it (every read endpoint is
scoped to the authenticated user's own shots — no search, browse, or likes), and their terms are
explicit: *"Scraping, copying, saving, or storing our data is strictly prohibited."* This library
backs commercial client work, so treat that as binding. Browse galleries to **discover**; ingest the
designer's or product's actual live site.

## Don't

- Don't hand-write values into `design/tokens/` — that directory is the measured/guessed boundary.
- Don't skip the guardrails read because a task looks small. That's when slop gets in.
- Don't silently drop a failed ingest. Leave it in the inbox with a reason, per the schema.
