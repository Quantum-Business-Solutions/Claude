# Which pages have comments, and how many

Built from the 28 HubSpot notification emails in Shawn's inbox, 17 Aug – 2 Sep 2026.

**There is no API for HubSpot's in-editor comments.** Every `/collaboration/*` and
`/annotations/*` endpoint 404s. `/cms/v3/comments` and `/comments/v3/comments` do respond,
but they return *public blog visitor* comments — 98 of them, none from Melinda or Sarah,
none on a Praxera page. So this index is assembled from the notifications, and it only
captures comments that emailed Shawn. If someone commented without triggering a
notification to him, it is not here.

Open the comments panel directly with `?commenting=true&csOpen=true`.

| page | comments | reviewers | open in editor |
|---|---|---|---|
| **Fitness Supplements** | **8** | Melinda (2 Sep) | [216179449410](https://app.hubspot.com/pages/4087538/editor/216179449410/content?commenting=true&csOpen=true) |
| **Get Started** | **5** | Melinda (17 Aug) | [216194811571](https://app.hubspot.com/pages/4087538/editor/216194811571/content?commenting=true&csOpen=true) |
| **Home** | **5** | Melinda (17 Aug ×3), Sarah (24 Aug ×2) | [216189433405](https://app.hubspot.com/pages/4087538/editor/216189433405/content?commenting=true&csOpen=true) |
| **How to Sell Supplements** | **3** | Melinda (17 Aug ×2, 2 Sep ×1) | [216176671879](https://app.hubspot.com/pages/4087538/editor/216176671879/content?commenting=true&csOpen=true) |
| Resources Hub | 1 | Melinda (2 Sep) | [216189433440](https://app.hubspot.com/pages/4087538/editor/216189433440/content?commenting=true&csOpen=true) |
| Design Services Hub | 1 | Melinda (2 Sep) | [216179449206](https://app.hubspot.com/pages/4087538/editor/216179449206/content?commenting=true&csOpen=true) |
| Privacy Policy | 1 | Melinda (2 Sep) | [216194811650](https://app.hubspot.com/pages/4087538/editor/216194811650/content?commenting=true&csOpen=true) |
| ~~How to Sell (page 219004967764)~~ | **4** | Sarah (24 Aug) | **PAGE DELETED — comments unrecoverable** |

**28 comments · 7 live pages · 55 of the 62 Praxera pages have comments at all.**

## The deleted page is the thing to know about

`219004967764` was a second "How to Sell Private Label Supplements" page. Sarah left four
comments on it on 24 Aug, including the single most consequential instruction anyone has
given on this project:

> **WEBSITE WIDE:**
> Remove any instance of "custom formulation"
> Update All instances of FoodScience Corp and fix with FoodScience LLC
> **Update all instances of "private label" with "Praxera".**
> The header is currently FPO, correct? Confirming that the logo we sent over should be used.
> Footer: Update "Praxera is part of the FoodScience LLC family of brands. We are…."
> Remove "sibling brand" sentence.
> **Do not connect with DaVinci. Please remove any instances of that word.**

Plus her manufacturing ruling — *"all instances of manufacturing replaced with Provider.
Caveat — turnkey production, us manufacturing… is ok"* — which is the client's own answer
to the exceptions question.

The page is gone, so those four are no longer visible to anyone in HubSpot. The full text
survives only in `HUBSPOT_PAGE_COMMENTS.md` in this repo.

## What this says about the process

In-editor comments are not a safe system of record: they die with the page. Sarah's
website-wide instruction was attached to a page that no longer exists, and nobody would
have known it was lost. Anything that matters should land in the sign-off page or the
Design Approval Sheet, not only in a comment bubble.
