# Praxera official email templates

Four coded HubSpot email templates, built from scratch for Praxera. Until now every
Praxera email in portal 4087538 was a clone of a DaVinci original and there was no
Praxera template of any kind.

## Where they live

HubSpot portal **4087538**, inside the Praxera theme folder (named `Private Label`,
deliberately — leave that name alone):

| Template | Design Manager path | Template ID |
|---|---|---|
| Praxera - Newsletter | `Private Label/Templates/Email/Praxera - Newsletter.html` | 221806459065 |
| Praxera - Marketing Email | `Private Label/Templates/Email/Praxera - Marketing Email.html` | 221805678355 |
| Praxera - Blog Notification | `Private Label/Templates/Email/Praxera - Blog Notification.html` | 221805678351 |
| Praxera - Simple Email | `Private Label/Templates/Email/Praxera - Simple Email.html` | 221806459137 |

All four are pushed to both the `draft` and `published` source-code environments, are
registered as template type 2 (email), compile with **no errors**, and show as
available for new content. They are additions only — nothing existing was touched.

Repo copies: `assets/praxera-email-templates/` (source of truth is
`tools/build_praxera_email_templates.py`, which generates them).
Render screenshots: `reports/praxera-email-templates/`.

## What each one is for

- **Newsletter** — masthead with an editable kicker, intro heading + copy, three
  article blocks (thumbnail left, headline / teaser / link right), a dark CTA band,
  footer. An article block hides itself if its headline is left blank.
- **Marketing Email** — masthead, eyebrow, headline, the standard HubSpot rich-text
  body (`content.email_body`), one optional supporting image, a single primary CTA
  button with an optional footnote, then a pale-green positioning strip (no second
  button, so there is exactly one call to action).
- **Blog Notification** — for the Praxera blog subscription (id 3608525332). Pulls
  the post's featured image, title, date, author and summary from the blog-post
  context, with a "Read the post" button. Every token is guarded and has an editable
  fallback field, so the template also works as a hand-written post announcement.
- **Simple Email** — minimal chrome for onboarding and guide delivery: a compact
  masthead bar, the rich-text body, an optional button, a sign-off, the footer.

## Design decisions worth knowing

- **Dark masthead and footer on purpose.** Both bands are painted `#092637` with the
  *white* logo. Shawn reads email on a dark theme; a white masthead relying on a
  transparent PNG inverts badly in Gmail/Outlook dark mode. A dark plate does not.
  There are `prefers-color-scheme` and `[data-ogsc]` rules that re-assert the plate
  colours if a client tries to invert them.
- **The logo stretch bug is fixed.** `Praxera Logo White.png` is 612x208 but the ink
  only occupies x=88..523, y=74..140 — the box is mostly transparent padding. The
  cloned DaVinci emails inherited DaVinci's 245x107 attributes and stretched the
  Praxera mark by 15-43%. These templates declare 294x100 (masthead) and 197x67
  (footer), both exactly on the 612:208 ratio, plus `height:auto` so responsive
  scaling cannot distort it. Band padding is deliberately small because the PNG's
  own transparent margin already supplies roughly 36px of breathing room.
- **Brand palette** sampled from the real logo: green `#6CA843`, light tint
  `#A3D06F`, ink `#092637`, body copy `#33434C`.
- **Compliance.** No DaVinci / VetriScience / Pet Tech links anywhere, no purchase
  path or ecommerce, no manufacturing claim in Praxera's voice. Product CTAs go to
  `https://www.praxerasupplements.com/get-started`. Footer carries the approved FDA
  disclaimer verbatim from the live site, plus "a FoodScience LLC brand".
- **HubSpot requirements.** Every template carries `site_settings.company_*` (name,
  address 1/2, city, state, zip, country), `subscription_name`, `unsubscribe_link`
  and `unsubscribe_link_all`, so HubSpot will let a marketer publish them. The
  office-location id the other Praxera emails use is 221681937557.
- **Editability.** Headlines, kickers, button labels and links are HubL `{% text %}`
  fields; body and teaser copy are `{% rich_text %}`; images are `{% image %}`. The
  scalar fields use `export_to_template_context` so the template keeps full control
  of the bulletproof table markup while the marketer still gets real fields in the
  classic email editor. Typography for marketer-entered rich text comes from the
  `#hs-inline-css` block, which HubSpot inlines at send time.
- **Email engineering.** 600px table layout, role="presentation", `mso` ghost tables
  for the two-column article rows, VML-safe `bgcolor` on every painted cell, a
  `max-width:620px` media query that stacks to one column, preheader text field.

## How it was verified

- HubSpot compiled all four with zero errors and lists them as available for new
  content (`/content/api/v2/templates`).
- A throwaway draft email was created on `Praxera - Marketing Email.html` to confirm
  HubSpot accepts a coded Praxera template in email context; the draft was then
  deleted. No existing email was touched.
- Each template was rendered in Chromium at 650px, 375px, 320px and against a dark
  background and inspected. PNGs are in `reports/praxera-email-templates/`.

## Not done / open

- HubSpot exposes no server-side render endpoint on this portal, so the screenshots
  are of the template markup with HubL substituted locally, not of HubSpot's own
  output. A seed test send is still worth doing before the first real campaign.
- No Litmus/Email-on-Acid client matrix was run. Outlook behaviour is covered by
  ghost tables and `mso` rules but has not been observed in a real Outlook client.
- The blog notification reads the post from the blog-post context. That path could
  not be exercised without an actual notification send, hence the fallback fields.
- These are templates only. No Praxera email was migrated onto them — the existing
  111 are untouched, as instructed.
