# Running this process as a Routine (unattended)

A Routine fires into a **fresh cloud session** with **no permission prompts** and nobody watching.
That changes what the process must do — not what it decides, but how loudly it fails.

Two things about that session are not what you would assume, and both were measured on
2026-08-30 after two fires of the 5243 routine completed in ~3 minutes and wrote nothing at all:

- **It does NOT clone the repository.** An interactive session carries `session_context.sources`;
  a routine-fired session's context has no `sources` at all, so `contact-verification/scripts/…`
  does not exist and every step referencing it fails at the first command. The routine prompt must
  therefore clone the code itself. The repository is public, so an unauthenticated
  `git clone --depth 1 --branch main` works with no credentials — verified.
- **It has NO MCP connector tools.** This is not a bug and not an outage; it is a property of how
  the Routine was created. `create_trigger` warns in plain text: *"this trigger stores no MCP
  connectors, so the sessions it fires will run without connector (`mcp__<server>__*`) tools."*
  Its `connectors` parameter is rejected outright for this organization, and the Routines UI on
  claude.ai lists only first-party connectors, not custom MCP servers like Unipile. So there is
  **no way to give a Routine the Unipile connector.**

**So LinkedIn is reached over plain HTTPS instead, never a connector.** `unipile.py` runs a
version-tagged ladder and reports which rung carried the run:

1. **Unipile v2** — `https://api.unipile.com/v2/{acc}/users/{slug}?with_sections=linkedin_experience`.
   Port 443, no relay, no connector. This is the primary path and the reason a Routine can work at
   all. Needs `UNIPILE_V2_KEY`. It also returns LinkedIn **company IDs**, which resolve a mover's
   destination far better than a company-name string.
2. **Unipile v1 via the relay** — kept as a fallback while v2 is in beta. Needs `UNIPILE_API_KEY`
   plus `UNIPILE_RELAY_TOKEN`.

**Pace to the published budget, not a guess.** Unipile allows **100 requests per ~16-minute
window** (`x-ratelimit-limit` / `x-ratelimit-remaining` / `retry-after` on every response).
`unipile.py` reads those headers and spreads the remaining budget across the remaining window, so
the correct sustained rate is ~9.6s per profile — roughly **375/hour**. Size a run from that: a
250-contact pass is about 40 minutes of reads. Do NOT hard-code a sleep; 3.5s burns the whole
budget in six minutes and then stalls.

Company-based search does not help this data: measured on list 5243, 815 unverified contacts span
**753 distinct companies**, 711 of them with a single contact. One profile read per contact is the
real shape of the work.

**Always request the FULL experience section, never `experience_preview`.** Measured 2026-08-30 —
Sandberg 5 rows vs 15, Weiner 7 vs 24 — and a CRM company falling outside a truncated preview reads
as departed, ejecting a real contact as "No Longer with Company".

**The relay** exists because Unipile serves *v1* on port 16072 while cloud egress reaches 443 only.
A Supabase Edge Function on 443 forwards to it. v2 needs no such thing; the relay is now fallback
infrastructure only, and can be deleted with v1. Source: `contact-verification/relay/`.

    https://ladhdgwedwynmdmeeena.supabase.co/functions/v1/unipile-relay

It stores **no credential**: the caller forwards its own `X-API-KEY`. Verified guards, tested live:
`POST`/`DELETE` → 405 `read_only` (so it can read profiles and can never send an invite, DM or
InMail) · a non-allowlisted `account_id` → 403 `account_not_allowed` (the five client identities on
this tenant are blocked in the relay, not merely by convention) · no key → 400 `missing_api_key`.
Supabase JWT verification is left **on**, so `UNIPILE_RELAY_TOKEN` must be set on the environment —
it is deliberately not committed, because this repository is public.

