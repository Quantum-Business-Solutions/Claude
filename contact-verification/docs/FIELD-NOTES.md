# RESUME — CAS list 5243 LinkedIn employment verification

## Goal
SDRs are dialing list 5243 RIGHT NOW. Verify every member still works where HubSpot says.
Verified-only callable list = HubSpot list **8260** (dynamic; grows as stamps land).

## Live state  (LAST UPDATED 2026-08-17, after 237 verdicts)
- **237 of 463 verified** — 110 no / 101 yes / 26 unreadable. **226 remaining** in queue_li.json.
- list 8260 (VERIFIED, callable) = **125 members**. Filter is now FOUR clauses:
  ai__li_still_at_company=yes AND hs_lead_status=ConnectandSell Prospect
  AND ai__contact_evidence DOES_NOT_CONTAIN "[NOT-MKT]" AND IN_LIST 5243
- reassoc_log.json: 31 movers fully re-associated (companies matched/created, both typeIds, flag reconciled).
- pending_movers.json: movers awaiting the pipeline. Drains to [] after each movepipe.py run.
- queue_noli.json — 29 unverified WITHOUT LinkedIn (needs ZoomInfo / name search). NOT STARTED.

## The loop to resume (this is the whole job)
1. `export TOKEN=<hubspot pat>` — the shell resets between calls, re-export every time.
2. `python3 nextbatch.py 6`  -> prints id | name | company | title | identifier
3. 6 parallel mcp__Unipile__execute-request calls (harRequest form, see below)
4. write verdicts to b.json, then `python3 wr.py b.json`
5. append any movers to pending_movers.json; run `python3 movepipe.py` every ~9-12 movers
6. repeat. Write after EVERY batch — SDRs are dialing live.

## The lookup (Unipile MCP only — direct curl to :16072 is blocked by the egress proxy)
Tool: mcp__Unipile__execute-request
```
GET https://api30.unipile.com:16072/api/v1/users/{identifier}?account_id=S6ua4SfUT4SMRFZFOmyUzQ&linkedin_sections=experience_preview
headers: X-API-KEY: <unipile key>, accept: application/json
```
- ONLY Shawn's accounts are authorized: S6ua4SfUT4SMRFZFOmyUzQ, 7lBoyXuETqKdiJYLj5HBGA.
  The other 5 Unipile accounts are CLIENT identities — never use them.
- Strip `?trk=...` tracking params off identifiers. URL-encode non-ASCII (ñ -> %C3%B1).
- `linkedin_sections` valid values include: experience, experience_preview, `*`, about, education...
  Do NOT send `*experience` — 400.
- 5–6 profiles per message in parallel. Write verdicts after EVERY batch (SDRs are live).

## Reading the profile — the rule that matters
**Dated `work_experience` is the truth. The headline is not.**
- Headline naming an employer ("CMO at Omilia") = usable on its own.
- Headline with NO employer ("Chief Marketing Officer", "CMO | Cybersecurity") = tells you nothing.
  Pull experience_preview. (Learned the hard way on Annie Reiss.)
- `websites` is stale garbage — Keith Pearce listed zendesk.com while at Alteryx;
  Ryan Kam listed salesforce.com while CMO at Omilia. NEVER infer employer from websites.
- Our company matches a row with `end: null` -> **yes**
- Our company row has an `end` date -> **no**, and the row with `end: null` is the destination
- No current row at all (most recent has an end date) -> **no**, between roles
- Profile is the wrong human (12.5% of stored URLs were) -> **unreadable**, do not stamp yes/no

