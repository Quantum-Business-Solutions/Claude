# Full blog QA — Kenzie's manual review + automated Playwright sweep, 27 Sep 2026

Two QA passes combined: Kenzie's manual review of 36 posts (per-post grammar/links/styling), and
an automated Playwright crawl comparing all 70 Praxera posts with a DaVinci original against their
rendered DaVinci originals (em-dashes, headings, content length, leftover branding).

## Confirmed clean (no action needed)

- **No new em-dashes introduced by the migration.** Automated count matches Kenzie's manual count
  post-for-post; 0 of 70 posts have more em-dashes than their DaVinci original.
- **No leftover davincilabs.com links** in any rendered post.
- **"Missing headings" and "shorter than original" were false alarms**, now disproven. The
  automated crawl first flagged 41 posts with missing headings and 35 posts noticeably shorter —
  both traced to one cause: the FAQ accordion lives in a separate module outside the article body,
  so it wasn't being counted on the Praxera side. Re-measured including the FAQ text: **0 posts are
  actually shorter, 0 headings are actually missing.** The rest of what looked "missing" was
  DaVinci-branded CTA headings ("Power Up with DaVinci's...") that were correctly rebranded to
  Praxera wording, not lost content.

## Real findings

### 1. "Custom formulation" language — 37 occurrences across 10 posts (standing rule violation)

Per the client's rule, Praxera does not offer Custom Formulation. Found anyway:

| Post | Count |
|---|---:|
| Custom Supplements vs. Private Label Supplements | 12 |
| Private Label Supplements: How to Make Money | 7 |
| Make Your Own Supplement Brand The Easy Way | 5 |
| Private Label Supplements: How to Get Superior-Quality at Low Cost | 4 |
| An Introduction to Sports Supplement Manufacturing | 4 |
| How Private Label Beauty Supplements Can Increase Revenue Fast | 1 |
| How Private Label Supplements Can Increase Revenue Fast | 1 |
| Make Money in the Fitness Industry with Private Label Supplements | 1 |
| Are Private Label Supplements Profitable | 1 |
| Top 10 Mistakes to Avoid With Supplement Manufacturing | 1 |

**"Custom Supplements vs. Private Label Supplements" is a bigger question than word-swaps** — the
entire post is built around comparing Praxera to a service it doesn't offer. Worth a call on
whether to rewrite it or retire it, not just edit sentences.

### 2. One post is unpublished but still linked to as if live

"Answers to Your Top Questions About Private Label Supplements" exists in HubSpot only as a
**DRAFT** (id 220638601745) — it 301-redirects when visited. "Managing the Top 3 Risks When
Selling Private Label Supplements" links to it by name. Either publish it or repoint that link.

### 3. A shared dead link, repeated across 5 posts

"FDA regulations" (or equivalent anchor text) points to `/blog/how-do-i-start-a-private-label-
supplement-business-0` (404) on:
- Why Wellness Businesses Should Sell Private Label Supplements
- What Qualifications Do You Need to Sell Private Label Supplements
- Tips for Selling Private Label Supplements for Immunity
- How to Spot High-Quality Private Label Supplements
- How To Private Label Protein Supplements

Looks copy-pasted once and never fixed. One corrected destination (an actual FDA page, since none
of these were really about an internal blog post) fixes all five.

### 4. Other broken/wrong links (from Kenzie's manual pass, confirmed real)

- `/private-label` (404) — "Top 10 Mistakes to Avoid With Supplement Manufacturing"
- `/shop-supplements.html` (404) and `/private-label-get-started` (404, should be
  `/get-started#consultation-form`) — "Supplement Dropshipping: 5 Best Tips for Success"
- `/blog/liquid-vitamin-benefits-and-uses` (404) — "Private Labeling Liquid Vitamins"
- `/blog/are-liquid-vitamins-better-than-pills` and `/blog/best-liquid-vitamins-for-kids` (both
  404) — "Liquid Supplement Manufacturing: Benefits vs. Costs"
- `/blog/do-supplements-need-fda-approval` (404) — "How to Scale Your Business..."
- Competitor Comparison Chart image is broken and its PDF link 404s — "How to Scale Your
  Business..."
- `/blog/how-dmg-supports-mitochondrial-function` (404), twice — "Trending Private Label
  Supplements"
- `#faq` anchor that doesn't exist on the page — "USP, NSF, GMP, and FDA..." and "What Is a
  Nutraceutical?"
- FDA DSHEA source link and NSF GMP registration link both 404 — "USP, NSF, GMP, and FDA..."
- fimdefelice.org doesn't load — "What Is a Nutraceutical?"
- Dozens more link to the homepage or /about/  /resources instead of the specific product/category
  page the anchor text names (full list is in Kenzie's original doc — happy to compile a
  standalone fix list if useful).

### 5. Compliance-adjacent wording, worth a rule call

- **"Guarantee"** appears repeatedly ("guarantees product quality," "guarantees compliance,"
  "guaranteed access," etc.) across many posts — supplements marketing generally avoids promising
  guaranteed outcomes. Not yet an established banned word like "custom formulation," but flagged
  the same way in every one of Kenzie's reviews, so worth a decision on whether it joins the
  banned list.
- **"FDA-certified"** ("Top 10 Mistakes...") is factually wrong — the FDA doesn't certify
  supplement facilities. Should be "FDA-registered."
- One leftover **"FoodScience"** brand mention — "Why Branded Ingredients Are Important for
  Private Label Supplements."

### 6. Cosmetic but widespread

- **Circled Ⓡ used instead of ®** on "Praxera" in at least 3 posts.
- **Stale years**: several 2026-titled posts still say 2020/2021/2022/2024 in the body
  ("Trending Private Label Supplements," "Top Selling Private Label Supplements," "Vitamin
  Manufacturing: 10 Top Sellers").
- **Inconsistent link colors** (blue vs. green) inside body text on nearly every post reviewed —
  looks like leftover inline styling from the DaVinci migration that was never normalized to the
  theme's link color.
- **FAQ text styled smaller/different gray than body** (15px #444 vs 18px #333) — consistent
  across every post, so likely an intentional accordion design choice, but flagging since it
  showed up in every single review.
- Mixed straight vs. curly apostrophes, inconsistent "private label" vs. "private-label"
  hyphenation, and a long tail of grammar nits — see Kenzie's original document for the full,
  post-by-post list; not reproduced here in full to keep this readable.

## What this doesn't cover

Kenzie's manual pass covered 36 of 71 posts. The automated pass covered all 70 posts that have a
DaVinci original (1 post, "Vitamin Manufacturing: 10 Top Sellers," is new writing with no
original to compare against) but only catches em-dashes, headings, content length, and leftover
branding/links — it does not catch grammar, link-destination correctness, or style/color
consistency the way Kenzie's manual read does.

## Source data

- Kenzie's original document: `36_Blog_Posts_-_Praxera.docx` (uploaded by the user)
- Automated crawl results: available on request, not checked into the repo (large JSON, browser
  session artifacts)
