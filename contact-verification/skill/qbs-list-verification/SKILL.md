---
name: qbs-list-verification
description: Verify and clean a HubSpot contact list against dated LinkedIn employment history so an SDR can dial it without reaching a person's old company. Use whenever someone wants to "verify a list", "clean list <id>", "check who still works there", "run the verification process on <list>", "confirm employment before we call", "re-verify a calling list", or points at a HubSpot objectLists URL and asks to make it accurate. Reads each contact on LinkedIn, records a verdict with evidence, re-associates movers to their real employer, repairs email and PHONE so reps never dial a former employer, and produces two output lists (moved-companies, no-associated-company). Runs interactively for a first pass (queues judgement calls for a human) and unattended for refresh passes. Requires the HubSpot PAT (see qbs-hubspot-private-app) and Shawn's authorized Unipile LinkedIn accounts only. NOT for ticket cleanup (qbs-ticket-reconciliation) or portal audits (hubspot-audit).
---

# QBS Contact List Verification

Turns a purchased or inherited HubSpot list into one a rep can dial without apologising.
Full reference lives in the repo: `contact-verification/docs/verification-process.html`
(clickable flow chart + stage specs), `evidence-ladder.html` (source yields, case histories),
and `FIELD-NOTES.md` (every gotcha, including mistakes that were corrected). **Read the process
doc before a first run on an unfamiliar portal.** This file is the operating checklist and the
guardrails; the docs are the depth.

## The one rule that generates the others
Dated `work_experience` rows are evidence. A headline is marketing. A vendor record is a lead to
a URL, never the verdict. When two sources disagree, the dated row wins and the disagreement gets
written into the evidence field. **Never upgrade a guess into a fact** — a blank field is the cheap
failure; a rep discovering the truth on a call is the expensive one.

## Credentials & access
- HubSpot: `export TOKEN=<PAT>` (see `qbs-hubspot-private-app`). Portal 20682069 unless told otherwise.
- NeverBounce: `export NB=<key>` (email rung only).
- LinkedIn: **Unipile MCP tool only** (`mcp__Unipile__execute-request`, harRequest form). Direct
  curl to the Unipile port is blocked by egress. **Allowlist — use ONLY these account_id values:**
  `S6ua4SfUT4SMRFZFOmyUzQ` and `7lBoyXuETqKdiJYLj5HBGA`. The other connected accounts are CLIENT
  identities; reading prospect profiles through them is not recoverable. Fail closed on anything else.
- ZoomInfo / NeverBounce via their MCP/REST tools for fallbacks.

## Modes
- **First pass on a list -> interactive.** It generates almost all the human-queue items
  (ambiguous destinations, unprovable emails, non-mover phone conflicts, any persona proposal).
  Run it with a person present.
- **Refresh pass -> unattended-safe.** Skips anything stamped within N days; small queue.

## Autonomous end-to-end run (the default; `/qbs-list-verification <listId>`)
The operator's expectation is: **pick a list, run the skill, it just does it.** Honour that.
Do not ask permission between phases, do not stop to report progress, do not hand back a plan
when you were asked for a clean list. Run this sequence to completion:

1. `scripts/listanatomy.py <listId>` — map the gate chain. If it WARNS that the list gates on
   `hs_persona`/`jobtitle`, note it now; it will explain the membership numbers later.
2. Phase 0 preflight + intake snapshot.
3. Loop: `queue.py <listId> 12` -> read -> judge -> `writeverdicts.py`. Repeat until
   `unverified` reads 0 **on two consecutive checks several minutes apart** (dynamic lists
   re-admit members while you work — one zero reading is not done). **`unverified 0` is not by
   itself proof the intake was covered**: this process writes `hs_lead_status`, which is list-entry
   criteria, so contacts our own writes eject stop being members and are never counted as unverified
   again. queue.py now also prints `in intake snapshot but no longer members: N` — reconcile that N
   against your lead-status writes before declaring the pass complete (on 3675 it was 112).
   queue.py re-queues any verdict older than `STALE_DAYS` (default 90), so a refresh pass actually
   re-reads aged records instead of reporting an instant zero.
4. Mover pipeline whenever ~10 movers accumulate, ZoomInfo-verifying each destination domain.
5. Refresh the two output lists; queue ICP enrichment for any company created.
6. Report once, at the end, in the honest format below.

**Self-continuation.** A long list will outlive a single turn. Schedule the next continuation
before the turn ends (`send_later` ~2 minutes out) carrying the full instruction — list id,
credentials, next batch number, escalation ladder, stop condition — so the loop survives a
context boundary. Stop re-arming only when the stop condition in step 3 is met.

**Stop and ask ONLY for:** a guardrail trip (below), a write outside this skill's field set,
or a Human-queue judgment call. Everything else, decide and keep moving. When in doubt about a
single contact, mark it `unreadable` + queue it — never stall the whole run on one record.

