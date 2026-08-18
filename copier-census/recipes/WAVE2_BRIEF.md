# Wave 2 briefing — copier dealer census validation

Read `../gapwork/RECIPE.md` first (the dealer-people recipe) and `../gapwork/HARD_RECIPE.md`
(the 9-source order for dealers that defeat LinkedIn). Everything below is in force on top of them.

## Hard constraints — do not violate

1. **Never write to HubSpot.** Produce a JSON result file only. All portal writes are done
   centrally after dedup against both unique properties. A direct write from an agent has
   already caused duplicate humans in this portal.
2. **Client accounts are excluded by design.** They are already filtered out of your shard.
   If you discover that one of your targets is a QBS customer, stop on that record and
   report it as `client_hold` — do not research it further.
3. **Never match a person on surname alone.** A previous wave matched "Annabelle Young"
   to the dealer "RJ Young" on surname and surfaced what appears to be a minor. A match
   needs the person's *current employer* to be the dealer, evidenced.
4. **Only Shawn's LinkedIn account** — `account_id=S6ua4SfUT4SMRFZFOmyUzQ`. Never any other.
5. **No residential people-search sites** (TruePeopleSearch and similar). Declined by the user.

## Unipile — the working recipe

Must go through the MCP tool `mcp__Unipile__execute-request`. Direct HTTP to the port is
unreachable from this container. `api:"sales_navigator"` returns 401 on this key; use `classic`.

Company search:
`POST /api/v1/linkedin/search?account_id=S6ua4SfUT4SMRFZFOmyUzQ`
body `{"api":"classic","category":"companies","keywords":"<DEALER NAME>"}`

People at that company (**no keyword filter — a keyword filter cost a previous wave at least
15 decision-makers, including a President whose headline contained the word "President"**):
`POST /api/v1/linkedin/search?account_id=...&limit=25`
body `{"api":"classic","category":"people","company":["<COMPANY_ID>"]}`

Profile with roles:
`GET /api/v1/users/<slug>?account_id=...&linkedin_sections=experience`
A role with `end: null` in `work_experience[]` is the current one.

**The company filter leaks.** Over 1,000 leaked results were rejected in wave 1 — leaks
consistently outnumber real finds. Confirm every hit against the profile's current employer
before keeping it.

**Throttling returns an empty item list with no error** — indistinguishable from "this company
has no employees on LinkedIn." Before recording a zero, re-run a canary query you know
returns people; if the canary is also empty, sleep 75s and retry. A false zero is worse than
a slow run.

**Emails are exposed only for DISTANCE_1 connections** (`contact_info.emails`). Confirmed
across ~330 profiles. Do not expect an email from a 2nd/3rd-degree profile.

## Email classification — the user's rule, enforced exactly

Free-mail domains (personal): gmail, googlemail, yahoo, ymail, rocketmail, hotmail, outlook,
live, msn, aol, icloud, me, mac, protonmail, proton, gmx, mail, zoho, yandex, comcast,
verizon, att, sbcglobal, bellsouth, cox, charter, spectrum, earthlink, juno, netzero,
roadrunner, rr, optonline, frontier, windstream, embarqmail, q, shaw, rogers, sympatico,
telus, bell, midco.

Report each email with `email_class` of exactly one of:
- `business` — domain matches the dealer (or the acquirer, for an acquired dealer), or the
  domain is a corporate domain that reveals the dealer's real website
- `personal` — a free-mail domain above. **These may never land in the business email field.**
- `unknown` — a corporate domain that is not obviously this dealer's; held for human review

## What counts as verified

Only these carry `validated: "Yes"`:
- LinkedIn profile showing the person currently at this dealer (company-to-people sweep)
- the dealer's own website naming them
- a state Secretary of State officer filing
- a state contract / cooperative vendor list naming them with title and email
- a press release or trade article (including Industry Analysts) naming them in role

These do **not**: a pattern-guessed email, a BBB listing, a ZoomInfo record with
`contactAccuracyScore` at or near 0, a chamber directory, a dealer-locator page.
Report those with `validated: "Needs Updated"` and say which source it came from.

An email you constructed from a naming pattern is `email_confidence: "inferred"` and never
`validated: Yes`, no matter how confident the pattern.

## Output

Write `wave2/<YOUR_SHARD>_result.json` — a JSON list, one object per target company:

```json
{
  "cid": "<company id from the shard, unchanged>",
  "company": "<name>",
  "outcome": "found | already_complete | no_people_online | not_a_dealer | acquired | defunct | non_us | client_hold | blocked",
  "company_verdict": "dealer|dealer_bad_domain|not_dealer|acquired|defunct|non_us|unresolved",
  "company_notes": "what you established about the company, with sources",
  "domain_correction": "<real domain, or null>",
  "acquired_by": "<acquirer name, or null>",
  "sources_tried": ["linkedin","company_site","sos_filing"],
  "people": [
    {
      "firstname": "", "lastname": "", "title": "",
      "linkedin_url": "https://linkedin.com/in/<slug> or null",
      "email": "or null", "email_class": "business|personal|unknown",
      "email_confidence": "verified|inferred",
      "phone": "or null",
      "is_decision_maker": true,
      "validated": "Yes|Needs Updated",
      "evidence": "one or two sentences naming the source and what it showed",
      "existing_contact_id": "<if this person is already a HubSpot contact in the shard data, else null>"
    }
  ]
}
```

`sources_tried` must be a **JSON list**, not a comma string — a string silently iterated into
single characters in a previous deliverable.

Write the file incrementally (rewrite it after every few companies) so partial progress
survives a timeout. Report counts honestly at the end: companies where you found nothing
are a real and useful result, and a fabricated find is far more expensive than a zero.
