import { NextRequest, NextResponse } from "next/server";
import { deleteReference, getReference, updateReference } from "@/lib/db";

export async function GET(_req: NextRequest, { params }: { params: { id: string } }) {
  const ref = await getReference(params.id);
  if (!ref) return NextResponse.json({ error: "not found" }, { status: 404 });
  return NextResponse.json({ reference: ref });
}

export async function PATCH(req: NextRequest, { params }: { params: { id: string } }) {
  const body = await req.json();
  const allowed = ["title", "notes", "category", "tags", "guardrails", "colors", "typography", "layoutNotes", "project", "sourceUrl"] as const;
  const patch: Record<string, unknown> = {};
  for (const key of allowed) {
    if (key in body) patch[key] = body[key];
  }
  const updated = await updateReference(params.id, patch);
  if (!updated) return NextResponse.json({ error: "not found" }, { status: 404 });
  return NextResponse.json({ reference: updated });
}

export async function DELETE(_req: NextRequest, { params }: { params: { id: string } }) {
  const ok = await deleteReference(params.id);
  if (!ok) return NextResponse.json({ error: "not found" }, { status: 404 });
  return NextResponse.json({ ok: true });
}
