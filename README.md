# Taste Library

A small app for saving designs we like — website UI, layouts, whole pages — and turning them into
a reusable **style vocabulary** (colors, typography, layout patterns, and "never do this"
guardrails), so QBS website builds and client deliverables draw on an actual, professionalized
taste instead of one-shot guesses.

Inspired by [this workflow](https://www.youtube.com/watch?v=7FU98O0JLHs): build a "taste library"
of references → extract the design vocabulary behind each one → use it on every new design task.

## What's here

- **Web app** (`src/`) — a Next.js app: a gallery of saved references, an upload form, and a
  per-reference detail view showing the extracted vocabulary.
- **Data** (`data/references.json` + `public/uploads/`) — flat-file storage, no database required.
  Images are not committed to git (see `.gitignore`) since they're mostly screenshots of other
  people's work saved for personal reference, not assets we own.
- **MCP server** (`mcp-server/`) — exposes the same library to Claude Code as tools, so it can
  check the style guide and add references directly during a session.
- **Claude Code skill** (`.claude/skills/design-library/SKILL.md`) — tells Claude when to consult
  the library before doing design/website work, and how to save new references it's shown.

## Setup

```bash
npm install
cp .env.example .env.local   # add FIRECRAWL_API_KEY for live-site ingest
npm run dev                  # http://localhost:3000
node mcp-server/src/seed.mjs # optional: 3 real measured references to start from
```

## Two ways in — prefer the first

### 1. Analyze a live URL (preferred)

Paste a site URL and the app reads its **real computed design tokens** — exact hexes by role, font
families and stacks, actual `px` type sizes, spacing base unit, border radius, and per-component
background/text/radius/shadow values. Those port straight into a Tailwind config.

Needs `FIRECRAWL_API_KEY` in `.env.local`. Also available as `POST /api/ingest` with
`{ url, project, category, tags, notes, guardrails }`.

### 2. Upload a screenshot (fallback)

For designs that aren't a reachable live site. Vocabulary here is *inferred* from the image rather
than measured, so it's softer evidence. Set `ANTHROPIC_API_KEY` to have Claude infer category,
tags, colors, typography, layout notes, and guardrails automatically; otherwise fill them in by
hand from the detail page.

The style guide keeps these separate — measured values are reported apart from inferred ones, so a
guessed color never carries the same authority as one read off a live stylesheet.

## A note on Dribbble and other galleries

Use them to **discover** work, then ingest the designer's or product's actual live site. Don't wire
up an automated Dribbble pipeline:

- Their API can't do it — every read endpoint is scoped to the authenticated user's *own* shots.
  There is no search, browse, popular, or likes endpoint.
- Their API terms are explicit: *"The only Dribbble data you may use in your product or application
  is that which is exposed via our API. Scraping, copying, saving, or storing our data is strictly
  prohibited."*

Ingesting the live site is permitted, yields real tokens instead of guesses, and is better evidence
anyway — a shipped site has survived real content and responsive breakpoints; a concept shot
hasn't.

### Registering the MCP server with Claude Code

```bash
cd mcp-server && npm install
```

Then add it to your Claude Code MCP config (e.g. `claude mcp add` or your `mcp_servers.json`):

```json
{
  "mcpServers": {
    "taste-library": {
      "command": "node",
      "args": ["/absolute/path/to/this/repo/mcp-server/src/index.js"]
    }
  }
}
```

Once registered, Claude Code can call `list_design_references`, `search_design_references`,
`get_design_reference`, `get_style_guide`, and `add_design_reference` directly — see
`.claude/skills/design-library/SKILL.md` for how it's expected to use them.

## Data model

Each reference (`data/references.json`) has: `title`, `sourceUrl`, `imagePath`, `sourceKind`
(`live-site` / `screenshot`), `project` (`qbs` / `personal` / `both`), `notes` (why it was saved),
`category`, `tags`, `colors`, `typography`, `layoutNotes`, `guardrails`, an `analysis` status, and
— for live-site references — a `tokens` object holding the measured values.

The prose vocabulary (`colors` / `typography` / `layoutNotes`) is derived automatically from
`tokens` when tokens are present, so the gallery and style guide read consistently no matter which
path created the reference: web ingest, MCP tool, or seed script.

Nothing here is QBS- or client-specific by structure — `project` just lets the style guide be
scoped when it matters.
