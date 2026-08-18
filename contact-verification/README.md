# Contact List Verification

Turns a purchased or inherited HubSpot contact list into one a rep can dial without
apologising. Reads every contact against dated LinkedIn employment history, records what
was found and how it is known, and routes each person to a channel: dial them,
re-target them at their new employer, or leave them alone.

Built from the full pass on QBS list 5243 — 662 contacts in, every one read, 340 surviving.

## Start here

| Document | What it is for |
|---|---|
| `docs/verification-process.html` | **The process.** End-to-end flow chart, stage specs, decision rules, failure modes. Read this first. |
| `docs/evidence-ladder.html` | Companion. Source-yield measurements and the case histories that produced the rules. |
| `docs/FIELD-NOTES.md` | Raw working notes taken as the work happened, including sections that correct earlier mistakes. Densest source of gotchas. |

## Credentials

Nothing is hardcoded. Every script reads from the environment:

```bash
export TOKEN=<hubspot private app token>     # 31 of 36 scripts
export NB=<neverbounce api key>              # email verification only
```

LinkedIn reads go through the Unipile MCP tool, not these scripts.

## Scripts, by phase

Not a pipeline yet — these are the steps as they were actually executed, in order of use.
`docs/verification-process.html` explains what each phase is doing and why.

**Queue and verdicts**
- `nextbatch.py` — print the next N unverified contacts from the queue
- `wr.py` — batch-write verdicts, evidence, verified date, source count

**Movers (re-association)**
- `movepipe.py` — the mover pipeline: verify domain, find/create company, delete stale
  associations, PUT new with **both** association type IDs, reconcile the flag
- `stampmovers.py` — ensure every re-associated contact carries the marker the lists key on
- `sweepaddl.py` — look for a current-employer address already sitting in a secondary field

**Email resolution**
- `patmail.py` — first-generation format engine (learned patterns only)
- `patmail2.py` — **use this one.** Full universal format set (14 formats) plus nickname
  short forms, ordered by real-world prevalence
- `runpat.py`, `runpat2.py`, `run14.py` — resolution runs (background + thread pool)
- `wremail.py`, `residue.py`, `fix4.py` — write results, applying the hard domain rule
- `pastemail.py` — file a prior-employer address to `previous__email` and clear the live field

**Phone (do not skip — this is the channel reps actually use)**
- `phoneaudit.py` — find contacts whose business number is not their employer's
- `whosephone.py` — identify which company a number actually belongs to
- `fixphones.py` — correct or clear them, preserving what was replaced
- `verifyphone.py` — prove the fix applied
- `audit8260.py`, `id32.py` — check whether the problem extends beyond the movers

**Lists and reconciliation**
- `twolists.py`, `mklist3.py`, `listb.py` — create the output lists (includes the
  hard-won HubSpot list-filter shapes)
- `reconcile662.py` — account for every contact that left the source list, with the reason
- `why46.py`, `diag422.py`, `split.py`, `gate.py` — diagnose why verified contacts fall
  out of an ICP list
- `notmkt.py`, `chk7.py`, `unmark.py` — persona-exclusion marker audits and repairs
- `final2.py`, `lscheck.py`, `counts2.py`, `livestate.py` — verification and state reads

## What is deliberately not in this repo

Contact-level run data — verdict logs, email and phone write logs, audit output. Those
files carry names, email addresses and phone numbers for several hundred real people, and
a git repository is the wrong place for them. They stay in the working directory of the
session that produced them. The code and the process are what belong here.

## Known state at time of commit

- Zero contacts on the calling list carry a former employer's phone or email
- 70 movers re-associated, 56 holding a confirmed current-employer email
- Two contacts have no dialable number at all and correctly fell off the phone-gated list
- Still open: 27 company records created during the pass were never enriched for tech
  signals, so verified contacts sit outside the ICP as *unproven* rather than disqualified;
  one duplicate contact needs a human merge; **no phone number has been dial-tested**
