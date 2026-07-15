# QBS Brand Guidelines (for audit deliverable)

For use when producing the client-mode Word deliverable.

## Colors

| Element | Color | Hex | RGB |
|---------|-------|-----|-----|
| Primary (headers, accents) | Dark Navy | `#0A1F44` | 10, 31, 68 |
| Secondary accent | Gold | `#C9A227` | 201, 162, 39 |
| Body text | Near-black | `#1A1A1A` | 26, 26, 26 |
| Muted text (captions, footers) | Slate | `#5A6470` | 90, 100, 112 |
| Rule lines, table borders | Light gray | `#D8DDE3` | 216, 221, 227 |
| Severity: Critical | Deep red | `#8B1E1E` | 139, 30, 30 |
| Severity: High | Amber | `#B5761F` | 181, 118, 31 |
| Severity: Medium | Gold | `#C9A227` | 201, 162, 39 |
| Severity: Low | Slate | `#5A6470` | 90, 100, 112 |
| Scoreboard fill | Gold with navy outline | see above | — |

Use navy and gold sparingly. The document should feel premium, not busy.

## Typography

- **Body:** Calibri 11pt, 1.15 line spacing
- **H1 (section headers):** Calibri Bold 18pt, navy, 12pt before / 6pt after
- **H2 (subsection):** Calibri Bold 14pt, navy, 10pt before / 4pt after
- **H3 (finding title):** Calibri Bold 11pt, navy, 6pt before
- **Caption/footer:** Calibri 9pt, slate
- **Code/monospace (for query snippets):** Consolas 10pt, on light gray (`#F4F5F7`) background

If Calibri is unavailable, fall back to Arial or Liberation Sans. Do not use Times New Roman or any serif for body.

## Layout

- Page size: US Letter (8.5 × 11 in)
- Margins: 1 in top/bottom, 0.9 in left/right
- Footer: "Quantum Business Solutions | Confidential" left-aligned, page number right-aligned, separated from body by a thin gold (0.5pt) rule
- Header: blank on body pages; cover page has the logo lockup

## Cover page

- Top: QBS logotype (if no image file available, text treatment: "QUANTUM BUSINESS SOLUTIONS" tracked out in navy, with a gold rule underneath)
- Centered block at vertical ~45%:
  - "HubSpot Portal Audit" (H1, navy, centered)
  - Client name (H2, navy, centered)
  - Date (caption, slate, centered)
- Bottom: "Prepared by Quantum Business Solutions" (caption, slate, centered)

## Scoreboard visual

Preferred: horizontal bar chart (one bar per dimension, 0–100 scale).

Fallback: table with filled-cell visual:

```
Data Health      ████████░░░░░░░  52/100  Degraded
Architecture     ██████████████░  78/100  Good
...
```

Using Unicode block characters in a fixed-width font cell works well. Navy fill characters on light gray track.

## Severity badges

Inline next to finding titles. Small rounded rectangle (or table cell), colored from severity palette above, white text, 9pt bold:

- `[ CRITICAL ]`
- `[ HIGH ]`
- `[ MEDIUM ]`
- `[ LOW ]`

In plain Word, approximate with a 1-row single-cell table with solid fill and white text.

## Footer text rules

- Every body page: "Quantum Business Solutions | Confidential"
- Appendix pages: "Quantum Business Solutions | Confidential | Appendix"
- Cover page: no footer

## What not to do

- No rainbow colors in charts. Navy + gold + severity scale only.
- No gradients or shadows on text.
- No background images or watermarks.
- No decorative dividers (stars, geometric shapes). Thin gold rule lines only.
- No emoji.
- No multiple fonts on one page (beyond body + headers + code).
- No centered body copy. Left-align everything except cover page titles.

## File naming

`{client_slug}_hubspot_audit_{YYYY-MM-DD}.docx`

Example: `connect_the_office_hubspot_audit_2026-04-19.docx`

Slug convention: lowercase, underscore-separated, no special characters.
