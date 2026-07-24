import { NextRequest, NextResponse } from "next/server";
import { getStyleGuide } from "@/lib/db";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const guide = await getStyleGuide({ project: searchParams.get("project") ?? undefined });
  return NextResponse.json({ styleGuide: guide });
}
