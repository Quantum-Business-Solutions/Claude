# What the routine actually does, step by step

Written 2026-08-30 so the schedule is documented rather than inferred from
code. Read with `../ROUTINE.md`, which is the *contract* (what a run may and
may not do). This is the *itinerary*.

**Read the status line before planning anything on this.** Only one of the
three programs below is built.

| program | state | can it run unattended? |
|---|---|---|
| `preflight` | built, green against live HubSpot | yes |
| `watch-sync` | built, **proven** — wrote 56 provider IDs on 2026-08-30 | yes |
| engagement / outreach | **not built** | no — there is no code to run |

---

## 1. `preflight` — the gate

`python3 scripts/preflight.py` (needs `QBS_HUBSPOT_TOKEN`)

Runs five checks against the live portal and exits non-zero rather than
letting a run proceed on bad ground. Nothing else may start until this is 0.

| check | what it proves | fails when |
|---|---|---|
| `auth` | the token works and carries the scopes | token revoked or wrong portal |
| `schema.lead_status` | `ConnectandSell Prospect` still resolves | someone renames the enum |
| `schema.*` | every `ai__` property still exists with the expected type | a property is deleted or retyped |
| `pool` | the ICP query still returns candidates | a filter silently matches nothing |
| `ledger` | the send ledger is alive and its counts are readable | the ledger is stale — see below |

Exit codes: **0** proceed · **2** environment/auth/data fault · **3** schema
drift, which a human must reconcile.

The `ledger` check is the one that matters most. All three logging paths died
on 2026-06-01 and nobody noticed for twelve weeks. A dead ledger reads "0 sent
today", and zero reads as *full capacity* — the over-send direction, which is
what gets a LinkedIn account restricted. So it fails closed: stale ledger,
no run.

Live output, 2026-08-30:

```
[PASS] auth: portal 20682069, 144 scopes
[PASS] schema.lead_status: 'ConnectandSell Prospect' resolves
[PASS] pool: 83,823 qualified candidates
[PASS] ledger: 0 today / 0 in 3d / 0 since epoch 2026-08-29 -> 20 allowed
PREFLIGHT OK
```

## 2. `watch-sync` — repair the join key

This is the one that ran for real. It does **not** touch LinkedIn on anyone's
behalf and sends nothing; it repairs the identifiers everything else depends
on. Split deliberately into two commands so the LinkedIn reads belong to the
routine and the HubSpot writes belong to the script.

**`plan --list-id <id> [--limit N]`** — reads the watch list from HubSpot and
emits a JSON queue of contacts whose LinkedIn identity needs work:

1. Pull the roster with both URL properties and the provider-id property.
2. Canonicalize each URL to `https://linkedin.com/in/<slug>` — the stored form
   for 94.9% of records. The HubSpot lookup is **byte-exact**, so a `www.`,
   a trailing slash or a capitalised slug all miss, and on upsert each miss
   becomes a *new duplicate contact*.
3. Where the two URL properties disagree, resolve by name if possible and
   **queue the contact if not**. 1.3% of contacts carry two URLs pointing at
   different people — usually a relative matched on surname (Jim Becker →
   `margie-becker`). Guessing here messages the wrong human as Shawn.
4. Validate any existing provider id with `is_member_id()` — a real one starts
   `ACo`/`ADo`. 29 of the 30 values already stored were numeric `member_urn`s,
   i.e. the wrong identifier entirely.

**`write --input <file|-> [--dry-run]`** — upserts the resolved rows back.

- Upsert key is **`linkedin_profile_url__unique_value`** (80.5% coverage),
  never `hublead_linkedin_member_id` (0.02% — it would create a duplicate for
  ~99.98% of the roster).
- `--dry-run` reports `would_write` and writes nothing.

Result on 2026-08-30: provider-id coverage went **30 → 86**, all 56 new values
real member IDs, 0 malformed, every URL canonical.

## 3. Engagement / outreach — not built

To be explicit, because the docs elsewhere describe the *intended* behaviour
in enough detail to read like a description of working code:

**Nothing in this repository has ever sent a LinkedIn message, invite or
comment.** There is no orchestration loop. The pieces it would be assembled
from are built and tested — the Reading Rule (`verify.py`), comment dedupe and
post eligibility (`posts.py`), cap accounting (`ledger.py`), the error
taxonomy (`errors.py`), the send-account allowlist (`config.py`) — but the
program that calls them in order does not exist.

When it is written, the contract in `../ROUTINE.md` governs it, and these are
the guardrails it must honour, each of which already has code and tests:

- `assert_send_account()` before any write — one API key spans seven accounts
  and five people.
- `decide_allowance()` before any send — halts on a stale ledger rather than
  reading silence as capacity.
- `read_roles()` for every employment judgement — raises `InstrumentError`
  when `work_experience` is absent, because a missing field must never become
  a finding about a person.
- `commented_post_ids()` fully paged — a partial dedupe set silently
  re-comments on older posts while looking authoritative.

---

## Which API answers which call

`transport.py` prefers v2 and falls back to v1 automatically, per call, and
records which answered in `route` so a degraded run is visible in the report.

| call | route | why |
|---|---|---|
| `profile()` | **v1 only** | v2 returns HTTP 200 with **zero** experience rows — retested 2026-08-30 under every array syntax. v1 returns 7 dated roles for the same person. A "successful" v2 profile is the exact shape that writes *No Longer with Company* across the CRM. |
| `posts()` | v2, falls back | shape differences absorbed by the shim |
| `self_comments()` | v2, falls back | fully paged on both versions |
| `health()` | v2 preferred | only v2 reports per-product status; v1 says OK while Sales Navigator is dead |

## Accounts — the live picture

v2 has **one** Shawn, and it is what the code pins:

```
acc_01m19mb99wfzvsb68etkn5n87x     Shawn Peterson
  user_id                ACoAAAGv8WABzhfWcURPIaBDzbgiEWX5e781Etw
  metadata.v1_account_id 7lBoyXuETqKdiJYLj5HBGA
  products               classic / company / sales_navigator all "running"
```

Note `sales_navigator: running`. `../ROUTINE.md` still says Sales Navigator is
unusable; that was true on v1, where every Sales Nav route returned
`401 errors/invalid_credentials`. On v2 it reports healthy. It has **not** been
exercised end to end — treat "running" as a claim to verify, not a capability
to build on.

**Unresolved:** v1 still lists 7 accounts and two of them are Shawn, both
live, both returning his 7 dated roles:

```
S6ua4SfUT4SMRFZFOmyUzQ   created 2026-03-09   <- config.SHAWN_ACCOUNT_ID
7lBoyXuETqKdiJYLj5HBGA   created 2026-05-10   <- what v2 maps to
```

They share the immutable member id, so `assert_identity` cannot tell them
apart and a write from either publishes as Shawn — this is not a
wrong-person risk. It is a split-session risk: two live Unipile sessions on
one LinkedIn member is a documented Unipile error condition
(`errors/multiple_sessions`). Pick one before the first send and delete the
other.
