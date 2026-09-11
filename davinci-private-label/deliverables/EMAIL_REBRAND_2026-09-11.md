# Praxera email drafts — rebrand pass (11 Sep 2026)

Portal 4087538. Scope: the 111 marketing emails whose name starts with `Praxera - `. All are in
DRAFT state; nothing was published or sent. Before-state of every email is in
`backups/email-footers/`.

## What changed

| Change | Emails |
| --- | --- |
| Footer (CAN-SPAM office location) set to the new Praxera address | 111 |
| Reply-to address set to info@praxerasupplements.com | 110 |
| Follow-us / social-share icons removed | 92 |
| Hard-coded DaVinci social icon row removed from branded footer | 2 |
| Dead `/en/pl-demo-*` links repointed to live pages | 62 |
| Praxera logo served from praxerasupplements.com instead of info.davincilabs.com | 107 |
| Broken logo file (CROUD ASSETS/Praxera Logo.png, 404) repaired | 2 |
| DaVinci-branded bottle photos replaced with Praxera-format bottles | 3 |
| Dated wording made evergreen | 4 |

## Footer

Office location `221681937557` (Praxera Supplements, 929 Harvest Lane, Williston, Vermont 05495)
now applies to all 111. HubSpot holds one footer per office location, and an email picks its
location in Settings → Footer, so DaVinci, Pet Naturals, VetriScience and Pet Tech Labs keep
their own footers untouched.

## Link repointing

| Old (404) | New (200) |
| --- | --- |
| /en/pl-demo-get-started | /get-started |
| /en/pl-demo-about | /about |
| /en/pl-demo-book-consultation | /book-consultation |
| /en/pl-demo-design-team | /design-team |
| /en/pl-demo-guides | /guides |
| /en/pl-demo-resources | /resources |
| /en/pl-demo-ingredients-testing | /learning/ingredients-testing |
| /en/pl-demo-onboarding-guide | /learning/onboarding-guide |

## Imagery

