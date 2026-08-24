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

## Phase 0 - Preflight (no writes; abort on any failure)
1. Self-test every query type against a case whose answer you already know before trusting a null
   result (a digits-only phone search silently matches nothing — see FIELD-NOTES). If the self-test
   fails, STOP.
2. Read the list's REAL criteria: `GET /crm/v3/lists/{id}?includeFilters=true`. Confirm it is a
   contact list (objectTypeId 0-1) and note every gating property.
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
- **unreadable** = no profile, or a real profile with no dated history. Name what was tried.

## Fields this process writes (repeatable conventions)
- **Evidence format** (`ai__contact_evidence`): always `Verified - <date> - <evidence> - Changed: <what changed in HubSpot>`. writeverdicts.py builds this; the `Changed:` clause auto-summarises flag/lead-status/title/URL/mover unless you pass an explicit `changed`.
- **`ai__job_title`** (AI-owned title field): write the current LinkedIn-verified title here via the batch `title` field. This exists because the native `jobtitle` is fought over by 3 integrations (~38% oscillation) — NEVER write `jobtitle`; this field is the trustworthy display title.
- **`validated__linkedin_or_manually`** (select): set every verified record — `yes`->`Yes`, `no`+Retired->`Retired`, any other `no`/`unreadable`->`Needs Updated`. (`Delete` is human-only, for bogus records.)
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
3. DELETE stale associations, PUT new with BOTH `associationTypeId` 1 AND 279 (one alone leaves
   `associatedcompanyid` empty). `associatedcompanyid` is calculated and lags ~20s - re-read before
   concluding failure.
4. Reconcile flag to `yes`; set `company`; set `ai__job_title` to the new-company title and
   `validated__linkedin_or_manually` (`Yes` if a live decision-maker, else `Needs Updated`); append
   evidence in the `Verified - <date> - ... - Changed: RE-ASSOCIATED to <newco> ...` format (never
   overwrite it, and it must contain `RE-ASSOCIATED` so the Moved-Companies list picks it up). Never
   write native `jobtitle`.
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

## Guardrails - halt and report, do not push through
- Any 401/403 -> hard stop (an auth failure otherwise reads as "no data" and stamps live records).
- `no` share >~60% or <~5% over the first 50 verdicts (baseline ~36%); unreadable >~20% (baseline ~8%);
  5 consecutive identity failures (an account/ban problem) -> stop.
- Live membership drifts >10% mid-run -> re-snapshot and re-confirm.
- Per-run ceilings (halt if exceeded): companies created, associations deleted, emails cleared,
  phones cleared, personas changed (default 0), NeverBounce/ZoomInfo credits.

## Never touch
`mobilephone`; `jobtitle` (3 competing writers, ~38% oscillation - write the AI-owned `ai__job_title` instead, truth also in evidence);
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
(`scripts/twolists.py`, `listb.py`): "Moved Companies" (evidence CONTAINS RE-ASSOCIATED) and
"No Primary Associated Company" (`number_of_associated_companies = 0`, includeObjectsWithNoValueSet).
A calling list is `ai__li_still_at_company = yes` AND `hs_lead_status = ConnectandSell Prospect`
AND IN_LIST <source> (add a dedicated exclusion marker property if you gate on one).

## Repeatability & live-list cadence (learned the hard way)
- **A dynamic calling list is never "done."** It keeps admitting new members from its own filter criteria. On list 3675, ~263 brand-new contacts appeared within hours of a full pass. Treat verification as a **standing cadence**, not a one-shot: the refresh must run often enough to stay ahead of intake (weekly for an active list; monthly is too slow if churn is high). Scope each refresh to members with **no `ai__li_still_at_company`** OR **`ai__contact_verified_date` older than 90 days**.
- **`unreadable` does NOT remove a contact from the calling list.** Only a `hs_lead_status` change does, and `unreadable` sets none — so locked/bogus/wrong-linked records keep getting dialed. Policy: after a human reviews the HUMAN queue, give the genuinely unusable ones (`no profile`, wrong-link you can't fix, bogus/placeholder) `Need Updated Info` so they leave the list; keep only real-but-locked profiles as dial-cautiously. Do not leave a large `unreadable` population silently dialable.
- **No LinkedIn URL = not LinkedIn-verifiable.** Members with an empty `hs_linkedin_url` (131 on 3675) can only be resolved by people-search or ZoomInfo; if neither confirms, they are `unreadable` + HUMAN, not silently "yes". Always run the people-search fallback before calling a no-URL member unverifiable.
- **Measure cleanliness honestly each run**: report members, and the split of verified-yes / unverified(no verdict) / unreadable-still-on-list / no-LinkedIn-URL — not just "coverage of the intake snapshot," which goes stale the moment new members arrive.

## Non-goals
Does not write `hs_persona` or native `jobtitle` (writes the AI-owned `ai__job_title` instead); does not blank what it did not prove wrong; does not
create/edit lists as part of a verdict run; does not verify a phone actually dials (the largest
open gap - flagged, not solved).
