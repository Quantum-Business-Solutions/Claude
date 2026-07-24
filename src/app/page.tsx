import { getStyleGuide, listReferences } from "@/lib/db";
import { ReferenceCard } from "@/components/ReferenceCard";
import { StyleGuidePanel } from "@/components/StyleGuidePanel";

export const dynamic = "force-dynamic";

export default async function GalleryPage({
  searchParams,
}: {
  searchParams: { project?: string; category?: string; tag?: string; q?: string };
}) {
  const filter = {
    project: searchParams.project,
    category: searchParams.category,
    tag: searchParams.tag,
    q: searchParams.q,
  };
  const [references, guide] = await Promise.all([listReferences(filter), getStyleGuide(filter)]);

  return (
    <main className="flex flex-col gap-8">
      <section>
        <p className="mb-6 max-w-2xl text-sm text-ink/60">
          Designs we&apos;ve saved because we liked something about them — and the style
          vocabulary Claude extracts from each one, so QBS website and client work can draw on a
          consistent, professional taste rather than one-off guesses.
        </p>
        <StyleGuidePanel guide={guide} />
      </section>

      <section>
        <form className="mb-4 flex flex-wrap gap-2 text-sm" method="get">
          <select
            name="project"
            defaultValue={searchParams.project ?? ""}
            className="rounded-lg border border-black/10 bg-white px-3 py-1.5"
          >
            <option value="">All projects</option>
            <option value="qbs">QBS client work</option>
            <option value="personal">Personal</option>
            <option value="both">Both</option>
          </select>
          <input
            type="text"
            name="tag"
            placeholder="filter by tag"
            defaultValue={searchParams.tag ?? ""}
            className="rounded-lg border border-black/10 bg-white px-3 py-1.5"
          />
          <input
            type="text"
            name="category"
            placeholder="filter by category"
            defaultValue={searchParams.category ?? ""}
            className="rounded-lg border border-black/10 bg-white px-3 py-1.5"
          />
          <input
            type="text"
            name="q"
            placeholder="search"
            defaultValue={searchParams.q ?? ""}
            className="rounded-lg border border-black/10 bg-white px-3 py-1.5"
          />
          <button className="rounded-lg bg-ink px-3 py-1.5 text-white" type="submit">
            Filter
          </button>
        </form>

        {references.length === 0 ? (
          <div className="card p-8 text-center text-sm text-ink/60">
            Nothing here yet.{" "}
            <a href="/upload" className="underline">
              Save your first reference
            </a>
            .
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {references.map((ref) => (
              <ReferenceCard key={ref.id} reference={ref} />
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
