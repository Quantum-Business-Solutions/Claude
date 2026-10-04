# Praxera SEO/AEO audit — 4 Oct 2026

Run ea8f6d5c-a907-4d7c-9be1-813938c8c3f6 (ClientCommand, standard tier). Report:
https://clientcommand.thequantumleap.business/pages/f7f14147-b95f-496e-af46-8bd3033eb5ec (not public).

| | 13 Sep | 4 Oct |
|---|---|---|
| Readiness | 57 (C) | 62 (C) |
| Pages D/F | 27 | 12 (6 are thank-you/internal pages) |
| Buyer queries in top ten | 0 of 9 | 0 of 21 |
| Organic keywords / visits | n/a | 51 / 0 |
| Authority Score | 2 | 2 |

## Cutover traffic finding (Semrush, US, estimates)
Only a small slice of davincilabs.com's organic traffic is private-label. Roughly 1,870 visits/month could move:
- www.davincilabs.com/private-labeling* (11 URLs): ~1,600/mo (/private-labeling alone ~1,307, #1-2 for ~15 "private label supplement manufacturer" terms)
- blog.davincilabs.com/private-label/*: ~212/mo
- info.davincilabs.com private-label guides: ~55/mo
The other ~21,000/mo is the consumer brand (blog.davincilabs.com/blog/*, rest of www) and stays on DaVinci.

**Gap:** the 134-entry redirect map (reference/redirects.json) has NO www.davincilabs.com/private-labeling* sources. These 11 URLs are the highest-value pages. reference/url_map.json maps a few of them to stale /en/pl-demo-* slugs (do not use).
Praxera sitemap equivalents exist for: /weight-management, /probiotics, /herbal, /fitness, /sleep, /aging, /womens-health, /how-to-sell-supplements, /get-started, /about. /private-labeling (main page) needs a target decision. Risk: Praxera copy deliberately drops "manufacturer" claims, so some #1 "manufacturer" rankings will not carry over.

## Change made 4 Oct (home page, id 216189433405, portal 4087538)
Added `telephone` (+1-800-325-1776) and `contactPoint` to the Organization JSON-LD in headHtml (QBS-SCHEMA block). Both values are shown in the live footer. Before/after: backups/seo-org-schema-2026-10-04/. Draft patched and push-live returned success; **public-site read-back NOT verified** (check was blocked by the auto-mode classifier). Rollback: PATCH draft headHtml from home-headHtml-before.json, then push-live.
Not added (no verified source): `sameAs` profile URLs; `legalName` "Praxera of Vermont" left as is (unconfirmed, see Tammy items).

## Correction
Earlier advice to noindex the /alp/ ad landing pages conflicts with the report's plan to rank them organically. Noindex only thank-you (`ty-*`, `learning/*-ty`, `ty-ingredients-testing`) and internal review pages (`pl-global-blocks`) unless the client decides the /alp pages are ad-only.

## Open items
301 cutover (client go-live); force HTTPS on www (HubSpot domain setting; http://www returns 404); blog index canonical + og:type; blog schema publisher "FoodScience Corporation" and generic author; alt text; H1 fixes; llms.txt (needs hosting approach + approved text); sameAs URLs; paid-search tracking/landing-page fixes.

## Update 4 Oct (later)
- Home Organization schema (telephone + contactPoint): **verified live** on the public site, JSON-LD valid.
- Blog index canonical: added `<link rel="canonical" href="https://{{ request.domain }}{{ request.path }}">` to `Private Label/Templates/Praxera - Blog Listing.html` (published). Before/after in backups/blog-index-canonical-2026-10-04/. First attempt used `content.absolute_url` (emitted nothing); replaced. **Public /blog and /blog/page/2 did not show the tag ~1 min after the second PUT — likely page cache; recheck.** Rollback: PUT the .before.html.
- Correction: `og:type=blog` is valid in the original Open Graph spec; no change made. Twitter card `summary` is also fine.
- Money-page forms: audit's "no form" was wrong for 6 of 12 (/, /alp/*, /design-services, /top-sellers load a HubSpot form via script). Still no form on /ingredient-sourcing, /testing, /soft-gels, /tablets, /certifications, /quality-standards.

## Update 4 Oct (evening): HTTPS, canonical, breadcrumbs
- HTTPS: domain already had Require HTTPS on (API: isHttpsOnly true) yet http://www returned 404 at the HubSpot edge ("404 predicted at edge"); user toggled it off/on and http now 301s to https (verified).
- Blog index canonical: the live blog listing appears to render from `Templates/BlogListing.html` (not only `Praxera - Blog Listing.html`, which the blog settings point at). Canonical `https://{{ request.domain }}{{ request.path }}` added to BOTH. Public /blog is served from HubSpot's pre-render cache (s-maxage 10h, last built 16:15 UTC) so the tag was not yet visible; polling.
- Breadcrumbs: invisible BreadcrumbList JSON-LD added to `Templates/Page - DND.html` (66 pages; Home > title, learning/* = Home > Resources > title) and `Templates/Praxera - Blog Post.html` (Home > Blog > title). Visible breadcrumb trail NOT added (design change, needs client sign-off). Backups + after copies in backups/breadcrumbs-2026-10-04/ and backups/blog-index-canonical-2026-10-04/. Rollback: PUT the .before.html files.
- AEO 50-question x 4-engine run started (background); first 5 questions x perplexity+gemini: Praxera 0/10 cited or mentioned; davincilabs.com cited in 2 of 5 perplexity answers.
