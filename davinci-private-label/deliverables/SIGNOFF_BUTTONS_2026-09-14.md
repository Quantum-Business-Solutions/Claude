# Sign-off sheet — why the approval buttons did not work

**14 Sep 2026 · portal `6d797a44…` · sheet `praxera-asset-signoff`**

## What Melinda hit

`audit_portal_access` on this portal returns **`client_users: []`** — there are no client
accounts on it at all. Everyone listed is QBS: Shawn, Marko, Justin, Barb, Patrick, Jandric,
Kenzie. So Melinda is opening the sheet on the **no-login client share link**, and on that route
the host sends the page no user at all.

With no user the sheet has no name and no side, and pressing an approval button ran `askSide()`,
which did one thing: scrolled the identity bar into view. If you are already near the top of the
page, nothing visibly happens. The button looks dead. That is the whole bug.

There is a second, separate way to hit it: if the host *does* sign someone in and reports their
`kind` as `team`, the sheet forced their side to QBS and rendered **Client ✓ as `disabled`** with
the tooltip "Client side only". And because the host supplied a name, the sheet also hid the
"I am QBS / I am the client / I am Regulatory" picker — so that person had no way to switch.
Hard blocked.

## Shipped — the sheet now asks who is reviewing

Shawn's call: no workaround for Melinda. Instead, when she first hits the page, a box asking who
is looking at it.

Live on the sheet since 14 Sep 19:37 UTC as the `clientlink` section (4,054 bytes). On the
no-login share link the sheet opens with a short box naming **Tammy Johnson, Melinda Elmadjian
and Sarah Miller**, a free-text field for anyone else, and a Skip. One click fills the name and
selects the client side; every approval button works from then on. Skip still leaves the sheet
usable under a neutral client label rather than a dead end.

This is better than silently preselecting the client side, which is where this started: an
approval now carries the reviewer's actual name rather than just "not QBS".

It cannot fire for QBS — a signed-in team member has no name box for it to find.

**Verified against what is actually on the sheet**, not a local build: the deployed bridge, run
against the deployed app, 20 checks passing — the box appears and names the three, one click
credits both the row and the activity log to Melinda on the client side, and a signed-in QBS
user is untouched. `boot` is byte-identical to before the change, and `check_signoff_sheet`
returns `ok: true` with no new problems.

## What changed in the code

Per Shawn: anyone may press any button, with nothing typed first. QBS may tick on the client's
behalf, and the sheet records who did it so a QBS tick is never mistaken for the client's.

| Before | After |
|---|---|
| `can()` gated each button on your side | `can()` is unconditional; `askSide()` and `needSide` are gone |
| `locked()` disabled the other side's button | always false — nothing renders disabled, and the bulk bar works for everyone |
| a mark stored `by` + `at` | a mark also stores `sd`, the side that gave it |
| a QBS-given client approval was indistinguishable from the client's | the row reads "Client · date · Name — **QBS, on their behalf**", and the activity log says so too |
| an unidentified click was refused and silently scrolled the identity bar | there is no prerequisite at all — the click lands, the mark saves |
| an unnamed person showed as "unnamed" | shows as *via the client link*, on the row and in the activity log |

`tools/test_signoff_buttons.js` drives the real minified build in Chromium against a stub host
that reproduces both routes — signed in with a `team` kind, and anonymous on the share link.
**21 checks, all passing**, including that a QBS-given client approval saves as
`by: "Melinda Elmadjian", sd: "qbs"` and that an anonymous one saves with no side at all.

### Attribution survives dropping the name requirement

Shawn's condition was that we can always tell it was not our team. That still holds, and it no
longer depends on anyone typing anything: every QBS person is signed in through the portal, so
the host hands the sheet their name and side automatically. A mark with **no name and no side
can only have come from the client share link**. The sheet says exactly that rather than
"unnamed".

## Reconciled drift, which would otherwise have been reverted

The live `boot` was ~700 chars **ahead** of `src/signoff.js`: someone had patched the live app
without committing it. Rebuilding from the repo would have silently thrown that away. Ported
back into source first:

- render keeps every table's horizontal scroll position, keyed by section rather than index, so
  folding a group does not shuffle them
- the root's height is pinned during the `innerHTML` swap, so the page does not jump
- focus is restored with `preventScroll`
- the 25-second poll skips its refresh while someone is typing in a textarea or input

## Not deployed — and why

Shipping this means replacing the sheet's `boot` section, which is **43,153 characters of
minified JavaScript on one line**. The only write path available here takes that body inline,
and the only verification available afterwards is a character count. One wrong character is a
`SyntaxError`, and a `SyntaxError` in `boot` renders the entire sign-off sheet blank — for the
client, in the week they are reviewing it. I am not doing that by hand on a live client
deliverable.

There is a better home for it anyway. `check_signoff_sheet` reports this sheet has **drifted
from ClientCommand's own `asset-signoff` template**:

| Section | This sheet | Template |
|---|---|---|
| `app` | 29,875 | 29,818 |
| `boot` | 43,532 | **43,573** |

A one-off paste into this page drifts it further and keeps the fix only until someone
re-templates the sheet. The change belongs in the `asset-signoff` template, where every client's
sheet picks it up.

**Ready to go:** `deliverables/signoff.min.js` (syntax-checked, 21/21 tests) and the source at
`src/signoff.js`, both committed.

Driving the live sheet end to end was not possible from here: Chromium rejects the agent
proxy's certificate (`ERR_CERT_AUTHORITY_INVALID`) and disabling TLS verification is not an
option. The tests instead run the real minified build in real Chromium against a host stub that
reproduces both routes exactly.

## Worth deciding separately

The portal has **no client users**. Tammy, Mindy and Sarah are all working through a shared
no-login link, which is why the sheet cannot tell them apart and why every approval depends on
someone remembering to type their own name. Giving the three of them real portal accounts would
fix the attribution problem at the root — and is the only way to be certain a "Client ✓" came
from the client.
