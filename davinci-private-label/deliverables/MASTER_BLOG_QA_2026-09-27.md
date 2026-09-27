# Master blog QA — every post, every category, 27 Sep 2026

Combines three sources into one systematic pass, applied to **all 71 published posts** (not just
the ones Kenzie or Jelena happened to sample):

1. Kenzie's manual review (36 posts: grammar, links, styling) — categories extracted and reapplied
   as automated checks everywhere she didn't personally look.
2. Jelena's (Jandric's) sign-off-sheet comments (structural format, link validity, scope questions)
   — same treatment.
3. A Playwright crawl of all 71 posts checking every category systematically, plus a bulk check of
   all 298 unique links found across them.

**Read this in two parts: what's actually broken (Section A), and two decisions only Shawn/Patrick
can make before any of this gets touched (Section B).** Section C is the proposed execution plan —
nothing below has been changed yet.

---

## Section A — confirmed findings

### A1. Systemic (theme-level) — one fix each, not 70 separate edits

**The FAQ section's heading is a styled `<div>`, never a real heading, on 100% of posts that have
one (65/65).** This is why every "Frequently Asked Questions" Table-of-Contents link that exists
goes nowhere (`#faq` matches nothing on the page) — confirmed broken on 5 posts that have both a
ToC and an FAQ, and it'll break on every future post built the same way. **One fix, in the "PL -
FAQ" module: make the heading a real `<h2 id="faq">`. Fixes the anchor everywhere at once.**

Affected today (ToC really does try to link to `#faq` and fails):
- What Is a Nutraceutical?
- USP, NSF, GMP, and FDA...
- How Much Does It Cost to Start a Private Label Supplement Business? (also has a second, separately
  broken self-referencing anchor — its own truncated id)
- Contract Manufacturing vs Private Labeling...
- How Healthcare Practitioners Build a Private Label Supplement Line...

### A2. Per-post — need individual edits

