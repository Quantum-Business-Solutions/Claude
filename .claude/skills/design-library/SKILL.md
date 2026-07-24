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

Call `add_design_reference` with:
- `title`, `sourceUrl` if there is one, `notes` capturing *why* it's good (specific, not vibes)
- `project`: `"qbs"`, `"personal"`, or `"both"`
- `localImagePath` if a screenshot is already saved on disk (it gets copied into
  `public/uploads/` and registered)
- Fill `tags`/`colors`/`typography`/`layoutNotes`/`guardrails` directly if you can already see and
  describe the image yourself — that skips needing an `ANTHROPIC_API_KEY`-backed auto-analysis
  pass. Otherwise leave them empty; the web app will auto-analyze on next visit if the key is
  configured, or a human can fill them in via the upload/detail pages.

## Don't

- Don't fabricate colors/typography/guardrails for a reference you haven't actually looked at.
- Don't skip checking the style guide before generating new design work when this skill is in play
  — that's the entire point of having captured it.
