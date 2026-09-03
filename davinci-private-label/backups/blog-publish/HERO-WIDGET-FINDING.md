# Why 42 posts show the wrong H1, no byline, and a dead CTA

One cause, three symptoms.

Each post's `hero` widget holds the correct `<h1>` and the byline. On **42 of 75 posts** that
widget carries a **`deleted_at` timestamp** (values cluster around `1788027xxxxxx`, so they
were flagged in one operation). HubSpot then ignores the widget and the template renders its
generic fallback hero instead:

- H1 becomes "Your brand. Our formulations." - identical across all 42
- the byline disappears
- the hero CTA renders `href=""`, so "Schedule a Consultation" reloads the page

The remaining 33 posts have no `deleted_at` and render correctly. The content is not missing
from any of them - it is present in the widget and simply suppressed.

## The API fix does not work

Tested on `blog/how-to-market-private-label-supplements`:

1. `PUT /content/api/v2/blog-posts/{id}` with `widgets.hero.deleted_at = None` - accepted
2. Read back: `deleted_at` is now `None`
3. Republished via `publish-action`
4. **Live page unchanged** - still the generic H1, still `href=""`

So clearing the flag is not sufficient. HubSpot appears to have dropped the widget from the
rendered layout when it was deleted, and restoring it needs the post editor - the same shape
of problem as the blog listing page, where `listing_template_path` was correct in the API and
the actual control lived on a page object only the UI could reach.

Before-state saved as `hero-test.before.json`. Nothing visible changed, so nothing was reverted.

## What this blocks

Three fixes all trace back to this and should not be attempted post-by-post through the API:

- 42 wrong H1s (39 of them published)
- 42 missing bylines
- 42 dead "Schedule a Consultation" CTAs - the primary conversion button on 55% of the blog

## Still clean to fix through the API

- 69 `/en/pl-demo-*` links across 47 posts
- 4 first-person manufacturing sentences
- 1 link sending readers to a Google search for "dmannose davinci"
