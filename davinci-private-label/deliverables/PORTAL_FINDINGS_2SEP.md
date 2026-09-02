# Portal findings, 2 September 2026

Queued for Hindsight — the retain failed on `Insufficient credits. Balance: $-0.01`.
Push this into Hindsight once the account is topped up.

## The apex-redirect bug — the one that blocked publishing

All 62 Praxera site pages were assigned to **`praxerasupplements.com`**, the apex, which is
configured `redirectTo = www.praxerasupplements.com`. HubSpot will not publish content to a
domain whose job is to redirect. That was the whole cause of *"it won't even let me publish
a page"*.

Fix: `PATCH /cms/v3/pages/site-pages/{id}` with `{"domain": "www.praxerasupplements.com"}`.
All 62 moved, zero errors; per-page log in
`backups/custom-formulation-removal/domain_move_log.json`.

Blog posts were already correct — they inherit `www` from the blog's settings, not from a
field on the post.

**Rule for next time:** when a HubSpot publish is refused, check the page's assigned domain
against `/cms/v3/domains` `redirectTo` before anything else. Apex-vs-www is easy to miss
because the page URL still looks right.

## Blog structure — decided

Praxera's blog stays a **subdirectory** at `www.praxerasupplements.com/blog`. No
`blog.praxerasupplements.com`. It consolidates SEO on one domain, the 134-entry redirect map
already targets `/blog` URLs, and `blog.davincilabs.com` is a legacy pattern rather than a
model. Shawn agreed 2 Sep. Do not set the subdomain up.

## The "Private Label" theme is Praxera's, despite the name

Nine templates under `Private Label/Templates/` render the Global Footer module, and **no live
content on any brand uses them**. Verified across all three content types:

| brand | blog template theme |
|---|---|
| DaVinci | `DaVinci_2023`, `DaVinci_new_2019` |
| PetTech | `Pet_Tech_Labs` |
| VetriScience | `VetriScience` |
| **Praxera** | **`Private Label`** — the only one |

**Blog posts carry no `templatePath`.** The template is set on the *blog* (content group), so
check `/content/api/v2/blogs`. Checking only site-pages and landing-pages misses this
entirely — it was a real hole in an earlier safety check.

## Module and editor know-how

- **"Card 1, Card 2…" in the sidebar** is fixed by `occurrence.sorting_label_field` in the
  module's `fields.json` (e.g. `"cards.title"`). 13 of the theme's 24 repeaters already set it;
  11 do not. Worth doing: Tile Grid (`tiles.tile_label`), FAQ (`items.question`), Stat Band,
  How It Works, and the button groups.
- **`PL - Card Grid` has no column field.** Layout is
  `repeat(auto-fit, minmax(min_column_width, 1fr))`, so cards-per-row is arithmetic: N fits
  when `N*min_column_width + (N-1)*gap <= max_width`. At `max_width 1200 / gap 24`,
  `min_column_width 340` forces 3-across (four would need 1432px). Anything 283–384 gives 3.
- **`PL - Tile Grid` has an `accent_glyph` field**, default empty, set on only 4 of 258 Praxera
  tiles — three "AND MORE" tiles at size 56 (intended) and one stray on the home Gummies tile
  at size 32 (cleared). A mystery "+" on a tile is this field.

## Mistake worth not repeating

A prepared `fields.json` built from a 21:35 read sat in a script while a permission block was
in place. When the block cleared at 22:10 it was fired without re-reading, and Shawn had edited
that same file by hand in between. The end state happened to match, but any other change he
made in that window was reverted. **Re-read immediately before PUTting a prepared write.**

## Write permissions in this harness

CMS page `PATCH` worked throughout. The source-code `PUT` for theme files was refused by the
auto-mode classifier twice, then allowed later in the same session — a refusal is not
necessarily permanent, but do not hammer it; stop and tell the user.

**Do not use ClientCommand's `call_hubspot_as_client` for this client.** Portals DaVinci Labs,
FoodScience and Pet Tech Labs all return `[]` for stored credentials, so it falls back to QBS's
global token and would write to portal **20682069** instead of the client's **4087538**.

