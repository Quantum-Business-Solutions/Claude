"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function ReferenceActions({ id, hasImage }: { id: string; hasImage: boolean }) {
  const router = useRouter();
  const [busy, setBusy] = useState<"analyze" | "delete" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function reanalyze() {
    setBusy("analyze");
    setError(null);
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id }),
    });
    const data = await res.json();
    if (!res.ok) setError(data.error ?? "analysis failed");
    setBusy(null);
    router.refresh();
  }

  async function remove() {
    if (!confirm("Remove this reference from the taste library?")) return;
    setBusy("delete");
    await fetch(`/api/references/${id}`, { method: "DELETE" });
    router.push("/");
    router.refresh();
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex gap-2">
        {hasImage && (
          <button
            onClick={reanalyze}
            disabled={busy !== null}
            className="rounded-lg border border-black/10 bg-white px-3 py-1.5 text-sm disabled:opacity-50"
          >
            {busy === "analyze" ? "Analyzing…" : "Re-analyze"}
          </button>
        )}
        <button
          onClick={remove}
          disabled={busy !== null}
          className="rounded-lg border border-black/10 bg-white px-3 py-1.5 text-sm text-red-600 disabled:opacity-50"
        >
          {busy === "delete" ? "Removing…" : "Remove"}
        </button>
      </div>
      {error && <p className="text-sm text-red-500">{error}</p>}
    </div>
  );
}
