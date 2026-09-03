# Baseline before the blog remediation

Captured 3 September 2026, before touching anything, so that "we did not break DaVinci or
Pet Tech" can be **proved** rather than asserted. Post count plus a content signature
(id, name, author, state for every post, hashed) per blog.

| Blog | Posts | Signature |
|---|---|---|
| DaVinci Blog | 534 | `4f58acb68189` |
| DaVinci PL Blog | 75 | `b5531c0affe9` |
| Pet Tech Labs | 67 | `b28fc7b19418` |
| Protocol Guide | 5 | `deb4f0cd6efd` |
| VetriScience | 1 | `7f085e19c98c` |
| Learning Center | 1 | `9c0f0a8c31cd` |

Re-run the snapshot after any blog work and compare. A changed hash means something outside
Praxera moved.

## Why this matters here

The three DaVinci author records are **shared**, not Praxera's own:

| Author record | DaVinci Blog | DaVinci PL | Protocol Guide | Praxera |
|---|---|---|---|---|
| DaVinci Healthcare Expert | 247 | 13 | 5 | 13 |
| DaVinci Industry Expert | - | 1 | - | 1 |
| Dom Orlandi, President of DaVinci | 6 | 1 | - | 1 |

Renaming them to clear DaVinci from Praxera's 15 posts would rewrite the byline on **273
DaVinci posts**. The safe route is new Praxera author records with only the 15 Praxera posts
repointed. Same class of mistake as the path-only redirect that leaked to two other brands
earlier today - on this portal, always check whether an object is shared before editing it.
