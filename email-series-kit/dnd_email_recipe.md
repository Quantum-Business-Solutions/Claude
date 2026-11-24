# Recipe: create a drag-and-drop GoodSuite email in one API call

Portal 20921734 (Client Command portal UUID f24e4ed1-6f85-4814-ba60-76de583a6a76).
Tool: `mcp__Client_Command_-_NEW__call_hubspot_as_client` (never the plain HubSpot MCP).

## 1. What exists

- Template (created 2026-11-18, do not edit the original v2): `templates/GoodSuite_DnD_Email_v1.html`
  - Source of truth on disk: `/tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/GoodSuite_DnD_Email_v1.html`
  - Fixed (locked) parts: logo header, micro nav, tri-colour brand bar, solutions chips, blue band, About, social icons, address, unsubscribe links, hidden preview text field.
  - Editable parts: ONE drag-and-drop area named `main` with six default sections: hero, intro, three-points card, closing text, CTA button, P.S. Staff can edit text inline, move/reorder/duplicate/delete sections, and add Rich text, Image, Button, Divider, Spacer modules from the editor.
- The old `templates/GoodSuite_Branded_Email_v2.html` is module/field based (not drag-and-drop). Do not use it for new work.
- Facebook footer icon fixed: `https://20921734.fs1.hubspotusercontent-na2.net/hubfs/20921734/gs-social-facebook-f.png` (the original `gs-social-facebook.png` shows a plus sign, not an "f", so it is not used in the DnD template).
- Generator script (builds the exact JSON body, 6 widgets + preview text): `/tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/build_dnd_email.py`
  - Edit the `E` dict (one entry per email) then run `python3 build_dnd_email.py`; it writes `emails/e<N>.json`. Paste the JSON as the `body` of the create call.

## 2. Create the email (AUTOMATED_EMAIL draft, one call)

`POST /marketing/v3/emails`

```json
{
  "name": "{{NAME}}",
  "subject": "{{SUBJECT 30-50 chars}}",
  "type": "AUTOMATED_EMAIL",
  "state": "AUTOMATED_DRAFT",
  "subcategory": "automated",
  "language": "en",
  "from": {"fromName": "GoodSuite", "replyTo": "marketing@goodsuite.com"},
  "subscriptionDetails": {"subscriptionId": "{{SUBSCRIPTION_ID e.g. 29902898}}"},
  "to": {"suppressGraymail": false},
  "content": {
    "templatePath": "templates/GoodSuite_DnD_Email_v1.html",
    "widgets": {
      "module-0-0-0": HERO,
      "module-1-0-0": INTRO,
      "module-2-0-0": POINTS,
      "module-3-0-0": CLOSING,
      "module-4-0-0": BUTTON,
      "module-5-0-0": PS,
      "preview_text": {"body": {"value": "{{PREVIEW_TEXT}}"}, "name": "preview_text", "type": "text"}
    }
  }
}
```

Rich text widget shape (HERO, INTRO, POINTS, CLOSING, PS):

```json
{"body": {"html": "{{HTML}}", "hs_enable_module_padding": true,
          "hs_wrapper_css": {"padding-top": "40px", "padding-right": "40px", "padding-bottom": "6px", "padding-left": "40px"},
          "path": "@hubspot/rich_text", "schema_version": 2},
 "id": "module-1-0-0", "module_id": 1155639, "name": "module-1-0-0", "order": 2, "type": "module"}
```

Button widget (BUTTON, module-4-0-0):

```json
{"body": {"destination": "{{CTA_URL}}", "hs_enable_module_padding": true,
          "hs_wrapper_css": {"padding-top": "10px", "padding-right": "40px", "padding-bottom": "34px", "padding-left": "40px"},
          "link_to": "url", "path": "@hubspot/button_email", "schema_version": 2,
          "style": {"alignment": "center", "background_color": {"color": "#94C83D"}, "border_enabled": false, "corner_radius": 100,
                    "font_style": {"color": "#003A69", "font": "Helvetica,Arial,sans-serif", "size": {"units": "px", "value": 16},
                                   "styles": {"bold": true, "font-weight": "bold", "italic": false, "underline": false}},
                    "inner_horizontal_padding": 40, "inner_vertical_padding": 16},
          "text": "{{CTA_TEXT}}"},
 "id": "module-4-0-0", "module_id": 1976948, "name": "module-4-0-0", "order": 5, "type": "module"}
```

Section to widget map (the template's default modules are named `module-<section>-<column>-<row>`, and an email widget with the same name overrides that module's content):

| name | section | background | content |
|---|---|---|---|
| module-0-0-0 | hero | #004B87 | pill tag, big word, one sub line (white text) |
| module-1-0-0 | intro | #ffffff | greeting, headline (the hook), italic accent, 1 to 2 short paragraphs |
| module-2-0-0 | points card | #F2F7FB | small caps label + 3 numbered points (title + one line) |
| module-3-0-0 | closing | #ffffff | one short paragraph before the button |
| module-4-0-0 | button | #ffffff | single CTA |
| module-5-0-0 | P.S. | #F2F7FB | one short aside, starts with bold "P.S." |

