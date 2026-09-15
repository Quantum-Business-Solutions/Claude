# Praxera footer — phone and email under the address

**15 Sep 2026 · portal 4087538**

## What Shawn asked for

Under the physical address in the site footer:

- **1-800-325-1776** — the number already published on `/contact`
- **info@praxerasupplements.com**

## The exact change

The footer's `Address` field (the `footer_phone_area` block) currently reads:

```html
<h3>Address</h3>
<p>929 Harvest Lane Williston, VT 05495</p>
<p>Praxera is part of the FoodScience LLC® family of brands. …</p>
```

It should read:

```html
<h3>Address</h3>
<p>929 Harvest Lane Williston, VT 05495</p>
<p><a href="tel:+18003251776">1-800-325-1776</a><br><a href="mailto:info@praxerasupplements.com">info@praxerasupplements.com</a></p>
<p>Praxera is part of the FoodScience LLC® family of brands. …</p>
```

Ready to paste: `deliverables/footer-address-field.after.html`.
Before-state: `backups/footer-contact/address-field.before.2026-09-15.html`.

Both are real links, so the number dials on a phone and the address opens a mail client. The
FoodScience sentence stays exactly as it is — the ® question is still open and this change does
not touch it.

## Why it is not applied from here

The footer is a **global module** — `Private Label/Modules/Global Footer`, `module_id`
**215777821974**, `"global": true` in its `meta.json`. The page template calls it with no
parameters:

```
{% module "global_footer" path='/Private Label/Modules/Global Footer', label="Global Footer" %}
```

so the content is not on any page. Confirmed: the home page's JSON has no `global_footer`, its
`widgets` object is empty, and the only "Harvest Lane" in it is inside the schema block, not the
footer.

Nor is it in the module's files. The published `fields.json` default still reads *"Operational
address TBD. Awaiting brand lock."* and *"Private Label is part of the FoodScience® family of
brands"* — the DaVinci-era text. What renders is a **global content record** that overrides it,
and HubSpot does not expose that record on any API path I could reach. Seventeen endpoints
tried across `/content/api/v2`, `/cms/v3`, and `/designmanager/v1`; the only one that answers
for this module returns the module definition and its field defaults, not the live content.

**So it is a HubSpot UI edit**: Design Manager → `Private Label/Modules/Global Footer` → the
global content for the Address field. One paste, and it lands on all 68 pages at once.

## Also worth doing while in there

**Every one of the 11 footer links is dead.** Private Label Supplements, Our Process, Design
Services, Resource Center, Guides, FAQ, Blog, Quality & Trust, Health Categories, Supplement
Forms, Contact — all render `href="#"`. The module builds them from HubSpot **simple menus**
(`{% simple_menu menu_tree=… %}`), so the menu items themselves have no URLs. The fix is in
Marketing → Navigation, not in the module. Nobody reported this because it is a build defect
rather than a content request, but a footer where nothing is clickable is the more visible
problem of the two.

## What the client actually asked for on the footer

One set of instructions, from Sarah Miller on 24 August, and all of it is already done:

| Request | State |
|---|---|
| Update "Praxera is part of the FoodScience LLC family of brands…" | done |
| Remove the "sibling brand" sentence | gone |
| No DaVinci anywhere | absent |
| Remove "custom formulation" (site-wide) | absent |

Nothing else about the footer appears anywhere in the record — not in the page-comment
transcripts, Mindy's review instances, the call actions, or the live comment threads and global
notes on the sign-off sheet. The phone and email are a new request, not an outstanding one.

Still open, unrelated to this change: **"FoodScience LLC®"** puts the ® on "LLC". The DaVinci-era
original marked it "FoodScience®" and Sarah's written rule carries no ® at all. Her call.

---

## Update, 15 Sep — duplicates removed, highlight gone

Two follow-ups from Shawn, both now live on all 68 pages.

**The phone and email showed twice.** The tappable pair was added below the address block;
separately, the same two lines were typed into the footer's global content as plain text
(`Phone: 800-325-1776`, `E-Mail: Info@praxerasupplements.com`). Both rendered.

The global-content record is on no reachable API path, so the plain lines could not be deleted
there. Instead the module template now swaps them for the linked pair **in the position they
already occupy** — directly under the street address. One copy each, and they are real `tel:`
and `mailto:` links rather than text you have to retype into your phone. If those lines are
ever cleared from the global content, the swap matches nothing and the links are appended
instead, so they cannot go missing.

**The pale-green highlight on the About Praxera caption is gone.** A paste on 15 Sep arrived
carrying its source colours inline — `color:#3a3f36` on `background-color:#ecefe7` — which beat
the stylesheet and rendered grey text in a pale-green block against the dark footer. The module
now strips inline `style` attributes off the caption and the address on the way out. The footer
is white on the dark band, always. `#ecefe7` and `#3a3f36` now appear **zero** times on the page.

### Verified

| Check | Result |
|---|---|
| HubL validated before upload (`/cms/v3/source-code/published/validate/`) | clean; the same call correctly rejects a deliberately broken copy |
| `tel:` / `mailto:` count, 11 live pages | exactly 1 each (`/contact` has 2 mailto — the second is its own body link) |
| Plain `Phone:` / `E-Mail:` lines remaining | 0 on all 11 |
| Highlight colours on the page | 0 |
| Caption rendered colour (Chromium, 1440 and 390) | `rgb(255,255,255)` on `rgb(50,50,50)` |
| Position | phone and email sit under the street address, above the FoodScience sentence |

Screenshots: `/tmp/shots/footer-desktop.png`, `/tmp/shots/footer-phone.png`.

### Two findings — not acted on

1. **Every `mailto:` on the site is rewritten to `href="javascript:void(0);"`** a few seconds
   after load. Isolated to `cdn.rlets.com` (the NextRoll/RollWorks capture pixel): block that one
   script and the `mailto:` survives; block Hotjar, the HubSpot loader or the cookie banner and it
   still breaks. This is **pre-existing and site-wide** — `/contact`'s own email links, which
   long predate this change, behave identically. The script does attach its own click handler, so
   it may still hand off to the mail client after firing its tracking; that cannot be proven from
   a headless browser, which blocks external protocol handlers either way. **Someone should click
   the footer email on a real machine and confirm Outlook opens.** The `tel:` link is untouched.
2. **The ZIP in the address looks short**: `Williston, VT 0549` — Vermont ZIPs are five digits and
   Williston is 05495. It lives in the global content, so it is a one-field edit in the footer
   editor. Not changed here — flagging only.
