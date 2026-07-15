---
name: qbs-atlas-page-builder
description: Use this skill when creating, migrating, editing, cleaning up, or pushing pages on Quantum's HubSpot portal under `atlas-theme child 2024`. Trigger on phrases like "create a new page on Quantum's site", "migrate to atlas", "rebuild the page", "push pages to HubSpot", "clone an atlas page", "update the website", "fix the website", "find duplicate pages", or any reference to `layoutSections`, `dnd_area`, `home.html`, `landing-page.html`, or migrating from legacy themes (CTA9, `Quantum_Business_Theme_CTA9`, Brightlane, ProX, Session). Also trigger on "Oops! Page not found" placeholder issues, broken atlas pages, "template is missing" errors, or any programmatic touch of `layoutSections` on QBS portal `20682069`. Encodes the clone-and-mutate pattern, the `dnd_area`-name rule, the dual-href CTA structure, real atlas template paths, and the atomic PATCH+push-live publish flow. Requires PAT auth — token setup is in `qbs-hubspot-private-app`. Covers both website (site) pages and landing pages.
---

# QBS Atlas Page Builder

Encodes the safe pattern for creating, migrating, editing, and cleaning up pages on Quantum's HubSpot portal using the `atlas-theme child 2024` theme. Replaces brittle "build modules from scratch" approaches with the clone-and-mutate pattern that preserves the Atlas drag-and-drop area structure.

## Dependency: token setup

This skill assumes a PAT is already loaded as `$TOKEN` and verified against portal `20682069`. The `qbs-hubspot-private-app` skill handles that — see its `verify.sh` and `helpers.sh` for the cold-start sequence. Don't duplicate token-setup work here; just confirm `$TOKEN` is set and call its helpers.

## When to use vs. not use

**USE this skill when:**
- Creating a new website (site) page or landing page on the QBS portal
- Migrating a page from a legacy theme (CTA9, `Quantum_Business_Theme_CTA9`, Brightlane, ProX, Session) to atlas
- Editing `layoutSections` on an existing atlas page programmatically
- Investigating "Oops! Page not found" placeholder issues, "This page's template is missing" errors, or broken atlas pages
- Cleaning up duplicates, archived-but-still-live pages, or zombie pages on `thequantumleap.business`

**DO NOT use this skill when:**
- The user only wants to change page metadata (name, slug, htmlTitle, metaDescription) without touching `layoutSections` — a plain `PATCH /cms/v3/pages/{type}/{id}` is fine
- The change can be made in HubSpot's editor in under a minute — manual is faster than API for one-off tweaks
- The user is editing blog posts (use `qbs-blog-post-creator` instead)

## The five cardinal rules

These are non-negotiable. Skipping any of them produces broken pages with extreme reliability.

### 1. `dnd_area.name` must be the literal string `"dnd_area"`

The atlas templates inject content into a section literally named `"dnd_area"`. Timestamped or suffixed names like `dnd_area_<timestamp>` orphan all your modules — the page renders the template's empty-state placeholder ("Oops! Page not found") instead of your content, and the editor misbehaves. Always use exactly `"dnd_area"`.

### 2. Clone an existing live atlas page — never build rows from scratch

The atlas DnD area depends on specific row IDs (e.g. `cell_1771797653512`), cell names, and module names being preserved. Constructing fresh rows in JSON breaks the DnD area; modules render but the editor breaks. Default reference pages:

| New page type | Clone from | Page ID | Template |
|---|---|---|---|
| Website (site) page | `/website-services` | `178783732741` | `home.html` |
| Landing page | `/bta-2024` | `169342159475` | `landing-page.html` |

The workflow is read-modify-write: GET the reference, deep-copy its `layoutSections`, walk the copy and mutate ONLY content fields (text, images, CTAs) inside cells, never touch row/cell/module IDs. See `references/atlas-pattern.md` for full mechanics.

### 3. CTAs have TWO href fields — update both

Atlas anchor structure:

```json
{
  "text": "BOOK A DEMO",
  "anchor": {
    "href": "https://meetings.hubspot.com/...",
    "link": {
      "no_follow": false,
      "open_in_new_tab": true,
      "url": {
        "href": "https://meetings.hubspot.com/...",
        "type": "EXTERNAL"
      }
    },
    "type": "link"
  }
}
```

