# Running this process as a Routine (unattended)

A Routine fires into a **fresh cloud session** that **clones the default branch** and runs with
**no permission prompts** and nobody watching. That changes what the process must do — not what
it decides, but how loudly it fails.

## The rule that matters

**An unattended run must never report success it cannot prove.** Every failure mode this process
has ever had presented as a confident clean bill of health:

| Failure | How it looked before | Now caught by |
|---|---|---|
| Checkout predates the QA fixes | "unverified 0 — nothing needed refreshing" | `preflight.py` code-version guard, exit 3 |
| Token missing or expired | reads return nothing = the stop condition | `preflight.py` auth probe, exit 2 |
| List empty or deleted | zero members = "fully verified" | `preflight.py` + `queue.py`, exit 2 |
| A written property renamed | writes land nowhere, run reports applied | `preflight.py` schema check, exit 3 |
| `hs_lead_status` lost a literal | movers cannot be ejected; 400s mid-run | `preflight.py` vocabulary check, exit 3 |
| LinkedIn unreadable | every contact scores `unreadable` | Unipile self-test, below (model step) |

## Required order for any unattended run

1. `TOKEN=... python3 scripts/preflight.py <listId>` — **stop the run on any non-zero exit and
   report the reason.** Do not continue and do not "try anyway".
2. **Unipile self-test.** Read one profile known to have dated experience rows, using only
   Shawn's accounts (`S6ua4SfUT4SMRFZFOmyUzQ` / `7lBoyXuETqKdiJYLj5HBGA`). If it does not return
   dated rows, HALT — every contact would otherwise score `unreadable` and look like a finding.
3. `TOKEN=... python3 scripts/listanatomy.py <listId>` — map the gate chain. It exits 3 on a
   non-contact or non-dynamic list, and warns when the list gates on properties this process
   writes (the run changes membership underneath itself).
4. `TOKEN=... STALE_DAYS=90 python3 scripts/queue.py <listId>` — work queue + intake snapshot.
5. Batch loop per SKILL.md. `writeverdicts.py` exits 1 on read-back mismatch, 2 on HTTP failure,
   3 on a guardrail breach. **Any non-zero exit ends the run and gets reported.**
6. Movers, then output lists.

## Reporting contract

Post one summary whatever happens, and never round a failure up to a success:

- refreshed count, verdict mix, movers re-associated, phones/emails repaired
- **every guardrail evaluated, with its number** — not "guardrails passed"
- the human queue: what was surfaced and how many
- coverage against the intake snapshot, **and the snapshot-gap count** (`queue.py` prints it) —
  `unverified 0` is not proof the intake was covered, because our own `hs_lead_status` writes
  eject contacts from the list that gates on it
- if the run halted: which step, which exit code, and what it means. A halted run is a
  successful routine. A silent run is not.

## What a routine must NOT do unattended

- write `hs_persona` (redefines list membership — propose, never write)
- write native `jobtitle` below the `title_conf` 0.90 gate (the gate is enforced in code)
- write `hs_lead_status` on a `yes`
- guess `dm` on a mover, or pick `results[0]` from an ambiguous company search
- touch ZoomInfo do-not-call properties (out of scope)
- use any Unipile account other than Shawn's two

## Known limit: cross-run state does not survive

`li_verdicts_<id>.json`, `pending_movers_<id>.json`, `reassoc_<id>_log.json`, `mem_<id>.txt`,
`dedupe_review_<id>.json` are working-directory files, correctly gitignored (contact PII). A
routine's container is destroyed after the run, so **every fire starts with none of them**.

That is fine for a **whole-list pass**, which is self-contained: one fire = one complete pass.

It is NOT fine for an **incremental daily worker**, where it breaks three things:
- a mover queued at the end of a batch is lost, and the contact is already flagged, so
  `queue.py` never surfaces it again — silent permanent loss
- the running guardrails compute over the accumulated log with `if n>=50`; daily batches under
  50 mean the guardrails **never fire at all**
- the intake snapshot is rewritten every fire, so coverage and the snapshot gap reset daily

**The intake snapshot is per-directory, which makes coverage self-flattering.** `queue.py` writes
`mem_<id>.txt` into the CURRENT directory and only if it does not already exist. Run from a fresh
checkout and it writes a NEW snapshot equal to today's membership, so the "in intake snapshot but
no longer members" gap reads ~0 — a perfect coverage number that measures nothing. Measured on the
completed list: against the real Aug-19 snapshot (1,614 ids) the gap is **902**; against a
same-day snapshot it is 0. A routine gets a fresh container every fire, so it always gets the
flattering number unless the snapshot is stored outside the container.

A daily worker therefore requires the cross-run state to live outside the container — in HubSpot
itself (properties and lists), or a controlled external store. See the daily-worker design before
scheduling one.
