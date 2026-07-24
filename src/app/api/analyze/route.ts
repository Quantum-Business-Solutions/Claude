import { NextRequest, NextResponse } from "next/server";
import path from "path";
import { getReference, updateReference } from "@/lib/db";
import { extractDesignVocabulary, isAnalysisConfigured } from "@/lib/claude";

export async function POST(req: NextRequest) {
  const { id } = (await req.json()) as { id?: string };
  if (!id) return NextResponse.json({ error: "id is required" }, { status: 400 });

  const ref = await getReference(id);
  if (!ref) return NextResponse.json({ error: "not found" }, { status: 404 });
  if (!ref.imagePath) {
    return NextResponse.json({ error: "reference has no saved image to analyze" }, { status: 400 });
  }
  if (!isAnalysisConfigured()) {
    return NextResponse.json(
      { error: "ANTHROPIC_API_KEY is not set on the server — add it to .env.local" },
      { status: 400 }
    );
  }

  try {
    const vocab = await extractDesignVocabulary({
      absoluteImagePath: path.join(process.cwd(), "public", ref.imagePath),
      title: ref.title,
      notes: ref.notes,
      sourceUrl: ref.sourceUrl,
    });
    const updated = await updateReference(id, {
      category: vocab.category,
      tags: [...new Set([...ref.tags, ...vocab.tags])],
      colors: vocab.colors,
      typography: vocab.typography,
      layoutNotes: vocab.layoutNotes,
      guardrails: vocab.guardrails,
      analysis: { status: "done", model: "claude-sonnet-5", analyzedAt: new Date().toISOString() },
    });
    return NextResponse.json({ reference: updated });
  } catch (err) {
    const updated = await updateReference(id, {
      analysis: { status: "error", error: (err as Error).message },
    });
    return NextResponse.json({ reference: updated, error: (err as Error).message }, { status: 500 });
  }
}
