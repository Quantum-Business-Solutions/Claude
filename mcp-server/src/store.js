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

  const ref = {
    id: randomId(),
    createdAt: now,
    updatedAt: now,
    title: input.title,
    sourceUrl: input.sourceUrl,
    imagePath,
    project: input.project ?? "both",
    notes: input.notes,
    category: input.category,
    tags: input.tags ?? [],
    colors: input.colors ?? [],
    typography: input.typography ?? [],
    layoutNotes: input.layoutNotes ?? [],
    guardrails: input.guardrails ?? [],
    analysis: { status: imagePath ? "pending" : "skipped" },
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

  for (const r of refs) {
    for (const t of r.tags ?? []) tagCounts.set(t, (tagCounts.get(t) ?? 0) + 1);
    if (r.category) categoryCounts.set(r.category, (categoryCounts.get(r.category) ?? 0) + 1);
    for (const c of r.colors ?? []) colorCounts.set(c, (colorCounts.get(c) ?? 0) + 1);
    for (const g of r.guardrails ?? []) guardrails.add(g);
  }

  const topN = (m, n) => [...m.entries()].sort((a, b) => b[1] - a[1]).slice(0, n);

  return {
    referenceCount: refs.length,
    topTags: topN(tagCounts, 15).map(([tag, count]) => ({ tag, count })),
    topCategories: topN(categoryCounts, 10).map(([category, count]) => ({ category, count })),
    commonColors: topN(colorCounts, 12).map(([color]) => color),
    guardrails: [...guardrails],
  };
}
