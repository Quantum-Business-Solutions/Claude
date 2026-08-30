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
2. **Unipile self-test — try BOTH transports before halting.** They fail independently:
   - **MCP connector** — routes via Anthropic's `mcp-proxy`, so it ignores the egress firewall.
     Currently the only path measured working from a cloud session. It also drops and reconnects.
   - **REST** — `python3 scripts/unipile.py selftest`. Measured from a cloud session: the agent
     proxy establishes the CONNECT tunnel and returns 200, the TLS handshake is then reset, and a
     direct socket times out on the tenant's non-standard port while 443 is open on the same IP.
     Outbound egress here reaches standard ports only, and no 443 host serves the tenant API. This
     is a property of the ENVIRONMENT, not of the DSN or the key — `unipile.py probe` shows it.

   Use only Shawn's accounts (`S6ua4SfUT4SMRFZFOmyUzQ` / `7lBoyXuETqKdiJYLj5HBGA`); every other
   account on that tenant is a client identity. **HALT only if both transports fail, and name
   which one did.** An outage written as several hundred `unreadable` verdicts is a lie about the
   data, not a finding about the contacts — and the verdict is durable while the outage is not.
3. `TOKEN=... python3 scripts/listanatomy.py <listId>` — map the gate chain. It exits 3 on a
   non-contact or non-dynamic list, and warns when the list gates on properties this process
   writes (the run changes membership underneath itself).
4. `TOKEN=... STALE_DAYS=90 python3 scripts/queue.py <listId>` — work queue + intake snapshot.
   Three intervals, not one: `STALE_DAYS` (90) for a confirmed verdict, `RETRY_DAYS` (14) for a
   transient `unreadable`, `NOPROFILE_DAYS` (180) for `no_profile`. Records come back in a strict
   **work order** — band 0 never verified, 1 verdict stale, 2 unreadable retry, 3 no_profile
   recheck — oldest first inside each band. **Work them in that order.** It is the anti-starvation
   guarantee: nothing is skipped forever, and a band that never drains is a capacity fact the
   printed depths make visible rather than something hidden by interleaving.

4b. **Choose MODE from what queue.py reports; do not assume.** `MODE=refresh` drops the `no`-share
   FLOOR, which is the only automated check against a judge rubber-stamping `yes`. That is correct
   when the queue is mostly stale re-confirmations and wrong when it is mostly never-verified
   records — a list can be a first pass wearing a refresh label. The ceilings apply in both modes.
   Set it on every writeverdicts call: `MODE=first_pass|refresh python3 scripts/writeverdicts.py …`
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
- write `unreadable` when the real answer is `no_profile`. Verdicts are yes / no / unreadable /
  no_profile; the split is what lets the queue retry a transient failure in 14 days and a person
  with no profile in 180 instead of re-reading them forever at full cost
- decide anything a human should decide. Pass `issue` + `issue_note` on the batch item — it writes
  `ai__verification_issue`, `_note` and `_on`, which live in HubSpot and survive this container.
  A judgement call queued only to a session scratch file is one nobody will ever see
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