HTML snippets used by the generator (inline styles, Poppins fallback stack, brand colours: blue #004B87, green #94C83D, sky #4BB7E4, mid blue #1E73BE, body text #44576B, muted #566B80, ink #0E2439, tint #F2F7FB):

- Hero pill: `<span style='display:inline-block; background-color:#94C83D; color:#003A69; font-size:11px; font-weight:600; letter-spacing:1.5px; text-transform:uppercase; padding:6px 16px; border-radius:100px;'>TAG</span>`; big word `font-size:56px; font-weight:700; color:#ffffff; letter-spacing:-2px`; sub line `font-size:18px; color:#D8ECF9`.
- Intro: `Hi {{ personalization_token('contact.firstname', 'there') }},` then `<h1>` 28px bold #004B87 (the hook), italic 20px accent #566B80, paragraphs 16px / 1.7 / #44576B. Company token: `{{ personalization_token('contact.company', 'your business') }}` (always give a fallback).
- Points: number pill is an inline-block span 26x26 radius 100px (colours #94C83D/#003A69, #4BB7E4/#00365F, #1E73BE/#ffffff); detail line has `margin-left:36px`.

## 3. Read it back (QA call)

`GET /marketing/v3/emails/{id}` and check:
- `type` = AUTOMATED_EMAIL, `state` = AUTOMATED_DRAFT, `subcategory` = automated (NOT BATCH_EMAIL / DRAFT).
- `content.templatePath` = `templates/GoodSuite_DnD_Email_v1.html`.
- `content.widgets` has module-0-0-0 ... module-5-0-0 and `preview_text`; none has `deleted_at`.
- `subscriptionDetails.subscriptionId` correct, `from.fromName` GoodSuite, no em dashes, tokens intact.
- Archive/delete a mistaken draft with `DELETE /marketing/v3/emails/{id}` (only drafts you created).

## 4. Gotchas hit (read these)

1. `type: AUTOMATED_EMAIL` alone is not enough. Without `"state": "AUTOMATED_DRAFT"` the API created a `BATCH_EMAIL` draft with `sendOnPublish: true` and an empty recipient block. It sent nothing, but delete it immediately. Always send `type`, `state` and `subcategory: automated` together.
2. `content.flexAreas` sections are silently dropped by the API (response shows `"main": {}`), for custom and stock templates, on POST and PATCH. Do not send flexAreas. The layout comes from the template's default dnd_area; widgets override module content by name.
3. `emailTemplateMode` is derived from the template, not the body. Coded DnD templates report `DESIGN_MANAGER` (the dnd_area inside is still drag-and-drop in the editor). Stock `@hubspot/email/dnd/*` templates report `DRAG_AND_DROP` but their layout cannot be set via API, so use our template.
4. A PATCH with a partial `content.widgets` map soft-deletes every widget you omit (`deleted_at` appears). Always PATCH the full widget set.
5. `PATCH /automation/v4/flows/{id}` returns 405. Use `PUT` with the full flow body and the current `revisionId`; keep `isEnabled: false`.
6. Legacy template create works with JSON: `POST /content/api/v2/templates` with `category_id: 2`, `template_type: 2`, `folder`, `path`, `source`, `is_available_for_new_content: true` (source-code API needs multipart, which the tool cannot send). `has_dnd_area: true` in the response confirms a DnD template.
7. The `{% text 'preview_text' %}` field in the template is what the editor's preview text maps to; set it through `widgets.preview_text`.
8. The marketing email `previewKey` URL needs a HubSpot login, so rendered output cannot be fetched with the PAT. Render locally instead (`render.py` + `shot.js` in the same folder, Playwright) and verify in the editor by eye.
9. Python PIL is broken in this sandbox; use ImageMagick `convert` or Playwright for images. Upload new images with `mcp__Client_Command_-_NEW__hubspot_upload_file` (base64) rather than editing existing files.
10. `/marketing/v3/emails?limit=30` output is huge; read the saved tool-result file with `python3 -I` and print only id/type/state/templatePath/name.

## 5. Copy rules (every email)

- First line after the greeting is a hook: specific, concrete, a question or a relevant observation. Never "I hope you are well", never "GoodSuite helps...".
- Subject 30 to 50 characters where possible, specific, no spam words (free, guarantee, act now, urgent), no ALL CAPS, no emoji.
- Preview text adds to the subject, does not repeat it; sentence case, not all caps, about 40 to 90 characters.
- One idea per email. Short paragraphs of 1 to 3 sentences. Under about 150 words of body.
- One primary call to action (single button to https://goodsuite.com/contact/ unless told otherwise).
- Plain, warm tone. No hype, no fear tactics, no invented statistics or claims.
- Personalise only with safe fallbacks (`contact.firstname` -> "there", `contact.company` -> "your business").
- No em dashes anywhere. US spelling.
- Offers stay "pending client confirmation" until the client confirms the exact services; keep workflows OFF and emails unpublished until approved.

## 6. Design QA checklist

Mobile (375px): single column, 16px body, tap targets 44px or more (footer links and icons are padded to this), no horizontal scroll. Dark mode: header logo switches to white, footer text brightens, body sections stay light with dark text. Every image has alt text. Preview text present. Address and both unsubscribe links come from the fixed footer. Button contrast: #003A69 on #94C83D (about 6:1).

## 7. Proof this recipe works

Eight emails (E1 to E8 of "Net New Cyber") were created from this exact body shape on 2026-11-18; each read back with templatePath, six widgets and preview text. A rendered copy was only checked locally, not in HubSpot.
