# Praxera — full asset QA sweep
**Date:** 11 Sep 2026 · **Portal:** 4087538 · **Scope:** emails, blogs, forms, links, website
**Excluded by request:** workflow enrolment triggers

Four independent Playwright-backed sweeps. **114 findings: 13 blockers, 38 high, 29 medium,
17 low, 17 info.** Nothing was changed — this is a findings list only.

Raw data: `reference/findings_all.json` (plus per-area files).
Header evidence: `reports/header-overlap-2026-09-11.png`.

---

## 1. Blockers

### 1.1 The Praxera 404 page is the old DaVinci Laboratories storefront
Found independently by two sweeps. Any bad URL on www.praxerasupplements.com returns a
41,668-byte page carrying `DV_2017Logo.png`, **72 anchors to davincilabs.com** (a green BUY
button, `where_to_buy`, `p=buy`, 24 product pages, facebook.com/DaVinciLabs), the DaVinci SKU
list, and the footer "DaVinci Laboratories of Vermont © 2017". The `<title>` is empty.
Breaks the no-DaVinci-assets rule **and** the no-purchase-path rule, and it is where every
broken internal link in this report deposits the visitor.
**Fix:** point the Praxera domain's system 404 page at a Praxera template.

### 1.2 Homepage SEO tags brand Praxera as a manufacturer
`<title>` = "Private Label Supplement Manufacturer | Praxera Private Label"; meta description
= og:description = "50 years of supplement manufacturing. 250+ doctor-formulated products…".
This is the literal text Google and LinkedIn/Facebook share cards show. Same framing on
`/alp/ads-mfg-usa`, `/alp/ads-contract-mfg`, `/alp/ads-pl-mfg`, `/certifications`, `/about`.

### 1.3 Body copy says Praxera is the manufacturer, in the first person
Verbatim on **home** and **health-categories**: "A private label supplement is a pre-formulated
dietary supplement produced by a manufacturer **(us)** and sold under your brand name."

### 1.4 Email guide PDFs are DaVinci- and Pet Tech-branded
- 220685976492 "Download the 5R Framework Quick Deploy Kit" → PDF with the DaVinci logo on
  page 1, footer "visit DAVINCILABS.COM", and DaVinci SKUs throughout.
- 220685976580 and 220688836180 "Please see our Client Onboarding Guide" → the **Pet Tech Labs**
  client-onboarding PDF. A correct Praxera version already exists and is verified live.

### 1.5 Eight emails carry legacy CTAs that land on blog.davincilabs.com
These are `{{cta()}}` tokens, so the DaVinci URL never appears as a literal href and a string
scan misses them entirely. Resolving each CTA redirect exposed them.

### 1.6 Retargeting email registers the lead with DaVinci
220693084785 says "you haven't completed your account registration on praxerasupplements.com";
its button resolves to fsc-live.com/dvapp/registration.php → davincilabs.com/register.

### 1.7 `/contact` publishes a misspelled mailto
`mailto:info@praxerasu**a**pplements.com` — mail to it bounces.

### 1.8 All 11 global-footer nav links are `href="#"`
1,386 dead anchors across 126 live pages. No Privacy or Terms link exists in the footer;
`/privacy` and `/terms` have zero inbound links sitewide.

### 1.9 `/top-sellers` form redirects to a DRAFT page that 404s
Redirect target `/ty-contact` is unpublished, so submitted leads land on the DaVinci 404 page.

### 1.10 One blog post is DRAFT and its URL is hijacked
220638601745 `/blog/top-questions-consumers-have-about-private-label-supplements` is
`state=DRAFT`. The blog is **71 live, not 72**. The URL also 301s to a DaVinci path that 404s,
because redirect 208573973878 has a bare-path `routePrefix` with `isOnlyAfterNotFound=false`
and now fires on the Praxera domain — the only one of 255 domain-less rules that shadows a
Praxera slug. A live post links to the dead URL twice.

---

## 2. High

### 2.1 Header: "Quality & Trust" prints on top of the logo from 801px to 970px
Site-wide, every page. Measured with the real Open Sans webfont loaded and the real logo:
the nav text overlaps the visible praxera wordmark by 64px at 801px and 26px at 900px,
clearing at **971px**. At 801–880px the left nav also wraps to two rows.
This is a **regression from the 9 Sep header CSS change** and it sits inside the band that
was previously reported as verified. The "Get Started" button itself never collides.
See `reports/header-overlap-2026-09-11.png`.

### 2.2 Blog bylines: 58 of 72 posts still name a DaVinci/FoodScience person
The API author field and the JSON-LD are correct ("Praxera Team"), but the byline readers see
lives in each post's hero `subhead`, which was not changed. Aryel Wilbur ×27, Melinda
Elmadjian ×20, Brandiann M. Kanya ×7, plus Dr. Ramneek Bhogal, Dr. Charlie Ware and Jon
Krouner. One reads **"By Dom Orlandi, President of Praxera"** — he is President of
FoodScience/DaVinci, so the title is false. Structured data and visible byline disagree on
every post.

