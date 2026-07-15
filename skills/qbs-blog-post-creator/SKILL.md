---
name: qbs-blog-post-creator
description: Create blog posts for the Quantum Business Solutions blog (thequantumleap.business) in QBS's established visual format and structure, then push live or save as draft via HubSpot API. Triggers when the user asks to write, draft, create, or publish a blog post for QBS, the Quantum blog, or thequantumleap.business. Also triggers on phrases like "write a blog post about X", "draft an article on Y", "publish a piece on Z", "new blog post", or "post to the blog". The skill matches QBS's exact visual design system (color palette, callout boxes, FAQ cards, TOC formatting), enforces the standard structure (Key Takeaways → TOC → 6-8 H2 sections → FAQ), validates against content cannibalization, and pushes the finished post to HubSpot portal 20682069. Always proposes the topic and full structure for review before pushing live.
---

# QBS Blog Post Creator

## What this skill does

Writes blog posts for thequantumleap.business in the exact visual and structural format QBS established across 265+ existing posts. Handles the entire pipeline: topic validation against existing content, outline approval, full draft, inline styling, metadata, and push to HubSpot via API.

## When to use vs. when not to use

**USE this skill when:**
- The user asks for a new blog post for QBS / Quantum / thequantumleap.business
- The user wants to draft an article on a specific topic for the QBS blog
- The user wants to add a post to the QBS Resources blog (separate contentGroupId)

**DO NOT use this skill when:**
- The user wants to write content for a different domain or blog (this is QBS-specific — the design system, brand voice, and HubSpot portal are all hardcoded)
- The user wants to edit an existing published post (use HubSpot UI for in-place edits, or build a separate edit-blog-post skill)
- The user wants generic blog content not destined for the QBS blog (just write it inline; no skill needed)

## Critical rules

**Push-live confirmation is required.** This skill never publishes a post live without explicit "yes, publish live" from the user. Default behavior is to draft + present for review, then publish only on confirmation. Even when the user says "publish it" up front, do a sanity check before the actual API call — show the title, slug, meta description, and word count, and ask one final time.

**Cannibalization check is mandatory.** Before writing, the skill must check the proposed topic against the existing blog inventory. QBS has known cannibalization clusters (CRM hygiene, ConnectAndSell, RevOps) where 5-12 posts already target the same keyword space. If the proposed topic falls into a cluster, the skill warns the user and offers to pivot before writing.

**Featured image is required.** Every post going forward gets a featured image. The skill prompts the user for an image file path, a stock image search term, or a HubSpot File Manager URL before pushing live. No more empty `featuredImage` fields.

**Internal linking is required.** Every post needs at least 4 internal cross-links to existing QBS blog posts or service pages. The skill reads the existing blog post list, suggests relevant cross-links based on topic overlap, and inserts them in-line in the body.

**Token comes from `CLIENT_HUBSPOT_TOKEN` env var.** Same pattern as other QBS skills. Never hardcode. Verify portal 20682069 before any API write.

## The QBS blog post format

Every post in the QBS visual system has eight structural elements in this exact order:

1. **Article wrapper** — `<article style="font-family: ..., line-height: 1.6; color: #222222; max-width: 1000px; ...">`
2. **Key Takeaways callout box** — light gray background (`#f8f8f8`), red left-border (`#e94560`), heading + bulleted list of 6-7 takeaways with selective `<strong>` emphasis
3. **`<!--more-->` break** — HubSpot read-more separator
4. **Introduction paragraphs** — 3-4 paragraphs, no heading, sets the stakes and previews the post
5. **Table of Contents box** — gray background (`#f9f9f9`), rounded corners, list of anchor links to each H2
6. **6-8 H2 sections** — each with anchor `id`, dark heading color (`#1a1a2e`), 5-8 paragraphs of body content. Light brand injection (1-2 sections explicitly Quantum-branded, others topic-driven)
7. **Conclusion section** — final H2, same styling, ties back to Quantum Q2 framework when relevant
8. **FAQ section** — H2 "Frequently Asked Questions", followed by 5-6 H3 Q&As each in a bordered card (`border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; margin-bottom: 20px;`)

**Standard length:** 4,000-6,000 words. Shorter posts feel lightweight relative to the rest of the blog; longer posts lose readers.

**Color palette (do not deviate):**
- Body text: `#222222`
- Headings: `#1a1a2e`
- Accent (links, borders, pull quotes): `#e94560`
- Light gray bg: `#f9f9f9` and `#f8f8f8`
- Light blue bg (used sparingly for TLDR/highlight boxes): `#f0f8ff`
- Borders: `#e0e0e0`