## Phase 0 - Preflight (no writes; abort on any failure)
**Run `preflight.py <listId>` first.** It refuses the run — before any record is touched — when
the checkout predates the QA fixes (exit 3), TOKEN is missing or HubSpot is unreachable (exit 2),
the list is empty or not a contact list (exit 2), a written property no longer exists (exit 3), or
`hs_lead_status` has lost one of the four literals (exit 3). Every one of those previously
presented as a confident "nothing needed refreshing". It is MANDATORY for an unattended run and
cheap enough to be worth it interactively. It cannot check LinkedIn — do the Unipile self-test
(step 1) yourself.

`listanatomy.py` now **exits 3** on a non-contact list or a non-DYNAMIC list, and prints a
second warning class: gates on properties **this process writes** (`hs_lead_status`, `phone`,
`business_phone`, …). That second case means the list changes membership underneath the run —
measure coverage against the intake snapshot, never against live membership.

1. Self-test every query type against a case whose answer you already know before trusting a null
   result (a digits-only phone search silently matches nothing — see FIELD-NOTES). If the self-test
   fails, STOP.
2. Read the list's REAL criteria - **`python3 scripts/listanatomy.py <listId>` does all of this
   automatically and writes `list_anatomy_<id>.json`**; the manual walk is described here so you can
   verify it. `GET /crm/v3/lists/{id}?includeFilters=true`. Confirm it is a
   contact list (objectTypeId 0-1) and note every gating property.
   **Map the FULL gate chain before writing anything — membership is rarely governed by the list you
   were handed.** Walk `filterBranch` recursively and record all four filter kinds; a parser that only
   reads `property` silently misses the ones that matter:
   - `filterType: "PROPERTY"` — contact fields (e.g. `hs_lead_status IS_ANY_OF [...]`, `phone IS_KNOWN`).
   - `filterType: "IN_LIST"` (`listId`) — **an upstream list the contact must ALSO be in.** Recurse into
     each one and map its criteria too. These are the real gates and they are invisible from the child list.
   - `filterBranchType: "ASSOCIATION"` (`objectTypeId 0-2`, `associationTypeId 279`) — conditions on the
     ASSOCIATED COMPANY (e.g. `lifecyclestage IS_NONE_OF [other, customer]`, `number_of_sales_employees`).
     Re-associating a contact re-evaluates every one of these.
   - Nested OR-of-AND branches — a contact needs only ONE branch to pass, so never conclude "removed"
     from a single failing clause.
   Write the chain to `list_anatomy_<id>.json`. On 3675 the chain was: 3675 -> IN_LIST 1678
   ("HubSpot Tech Used - Not Clients") AND IN_LIST 3196 ("CEO - 50-99 Sales Employees", itself gated on
   `hs_persona = persona_1` + an ASSOCIATION filter on company `number_of_sales_employees`), plus a phone
   requirement (`phone` OR `mobilephone` OR `business_phone` IS_KNOWN) and a company-lifecyclestage gate.
   Knowing this up front is what separates "our writes broke the list" from "the ICP gate did its job".
3. **Snapshot intake membership to `mem_<id>.txt` before the first write** and keep it immutable.
   This process writes lead status (and, if enabled, persona) — both are often list entry criteria,
   so its own writes eject records from the list it is working. On list 5243 that removed 171 of 662
   before they were read. Measure PROGRESS against live membership, COVERAGE against the snapshot.
4. Refuse to run if: the list is static or not a contact list; OR any list this run writes into
   filters on a prose property this run writes (e.g. a calling list keyed on evidence text) unless
   that clause uses a dedicated marker property.

## The batch loop (write after EVERY batch - reps dial while it runs)
1. `python3 scripts/queue.py <listId> 6` -> next 6 unverified with their LinkedIn identifier.
2. ~6 parallel `mcp__Unipile__execute-request` reads, harRequest form, allowlisted account_id,
   `linkedin_sections=experience_preview`. Identifier hygiene: strip `?trk=`, URL-encode non-ASCII,
   never send `*experience`.
   - No URL on file, or 422/locked -> fallback ladder: ZoomInfo `externalUrls` (try each returned
     URL; the first is often dead) -> LinkedIn people search on name+company -> only then `unreadable`,
     naming every source tried.
   - CRM company absent AND `work_experience_total_count` exceeds rows returned -> re-pull with
     `linkedin_sections=experience` BEFORE judging. Skipping this makes confident wrong "no"s.
3. Judge each into a verdict (below).
4. Write the batch: `python3 scripts/writeverdicts.py <listId> batch.json`. It enforces the
   lead-status rules, chunks at 100, diffs requested-vs-returned, reads back to confirm, appends to
   `li_verdicts_<id>.json`, and queues movers to `pending_movers_<id>.json`.
   Batch item fields: `id`, `verdict`, `ev`, and optional `ls`, `newco`, `sources`,
   `title` (current LinkedIn title -> `ai__job_title`), `li_url` (corrected LinkedIn URL -> written
   to BOTH `hs_linkedin_url` and `linkedin_profile_url__unique_value`), `changed` (explicit
   "what changed in HubSpot"). Every write also sets `validated__linkedin_or_manually` and stamps
   the evidence in the standard format (below).