`anchor.href` (top) and `anchor.link.url.href` (nested) should always agree. If they diverge, the nested one usually wins on click, so the user lands somewhere different from what the inspector shows. When you set a new external URL, also set `link.url.type` to `"EXTERNAL"`.

### 4. Use real templates only

Real atlas-theme child 2024 templates:

| Template path | Used for |
|---|---|
| `atlas-theme child 2024/templates/home.html` | Most service / website pages (the homepage and `/website-services` use this) |
| `atlas-theme child 2024/templates/about.html` | About / contact-style pages (`/about-us`, `/contact-us`) |
| `atlas-theme child 2024/templates/landing-page.html` | Landing pages (`/bta-2024`, all live LPs) |

`atlas-theme child 2024/templates/site-page.html` does NOT exist. Made-up paths produce "This page's template is missing" in the editor.

### 5. Atomic publish: PATCH then push-live

```
PATCH /cms/v3/pages/{site|landing}-pages/{id}    (with full layoutSections)
POST  /cms/v3/pages/{site|landing}-pages/{id}/draft/push-live    (no body)
```

Don't try `state: "PUBLISHED"` with `publishImmediately: true` — the state field changes but the page never actually publishes (`currentlyPublished` stays null and the URL keeps 404ing). Use the explicit `/draft/push-live` action endpoint.

## The 4-layer mental model

The atlas theme owns the chrome. We own the content. Four layers, never blur them:

1. **Theme settings** (colors, fonts, button styles) — Settings → Website → Themes → atlas-theme child 2024 → Edit theme settings. Never override these with custom CSS.
2. **Global header / footer** — Atlas Global Content Editor. Page-creation code never touches `.header-container`, `.navigation-primary`, `.footer-container`, or any menu classes.
3. **Page content** — pushed as native `layoutSections` so HubSpot's drag-and-drop editor still works.
4. **Enhancement CSS** — about 30 lines max in `headHtml` (fonts plus a small set of QBS utility classes). Nothing else.

Most page-creation bugs trace to mixing these layers — putting page content in `footerHtml`, or using `display: none !important` to hide an Atlas module instead of removing it from `layoutSections`.

## Pre-flight and self-QA checks

Before declaring any page operation "done":

- `dnd_area.name` is the literal string `"dnd_area"` — not timestamped, not suffixed
- Row count matches the reference, OR if rows were added, every cell/module `name` is unique across `layoutSections`
- Every CTA's `anchor.href` and `anchor.link.url.href` agree (run the dual-href validator from `references/atlas-pattern.md`)
- `templatePath` is one of the three real atlas-theme child 2024 templates
- No empty `href=""`, no `#webinars` / `#resources` anchors that don't exist on the new page
- Snapshot saved to `/tmp/snapshot_<timestamp>/` if more than ~10 pages are about to change

## Common pitfalls (do not repeat these)

Real failure modes from past work — listed so you don't recreate them:

- Building rows from scratch with hand-written JSON instead of deep-copying real ones from a reference page. The DnD area breaks; editor shows orphan styling. (Duplicating an *existing* row from the same page and suffixing its names is fine — see "Adding rows, images, and videos".)
- Generating a unique `dnd_area` name like `dnd_area_<timestamp>_<id>`. Template doesn't render the section; "Oops! Page not found" placeholder appears.
- Using a made-up template path (e.g. `site-page.html`). HubSpot shows "This page's template is missing."
- Updating only `anchor.href` on a CTA. The nested `anchor.link.url.href` keeps the old URL and becomes the actual click target.
- Trying to publish a draft via `PATCH state=PUBLISHED, publishImmediately=true`. The state changes but the page never publishes; URL keeps 404ing.
- Editing the parent `@marketplace/kalungicom/atlas-theme/...` instead of `atlas-theme child 2024/...`. Always edit the child theme.
- Inline `<style>` overrides inside rich-text content. Use theme settings instead — inline styles won't survive theme updates.
- Hiding modules with `display: none !important` instead of removing from `layoutSections`. They reappear on next save.

## Adding rows, images, and videos

