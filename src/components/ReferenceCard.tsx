import Link from "next/link";
import { DesignReference } from "@/lib/types";

export function ReferenceCard({ reference }: { reference: DesignReference }) {
  return (
    <Link
      href={`/references/${reference.id}`}
      className="card group flex flex-col overflow-hidden transition hover:shadow-md"
    >
      <div className="aspect-[4/3] w-full overflow-hidden bg-black/5">
        {reference.imagePath ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={reference.imagePath}
            alt={reference.title}
            className="h-full w-full object-cover transition group-hover:scale-[1.02]"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-xs text-ink/40">
            no image
          </div>
        )}
      </div>
      <div className="flex flex-1 flex-col gap-2 p-4">
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-sm font-semibold leading-snug">{reference.title}</h3>
          <span className="chip shrink-0 capitalize">{reference.project}</span>
        </div>
        {reference.category && <p className="text-xs text-ink/60">{reference.category}</p>}
        {reference.tags.length > 0 && (
          <div className="mt-auto flex flex-wrap gap-1.5 pt-1">
            {reference.tags.slice(0, 4).map((tag) => (
              <span key={tag} className="chip">
                {tag}
              </span>
            ))}
          </div>
        )}
        {reference.analysis.status === "pending" && (
          <p className="text-xs italic text-ink/40">analyzing…</p>
        )}
        {reference.analysis.status === "error" && (
          <p className="text-xs text-red-500">analysis failed</p>
        )}
      </div>
    </Link>
  );
}