## Verdicts and the exact vocabulary
- **yes** = a dated row for the CRM company with `end: null`. Write evidence + date only.
  **NEVER write hs_lead_status on a yes** — it must stay `ConnectandSell Prospect` or they drop off
  the calling list. (writeverdicts.py refuses an `ls` on a yes.)
- **no** = that company's row has an end date, or a different employer is current. Set lead status
  to exactly one literal: `No Longer with Company` (moved) / `Need Updated Info` (moved, destination
  ambiguous/fractional) / `Retired - Remove from All Lists` / `Not Decision Maker` (employed, cannot buy).
- **unreadable** = a TRANSIENT failure to read: 422/locked, rate-limited, a profile that would not
  load. Worth retrying in days. Name what was tried.
- **no_profile** = there is no LinkedIn profile to read, or a real profile carries no dated history.
  This is PERMANENT for this method — retrying costs a read and buys nothing. Splitting it out of
  `unreadable` is what lets the queue retry the two at different intervals (14 days vs 180) and
  what makes the `unreadable` guardrail mean something. **Use it.** Writing a no-profile contact as
  `unreadable` re-reads them roughly every two weeks, forever, and inflates the guardrail that halts
  the run.
- **When a record needs a human, say so in the record.** Pass `issue` (and `issue_note`) on the
  batch item: it writes `ai__verification_issue`, `ai__verification_issue_note` and
  `ai__verification_issue_on`. Values: `wrong_link_suspected`, `identity_unresolved`, `no_identifier`,
  `ambiguous_destination`, `company_ambiguous`, `succession_conflict`, `duplicate_contact`,
  `division_scope_unclear`, `persona_review`, `title_conflict`, `phone_unverified`,
  `email_unprovable`, `retired_headline`. This is the durable exception register — a judgement call
  queued only to a session scratch file is a judgement call nobody ever sees.

## Fields this process writes (repeatable conventions)
- **Evidence format** (`ai__contact_evidence`): always `Verified - <date> - <evidence> - Changed: <what changed in HubSpot>`. writeverdicts.py builds this; the `Changed:` clause auto-summarises flag/lead-status/title/URL/mover unless you pass an explicit `changed`.
- **`ai__job_title`** (AI-owned title field): write the current LinkedIn-verified title here via the batch `title` field. Always safe — nothing else writes it.
- **`jobtitle`** (native title field, ≥90% confidence only): pass `title_conf` (0-1) alongside `title`. At `title_conf >= 0.90` the batch ALSO writes the native `jobtitle`, so reps see the corrected title in the sidebar, screen-pop and exports without a view change. The gate is enforced in code and **fails closed** — no `title_conf`, no native write — and additionally requires verdict `yes` (movers: a resolved employer domain) and evidence free of hedge words (`probably`, `CAUTION`, `succession`, `may be`, …). Do NOT use `ai__sources_confirming` as the confidence signal; it is a count, populated liberally, and would wave nearly everything through. **What ≥0.90 means:** a dated LinkedIn row for THIS employer whose title string you are reading directly, `end: null`, no competing row, no division/parent ambiguity — i.e. you are reading the title, not inferring it. A headline-only title, a people-search hit, or a vendor title is never ≥0.90.
  Two things make the write reversible and honest: the prior `jobtitle` value is recorded in the evidence string (`jobtitle was 'X' -> 'Y' (conf 0.95)`), and the write is **read back**. `jobtitle` has 3 competing integration writers (~38% oscillation, confirmed reverting a `movepipe` write), so expect some reverts: the scripts print `held on read-back N/M`. A revert is a competing integration, not a failed write — `ai__job_title` still holds the truth, and making the native field stick durably is a HubSpot-admin change to the integration field mappings (Shawn only).
- **`validated__linkedin_or_manually`** (select): set every verified record — `yes`->`Yes`, `no`+Retired->`Retired`, any other `no`/`unreadable`/`no_profile`->`Needs Updated`. (`Delete` is human-only, for bogus records.)
- **`ai__contact_verified_date`** = the last date employment was actually CONFIRMED. Written **only**
  on `yes` or `no`. **`ai__li_last_attempt_date`** = every touch, including a failed read. Stamping a
  verified date on an unreadable made a never-verified record look fresh for 90 days.
- **`ai__li_tenure_years`** / **`ai__li_recent_role_change`**: pass `tenure` (number) and
  `role_change` (`yes`/`no`) on the batch item. Both come off the dated row you already read, cost
  nothing extra, and are the only way tenure-stratified decay is ever computable.
- **`ai__reassociated_on`** (movers): a date, stamped by movepipe. The Moved-Companies list filters
  on THIS, not on the `RE-ASSOCIATED` substring, which truncated out of 22 of 70 movers.
