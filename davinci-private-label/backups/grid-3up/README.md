# Grids rendering 4+2, and the six that still don't divide evenly

3 September 2026. Raised on a live call: a six-product grid was laying out four on the
first row and two on the second.

## Cause

`PL - Card Grid` has no column-count field. It lays out
`repeat(auto-fit, minmax(min_column_width, 1fr))`, so the number per row falls out of the
arithmetic: N fit when `N*min_column_width + (N-1)*gap <= max_width`.

On the category pages **`min_column_width` was never set**, so the module default of 260px
applied. At `max_width` 1200 and `gap` 24 that fits four, and six products become 4+2.

`fitness` already looked right because it carries 340 - set during an earlier fix - and 340
is the value that forces exactly three: `3*340+2*24 = 1068` fits, `4*340+3*24 = 1432` does not.
Anything from 283 to 384 gives three; 340 sits comfortably in the middle.

## Fixed and published

Seven pages, `min_column_width` set to 340, now 3+3:
detox, weight-management, herbal, immune-support, cognitive, prenatal, joint-support.

## The full audit

All 59 card and tile grids on the site were measured. Six remain uneven and were left alone
because the right answer is a design call, not arithmetic:

| Page | Grid | Renders | Note |
|---|---|---|---|
| how-to-sell | 7 tiles | 6+1 | one stranded tile, the worst of these |
| gummies | 7 tiles | 6+1 | same |
| sleep | 5 products | 4+1 | stranded |
| testing | 4 cards | 3+1 | stranded |
| heart-health | 7 products | 4+3 | reads fine |
| (home) | 7 category tiles | 4+3 | reads fine |

`grid-audit.json` holds the raw measurements.

## Watch for

The same unset-field pattern is likely elsewhere in the theme: a module whose behaviour comes
from a default rather than an explicit value looks correct until content length changes. When
a layout looks wrong, check whether the controlling field is set at all before assuming the
value is wrong.