### 2.3 Manufacturer framing across the site and blog
- "we produce…" on **15 pages**, "we handle production…" on **10 pages** (a shared template
  snippet).
- "our facility/facilities" on about, contact, quality-standards, testing.
- **10 blog posts** call Praxera a manufacturer: "all of our facilities are FDA-certified…
  Our industry-leading manufacturing facilities produce over 250…", "Praxera operates an
  FDA-registered facility", "manufactured at Praxera", "Some manufacturers (like Praxera)".
- **5 emails**: "Our order placement and manufacturing process…", "we will teach you all
  about our private label supplement manufacturing services", "producing quality,
  doctor-formulated supplements".
- **"FDA-certified facility"** ×4 across 2 posts — FDA registers facilities, it does not
  certify them.

### 2.4 Search-and-replace artefacts that invent an entity
"**Praxera® Laboratories**" ×4 in two emails ("Praxera® Laboratories has lower minimum order
quantities than most private label supplement manufacturers"), and "**Praxera® Labs**" on
4 blog posts. Neither entity exists; both are the surviving half of "DaVinci® Laboratories".

### 2.5 DaVinci product names and artwork still in Praxera assets
- **13 emails** name DaVinci SKUs in visible copy (Tri-Mag 300, Daily Best Ultra™, GI
  Benefits®, Scale Down®, Mega Probiotic™ ND, Hair Effects™, Clear GI™, ADK…). Confirmed
  inherited by diffing against the DaVinci source emails.
- **Bottle-lineup photography survived the image swap** in ~20 emails: labels legibly read
  TRI-MAG 300, CHOLESTSURE, ALL-ZYME, COMPLEX-75, HAIR EFFECTS, and several bottles carry a
  "DR. CROSS" customer brand. The **blog listing hero is the same DaVinci lineup shot.**
- Blog posts still sell DaVinci SKUs as Praxera products (DIMPRO®, Mango-Plex, Dyglofit™…).

### 2.6 Praxera-hosted image URLs spell out DaVinci
10 emails reference live 200-returning URLs such as
`praxerasupplements.com/hubfs/Download Offers/DaVinci Labs/Newsletters/DaVinci-Churn_26.jpg`.
19 emails use a filename containing "davinci" or "DAV_". Anyone who right-clicks an image or
forwards the email sees the DaVinci path.

### 2.7 Schema markup points at DaVinci-family properties
- Organization JSON-LD on **19 site pages** (including home) sets `logo` and `image` to
  `https://www.pettechlabs.com/hubfs/Praxera/Praxera%20Logo.png`, and `legalName` to
  "Praxera of Vermont".
- The blog's schema `publisher.logo` on **all 71 published posts** resolves to a file that is
  the **DaVinci® Laboratories wordmark**, with `publisher.name = "FoodScience Corporation"`.

### 2.8 Live paid-ads pages carry internal placeholder copy
`/alp/ads-contract-mfg`, `/alp/ads-mfg-usa`, `/alp/ads-pl-mfg` all publish, verbatim:
"[PLACEHOLDER: This is a paid-traffic landing page. Justin should add the specific value props
and CTAs that match the targeted keyword.]"

### 2.9 No Praxera-domain identity exists in the portal
Of 81 CRM owners: 58 @foodsciencecorp.com, 1 @davincilabs.com, 2 @vetriscience.com, 1
@petnaturals.com, 6 @thequantumleap.business — **zero @praxerasupplements.com**. So owner
tokens in 5 emails render "Email me at <owner>@foodsciencecorp.com", and two hardcoded booking
links resolve to FoodScience staff round-robins. DaVinci's toll-free **800-325-1776** is
printed in 4 emails and on `/contact`.

### 2.10 Broken links and images
- **24 internal URLs 404**, mostly blog cross-links, plus `/private-label`,
  `/private-labeling`, `/private-label-get-started`, `/shop-supplements.html` (also a
  purchase-path violation) and `/guides` (linked from 3 emails).
- **3 broken assets**, all on blog posts (which is why the site-page crawl showed 389/389
  images at 200): `Praxera_Infographic.jpg` and `Praxera_Infographic (2).pdf` on
  `/blog/how-to-scale-your-business-with-private-label-supplements`; `Praxera.LitX (2).png`
  on `/blog/how-to-sell-supplements`.

### 2.11 105 of 111 emails stretch their images
The `width`/`height` attributes were inherited from the DaVinci originals after the `src` was
swapped. The Praxera logo is 612×208 but declared 260×102 / 200×97 / 230×112 — 15% to 43% too
tall — in 101 emails. The footer image is declared 122% too tall.

### 2.12 Form configuration gaps
- Form `471fb48f` consent text still reads literal **`[BRAND_TBD]`**; three other forms link
  consent to `www.Praxeralabs.com`, which does not resolve.
- **4 forms notify nobody**, including `d8dfdd90`, used in 27 of 35 placements. A **deleted
  user** is the only recipient on the /design-team form. Every resolvable recipient is a
  creativesidemarketing.com address. No follow-up email is set on any Praxera form.
