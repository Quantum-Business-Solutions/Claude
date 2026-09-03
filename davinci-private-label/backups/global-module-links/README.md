# The guide download link, and a cross-brand redirect incident

3 September 2026.

## What was broken

The "Download the Guide" button under *Get the free Definitive Guide to Private Labeling*
pointed at `/guide-definitive-private-label`, which returns 404. The lead-capture path from
that block captured nothing.

The block is `Private Label/Modules/PL - Global Guide Offer.module` (the `pl-go__` CSS
prefix). It is a global module, so it renders on every page and appears in no page's
`layoutSections` - which is why searching page content for it found nothing.

## The incident: a redirect that hijacked two other brands

First attempt was a URL redirect. It was created with a **path-only** `routePrefix`
(`/guide-definitive-private-label`).

**Portal 4087538 serves DaVinci, Pet Tech Labs, VetriScience and Praxera from one instance,
and a path-only redirect matches that path on every connected domain.** Within a minute,
`info.davincilabs.com/guide-definitive-private-label` and
`www.pettechlabs.com/guide-definitive-private-label` were both 301ing to a Praxera page.

Shawn caught it and asked whether DaVinci was being redirected. It was.

Sequence: patched it to a full-URL prefix with `isMatchFullUrl` - still leaked; deleted the
redirect outright, on the reasoning that a dead button on Praxera is far less harmful than
hijacking two other brands' live URLs. Deletion confirmed against the API (404 on the id,
zero matching redirects remain). The edge cache held the 301 for a few minutes and then
cleared. All three domains verified back to 404, which is the state they were in before -
that URL has never existed as a page on any of them.

**Rule for this portal: never create a redirect with a path-only `routePrefix`.** Always
scope it with the full `https://www.praxerasupplements.com/...` form, and verify against
the other brand domains afterwards, not just the one you meant to change.

## The proper fix, and what is left

`fields.json` for the module now defaults `button.link.url.href` to
`/learning/definitive-guide`, which is live and returns 200. Written and verified.

**This is not yet visible on the site.** A global module's saved content overrides the
field default, so the stored value still holds the old URL. Changing the default only
affects fresh instances. Republishing the homepage did not pick it up.

Finishing it needs the HubSpot UI: Design Manager, open **PL - Global Guide Offer**, edit the
global content, set the button link to `/learning/definitive-guide`, publish. One field.

Alternatively a **domain-scoped** redirect would work, using the full-URL form - but given
the incident above, the module edit is the safer route.

## Related

`PL - Global Product Guide Link.module` is the source of the 27 links to
`davincilabs.com/product-guide`. Its `fields.json` carries no href default, so that URL is
also in saved global content and needs the same UI edit.