DaVinci-labelled product photos (All-Zyme, Perna Plus, Cal Mag) were replaced in three emails with
new Praxera-format bottles built to the Private Label deck layout (white bottle, "YOUR LOGO GOES
HERE", green rule). Higgsfield had no credits, so the images were generated through Fal and
uploaded to the portal file manager at /Praxera/email/:

- praxera-bottle-bone-mineral.png
- praxera-bottle-joint-support.png
- praxera-bottle-digestive-enzyme.png

Product names in the copy changed with them: Cal Mag → Bone & Mineral Support, Perna Plus → Joint
Support, All-Zyme™ → Digestive Enzyme.

## Open items

- Two emails ("Danielle: DV Mission & Register", "Paul: DV Mission & Register") run DaVinci's
  "STAND FOR MORE" campaign banner and mention FoodScience. They need a content decision, not a
  swap.
- Five bit.ly shortlinks in two emails resolve to DaVinci pages.
- Three emails previously sent from the contact owner's address; they now use
  info@praxerasupplements.com like the rest. Revert from the backup if the owner address was wanted.
- Five live blog posts carry a year in the title. Titles proposed in the sign-off sheet; the edit
  needs a go because the posts are published.

## Second round (same day)

| Change | Where |
| --- | --- |
| Green Get Started button added to the site navigation | Global Header module, live on all 68 Praxera pages and the mobile menu |
| Five live blog titles made evergreen (URLs untouched) | praxerasupplements.com blog |
| DaVinci campaign imagery and the "STAND FOR MORE" line removed | 2 DV Mission & Register emails |
| Five bit.ly shortlinks repointed from davincilabs.com shop pages to Praxera format pages | 2 Supplement Formats emails |
| DaVinci practitioner registration link (fsc-live.com) repointed to /get-started | 3 emails |
| "PraxeraLabs.com" corrected to praxerasupplements.com | 2 emails |
| Dated alt text replaced | 3 emails |

### Blog titles

| Slug (unchanged) | New title |
| --- | --- |
| top-selling-private-label-supplements-for-2021 | Top Selling Private Label Supplements |
| trending-private-label-supplements-for-2022 | Trending Private Label Supplements |
| 2023-trends-in-vitamin-and-supplement-industry | Trends in the Vitamin and Supplement Industry |
| vitamin-manufacturing-10-top-sellers-to-consider-in-2026 | Vitamin Manufacturing: 10 Top Sellers to Consider This Year |
| how-much-to-start-a-private-label-supplement-business | How Much Does It Cost to Start a Private Label Supplement Business? |

Before-state of the posts is in `backups/blog-titles.pre-change.json`; the header module's published
files are in `backups/global-header/`.

### Header button

`Private Label/Modules/Global Header.module` gained a `cta` field group (show / text / link,
defaulting to Get Started → /get-started) and a `.headerCta` style. The right-hand nav area is now a
flex row so the button sits flush right. The module is used only by Praxera pages.

## Full email QA, 11 Sep

Every one of the 111 drafts was re-read from HubSpot and checked for: footer office location,
reply-to, from name, subject, social modules, placeholder text, dated copy, brand mentions in
visible text, and the HTTP status of all 174 links and images.

| Result | Count |
| --- | --- |
| Emails clean | 108 |
| Emails with a finding | 3 |

Remaining findings, all needing a decision rather than a fix:

- Two emails link to foodsciencecorp.com, which refuses automated checks (403). Open it in a browser
  to confirm, and decide whether the parent-company mention stays.
- One email links to the Praxera blog post "Top questions consumers have about private label
  supplements", which is still a draft, so the link 404s until the post is published.

No HubSpot CTA objects are used in any Praxera email or page. Every button is a plain link, so there
is nothing to clone; all destinations were checked.

## Visual image scan (Playwright), 11 Sep

Filenames and alt text do not reveal what a picture shows, so every image used in the Praxera assets was
downloaded, laid out in contact sheets with Playwright, and looked at.

| Where | Images checked | DaVinci-branded |
| --- | --- | --- |
| Emails | 118 | 31 |
| Website pages and blog posts | 237 | 0 |

The 31 in the emails were DaVinci-labelled bottles and powders, three blog link-preview cards showing
blog.davincilabs.com, the DaVinci Laboratories logo, a 5R gut-health graphic carrying that logo, a
FoodScience of Vermont private-label graphic, and a label sheet with one DaVinci bottle in it.

Each was replaced with a Praxera private-label counterpart in the same format and with the same product
name, generated to match the existing Praxera sell-sheet bottle style: white bottle, "YOUR LOGO GOES
HERE", navy product name, lime rule. Twenty new images were produced and uploaded to /Praxera/email/ in
the portal file manager. Alt text was rewritten on 65 images so it describes what is now shown.

A second full visual pass over the 110 images now in the emails found no DaVinci branding anywhere.

## Live site findings, 11 Sep

| Finding | Scale | Status |
| --- | --- | --- |
| Images served from info.davincilabs.com on live Praxera pages | 74 references across 36 pages | Fixed: repointed to the Praxera domain, same files, 28 pages republished |
| Form redirects sending visitors to google.com after submit | 23 live pages | Fixed: now go to /ty-consultation |
| Form redirect sending visitors to a DaVinci thank-you page | learning/onboarding-guide | Fixed: now goes to /learning/onboarding-guide-ty |
| HubSpot CTA objects | 2, embedded in 61 blog posts | Already Praxera-branded and pointing at live Praxera guides — no action |
| NSF GMP-certified badge on certifications and quality-standards | 2 pages | Flagged: Mindy said we do not hold NSF or USP certification |
| "2026 Guide" baked into a blog hero image | 1 post | Flagged: the title was made evergreen, the artwork was not |
| Broken images | Praxera_Infographic.jpg and one guide image | Flagged |

Backups of every page changed are in `backups/page-davinci-domain/` and `backups/form-redirects/`.

## QA round two, 11 Sep

A second QA pass rendered the reworked emails and checked the automation. It caught problems in the
first image swap, which have been corrected.

| Problem | Scale | Fix |
| --- | --- | --- |
| Images paired with the wrong product copy after the swap | 10 emails, 23 images | Re-paired from each email's pre-swap revision, so every photo sits with its own product again |
| Replacement images distorted or oversized | 12 emails | Widths capped to match their siblings, heights recomputed from the real aspect ratio |
| Praxera logo invisible on a near-black masthead | 4 emails | Now uses the white Praxera logo already in the file manager |
| Praxera assets served from pettechlabs.com | 6 emails, 18 references | Now served from the Praxera domain |
| DaVinci-branded guide PDFs delivered to prospects | 4 fulfilment emails | Now deliver Praxera-Private-Label-Guide.pdf and Praxera-Client-Onboarding.pdf, which already existed |
| Form thank-you redirects pointing at pages that do not exist | 7 forms | Repointed to the live Praxera thank-you pages |

Images whose file name says DaVinci were downloaded and looked at: all are brand-neutral graphics
(the 5Rs banners, a calendar icon, stock photography). The names are cosmetic.

## Still open

| Item | Who decides |
| --- | --- |
| 75 workflow emails are batch drafts, not automated emails. A workflow cannot send them as they stand. | Patrick — this is the first cutover blocker |
| Four workflows enrol on davincilabs.com pageviews, four more on membership of live DaVinci workflows, one only on DVL-named lists | Patrick |
| Sales Qualified Leads workflow routes to two owner IDs that do not exist and notifies a deleted user | Patrick |
| Fifteen workflow branches test clicks on six deleted DaVinci emails, so they always take the default path | Patrick |
| "Welcome to DaVinci Posts.zip" is still attached to the D4HCP intro email | Patrick |
| Sixteen emails name catalog products (Immuno-DMG, Scale Down, Liposomal C and others). Mindy's page comments treat several as Praxera products | Mindy / Tammy |
| FoodScience named as parent company in three emails, two linking foodsciencecorp.com | Mindy / Tammy |
| "Custom formulation" still appears in two emails and in the name of the auto-responder | Mindy / Tammy |
| NSF GMP-certified badge on two live pages | Regulatory |
| DaVinci's Hotjar tracking script runs on every Praxera page | Patrick |
| Blog post "Top questions consumers have about private label supplements" is still a draft, so one email link 404s | Justin |

## Site QA round two, 11 Sep

A full crawl of the 57 published pages and 68 published blog posts, with pages rendered and reviewed.

Passed: every page returns 200 with a sane title, the green Get Started button is in the header of all
127 pages pointing at a live page, and 521 image URLs return a valid image.

Fixed in this pass:

| Finding | Scale | Fix |
| --- | --- | --- |
| Links to DaVinci blog articles in page copy | 5 links on 3 pages | Repointed to the same articles on the Praxera blog |
| Links using the old /private-label/ blog path, which 404 | 52 links across 25 blog posts | Rewritten to /blog/, all 52 resolved to live Praxera posts |
| A guide link pointing at a DaVinci CDN PDF | learning/definitive-guide | Now points at /design-services |
| Malformed link "/eBay.com" | how-to-sell-supplements | Now a working eBay link |
| Alt text reading "DaVinci Vermont manufacturing facility" | about | Rewritten |
| Praxera blog images served from pettechlabs.com | 6 posts | Now served from the Praxera domain |

### Needs a person

| Finding | Why it is not mine to fix |
| --- | --- |
| DaVinci's Hotjar script runs on all 127 Praxera pages, recording visitors into DaVinci's analytics | It is a portal-level setting, not in any Praxera page or template. Removing it in the API would affect DaVinci pages. Justin should set a per-domain override in HubSpot |
| The blog listing overflows the screen, 1571px wide on a 390px phone | The featured-image rule lives in a blog template stylesheet. Needs a one-line CSS rule and a check that the DaVinci blog does not share it |
| Two broken images live: Praxera_Infographic.jpg on the scale-your-business post and Praxera.LitX (2).png on how-to-sell-supplements, plus the infographic PDF | The source files are missing. Someone has to supply them |
| STEP 04 missing from how-to-sell-supplements, empty modules on certifications and quality-standards | Content, not configuration |
| /pl-global-blocks is published and in the sitemap | It is an internal build page. Unpublishing is Justin's call |
| Blog listing shows the byline "DaVinci Healthcare Expert" on one post | The author record may be shared with the DaVinci blog |
| Twelve dead citation links pasted from Word on the gummy-vitamins post | Needs the real sources |

## Header, tracking and bylines, 11 Sep (late)

**Navigation.** The nav areas were fixed-width and could not shrink, so below about 1280px the left
group wrapped onto two lines and "Quality & Trust" broke apart. The header now keeps its three areas on
one row, labels never break mid-phrase, and padding steps down at 1250px and 1050px. Tested from 1600px
down to 820px against the live page markup: the nav holds one row to 1000px, and the mobile menu takes
over at 800px. The green button also sits further right.

An earlier attempt at this used auto-width areas and broke the live header; it was reverted within
minutes. The lesson is in the QA note below.

**LocaliQ tracking.** The Capture Code LocaliQ sent on 9 September was not installed anywhere. It is now
in the global header module, so it loads on all 127 pages including blog posts:

```
//cdn.rlets.com/capture_configs/402/6f3/e04/053492c94b2b6b8b611e1c0.js
```

It sits in the module rather than HubSpot's portal-level site header, because that setting is shared with
DaVinci. If Justin also adds it in settings, one copy must be removed or the site will double-fire.

**Blog bylines.** All 72 Praxera posts now carry a single general author, "Praxera Team". Fifteen of them
had been bylined to DaVinci people, including "DaVinci Healthcare Expert" on 13 posts and "Dom Orlandi,
President of DaVinci" on one; those names were being published in each post's structured data, so search
engines read them as the author. The previous author of every post is saved in
`backups/blog-authors/before.json`.

**Email logo in dark mode.** The Praxera logo files are already transparent, so there is no white box in
the file. What breaks is dark mode: the navy wordmark on a dark background is close to unreadable. The
masthead had no background colour set on 68 emails, which lets a dark-mode client repaint it. Those 68
now carry an explicit background, so clients that respect it keep the logo legible. Four emails with a
dark masthead already use the white logo.

To be bulletproof in every client, including the ones that force inversion, the masthead would need to be
a fixed dark band with the white logo on every email. That is a brand-kit decision for Patrick, and it is
one pass to apply once someone says yes.

### QA note for this repo

Render checks must include the real logo and the live stylesheets. A local render with the logo missing
made a broken header look fine, and it went live for a few minutes before being caught.
