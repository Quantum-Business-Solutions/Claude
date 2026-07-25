---
name: design-library
description: Use this skill whenever doing website, landing page, proposal, or product design work — for QBS client work or personal projects — to ground the output in the taste library instead of guessing. Also use it whenever the user shares a design they like ("save this", "I like this style", a screenshot, a Dribbble/Pinterest/site link) so it gets captured for future work. Trigger on "design inspiration", "taste library", "style guide", "what do we like", "design references", or before generating any new UI/website/landing-page design.
---

# Design library (taste library)

This repo hosts a small app + MCP server for saving designs we like and turning them into a
reusable style vocabulary, so QBS website/proposal/product design work is grounded in an actual,
professionalized taste instead of one-shot guesses.

- Web app: Next.js app at the repo root (`npm run dev`, default `http://localhost:3000`) — gallery,
  upload form, and per-reference detail view.
- Data: `data/references.json` (one record per saved design) + images in `public/uploads/`.
- MCP server: `mcp-server/` exposes the same library as tools (`list_design_references`,
  `search_design_references`, `get_design_reference`, `get_style_guide`, `add_design_reference`) so
  Claude Code can query and add to it directly, without the web UI. Register it once per
  `docs/DESIGN_LIBRARY.md` ("Registering the MCP server"), then use `ToolSearch` for
  `mcp__taste-library__*` tools.

## Before starting design/website work

1. Call `get_style_guide` (optionally scoped to `project: "qbs"` or `"personal"`) to pull the
   current common tags, categories, recurring colors, and — most important — the accumulated
   **guardrails** (explicit "never do X" rules from past references).
2. If the work maps to a specific style (e.g. "pricing page", "SaaS landing hero"), also call
   `search_design_references` or `list_design_references` with a matching category/tag to pull
   concrete examples, not just the aggregate guide.
3. Apply the guardrails as hard constraints, and lean toward the recurring tags/colors/type
   patterns unless the user directs otherwise for this specific piece of work.
4. If the library has nothing relevant yet, say so plainly rather than inventing a "typical" style
   — this is meant to replace guessing, not launder it.

## When the user likes something / wants to save a reference

**Prefer analyzing a live site over saving a picture.** A screenshot only supports guessed
vocabulary ("looks like a large serif headline"); a live site yields measured tokens — exact hexes
with roles, real font stacks, actual `px` sizes, border radii, and per-component background/text/
radius/shadow values. Those port straight into a Tailwind config; guesses don't.

For a reachable live site:
1. Scrape it with Firecrawl using the `branding` format (`firecrawl_scrape` with
   `formats: ["branding"]`, optionally plus `screenshot`).
2. Call `add_design_reference` with `sourceKind: "live-site"`, `sourceUrl`, and the extracted
   values in `tokens`. Also set `guardrails` from what the user actually said they want to avoid.

Or, if the app is running with a `FIRECRAWL_API_KEY` configured, `POST /api/ingest` with
`{ url, project, category, tags, notes, guardrails }` does both steps in one call.

For anything not a reachable live site (a print piece, a concept shot, an app UI), fall back to
`localImagePath` with `sourceKind: "screenshot"` and fill `colors`/`typography`/`layoutNotes`
yourself if you can see the image; otherwise leave them for the app's vision pass.

Either way, `notes` should capture *why* it's good — specific, not vibes.

## Dribbble, Pinterest, and other galleries

Use them the way a designer does: browse to **discover** work. Do not build or run an automated
pipeline that pulls their content into this library.

- Dribbble's API cannot do it anyway — every read endpoint is scoped to the authenticated user's
  own shots; there is no search, browse, or likes endpoint.
- Dribbble's API terms are explicit: *"The only Dribbble data you may use in your product or
  application is that which is exposed via our API. Scraping, copying, saving, or storing our data
  is strictly prohibited."* This library is used for commercial client work, so treat that as
  binding.

The right move when a Dribbble shot is great: find the designer's or product's **actual live site**
and ingest that instead. It's permitted, it yields real tokens, and it's better evidence — a
shipped site has survived real content and responsive breakpoints, which concept art hasn't.

## Don't

- Don't fabricate colors/typography/guardrails for a reference you haven't actually looked at.
- Don't skip checking the style guide before generating new design work when this skill is in play
  — that's the entire point of having captured it.
