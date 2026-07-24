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
cp .env.example .env.local   # optional — only needed for auto-analysis, see below
npm run dev                  # http://localhost:3000
```

### Auto-analysis (optional)

Set `ANTHROPIC_API_KEY` in `.env.local` to have Claude automatically look at each uploaded
screenshot and extract its category, tags, colors, typography notes, layout notes, and guardrails.
Without a key, references are still saved — just add the vocabulary by hand from the detail page,
or fill it in via `add_design_reference` if you're adding it through the MCP server / Claude Code.

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

Each reference (`data/references.json`) has: `title`, `sourceUrl`, `imagePath`, `project`
(`qbs` / `personal` / `both`), `notes` (why it was saved), `category`, `tags`, `colors`,
`typography`, `layoutNotes`, `guardrails`, and an `analysis` status. Nothing here is QBS- or
client-specific by structure — `project` just lets the style guide be scoped when it matters.
