import { promises as fs } from "fs";
import path from "path";
import { DesignTokens } from "./types";

const FIRECRAWL_ENDPOINT = "https://api.firecrawl.dev/v2/scrape";
const UPLOAD_DIR = path.join(process.cwd(), "public", "uploads");

export function isIngestConfigured(): boolean {
  return !!process.env.FIRECRAWL_API_KEY;
}

export interface IngestResult {
  tokens: DesignTokens;
  title: string;
  description?: string;
  imagePath?: string;
  /** Human-readable vocabulary derived from the measured tokens. */
  derived: {
    colors: string[];
    typography: string[];
    layoutNotes: string[];
  };
}

/**
 * Reads a live site and returns its real design tokens.
 *
 * This is the preferred way to add a reference: the values come from the
 * rendered page (computed colors, font stacks, radii, component specs) rather
 * than from eyeballing a static image, and it keeps us on sites that actually
 * shipped instead of concept art.
 */
export async function ingestLiveSite(url: string): Promise<IngestResult> {
  const apiKey = process.env.FIRECRAWL_API_KEY;
  if (!apiKey) {
    throw new Error(
      "FIRECRAWL_API_KEY is not set — add it to .env.local to enable live-site ingest."
    );
  }

  const res = await fetch(FIRECRAWL_ENDPOINT, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      url,
      formats: ["branding", { type: "screenshot", fullPage: false }],
    }),
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Firecrawl returned ${res.status}: ${body.slice(0, 300)}`);
  }

  const payload = (await res.json()) as {
    data?: {
      branding?: Record<string, unknown>;
      screenshot?: string;
      metadata?: Record<string, unknown>;
    };
  };

  const data = payload.data ?? {};
  const branding = (data.branding ?? {}) as Record<string, any>;
  const metadata = (data.metadata ?? {}) as Record<string, any>;

  const tokens: DesignTokens = {
    colorScheme: branding.colorScheme,
    colors: branding.colors,
    fonts: branding.fonts,
    fontStacks: branding.typography?.fontStacks,
    fontSizes: branding.typography?.fontSizes,
    spacing: branding.spacing,
    components: branding.components,
    personality: branding.personality,
    designSystem: branding.designSystem,
    confidence: branding.confidence,
  };

  const imagePath = data.screenshot ? await saveScreenshot(data.screenshot) : undefined;

  return {
    tokens,
    title: metadata.title || metadata.ogTitle || hostnameOf(url),
    description: metadata.description || metadata.ogDescription,
    imagePath,
    derived: deriveVocabulary(tokens),
  };
}

/**
 * Turns measured tokens into the same shape of prose vocabulary the rest of the
 * library already stores, so live-site and screenshot references stay
 * comparable in the gallery and the style guide.
 */
export function deriveVocabulary(tokens: DesignTokens): IngestResult["derived"] {
  const colors = Object.entries(tokens.colors ?? {})
    .filter(([, hex]) => !!hex)
    .map(([role, hex]) => `${hex} (${role})`);

  const typography: string[] = [];
  for (const font of tokens.fonts ?? []) {
    typography.push(font.role ? `${font.family} — ${font.role}` : font.family);
  }
  for (const [step, size] of Object.entries(tokens.fontSizes ?? {})) {
    typography.push(`${step}: ${size}`);
  }

  const layoutNotes: string[] = [];
  if (tokens.spacing?.baseUnit) {
    layoutNotes.push(`${tokens.spacing.baseUnit}px spacing base unit`);
  }
  if (tokens.spacing?.borderRadius) {
    layoutNotes.push(`${tokens.spacing.borderRadius} default border radius`);
  }
  for (const [name, spec] of Object.entries(tokens.components ?? {})) {
    const bits = [
      spec.background ? `bg ${spec.background}` : null,
      spec.borderRadius ? `radius ${spec.borderRadius}` : null,
    ].filter(Boolean);
    if (bits.length) layoutNotes.push(`${name}: ${bits.join(", ")}`);
  }
  if (tokens.designSystem?.framework) {
    layoutNotes.push(`framework: ${tokens.designSystem.framework}`);
  }

  return { colors, typography, layoutNotes };
}

async function saveScreenshot(screenshot: string): Promise<string | undefined> {
  await fs.mkdir(UPLOAD_DIR, { recursive: true });
  const id = Date.now().toString(36) + Math.random().toString(36).slice(2, 8);

  // Firecrawl returns either a data URI or a hosted URL depending on account.
  if (screenshot.startsWith("data:")) {
    const comma = screenshot.indexOf(",");
    if (comma === -1) return undefined;
    const buffer = Buffer.from(screenshot.slice(comma + 1), "base64");
    const filename = `${id}-site.png`;
    await fs.writeFile(path.join(UPLOAD_DIR, filename), buffer);
    return `/uploads/${filename}`;
  }

  if (screenshot.startsWith("http")) {
    const res = await fetch(screenshot);
    if (!res.ok) return undefined;
    const buffer = Buffer.from(await res.arrayBuffer());
    const filename = `${id}-site.png`;
    await fs.writeFile(path.join(UPLOAD_DIR, filename), buffer);
    return `/uploads/${filename}`;
  }

  return undefined;
}

function hostnameOf(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}