- **LinkedIn URL**: when you correct a slug, pass `li_url`. It is written to `hs_linkedin_url` AND the unique field `linkedin_profile_url__unique_value` (set per-record). A unique-value **collision means another contact already owns that URL** -> compare the two: same person = duplicate (queue for merge, `dedupe_review_<id>.json`), different person = the other record is wrong-linked (queue to fix its URL). Never force past the collision.
- Canonical verdict field is `ai__li_still_at_company` (the calling list keys on it); the legacy string `ai__still_works_at_company` is NOT used.
- Persona ("can this person buy?"): the test is buying power, not department. C-level/EVP/SVP/VP with
  a function, Director of Demand Gen, GM, COO, CRO = buyers. EA/gatekeeper, IC rep, one-person shop,
  outside consultant = not. Anything between the two -> QUEUE, do not decide. **Persona re-mapping
  (`hs_persona`) defaults OFF and produces proposals for human approval** — it was the single largest
  destructive write on 5243.

## Mover pipeline (one transaction per contact; run after ~10-12 movers accumulate)
`scripts/movepipe.py` pattern:
1. Verify the destination domain by `enrich_companies` companyWebsite -> accept only FULL_MATCH on
   the expected name. Never guess a domain. Disambiguate alias-vs-move first (a changed email domain
   is usually an alias, not a move) and never pick between same-named companies -> QUEUE.
   Independent / fractional / between-roles / retired have NO destination: leave `no`, do not create
   a company, do not flip to `yes`.
2. Find-or-create company by `domain EQ`. On create, ENQUEUE tech-signal enrichment (an unenriched
   new company silently drops its occupants out of every ICP list).
   **A newly created company has NONE of the ICP fields the calling list gates on** (`number_of_sales_employees`,
   tech signals, lifecyclestage), so every mover re-associated to a new company disappears from the calling
   list until those are filled. Pull `employeeCountByDepartment` from ZoomInfo `enrich_companies` and write
   the ICP band to `icp_queue_<id>.json` — do NOT auto-write ICP fields; they redefine list membership and
   are a human decision. **Then check whether the mover still belongs in the ICP at all:** of 7 new companies
   on 3675, only ONE was inside the target 50-99 sales-employee band (it had 67); the others measured 174, 12,
   11, 3 and 2. A mover dropping off the calling list is usually CORRECT: they left
   for a company outside the target profile. Do not "fix" it by loosening the ICP; route them from the
   Moved-Companies list to a campaign that fits.
3. DELETE stale associations, PUT new with BOTH `associationTypeId` 1 AND 279 (one alone leaves
   `associatedcompanyid` empty). `associatedcompanyid` is calculated and lags ~20s - re-read before
   concluding failure.
4. Reconcile flag to `yes`; set `company`; set `ai__job_title` to the new-company title and
   `validated__linkedin_or_manually` (`Yes` if a live decision-maker, else `Needs Updated`); append
   evidence in the `Verified - <date> - ... - Changed: RE-ASSOCIATED to <newco> ...` format (never
   overwrite it, and it must contain `RE-ASSOCIATED` so the Moved-Companies list picks it up). Native
   `jobtitle` is written only when `title_conf >= 0.90` AND the new employer's domain resolved.
5. **Carry the phone in the same transaction.** `business_phone` predates the move so it is the old
   employer's line - overwrite with the new company's number, or CLEAR it if the company has none.
   Never touch `mobilephone`. Touch `phone` only when an exact-digit match proves it belongs to a
   different company. (`scripts/phoneaudit.py` -> `fixphones.py` -> `verifyphone.py`.)
