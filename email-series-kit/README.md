# Email series kit (HubSpot nurture series, Content Library ready)

How the GoodSuite series (58 drag-and-drop HubSpot emails, 7 series) was built, QA'd and saved to the
Client Command Content Library, written so the same approach works for another client.

Built Nov 2026 for GoodSuite (HubSpot portal 20921734). Nothing here sends or enrolls anything.
Everything is created as a HubSpot DRAFT.

## What is in this folder

| Path | What it is |
|---|---|
| `dnd_email_recipe.md` | HubSpot DnD email widget structure, API gotchas, design QA checklist |
| `template/GoodSuite_DnD_Email_v1.original.html` | First version of the custom email template |
| `template/GoodSuite_DnD_Email_v1.template.html` | Final template (white-edge and square-border fixes, inline-block chips and buttons) |
| `tools/newtpl.py` | Generates the final template from the original |
| `tools/hs_model.py` | Local model of HubSpot's section/column wrappers, so you can render an email in Playwright and see what HubSpot will do |
| `tools/bind.py`, `iterate2.py`, `evalw3.js` | Non-breaking-space binding of last words, plus the stranded-word, overflow and short-line evaluators |
| `examples/goodsuite_capture_plan.json` | The 58 title, tag and summary entries used for `capture_content` |
| `examples/goodsuite_binding_keys.json` | Per-element nbsp binding choices (example output) |
| `examples/goodsuite_qa_report.md` | Earlier QA report for the series |

## The repeatable flow

1. **Plan the series.** One series per audience and trigger (for example "Copier lease renewal, prospects").
   Write a short arc, one message per email, one CTA per email.
2. **Build as DnD drafts.** Follow `dnd_email_recipe.md`. Always send the full `content.widgets` set on
   a PATCH (a partial set soft-deletes the omitted widgets). Use `call_hubspot_as_client` for client
   portals, never the QBS HubSpot connector.
3. **Template.** Rebrand `template/*.template.html`: colours, logo, footer, phone, address. Update an existing
   template with `PUT /content/api/v2/templates/{id}` and `{"source": ...}`. The source-code API needs multipart,
   which the MCP cannot send.
4. **QA in a browser.** HubSpot previews need a login, so render locally with `tools/hs_model.py`
   and check desktop and a 375px phone width. Things that went wrong and are fixed in the template:
   - every `.hse-section` gets inline 10px side padding (the "white edges"), overridden with `!important` head CSS
   - HubSpot's table reset breaks `border-radius` on `td`, so chips and buttons are inline-block anchors
   - `td { word-break: break-word }` splits words mid-word when an nbsp-bound phrase is too wide, so cap how many words you bind
5. **Verify against HubSpot.** Read every email back after the PATCH and diff it against the intended content.
   Do not trust a batch that reports success.
6. **Capture into the Content Library.**
   `capture_content(portal_id, hubspot_id, reason, title, summary, tags, audience)` per email.
   Re-capturing the same email makes a new version.
7. **Kits.** There is no MCP tool to create kits yet, so use SQL (see below). One kit per series, position
   equal to the email number, role `email N`, so `deploy_content` with `kit_id` deploys the whole series in order.
8. **Leave everything in draft.** Approval is a human gate. `deploy_content` is a dry run by default and
   creates drafts only.

## Library conventions used

Title: `<Series> | Email N | <Topic>`

Tags (placement is read from these):

- `type:nurture`
- `series:<slug>`
- `stage:prospect` or `stage:customer-expansion`
- topic tags, for example `managed-print`, `managed-it`, `cybersecurity`, `copier-lease`
- the client or industry tag, for example `goodsuite`, `office-technology`

Summary: `Email N of M in "<series>" for <who gets it>. Subject: "<subject>". <preview text>`

Audience: `office-technology` (or `universal`, `quantum-internal`).

## Kit SQL (pattern)

```sql
with defs(slug,name,summary,tags) as (values
  ('<series-slug>','<Kit name>','<one sentence>',array['nurture','<topic>','<industry>'])
), k as (
  insert into qbs_content_kits(name,summary,tags,status)
  select name,summary,tags,'draft' from defs
  on conflict (name) do nothing returning id,name
), kk as (select k.id kid, d.slug from k join defs d on d.name=k.name)
insert into qbs_content_kit_items(kit_id,item_id,position,role)
select kk.kid, i.id,
  (regexp_match(i.title,'\| Email (\d+) \|'))[1]::int,
  'email '||(regexp_match(i.title,'\| Email (\d+) \|'))[1]
from kk join qbs_content_items i on ('series:'||kk.slug)=any(i.tags) and '<client-tag>'=any(i.tags);
```

## Reusing for another client

Expect these "Change:" flags when deploying a GoodSuite item to a different portal:

- it uses the custom template `templates/GoodSuite_DnD_Email_v1.html`, which must exist in the target portal.
  Create it there first from `template/` after rebranding.
- GoodSuite names, the phone number and the four booking-page links in the CTAs
- source-portal links and images

Booking links used by the series, by lane (replace per client):

- Lease lanes (L1, L2): `/book-a-meeting-for-printers-and-copiers/`
- Managed IT lanes (L3, L6): `/...-managed-it/`
- Cybersecurity lanes (L4, net new cyber): `/...-cybersecurity/`
- Managed print lane (L5): `/...-managed-print/`

## Known residuals from the GoodSuite build

- The real HubSpot render was never seen after the template change (previews need a login). The local model reproduces what Nasim's Zoom recording showed.
- Some emails still have short last lines on phones, three paragraphs end in the recipient company token, and a few long hero headlines wrap to three lines on phones.
