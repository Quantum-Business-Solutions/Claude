# Unattended run contract — QBS LinkedIn routines

This overrides habit. Read it before acting on any scheduled LinkedIn run.

Nobody is watching. The bar for **reporting a problem** instead of working
around it is zero, and the bar for **writing to LinkedIn** is high.

## The rule this whole repo exists for

`qbs-linkedin-watch-sync` reported `lastRunAt` normally for **months** while
never once completing. All three logging paths — Hindsight tallies, HubSpot
tasks, and the contact date properties — stopped on **2026-06-01** while sends
continued. Nobody noticed for twelve weeks.

> **A halted run is a successful routine. A silent one is not.**

A run that does nothing must say so, loudly, and say *what preflight
confirmed*, so "nothing to do" is distinguishable from "nothing worked".

## Preflight — mandatory, in order

Stop on any non-zero exit. Report the exit code and what it means. Do not
"try anyway".

```
QBS_HUBSPOT_TOKEN=$TOKEN python3 scripts/preflight.py [--skip-watch-list]
```

- **exit 2** — environment, auth or data fault. Fix and re-run.
- **exit 3** — schema drift. The portal changed under the code. A human must
  reconcile the two before any run is trusted.

**Then the Unipile self-test, which preflight cannot fully do.** Read one
profile known to carry dated experience rows:

```
GET /users/michelinenijmeh?account_id=<send account>&linkedin_sections=experience
```

Assert `work_experience` is present and rows carry `start`. **If it is absent,
HALT.** Omitting `linkedin_sections` returns HTTP 200 with no `work_experience`
key at all — every contact then scores unreadable, or worse `no`, and the run
writes "No Longer with Company" across the CRM. A missing key is an instrument
failure, never a verdict. `verify.read_roles` raises `InstrumentError` on it.

**Use the code, not the MCP.** An earlier version of this document required
every Unipile call to go through the Unipile MCP connector, because the tenant
DSN sits on port 16072 and this environment reaches 443 only. That is no
longer true, and following it now would make a routine refuse the only
transport that works unattended:

- `unipile.base_url()` puts the host on 443 and moves the port into `?port=`.
- `transport.UnipileClient` prefers v2 (plain host, no workaround) and falls
  back to v1 automatically, recording which answered in `route`.
- **Routine-fired sessions have no MCP connectors at all** (measured), so an
  MCP-only rule guarantees a schedule can never touch LinkedIn. That is
  precisely how both programs stayed dark for twelve weeks.

Report the `route` in the run summary. A silent degrade to v1 is how a version
problem stays invisible.

**`profile()` is pinned to v1 and must not be "upgraded".** v2 returns HTTP
200 with zero experience rows — retested 2026-08-30 under every array syntax,
against a v1 control returning seven dated roles for the same person. A
healthy-looking v2 profile is the exact shape that writes "No Longer with
Company" across the CRM.

## Identity — assert before anything writes

Only `config.SHAWN_ACCOUNT_ID` may send or comment, enforced by
`config.assert_send_account()` — an **allowlist**. Never replace it with a
blocklist: one API key spans seven accounts and five people, so a blocklist
passes for anyone newly connected.

Assert the member id `ACoAAAGv8WABzhfWcURPIaBDzbgiEWX5e781Etw` as well. Member
ids are immutable; slugs are user-changeable.

**Shawn is connected twice and both sessions are live.** They share that
member id, so the identity assertion cannot separate them — only the account
id can. v2 maps to `7lBoyXuETqKdiJYLj5HBGA`; config sends as
`S6ua4SfUT4SMRFZFOmyUzQ`. Both work today. `preflight.check_send_account`
reports the split on every run. Two live sessions on one LinkedIn login is a
documented provider error (`errors/multiple_sessions`, classified HALT), so
**one must be disconnected before the first send** — and that choice is
Shawn's, not a routine's.

**Sales Navigator: reports healthy on v2, never exercised.** On v1 every
Sales Nav route returned `401 errors/invalid_credentials` on both of Shawn's
accounts while Classic returned 200 — entitlement present, session not. On v2
the account reports `sales_navigator: running`. That is a claim from the
provider, not a verified capability: nothing has been read through it end to
end. Treat it as unproven and verify before building on it.

## Never, unattended

- Send or comment while the send ledger is stale. A dead ledger reads zero
  sends today, and zero reads as full capacity — the over-send direction, which
  is what gets an account restricted.
- Call `ledger.decide_allowance` without a real `independent_count`. It is a
  required argument with no default, because an empty ledger cannot tell
  "nothing sent" from "nothing recorded". Passing `None` halts, by design.
- Treat a comment-fetch error as "no prior comment". Skip the post instead.
- Map a missing `work_experience` to `no`.
- Write `hs_lead_status` on a `yes`.
- Upsert the roster on `hublead_linkedin_member_id` — it is populated on 0.02%
  of contacts and would create a duplicate for nearly every one. Upsert on
  `linkedin_profile_url__unique_value`, always canonicalized.
- Guess between two conflicting LinkedIn URLs. 1.3% of contacts carry URLs
  pointing at different people, usually a relative matched on surname.
  Messaging one sends Jim's pitch to Margie, as Shawn. Queue it.

## Queue, never guess

Anything needing a human goes **in the record**, not a scratch file — session
files do not survive the container. Use `ai__verification_issue`,
`ai__verification_issue_note`, `ai__verification_issue_on`.

Queue on: conflicting URLs, ambiguous employer, same-name company, succession
conflict, duplicate pair, division-scope uncertainty.

## Report at the end, whatever happened

- Counts by outcome — resolved, queued, skipped, and **why** for each skip.
- **Every guardrail with its actual number.** Never "guardrails passed".
- If the run halted: which step, which exit code, what it means.
- If nothing needed doing: say so in one line **and** state what preflight
  confirmed.