HubSpot-only work never had this problem: `QBS_HUBSPOT_TOKEN` is set on the environment and
`api.hubapi.com` is on 443.

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
| No repository in the fired session | run ends in minutes having written nothing | step 0 clone, below |
| No MCP connector in the fired session | same silent 3-minute no-op | step 0b transport check, below |
| A `no` verdict with nowhere to go | contact ejected, destination lost, never resurfaces | `writeverdicts.py` refuses it, exit-code-free refusal keeps them queued |
| Ejection workflow detached the old employer | `previous employer record unknown` | `movepipe.py` reads `associatedcompanyid` history |
| Mover's new employer is an existing account | an active client relabelled a cold prospect | `movepipe.dest_status()` + `destination_is_account` |
| A LinkedIn URL pointing at a different person | a confident verdict about the wrong human | `writeverdicts.identity_doubt()` |

## Required order for any unattended run

0. **Get the code.** Never assume a checkout exists:

   ```
   if [ -d /home/user/Claude/contact-verification ]; then REPO=/home/user/Claude
   else cd /tmp && rm -rf qbsrepo \
        && git clone --depth 1 --branch main \
             https://github.com/Quantum-Business-Solutions/Claude qbsrepo \
        && REPO=/tmp/qbsrepo
   fi
   ```

   **This clone command deliberately still points at THIS repo, even though
   `Quantum-Business-Solutions/qbs-contact-verification` is now the home for this process.**

   The code was extracted to its own repository because `main` here is whatever session merged
   last: on 2026-09-01 the routine cloned a `main` three days stale, found no reachable transport,
   and correctly halted having written nothing. A workspace is a bad release channel.

   **The extraction is not finished, for one measured reason: the new repository is PRIVATE and a
   routine-fired session has no credential for it.** A clone from an interactive session succeeds
   and proves nothing — git read access there is served by the session's git proxy for repos
   attached to that session. A fresh session spawned into the same environment
   (`env_01TxD1DB6PTzpB6nQpEiFy88`), which is what a Routine gets, returned:

   ```
   git clone https://github.com/Quantum-Business-Solutions/qbs-contact-verification
   -> exit 128: could not read Username for 'https://github.com': no credentials for HTTPS
   ```

   Until one of these is done, the trigger clones THIS repo and **every change must land in both**:

   1. **Make the new repository public** (recommended). Nothing contact-level is tracked in it and
      its `.gitignore` files cover every filename the scripts produce, so an unauthenticated clone
      would then work exactly as this repo's does today.
   2. Attach the new repository to the environment so fired sessions inherit a credential. Keeps it
      private, and needs a real test fire to confirm — environment sources propagating to
      trigger-fired sessions is unverified.

   Do **not** paper over it with a fallback that silently clones the old repo on failure. That is
   the 2026-09-01 staleness bug with extra steps: the run would succeed, against the wrong code,
   and say nothing. Halt on a clone failure and report the exact git error.

   Halt on a clone failure and report the exact git error. Use `$REPO` in every path that follows.

0b. **The transport check is no longer a separate step — `preflight.py` runs it.**

   It shells out to `unipile.py selftest` and exits 2 when no rung returns dated rows. It used to
   be a sentence at the end of preflight telling the model to run the self-test itself, and
   preflight exited 0 either way — so a routine whose key had rotated passed, reached the batch
   loop, failed every read, and recorded an environment misconfiguration as findings about people.
   `SKIP_TRANSPORT=1` exists for schema-only checks and warns loudly.

   If you need to see it directly: `python3 $REPO/contact-verification/scripts/unipile.py selftest`
   (exit 0 = a rung returned dated rows · 2 = no reachable path · 3 = reachable but nothing usable),
   and `unipile.py probe` for the per-endpoint reason. Never write `unreadable` verdicts to
   represent an outage — that is a durable lie about the data which outlives the outage; a halt is
   not.

1. `TOKEN=... python3 $REPO/contact-verification/scripts/preflight.py <listId>` — **stop the run on
   any non-zero exit and report the reason.** Do not continue and do not "try anyway".
2. `TOKEN=... python3 scripts/listanatomy.py <listId>` — map the gate chain. It exits 3 on a
   non-contact or non-dynamic list, and warns when the list gates on properties this process
   writes (the run changes membership underneath itself). It exits 0 with an EMPTY map on an API
   failure, so a map naming no gates on a list you know is gated is a FAILURE, not a finding.
