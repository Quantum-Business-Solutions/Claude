import { promises as fs } from "fs";
import path from "path";
import Anthropic from "@anthropic-ai/sdk";

export interface ExtractedVocabulary {
  category: string;
  tags: string[];
  colors: string[];
  typography: string[];
  layoutNotes: string[];
  guardrails: string[];
}

const MODEL = "claude-sonnet-5";

function mediaTypeFor(filePath: string): "image/png" | "image/jpeg" | "image/webp" | "image/gif" {
  const ext = path.extname(filePath).toLowerCase();
  if (ext === ".jpg" || ext === ".jpeg") return "image/jpeg";
  if (ext === ".webp") return "image/webp";
  if (ext === ".gif") return "image/gif";
  return "image/png";
}

export function isAnalysisConfigured(): boolean {
  return !!process.env.ANTHROPIC_API_KEY;
}

/**
 * Reads a saved reference screenshot and asks Claude to extract the design
 * vocabulary behind it: category, palette, type, layout notes, and any
 * "never do this" guardrails implied by the reference and the caller's notes.
 */
export async function extractDesignVocabulary(params: {
  absoluteImagePath: string;
  title: string;
  notes?: string;
  sourceUrl?: string;
}): Promise<ExtractedVocabulary> {
  if (!isAnalysisConfigured()) {
    throw new Error("ANTHROPIC_API_KEY is not set — add it to .env.local to enable auto-analysis.");
  }

  const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
  const imageBuffer = await fs.readFile(params.absoluteImagePath);
  const base64 = imageBuffer.toString("base64");
  const mediaType = mediaTypeFor(params.absoluteImagePath);

  const contextLines = [
    `Title: ${params.title}`,
    params.sourceUrl ? `Source: ${params.sourceUrl}` : null,
    params.notes ? `Why we saved it: ${params.notes}` : null,
  ]
    .filter(Boolean)
    .join("\n");

  const message = await client.messages.create({
    model: MODEL,
    max_tokens: 1024,
    messages: [
      {
        role: "user",
        content: [
          {
            type: "image",
            source: { type: "base64", media_type: mediaType, data: base64 },
          },
          {
            type: "text",
            text:
              `This is a design screenshot saved to a personal "taste library" used to guide future website and product design work.\n\n${contextLines}\n\n` +
              `Analyze the design and respond with ONLY a JSON object (no markdown fences, no commentary) matching this shape:\n` +
              `{\n` +
              `  "category": string,            // e.g. "SaaS landing page", "pricing page", "portfolio", "dashboard"\n` +
              `  "tags": string[],               // 4-8 short style descriptors, e.g. "editorial", "high-contrast", "bento-grid"\n` +
              `  "colors": string[],             // dominant colors as hex codes where identifiable, else short names\n` +
              `  "typography": string[],         // notes on type choices, e.g. "large serif display headline", "monospace labels"\n` +
              `  "layoutNotes": string[],        // structural/layout observations, e.g. "asymmetric hero split 60/40", "sticky nav with underline hover"\n` +
              `  "guardrails": string[]          // short imperative rules this reference implies, e.g. "avoid purple gradients", "never center-align long body copy"\n` +
              `}`,
          },
        ],
      },
    ],
  });

  const textBlock = message.content.find((b) => b.type === "text");
  if (!textBlock || textBlock.type !== "text") {
    throw new Error("Claude did not return a text response for analysis.");
  }

  const jsonText = extractJson(textBlock.text);
  const parsed = JSON.parse(jsonText) as Partial<ExtractedVocabulary>;

  return {
    category: parsed.category ?? "uncategorized",
    tags: parsed.tags ?? [],
    colors: parsed.colors ?? [],
    typography: parsed.typography ?? [],
    layoutNotes: parsed.layoutNotes ?? [],
    guardrails: parsed.guardrails ?? [],
  };
}

function extractJson(text: string): string {
  const trimmed = text.trim();
  if (trimmed.startsWith("{")) return trimmed;
  const match = trimmed.match(/\{[\s\S]*\}/);
  if (match) return match[0];
  throw new Error("Could not find JSON in Claude's analysis response.");
}
