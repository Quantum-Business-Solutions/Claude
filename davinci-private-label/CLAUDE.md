# DaVinci Labs / FoodScience LLC — Praxera rebrand

Client: FoodScience LLC (DaVinci Labs). Contacts: Tammy Johnson (reports weekly to her CEO),
Sarah Miller (QA), Mindy (content). QBS lead: Patrick. HubSpot portal **4087538**, shared by
DaVinci, Pet Tech Labs, VetriScience and Praxera. Project: rename "Private Label" to
**Praxera** at `www.praxerasupplements.com`. **Core-site launch 14 September 2026**; remaining
pages by 30 September. Read `deliverables/CALL_ACTIONS_2SEP.md` for the current open list.

## Rules from the client — do not break these
- **Nothing publishes until cutover.** All work stays in drafts.
- **DaVinci is never mentioned on the Praxera site.**
- **Praxera does not manufacture.** Replace manufacturing claims with "Provider" language;
  the only permitted phrases are "turnkey production" and "US manufacturing" (Sarah's rule).
- **Praxera does not offer Custom Formulation or dropshipping.** Custom Formulation is gone
  from the footer and its page is deleted. The dropshipping page is excluded from the
  14 Sep launch and rewritten after; `our-process` still has one dropship sentence awaiting
  Tammy's wording.
- **Never change a slug.** The 134-entry redirect map depends on them.
- **Do not touch Pet Tech Labs or VetriScience content**, and do **not** change the portal's
  file-hosting domain — Praxera image URLs showing `pettechlabs.com` is normal shared-portal
  behaviour, not contamination.
- **Leave the "Private Label" theme name alone** (Shawn, 2 Sep). It is Praxera's theme; no
  other brand's live content uses it.
- Praxera blog stays a **subdirectory** at `/blog`. No `blog.` subdomain.

## Technical facts that cost time to learn
- Pages must be on **`www.praxerasupplements.com`**, not the apex — the apex is a redirect
  domain and HubSpot refuses to publish to it. Check `/cms/v3/domains` `redirectTo` first
  whenever a publish is refused.
- Edit drafts via `/cms/v3/pages/site-pages/{id}/draft`. Blog posts take their template and
  domain from the blog settings (`/content/api/v2/blogs`), not from the post.
- Theme files: `PUT /cms/v3/source-code/published/content/{path}`. The auto-mode classifier
  may refuse this; stop and tell the user rather than retrying.
- `PL - Card Grid` has no column count — cards per row follows from `min_column_width`
  (340 gives 3-across at max width 1200, gap 24). `PL - Tile Grid` has an `accent_glyph`
  field; a stray "+" on a tile is that field. Repeater labels in the editor come from
  `occurrence.sorting_label_field` in a module's `fields.json`.
- `archivedAt` of `1970-01-01` means **not** archived; `archivedInDashboard` is the real flag.
- Load page drafts in small batches — pulling all at once has hit out-of-memory.
- The HubSpot PAT is supplied by the user in chat. **Never write it to this repo.**

## Where things are
- `deliverables/` — client-facing records: sign-off page recipe, review instances, transcribed
  HubSpot page comments, call action list, findings.
- `backups/` — before-JSON for every page or theme file changed, with apply/rollback notes.
- `tools/` — the scripts; `find_mindy_items.py` classifies manufacturing and Custom
  Formulation mentions, `domain_move.py` moved pages apex to www.
- Key page IDs: home 216189433405, fitness 216179449410, design-services 216179449206,
  resources 216189433440, how-to-sell 216176671879, privacy 216194811650.
