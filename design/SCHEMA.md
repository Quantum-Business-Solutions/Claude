# Ingest contract

The point of this file: **every reference comes out in the same shape, every time.** Without a
fixed contract, each ingest is an improvisation and the library stops being comparable across
entries. Anything that processes `design/inbox.md` must conform to what's below, exactly.

## Slug rule (deterministic — do not improvise)

Take the URL's hostname, drop a leading `www.`, drop the final TLD segment, replace any remaining
non-alphanumeric run with a single hyphen, lowercase.

| URL | slug |
|---|---|
| `https://linear.app` | `linear` |
| `https://stripe.com` | `stripe` |
| `https://www.orbitmedia.com` | `orbitmedia` |
| `https://vercel.com/design` | `vercel` |
| `https://www.gov.uk` | `gov` |

Collision (two URLs, same slug): append `-2`, `-3`, … in ingest order. Never silently overwrite an
existing token file for a different URL.

## `design/tokens/<slug>.json`

Measured values read off the live page. Keys in this order; omit a key entirely when the extractor
returned nothing for it rather than writing `null` or `{}`.

```json
{
  "url": "https://linear.app",
  "measuredAt": "2026-07-25",
  "extractor": "firecrawl/branding",
  "confidence": 0.925,
  "colorScheme": "dark",
  "colors": {
    "primary": "#D0D6E0",
    "secondary": "#E4F222",
    "accent": "#E5E5E6",
    "background": "#08090A",
    "textPrimary": "#08090A",
    "link": "#5E6AD2"
  },
  "fonts": [
    { "family": "Inter", "role": "body" },
    { "family": "SF Pro Display", "role": "heading" }
  ],
  "fontSizes": { "h1": "64px", "h2": "48px", "body": "15px" },
  "spacing": { "baseUnit": 8, "borderRadius": "2px" },
  "components": {
    "buttonPrimary": { "background": "#E5E5E6", "textColor": "#08090A", "borderRadius": "9999px" }
  },
  "personality": { "tone": "modern", "energy": "medium", "targetAudience": "tech-savvy professionals" },
  "framework": "custom"
}
```

Rules:
- `measuredAt` is a plain `YYYY-MM-DD` date. Sites get redesigned; a token file older than ~a year
  should be treated as stale and re-measured rather than trusted.
- `confidence` is the extractor's own `overall` score. Below `0.7`, say so in the reference entry
  instead of quoting the values as fact.
- Never hand-write values into a token file. If it wasn't measured, it doesn't belong here — put
  the observation in `references.md` prose instead. **This file is the boundary between measured
  and guessed, and it only holds measured.**

## `design/references.md` entry

Appended in ingest order, using exactly this shape:

```markdown
## <Name>

- **url:** <url>
- **tokens:** `design/tokens/<slug>.json`   ← omit this line if no tokens were captured
- **tags:** <comma, separated, lowercase-hyphenated>
- **category:** <one short phrase>

<One or two sentences on why it's here. Specific and applicable — name the move, not the mood.
"One accent reserved for links and the primary CTA" is usable; "clean and modern" is not.>
```

## Technique references

Some references are a visual technique, not a site — an illustration style, a motion pattern, a
composition. These live under the `# Technique references` heading in `references.md`, carry a
`source:` line instead of `url:`, and **omit `tokens:` entirely**: the extractor reads CSS and has
nothing to say about a 3D render. The prose carries the whole reference, so it has to be specific
enough to brief or build against — and it should say plainly if the technique has no shipped
examples, since that's a cost signal.

## `design/guardrails.md`

Rules accumulate here, deduplicated, as plain imperative bullets. A guardrail belongs here only if
it generalizes past the one site it came from. Site-specific observations stay in the entry prose.

## Failure handling

Non-negotiable, because a silent failure is worse than no entry: if a URL can't be reached or the
extractor returns nothing usable, leave it in `design/inbox.md` with a `# failed: <reason>` comment
appended to its line. Do not write a partial token file, and do not invent values to fill a gap.
