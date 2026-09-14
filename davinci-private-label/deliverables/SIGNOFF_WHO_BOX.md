# Sign-off sheets — the "who is reviewing?" box

**14 Sep 2026.** Built once, deployed per client, from `tools/build_clientlink_box.py`.

## Why

Client sheets are opened on the no-login share link, so the portal sends the page no user. With
no name and no side the app refuses a mark and only scrolls the identity bar when you press one
— which reads as a dead button. That is what Melinda hit on Praxera.

So the sheet now asks, once, on arrival: **"Who is reviewing today?"** One click sets the name
and the client side, and every button works from then on. A free-text field covers anyone not
listed; Skip falls back to a neutral client label rather than a dead end.

It is a no-op for QBS — a signed-in team member gets "Signed in as …" and no `#who` box, so it
never builds.

## Live

| Client | Portal | Sheet | Names offered | Section |
|---|---|---|---|---|
| Praxera | `6d797a44…` | `praxera-asset-signoff` | Tammy Johnson, Melinda Elmadjian, Sarah Miller | `clientlink`, 4,067 bytes |
| Revolution Office | `b483aef1…` | `revolution-website-signoff` | Tom Menton | `clientlink`, 4,178 bytes |

Each client's box carries only that client's people. Revolution's contains no Praxera, DaVinci
or FoodScience name — checked, not assumed. Its copy also stays neutral about what the marks are
called, because Revolution's sheet says "Verified ✓" where Praxera's says "Client ✓".

Revolution has one real client account on the portal (Tom Menton, `tmenton@revolutionoffice.com`).
Praxera has **none** — all three of its reviewers share the anonymous link, which is why its box
lists three names.

## How it is kept apart

The box is a **separate document section on one page**. Section writes hit one document; there is
no shared include and nothing propagates. The one thing that *would* spread is ClientCommand's
`asset-signoff` template, and it is untouched — on both sheets `app` and `boot` are byte-identical
to what they were before.

| | Praxera | Revolution | Template |
|---|---|---|---|
| `app` | 29,875 | 29,818 | 29,818 |
| `boot` | 43,532 | 43,401 | 43,573 |

Both sheets' `boot` differed from the template before any of this; that drift is pre-existing.

## Verified

`tools/test_clientlink_bridge.js` drives the **deployed** box against the **deployed** app for
each client in Chromium — 20 checks each, all passing:

- the box appears on the share link and offers that client's reviewer
- one click fills their name, selects the client side and closes the box
- the next click marks the row, credited to them, saved to the portal
- the activity log records it on the client side under their name
- a signed-in QBS user is untouched — no box, no side change

Both `check_signoff_sheet` runs return `ok: true` with no new problems.

## To add another client

Add an entry to `CLIENTS` in `tools/build_clientlink_box.py`, run it, and upsert the generated
file as a `clientlink` section at `display_order` 10. First confirm the client's app has the
hooks: `grep -c 'data-s="client"'` and `grep -c 'id="who"'` against their `boot`.

## Still the better fix

This is a stopgap. The durable version is in `src/signoff.js` — no name needed at all, nothing
rendered disabled, marks recording which side gave them, QBS able to tick on the client's behalf
with it labelled as such. It belongs in the `asset-signoff` template so every sheet gets it,
which is a decision for whoever owns that template: it changes behaviour on every client's sheet.
Once it ships, these `clientlink` sections come out.