- 8 forms write to `i_would_like_to_subscribe_to_the_davinci_blog`, **pre-checked `true`** on
  both main lead forms. 6 emails sit on the "DaVinci Blog Subscription" type, whose name
  HubSpot prints in the preference centre.

### 2.13 Mobile overflow
`/get-started` — a hand-authored inline `width: 45em` (720px) forces **350px of horizontal
scroll at 390px**. Blog post 220637272693 overflows **425px** from bare-URL anchor text up to
145 characters; 4 other posts share the pattern.

### 2.14 Two emails are built on the VetriScience template
220685976492 and 220685976494 carry 24 `vs-*` classes and, with no `display:none` or media
queries present, render **both the desktop and mobile headers at once** — two stacked nav bars.
Six emails also show a "SHOP" nav item promising an ecommerce path Praxera does not have, with
every nav link resolving to the homepage.

### 2.15 Heritage claims contradict each other
"we opened our doors more than 50 years ago" and "family-owned company… for over 50 years"
across 8 emails, against "leading the private label space for over 25 years" in another —
both transplanted onto a brand that is months old.

---

## 3. Redirect readiness (answers the open question)

71 of 72 Praxera slugs match their DaVinci originals exactly. **One does not:**
`/blog/vitamin-manufacturing-10-top-sellers-to-consider-in-**2026**` vs DaVinci's
`…-in-**2024**`. The `-2024` path returns **404** on the Praxera domain.

Of 537 portal redirects, **exactly one** DaVinci→Praxera rule exists (the blog root,
220592488537). None of the 75 old article URLs redirect yet. A 1:1 pattern rule would work for
71 posts and 404 on this one, so it needs a flat redirect alongside the wildcard.

A separate 2021-named post (`/blog/top-selling-private-label-supplements-for-2021`) is a
**different article**, not a second clone, and its slug matches — it will redirect cleanly.

---

## 4. Decisions for the client, not fixes

- **Duplicate post.** `tips-for-buying-wholesale-private-label-supplements` and `…-0` share
  title, H1, featured image and **30 of 37 sentences verbatim**; both are PUBLISHED on Praxera.
  On DaVinci the second is DRAFT — they deliberately never shipped it. **Six more Praxera posts
  are live whose DaVinci originals are still DRAFT**, and four of those are in the
  manufacturer-language list.
- **Evergreen titles are half-applied.** All five posts still render the dated H1 ("…to
  Consider in 2026", "…for 2023", "(2026 Guide)") while the title tag, meta and listing show
  the evergreen version.
- **STEP 04 on `/how-to-sell-supplements`** still has only its one-line subhead ("Source
  high-quality supplements from a partner who can prove it.") and no body. The
  Shopify/WooCommerce comparison block currently sitting under it appears to belong to a
  different step.
- **Duplicate `how-to-sell-supplements`** exists as both a site page and a blog post, each
  self-canonicalising — they compete with each other in search.
- **`tel:1-800-325-1776`** and **`info@praxera.com`** (wrong domain, published 3×) need a
  Praxera answer before they can be replaced.

---

## 5. Verified clean

- The **24 form redirects are genuinely fixed** — zero `google.com` in any of the 266 portal
  forms; all 23 redirect targets return 200 and are Praxera URLs.
- **Zero URL shorteners** remain anywhere.
- **No Praxera page embeds a DaVinci form guid**; all 12 Praxera form guids resolve live.
- **No published blog post links to any DaVinci property** — all 73 DaVinci anchors found came
  from the 404 page.
- The **mobile blog-listing overflow did not reproduce**: `/blog` and `/blog/page/2` measure
  `scrollWidth == innerWidth` at 1440, 900, 390, 375 and 360px, with zero overflowing elements.
  The earlier report of this was wrong; there is nothing to fix.
- The **LocaliQ capture script is on 56/56 published pages**, and is not injected onto any
  DaVinci page by the Praxera header.
- Canonicals correct on all 71 published posts. Email sender identity clean across all 111.
  No broken images, JS errors, empty sections or placeholder text in the email set.

---

## 6. Corrections to earlier reporting

1. **Blog authors were not fully changed.** The API author was updated on all 72; the visible
   byline was not. 58 posts still name a person. (§2.2)
2. **The header fix left a regression.** "Quality & Trust" overlaps the logo from 801–970px —
   inside the range previously reported as verified. The earlier check rendered without the
   real webfont. (§2.1)
3. **There are 3 legacy CTA objects, not 2**, and they appear on **all 72** posts, not 61.
   All three destinations are Praxera URLs returning 200.
4. **The blog is 71 published, not 72** — one post is DRAFT. (§1.10)
5. **The mobile listing overflow does not exist.** (§5)

---

## 7. Method note

Headless Chromium cannot reach the live site through this environment's proxy, so every visual
check curls the page HTML, curls each stylesheet and **the real Open Sans webfont files**,
localises the logo and images, then renders from `file://`. An earlier pass that skipped the
real logo and fonts produced a false pass on the header — hence §2.1 and §6.2. Any future
render check must load the real font and the real logo before layout is judged.
