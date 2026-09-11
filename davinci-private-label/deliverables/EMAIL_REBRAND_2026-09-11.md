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
