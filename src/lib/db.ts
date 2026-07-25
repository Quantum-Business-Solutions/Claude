import { promises as fs } from "fs";
import path from "path";
import { DesignReference, NewDesignReferenceInput, StyleGuide } from "./types";
import { deriveVocabulary } from "./branding";

const DATA_DIR = path.join(process.cwd(), "data");
const DATA_FILE = path.join(DATA_DIR, "references.json");

async function ensureDataFile() {
  await fs.mkdir(DATA_DIR, { recursive: true });
  try {
    await fs.access(DATA_FILE);
  } catch {
    await fs.writeFile(DATA_FILE, "[]\n", "utf-8");
  }
}

async function readAll(): Promise<DesignReference[]> {
  await ensureDataFile();
  const raw = await fs.readFile(DATA_FILE, "utf-8");
  try {
    return JSON.parse(raw) as DesignReference[];
  } catch {
    return [];
  }
}

async function writeAll(refs: DesignReference[]): Promise<void> {
  await ensureDataFile();
  await fs.writeFile(DATA_FILE, JSON.stringify(refs, null, 2) + "\n", "utf-8");
}

export interface ListFilter {
  project?: string;
  category?: string;
  tag?: string;
  q?: string;
}

export async function listReferences(filter: ListFilter = {}): Promise<DesignReference[]> {
  let refs = await readAll();

  if (filter.project && filter.project !== "all") {
    refs = refs.filter((r) => r.project === filter.project || r.project === "both");
  }
  if (filter.category) {
    refs = refs.filter((r) => r.category?.toLowerCase() === filter.category!.toLowerCase());
  }
  if (filter.tag) {
    refs = refs.filter((r) => r.tags.some((t) => t.toLowerCase() === filter.tag!.toLowerCase()));
  }
  if (filter.q) {
    const q = filter.q.toLowerCase();
    refs = refs.filter((r) =>
      [r.title, r.notes, r.category, ...r.tags, ...r.guardrails]
        .filter(Boolean)
        .some((field) => field!.toLowerCase().includes(q))
    );
  }

  return refs.sort((a, b) => (a.createdAt < b.createdAt ? 1 : -1));
}

export async function getReference(id: string): Promise<DesignReference | undefined> {
  const refs = await readAll();
  return refs.find((r) => r.id === id);
}

export async function createReference(input: NewDesignReferenceInput): Promise<DesignReference> {
  const refs = await readAll();
  const now = new Date().toISOString();
  // Keep prose vocabulary in step with measured tokens regardless of caller.
  const derived = input.tokens ? deriveVocabulary(input.tokens) : null;
  const ref: DesignReference = {
    id: cryptoRandomId(),
    createdAt: now,
    updatedAt: now,
    title: input.title,
    sourceUrl: input.sourceUrl,
    imagePath: input.imagePath,
    sourceKind: input.sourceKind ?? "screenshot",
    project: input.project,
    notes: input.notes,
    category: input.category,
    tags: input.tags ?? [],
    colors: input.colors ?? derived?.colors ?? [],
    typography: input.typography ?? derived?.typography ?? [],
    layoutNotes: input.layoutNotes ?? derived?.layoutNotes ?? [],
    guardrails: input.guardrails ?? [],
    tokens: input.tokens,
    analysis: {
      // A live-site ingest already carries measured values, so there is
      // nothing for the vision pass to add.
      status: input.tokens ? "done" : input.imagePath ? "pending" : "skipped",
      analyzedAt: input.tokens ? now : undefined,
    },
  };
  refs.push(ref);
  await writeAll(refs);
  return ref;
}

export async function updateReference(
  id: string,
  patch: Partial<DesignReference>
): Promise<DesignReference | undefined> {
  const refs = await readAll();
  const idx = refs.findIndex((r) => r.id === id);
  if (idx === -1) return undefined;
  refs[idx] = { ...refs[idx], ...patch, id: refs[idx].id, updatedAt: new Date().toISOString() };
  await writeAll(refs);
  return refs[idx];
}

export async function deleteReference(id: string): Promise<boolean> {
  const refs = await readAll();
  const next = refs.filter((r) => r.id !== id);
  const changed = next.length !== refs.length;
  if (changed) await writeAll(next);
  return changed;
}

export async function getStyleGuide(filter: ListFilter = {}): Promise<StyleGuide> {
  const refs = await listReferences(filter);

  const tagCounts = new Map<string, number>();
  const categoryCounts = new Map<string, number>();
  const colorCounts = new Map<string, number>();
  const typographyCounts = new Map<string, number>();
  const guardrails = new Set<string>();

  // Measured values, tracked separately so a guessed color never gets
  // presented with the same authority as one read off a live stylesheet.
  const fontFamilyCounts = new Map<string, number>();
  const radiusCounts = new Map<string, number>();
  const baseUnitCounts = new Map<number, number>();
  const accentColors = new Set<string>();
  let liveSiteCount = 0;

  for (const r of refs) {
    for (const t of r.tags) tagCounts.set(t, (tagCounts.get(t) ?? 0) + 1);
    if (r.category) categoryCounts.set(r.category, (categoryCounts.get(r.category) ?? 0) + 1);
    for (const c of r.colors) colorCounts.set(c, (colorCounts.get(c) ?? 0) + 1);
    for (const t of r.typography) typographyCounts.set(t, (typographyCounts.get(t) ?? 0) + 1);
    for (const g of r.guardrails) guardrails.add(g);

    if (r.sourceKind === "live-site") liveSiteCount++;
    if (r.tokens) {
      for (const f of r.tokens.fonts ?? []) {
        fontFamilyCounts.set(f.family, (fontFamilyCounts.get(f.family) ?? 0) + 1);
      }
      const radius = r.tokens.spacing?.borderRadius;
      if (radius) radiusCounts.set(radius, (radiusCounts.get(radius) ?? 0) + 1);
      const unit = r.tokens.spacing?.baseUnit;
      if (unit) baseUnitCounts.set(unit, (baseUnitCounts.get(unit) ?? 0) + 1);
      for (const key of ["accent", "link", "secondary"] as const) {
        const hex = r.tokens.colors?.[key];
        if (hex) accentColors.add(hex);
      }
    }
  }

  const topN = <K>(m: Map<K, number>, n: number) =>
    [...m.entries()].sort((a, b) => b[1] - a[1]).slice(0, n);

  return {
    referenceCount: refs.length,
    liveSiteCount,
    topTags: topN(tagCounts, 15).map(([tag, count]) => ({ tag, count })),
    topCategories: topN(categoryCounts, 10).map(([category, count]) => ({ category, count })),
    commonColors: topN(colorCounts, 12).map(([color]) => color),
    commonTypography: topN(typographyCounts, 10).map(([t]) => t),
    guardrails: [...guardrails],
    measured: {
      fontFamilies: topN(fontFamilyCounts, 10).map(([family, count]) => ({ family, count })),
      borderRadii: topN(radiusCounts, 6).map(([value, count]) => ({ value, count })),
      baseUnits: topN(baseUnitCounts, 4).map(([value, count]) => ({ value, count })),
      accentColors: [...accentColors].slice(0, 12),
    },
  };
}

function cryptoRandomId(): string {
  // avoid pulling in the `uuid` package for one call
  return (
    Date.now().toString(36) + Math.random().toString(36).slice(2, 10)
  );
}