---

# Second batch — client call and fixes, 2 September (evening)

Also queued for Hindsight; the retain failed again on `Insufficient credits. Balance: $-0.01`.

## LAUNCH IS 14 SEPTEMBER, NOT 30 SEPTEMBER

From the 2 Sep call. Sarah: *"targeting the 14th for a core site launch"*; Patrick agreed.
Remaining pages updated by the 30th. Tammy's reasoning: all DaVinci branded sites go live
9/30 and her team will have no capacity to troubleshoot Praxera that week, so Praxera
launches quietly first — *"Nobody even knows what the hell Praxera is… a tree falling in the
woods."* Patrick added it buys an SEO head start: both sites live, canonical switched to
Praxera, then wind DaVinci private-label content out of the nav.

Tammy reports on-track weekly to her CEO and cannot report a slip a week out.

## Three defects fixed — 39 pages, all backed up and verified

1. **AND MORE tiles were broken, not unlinked.** Patrick told Tammy on the call *"that's not
   linked anywhere yet."* Wrong — all 20 pointed at `/pl-demo-pillar`, which does not exist
   on praxerasupplements.com, so they would 404. Repointed to `/learning/definitive-guide`.
   **Lesson: "not linked" and "linked to a dead slug" look identical in the editor.**
2. **The literal "None"** Tammy caught under Frequently Asked Questions is a Python `None`
   that a build script stringified into the FAQ module's `section_subhead` as
   `<p style="…">None</p>`. It was on **22 pages**, not the two she saw. Cleared to `""`.
   If a stray "None" reappears, look for a generator writing `str(None)`.
3. **Removed the "Dropship Private Label Supplements" link** from the resources card. It was
   also a DaVinci outbound link, so resources dropped 19 → 18.

## Dropshipping

Tammy: *"We do not want to offer drop shipping… this can't go live like this."* The page is
built on the service end to end — fulfilment claims, "built-in dropshipping infrastructure",
a full FAQ on fulfilment times and international dropshipping, and the meta description.
Rewriting it as informational is a full rewrite. It is DRAFT, so the pre-launch action is
simply **do not publish it** — put it on the launch checklist as an explicit exclusion.

**Still open:** `our-process` reads *"Inventory ships to your warehouse or we dropship direct
to your customers."* That contradicts her instruction but is reading copy on a page she did
not review, so it needs her word.

## Settled — stop asking

- **Email:** one address, `info@praxerasupplements.com`. John (IT) setting it up. No per-rep
  addresses. The three people are Mindy, Arielle, Lindsey.
- **Blogs** come to Praxera, not the new DaVinci site. Dan asked, Sarah confirmed.
- **Praxera contact form:** no topic dropdown — every enquiry is private label. Same shared
  inbox. On the DaVinci side "private label" and "set up an account" come off at split.
- **Consumer traffic** to Shopify/Klaviyo 9/30; practitioners stay in HubSpot.
- **Blog stays a subdirectory.** No `blog.` subdomain.
- **The theme is not being renamed.** Shawn: *"just leave the theme alone."*

## Still open from the call

Design Services overpromises — remove "Talk to a designer" (no capacity), merge the two boxes;
Tammy pasted replacement copy into the Zoom chat that **only Patrick has**. Chewables and
capsules images washed out — natural tones, explicitly not bright red or blue because *"those
bright colours are synthetics"*. Amazon icon unrecognised — replace with an add-to-cart bag.
Stray caret on resources. Widow words. Guides: add Ariel's YouTube clips, refresh the 2024 CRN
survey, reattribute the old testimonial to **Melinda Elmadjian, Contract Manufacturing
Business Leader** — *"it's not corporation, it's LLC."*

## Correction to the call

Sarah said the privacy page still has `[BRAND_TBD]`. **It does not** — zero `BRAND_TBD`, zero
`[ALL_CAPS]` placeholders, zero bare "TBD". Confirm with her so it is not chased twice.
