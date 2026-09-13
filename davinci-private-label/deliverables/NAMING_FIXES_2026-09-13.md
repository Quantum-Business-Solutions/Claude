# Praxera — naming corrections
**13 Sep 2026 · portal 4087538** · before-states in `backups/foodscience-naming/`,
`backups/praxera-laboratories/`, `backups/berberine-sell-sheet/`

## 1. "FoodScience" — corrected to the entity name
Sarah Miller's standing rule: *"Update all instances of FoodScience Corp to FoodScience LLC."*

| Asset | Was | Now |
|---|---|---|
| Email 220688836168 *Danielle: DV Mission & Register* | FoodScience® Corporation | FoodScience LLC |
| Email 220688836170 *Paul: DV Mission & Register* | FoodScience® Corporation | FoodScience LLC |
| Email 220685976504 *Client_Onboarding_BoF_Danielle_#4* | FoodScience® | FoodScience LLC |
| Post 220637279576 *why-branded-ingredients…* | FoodScience® LLC | FoodScience LLC |
| Page `certifications` | "FoodScience is registered with the FDA…" | "FoodScience LLC is registered…" |
| Page `about` | "FoodScience operates multiple manufacturing facilities" | "FoodScience LLC operates…" |

Pages were pushed live; emails remain DRAFT; the post was pushed live.
Left alone deliberately: "Part of the FoodScience family." and "the FoodScience family of
companies" on `/about` — collective phrasing, not an entity claim.

## 2. "Praxera Laboratories" / "Praxera Labs" — the entity does not exist
All 7 occurrences across 5 assets now read **Praxera**.

| Asset | Was | Now |
|---|---|---|
| Email 220685976504 (×2) | Praxera® Laboratories | Praxera |
| Email 220688836176 (×2) | Praxera® Laboratories | Praxera |
| Post 220637272691 | Praxera Lab's existing stock formulations | Praxera's existing stock formulations |
| Post 220637279555 | Praxera Lab's | Praxera's |
| Post 220637272677 | At Praxera® Labs, | At Praxera, |

Posts pushed live; emails remain DRAFT. A portal-wide re-scan of all 111 emails, 68 pages
and 72 posts returns **zero** remaining bad-naming variants of either kind.

## 3. Berberine Force sell sheet — DaVinci removed, pixel-for-pixel
`Berberine_Force_Sell_Sheet.pdf` (HubSpot file 221631457543) read *"DaVinci® formulated this
product to include a stable, water soluble version of folate."* No DaVinci original of this
sheet exists in the portal — Justin built it on 11 Sep and the DaVinci mention came across
with the source copy.

Rather than rebuild the page, the single word was replaced **in place**: the embedded
`UniversLTStd-Cn` font was extracted from the PDF itself, the old word redacted, and
"Praxera" re-set at the same baseline, size (8.97pt) and colour, tracked so the line occupies
the original 34.93pt and does not reflow. Everything else in the file is untouched.
Before/after at `reports/berberine-davinci-fix.png`. Uploaded and verified live.

## 4. FDA disclaimer — checked against the originals, no action needed
Shawn's instruction was to match whatever the DaVinci originals did.

| Praxera guide | DaVinci original | Original has disclaimer? | Praxera has it? | Verdict |
|---|---|---|---|---|
| Praxera-Private-Label-Guide (27pp) | DaVinci-Laboratories-Private-Label-Guide (27pp) | **No** | No | matches — leave |
| Praxera-Client-Onboarding (13pp) | PTL_clientOnboarding_2024 (13pp) | **No** | No | matches — leave |
| Praxera-Ingredients-Guide | DaVinci-Labs-Private-Label-Ingredients-Certifications-Guide | Yes | Yes | matches |

All 15 sell sheets carry it. Nothing to change.
