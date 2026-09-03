# PREXERA -> PRAXERA, alt text only

Applied 3 September 2026, 14:54 UTC.

## What was wrong

The brand name is misspelled **PREXERA** in 17 files in the HubSpot File Manager,
uploaded in three batches:

| when | files | what |
|---|---|---|
| 4 Aug 2026, 16:03-17:08 | 10 | category tiles and home page images |
| 7 Aug 2026, 18:45 | 1 | `prexera-pl-bottle-light` (unused) |
| 11 Aug 2026, 18:39-18:42 | 6 | icon SVGs (all unused) |

The 4 August batch went up **roughly three hours before** Sarah spelled the name out
letter by letter on that afternoon's call ("P-R-A-X-E-R-A", 19:45 UTC). The images were
produced from the name as heard, and nobody renamed them afterwards.

## What was fixed

Five `alt` values, the only place the misspelling was read by anything that matters -
screen readers and Google Images.

| page | before | after |
|---|---|---|
| `(home)` | `vitamin-manufacturer-prexera` | `vitamin-manufacturer-praxera` |
| `(home)` | `prexera` | `praxera` |
| `(home)` | `prexera-shipping` | `praxera-shipping` |
| `dropshipping` | `prexera-shipping` | `praxera-shipping` |
| `multivitamin` | `vitamin-manufacturer-prexera` | `vitamin-manufacturer-praxera` |

Only the spelling changed. The wording was left exactly as it was, including
"manufacturer", which belongs to Sarah's separate manufacturing-language decision and
is not ours to reword here.

Verified after the write: zero misspelled `alt` values across all 63 drafts, all `src`
URLs unchanged (10, 1 and 8 references on the three pages), and the images still return
HTTP 200.

## What was deliberately NOT changed

**The 147 `src` references on 22 pages, and the CSS selectors in `headHtml`.** These are
not typos in our copy - they are the real names of the real files. Renaming a file in
HubSpot changes its URL, so a rename breaks every reference until all of them are updated
in the same pass, and the theme's `headHtml` also targets those exact names:

```
img[src*="WOMENS-CATEGORY-PREXERA"], img[src*="PREXERA-MENS"],
img[src*="prexera-probiotic"], img[src*="sleep-prexera"]
```

Doing that safely means: upload correctly-named copies, repoint all 22 pages and the CSS,
confirm every image still resolves, then delete the originals. That is a coordinated job,
not a find-and-replace, and it should not run while someone else is editing the same pages.
Impact if it is never done: the misspelling shows in the page source and in image-search
filenames. It is invisible on the rendered page.

Seven of the 17 files (`prexera-pl-bottle-light` and the six icon SVGs) are referenced by
no page at all and can be renamed or removed with zero risk whenever the rest is tackled.

## Concurrency

Barb was editing other pages throughout (Custom Formulation sweep). The three pages touched
here were last edited 40 to 69 minutes earlier and were not among the ones she was working.
Each was re-read immediately before its write.
