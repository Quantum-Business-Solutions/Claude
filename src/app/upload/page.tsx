"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

type Mode = "url" | "screenshot";

export default function UploadPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("url");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submitUrl(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    const form = new FormData(e.currentTarget);
    const tags = String(form.get("tags") ?? "")
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);
    const guardrails = String(form.get("guardrails") ?? "")
      .split("\n")
      .map((g) => g.trim())
      .filter(Boolean);

    try {
      const res = await fetch("/api/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: form.get("url"),
          project: form.get("project"),
          notes: form.get("notes") || undefined,
          category: form.get("category") || undefined,
          tags,
          guardrails,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "failed to read that site");
      router.push(`/references/${data.reference.id}`);
      router.refresh();
    } catch (err) {
      setError((err as Error).message);
      setSubmitting(false);
    }
  }

  async function submitScreenshot(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch("/api/references", {
        method: "POST",
        body: new FormData(e.currentTarget),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "failed to save reference");
      router.push(`/references/${data.reference.id}`);
      router.refresh();
    } catch (err) {
      setError((err as Error).message);
      setSubmitting(false);
    }
  }

  const field = "rounded-lg border border-black/10 px-3 py-2";

  return (
    <main className="mx-auto max-w-xl">
      <h1 className="mb-1 text-xl font-semibold">Save a reference</h1>
      <p className="mb-5 text-sm text-ink/60">
        Analyzing a live URL is the better path — it reads the real colors, fonts, sizes, radii,
        and component specs off the rendered page instead of guessing from a picture. Use a
        screenshot when the design isn&apos;t a site you can reach.
      </p>

      <div className="mb-5 flex gap-1 rounded-lg border border-black/10 bg-white p-1 text-sm">
        <button
          onClick={() => setMode("url")}
          className={`flex-1 rounded-md px-3 py-1.5 ${mode === "url" ? "bg-ink text-white" : "text-ink/70"}`}
          type="button"
        >
          Analyze a live URL
        </button>
        <button
          onClick={() => setMode("screenshot")}
          className={`flex-1 rounded-md px-3 py-1.5 ${mode === "screenshot" ? "bg-ink text-white" : "text-ink/70"}`}
          type="button"
        >
          Upload a screenshot
        </button>
      </div>

      {mode === "url" ? (
        <form onSubmit={submitUrl} className="card flex flex-col gap-4 p-6">
          <label className="flex flex-col gap-1 text-sm">
            Site URL
            <input
              name="url"
              type="url"
              required
              placeholder="https://linear.app"
              className={field}
            />
            <span className="text-xs text-ink/50">
              The live site itself, not a gallery listing of it.
            </span>
          </label>

          <label className="flex flex-col gap-1 text-sm">
            Where does this apply?
            <select name="project" defaultValue="both" className={field}>
              <option value="both">Both QBS + personal</option>
              <option value="qbs">QBS client work</option>
              <option value="personal">Personal</option>
            </select>
          </label>

          <label className="flex flex-col gap-1 text-sm">
            Category
            <input name="category" placeholder="e.g. SaaS landing page" className={field} />
          </label>

          <label className="flex flex-col gap-1 text-sm">
            Tags (comma separated)
            <input name="tags" placeholder="minimal, dark-mode, editorial" className={field} />
          </label>

          <label className="flex flex-col gap-1 text-sm">
            Why are you saving it?
            <textarea name="notes" rows={2} className={field} />
          </label>

          <label className="flex flex-col gap-1 text-sm">
            Guardrails (one per line)
            <textarea
              name="guardrails"
              rows={2}
              placeholder={"never center long body copy\nkeep one saturated accent"}
              className={field}
            />
          </label>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="rounded-lg bg-ink px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {submitting ? "Reading the site…" : "Analyze and save"}
          </button>
        </form>
      ) : (
        <form
          onSubmit={submitScreenshot}
          className="card flex flex-col gap-4 p-6"
          encType="multipart/form-data"
        >
          <label className="flex flex-col gap-1 text-sm">
            Title
            <input name="title" required className={field} />
          </label>

          <label className="flex flex-col gap-1 text-sm">
            Screenshot
            <input name="image" type="file" accept="image/*" className="text-sm" />
            <span className="text-xs text-ink/50">
              Your own screenshot, kept for private reference.
            </span>
          </label>

          <label className="flex flex-col gap-1 text-sm">
            Source URL
            <input name="sourceUrl" className={field} />
          </label>

          <label className="flex flex-col gap-1 text-sm">
            Where does this apply?
            <select name="project" defaultValue="both" className={field}>
              <option value="both">Both QBS + personal</option>
              <option value="qbs">QBS client work</option>
              <option value="personal">Personal</option>
            </select>
          </label>

          <label className="flex flex-col gap-1 text-sm">
            Category
            <input name="category" placeholder="e.g. pricing page" className={field} />
          </label>

          <label className="flex flex-col gap-1 text-sm">
            Tags (comma separated)
            <input name="tags" className={field} />
          </label>

          <label className="flex flex-col gap-1 text-sm">
            Why are you saving it?
            <textarea name="notes" rows={3} className={field} />
          </label>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="rounded-lg bg-ink px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {submitting ? "Saving…" : "Save reference"}
          </button>
        </form>
      )}
    </main>
  );
}
