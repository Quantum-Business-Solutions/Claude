# Revolution Office logo — closed-circle recreation

Vector recreation of the Revolution Office lockup with the ring **closed** (the
original mark has a gap on the right side of the circle). Text is outlined to
paths, so the SVGs render identically everywhere with no font dependency.

## What's here

| Folder | Contents |
|---|---|
| `horizontal/` | Ring + wordmark side by side (the original arrangement) |
| `stacked/` | Ring centred above the wordmark, for square-ish placements |
| `icon/` | Ring + R only, for favicons, avatars, app tiles |

Each folder has, per colourway:

- `*.svg` — transparent vector master (scale to any size)
- `*_transparent.png` — 2400 px wide PNG with alpha
- `*_bg.png` — same artwork on the intended solid background (white, ink, navy or orange) so light artwork is previewable

## Colourways

| # | Name | Ring / R | Text | Intended background |
|---|---|---|---|---|
| 01 | original-orange-black | `#E8872B` | `#141414` | white |
| 02 | all-black | `#141414` | `#141414` | white |
| 03 | all-white | `#FFFFFF` | `#FFFFFF` | dark |
| 04 | orange-white | `#E8872B` | `#FFFFFF` | dark |
| 05 | navy-orange | `#E8872B` | `#1B2A4A` | white |
| 06 | charcoal-orange | `#E8872B` | `#3A3A3A` | white |
| 07 | all-orange | `#E8872B` | `#E8872B` | white |
| 08 | grey-black | `#8A8F98` | `#141414` | white |
| 09 | teal-black | `#0E8A8A` | `#141414` | white |
| 10 | blue-black | `#1F5FBF` | `#141414` | white |
| 11 | green-black | `#2E8B57` | `#141414` | white |
| 12 | red-black | `#C8402E` | `#141414` | white |
| 13 | orange-on-navy | `#E8872B` | `#FFFFFF` | navy `#1B2A4A` |
| 14 | black-on-orange | `#141414` | `#141414` | orange `#E8872B` |
| 15 | white-on-orange | `#FFFFFF` | `#FFFFFF` | orange `#E8872B` |

Typeface: Montserrat (ExtraBold for REVOLUTION and the R, Bold for OFFICE,
Medium for the tagline). Montserrat is the closest open licence match to the
original's geometric sans and is bundled in `fonts/` under the SIL Open Font
License.

## Regenerating or adding a colourway

```bash
pip install fonttools cairosvg
python3 build_logo.py
```

Add an entry to `VARIANTS` in `build_logo.py` (accent colour, text colour,
preview background) and rerun. Sizes and spacing are the constants at the top
of the script.
