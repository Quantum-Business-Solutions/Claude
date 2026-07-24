"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export default function UploadPage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    const formData = new FormData(e.currentTarget);

    try {
      const res = await fetch("/api/references", { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "failed to save reference");
      router.push(`/references/${data.reference.id}`);
      router.refresh();
    } catch (err) {
      setError((err as Error).message);
      setSubmitting(false);
    }
  }

  return (
    <main className="mx-auto max-w-xl">
      <h1 className="mb-1 text-xl font-semibold">Save a reference</h1>
      <p className="mb-6 text-sm text-ink/60">
        Drop in a screenshot of a design you like. If an{" "}
        <code className="chip">ANTHROPIC_API_KEY</code> is configured, Claude will look at it and
        auto-extract the category, colors, type, layout notes, and guardrails for you.
      </p>

      <form onSubmit={handleSubmit} className="card flex flex-col gap-4 p-6" encType="multipart/form-data">
        <label className="flex flex-col gap-1 text-sm">
          Title
          <input name="title" required className="rounded-lg border border-black/10 px-3 py-2" />
        </label>

        <label className="flex flex-col gap-1 text-sm">
          Screenshot
          <input name="image" type="file" accept="image/*" className="text-sm" />
        </label>

        <label className="flex flex-col gap-1 text-sm">
          Source URL
          <input
            name="sourceUrl"
            placeholder="https://dribbble.com/shots/…"
            className="rounded-lg border border-black/10 px-3 py-2"
          />
        </label>

        <label className="flex flex-col gap-1 text-sm">
          Where does this apply?
          <select name="project" defaultValue="both" className="rounded-lg border border-black/10 px-3 py-2">
            <option value="both">Both QBS + personal</option>
            <option value="qbs">QBS client work</option>
            <option value="personal">Personal</option>
          </select>
        </label>

        <label className="flex flex-col gap-1 text-sm">
          Category (optional — Claude will infer if left blank and a screenshot is provided)
          <input
            name="category"
            placeholder="e.g. SaaS landing page"
            className="rounded-lg border border-black/10 px-3 py-2"
          />
        </label>

        <label className="flex flex-col gap-1 text-sm">
          Manual tags (comma separated, optional)
          <input name="tags" placeholder="editorial, bento-grid, dark-mode" className="rounded-lg border border-black/10 px-3 py-2" />
        </label>

        <label className="flex flex-col gap-1 text-sm">
          Why did you save this?
          <textarea
            name="notes"
            rows={3}
            placeholder="What specifically do you like about it?"
            className="rounded-lg border border-black/10 px-3 py-2"
          />
        </label>

        {error && <p className="text-sm text-red-500">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="rounded-lg bg-ink px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {submitting ? "Saving…" : "Save reference"}
        </button>
      </form>
    </main>
  );
}
