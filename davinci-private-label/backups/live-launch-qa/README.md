# Live-site QA, 3 September 2026

61 of the 63 Praxera pages were published today. This is the state of the live site as
crawled immediately afterwards, plus the one change made in response.

## Navigation is broken sitewide. One root cause.

The header and footer on every page render the HubSpot menu **"Private Label"**, id
`215784846432`. Every one of its five items looks like this:

```json
{ "label": "Private Label Supplements", "url": null, "page_id": null, "children": [] }
```

Labels were entered. Destinations never were, and no child items were ever added. That
produces exactly the two symptoms reported: clicking a header item does nothing, and there
are no dropdowns. It is not the theme and not caching.

Because every page renders the same menu object, **populating that one menu repairs all 60
pages at once.**

## Crawl results, all 63 URLs

| Defect | Count | Pages |
|---|---|---|
| Header links with empty `href=""` | 720 | 60 |
| Footer links pointing at `href="#"` | 660 | 60 |
| Links to `/pl-demo-*` (all 404) | 136 | 20 |
| Links to davincilabs.com | 56 | 30 |

The `pl-demo` links are the category tiles, seven destinations used 19 times each:
`pl-demo-womens-health`, `-mens-health`, `-probiotics`, `-sleep`, `-fitness`,
`-weight-management`, `-cognitive`, plus `-book-consultation` and `-design-team`.
Every one 404s. The correct Praxera slugs exist and return 200; the links were simply never
repointed at the rename.

**An earlier QA pass in this session missed these.** It searched for `pl-demo-pillar`
specifically rather than the whole `pl-demo-*` family, and reported zero broken AND MORE
links, which was true but far too narrow a question.

Of the DaVinci links, 27 go to `davincilabs.com/product-guide` and roughly 20 to
`blog.davincilabs.com`. `/guide-definitive-private-label`, the destination of the guide
download call to action, also 404s.

## The one change made

`/dropshipping` was returned to draft and now serves 404. Tammy on 2 September, 00:30:25:

> "I don't think we want this page. We do not want to offer drop shipping... this line in
> here at the top, we ship every order directly to your customer. We need to be out of that
> business... So maybe this has to be hidden for now, if you can't get to it. **But this
> can't go live like this.**"

It had been published with the other 60. Before-state is in `dropshipping-unpublish.before.json`.
Note that `currentState` is ignored by the CMS v3 PATCH; the field that works is `state`.

## Still live and still wrong

- The 404 page and `/blog` both still serve the full DaVinci Labs site, now to real visitors.
- `pl-module-library` and the duplicate `-temporary-slug-blog/...` page are draft, so both 404.

`link-crawl.json` holds the raw crawl output; `tools/crawl_links.py` regenerates it.
