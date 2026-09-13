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

## v2 — ring matched to the original (13 Sep)
The first rebuild used an even five-segment donut. v2 matches the original's composition:
rounded "petal" wedges (corner radius 34 units, 4.2° white gaps), the original's **two**
greens sampled from the source render (`#76BD43` for 01, `#A3D06F` for 04), and a large
centre disc that overlaps the band and sits left of the ring centre, with a thick white
keyline — as in the original. See `reports/praxera-5r-qa-ring.png`.

Text fidelity re-verified after the rebuild: still exactly one changed word
(DaVinci → Praxera), 6 ™ and 1 ® preserved, page size 792 × 612 pt.

## Live as of 13 Sep
- HubSpot file **221802319406**, `/Praxera/Private Label Supplements Guide/`, PUBLIC_INDEXABLE.
- Served (verified 200, 2,738,041 bytes, text confirms Praxera / no DaVinci) at
  `https://www.praxerasupplements.com/hubfs/Praxera/Private%20Label%20Supplements%20Guide/Praxera-5R-Gut-Health-Protocol.pdf`
- Email **220685976492** ("Download the 5R Framework Quick Deploy Kit") repointed from the
  DaVinci PDF to the above. Still DRAFT. Anchor text, subject, sender and all 17 widgets
  unchanged; before-state in `backups/email-5r-pdf/`.

**Note:** the Files API returns this asset's canonical `url` on **www.pettechlabs.com** —
that is the portal's file-hosting domain setting, which we were told not to change. The
same file also serves correctly from the Praxera domain, and that is the URL used in the
email. Worth fixing at the portal level so Praxera assets stop defaulting to a Pet Tech URL.

## v3 — ring is now the original artwork, not a lookalike (13 Sep)
v2 approximated the ring with generated SVG petals. Shawn: "the petals look off... they
arent even like the old one" — correct. The original is not a uniform segmented ring: the
shapes are irregular hand-drawn bezier blobs of different sizes (the 01 blob is 232 x 142pt
and bleeds off the top of the page; the 04 blob is 166 x 207pt).

v3 stops approximating. It renders the original page's own vector artwork at 600 dpi,
crops the ring region (page points 330,0 - 792,372 — above where the column headers begin),
paints out the centre disc, and composites the Praxera product photo into it behind the
same white keyline. The petals, the two greens, the three photographs, the numbers and
their positions are therefore pixel-identical to the source.

`ring-artwork.png` is that composited ring. Only the centre photo differs from the original.

Text fidelity re-verified: still exactly one changed word (DaVinci → Praxera), 6 ™, 1 ®,
792 x 612 pt.

File 221802319406 replaced in place (7,432,041 bytes) and re-verified live on the Praxera
domain. Email 220685976492 needed no further change — it already points at this URL.

## v4 — "YOUR LOGO GOES HERE" on the bottles (13 Sep)
The generated bottles had blank labels. They now carry "YOUR LOGO GOES HERE" in the same
small letter-spaced caps used across the existing Praxera bottle renders (`px-*.png`), so
the guide reads as part of the same private-label mockup family. The text is composited at
4x supersample and auto-fitted to each label's real width, so it sits inside the panel at
every size rather than overflowing.
