import { DesignTokens } from "@/lib/types";

function Swatch({ label, hex }: { label: string; hex: string }) {
  return (
    <div className="flex items-center gap-2">
      <span
        aria-hidden
        className="h-6 w-6 shrink-0 rounded border border-black/15"
        style={{ backgroundColor: hex }}
      />
      <span className="font-mono text-xs tabular-nums">{hex}</span>
      <span className="text-xs text-ink/50">{label}</span>
    </div>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-ink/50">{label}</h3>
      {children}
    </div>
  );
}

/**
 * Renders values measured off a live site. Kept visually distinct from the
 * prose vocabulary so it's obvious which numbers are real.
 */
export function TokenPanel({ tokens }: { tokens: DesignTokens }) {
  const colorEntries = Object.entries(tokens.colors ?? {}).filter(([, hex]) => !!hex) as [
    string,
    string
  ][];
  const sizeEntries = Object.entries(tokens.fontSizes ?? {});
  const componentEntries = Object.entries(tokens.components ?? {});

  return (
    <div className="card flex flex-col gap-4 p-5">
      <div className="flex items-baseline justify-between gap-2">
        <h2 className="text-sm font-semibold">Measured tokens</h2>
        <span className="chip">read from the live site</span>
      </div>

      {colorEntries.length > 0 && (
        <Row label="Colors">
          <div className="grid grid-cols-1 gap-1.5 sm:grid-cols-2">
            {colorEntries.map(([role, hex]) => (
              <Swatch key={role} label={role} hex={hex} />
            ))}
          </div>
        </Row>
      )}

      {(tokens.fonts?.length || sizeEntries.length > 0) && (
        <Row label="Type">
          <ul className="space-y-0.5 text-sm text-ink/80">
            {tokens.fonts?.map((f) => (
              <li key={f.family + (f.role ?? "")}>
                <span className="font-medium">{f.family}</span>
                {f.role && <span className="text-ink/50"> — {f.role}</span>}
              </li>
            ))}
            {sizeEntries.map(([step, size]) => (
              <li key={step} className="font-mono text-xs tabular-nums text-ink/70">
                {step}: {size}
              </li>
            ))}
          </ul>
        </Row>
      )}

      {(tokens.spacing?.baseUnit || tokens.spacing?.borderRadius) && (
        <Row label="Spacing">
          <div className="flex flex-wrap gap-1.5">
            {tokens.spacing?.baseUnit && (
              <span className="chip font-mono">{tokens.spacing.baseUnit}px base unit</span>
            )}
            {tokens.spacing?.borderRadius && (
              <span className="chip font-mono">{tokens.spacing.borderRadius} radius</span>
            )}
          </div>
        </Row>
      )}

      {componentEntries.length > 0 && (
        <Row label="Components">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="text-ink/50">
                  <th className="pr-3 font-medium">element</th>
                  <th className="pr-3 font-medium">background</th>
                  <th className="pr-3 font-medium">text</th>
                  <th className="font-medium">radius</th>
                </tr>
              </thead>
              <tbody className="font-mono tabular-nums">
                {componentEntries.map(([name, spec]) => (
                  <tr key={name} className="border-t border-black/5">
                    <td className="py-1 pr-3 font-sans">{name}</td>
                    <td className="py-1 pr-3">{spec.background ?? "—"}</td>
                    <td className="py-1 pr-3">{spec.textColor ?? "—"}</td>
                    <td className="py-1">{spec.borderRadius ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Row>
      )}

      {tokens.personality && (
        <Row label="Reads as">
          <div className="flex flex-wrap gap-1.5">
            {tokens.personality.tone && <span className="chip">{tokens.personality.tone}</span>}
            {tokens.personality.energy && (
              <span className="chip">{tokens.personality.energy} energy</span>
            )}
            {tokens.personality.targetAudience && (
              <span className="chip">{tokens.personality.targetAudience}</span>
            )}
          </div>
        </Row>
      )}

      {typeof tokens.confidence?.overall === "number" && (
        <p className="text-xs text-ink/40">
          Extractor confidence: {Math.round(tokens.confidence.overall * 100)}%
        </p>
      )}
    </div>
  );
}
