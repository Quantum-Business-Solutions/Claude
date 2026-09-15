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
