import { NextRequest, NextResponse } from "next/server";
import { createReference } from "@/lib/db";
import { ingestLiveSite, isIngestConfigured } from "@/lib/branding";
import { Project } from "@/lib/types";

/**
 * Adds a reference by reading a live site's real design tokens.
 *
 * Preferred over uploading a screenshot: the values are measured off the
 * rendered page rather than inferred from a picture, and it keeps the library
 * pointed at sites that actually shipped.
 */
export async function POST(req: NextRequest) {
  const body = (await req.json()) as {
    url?: string;
    project?: Project;
    notes?: string;
    category?: string;
    tags?: string[];
    guardrails?: string[];
  };

  if (!body.url) {
    return NextResponse.json({ error: "url is required" }, { status: 400 });
  }

  let parsed: URL;
  try {
    parsed = new URL(body.url);
  } catch {
    return NextResponse.json({ error: "url is not a valid URL" }, { status: 400 });
  }
  if (parsed.protocol !== "https:" && parsed.protocol !== "http:") {
    return NextResponse.json({ error: "url must be http(s)" }, { status: 400 });
  }

  if (!isIngestConfigured()) {
    return NextResponse.json(
      {
        error:
          "FIRECRAWL_API_KEY is not set on the server — add it to .env.local to enable live-site ingest.",
      },
      { status: 400 }
    );
  }

  try {
    const result = await ingestLiveSite(body.url);
    const ref = await createReference({
      title: body.category ? `${result.title}` : result.title,
      sourceUrl: body.url,
      imagePath: result.imagePath,
      sourceKind: "live-site",
      project: body.project ?? "both",
      notes: body.notes ?? result.description,
      category: body.category,
      tags: body.tags ?? [],
      tokens: result.tokens,
      colors: result.derived.colors,
      typography: result.derived.typography,
      layoutNotes: result.derived.layoutNotes,
      guardrails: body.guardrails ?? [],
    });
    return NextResponse.json({ reference: ref }, { status: 201 });
  } catch (err) {
    return NextResponse.json({ error: (err as Error).message }, { status: 502 });
  }
}
