# Blog remediation — Praxera only

3 September 2026. Three fixes applied to Praxera blog posts. QA'd before and after, with a
baseline proving the other brands did not move.

## Scoping — how DaVinci and Pet Tech were protected

The strings edited here **also exist on the DaVinci PL Blog**, because Praxera's posts were
copied from it:

| String | Also present in |
|---|---|
| `/en/pl-demo-` | nowhere else — Praxera only |
| "We proudly manufacture our supplements" | DaVinci PL Blog, 1 post |
| "in all of our facilities" | DaVinci PL Blog, 2 posts |
| "our Scientific Review Board and NSF GMP 455-2 certified manufacturing" | DaVinci PL Blog, 1 post |
| `dmannose+davinci` | DaVinci PL Blog, 1 post |

**The operation iterated over an explicit list of the 75 Praxera post ids and PATCHed each by
id.** No search-and-replace ran across the portal. A shared string is only dangerous when the
operation is scoped by content — which is exactly how the path-only redirect leaked to two
other brands earlier the same day. Scoping by id is the lesson from that.

## Applied

**47 posts, 73 replacements**, then all 47 republished.

- **69 `/en/pl-demo-*` links → real pages.** guides, about, get-started, resources,
  design-team, design-services, ingredients-testing. These were demo scaffolding that never
  existed and all 404'd, carrying high-intent anchors like "Learn about our private label
  program". **Verified live: 69 → 0.**
- **Three first-person manufacturing sentences**, verified individually on the live pages:
  - "We proudly manufacture our supplements in" → "Our supplements are produced in"
  - "in all of our facilities" → "across every production facility"
  - "…NSF GMP 455-2 certified manufacturing" → "…certified production", and
    "partner with a true nutraceutical manufacturer" → "…nutraceutical provider"
- **One link sending readers to a Google search for "dmannose davinci"** → `/probiotics`.

## Post-QA against the baseline — no collateral damage

| Blog | Posts | Signature |
|---|---|---|
| DaVinci Blog | 534 | unchanged |
| DaVinci PL Blog | 75 | unchanged |
| Pet Tech Labs | 67 | unchanged |
| Protocol Guide | 5 | unchanged |
| VetriScience | 1 | unchanged |
| Learning Center | 1 | unchanged |

## Two QA traps worth remembering

**A looser check than the fix produces false alarms.** The post-QA searched for
"certified manufacturing" and reported 4 hits still present, implying the fix had failed.
Checking the exact sentences on the exact pages showed all three were fixed — the 4 hits were
unrelated text on other posts. Verify with the same specificity you edited with.

**Stored HTML entity-encodes ampersands.** The Google link did not match on the first pass
because the content holds `client=safari&amp;rls=en&amp;q=...` while the plain URL uses `&`.
A regex over the query string caught it. Worth assuming for any href carrying parameters.

## Left alone deliberately

- The same sentences on the DaVinci PL Blog. DaVinci does manufacture; those are true there.
- The 42 broken hero widgets — see `../blog-publish/HERO-WIDGET-FINDING.md`. The API fix is
  proven not to work.
- The three shared DaVinci author records.