**Missing byline (3 posts)** — no "By ... · Updated ..." line at all:
- Vitamin Manufacturing: 10 Top Sellers to Consider This Year (also the only post with no FAQ
  section at all — it's new writing, not migrated from anything)
- 5 Best Private Label Supplements for Sleep on the Market
- How Much Does It Cost to Start a Private Label Supplement Business?

**Circled Ⓡ instead of ® (3 posts, 11 occurrences)**:
- Must-Have Private-Label Probiotics... (5)
- Top Private Label Herbal Supplements... (5)
- Supplement Dropshipping: 5 Best Tips for Success (1)

**Leftover "FoodScience" brand mention (1 post)**: Why Branded Ingredients Are Important for
Private Label Supplements.

**Genuinely stale years** (not citation dates — checked every year-mention by hand, most of the 21
posts the automated pass flagged turned out to be legitimate research citations or market-size
stats, not errors):
- Vitamin Manufacturing: 10 Top Sellers to Consider **This Year** — title says 2026, body says
  "2024" four separate times ("top-selling products of 2024," "10 top selling supplements in
  2024," twice more)
- Trending Private Label Supplements — says "2022" repeatedly, but also "5 top private label
  supplements for 2023" in the same post. Doesn't agree with itself, let alone the current year.
- Top Selling Private Label Supplements **for 2021** — the whole post's premise is 2021.
- Both "Tips for Buying Wholesale Private Label Supplements" posts link to that same 2021 post as
  "Related Content," carrying the stale year forward.

**"Custom formulation" / "custom formula" language — 79 occurrences across 16 posts** (broader
regex than the earlier pass, and now includes the FAQ text, which the first sweep missed):

| Post | Count |
|---|---:|
| Custom Supplements vs. Private Label Supplements | 16 |
| White Label Supplements vs. Private Label: What Is the Difference? | 15 |
| Private Label Supplements: How to Make Money | 9 |
| Contract Manufacturing vs Private Labeling... | 9 |
| Private Label Supplements: How to Get Superior-Quality at Low Cost | 7 |
| Make Your Own Supplement Brand The Easy Way | 7 |
| An Introduction to Sports Supplement Manufacturing | 6 |
| Tips for Buying Wholesale Private Label Supplements (the "-0" duplicate) | 2 |
| 8 more posts | 1 each |

**Two entire posts are built around the topic Praxera doesn't offer**, not just a stray sentence —
"Custom Supplements vs. Private Label Supplements" and "White Label Supplements vs. Private Label:
What Is the Difference?" Jelena already flagged the first one directly: *"There is an entire
section on custom formulations - do we want this?"* Same question applies to the second.

**"Guarantee" wording — 23 occurrences across 16 posts** (not yet an established banned word like
"custom formulation," but Kenzie and Jelena independently flagged it every time they saw it):
How to Compare Dietary Supplement Providers, How to Develop a Private Label Brand, "...More Than
Just a Trend," Challenges and Opportunities..., NAD+ Activate (×2), Must-Have Probiotics (×2), 5
Best Sleep Supplements, USP/NSF/GMP/FDA, Why Branded Ingredients..., Truth in Labeling..., Custom
Supplements vs..., An Introduction to Sports Supplement Manufacturing, Top Herbal Supplements...,
How to Market Private Label Supplements, How To Sell Supplements (×2), Top 10 Mistakes... (×5).

**Confirmed broken links** (checked with a direct request outside the browser, not just Kenzie's
manual click-through):

| Link target | Status | Where |
|---|---|---|
| `/blog/how-do-i-start-a-private-label-supplement-business-0` | 404 | 5 posts — same dead link, copy-pasted (Why Wellness Businesses..., What Qualifications..., Tips for Selling...Immunity, How to Spot High-Quality..., How To Private Label Protein Supplements) |
| `/blog/how-to-promote-your-private-label-supplements-on-social-media` | 404 | needs the `dev-blog/` prefix — the real post is one path over |
| `/blog/top-questions-consumers-have-about-private-label-supplements` | 404 (redirect) | Still a **DRAFT** in HubSpot (id 220638601745), never published, but "Managing the Top 3 Risks..." links to it as if live |
| `/blog/are-liquid-vitamins-better-than-pills`, `/blog/best-liquid-vitamins-for-kids` | 404 | Liquid Supplement Manufacturing: Benefits vs. Costs |
| `/blog/liquid-vitamin-benefits-and-uses` | 404 | Private Labeling Liquid Vitamins |
| `/blog/do-supplements-need-fda-approval` | 404 | How to Scale Your Business... |
| `/blog/how-dmg-supports-mitochondrial-function` | 404 (×2 on the page) | Trending Private Label Supplements |
| `/blog/fda-and-selling-supplements-what-you-need-to-know` | 404 | Challenges and Opportunities... ("Related Content") |
| `/private-label`, `/private-labeling`, `/private-label-get-started`, `/shop-supplements.html` | all 404 | old DaVinci-era paths, referenced from Top 10 Mistakes, Supplement Dropshipping: Can It Boost Profitability, Supplement Dropshipping: 5 Best Tips |
| `/hubfs/Praxera_Infographic (2).pdf` | 404 | How to Scale Your Business... — the Competitor Comparison Chart image is also broken on that page |
| `www.fda.gov/regulatory-information/.../dietary-supplement-health-and-education` | 404 (real FDA page, gone) | What Is a Nutraceutical? |
| `www.fda.gov/food/dietary-supplements-guidance-documents-regulatory-information/current-good-manufactur...` | 404 (real FDA page, gone) | USP, NSF, GMP, and FDA... |
| `healthcenter.uga.edu/protein-powder-...` | 404 | Top Private Label Protein Powders |
| `belabelwise.org` | 500 (server error) | An Introduction to Sports Supplement Manufacturing |
| `fimdefelice.org/about-fim` | SSL failure, site broken | What Is a Nutraceutical? |
| A literal broken citation link: `https://l "_enref_1" /o "Cooperman, 2025 #4547` | malformed | "Are Private-Label Vitamins a Profitable Business?" — this is a leaked Word/EndNote reference-manager field code that got pasted straight into a live link |

**Links that returned an error to our automated checker but are likely just bot-blocked, not
actually broken** (PubMed, NSF.org, ods.od.nih.gov, GrandViewResearch, ResearchGate, ScienceDirect,
Tandfonline, USP.org, CDC, ASHA, Forbes, Canva, Adobe — 47 links total, all 401/403/timeout from
sites known to challenge scripted requests). Not claiming these are broken — flagging so a human
click-through can confirm, the same caveat Kenzie gave for the couple she hit personally.

**Link-color consistency** — genuinely messy on ~20 of the 66 migrated posts (mixing the theme's
correct green `#6BA644` with a leftover blue `#6BBFEC`, and a handful of one-off colors like
`#4A6EE0` or near-black that look like copy-paste accidents). **The 5 newer, non-migrated posts use
a consistent two-color scheme on purpose** (a distinct blue for citations/sources, green for
internal links, ~17-18 blue vs 1 green each) — that one looks intentional, not broken. Full
per-post color breakdown is in the raw data if useful.

### A3. Confirmed clean (already checked, no work needed)

- No new em-dashes introduced by the migration anywhere (matches Kenzie's manual counts post for
  post).
- No leftover davincilabs.com links.
- No real content shrinkage — the "shorter than original" and "missing headings" alarms from the
  first automated pass were both measurement artifacts (the FAQ module lives outside the area that
  pass was scoped to) and cleared to zero once corrected.

---

## Section B — two decisions needed before touching content

**B1. Format standardization.** 5 posts (the ones with the broken `#faq` anchor above) were
written fresh, not migrated, and look and read differently from the other 66: they have a "Key
Takeaways" block and a working Table of Contents; the other 66 don't. Jelena flagged this directly
on "Contract Manufacturing vs Private Labeling": *"Different format compared to other blogs with
Key Takeaways at the top."* Question: is this the new standard going forward (bring the other 66
up to it), a one-off for these 5, or does it not matter? Changes the size of the job by an order of
magnitude either way.

**B2. Scope for the two "custom formulation" posts.** "Custom Supplements vs. Private Label
Supplements" and "White Label Supplements vs. Private Label: What Is the Difference?" aren't just
posts with a banned phrase in them — their entire premise is a comparison Praxera can't make
honestly, since it doesn't offer custom formulation. Rewrite the premise, or retire the posts?

**B3 (smaller, same shape).** Is "guarantee"/"guarantees"/"guaranteed" a banned word like "custom
formulation," or is it fine in context? 16 posts are affected either way.

---

## Section C — proposed execution plan (not started)

**Phase 1 — zero-risk, systemic, do first.** Fix the FAQ module's heading tag (one file). Re-crawl
all 71 posts afterward to confirm every `#faq` anchor now resolves and nothing else moved.

**Phase 2 — mechanical, low judgment, per post but scriptable.** Ⓡ→® swap, the 3 missing bylines,
the shared dead FDA-regulations link (one corrected destination, applied to 5 posts), the
`dev-blog/` prefix fix, the malformed citation link, the stale-year fixes on the 3 identified posts.
Each post gets a before/after backup the same way the hero-widget restore did earlier this session,
verified live before moving to the next.

**Phase 3 — needs the Section B answers first.** "Custom formulation" and "guarantee" language
rewrites, the two full-post scope calls, and whether to standardize format across all 71.

**Phase 4 — judgment calls, smallest batch.** Link-color cleanup on the ~20 messy posts (strip the
stray inline colors, keep the theme green) — proposed as its own batch since "which color is
correct" needs a quick visual confirmation, not just a find-and-replace. Bot-blocked links get a
manual click-through pass rather than a script, same as Kenzie's approach.

Every phase: backup before, small batches (5-10 posts), re-verify with Playwright after each batch,
nothing published without your sign-off per the standing rule.

## Source data

Kenzie's document, the sign-off sheet's open comments, and all raw crawl/link-check JSON are
available on request — not checked into the repo (large, browser-session-specific).
