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

   Halt on a clone failure and report the exact git error. Use `$REPO` in every path that follows.

0b. **Confirm a LinkedIn transport before doing anything else.**

   ```
   UNIPILE_RELAY_TOKEN=... python3 $REPO/contact-verification/scripts/unipile.py selftest
   ```

   Exit 0 means a path returned **dated** experience rows — the only thing that makes a verdict
   possible. Exit 2 is no reachable path; exit 3 is reachable but returned nothing usable.

   The relay is tried first and is the path that works unattended. If it fails, the MCP connector
   is the fallback **when one exists** (interactive sessions only — `ToolSearch` for
   `select:mcp__Unipile__execute-request`). **Halt only if both fail, and say which failed and
   how.** Never write `unreadable` verdicts to represent an outage: an outage recorded as verdicts
   is a durable lie about the data that survives long after the outage ends; a halt is not.

1. `TOKEN=... python3 $REPO/contact-verification/scripts/preflight.py <listId>` — **stop the run on
   any non-zero exit and report the reason.** Do not continue and do not "try anyway".
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
