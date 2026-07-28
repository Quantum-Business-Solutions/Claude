# Guardrails

The accumulated "always / never" list. **Read this before generating any design work** — it's the
highest-value file here, because it's the only one that encodes decisions rather than observations.

A rule earns a place here only if it generalizes past the site it came from. Anything true of just
one reference stays in that entry's prose in `design/references.md`.

## Never

- No purple-to-blue gradient heroes on white. The single most recognizable AI-generated tell.
- No Inter as a default just because it's safe. If Inter is the right call, it should be a call.
- No three-equal-feature-card row as the section after the hero.
- No generic glassmorphism applied to every surface.
- No emoji as section markers.
- No centered long-form body copy — centering is for short display text only.
- Don't soften a tight radius into pill-shaped cards globally. Mixed radii can be deliberate
  (Linear runs 2px surfaces against fully-rounded buttons); a uniform `rounded-lg` everywhere is
  the tell.
- Don't number sections `01 / 02 / 03` unless the content is genuinely sequential.

## Always

- Reserve the accent for links and the primary CTA. If everything is accented, nothing is.
- Pick the neutral deliberately — a grey biased slightly toward the accent hue reads chosen; a pure
  mid-grey reads inherited.
- Pair a display face against a distinct body face. One family at one weight is the boilerplate
  signature. A condensed heading over a regular body (Orbit Media) is a cheap, effective move.
- Let the typeface do brand work. Söhne over a system sans is a large part of why Stripe reads
  bespoke rather than bootstrapped.
- State the design read before building: page kind, audience, aesthetic family. Guessing the
  direction is what produces slop.
- Build wide before going deep — several distinct directions first, then iterate the chosen one.
  Don't one-shot.
- Size body copy for the reading it actually requires. 15–16px is a default, not a decision;
  Basecamp runs 20px and GOV.UK 19px because both expect to be *read*. Long-form B2B copy at 15px
  is a legibility choice made by accident.
- Treat "no color" as an available direction. Vercel carries a whole page on type and a near-black
  accent. Reaching for a palette isn't automatically the richer choice.
- Match register to audience breadth. A broad or procedural audience wants the GOV.UK register —
  zero radius, maximum contrast, one unmistakable action — and most "sophisticated" styling is
  optional there.

## Matching the medium to the reference

- **Don't approximate a render.** If a reference's quality comes from 3D rendering — soft shadows,
  ambient occlusion, beveled edges, material response — flat SVG or CSS polygons will not get close.
  They produce SmartArt: flat slabs, dead flat-fill "metal", and a diagram look. Either use a medium
  that can actually light a surface (WebGL, or a real Blender/Spline render) or pick a different
  concept. A footnote admitting the output is flat does not make shipping it acceptable.
- Corollary: decide the medium *before* building, from what the reference depends on. Getting this
  wrong wastes the whole build, not just the finish.
- Arbitrary decoration is a tell. If a mark can't answer "what does this represent," cut it — small
  accent dots and rings sprinkled on surfaces read as filler, because they are.

## Reading measured tokens

- A radius like `33554400px` means "fully rounded" (browser-computed), not a literal value. Read it
  as `9999px`.
- Fractional type sizes (`55.87px`) mean a fluid/responsive scale measured at one viewport. Read
  them as ratios, not authored numbers.
- Extractors mislabel state colors as base colors. GOV.UK's `link: #FFDD00` is its focus highlight;
  Vercel's `link: #9A050F` doesn't match the visible treatment at all. Sanity-check a color against
  the site before building on it.

## Sourcing

- Ingest **live sites**, not gallery images. A shipped site has survived real content, long copy,
  and responsive breakpoints; a concept shot hasn't.
- Don't store scraped Dribbble content in this repo. Their API can't serve it anyway (every read
  endpoint is scoped to the authenticated user's own shots — no search or browse), and their terms
  are explicit: *"Scraping, copying, saving, or storing our data is strictly prohibited."* This
  library backs commercial client work, so treat that as binding. Browse galleries to **discover**,
  then ingest the real site.
- Never hand-write a value into `design/tokens/`. That directory is the boundary between measured
  and guessed, and it holds only measured. Observations go in prose.
