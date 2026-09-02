# Custom Formulation removal — prepared, NOT yet applied

Authorised by Shawn on 2 Sep 2026: "They are not offering custom formulation..
remove it from capabilities and delete the Praxera custom formulation page."

Both HubSpot writes were blocked by the Claude Code auto-mode permission
classifier. Everything up to the write is done and verified; the two calls
below are all that remain.

## Safety checks that passed first

- Templates referencing the Global Footer module: 9.
- Pages on those templates: 135 — 62 Praxera + 73 DaVinci `pl-demo-*-v3`.
- **PUBLISHED pages among them: 0.** Every one is a draft, so no live page moves.
- All 62 Praxera pages render the module DEFAULT; none has its own saved footer
  copy, so one edit reaches all of them.
- Nothing links to `/custom-formulation` except that page itself, so deleting it
  breaks no internal link.

## Change 1 — the footer

`fields.json.before` → `fields.json.after`, a surgical 424-byte removal of one
array element. Original formatting preserved; the file still parses; the two
structures are identical apart from that element.

    Capabilities        before                     after
      [0] Private Label Supplements   #      Private Label Supplements   #
      [1] Custom Formulation          #      Our Process                 #
      [2] Our Process                 #      Design Services             #
      [3] Design Services             #

    PUT /cms/v3/source-code/published/content/
        Private Label/Modules/Global Footer.module/fields.json
    multipart/form-data, field "file" = fields.json.after

Clears all six of Melinda's "remove Custom Formulation from the bottom"
comments at once.

## Change 2 — the page

    DELETE /cms/v3/pages/site-pages/216189433487

`Private Label - Page - Custom Formulation`, DRAFT,
https://praxerasupplements.com/custom-formulation
Full JSON captured in `custom-formulation-page-draft.json` and
`custom-formulation-page-published.json` — restorable by POST if wanted back.

## Deliberately NOT used

`call_hubspot_as_client` on the ClientCommand portal. That portal has no stored
PAT (`exists: false, will_fallback_to_qbs_global: true`), so it would have
authenticated with QBS's own token against portal 20682069 instead of the
client's 4087538 — a write to the wrong company's site.

## Still open after these two

Removing the *service* from the site is a bigger job than these two calls:
99 prose sentences on 26 pages, 55 mentions across 14 blog posts, 8 across
5 emails, the "Praxera - Custom Formulation - Auto-responder" email, and a
field option on Praxera - Main Lead Form.
