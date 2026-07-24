import { StyleGuide } from "@/lib/types";

export function StyleGuidePanel({ guide }: { guide: StyleGuide }) {
  if (guide.referenceCount === 0) {
    return (
      <div className="card p-5 text-sm text-ink/60">
        No references saved yet — once you save a few, this panel will summarize the taste
        vocabulary Claude will draw on (common tags, colors, type, and guardrails).
      </div>
    );
  }

  return (
    <div className="card grid gap-5 p-5 sm:grid-cols-2">
      <div>
        <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink/50">
          Top tags · {guide.referenceCount} references
        </h2>
        <div className="flex flex-wrap gap-1.5">
          {guide.topTags.map(({ tag, count }) => (
            <span key={tag} className="chip">
              {tag} <span className="ml-1 text-ink/40">{count}</span>
            </span>
          ))}
        </div>
      </div>
      <div>
        <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink/50">Categories</h2>
        <div className="flex flex-wrap gap-1.5">
          {guide.topCategories.map(({ category, count }) => (
            <span key={category} className="chip">
              {category} <span className="ml-1 text-ink/40">{count}</span>
            </span>
          ))}
        </div>
      </div>
      {guide.commonColors.length > 0 && (
        <div>
          <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink/50">
            Recurring colors
          </h2>
          <div className="flex flex-wrap gap-1.5">
            {guide.commonColors.map((c) => (
              <span key={c} className="chip font-mono">
                {c}
              </span>
            ))}
          </div>
        </div>
      )}
      {guide.guardrails.length > 0 && (
        <div>
          <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink/50">
            Guardrails
          </h2>
          <ul className="list-inside list-disc space-y-0.5 text-sm text-ink/80">
            {guide.guardrails.slice(0, 8).map((g) => (
              <li key={g}>{g}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
