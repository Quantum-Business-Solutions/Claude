# Praxera website — outstanding changes after the 8 Sep call and Mindy's weekend review

Sources: 8 Sep "PL Website Project Check-in" (transcript), Melinda's 8 Sep email + Design
Approval Sheet v6 (090726), 3 Sep call. Every item below was checked against the live site
on 8 Sep evening; "live now" is what a visitor sees today.

Dates agreed on the call: **soft launch ~14 Sep** (already reachable, nobody pointed at it),
**Regulatory needs one week** on the live-looking site, **public by end of September**.

## Done today
- "Developed by us. Made for you." — one global module on every page with Mindy's text (20 pages converted, 0 inline copies left).
- Dropshipping page — unpublished (draft), as confirmed on both calls.
- Sticky navigation — global header now fixed on scroll with a solid white background (Global Header module.css). Shawn confirmed on screen 8 Sep evening.
- Product links → DaVinci — the "Explore the Product Guide" module on 26 pages now reads "Schedule a Consultation →" and goes to /get-started. Zero pages link to DaVinci for product info.

## Verified already in place (checked 8 Sep evening)
- FDA disclaimer box: one identical version on every page that carries it (58 live pages), and it already begins with `*` as Mindy asked. An earlier draft of this sheet listed it as outstanding; that was a checking error on our side, not a site problem.

## A. Copy and consistency — QBS can do, no client decision needed

| # | Item | Live now | Target (agreed) | Pages |
|---|---|---|---|---|
| A1 | Formulations subheader standard | 5 pages "Our … formulations", 6 pages "Real Praxera … / These are actual products… Browse the full catalog" | Women's Health format: "Praxera's <category> formulations available for private label" / "A selection of our existing <category> supplement line, available for private label today." / "Schedule a consultation for the full catalog and custom options." on its own line | 11: fitness, herbal, aging*, sleep, weight-management, immune-support, cognitive, pediatric, heart-health, detox, energy |
| A2 | Daily Best™ → Daily Best® | 8 mentions use ™ | Keep the ® (Tammy) | womens-health, probiotics, mens-health, prenatal, multivitamin |
| A3 | Fitness product cards | "Vitamin C, B-Complex, Magnesium" card present; no vegan protein | Remove that card, add **Vegan Protein** (keeps 6 cards) | fitness |
| A4 | Placeholder hero subheaders | "…are one of the most consistently in-demand categories in the wellness market…" | Regulatory-approved intro copy lifted from the matching davincilabs.com/shop-supplements page (Tammy approved on call) | 9: multivitamin, immune-support, cognitive, pediatric, joint-support, heart-health, detox, energy, mens-health |
| A5 | Gummies hero image | Off-centre | Centre the gummy | gummies |
| A6 | Orphan single words on second line of headlines | Mindy adjusted several by hand | QA pass that nothing broke; fix stragglers by font size, not copy | site-wide |

\*Aging: Mindy believed she fixed it; HubSpot still holds "Our aging formulations". Her edit did not save.

## B. Needs a decision or content from the client

| # | Item | Why it's open |
|---|---|---|
| B1 | **"and more" tile** on home and how-to-sell | Isn't a link at all (Tammy noticed 3 Sep). Obvious destination is the same one the product-guide link now uses: /get-started |
| B2 | **Steps section: numbers or icons, not both** | Shawn's call; needs the page pointed out — the module is global |
| B3 | **Fish Oils & Omega category page** | Mindy recommends adding; new page, new copy |
| B4 | **Tagline under Praxera** | Marketing decision. Options from Taylor in Mindy's email: "Helping Practices Build More Than Patient Loyalty" / "Applied Expertise. Built for Your Brand." / "Expert Formulations. Your Brand." |
| B5 | **FAQ answer** on 17 category pages still says "we handle production… we produce" | Approval sheet ready (`faq-manufacturing-wording-for-approval.md`) |
| B6 | **TY: Sell Sheets** page — "NEED INFO"; **Ingredient Sourcing** — "In Progress" | Per the approval sheet |
| B7 | **Definitive Guide** third-party-testing / NSF / USP passage | Tammy inclined to leave as general education. Mindy's highlights are HubSpot comments (nothing shows on the live page) — resolve them in the editor |
| B8 | **Custom formulation** in Mindy's own subheader line ("full catalog and custom options") | Client wording, so it stands — noting it against the earlier "don't offer custom formulation" rule |

## C. Emails and workflows (not website, tracked here so it isn't lost)
- Reply-to on 108 emails → **info@praxerasupplements.com** exists (Sarah). Shawn: change at the last second.
- Email footer is the **universal DaVinci brand footer** — must not be edited (would change every DaVinci email). Patrick to create the Praxera brand kit, then re-clone to it.
- No HubSpot CTAs are embedded in any of the 111 emails (plain links only) — nothing to clone there.
- Workflows: all 12 off, all sends Praxera, enrolment forms fixed; switch-over plan is DaVinci off / Praxera on in one move.

## How the fixes get made without breaking anything
Every change: fresh read → full before-state saved to `backups/` → dry run printed and reviewed → one low-traffic pilot page → live check → batch → read-back → control check that untouched pages are byte-identical → commit. Scope is enforced in code (Praxera URLs / "Praxera - " names only) and shared assets — brand footer, file-hosting domain, Hotjar, anything DaVinci or PetTech — are flagged, never edited. Client-facing copy waits for client sign-off; drafts and staging do not.