See `references/design-system.md` for the full inline-style cookbook.

## Workflow

### Step 1 — Topic validation

Run `scripts/check_topic.py "your proposed topic or title"`:

```bash
python3 scripts/check_topic.py "Buying group architecture in HubSpot"
```

The script:
1. Pulls all existing blog posts (titles only, fast)
2. Computes title-prefix overlap with the proposed topic
3. Flags any cannibalization risk (3+ posts targeting similar keywords)
4. Returns either GREEN (clear) or YELLOW (caution — show user the cluster) or RED (refuse — heavily saturated topic)

If RED, the skill stops and tells the user the topic is saturated and suggests a related angle.

### Step 2 — Outline approval

Skill produces:
- Proposed title (≤95 chars, includes the target keyword cleanly)
- Proposed slug (lowercase, hyphenated, ≤80 chars)
- Proposed meta description (140-160 chars, ends with brand mention)
- Proposed 6-8 H2 section headings with anchor IDs
- Proposed FAQ questions (5-6)
- 1-2 ConfigOptions: brand-injection level (light vs heavy), inclusion of Q2 framework callout

User reviews and approves or edits. **No writing begins until the outline is approved.**

### Step 3 — Full draft generation

Once outline is approved, skill writes the full body content following the design-system rules in `references/design-system.md`. Output is the styled HTML body with all 146+ inline style attributes correctly applied.

The draft is saved locally as `/home/claude/blog_draft_<slug>.html` for review.

### Step 4 — Internal links + featured image

Run `scripts/suggest_links.py <slug>`:
- Reads the draft body
- Pulls existing QBS blog post titles
- Suggests 6-10 relevant existing posts to link to from inside this draft
- User picks 4-6 to insert; skill rewrites the body with the links

Then prompt user for featured image:
- File path to upload via API
- Stock image search term (skill calls Unsplash API if available, else prompts for URL)
- Existing HubSpot File Manager URL

Image gets uploaded/referenced and set as `featuredImage` with `useFeaturedImage: True`.

### Step 5 — Push to HubSpot

Run `scripts/publish.py /path/to/draft.html`:

1. Verifies portal is QBS (20682069)
2. Constructs the full payload (title, slug, meta, body, contentGroupId, blogAuthorId, tagIds, featuredImage)
3. Shows final preview: title, slug, URL it will live at, word count, image URL
4. Asks user one final time: "Publish live, save as draft, or cancel?"
5. On confirm:
   - POST to `/cms/v3/blogs/posts` with state=PUBLISHED (or DRAFT)
   - PATCH publishDate to current timestamp (avoids the 1970 default)
   - For DRAFTs flagged for live: call `/draft/push-live`
   - GET to verify final state and URL
6. Reports back: live URL, publishDate, post ID

## What this skill never does

- Publishes to anything other than QBS portal 20682069
- Picks a topic for the user — topic is always user-provided or user-confirmed from suggestions
- Skips the cannibalization check (the saturation problem is real and the skill must enforce against it)
- Publishes without a featured image (regression from the 265-post no-image gap)
- Modifies existing blog posts (separate skill if needed)
- Schedules posts for future publish (HubSpot UI handles this better than API)

## Configuration

`scripts/_common.py` constants:

- `QBS_PORTAL_ID = 20682069`
- `QBS_DOMAIN = "thequantumleap.business"`
- `MAIN_BLOG_CONTENT_GROUP_ID = "66867919381"` — the `/blog` collection
- `RESOURCES_CONTENT_GROUP_ID = "181736274810"` — the `/resources` collection
- `DEFAULT_AUTHOR_ID = "85359369657"` — Shawn Peterson
- `CANNIBALIZATION_CLUSTERS` — list of saturated keyword prefixes that trigger warnings

If the user wants to post to the Resources blog instead of the main blog, pass `--resources` to publish.py.

## See also

- `references/design-system.md` — the complete CSS / inline-style cookbook with every reusable snippet
- `references/post-structure.md` — the section-by-section template with example prose
- `references/cannibalization-clusters.md` — the topics where new content should be carefully avoided
- `scripts/check_topic.py` — pre-write topic validation
- `scripts/suggest_links.py` — internal-linking helper
- `scripts/publish.py` — push to HubSpot with full safety checks
- `scripts/_common.py` — HTTP client, portal verification, design-system constants
