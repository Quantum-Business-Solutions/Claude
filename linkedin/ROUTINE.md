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

**Then the Unipile self-test, which preflight cannot do.** Unipile sits behind
port 16072 and the agent proxy does not carry non-443 ports, so Python cannot
reach it — all Unipile calls go through the **Unipile MCP**, never curl.

Read one profile known to carry dated experience rows:

```
GET /users/michelinenijmeh?account_id=S6ua4SfUT4SMRFZFOmyUzQ&linkedin_sections=experience
```

Assert `work_experience` is present and rows carry `start`. **If it is absent,
HALT.** Omitting `linkedin_sections` returns HTTP 200 with no `work_experience`
key at all — every contact then scores unreadable, or worse `no`, and the run
writes "No Longer with Company" across the CRM. A missing key is an instrument
failure, never a verdict.

## Identity — assert before anything writes

Only `S6ua4SfUT4SMRFZFOmyUzQ` (Shawn Peterson) may send or comment. Assert
`connection_params.im.id == ACoAAAGv8WABzhfWcURPIaBDzbgiEWX5e781Etw` — member
IDs are immutable, slugs are not.

One API key spans **seven accounts and five people**. The others are colleague
and client identities. `config.assert_send_account()` is an allowlist; never
replace it with a blocklist, which passes for anyone newly connected.

**Sales Navigator is currently unusable through Unipile.** Every Sales Nav
route returns `401 errors/invalid_credentials` on both of Shawn's accounts
while Classic routes return 200 — the entitlement is present, the session is
not. Do not build on Sales Nav until that is reconnected.

## Never, unattended

- Send or comment while the send ledger is stale. A dead ledger reads zero
  sends today, and zero reads as full capacity — the over-send direction, which
  is what gets an account restricted.
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
