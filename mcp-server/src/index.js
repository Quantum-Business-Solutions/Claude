#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { addReference, getReference, getStyleGuide, listReferences } from "./store.js";

const server = new McpServer({
  name: "taste-library",
  version: "0.1.0",
});

const projectEnum = z.enum(["qbs", "personal", "both", "all"]).optional();

server.registerTool(
  "list_design_references",
  {
    title: "List saved design references",
    description:
      "List designs saved in the taste library, optionally filtered by project (qbs/personal/both), category, or tag. Use this before starting website or design work to see what taste has already been captured.",
    inputSchema: {
      project: projectEnum,
      category: z.string().optional(),
      tag: z.string().optional(),
    },
  },
  async ({ project, category, tag }) => {
    const refs = await listReferences({ project, category, tag });
    return { content: [{ type: "text", text: JSON.stringify(refs, null, 2) }] };
  }
);

server.registerTool(
  "search_design_references",
  {
    title: "Search design references",
    description:
      "Full-text search across saved design references (title, notes, category, tags, guardrails) for a keyword, e.g. 'pricing table' or 'dark mode'.",
    inputSchema: {
      q: z.string().describe("Search keyword or phrase"),
      project: projectEnum,
    },
  },
  async ({ q, project }) => {
    const refs = await listReferences({ q, project });
    return { content: [{ type: "text", text: JSON.stringify(refs, null, 2) }] };
  }
);

server.registerTool(
  "get_design_reference",
  {
    title: "Get a design reference",
    description: "Fetch full details for a single saved design reference by id.",
    inputSchema: { id: z.string() },
  },
  async ({ id }) => {
    const ref = await getReference(id);
    if (!ref) {
      return { content: [{ type: "text", text: `No reference found with id ${id}` }], isError: true };
    }
    return { content: [{ type: "text", text: JSON.stringify(ref, null, 2) }] };
  }
);

server.registerTool(
  "get_style_guide",
  {
    title: "Get the synthesized style guide",
    description:
      "Get an aggregated style guide across the whole taste library (or one project): most common tags, categories, colors, and the full list of guardrails ('never do X') implied by saved references. Use this to ground any new website or design work in established taste before generating anything.",
    inputSchema: { project: projectEnum },
  },
  async ({ project }) => {
    const guide = await getStyleGuide({ project });
    return { content: [{ type: "text", text: JSON.stringify(guide, null, 2) }] };
  }
);

server.registerTool(
  "add_design_reference",
  {
    title: "Save a new design reference",
    description:
      "Save a new design you or the user like into the taste library, so future website/design work can draw on it. If localImagePath points to an image file already on disk, it will be copied into the library's uploads folder. Style vocabulary (colors/typography/layout/guardrails) can be passed directly if already known (e.g. from having looked at the image), otherwise leave them empty and analyze later via the web app.",
    inputSchema: {
      title: z.string(),
      notes: z.string().optional().describe("Why this was saved / what's good about it"),
      sourceUrl: z.string().optional(),
      localImagePath: z.string().optional().describe("Absolute path to an image file already on disk to copy in"),
      project: z.enum(["qbs", "personal", "both"]).optional(),
      category: z.string().optional(),
      tags: z.array(z.string()).optional(),
      colors: z.array(z.string()).optional(),
      typography: z.array(z.string()).optional(),
      layoutNotes: z.array(z.string()).optional(),
      guardrails: z.array(z.string()).optional(),
    },
  },
  async (input) => {
    const ref = await addReference(input);
    return { content: [{ type: "text", text: JSON.stringify(ref, null, 2) }] };
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
