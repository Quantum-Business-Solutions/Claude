# Praxera — the three paid-traffic landing pages

**Date:** 13 Sep 2026 · **Portal:** 4087538
**Before-state:** `backups/alp-ads-copy/` · **Change log:** `reference/ads_lp_copy_changes.json`
**Status: written to the HubSpot DRAFT buffer. Nothing pushed live.**

| ID | Slug | Title | Sign-off |
|---|---|---|---|
| 216192983652 | `alp/ads-mfg-usa` | Supplement Manufacturer USA \| Praxera Private Label | not reviewed |
| 216192983654 | `alp/ads-contract-mfg` | Supplement Contract Manufacturer \| Praxera Private Label | not reviewed |
| 216194811734 | `alp/ads-pl-mfg` | Private Label Supplement Manufacturer \| Praxera Private Label | not reviewed |

Checked against the sign-off sheet before writing: all three are **not reviewed** and carry the
`placeholder copy` chip. Patrick has not approved any of them, so nothing he validated was touched.

## Was there a DaVinci original?

**No.** I searched every non-Praxera page in the portal for an ads / manufacturer landing page.
Sixteen matches came back and fifteen are **Pet Tech Labs**, who genuinely are a contract
manufacturer. The only DaVinci one is a **draft that never shipped** —
`207982916662` "LP: Liquid Supplement Contract Manufacturer" on info.davincilabs.com. It was read
read-only for reference and not modified.

So there is no approved DaVinci copy to lift. Every line below is written fresh against the
standing rules and against language already live and approved on `/about`, `/our-process` and the
category pages.

## What was actually on the pages

They were **not empty**. Each carried a full build — hero, stat bar, body, three cards, form, CTA,
FAQ — with one literal paragraph in the middle of the body:

> [PLACEHOLDER: This is a paid-traffic landing page. Justin should add the specific value props and
> CTAs that match the targeted keyword.]

That paragraph is **live and public on all three pages right now**, and the surrounding copy broke
several standing rules. Both were fixed in the draft.

## Rule breaks found in the existing copy

| Where | Was | Rule |
|---|---|---|
| stat bar, all 3 | "100% **USA-manufactured**" | Mindy — never present Praxera as manufacturing |
| card 1, all 3 | "**U.S. manufacturing**, FDA-registered" / "Manufactured in Vermont" | reads as Praxera's own plant |
| FAQ, ads-mfg-usa | "**Our Vermont facility** has been continuously FDA-registered" | Mindy — never "our facilities" |
| FAQ, ads-mfg-usa | "**We host facility tours**" | Mindy — never "our facilities" |
| FAQ, ads-pl-mfg | "Why work with Praxera over other private label **manufacturers**?" | Sarah — Provider language |
| FAQ, ads-pl-mfg | "**Manufacturing**, quality testing, certificates of analysis…" | Sarah — Provider language |
| body, all 3 | "We brand and provide. You sell." + "Your brand, **our infrastructure**" | implies owned production |
| meta, ads-contract-mfg | "Private label or **custom formulation**" | Sarah — remove every instance |
| meta, all 3 | "**250-plus** products" | site says 190-plus on `/`, `/about`, `/our-process` |
| CTAs, all 3 | "Schedule a Consultation" → `/contact` | Tammy — consultation CTAs go to `/get-started` |

## What the copy says now

**`alp/ads-mfg-usa`** — keyword: *supplement manufacturer USA*. Hero kept ("Made in the USA.
FDA-registered, GMP-certified." — already compliant). Body gains a "Why US-made matters for your
brand" section: shorter lead times, fewer supply-chain surprises, and a Made in the USA claim the
brand can substantiate. Four value props, then a soft close. FAQ rewritten so the facility is
described, never claimed: *"Praxera products are made in a Vermont facility that has been
continuously FDA-registered…"*, *"Tours can be arranged for prospective and active clients."*

**`alp/ads-contract-mfg`** — keyword: *supplement contract manufacturer*. The hardest of the three,
because the search term is the thing Praxera is not. The body answers the searcher's real question
without making the claim: private label means an existing formulation with your brand on it; a
custom product means working with our formulators to a specification you own; Praxera supports both
**as your turnkey provider**, with turnkey production running in an FDA-registered, GMP-certified
US facility in Vermont. FAQ grew from 2 to 5 entries — two was thin for a paid page.

**`alp/ads-pl-mfg`** — keyword: *private label supplement manufacturer*. Hero and subhead kept, both
already compliant. Body gains a "Private label, start to finish" section — 190-plus products,
in-house label design, certificates of analysis and sell sheets on every order, no set-up fees,
8 to 12 weeks — plus a line for the half of the audience launching a first product.

All three: stat bar now reads "100% **made in the USA**", card 1 is "**Made in a US facility**", every
"Schedule" CTA points at `/get-started`, and the metas are rebuilt at 190-plus with the
manufacturing claims out.

## QA

`tools/qa_ads_lp_copy.py` checks 72 copy fields across the three pages against ten rules —
no "custom formulation", FoodScience LLC not Corp, no DaVinci, Provider language (every
`manufactur*` must sit inside an approved construction such as "US manufacturing", "turnkey
production", "manufactured in a US facility"), no purchase path, CTAs to `/get-started`, no
"Praxera Laboratories", 190-plus not 250, no placeholder text, Daily Best® keeps its mark.

```
checked 72 copy fields across 3 pages
PASS - no rule violations in the new copy.
```

`tools/qa_ads_lp_render.py` + `tools/qa_ads_lp_shots.js` mirror each **draft preview** with its
stylesheets and fonts and drive Chromium over all three at 1440px, 900px and 390px. Clean at every
width: no broken images, no sideways scroll, no DaVinci text, no placeholder text, exactly one `h1`,
no empty sections, and all four "Schedule"/"Get Started" CTAs resolving to `/get-started`.
Screenshots in `/tmp/adslp/`. The `AOS is not defined` / `hbspt is not defined` console errors are
artefacts of the local mirror — those two scripts are not mirrored — not page faults.

## Open for Shawn

1. **The titles still say "Manufacturer."** All three page titles and slugs target a
   *…manufacturer* keyword, which is the whole point of the ad buy, and collides head-on with
   Mindy's rule that Praxera is never marketed as manufacturing. There is no DaVinci original to
   fall back on. Titles and slugs were left alone — changing a slug breaks SEO and changing the
   title breaks the keyword match. **Client decision.**
2. **The form on these three pages notifies nobody.** `Praxera - Schedule a Consultation
   (Ads pages)` (`c82c667f`) has no notification recipients and `notifyContactOwner` is false. It
   has had **zero submissions**, so nothing has been lost, but a paid click that converts today
   reaches no one. The precedent set on the main consultation form is contact owner + Sam Fuller +
   Patrick. Say the word and I will set it.
3. **The placeholder is live now.** Either push these drafts (one command) or unpublish the three
   pages until the copy is signed off. Both are client-facing, so neither happens without a go.
