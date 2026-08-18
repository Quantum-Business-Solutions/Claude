# dealer-people : the two-call method

Use the Unipile MCP tool `mcp__Unipile__execute-request`. Direct HTTP does NOT work from this
container (port 16072 unreachable). Only the MCP route works.

KEY: ${UNIPILE_API_KEY}   <-- REDACTED. Supply via environment; never commit the key.
ACCOUNT: S6ua4SfUT4SMRFZFOmyUzQ   <-- the ONLY account you may use, ever.

## CALL 1 — find the dealer's LinkedIn company id

harRequest:
{"method":"POST",
 "url":"https://api30.unipile.com:16072/api/v1/linkedin/search?account_id=S6ua4SfUT4SMRFZFOmyUzQ&limit=5",
 "headers":[{"name":"X-API-KEY","value":"<KEY>"},
            {"name":"accept","value":"application/json"},
            {"name":"content-type","value":"application/json"}],
 "queryString":[],"httpVersion":"HTTP/1.1","cookies":[],"headersSize":-1,"bodySize":-1,
 "postData":{"mimeType":"application/json",
   "text":"{\"api\":\"classic\",\"category\":\"companies\",\"keywords\":\"<DEALER NAME>\"}"}}

VERIFY THE MATCH before using the id. Check `location` against the dealer's city/state and the
`summary` against office imaging. A name search returns near-misses — searching "RJ Young"
also returned "RJ YOUNG FARMS, INC." in Iowa. If nothing matches the city/state, record
`company_match:"not_found"` and move on. Do NOT force a match.

## CALL 2 — list the senior people at that company

Same shape, but:
 "text":"{\"api\":\"classic\",\"category\":\"people\",\"company\":[\"<COMPANY_ID>\"]}"

Use limit=25 in the URL.

DO NOT ADD A `keywords` FILTER. Measured across two shards: the keyword form
("president owner vice president...") returned ZERO people for several demonstrably live
dealers and hid a CFO, a President, a COO, a VP Sales & Service and a Director of Sales that
the unfiltered form found. Pull the company's people unfiltered and judge seniority yourself
from the headlines. The filter looks like an optimisation and is a net loss.

You may pass SEVERAL company ids in one array — {"company":["123","456"]} — which is efficient
for a dealer with duplicate or sibling LinkedIn pages.

THROTTLING IS SILENT. When rate-limited the API returns an EMPTY item list with no error, which
is indistinguishable from "this company has no people". Keep one known-good query as a canary.
If a confidently-matched company returns zero people, wait 75 seconds and re-run once before
recording it as empty. Several dealers were nearly written off this way.

COMPANY SEARCH IS SEMANTIC, NOT LITERAL. Adding a city to the query often returns ZERO even
when the plain name works. But a plain generic name returns a page of OTHER REAL COPIER DEALERS
— the highest-risk false-match pattern in this dataset. Search the plain name, then verify the
result by city/state or by an exact vanity-URL/domain tie (e.g. /company/fbsaz -> fbsaz.com).

The company filter LEAKS. Every returned person must have a headline that names the dealer or
an unmistakable role at it. Real leak examples: "Owner at Nashville Sweets" and
"Owner - Grasshopper Mowing" both came back on an RJ Young search. Reject them.

## CALL 3 — only for people whose `network_distance` is DISTANCE_1

harRequest GET:
 "url":"https://api30.unipile.com:16072/api/v1/users/<public_identifier>?account_id=S6ua4SfUT4SMRFZFOmyUzQ&linkedin_sections=experience"

First-degree profiles expose `contact_info.emails`. Second and third degree DO NOT — this is a
hard LinkedIn limit, not a bug, so do not waste calls on non-first-degree profiles hoping for
an address. Also read `work_experience`: `end: null` means the role is current.

## SALES NAVIGATOR IS UNAVAILABLE
`"api":"sales_navigator"` returns 401 expired_credentials. Do not retry it. Classic works and
is sufficient.

## DO NOT
- Do not write anything to HubSpot.
- Do not use any account_id other than S6ua4SfUT4SMRFZFOmyUzQ.
- Do not invent an email. If no address is exposed, that is the finding.
- Do not report someone whose headline shows they left, or a role with an end date, as current.
- Do not assert anyone has died. An obituary is a hold for a human.

## EMAIL CLASSIFICATION — MANDATORY (added 17 Aug 2026)

LinkedIn's `contact_info.emails` returns whatever address the person chose to publish. That is
OFTEN A PERSONAL ADDRESS — two already found this way were personal Gmail. A personal address
must NEVER be written to the primary `email` field, and a populated business `email` must NEVER
be overwritten by one.

Classify every address you return:

  business  — the domain is the dealer's own domain, a proven alias of it, or any other
              corporate domain that is not a free-mail provider
  personal  — the domain is a consumer mail provider. Treat these as personal:
              gmail, googlemail, yahoo, ymail, rocketmail, hotmail, outlook, live, msn, aol,
              icloud, me.com, mac.com, protonmail, proton.me, gmx, mail.com, zoho, yandex,
              comcast, verizon, att.net, sbcglobal, bellsouth, cox.net, charter, spectrum,
              earthlink, juno, netzero, roadrunner, rr.com, optonline, frontier, windstream,
              embarqmail, q.com, shaw.ca, rogers.com, sympatico, telus.net, bell.net
  unknown   — a corporate-looking domain you could not tie to this dealer or any other company

Report it in the person object as:
  "email":"", "email_class":"business|personal|unknown", "email_domain":"",
  "email_matches_dealer_domain":true|false

Where it will be written (for your awareness — you do not write anything):
  business + the CRM record has no email    -> primary `email` field
  business + the CRM already has an email   -> `email_other`, primary is left untouched
  personal, always                          -> `linkedin__email` only, never the primary field
  unknown                                   -> `linkedin__email` and flagged for review

Do not editorialise a personal address into a business one. If someone published a Gmail, say
Gmail. A correctly-labelled personal address is useful; a mislabelled one poisons a send list.