3. `TOKEN=... STALE_DAYS=90 python3 scripts/queue.py <listId>` — work queue + intake snapshot.
   Three intervals, not one: `STALE_DAYS` (90) for a confirmed verdict, `RETRY_DAYS` (14) for a
   transient `unreadable`, `NOPROFILE_DAYS` (180) for `no_profile`. Records come back in a strict
   **work order** — band 0 never verified, 1 verdict stale, 2 unreadable retry, 3 no_profile
   recheck — oldest first inside each band. **Work them in that order.** It is the anti-starvation
   guarantee: nothing is skipped forever, and a band that never drains is a capacity fact the
   printed depths make visible rather than something hidden by interleaving.

3b. **Choose MODE from what queue.py reports; do not assume.** `MODE=refresh` drops the `no`-share
   FLOOR, which is the only automated check against a judge rubber-stamping `yes`. That is correct
   when the queue is mostly stale re-confirmations and wrong when it is mostly never-verified
   records — a list can be a first pass wearing a refresh label. The ceilings apply in both modes.
   Set it on every writeverdicts call: `MODE=first_pass|refresh python3 scripts/writeverdicts.py …`
4. Batch loop per SKILL.md. `writeverdicts.py` exits 1 on read-back mismatch, 2 on HTTP failure,
   3 on a guardrail breach. **Any non-zero exit ends the run and gets reported.**
5. **Movers — this step is not optional, and a run that skips it leaves people stranded.**
   `movepipe.py <listId> --from-hubspot` rebuilds the queue from `ai__pending_mover_to`, so it
   works in a fresh container that never saw the verdict batch. Run it in the SAME fire as the
   verdicts. What it now does, and why each part exists:

   - **Sets the lead status away from the ejected value first.** A portal workflow enrolls on
     `hs_lead_status = No Longer with Company` and, ~20 seconds later, removes the company
     association and blanks native `jobtitle`. Re-associating while that status is still on the
     record races the workflow.
   - **Recovers the previous employer from property history** when the live association is already
     gone (`propertiesWithHistory=associatedcompanyid`). This is the normal case, not the edge case.
   - **Checks what the destination already is** before writing `ConnectandSell Prospect`:
     a current client, former client, open deal or upcoming meeting gets that company's real status
     instead, plus a `destination_is_account` flag for a human.
   - **Writes native `jobtitle`** at `title_conf >= 0.95` with a resolved employer domain, and
     reads it back.
   - **Sets `validated__linkedin_or_manually` = `Yes`**, because the record has now been checked
     against a dated source and corrected.

   Then output lists.

6. **`selfqa.py` — last, always, whatever happened.**

   ```
   TOKEN=... python3 $REPO/contact-verification/scripts/selfqa.py --days 14
   ```

   It recomputes today's numbers from HubSpot and sets them beside the trailing 14-day baseline:
   verdict mix drift, absolute ceilings on `unreadable`/`no_profile`, movers queued but never
   re-associated, `no` verdicts with nowhere to go, records awaiting a human, and months-to-finish
   at today's pace. Exit 1 means something is out of band and belongs in the run summary; it is
   deliberately NOT a halt, because turning a report into an outage teaches everyone to skip it.

   Two properties of this step matter more than the metrics:

   - **It grades the run from the CRM, not from the run's own log.** A pass that reads its own
     output cannot detect that its output is wrong. The 93.4% `unreadable` baseline it reported on
     first use is the Aug 30–31 transport outage, sitting in the data as findings about people.
   - **It proposes; it never changes anything.** If a run concludes the process should work
     differently, that goes in the summary as a proposal for a human. A scheduled job permitted to
     edit its own rules, thresholds or prompts can drift a long way while reporting that all is
     well, and it is unrecoverable because the yardstick moved with it. **Never grant the routine
     write access to its own definition of success.**

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
- write native `jobtitle` below the `title_conf` 0.95 gate (the gate is enforced in code)
- bank a `no` verdict with no destination and no `no_destination` reason. `writeverdicts.py`
  refuses it. 446 contacts across the portal are in exactly that state from earlier passes: read,
  confirmed departed, and left pointing at nothing. A refused record stays in the queue; a banked
  one never comes back
- write `ConnectandSell Prospect` on a mover whose destination is a current client, former client,
  open opportunity or has a meeting booked (`dest_status()` enforces this)
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
