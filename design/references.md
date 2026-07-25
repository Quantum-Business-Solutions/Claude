# Design references

Sites worth drawing on. Entry shape is fixed by `design/SCHEMA.md` — conform to it so entries stay
comparable. Hand-editing is fine and expected; you don't need Claude, a server, or a database.

Where a `tokens:` line is present, those values were **measured** off the live page. Everything in
the prose is judgement. Keep the judgement specific: name the move, not the mood.

---

## Linear

- **url:** https://linear.app
- **tokens:** `design/tokens/linear.json`
- **tags:** minimal, dark-mode, restrained-motion, product-led
- **category:** SaaS product marketing

The reference point for restrained dark product marketing: near-black ground, a single indigo link
accent, almost no decoration — hierarchy carried entirely by type weight and spacing. The detail
worth stealing is the radius tension: 2px on surfaces against fully-rounded buttons, so the pills
read as a decision rather than a global setting.

## Stripe

- **url:** https://stripe.com
- **tokens:** `design/tokens/stripe.json`
- **tags:** trust-first, light-ground, single-accent, enterprise
- **category:** B2B fintech / trust-first

How to look credible to a procurement panel without looking dull: white ground, near-black text,
one confident indigo reserved for links and the primary CTA. Söhne rather than a system sans is a
large part of why it reads bespoke instead of bootstrapped.

## Orbit Media Studios

- **url:** https://www.orbitmedia.com
- **tokens:** `design/tokens/orbitmedia.json`
- **tags:** agency-peer, warm-accent, condensed-headings, credibility-first
- **category:** Consulting / professional services

The closest live peer to QBS's own positioning — a Chicago web design and digital marketing agency.
Warm brick accent instead of default tech blue, condensed headings against a regular body face, and
a 4px base unit that runs tighter than the usual 8px agency template. The most directly applicable
reference here for QBS client homepages.

## Vercel

- **url:** https://vercel.com
- **tokens:** `design/tokens/vercel.json`
- **tags:** monochrome, type-led, tailwind, developer-audience
- **category:** Developer platform marketing

Carries the whole page on type and a near-black accent (`#171717`) with essentially no color — the
64px/56px scale against 16px body does the work. Useful proof that "no color" is a viable direction
rather than a missing decision. Built on Tailwind with a 4px base unit.

Two measured values to read carefully: the button radius came back as `33554400px`, which is a
browser-computed artifact meaning "fully rounded" rather than a usable token — treat it as
`9999px`. And the captured `link: #9A050F` (dark red) doesn't match the site's visible link
treatment; it's likely an incidental or state-specific capture. The `accent` and `background` are
the trustworthy reads here.

## Basecamp

- **url:** https://basecamp.com
- **tokens:** `design/tokens/basecamp.json`
- **tags:** text-forward, warm, opinionated-voice, high-body-size
- **category:** B2B SaaS, voice-led

The counterexample to screenshot-forward SaaS: no product chrome in the hero, just an argument in
large type. The 20px body size is the notable decision — nearly a third larger than the 15–16px
default, which is what makes long-form copy on a B2B page actually readable. Blue primary with a
green secondary, on a barely-tinted blue-white ground rather than pure white.

Type sizes came back fractional (`55.87px`, `20.32px`) because the site uses a fluid/responsive
scale — those are the values at the measured viewport, not authored numbers. Read them as ratios.

## GOV.UK

- **url:** https://www.gov.uk
- **tokens:** `design/tokens/gov.json`
- **tags:** accessibility-first, zero-radius, high-contrast, public-sector
- **category:** Public service / clarity extreme

The clarity extreme, and valuable precisely as a counterweight: `0px` radius everywhere, `#0B0C0C`
on white, 19px body, and a green primary action that never competes with anything else on the page.
When a client's audience is genuinely broad or the content is genuinely procedural, this is the
register — and it's a reminder that most "sophisticated" styling is optional.

The `link: #FFDD00` capture is real and worth knowing: that yellow is GOV.UK's focus-state
highlight, one of the most-copied accessibility patterns in web design. It's a focus color, not a
link color.

---

## Candidates not yet adopted

Two review boards were assembled earlier and never approved into this list — 18 references by page
type (pricing, dashboard, proposal, case study, team, blog, contact) and 10 by aesthetic family
(award-winning, minimal, brutalist, dark, maximalist). They live as published artifacts, not in this
repo. To adopt any of them, find the design's **live site**, drop it in `design/inbox.md`, and run
`/design-ingest`. See the sourcing section of `design/guardrails.md` for why the gallery images
themselves aren't stored here.