The clone-and-mutate pattern doesn't limit you to the reference page's row count — you can add rows, images, and videos as needed. The constraint is on inventing new *module types*, not on duplicating rows of types that already exist on the reference.

### Adding more rows

To extend a page beyond the reference's row count (e.g., reference has 6 rows, you need 19): deep-copy an existing row that contains the module type you want, then walk the copy and suffix every `name` field on rows, cells, and modules with a unique tag (e.g., `_s07mining`, `_s14objections`). Module IDs themselves should NOT change — the suffix goes on the `name` field only. This keeps every module instance uniquely addressable in the DnD editor while preserving the underlying module type. Verify after: every `name` in `layoutSections` is unique, no two cells/modules share the same string.

Reference templates' default row count and what they contain:

| Template | Rows | Section types available to clone |
|---|---|---|
| `home.html` (e.g. `/website-services`) | 6 | hero, H2+rich-text+sidebar, product-features (3-col), CTA, FAQ |
| `landing-page.html` (e.g. `/bta-2024`) | varies | hero, form, testimonials |

### Uploading images for a page

Use the Files v3 API. Upload to a folder named after the page slug so assets stay organized:

```
POST /files/v3/files
  -F file=@/path/to/image.png
  -F options='{"access":"PUBLIC_INDEXABLE","overwrite":false}'
  -F folderPath="/sales-blitz-playbook"
```

The response includes `id` and `url`. Use the `url` directly in `<img src="...">` tags inside Rich Text module content. Save the upload manifest (filename → url + id) to a local JSON file so subsequent edits can reference assets without re-uploading.

### Embedding images in modules

Inside a Rich Text or H2 module's `params.content` HTML:

```html
<img src="https://20682069.fs1.hubspotusercontent-na1.net/hubfs/20682069/<page-folder>/<filename>" 
     alt="Description" loading="lazy">
```

Cap oversized images via `headHtml` CSS rather than inline width, so a single rule can re-size all instances:

```css
img[src*="rev-efficiency-model"] { max-width: 720px !important; display: block; margin: 24px auto !important; }
img[src*="show-rate"] { max-width: 480px !important; }
img[src*="screenshot"] { max-width: 320px !important; border: 1px solid var(--ql-border); border-radius: 8px; }
```

White-background logos (e.g. partner logos like ConnectAndSell) on a dark theme need a containing white card so they don't punch a hole in the design — wrap with padding + white background.

### Embedding YouTube / Vimeo videos

Inside Rich Text module content:

```html
<div style="max-width:800px;margin:16px auto;border-radius:12px;overflow:hidden;">
  <iframe src="https://www.youtube.com/embed/VIDEO_ID" 
          frameborder="0" allowfullscreen 
          style="display:block;width:100%;height:450px;border:0;"></iframe>
</div>
```

Inline `height:450px` is the most reliable way — global `iframe { height: 100% }` rules in `headHtml` will collapse the iframe to zero height inside auto-sized parents. If you must use a CSS rule, use `min-height` instead of `height`.

### Reference visual examples

Two QBS pages currently embody the long-form playbook pattern (dark theme, gold accents, ql-* utility classes, mixed text + images + video):

| Page | ID | Notes |
|---|---|---|
| `/sales-sequences-playbook` | `207926720522` | Original visual reference. Uses footerHtml for content (NOT recommended — modules not editable). |
| `/sales-blitz-playbook` | `212452502626` | Recommended pattern: content in `layoutSections`, design system in `headHtml`. Use this as the clone source for any future long-form playbook page. |

## File map

```
qbs-atlas-page-builder/
├── SKILL.md                  ← you are here
└── references/
    └── atlas-pattern.md      ← detailed clone-and-mutate workflow + curl recipes
```

## When in doubt

If a planned mutation requires a section type that doesn't exist on any QBS atlas page (e.g., an accordion, a tabbed widget, a video gallery component you've never seen rendered before), the right move is to do that work in the HubSpot UI — clone the reference page in HubSpot, drop in the new section via drag-and-drop, save. Then GET the saved page and use *that* as the new reference for any further automation. Don't try to construct novel DnD module specimens in JSON.

Adding *more rows of section types that already exist on the reference page* is fine — see "Adding rows, images, and videos" above.