## Write vocabulary (HubSpot contact properties that exist)
- `ai__li_still_at_company` — enum: yes | no | unreadable
- `ai__contact_evidence` — string, cite the identifier + dated roles (max ~1000 chars)
- `ai__contact_verified_date` — date, YYYY-MM-DD (census stamps have this BLANK; that's how to tell them apart)
- `ai__sources_confirming` — number
- `hs_lead_status` — for movers: `No Longer with Company`.
  Destination ambiguous/fractional/multiple: `Need Updated Info`. Retired: `Retired - Remove from All Lists`.
- Leave `hs_lead_status` ALONE on confirmed (yes) contacts — it must stay `ConnectandSell Prospect`
  or they drop off list 8260.

Batch write: POST /crm/v3/objects/contacts/batch/update  {"inputs":[{"id","properties"}]}

## Reassociation (movers with a known destination)
Both typeIds are required or `associatedcompanyid` stays empty:
```
PUT /crm/v4/objects/contacts/{cid}/associations/companies/{companyId}
[{"associationCategory":"HUBSPOT_DEFINED","associationTypeId":1},
 {"associationCategory":"HUBSPOT_DEFINED","associationTypeId":279}]
```

## Rebuild the queue (run after any big write)
See the `Rebuild live remaining verification queue` script: pulls 5243 membership,
batch-reads props, splits into queue_li.json / queue_noli.json by presence of a LinkedIn identifier.

## Measured so far
LinkedIn beats ZoomInfo 7/9 vs 2/9 on the same people. Confirm rate is running ~1 in 6 —
this list has heavy employment decay, so expect most stamps to be `no`.

## Still open
- 29 unverified with no LinkedIn URL (queue_noli.json) -> ZoomInfo enrich_contacts, 10/batch
- Movers whose destination company record was ambiguous: Juliette Kopecky, Randy Guard,
  Nadya Kohl, Jim Wilson, Brad Hill, David Howland, Yama Habibzai
- `jobtitle` has 3 competing writers at 38% oscillation (HubSpot admin fix — Shawn only)
- 4 persona workflows race each other; `Does Not Match Persona` only fires on BLANK personas
- ROTATE: HubSpot PAT, both Unipile keys, NeverBounce key (all appeared in transcript)

## MOVER PIPELINE (run this after every ~20 verdicts, not at the end)
A `no` verdict is only half the job. The full loop for a mover with a real company destination:

1. **ZoomInfo** `enrich_contacts`, max 10 per call, keyed on firstName+lastName+companyName (the NEW company).
   requiredFields: email, phone, mobilePhone, jobTitle, companyName, contactAccuracyScore,
   zoominfoCompanyId, positionStartDate, managementLevel. Always pass a `userIntent`.
   - FULL_MATCH with a positionStartDate that agrees with LinkedIn = two independent sources. Best evidence there is.
   - COMPANY_ONLY_MATCH = ZI knows the company, not the person. No email. Keep the LinkedIn verdict, skip the email.
   - Watch for ZI returning a nonsense companyName on a FULL_MATCH (it gave "Christine Nicole Photography"
     for Micheline Nijmeh, who is CMO at ThoughtSpot). LinkedIn wins on employer; ZI's phone may still be good.
2. **NeverBounce** every new email before writing it. `/v4/single/check`.
   valid / catchall / unknown are all safe to write. Only `invalid` is disqualifying.
3. **Prefer a first-party email** over a derived one — LinkedIn's contact_info block is the person's own
   published address (gwen.lamar@ beat ZoomInfo's gwendolyn.lamar@, both valid).
4. **Company record**: search `/crm/v3/objects/companies/search` by **domain EQ**, not by name.
   Name search returns junk ("Federal Signal" -> five federal credit unions). Create it if the domain misses.
5. **Re-associate**: DELETE stale associations, then PUT the new one with BOTH typeIds (1 and 279).
6. **Preserve the old email** into `ai__email_information` before overwriting `email`.

### THE RULE I GOT WRONG ONCE — reconcile the flag after re-association
`ai__li_still_at_company` is scoped to *the company the contact is associated to*. The moment you
re-associate a mover to their new employer, a `no` is a lie and it hides a freshly verified, freshly
emailed marketing leader from list 8260. After re-associating:
- still a marketing leader -> `yes`, `hs_lead_status = ConnectandSell Prospect`, `sources_confirming = 2`
- left marketing (COO/GM/comms/foundation) -> `yes` for employment, but `hs_lead_status = Not Decision Maker`
  so they stay accurate in the CRM without polluting the calling list
- went independent / fractional / between roles / retired -> do NOT re-associate; leave `no` +
  `No Longer with Company` (or `Retired - Remove from All Lists`)

### Also observed
`jobtitle` gets rewritten within seconds of a PATCH ("Senior VP, Revenue Marketing" -> "Senior Vice President
of Revenue Marketing"). That is the 3-writer / 38%-oscillation problem. Substance survives, exact string does not.
Do not rely on an exact jobtitle string you just wrote.

### HARD RULE — email domain must match the LinkedIn-confirmed company (Shawn, 2026-08-17)
Never write a ZoomInfo email whose domain does not belong to the company LinkedIn confirmed.
ZoomInfo will happily return a former-employer address; writing it puts the exact stale data back
that this whole cleanup exists to remove.

Before any email write:
  email_domain == company_domain (or shares the org root token) -> write it
  anything else                                                 -> DO NOT WRITE. Leave the field blank.
A blank email is fine. A wrong email is not — it re-poisons the record and bounces on the next send.
Same test applies to emails harvested from a LinkedIn contact_info block.

Audit that already ran on the first 22 movers: 0 mismatches, and 0 of them had a pre-existing email,
so nothing stale was reinstated. 13 were left blank because ZoomInfo had no address for them.

### WORKFLOW 1829121879 — NOT A BUG. THIS IS THE DESIGN. (corrected by Shawn 2026-08-17)

> CORRECTED BY SHAWN 2026-08-17, read this before acting on anything below in this section:
> "their lead status may change.. the point of that workflow was when someone's information is
> found they can go back to being a prospect at their new company"
>
> So the overwrite is INTENTIONAL AND DESIRABLE. Finding fresh information on a contact is
> exactly the trigger that should return them to prospect status at their new employer. Do NOT
> try to suppress workflow 1829121879, and do NOT ask Shawn to add a lead-status guard to it -
> I recommended that earlier and it was WRONG. Withdraw that recommendation.
>
> What follows is therefore a description of expected behaviour, not a defect:
>   - writing `email` triggers 1829121879, which sets hs_lead_status asynchronously AFTER the PATCH
>   - re-asserting lead status inside the same PATCH does not survive, and should not be attempted
>   - never "fix" a lead status back to a stale value just because you saw it before the write
>
> The ONE case that still needs protection is a contact who genuinely cannot buy (an EA, an IC
> rep, a one-person shop). For those the lead status is allowed to flip to Prospect - the durable
> exclusion is the persona marker in ai__contact_evidence, which no workflow writes, and which
> list 8260 filters on. That is why the marker exists and why it must not live in hs_lead_status.
CULPRIT IDENTIFIED: workflow **1829121879 "Update - Contact Needs Updated - After New Info Put In"**.
  enrollment: contact_needs_updated = "Needs Updated" AND email IS_KNOWN AND email updated AFTER
              contact_needs_updated was set.  shouldReEnroll = TRUE.
  action 2:   SET hs_lead_status = "ConnectandSell Prospect" (static)
  it also flips contact_needs_updated -> "Updated", which un-arms it until the flag is set again.

THE TRIGGER IS WRITING AN EMAIL, NOT THE RE-ASSOCIATION. (I first blamed re-association; the data
says otherwise.) Discriminator from the 2026-08-17 run:
  Aaron Russo, Ann Boyd  — I wrote a new email -> flipped to ConnectandSell Prospect ~15s later
  Kim Legelis, Bill Clausen — no email written  -> "Not Decision Maker" stuck fine
So: any time you write `email` onto a contact carrying contact_needs_updated = "Needs Updated",
expect hs_lead_status to be overwritten to ConnectandSell Prospect seconds later.

WORKAROUND that works: re-PATCH hs_lead_status AFTER the workflow has run. It sticks the second
time because the workflow already consumed its enrollment (contact_needs_updated is now "Updated").
All four non-marketing contacts verified as "Not Decision Maker" after the re-PATCH.

DURABLE BELT — the [NOT-MKT] marker. `ai__contact_evidence` is a field no workflow writes.
Prefix `[NOT-MKT] ` on it for anyone employed but NOT a marketing decision maker. List 8260 now
carries a fourth filter:
  ai__contact_evidence DOES_NOT_CONTAIN "[NOT-MKT]"  (operationType STRING, includeObjectsWithNoValueSet true)
Write `Not Decision Maker` as well — the marker is the belt, the lead status is the braces.
Applied to: Kim Legelis (2096251), Bill Clausen (9264889945), Aaron Russo (2454751), Ann Boyd (1612612).
movepipe.py adds the marker automatically when mkt=False.

OTHER hs_lead_status writers found while hunting (all enabled, contact-scoped):
  388688220  "Lead Status to CAS Prospect"      enrolls on hs_lead_status IS_UNKNOWN -> CAS Prospect
  213710961  "Engaged Exec to CAS List"         well-behaved: EXCLUDES Not Decision Maker from enrollment
  1646808477 "Quick Hang Up to CAS Prospect"
  1685953621 "Voicemail Reached"                shouldReEnroll = true
SHAWN ADMIN FIX: add "Not Decision Maker" (and "No Longer with Company", "Retired - Remove from All
Lists") to a suppression check in 1829121879 the way 213710961 already does it.

### THE [NOT-MKT] TEST — CORRECTED BY SHAWN (2026-08-17)
"not a marketer, doesnt mean they cant be a decision maker."

I was applying [NOT-MKT] to anyone outside the marketing department. WRONG. The test is
**CAN THIS PERSON BUY?**, not "what department are they in?"

MARK [NOT-MKT] only when the person genuinely has no budget to spend:
  - independent / fractional / one-person consultancy (no company to buy for)
  - individual-contributor sales rep (carries a quota, does not sign contracts)
  - outside advisor/consultant to a company that has its own exec in that seat
  - retired

DO NOT mark [NOT-MKT] just because the title is not marketing. These people BUY:
  - CRO, VP/SVP Sales, Chief Commercial Officer  (they own the outbound number - often a
    BETTER ConnectAndSell buyer than the CMO)
  - EVP Partnerships, GM, COO, Director of Demand Generation, VP Communications
  - any exec with a P&L or a departmental budget

Flipped back ON 2026-08-17 after Shawn's correction: Bill Clausen (EVP Partnerships, ECHO),
Aaron Russo (VP Global Flagship Sales, Accruent), Ann Boyd (VP Communications, Checkmarx),
Judah Guber (CRO, Onetab), Lyndsi Stevens (Dir Demand Gen, Defense Unicorns),
Rich Wenning (Market Director NA, Consortium), Michele Bedford (Director Strategy Gov, Microsoft).
Marker KEPT on: Kim Legelis (outside consultant), David Tam (own 1-person shop),
Ralph Calistri (IC rep at Cisco).

## OPEN ITEM found 2026-08-17: stale emails survive the mover pipeline
movepipe.py only WRITES an email when it passes the domain hard rule. It never
clears an existing email that belongs to the PRIOR employer. Spot check after
the 66-mover run:
  - Thomas Been  -> Domino Data Lab, but email still thomas.been@datastax.com
  - Trisha Fields -> Mighty & True,  but email still tfields@sonatype.com
So ~all movers with no findable new address still carry a dead address.
FIX (do as a sweep over reassoc_log.json once verification is finished):
for each mover, if email domain != new company domain, move the address into
ai__email_information as "STALE - <addr> was at <prior employer>" and blank the
email field. NOTE: writing/clearing `email` is what triggers workflow 1829121879
to overwrite hs_lead_status, so re-assert hs_lead_status in the same PATCH and
re-check after.

## ALSO confirmed 2026-08-17: jobtitle really is being reverted
movepipe PATCHed Trisha Fields jobtitle="Vice President, Client Strategy";
`company` and the association stuck, jobtitle read back as the OLD
"Vice President of Performance Marketing". This is the 3-competing-writers
oscillation on jobtitle. Do not trust HubSpot jobtitle; the truth is in
ai__contact_evidence.

# ===== 2026-08-17: LIST 5243 VERIFICATION COMPLETE =====

## Final state (read back from HubSpot, not from my logs)
LIST 5243: 342 members -> 316 yes / 11 no / 15 unreadable / **0 unverified**
LIST 8260 (the clean calling list): 308 members, ALL 'yes'
li_verdicts.json: 493 verdicts total (people leave list 5243 as lead status changes,
so the log is larger than current membership - that is expected, not a bug)
reassoc_log.json: 71 movers fully re-associated to their real employer

## What "0 unverified" means and how I got there
The old nextbatch.py only walked queue_li.json (contacts that HAD a stored LinkedIn
URL). It reported "REMAINING 0" while 30 contacts on the list had never been touched
because they had NO LinkedIn URL on file. ALWAYS verify completion by reading
ai__li_still_at_company straight off list membership, never off the local queue.

## NEW TECHNIQUE that closed the last 30: LinkedIn people search
When there is no LinkedIn URL anywhere, search LinkedIn by name+company:
  POST https://api30.unipile.com:16072/api/v1/linkedin/search?account_id=...&limit=5
  body {"api":"classic","category":"people","keywords":"Firstname Lastname Company"}
Then read the returned public_identifier with the normal users/{id} call.
Order of attack for a contact with no URL:
  1. ZoomInfo enrich_contacts requiredFields ["externalUrls",...] -> often hands back
     the LinkedIn URL (this alone solved ~half of them)
  2. if ZoomInfo gives several LinkedIn URLs, try them in order - the first is often dead
  3. if ZoomInfo has none or NO_MATCH, LinkedIn people search by keywords
  4. only after all three fail -> 'unreadable', and say in the evidence exactly which
     sources were tried and what ZoomInfo did or did not corroborate

## ZoomInfo was WRONG or STALE on a lot of them - always finish on LinkedIn
  - Juliann Irwin: ZI said Kasasa (updated 2026-07-23). LinkedIn: left 12/2023.
  - Nancy Elsner: ZI said TouchTunes (updated 2026-08-14, THREE DAYS OLD). LinkedIn: left 04/2024.
  - Steve Dauber: ZI said RedSeal VP Marketing "since 2009". LinkedIn: left 01/2011.
  - Steve Susina: ZI said NRI. LinkedIn: ended 06/2026.
  - Chris Heggem: ZI said Wallarm. LinkedIn: Ciroos.
  - Ciroos company name-search in ZI returned redcrosskarnataka.org (garbage).
  Rule stands: ZoomInfo is a lead to a URL, never the verdict.

## Verify a domain, never guess one
enrich_companies by NAME fails or returns garbage often (Tusker NO_MATCH, Aidoc
NO_MATCH, Ciroos wrong). enrich_companies by companyWebsite is the reliable check:
pass a candidate domain and only accept a FULL_MATCH on the right name.
Confirmed this session: tuskerco.com, ciroos.ai, aidoc.com, domino.ai, anaplan.com,
jfrog.com, celonis.com, artsquest.org, devicie.com, revenuebase.ai, mightyandtrue.com,
aftr.live, sandkindustrial.com.

## Persona calls I made (flip any of these if you disagree)
OFF the list ([NOT-MKT] or 'no'):
  Stephanie Hunicke - own one-person freelance event shop
  Julie Kawejsza - founder of AFTR, a brand-new one-person content studio
  Michel Benjamin - founder of his own fractional-CMO practice
  Marcie Montague - opening an independent bookstore
  Stacie Immesberger - Anaplan "Supply Chain Domain Advisory", an SME seat
  Chris Sheen - Celonis "Director of Social", a function lead not a budget holder
  Carey Waterman - Executive Assistant to the CMO/CRO, a gatekeeper
ON the list despite an odd title:
  Forrest Leighton - fractional CMO AT a named company (RevenueBase)
  Trisha Fields - VP Client Strategy at an agency (Mighty & True)
  Katy Gilligan - promoted from SVP Marketing to COO at Brandpoint
  Elise Ring - moved from VP Marketing to VP Strategic Growth, still on the leadership team
  Laura Felthaus - VP Marketing scope EXPANDED to VP/GM Residential with P&L

## Not-a-US-dial (timezone flags written into the evidence field)
Ayaan Mohamud (Sydney), Kaushal Bhatt (Bengaluru), Abhijit Mhetre (Pune),
Joanne Wong (Singapore), Gily Netzer (Tel Aviv), Chris Sheen (London)

# ===== 2026-08-17b: MOVER EMAIL REPAIR =====
Shawn: "We'd definitely want the new email for their current role if we can get it."

## Before -> after across the 70 re-associated movers
  email at CURRENT employer : 28 -> 53
  email at PRIOR employer   : 18 ->  4  (all four flagged DO NOT EMAIL)
  no email at all           : 24 -> 13
25 addresses written: 15 NeverBounce 'valid', 8 'catchall', 2 pattern-derived-unverified.

## THE METHOD (repeatable - this is the part to reuse)
ZoomInfo has NO email for most recent movers (COMPANY_ONLY_MATCH, or FULL_MATCH with the
email field simply absent). Do not stop there. Derive and then PROVE:
 1. Learn the company's real address format from a known-good address AT THAT EXACT DOMAIN
    already sitting in HubSpot:
      POST /crm/v3/objects/contacts/search  filter email CONTAINS_TOKEN "*@thedomain.com"
    Score the samples against a pattern table (first.last, flast, first, firstlast, f.last,
    firstl, ...) and keep the patterns that actually explain a sample. 22 of 42 domains were
    solved from data we already owned - zero external calls.
 2. Construct the candidate and verify it with NeverBounce /v4/single/check.
      valid    -> write it. Proven mailbox.
      catchall -> domain accepts mail but will not confirm the person. Write it, flag it.
      unknown  -> the server refuses verification (Workday, Zendesk, Microsoft, UKG, dell.org,
                  hexagonmi, aidoc...). Proves nothing. Only write if the pattern is
                  unambiguous from >=2 samples, and flag it UNVERIFIED.
      invalid  -> real negative when the domain DOES answer. Never write it.
 3. Run NeverBounce in a THREAD POOL (6 workers) and in the BACKGROUND - a serial loop over
    ~40 contacts blows the 2-minute Bash timeout.
 4. Preserve every replaced address in ai__email_information. Nothing is lost.

## invalid-at-an-answering-domain is a real finding, not a dead end
 - Thomas Been: every pattern INVALID at domino.ai, which does answer verification. The company
   rebranded Domino Data Lab -> Domino but kept the OLD mail domain. thomas.been@dominodatalab.com
   is valid. ALIAS-DOMAIN RULE: accept a different domain only when ZoomInfo enrich_companies on
   it returns the SAME company id (dominodatalab.com -> id 358094550 == domino.ai). Then it is
   the same employer, not a different org, and the hard rule is satisfied in spirit.
 - Kristin Melville: every pattern INVALID at celigo.com, which also answers. Her address is
   genuinely non-standard. Left alone and flagged - a guess there would be WRONG, not unproven.

## RESOLVED 2026-08-17c - all four prior-employer addresses are gone (see below)
  Kristin Melville  kmelville@clari.com        -> should be @celigo.com   (all patterns invalid)
  Mariana Cogan     mariana.cogan@people.ai    -> should be @hexagonmi.com (no sample, unknown)
  Stacy Malyil      smalyil@healthwise.org     -> should be @aidoc.com     (ambiguous pattern)
  Juliann Irwin     juliann.irwin@kasasa.com   -> should be @sandkindustrial.com (no reliable sample)
I did NOT blank these - blanking is Shawn's call. They are safe to DIAL, not to email.

## WORKFLOW RACE - re-asserting inside the same PATCH IS NOT ENOUGH
Writing `email` triggers workflow 1829121879, which fires asynchronously AFTER the PATCH and
overwrites hs_lead_status. I re-asserted lead status in the same PATCH; 9 of 10 held and Joy
Corso still drifted. So: always RE-READ lead status after an email write, do not trust the
write. The durable protection remains the [NOT-MKT] marker in ai__contact_evidence, which no
workflow touches, and which list 8260 filters on.
(Joy Corso's drift was harmless - the stale 'Not Decision Maker' was itself wrong; she is CAO/CPO
at Sprinklr but still owns the Marketing org, so 'ConnectandSell Prospect' is the right value.)


# ===== 2026-08-17c: PRIOR-EMPLOYER EMAILS ELIMINATED + LIST PLUMBING FOUND =====
Shawn: "we don't want the old stale emails ... we'd definitely can move that to past email
address property I have"

## The property to use - it already exists and is already well populated
  previous__email                  "Previous - Email"                 string/text   (12,785 populated)
  previous__company_domain_name    "Previous - Company Domain Name"   URL type      (12,051 populated)
CAREFUL: previous__company_domain_name is a URL-type property. A bare domain is REJECTED with
INVALID_URL - you must write "https://" + domain.
NEVER clobber an existing previous__email value; read it first and leave it if already set.

## Final state of the 70 movers
  email at CURRENT employer : 56
  email field empty         : 14   (old address preserved in previous__email)
  email at PRIOR employer   :  0
  previous__email populated : 69 of 70

## Clearing a primary email - the gotcha
PATCHing email:"" fails with "Remove all secondary emails first before deleting the primary
email" whenever hs_additional_emails holds anything. Clear hs_additional_emails in one PATCH,
then clear email in a SECOND PATCH. Two writes, in that order.

## LOOK IN hs_additional_emails BEFORE HUNTING - the answer is sometimes already in the CRM
Stacy Malyil's current-employer address stacys@aidoc.com was sitting in hs_additional_emails
the whole time while the primary Email field held a dead healthwise.org address. Mariana Cogan's
mariana.cogan@hexagon.com likewise. ALWAYS sweep hs_additional_emails, email_2, email_other,
work_email and linkedin__email for an address on the current employer's domain before deriving
anything. Cost: one batch read. Both were NeverBounce 'valid'.

## NICKNAME VARIANTS - try them before giving up
celigo.com rejected kristin.melville, kmelville, kristinmelville, kristin, kris and melville as
INVALID, then accepted kris.melville@celigo.com. She goes by Kris. Because the server answered
INVALID five times and VALID once it is discriminating properly, so that is a genuine positive
and not a catch-all. When a domain answers verification, keep trying variants - the negatives
are informative.

## ALIAS DOMAINS - two tiers, and they are not equally strong
  TIER 1, same ZoomInfo company id -> accept.
    dominodatalab.com -> id 358094550, identical to domino.ai. Same company, legacy mail domain.
  TIER 2, parent/child, DIFFERENT ids -> accept only with a NeverBounce 'valid' AND a note.
    hexagon.com = Hexagon, id 17662709 (parent). hexagonmi.com = Hexagon Manufacturing
    Intelligence, id 396535383 (the division LinkedIn confirms she leads marketing for).
    Groups that size run one corporate mail domain. Recorded as tier 2 in the evidence field.

## A BUG I CREATED - never put the exclusion token inside a note that REMOVES it
When Shawn corrected my persona filtering I flipped 7 people back ON, and appended a note reading
"CORRECTED: <token> marker REMOVED". That note CONTAINS the token, so list 8260's
"evidence DOES NOT CONTAIN <token>" filter kept matching and those 7 stayed wrongly excluded for
hours. Ann Boyd, Rich Wenning, Michele Bedford, Aaron Russo, William Clausen, Judah Guber,
Lyndsi Stevens. Fixed by stripping every occurrence and writing the correction as
"PERSONA EXCLUSION LIFTED" with no token. List 8260 went 307 -> 312.
RULE: a filter token is a control character, not prose. Never write it in a sentence about
itself. Build it at runtime in scripts so the script file cannot seed it either.

## WHY 46 OF 70 MOVERS ARE NO LONGER ON LIST 5243 - it is the ICP filter, mostly working
List 5243 requires ALL of: lead status in [CAS - No Pitch - Quick Hang Up, ConnectandSell
Prospect]; a KNOWN phone (mobilephone OR phone OR business_phone); hs_persona in
persona_3/8/11; lifecyclestage not other/customer; AND membership in list 422 "HubSpot Tech
Used - All" AND list 4830 "ZoomInfo - Contacts".
  list 4830 = currently_use_zoominfo_ = Yes (OR nested list)
44 of the 46 are still in 422 but fell OUT of 4830. Re-associating a contact to a new employer
moves them to a company that does not carry currently_use_zoominfo_ = Yes, so they leave 5243 -
and 8260 gates on IN_LIST 5243, so all the verification work on them cannot surface.
THE SPLIT THAT MATTERS:
  27 of 46 sit on company records I CREATED this session. Their ICP flags were never enriched,
     so "out of profile" is UNPROVEN, not established. These may be qualified prospects being
     silently dropped. -> NEXT ACTION: enrich those 27 companies for the HubSpot and ZoomInfo
     tech signals; whichever qualify flow back onto 5243 and then 8260 automatically.
  18 of 46 sit on pre-existing ENRICHED companies with currently_use_zoominfo_ blank. Genuinely
     outside the ZoomInfo/HubSpot ICP for this campaign. Accurate records, wrong campaign.
   1 shows uses ZoomInfo = Yes and should return on the next list rebuild.

# ===== 2026-08-17e: PHONE — THE OLD COMPANY'S SWITCHBOARD WAS STILL ON THE MOVERS =====
Shawn: "Did we make sure that the company phone is the company/business phone on the contacts
now and not their old company phone... So we don't end up calling their old company"

He was right, and this was the most damaging defect found in the whole pass. Email was the
low-stakes version of this problem. The PHONE is the channel the reps actually use, and list
5243 REQUIRES a known phone, so every one of these was dialable.

## What was wrong
69 of 70 movers had a business/company number that did not match their new employer.
31 were PROVEN to belong to a named FORMER employer by matching the number against that
company's own record in HubSpot:
  Thomas Been -> DataStax        Nancy Elsner -> TouchTunes    Chris Heggem -> Noname Security
  Keith Pearce -> Alteryx        David Spitz -> Egnyte         Venu Nambiar -> Marlabs
  Kelli Negro -> Billtrust       Tal Klein -> Relay Network    Taylor Mortti -> Virtuoso
  Renette Youssef -> Velo3D      Eric Olson -> QuickBase       Micheline Nijmeh -> JFrog
  Mariana Cogan -> People.ai     Melike Abacioglu -> Mixpanel  Matthew Gaudio -> Advizex
  ...and 16 more. Several corroborate the filed previous__email exactly (dspitz@egnyte.com etc).

## The decisive argument, which covers the ones we could NOT name
business_phone is by definition the CURRENT employer's business line. Every one of these values
was on the record BEFORE the move was discovered, so it describes the OLD job whether or not a
company record exists to prove ownership. Do not wait for proof on each one.

## The fix applied (fixphones.py)
44 records corrected:
  - business_phone -> the new employer's switchboard where the company record has one
  - business_phone CLEARED where the new company has no number (better empty than wrong)
  - `phone` touched ONLY where proven to belong to a former employer (3 cases)
  - mobilephone NEVER touched - a mobile follows the person
  - old number + whose it was recorded in ai__contact_evidence
VERIFIED AFTER: all 70 movers now have business_phone matching their employer or empty. Zero
mismatches. 2 contacts (Mariana Cogan, Melike Abacioglu) now have NO dialable number at all and
will correctly fall off 5243 - both had only former-employer numbers.

## Is it wider than the movers? Checked, and mostly no.
Calling list 8260, all 312:
  276  business_phone matches the associated company
   32  does not match
    3  company record has no phone to compare
    1  contact has no business_phone
NONE of the 32 is owned by a DIFFERENT company record - they are alternate or direct lines at
the same employer (three Azul contacts share Azul's office line, two Workiva contacts share the
Ames HQ line while the company record holds a toll-free). So the wrong-company phone problem was
specific to re-association, which is what created it.
Two to eyeball by hand, not proven wrong: (651) 687-7000 on Steven Pritt / Thomson Reuters and
+44 7900276885 on Christina O'Connor / Deltek - both are numbers that ALSO sat on a mover's
record before this fix, so one of each pair is wrong.
A check on how many contacts share each number returned all zeros and is UNRELIABLE - the
CONTAINS_TOKEN search on business_phone does not match raw digits against the stored
parenthesised format. Do not cite that check.

## ADD THIS TO THE MOVER PIPELINE PERMANENTLY
Re-association must carry the phone, not just the company and the email:
  1. read the new company's `phone`
  2. if business_phone != the new company's phone -> overwrite it, or clear it if the company
     has no number
  3. leave mobilephone alone
  4. record the replaced number and its owner in the evidence field
Skipping step 2 leaves a dialable line to the wrong company on a list whose entry criteria
require a phone. That is the worst possible combination.

# ===== 2026-08-18: TWO QA AUDITS. THREE CLAIMS OF MINE WERE WRONG. =====
Shawn asked for two quality agents to QA the process. Both landed. Corrections first, because
three things I had written down and told him were not true.

## 1. "662 contacts in, every one read on LinkedIn" — FALSE
Verified with coverage.py against the intake snapshot:
  intake (mem5243.txt)          662
  carrying a verdict            491
  NEVER verified                171
li_verdicts.json holds 493 verdicts, 2 of which are for contacts not in the intake snapshot.
The 171 left list 5243 BEFORE they were read - ejected by this process's own lead-status and
persona writes, because both are entry criteria for the list. None of them are on any calling
list, so no rep is dialing an unverified record, but "we read them all" was wrong.
RULE: measure PROGRESS against live membership; measure COVERAGE against the intake snapshot.

## 2. "None of the 32 non-matching phones belonged to a different company" — FALSE
id32.py identified ownership with companies.search phone CONTAINS_TOKEN "*<raw digits>*" - the
EXACT query shape I had condemned one message earlier - and returned "no company record owns it"
for all 32. I read that silence as a finding and wrote a conclusion on it.
redo32.py does it correctly: tries digits, dashed, parenthesised, +1 and dotted forms, AND
self-tests on (212) 991-6540 = TouchTunes, a number known to be present, before trusting any
null. Result: 9 of 32 sit on a differently-named company's number.
  Heath Johnson + Erin Wall  Workiva          -> webfilings.com   (Workiva's original name)
  Tommy Bliven               66degrees        -> Pandera Systems  (rebranded to 66degrees)
  Robert Hilson              Reveal           -> Logikcull        (acquired by Reveal)
  John Reumann               Taylor           -> MentorMate       (a Taylor company)
  Kevin Potts                Softdocs         -> ValGenesis
  Joshua Raymond             OMNIA Partners   -> Ministry Brands
  Dana Liedholm              Cytracom         -> Kaseya
  Josh Stancil               Procure Analytics-> Insight Sourcing Group
ALL NINE FLAGGED IN ai__contact_evidence, NONE OVERWRITTEN (flag9.py). They are confirmed
CURRENT at their employer, so the number may be a predecessor line that still reaches them, and
replacing a working direct line with a toll-free menu is worse. Non-mover phone conflicts are a
HUMAN QUEUE item, never an auto-write.

## 3. THE ALIAS TEST DOES NOT DETECT REBRANDS OR ACQUISITIONS — correct the rule
I had written: same ZoomInfo company id => same company. That is sound for DOMAIN aliases inside
one entity (dominodatalab.com and domino.ai are both id 358094550). It is NOT a test for
corporate identity across a rename or acquisition. ZoomInfo keeps the predecessor as its own
record with its own id:
  Workiva 371769443   vs WebFilings 353924011
  Reveal 351793036    vs Logikcull 369750751
  66degrees 354213475 vs Pandera Systems 346166229
  Taylor 103284965    vs MentorMate 24543647
So "different id" does NOT mean "different company" once an acquisition is involved. The alias
test can only ever CONFIRM sameness, never establish difference.

## 4. Unreadable rate was understated ~3x
41 of 493 verdicts are `unreadable` = 8.3%. The doc said "15 of 662" (2.3%), which was only the
residue still on the list at the end. Budget ~8% for Stage 2 failure, not 2%.

## THE METHOD RULE THAT GENERATED TWO OF THESE ERRORS
Self-test every query against a case whose answer you already know, BEFORE trusting a null
result. A digits-only token search against parenthesised stored numbers returns nothing for
every input, forever. That silence was read as a finding twice in this pass. redo32.py now
does the self-test and refuses to continue if it fails - copy that pattern.

## DNC IS OUT OF SCOPE - Shawn, twice, 2026-08-18
"dont worry about the do not call zoominfo properties" / "i dont want that in here.. i am just
wantint to clean data". An audit found 86 of 312 on the calling list carry a ZoomInfo DNC flag
(78 mobile-only, 3 direct-only, 5 both). NOT ACTED ON, NOT ADDED TO THE PROCESS DOC. Do not
raise it again unless Shawn does.

## STILL TO FOLD IN FROM THE AUDITS (not yet done)
The completeness audit raised 32 items and the automation audit 4 sections. Corrected above are
the ones where the doc was WRONG. The larger set of ADDITIONS is still outstanding - the biggest:
  - hs_lead_status exact enum vocabulary, and the rule to leave it alone on a `yes`
  - the calling list's own four clauses (f8260.json) - the doc never defines its stated output
  - hs_persona: 105 of 324 removals, mechanism entirely absent from the doc
  - movers who went independent/fractional/retired: do NOT re-associate, do NOT flip to `yes`
  - read-back verification of every write, and calculated-field lag (associatedcompanyid ~20s)
  - Unipile account allowlist and the missing account_id on the profile-read line
  - bounce history outranks the email verifier; never re-check an address with bounce data
  - wr.py OVERWRITES ai__contact_evidence; every other writer appends - marker loss root cause
  - the write endpoints are entirely absent from the runbook
  - name normalisation (NFKD, strip to a-z) for pattern construction; O'Dell-class crashes
  - ai__contact_verified_date and D="2026-08-17" hardcoded in 10 scripts
