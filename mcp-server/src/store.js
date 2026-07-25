import { promises as fs } from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, "..", "..");
const DATA_FILE = path.join(REPO_ROOT, "data", "references.json");
const UPLOAD_DIR = path.join(REPO_ROOT, "public", "uploads");

async function ensureDataFile() {
  await fs.mkdir(path.dirname(DATA_FILE), { recursive: true });
  try {
    await fs.access(DATA_FILE);
  } catch {
    await fs.writeFile(DATA_FILE, "[]\n", "utf-8");
  }
}

export async function readAll() {
  await ensureDataFile();
  const raw = await fs.readFile(DATA_FILE, "utf-8");
  try {
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

async function writeAll(refs) {
  await ensureDataFile();
  await fs.writeFile(DATA_FILE, JSON.stringify(refs, null, 2) + "\n", "utf-8");
}

function randomId() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 10);
}

/**
 * Derives the prose vocabulary (colors/typography/layoutNotes) from measured
 * tokens. Applied whenever a caller supplies tokens but not the prose arrays,
 * so the gallery and style guide read consistently no matter which path — web
 * ingest, MCP tool, or seed — created the reference.
 */
function deriveVocabulary(tokens) {
  const colors = Object.entries(tokens.colors ?? {})
    .filter(([, hex]) => !!hex)
    .map(([role, hex]) => `${hex} (${role})`);

  const typography = [];
  for (const font of tokens.fonts ?? []) {
    typography.push(font.role ? `${font.family} — ${font.role}` : font.family);
  }
  for (const [step, size] of Object.entries(tokens.fontSizes ?? {})) {
    typography.push(`${step}: ${size}`);
  }

  const layoutNotes = [];
  if (tokens.spacing?.baseUnit) layoutNotes.push(`${tokens.spacing.baseUnit}px spacing base unit`);
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

export async function listReferences({ project, category, tag, q } = {}) {
  let refs = await readAll();
  if (project && project !== "all") {
    refs = refs.filter((r) => r.project === project || r.project === "both");
  }
  if (category) {
    refs = refs.filter((r) => (r.category ?? "").toLowerCase() === category.toLowerCase());
  }
  if (tag) {
    refs = refs.filter((r) => (r.tags ?? []).some((t) => t.toLowerCase() === tag.toLowerCase()));
  }
  if (q) {
    const needle = q.toLowerCase();
    refs = refs.filter((r) =>
      [r.title, r.notes, r.category, ...(r.tags ?? []), ...(r.guardrails ?? [])]
        .filter(Boolean)
        .some((field) => String(field).toLowerCase().includes(needle))
    );
  }
  return refs.sort((a, b) => (a.createdAt < b.createdAt ? 1 : -1));
}

export async function getReference(id) {
  const refs = await readAll();
  return refs.find((r) => r.id === id);
}

export async function addReference(input) {
  const refs = await readAll();
  const now = new Date().toISOString();

  let imagePath;
  if (input.localImagePath) {
    await fs.mkdir(UPLOAD_DIR, { recursive: true });
    const ext = path.extname(input.localImagePath) || ".png";
    const filename = `${randomId()}${ext}`;
    await fs.copyFile(input.localImagePath, path.join(UPLOAD_DIR, filename));
    imagePath = `/uploads/${filename}`;
  }

  const derived = input.tokens ? deriveVocabulary(input.tokens) : null;

  const ref = {
    id: randomId(),
    createdAt: now,
    updatedAt: now,
    title: input.title,
    sourceUrl: input.sourceUrl,
    imagePath,
    sourceKind: input.sourceKind ?? (input.tokens ? "live-site" : "screenshot"),
    project: input.project ?? "both",
    notes: input.notes,
    category: input.category,
    tags: input.tags ?? [],
    colors: input.colors ?? derived?.colors ?? [],
    typography: input.typography ?? derived?.typography ?? [],
    layoutNotes: input.layoutNotes ?? derived?.layoutNotes ?? [],
    guardrails: input.guardrails ?? [],
    tokens: input.tokens,
    analysis: {
      status: input.tokens ? "done" : imagePath ? "pending" : "skipped",
      analyzedAt: input.tokens ? now : undefined,
    },
  };
  refs.push(ref);
  await writeAll(refs);
  return ref;
}

export async function getStyleGuide({ project } = {}) {
  const refs = await listReferences({ project });

  const tagCounts = new Map();
  const categoryCounts = new Map();
  const colorCounts = new Map();
  const guardrails = new Set();

  // Measured values are tracked separately from inferred vocabulary so a
  // guessed color is never presented as authoritatively as a read one.
  const fontFamilyCounts = new Map();
  const radiusCounts = new Map();
  const baseUnitCounts = new Map();
  const accentColors = new Set();
  let liveSiteCount = 0;

  for (const r of refs) {
    for (const t of r.tags ?? []) tagCounts.set(t, (tagCounts.get(t) ?? 0) + 1);
    if (r.category) categoryCounts.set(r.category, (categoryCounts.get(r.category) ?? 0) + 1);
    for (const c of r.colors ?? []) colorCounts.set(c, (colorCounts.get(c) ?? 0) + 1);
    for (const g of r.guardrails ?? []) guardrails.add(g);

    if (r.sourceKind === "live-site") liveSiteCount++;
    if (r.tokens) {
      for (const f of r.tokens.fonts ?? []) {
        fontFamilyCounts.set(f.family, (fontFamilyCounts.get(f.family) ?? 0) + 1);
      }
      const radius = r.tokens.spacing?.borderRadius;
      if (radius) radiusCounts.set(radius, (radiusCounts.get(radius) ?? 0) + 1);
      const unit = r.tokens.spacing?.baseUnit;
      if (unit) baseUnitCounts.set(unit, (baseUnitCounts.get(unit) ?? 0) + 1);
      for (const key of ["accent", "link", "secondary"]) {
        const hex = r.tokens.colors?.[key];
        if (hex) accentColors.add(hex);
      }
    }
  }

  const topN = (m, n) => [...m.entries()].sort((a, b) => b[1] - a[1]).slice(0, n);

  return {
    referenceCount: refs.length,
    liveSiteCount,
    topTags: topN(tagCounts, 15).map(([tag, count]) => ({ tag, count })),
    topCategories: topN(categoryCounts, 10).map(([category, count]) => ({ category, count })),
    commonColors: topN(colorCounts, 12).map(([color]) => color),
    guardrails: [...guardrails],
    measured: {
      fontFamilies: topN(fontFamilyCounts, 10).map(([family, count]) => ({ family, count })),
      borderRadii: topN(radiusCounts, 6).map(([value, count]) => ({ value, count })),
      baseUnits: topN(baseUnitCounts, 4).map(([value, count]) => ({ value, count })),
      accentColors: [...accentColors].slice(0, 12),
    },
  };
}
