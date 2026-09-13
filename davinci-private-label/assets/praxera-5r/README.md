# Praxera 5R Gut Health Protocol — rebuild

Rebuilt from the DaVinci Laboratories original (`5Rs-Design-B (1).pdf`, HubSpot file,
3 Apr 2026) because the original is DaVinci-branded end to end and is linked from a live
Praxera email (220685976492, "Download the 5R Framework Quick Deploy Kit").

**Not uploaded to HubSpot. Not linked from any email. Awaiting sign-off.**

## Build
`build.py` emits `praxera-5r.source.html` (self-contained, images inlined as data URIs);
Playwright prints it to PDF at 11in x 8.5in landscape, matching the original page size
exactly (792 x 612 pt).

Rebuilt as HTML->PDF rather than image generation so every character is real, selectable,
searchable text. An image model garbles dense body copy and the 16 product names.

## What changed vs the original
| | Original | Rebuild |
|---|---|---|
| Logo | DaVinci Laboratories | praxera |
| Intro | "match DaVinci's digestive health products" | "match Praxera's ..." |
| Footer | DAVINCILABS.COM | PRAXERASUPPLEMENTS.COM |
| Centre photo | DaVinci bottles, labels readable (G.I. BENEFITS, CLEAR G.I., VIRA-SHIELD) | generated Praxera-format containers, blank labels, green accent stripe |

Everything else is byte-identical. A text diff of the two PDFs returns exactly one
changed word: DaVinci -> Praxera. All 5 step descriptions, all 16 product names, the ™/®
marks (6 and 1) and the FDA disclaimer carry over unchanged.

Product names were kept deliberately (Shawn, 13 Sep): these are the same formulas, now
sold under Praxera.

## Assets
- `art-capsules.png`, `art-leaf.png`, `art-microbiome.png` — decorative photography
  extracted from the original PDF. Generic imagery, no DaVinci branding, owned by
  FoodScience LLC which owns both brands.
- `product-shot-generated.png` — generated (Fal flux-pro v1.1) to replace the DaVinci
  bottle photo. Labels are deliberately blank.

## Known cosmetic differences
The original's ring is an organic composition of overlapping blobs at varying radii; the
rebuild uses an even five-segment ring. Same information, same order, same colours,
slightly more geometric. Flag if the client wants the looser original treatment.
