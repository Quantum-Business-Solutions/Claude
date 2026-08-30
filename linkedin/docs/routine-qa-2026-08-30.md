# Step-by-step QA of the scheduled routine, 2026-08-30

Every step below was **executed**, not reasoned about. Run against the live
portal and live Unipile.

## What is actually scheduled

Three Routines existed. One was a spent one-shot and has been deleted.

| routine | cron | next | what it does |
|---|---|---|---|
| **LinkedIn watch-sync** | `30 12 * * 1-5` | 2026-08-31 12:33 UTC | resolves member IDs. **Read-only on LinkedIn.** |
| Contact Verification | `0 13 1 * *` | 2026-09-01 | separate program, already migrated to v2 by another agent |
| ~~Env check~~ | one-shot | — | spent; deleted |

**There is no engagement routine, because there is no engagement code.**

## The run, step by step

```
STEP 1  Unipile reachability
        host api30.unipile.com, tenant port 16072
        REACHABLE over 443 with ?port=16072 — 7 account(s)                 PASS

STEP 2  preflight --skip-watch-list                                     exit 0
        auth ............ portal 20682069, 144 scopes
        schema.contacts . all present
        upsert_key ...... linkedin_profile_url__unique_value unique=True
        sources_confirming type=number
        verdicts ........ moved / no / no_profile / unreadable / yes
        lead_status ..... 'ConnectandSell Prospect' resolves
        task_types ...... all present
        pool ............ 83,822 qualified candidates
        ledger .......... 0/0/0 -> NOT CLEARED TO SEND (needs a Unipile count)
        send_account .... v1 and v2 agree on 7lBoyXuETqKdiJYLj5HBGA

STEP 3  identity + Reading Rule on a live profile
        identity OK : Shawn Peterson | 7lBoyXuETqKdiJYLj5HBGA
        dated rows  : 11
        Reading Rule: moved | role at 'Zscaler' ended 2020-06-01;
                             now at 'ThoughtSpot' (Chief Market...)         PASS

STEP 4  pytest                                          332 passed in 0.24s

STEP 5  watch_sync plan --list-id 8260 --limit 60                       exit 0
        ready 57 | needs_resolution 1 | skipped 2 | total 60
          1  no LinkedIn URL on the contact
          1  slug 'techmarketingpro' does not match first name

STEP 6  resolve the outstanding provider id
        jennifer-maisch-8709984 -> invalid_recipient (locked profile)
        recorded as a skip, not retried, no verdict invented               PASS

STEP 7  write --dry-run
        {"written":0,"submitted":0,"complete":true,"rejected":[],"dry_run":true}
```

The pipeline runs end to end. Step 3 is worth noting: the destination-ranking
fix picked **ThoughtSpot (Chief Market…)** — the real senior role — from a
live 11-row profile. Before the fix that would have been whichever row the
array happened to list first.

## Can it comment on posts? No. Demonstrated, not asserted.

```
Unipile (v1) has post_comment      : True
UnipileClient has post_comment     : False        <- the v2-preferred client
callers of post_comment anywhere   : 0 (outside tests)
scripts/                           : preflight.py, watch_sync.py
```

`post_comment` exists on the v1 client and **nothing calls it**. The
v2-preferred transport, which is what everything now routes through, has no
comment method at all. There is no orchestration script, so there is nothing
to schedule.

Three separate things are missing before a comment can happen:

1. **The engagement roster.** `preflight` returns exit 2:
   `'LinkedIn Watch — Sales Nav' does not exist`.
2. **A comment method on `UnipileClient`**, with `assert_send_account` on it.
3. **The loop itself** — select post, dedupe, draft, cap-check, post, log.

And a fourth that is not code: the ledger is empty since the epoch, so
`decide_allowance` halts any send path that cannot supply an independent
count. That is deliberate, and it means the first send day needs a real
Unipile count wired in, not just an orchestrator.

## Issues found in the routine, and what was done

**The routine never checked out the code, and `linkedin/` does not exist on
`main`.** It named the branch as context and then ran `PYTHONPATH=linkedin`
against whatever the container happened to hold. Yesterday's run worked, so
the environment supplied the branch — but that was luck, not contract, and
the sibling Contact Verification routine documents *two runs that failed
silently on exactly this*. Fixed: an explicit STEP 0 that checks out the
branch or clones it, and HALTs if the code is absent.

**The routine bypassed the v2 transport entirely.** It called `Unipile()`
directly, so the only scheduled work in the system ran v1-only and the v2
migration was not actually in effect anywhere. Fixed: it now uses
`UnipileClient` and must report which version answered.

**It listed only `UNIPILE_API_KEY`.** The environment holds `UNIPILE_V2_KEY`.
Fixed: both named, v2 marked primary, v1 the fallback.

**It told the agent to "sanity-check the count".** Now that `write` reports
`written` / `submitted` / `complete`, the instruction is explicit: a false
`complete` or a mismatch must be reported loudly with every rejection.

**A spent one-shot Routine was still enabled.** Deleted.

## What runs tomorrow, and what it can do

12:33 UTC, watch-sync. It can read profiles and write two properties —
`hublead_linkedin_member_id` and `linkedin_profile_url__unique_value` — on
contacts already in list 8260. It cannot comment, invite, message, create a
contact, or change a lead status. On today's data it would resolve at most one
contact and skip it as locked.

The realistic failure modes left, in order of likelihood:

- the branch checkout fails in the fired environment (now HALTs loudly instead
  of running against missing code)
- Unipile rate-limits (429 after ~4 rapid profile reads on v2; the routine is
  told to pace and to stop the batch, not retry through it)
- a HubSpot 207 partial write (now surfaced rather than counted as success)
