# Contact List Verification

Turns a purchased or inherited HubSpot contact list into one a rep can dial without
apologising. Reads every contact against dated LinkedIn employment history, records what
was found and how it is known, and routes each person to a channel: dial them,
re-target them at their new employer, or leave them alone.

## Start here

| Document | What it is for |
|---|---|
| `skill/qbs-list-verification/SKILL.md` | **The authority.** Process, verdict vocabulary, guardrails, field conventions, judgment rules. |
| `RUNBOOK.md` | **The mechanics.** Copy-paste commands, list-agnostic — substitute `<LIST>` and run. |
| `docs/FIELD-NOTES.md` | Raw working notes, including sections that correct earlier mistakes. Densest source of gotchas. |
| `docs/verification-process.html` | Flow chart and stage specs. |
| `docs/evidence-ladder.html` | Source-yield measurements and the case histories behind the rules. |

## Run it

```
/qbs-list-verification <listId>
```

One command. The skill runs Phase 0, loops the batches, runs the mover pipeline, refreshes
the output lists, and reports — stopping only for the judgment calls it is required to
escalate. See **Autonomous end-to-end run** in SKILL.md for the exact contract and the
stop conditions.

## Credentials

Nothing is hardcoded. Every script reads from the environment:

```bash
export TOKEN=<hubspot private app token>     # see the qbs-hubspot-private-app skill
export NB=<neverbounce api key>              # email verification rung only
```

LinkedIn reads go through the Unipile MCP tool (Shawn's two authorized accounts only — the
other identities on that tenant are client accounts). ZoomInfo enrichment goes through the
ZoomInfo MCP tools as a *corroborator*, never as an override.

## Scripts

Thirteen scripts. Everything else is judgment, and judgment lives in the skill.

| Script | Phase | What it does |
|---|---|---|
| `preflight.py <listId>` | Phase 0 | **Run before anything, mandatory unattended.** Refuses a run it cannot prove safe: the checkout predates the QA fixes (exit 3), TOKEN missing or HubSpot unreachable (exit 2), the list empty / not a contact list / not DYNAMIC (exit 2), a written property missing, or `hs_lead_status` / `ai__li_still_at_company` missing a value the process writes (exit 3). Every one of those used to present as a confident "nothing needed refreshing". |
| `unipile.py probe\|selftest\|profile` | Phase 0 | Reaches LinkedIn by whatever transport works. Probes each candidate endpoint, separating TCP reachability from auth so a firewall is never mistaken for a bad key. **Measured: outbound egress from a cloud session reaches port 443 only, and no 443 host serves the tenant API — so the MCP connector is the only LinkedIn path a routine has.** Halt only when BOTH transports fail, and say which. |
| `listanatomy.py <listId>` | Phase 0 | **Run first.** Maps the full gate chain — recurses every `IN_LIST` upstream gate and every company-level `ASSOCIATION` filter, then lists every property that can eject a contact. Warns when the list gates on a field this process must not write. |
| `queue.py <listId> [N]` | batch loop | Next N unverified contacts + their LinkedIn identifier; snapshots intake. |
| `writeverdicts.py <listId> <batch.json>` | batch loop | Writes a batch and enforces the rules no caller may bypass: refuses a lead status on a `yes`, allows only the four valid literals, writes native `jobtitle` only at `title_conf` ≥ 0.90 (fails closed, read back), stamps evidence in the standard format, chunks at 100, diffs requested-vs-returned, reads back to confirm, logs per-list, queues movers. |
| `movepipe.py <listId> <movers.json>` | movers | Find-or-create company, swap associations (both type IDs), reconcile the flag, carry the phone, stamp `RE-ASSOCIATED` evidence. |
| `phoneaudit.py` → `fixphones.py` → `verifyphone.py` | phone | Find numbers that belong to a former employer, correct or clear them, prove the fix applied. |
| `patmail2.py` | email | Universal format set (14 formats) plus nickname short forms, ordered by real-world prevalence. |
| `twolists.py`, `listb.py` | outputs | Create the three output lists — Moved Companies, No Primary Associated Company, and the AI Verification Issues review queue (carries the hard-won HubSpot list-filter shapes, and probes a filter shape rather than asserting one). |
| `backfill.py <listId> [--apply]` | migration | Dry-run by default. Brings records written by older code up to the current standard **without inventing anything**: derives `ai__reassociated_on` from the date already in the evidence, and clears `ai__contact_verified_date` where the verdict is `unreadable`/`no_profile`. Refuses to derive tenure or role-change, which would need a re-read. |

## What is deliberately not in this repo

Contact-level run data — verdict logs, email and phone write logs, audit output, intake
snapshots. Those files carry names, employers and phone numbers for real people, and a git
repository is the wrong place for them. They stay in the working directory of the session
that produced them (`.gitignore` enforces this). The code and the process are what belong here.

## Corrections applied after QA audits

Claims in earlier versions of these docs that were wrong and are now fixed:

- "every one read on LinkedIn" — on list 5243, 491 of 662 were read; 171 left the list first
- "none of the 32 mismatched phones belonged to another company" — 9 of 32 do. The check that
  said otherwise used a digits-only search that cannot match a parenthesised stored number, so
  it returned nothing for every input and the nothing was read as an answer
- "same vendor company id means same company" — sound for domain aliases within one record, but
  it cannot detect a rebrand or acquisition; the vendor keeps predecessors as separate records
- this README previously listed ~29 one-off scripts that were deleted in the PII cleanup

The method rule that would have caught most of them: **self-test every query against a case
whose answer you already know before trusting a null result.**

## Open gaps

- **No phone number has been dial-tested.** The process corrects and clears numbers on
  evidence, but never proves one rings the right desk. Largest open gap.
- **Duplicate contacts** are detected (unique-URL collision) and queued, never merged.
- **`hs_persona`** is frequently the real ICP gate and this process is forbidden to write it,
  so blank-persona contacts stay invisible until a human decides. Evidence-backed proposals
  are produced; applying them is a human call.
- **Succession conflicts are caught by eye, not by code.** Two contacts on the same list can
  both verify as the current CEO of one company (each profile is internally consistent; one is
  simply stale). Nothing in the batch loop cross-checks the run's `yes` set for duplicate
  company + C-level pairs — it took a human noticing. Worth a script.
- **Company-name collisions rely on judgment.** A destination company match can be a
  `FULL_MATCH` on the name and still be the wrong business — the corroborator rule is written
  down and followed, but nothing enforces it mechanically.
