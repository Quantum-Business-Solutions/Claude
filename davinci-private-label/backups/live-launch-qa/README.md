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

---

# Post-launch QA sweep

Run after the blog went live and the nav was rebuilt. All 63 pages plus the blog listing and
its posts, 80 URLs. `tools/full_site_qa.py` regenerates it;
`fullqa-postlaunch.json` is the raw output.

## Playwright could not be used

Its bundled Chromium cannot reach the site from this environment - `ERR_CONNECTION_RESET`
through the agent proxy, across three configurations (default, explicit `proxy=`, and
`--proxy-server` with the CA bundle and `--ignore-certificate-errors`). Ordinary HTTP
fetches work fine, so the sweep was done that way.

**What that means for coverage:** status codes, rendered HTML, links, nav, metadata and
copy are all checked. **Not** checked: JavaScript-rendered content, visual layout,
responsive behaviour, or console errors. Those need a browser on a machine that can
reach the site.

## Fixed and confirmed live

- **Blog listing.** Praxera nav renders, zero links to davincilabs.com, 16 posts listing.
  The blog-level `listing_template_path` was never the lever - the listing is a **page
  object**, id `220598739288`, that only the HubSpot UI can reach. Every CMS API returns 404
  for that id: site-pages, landing-pages, blog-posts, v2 pages, filtered queries, archived.
  Justin set its template in the page editor and published it. Worth remembering: a blog's
  listing template can be overridden by a page object that is invisible to the API.
- Header nav present on **all** pages.
- Visible DaVinci text down to a single source, described below.

## Outstanding

| Issue | Scale |
|---|---|
| DaVinci in blog **author names** | 15 posts |
| Links to davincilabs.com | 31 pages |
| `/fitness` serving stale `pl-demo` links | 7 links |
| Blog posts with an empty `href` | 5 posts |
| Placeholder copy | `/about`, `/contact` |

**Author names are the notable one.** 13 posts are bylined "DaVinci Healthcare Expert", one
"DaVinci Industry Expert", one "Dom Orlandi, President of DaVinci". Renaming three author
records clears all 15. 20 posts are already bylined Melinda Elmadjian.

**`/fitness` is stuck.** Its draft contains zero `pl-demo` references and it was pushed live,
yet the published page still serves seven of them, all 404ing. Every other page took the same
fix. It was the only page in that state out of 63 - probably needs a manual republish.

## A false positive in my own scan, recorded so it is not chased

The sweep flagged 77 pages for first-person manufacturing claims. That was the regex matching
**"Our Facility"** - a navigation item added when the menu was rebuilt earlier the same day.
Real manufacturing-claim counts are unchanged. A pattern written against page copy will start
matching navigation once navigation exists; scope such checks to the content area.
