# Rebuilding the navigation on the live site

3 September 2026, immediately after 61 pages were published.

## The whole site's navigation was dead, from one object

The header renders a HubSpot **menu object** called "Private Label", id `215784846432`,
through `Private Label/Modules/Global Header.module`. Every item in it looked like this:

```json
{ "label": "Private Label Supplements", "url": null, "page_id": null, "children": [] }
```

Labels had been typed in. Destinations were never set and no child items were ever added.
The module template does `href="{{ child.url }}"`, so a null url renders `href=""` and a
click does nothing; and it only draws a dropdown `{% if child.children %}`, so with no
children there were no dropdowns. Both reported symptoms, one cause.

Because every page renders the same menu object, this was **720 dead links across 60 live
pages** from a single empty object - and repairing that object repaired all of them at once.

### API gotcha worth remembering

`PUT /content/api/v2/menus/{id}` **accepts a payload containing `body.pages_tree` and
silently ignores it** - it returns 200 and changes nothing. The field that actually writes is
top-level **`pagesTree`**. Two updates were reported as successful before this was spotted;
always read the menu back and count the children rather than trusting the response.

Same class of bug as unpublishing: CMS v3 ignores `currentState` and honours `state`.

## The structure built

Five top-level items, matching the existing header design (the template puts items 1-2 left
of the logo and 3+ right, so the count matters). 44 child links, every destination verified
HTTP 200 before the write.

| Item | Links to | Children |
|---|---|---|
| Private Label Supplements | `/our-process` | 6 service pages + 7 supplement formats |
| Health Categories | `/` | 17 category pages |
| Quality & Trust | `/quality-standards` | 5 |
| About | `/about` | 4 |
| Resources | `/resources` | 5 |

**"Health Categories" points at the homepage and that is a compromise.** No category index
page exists, and the parent item is rendered as a real link rather than a hover-only label,
so it had to go somewhere. The homepage at least carries the category grid. A proper hub
page would be better and is worth raising.

## The pl-demo links

121 links across 18 pages pointed at `/pl-demo-*` slugs left over from the pre-rename demo
site. All of them 404'd; the real Praxera slugs existed and returned 200 the whole time.
Repointed and pushed live. Replacement matched the full quoted href (`"/pl-demo-sleep"`), never
a bare substring, so a longer slug could not be corrupted by a shorter one's rule.

`dropshipping` was skipped - the client deleted the page during this work, so the API 404s
on it. That is expected, not an error.

## Still outstanding

- **`/guide-definitive-private-label` 404s.** It is the destination of the "Download the
  Guide" call to action, so that lead-capture path is dead. `/learning/definitive-guide` is
  live and is the obvious target. The client also wants an inline form there instead of a
  button, which converts better - it needs a nominated HubSpot form.
- 1 `pl-demo` reference remains on the homepage.
- The footer menus are a different mechanism - `simple_menu` fields on the Global Footer
  module, rendering 660 `href="#"` links across 60 pages. Not yet touched.
- 56 links still point at davincilabs.com.
