# Praxera — meeting links in the emails

**14 Sep 2026 · portal 4087538** · before-states in `backups/meeting-link-getstarted/`

## The dead one — fixed

`https://meetings.hubspot.com/samantha-fuller/private-label-round-robin` is **not in the
portal's scheduler**. Samantha Fuller has a personal link (`samantha-fuller`), but the
private-label round robin under her name does not exist among the portal's 35 meeting links.

A note on how this was confirmed: `meetings.hubspot.com` answers **HTTP 200 with an 82KB
JavaScript shell for every slug, real or invented** — I checked with a deliberately fake slug.
A 200 proves nothing here. Only the scheduler API settles it.

Per Shawn, all **8 links across 6 emails** now point at
`https://www.praxerasupplements.com/get-started`.

| Email | Links |
|---|---|
| 220685976456 · Private_Label_Guide_ToF_Paul_Get Started_Private_Label_With_Praxera | 2 |
| 220685976586 · 1: Private Label Guide: High-Priority | 2 |
| 220688283275 · Private Label: High Priority - 6 Benefits | 1 |
| 220692678021 · Private Label: High Priority - how to make money | 1 |
| 220692678023 · 3: Private_Label_Guide_ToF_Paul_ Step-by-step Guide to managing shipping and Inventory | 1 |
| 220692678044 · Private_Label_Guide_ToF_Paul_6_Benefits of Selling PL | 1 |

The copy around every one reads "book a call", "schedule a quick call" or "grab a few minutes
from our calendar", so `/get-started` — Schedule a Consultation — lands correctly. One of the
two on 220685976586 is the click-through on an image module, not body text.

All six remain **DRAFT**. Nothing sent, nothing published.

## Two more meeting links — real, but they book DaVinci people

The sweep for the dead link turned up two others on Praxera emails. Both **do** exist in the
portal, so neither is broken — but both route a Praxera prospect to a DaVinci calendar, which
is a different question and not one I acted on.

| Link | Whose | On |
|---|---|---|
| `lschencker-carroll/round-robbin-` — "Sales Round Robbin" | Lindsey Schencker-Carroll | 220685976492 *5Rs*, 220685976494 *Top-Sellers*, 220685976583 *PL 5rs #5*, 220688836213 *PL 5rs #6* |
| `art-monaghan/private-label-chatbot-round-robin` — "Private Label Chatbot Round Robin" | Art Monaghan | 220685976583 *PL 5rs #5*, 220688836213 *PL 5rs #6* |

Worth knowing: the portal also has **`lschencker-carroll/private-label-form-round-robin`**
("Private Label Form - Round Robin"), which looks like the round robin the dead Samantha Fuller
link was reaching for. If Praxera bookings should land on a real round robin rather than
`/get-started`, that is the candidate — say the word and I will switch the six.
