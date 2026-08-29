# Watch-Sync — design and rationale

The roster builder for the engagement routine. Replaces `qbs-linkedin-watch-sync`,
which never completed a single run since inception.

## Why it doesn't use Sales Navigator

The audit proposed replacing the browser scrape with Unipile's
`POST /linkedin/search`, fed a Sales Nav list URL. **That would have failed the
same way.** Tested live on 2026-08-29:

| Call | Result |
|---|---|
| `type=INDUSTRY` (Classic) on `S6ua4Sf…` | **200 OK** |
| `service=SALES_NAVIGATOR&type=LEAD_LISTS` on `S6ua4Sf…` | **401 invalid_credentials** |
| same on `7lBoyXuE…` | **401 invalid_credentials** |

Both accounts report `premiumFeatures: ["sales_navigator"]`, so the LinkedIn
entitlement is real — but Unipile's Sales Navigator **session** is not
authenticated. Per the endpoint spec, 401 on that route means a disconnected
account, not a bad API key, and the Classic 200 on the same account proves the
key and the LinkedIn session are both fine.

Two corrections to the audit while we're here:

- It claimed *"Unipile has no endpoint that enumerates saved lead lists
  (verified against the full API index)."* Not so — `LEAD_LISTS` and
  `SAVED_SEARCHES` are both valid `type` values on
  `GET /linkedin/search/parameters` with `service=SALES_NAVIGATOR`. The problem
  is the dead session, not a missing endpoint.
- It blocked on *"the Sales Navigator list URL must be copied from the address
  bar."* Moot. Even with the URL, the call 401s.

**So the roster comes from HubSpot** — reachable, authoritative, already the
system of record, and it needs nothing pasted from a browser.

## What the job actually is

Resolving **provider IDs**, not scraping names.

`GET /users/{id}/posts` rejects a vanity slug with `422 invalid_recipient`; it
requires the LinkedIn member id (`ACo…`). Only **29 of 153,330** contacts carry
one. Without this step the engagement routine has almost nobody whose posts it
can fetch — so this is the gate on the whole engagement program, not a
nice-to-have.

Every resolved id is written to `hublead_linkedin_member_id`, which is unique
and immutable. Coverage compounds run over run, and once a contact has one, a
vanity-URL rename can never silently drop them off the roster again.

## The plan / write split

Unipile is behind port 16072 and the agent proxy carries only 443, so Python
cannot call it. Same contract as `contact-verification`:

```
plan   → read HubSpot, emit the work queue as JSON        (deterministic, code)
         ↓
       routine resolves each profile via the Unipile MCP  (judgment + MCP)
         ↓
write  → take resolved JSON, write back to HubSpot        (deterministic, code)
```

`write` batches **by contact id**, never by upsert. An upsert would create a
contact on any key miss, and at this point the record id is already known.

## Classification

Every roster member lands in exactly one bucket:

| Bucket | Meaning |
|---|---|
| `ready` | already has a provider id — engagement can fetch posts today |
| `needs_resolution` | has a trustworthy URL, needs one Unipile profile read |
| `skipped` | cannot be resolved safely; reason recorded per contact |

A run where both `ready` and `needs_resolution` are zero **exits 2**. An empty
roster is a failure, not a quiet success — that distinction is the entire
lesson of the original task.

## Live test, list 8260 (40 contacts)

First run: 36 resolvable, **4 skipped (10%)**. Three of those four were false
negatives, and each pointed at a real matcher gap:

| Contact | Stored | Diagnosis |
|---|---|---|
| Helen Piña | `helen-piã±a-7b83773` vs `helenpina` | mojibake on one side only |
| Shivani Chakravarthy | `shivani-chakravarthy-130138197` vs `shivanich` | vanity vs auto-generated slug, same person |
| Mike Grahl | `grahl` | bare-surname slug |
| Celest Hall | — | genuinely no LinkedIn URL |

Three rules added:

1. If exactly one side is mojibake, the clean side wins — a corrupted slug can
   never match a real profile, so there is nothing to weigh.
2. If both slugs match the contact's name, take the unique property. That is a
   cosmetic difference, not a wrong-person conflict, and skipping would drop a
   valid prospect.
3. A slug exactly equal to the surname is accepted. Requiring the first initial
   rejects a common style; exact equality keeps the relative cases out, since
   those are always `margie-becker`, never bare `becker`.

Second run: **1 skipped (2.5%)**, and that one has no LinkedIn URL at all.

## End-to-end verification

Resolved Micheline Nijmeh through the Unipile MCP —
`ACoAAAAXYqUBKmRosX0V1O_okKokDG_a3zABHPY`, `work_experience` present with dated
rows (CMO at ThoughtSpot, `end: null`). Dry run reported `would_write: 1`; the
live write reported `written: 1`; HubSpot then returned:

```
hublead_linkedin_member_id         ACoAAAAXYqUBKmRosX0V1O_okKokDG_a3zABHPY
linkedin_profile_url__unique_value https://linkedin.com/in/michelinenijmeh
```

Note the canonicalization: the input was
`https://www.linkedin.com/in/michelinenijmeh/` and what landed is the portal's
dominant bare-host, no-trailing-slash form. Writing it as supplied would have
missed the unique key on every future lookup and created a duplicate.

## Open question

Lists **5243** (1,136 members) and **8260** (281) are both scoped to *"Head of
Marketing"*. The config names them generically as the verification universe and
the verified-callable set, but they are far narrower than the 83,826-contact
ICP. Worth confirming whether engagement should target those lists or a broader
roster.

## Test fire, 2026-08-29

The routine was created (`trig_01N5WJvp47qoYtrEg7wUtUPB`, weekdays 12:30 UTC,
fresh session per fire) and fired manually. Result: the session ran ~2.5 minutes
and completed, and **wrote zero provider IDs**.

That is the correct outcome for the condition it hit, and it is what the run
contract asks for — halt and report rather than proceed on a broken instrument.

### Confirmed blocker: routines carry no connector grant

`create_trigger` returned:

> this trigger stores no MCP connectors, so the sessions it fires will run
> without connector (`mcp__<server>__*`) tools

Passing `connectors: ["Unipile"]` explicitly was refused — *"the connectors
parameter is not available for this organization."* So a fired session has no
`mcp__Unipile__execute-request`, and Unipile is unreachable any other way from
the sandbox (port 16072, non-443, not carried by the agent proxy).

Steps 1 and 4 (preflight, `plan`) need only HubSpot and work. Step 5
(resolution) cannot run at all.

**To fix:** recreate the routine from the claude.ai Routines UI, where
connectors can be attached. Worth checking how the existing
`contact-verification` routine obtains its Unipile access, since it has the
same dependency and was created the same way.

### The test also found a bug that would have shipped

Verifying the effect rather than reading the run's own report surfaced this:
of the 30 contacts carrying `hublead_linkedin_member_id`, **29 hold a numeric
value** (`67306739`, `19325984`, `156477844`) rather than a member id.

Those are `member_urn` values — a *different* identifier.
`GET /users/{id}/posts` rejects them with `422 invalid_recipient`. Only the one
contact resolved by hand in this session carries a real `ACoAAA…` id.

`build_queue` originally treated the property's mere *presence* as "ready".
Those 29 would have been handed to the engagement routine as engageable,
failed at fetch time, and done so quietly on every run forever — the exact
silent-failure class this rebuild exists to eliminate. Classification now
validates the `ACo`/`ADo` prefix, and a populated-but-wrong value is recorded
as `stale_provider_id` and re-resolved.

So the honest provider-id coverage is **1**, not 30. The engagement routine is
gated on this run working.
