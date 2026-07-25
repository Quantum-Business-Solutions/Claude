import { notFound } from "next/navigation";
import { getReference } from "@/lib/db";
import { ReferenceActions } from "@/components/ReferenceActions";
import { TokenPanel } from "@/components/TokenPanel";

export const dynamic = "force-dynamic";

function VocabList({ label, items }: { label: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div>
      <h2 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-ink/50">{label}</h2>
      <ul className="list-inside list-disc space-y-0.5 text-sm text-ink/80">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

export default async function ReferenceDetailPage({ params }: { params: { id: string } }) {
  const ref = await getReference(params.id);
  if (!ref) notFound();

  return (
    <main className="mx-auto grid max-w-4xl gap-8 sm:grid-cols-2">
      <div>
        {ref.imagePath ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={ref.imagePath} alt={ref.title} className="w-full rounded-2xl border border-black/10" />
        ) : (
          <div className="card flex aspect-[4/3] items-center justify-center text-sm text-ink/40">
            no image saved
          </div>
        )}
      </div>

      <div className="flex flex-col gap-5">
        <div>
          <div className="mb-1 flex flex-wrap items-center gap-2">
            <h1 className="text-xl font-semibold">{ref.title}</h1>
            <span className="chip capitalize">{ref.project}</span>
            {ref.sourceKind === "live-site" && <span className="chip">live site</span>}
          </div>
          {ref.category && <p className="text-sm text-ink/60">{ref.category}</p>}
          {ref.sourceUrl && (
            <a href={ref.sourceUrl} target="_blank" rel="noreferrer" className="text-sm text-ink/60 underline">
              {ref.sourceUrl}
            </a>
          )}
        </div>

        {ref.notes && (
          <div>
            <h2 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-ink/50">
              Why we saved it
            </h2>
            <p className="text-sm text-ink/80">{ref.notes}</p>
          </div>
        )}

        {ref.tags.length > 0 && (
          <div>
            <h2 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-ink/50">Tags</h2>
            <div className="flex flex-wrap gap-1.5">
              {ref.tags.map((t) => (
                <span key={t} className="chip">
                  {t}
                </span>
              ))}
            </div>
          </div>
        )}

        {ref.tokens ? (
          <TokenPanel tokens={ref.tokens} />
        ) : (
          <>
            <VocabList label="Colors" items={ref.colors} />
            <VocabList label="Typography" items={ref.typography} />
            <VocabList label="Layout notes" items={ref.layoutNotes} />
          </>
        )}
        <VocabList label="Guardrails" items={ref.guardrails} />

        {ref.analysis.status === "pending" && (
          <p className="text-sm italic text-ink/40">Analyzing…</p>
        )}
        {ref.analysis.status === "skipped" && (
          <p className="text-sm text-ink/40">
            No auto-analysis yet — set <code className="chip">ANTHROPIC_API_KEY</code> and re-analyze, or fill in
            vocabulary manually via the API.
          </p>
        )}
        {ref.analysis.status === "error" && (
          <p className="text-sm text-red-500">Analysis failed: {ref.analysis.error}</p>
        )}

        <ReferenceActions id={ref.id} hasImage={!!ref.imagePath} />
      </div>
    </main>
  );
}
