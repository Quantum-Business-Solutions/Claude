# Praxera blog subscription — one toggle needed in HubSpot

**Portal 4087538 · Praxera Supplements Blog (content group 220598739286)**

## The problem
Seven Praxera forms show a tick-box labelled **"I would like to subscribe to the Praxera
Blog"**, but it writes to the contact property
**`i_would_like_to_subscribe_to_the_davinci_blog`**. A prospect ticks a box that says
Praxera and lands in DaVinci's blog subscriber pool.

| Form | GUID |
|---|---|
| Praxera - Main Lead Form | 6ae15824 |
| Praxera - Main Lead Form (legacy field set) | e88e8d00 |
| Praxera - Client Onboarding Guide | 81f2906b |
| Praxera - Onboarding Guide | 6d4066c8 |
| Praxera - Ingredients & Testing Guide (page form) | 2e55f9cc |
| Praxera - Ingredients, Testing & Certification Guide | 471fb48f |
| Praxera - Supplements Guide | dd7328fc |

(94 portal forms use that property in total; the other 87 are DaVinci's and stay as they are.)

## Why it can't be finished by API
The Praxera blog has **no subscription apparatus at all** —
`subscription_contacts_property`, `email_api_subscription_id` and the instant/daily/weekly/
monthly lists are all null or empty, and none of the portal's 1,301 contact properties
references content group 220598739286. Every sibling brand has the full set:

| Blog | Contact property | Subscription type |
|---|---|---|
| DaVinci | `blog_default_hubspot_blog_5451037108_subscription` | 4588996 |
| VetriScience | `blog_development_blog_146251300211_subscription` | 255736609 |
| Pet Tech Labs | *(blog not wired)* | 222466430 |
| **Praxera** | **none** | **none** |

HubSpot does not expose creation of any of it. Verified 13 Sep 2026:
- `POST /communication-preferences/v3/definitions` → **405 Method Not Allowed**
- `POST /email/public/v1/subscriptions` → **405 Method Not Allowed**
- `PUT /content/api/v2/blogs/220598739286` with the subscription fields → accepted but
  silently leaves them **null** (re-read confirms nothing changed)

405 means the method does not exist, so this is not a missing-scope problem — no token
could do it.

## The one action needed (HubSpot UI, ~1 minute)
**Settings → Content → Blog → Praxera Supplements Blog → Subscriptions → enable email
subscription.**

That single toggle provisions the contact property, the "Praxera Blog Subscription"
subscription type, the four frequency lists and the subscription form — the same set the
other brands already have.

## Then
Run `python3 tools/repoint_blog_subscription.py` (dry run) and then `--apply`. It finds the
new property automatically, repoints all seven forms, backs up each one first, and refuses
to run at all until the toggle has been done. It only ever touches forms whose name contains
"Praxera".

## Correction to an earlier report
I previously said this box was **pre-checked `true`** on the two main lead forms. It is not
— all seven have an empty `defaultValue`. The consent concern I raised does not apply.