6. Email ladder (`patmail2.py`, the 14-format universal set + nicknames): rung 0 existing bounce
   data outranks the verifier; rung 1 sweep hs_additional_emails/email_2/work_email/linkedin__email
   and the LinkedIn contact_info block (a first-party address beats a derived one); rung 2 learn the
   domain format from an in-portal colleague; rung 3 construct + NeverBounce (valid=write,
   catchall=write+flag, unknown=write only on 2+ agreeing samples & flag, invalid=never). Hard rule:
   domain must be the confirmed employer's (tier-1 alias = same ZoomInfo id; tier-2 parent/division =
   valid + note). File any prior address to `previous__email` (never clobber) and
   `previous__company_domain_name` (URL type - prefix https://). To clear a primary email: empty
   `hs_additional_emails` first, THEN `email` (two writes, in that order).

## Sales Navigator: find the movers instead of re-reading everyone
Unipile's `POST /api/v1/linkedin/search` exposes Sales Navigator's native filters under
`{"api":"sales_navigator","category":"people",...}` — verified against the endpoint schema, not
assumed. The one that changes the method is **`changed_jobs: true`** ("CHANGED JOBS"), alongside
`current_company`, `past_company`, `company_headcount` and `seniority`.

**Why this matters more than any speed gain.** The default method reads every contact to discover
the ~1-in-4 who moved: on the completed list, ~1,900 profile reads to find ~450 movers. Querying
`changed_jobs: true` scoped to the ICP companies surfaces the movers *directly*, so the expensive
read is spent only on records where something actually changed.

**How to use it without weakening the evidence standard** — this is a TARGETING tool, not an
evidence tool:
- A `changed_jobs` hit is a **candidate**, never a verdict. It says LinkedIn thinks something
  changed; it does not say what, when, or that the profile is the right human. Still read the
  dated experience rows and still apply the wrong-linked-slug corroborator rule (~1 in 4).
- It cannot prove a negative. A contact NOT returned is not confirmed still-employed — the filter
  is LinkedIn's own signal with unknown recall, and it says nothing about anyone who left without
  updating their profile. **The dated-row re-read stays the backstop**, just at a longer interval.
- So: `changed_jobs` sets the daily working queue; `STALE_DAYS` still forces a full re-read
  eventually. Do not let the cheap query replace the expensive one — let it re-order it.
- Sales Navigator runs on the same authorized accounts as everything else. Shawn's two account_ids
  only, and it consumes the same LinkedIn rate budget as `qbs-linkedin-daily`.

## ZoomInfo: corroborator, never overrider
ZoomInfo (`mcp__ZoomInfo__enrich_companies` / `enrich_contacts`) is the second source that makes
`sources: 2` honest. It never outranks dated LinkedIn history.
- **Companies** (`enrich_companies`): accept a domain ONLY on `matchStatus: FULL_MATCH` **plus an
  independent corroborator** — the returned city/state matching the person's LinkedIn location, or the
  industry matching the role. On 3675 this corroborated 6 of 6 destination domains (each ZoomInfo city/state
  matched the person's own LinkedIn location) and it is also what separates two real companies that share a
  name: an energy-software firm and a crypto exchange both trade as "Kraken", and only the industry +
  headquarters check picks the right one. Request `isDefunct`/`companyStatus` and never associate anyone to a
  defunct company. `NO_MATCH` on a small private brand is normal -> leave the domain UNRESOLVED and match by
  name; never invent a domain.
- **Contacts** (`enrich_contacts`): require `matchStatus: FULL_MATCH` AND `contactAccuracyScore >= 85`.
  `COMPANY_ONLY_MATCH` means it matched the COMPANY, not the PERSON — accuracy comes back `0.0` and you
  write NOTHING from it (this is exactly how a wrong number reaches a rep). Prefer `validDate` /
  `positionStartDate` as corroboration: on 3675 a mover's ZoomInfo position-start month matched the LinkedIn
  move month exactly, which is what earns `sources: 2`.
- **DNC is a hard stop, not a preference.** Always request `directPhoneDoNotCall` and `mobilePhoneDoNotCall`.
  `true` -> the number is NEVER written and the evidence must say so. On 3675 a confirmed mover's ONLY
  ZoomInfo number was a DNC-flagged mobile; writing it would have handed a rep a number they are not
  permitted to dial.
- Where ZoomInfo and LinkedIn AGREE, record `sources: 2`. Where they DISAGREE, LinkedIn's dated history wins
  and the record goes to the HUMAN queue — never split the difference.
- Credits are consumed per company/contact (free for a year after first enrichment). Batch up to 10 per call
  and keep enrichment inside the per-run ceiling.

## Guardrails - halt and report, do not push through
Four of these are now **enforced in code** (the model cannot hold running totals across context
boundaries, so prose guardrails in an autonomous run are decoration):
- Any non-2xx from HubSpot -> `sys.exit(2)` in queue.py / writeverdicts.py / movepipe.py. **ENFORCED.**
  An auth failure otherwise reads as "no data": zero members, zero unverified — which satisfies the
  stop condition exactly, so one expired token could report a dirty list as clean.
- A membership walk returning zero members -> refuse to run or to write the intake snapshot. **ENFORCED.**
- `no` share >60% or <5%, unreadable >20%, or `no_profile` >35%, computed over the accumulated
  verdict log once it passes 50 -> `sys.exit(3)`. **ENFORCED** in writeverdicts.py.
  Set `MODE=refresh` on a refresh pass: it drops the `no`-share FLOOR only. A refresh deliberately
  selects records confirmed before, so most re-confirm and a near-zero `no` share is correct
  behaviour, not a rubber-stamping judge. The ceilings still apply in both modes — they detect the
  instrument failing, and the mode does not excuse that.
- Read-back that does not match the requested verdict -> printed per id, `sys.exit(1)`, and the
  unconfirmed ids are **not** written to the verdict log. **ENFORCED.**
- 5 consecutive identity failures (an account/ban problem) -> stop. *Judgment; not enforced.*
- Live membership drifts >10% mid-run -> re-snapshot and re-confirm.
- Per-run ceilings (halt if exceeded): companies created, associations deleted, emails cleared,
  phones cleared, personas changed (default 0), NeverBounce/ZoomInfo credits. *Not enforced in code —
  the mover log records `unassoc_ids` and `prev_company` per contact so the damage is at least
  reconstructible; a ceiling check is still owed.*

## Never touch
`mobilephone`; `jobtitle` **below the 0.90 confidence gate** (3 competing writers, ~38% oscillation - `ai__job_title` is always the trustworthy copy, and the prior native value is preserved in the evidence);
`hs_persona` without approval; `hs_lead_status` on a `yes`; a populated `previous__email`; any
contact outside the intake snapshot; `email`/`phone` on a non-mover you have not PROVEN wrong
(non-mover phone conflicts are flag-only). Do not suppress the lead-status workflow - it is by design
(fresh info -> back to prospect); re-READ status after an email write rather than re-asserting it.

## Human queue (surface, never auto-decide)
Ambiguous company match or destination; tier-2 alias; unprovable email; non-mover phone conflict;
any proposed persona change; any proposed email/phone blanking on a non-mover; departed/retired
before suppression. Emit each with the evidence needed to decide in seconds.

## Outputs
Per-list verdict log `li_verdicts_<id>.json`; `pending_movers_<id>.json`; and two dynamic lists
(`scripts/twolists.py`, `listb.py`): "Moved Companies" (`ai__reassociated_on` IS KNOWN, OR the
legacy evidence substring for movers written before that property existed) and
"No Primary Associated Company" (`number_of_associated_companies = 0`, includeObjectsWithNoValueSet).
A calling list is `ai__li_still_at_company = yes` AND `hs_lead_status = ConnectandSell Prospect`
AND IN_LIST <source> (add a dedicated exclusion marker property if you gate on one).

## Repeatability & live-list cadence (learned the hard way)
- **A dynamic calling list is never "done."** It keeps admitting new members from its own filter criteria. On list 3675, ~263 brand-new contacts appeared within hours of a full pass. Treat verification as a **standing cadence**, not a one-shot: the refresh must run often enough to stay ahead of intake (weekly for an active list; monthly is too slow if churn is high). Scope each refresh to members with **no `ai__li_still_at_company`** OR **`ai__contact_verified_date` older than 90 days**.
- **`unreadable` does NOT remove a contact from the calling list.** Only a `hs_lead_status` change does, and `unreadable` sets none — so locked/bogus/wrong-linked records keep getting dialed. Policy: after a human reviews the HUMAN queue, give the genuinely unusable ones (`no profile`, wrong-link you can't fix, bogus/placeholder) `Need Updated Info` so they leave the list; keep only real-but-locked profiles as dial-cautiously. Do not leave a large `unreadable` population silently dialable.
- **No LinkedIn URL = not LinkedIn-verifiable.** Members with an empty `hs_linkedin_url` (131 on 3675) can only be resolved by people-search or ZoomInfo; if neither confirms, they are `unreadable` + HUMAN, not silently "yes". Always run the people-search fallback before calling a no-URL member unverifiable.
- **The stored LinkedIn slug is often WRONG-LINKED (a different same-name person).** A very common failure mode, separate from "no URL" and "locked": the `hs_linkedin_url` resolves to a real profile, but it's a *different human* with the same name (on 3675: a record saying "CEO of an IT-finance firm" was linked to a same-name CEO of an unrelated consultancy; another "CEO, agri-science" was linked to a same-name hospitality CEO in a different state). **Trigger:** the linked profile's current company does not match the HubSpot company. **Rule:** do NOT trust a name-only match — run a people-search by `name + company` and accept a hit ONLY when an independent corroborator lines up (profile location = company HQ region, industry, or role). Corroborated → judge on that profile AND write the corrected slug back via `li_url` (both URL fields). No corroborator → `unreadable` + `Need Updated Info`, never guess. This is why "yes" needs a company match, not just an open profile.
- **HubSpot titles are frequently wrong even when employment is current** — several "President"/"CEO" records were actually Marketing/VP/Director on LinkedIn (one "President" had only ever been a Marketing Director at that company; one "President & CEO" had been VP Sales). Judge employment and persona from the **dated LinkedIn history, never the HubSpot title string**; capture the real title in `ai__job_title` so the correction is visible.
- **"CEO / role with no end date" after an acquisition is ambiguous, not automatically current.** Watch for the company logo/name having changed to an acquirer. If LinkedIn still shows the role active (`end: null`), judge `yes` but NOTE the acquisition in evidence so the rep knows who actually owns the line now.
- **Former-CEO-now-Board/Advisor is NOT a buyer.** A "Former CEO"/"Board Advisor"/"Board Member" who stepped out of the operating seat (one 3675 record had ended the CEO role a year earlier and held only a board-advisor seat) is still affiliated with the company but is no longer the decision-maker → `Not Decision Maker`, not `yes`.
- **Measure cleanliness honestly each run**: report members, and the split of verified-yes / unverified(no verdict) / unreadable-still-on-list / no-LinkedIn-URL / wrong-linked-slug — not just "coverage of the intake snapshot," which goes stale the moment new members arrive.
- **The list count WILL crater, and most of it is the process working.** Expect the owner to ask "why did my list drop?" Have the arithmetic ready before they ask: on 3675, 389 of 1,680 verdicts carried a lead status (216 No Longer with Company / 94 Not Decision Maker / 48 Need Updated Info / 31 Retired) and each one correctly ejects the contact. Report intended removals and unintended ones separately — never as one number.
- **Never diagnose a membership drop by assertion — run the attribution.** The procedure, in order: (1) pull current membership; (2) intersect with your verdict log to find verified-`yes` contacts that fell off; (3) read their `hs_lead_status`, phone fields, `number_of_associated_companies` — this rules the process in or out; (4) test them against EACH upstream `IN_LIST` gate separately; (5) only then look at the ASSOCIATION (company) filters. On 3675 this proved 487 verified-good CEOs fell off, and that **zero** of the 308 that failed the CEO gate had been touched by our pipeline — they fail `hs_persona = persona_1` (163 blank, 140 `persona_14`), a field this process is forbidden to write. Without the attribution that looks exactly like self-inflicted damage.
- **`hs_persona` is the silent ICP gate.** A calling list keyed on a persona value cannot see a contact whose persona is blank or wrong, no matter how cleanly verified they are. 163 contacts on 3675 are confirmed current CEOs with a blank persona — invisible to the CEO list. Surface this as a headline finding with counts; it is usually the single biggest recoverable pool on the list, and fixing it is a persona decision (human-approved), never a silent write.
- **Do not trust a membership count taken during recalculation.** After a few hundred property writes HubSpot re-evaluates dynamic lists asynchronously; list 3675 read 964, then 112, then 87, then 576 within one hour, all while `processingStatus` said COMPLETE. Take counts twice, several minutes apart, and report a settled number or explicitly label it as still moving.

- **A slug whose NAME doesn't match the contact's name is a wrong-link you can catch for free.** Before spending a read, compare the stored slug against the contact name: a record for one surname pointing at a slug built from a completely different surname is mis-linked on its face (on 3675 one such slug resolved to an automation engineer at a pharma company, nothing to do with the CRM employer). Same-name wrong-links still need the company check, but name-mismatch is a zero-cost pre-filter.
- **One person can have TWO LinkedIn profiles — distinct from two CRM contacts.** On 3675 a contact's stored slug showed an old employer while a second profile for the same name in the same city showed the CRM employer with a current dated role. Two different member ids, one human, one stale profile. This is NOT the unique-URL collision case (that means two CRM *contacts*). Rule: corroborate on company + city, judge on the profile with the dated current role, write that slug back, and flag the pair for human dedupe review - do not assume the stored one is authoritative just because it loaded.
- **Junk source records are a category, not a one-off.** Watch for: a placeholder name (a first name repeated as the surname), a self-declared title with no dated history ("Independent Business Owner" with `start: null`), several contacts sharing one company with identical vague titles, or an out-of-network profile with no connections. These pass an "is there a profile?" test and fail every evidence test. They are `unreadable` + `Need Updated Info`, and when several cluster on one company, say so in the report - the finding is about the SOURCE of the data, not the individual records. A rep once burned a call on exactly this.
- **Two companies can share a name — corroborate the COMPANY, not just the person.** The same-name trap that bites on people bites harder on employers, and it silently corrupts mover re-association. Seen: a `FULL_MATCH` on a destination company name returned a UK rail-adhesion business for a US software fund; a contact's CRM company (the legal name behind a labeling brand) matched an unrelated printing shop 2,000 miles away; another company name resolved to either an HR-services LLC or a risk-decisioning fintech with no way to tell which the record meant. **Rule:** a company name match needs its own independent corroborator — HQ city/state near the person's location, or the industry matching the person's career — exactly like a person match. Name matched + corroborator failed = reject the record, create the company from the LinkedIn evidence alone, and say so in the evidence string. Never let a `FULL_MATCH` badge substitute for the check.
- **Near-homograph company names are a live re-association hazard.** A mover's origin and destination companies differed by a single transposed letter and both sold into the same market — genuinely different firms. A single typo in `newco` silently attaches the contact to the wrong employer and the evidence string will read plausibly. When the origin and destination names are within a character or two of each other, state explicitly in the evidence that they are distinct companies.
- **Cross-check succession WITHIN the run, not just per contact.** Two contacts on list 3675 both read as CEO of the same company: one profile said "CEO since 9/2024, no end date", the other "CEO since 1/2026". Both are `yes` on their own dated history; together they prove one profile is stale. **Rule:** when two verified contacts claim the same top seat at the same company, keep both verdicts but write the conflict into the older one's evidence so the rep confirms before opening with the title. A per-contact loop will never catch this — scan the run's `yes` set for duplicate company+C-level pairs before the final report.
- **An explicit "Retired" headline overrides an un-ended role row.** Four contacts this run had an open-ended (`end: null`) executive row and a headline reading "Retired" / "Relax, Refresh, Recharge…Retired" / "Retired <Market> President at <company>". Going by dated history alone keeps all four on the dial list. **Rule:** a first-person "Retired" headline is stronger evidence than a row the person simply never closed out → `Retired - Remove from All Lists`, and say in the evidence that the row was left open. Corroborate where cheap (a people-search showing someone else now holds the title).
- **Promotion into the parent, holding company, or a sibling brand is still `yes`, not a mover.** Repeatedly seen: a distributor's president moved up to a regional presidency of the group that owns it; a hospital market president became regional president of the health system that owns it; an office-products SVP became president of a brand explicitly described as "an <parent> brand"; a title-insurance record's contact is chairman of the parent financial group. Re-associating these to the parent is defensible, but flagging them "No Longer with Company" throws away a warm relationship. **Rule:** before writing `no`, check whether the new employer OWNS or IS a brand of the CRM company. If so, judge `yes`, correct `ai__job_title` to the new scope, and note the parent/brand relationship in the evidence.
- **Spinoff and rebrand: the person is current, only the company NAME is stale.** An operating unit spun out of its parent (its own experience rows will say so — "spun off from <parent>, <date>"); a company trading under a new name with the old website still on the profile. **Rule:** `yes`, set `ai__job_title` to the current entity, and put the rename/spinoff in the `changed` clause so nobody re-verifies it next quarter. Do NOT queue these as movers — there is no new employer.
- **The HubSpot title often belongs to a DIFFERENT employer than the HubSpot company.** Distinct from "the title is simply wrong": the title is real, it just came from a side business or a prior firm. Seen: "Managing Partner" that described a one-person drone venture while the CRM company was a large reseller where the person was an account executive; "Independent Business Owner" that belonged to a side business, not the CRM employer; "President" carried over from a firm the person sold years earlier; "Co-Owner" from a pre-acquisition partnership. **Rule:** when the CRM title doesn't match the current row, scan the WHOLE history for where that title actually came from — it usually names another row exactly, and that identifies the record as mis-titled rather than the person as mis-employed.
- **Division / regional president is not company president — capture the scope.** "President, Consulting Division", "President - West Division", "President - Alabama", "Regional CEO, <function>", "President, <segment>", "CEO, Property & Casualty". All are genuine `yes` verdicts and genuine buyers, but a rep who opens with "as President of <company>" is wrong on the first sentence. Always write the qualified scope into `ai__job_title`.
- **University / student-organization titles are junk records, and they cluster.** "SBA President" (Student Bar Association), "President, <subject> Society", "Director, <named award> Program" — all at one university, all captured as though they were company executives. One had already graduated into a law firm. The title alone is dispositive: no buying authority under any reading. `Not Decision Maker`, and report them as a SOURCE problem (recommend deletion from calling lists), not as three unlucky individuals.
- **Verdict-log IDs go stale.** A contact stamped earlier in the run can be deleted or merged before the final report (1 of 1,069 on this run no longer resolved). Read-backs will silently return fewer records than you asked for — compare the counts and mention the gap rather than reporting the log length as if it were live membership.

- **Persona remediation is a proposal workflow, and it belongs at the end of a run.** Because `hs_persona` is often the real ICP gate and this process must not write it, the deliverable is an evidence-backed candidate list: contacts you verified `yes` whose `ai__job_title` shows a C-level/owner title but whose persona is blank or wrong. Emit `persona1_candidates.json` (id, current persona, LinkedIn-verified title) and hand it over. Exclude former-CEO/board-advisor titles - they are affiliation, not authority. Never apply it silently; a persona write redefines list membership.

## Running unattended (Routines)
See `ROUTINE.md`. The judgment in this skill is identical whether a human is watching or not —
what changes is that **nobody is there to answer a question**, so the bar for "queue it" drops to
zero. Anything this skill says to surface, a routine surfaces and does NOT decide: ambiguous
destination company, unprovable email, persona proposal, succession conflict, duplicate pair,
division-scope uncertainty. An unattended run that decided a close call correctly and an
unattended run that decided one incorrectly look identical in the report; a queued one does not.

Two properties of an unattended run to design against:
- **It cannot be asked a follow-up.** Report the number behind every guardrail, not "guardrails
  passed", so the run is auditable after the fact by someone who was not there.
- **The judging is not deterministic** even though the scripts are. Two runs over the same records
  can differ at the margins. That is why every guardrail that matters lives in code with an exit
  code rather than in prose — prose is advice to the judge, an exit code is not.

## Non-goals
Does not write `hs_persona`; does not write native `jobtitle` below `title_conf` 0.90 (`ai__job_title` is always written); does not blank what it did not prove wrong; does not
create/edit lists as part of a verdict run; does not verify a phone actually dials (the largest
open gap - flagged, not solved).
