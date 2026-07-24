import { NextRequest, NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";
import { createReference, listReferences, updateReference } from "@/lib/db";
import { extractDesignVocabulary, isAnalysisConfigured } from "@/lib/claude";
import { Project } from "@/lib/types";

const UPLOAD_DIR = path.join(process.cwd(), "public", "uploads");

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const refs = await listReferences({
    project: searchParams.get("project") ?? undefined,
    category: searchParams.get("category") ?? undefined,
    tag: searchParams.get("tag") ?? undefined,
    q: searchParams.get("q") ?? undefined,
  });
  return NextResponse.json({ references: refs });
}

function sanitizeFilename(name: string): string {
  return name.replace(/[^a-zA-Z0-9.\-_]/g, "_").slice(-100);
}

export async function POST(req: NextRequest) {
  const form = await req.formData();

  const title = (form.get("title") as string | null)?.trim();
  if (!title) {
    return NextResponse.json({ error: "title is required" }, { status: 400 });
  }

  const project = ((form.get("project") as string | null) ?? "both") as Project;
  const sourceUrl = (form.get("sourceUrl") as string | null)?.trim() || undefined;
  const notes = (form.get("notes") as string | null)?.trim() || undefined;
  const category = (form.get("category") as string | null)?.trim() || undefined;
  const tagsRaw = (form.get("tags") as string | null) ?? "";
  const tags = tagsRaw
    .split(",")
    .map((t) => t.trim())
    .filter(Boolean);

  const file = form.get("image") as File | null;
  let imagePath: string | undefined;

  if (file && file.size > 0) {
    await fs.mkdir(UPLOAD_DIR, { recursive: true });
    const id = Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
    const filename = `${id}-${sanitizeFilename(file.name || "reference.png")}`;
    const bytes = Buffer.from(await file.arrayBuffer());
    await fs.writeFile(path.join(UPLOAD_DIR, filename), bytes);
    imagePath = `/uploads/${filename}`;
  }

  const ref = await createReference({ title, sourceUrl, imagePath, project, notes, category, tags });

  if (imagePath && isAnalysisConfigured()) {
    try {
      const vocab = await extractDesignVocabulary({
        absoluteImagePath: path.join(process.cwd(), "public", imagePath),
        title,
        notes,
        sourceUrl,
      });
      const updated = await updateReference(ref.id, {
        category: ref.category ?? vocab.category,
        tags: [...new Set([...ref.tags, ...vocab.tags])],
        colors: vocab.colors,
        typography: vocab.typography,
        layoutNotes: vocab.layoutNotes,
        guardrails: vocab.guardrails,
        analysis: { status: "done", model: "claude-sonnet-5", analyzedAt: new Date().toISOString() },
      });
      return NextResponse.json({ reference: updated }, { status: 201 });
    } catch (err) {
      const updated = await updateReference(ref.id, {
        analysis: { status: "error", error: (err as Error).message },
      });
      return NextResponse.json({ reference: updated }, { status: 201 });
    }
  }

  return NextResponse.json({ reference: ref }, { status: 201 });
}
