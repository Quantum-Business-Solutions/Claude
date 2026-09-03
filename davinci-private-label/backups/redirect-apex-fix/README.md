# Redirect plan: apex -> www

Fixed 3 September 2026. Repo planning file only; nothing in HubSpot was touched.

## The problem

`reference/redirects.json` holds the 134 cutover redirects that carry DaVinci's
private-label search rankings across to Praxera. **59 of them pointed at
`https://praxerasupplements.com`** - the apex domain, which is configured in HubSpot
with `redirectTo = www.praxerasupplements.com`.

Every one of those 59 would therefore have been a double hop at cutover:

    info.davincilabs.com/pl-demo-about-v3
      -> praxerasupplements.com/about        (301)
      -> www.praxerasupplements.com/about    (301)

Google follows chains, but each hop bleeds a little link equity and adds latency, and
chains are a standard technical-SEO defect. These 59 are the money pages - about, the
category pages, the ad landing pages - so it is the worst possible set to lose equity on.

The 75 blog redirects were already correct.

## The fix

All 134 destinations now use `https://www.praxerasupplements.com`. Entry count, sources
and pairings are unchanged - only the destination host.

## Why this happened

Same root cause as the publishing block fixed on 2 September: the apex looks like the
canonical address but is a redirect. Anything generated before that was understood points
at the apex. Worth checking any other artifact that hard-codes a Praxera URL.

## Still outstanding

Only **1 of 537** redirects currently live in the portal points at Praxera
(`blog.davincilabs.com/praxera-supplements-blog -> www.praxerasupplements.com/blog`).
The other 133 in this plan are **not deployed**. They must be in place at cutover or the
old DaVinci private-label URLs will 404 and their rankings will be lost rather than
transferred. Deploying them is a deliberate cutover step, not something to do early -
the destinations are still drafts.
