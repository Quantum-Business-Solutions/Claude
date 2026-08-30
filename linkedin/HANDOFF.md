# Handoff — QBS LinkedIn program

Written 2026-08-30 for whoever picks this up next. Read this before touching
anything; several of the findings below cost hours to establish and are not
obvious from the code.

## Where things are

Repo `Quantum-Business-Solutions/Claude` — **public**, so never write contact
PII or credentials into it. Branch `claude/linkedin-engagement-task-debug-5o6xu1`.

```
contact-verification/   Shawn's existing list-verification program (on main)
linkedin/               this program
  ROUTINE.md            the unattended-run contract — read it first
  docs/                 system overview, environment, known issues, components
  qbs_linkedin/         config, normalize, ledger, verify, posts, errors, unipile
  scripts/              preflight.py, watch_sync.py
  tests/                195 tests, all passing
```

Run tests with `PYTHONPATH=linkedin python3 -m pytest linkedin/tests -q`.

## Credentials

Environment variables only. Never commit, never paste into chat — both keys
have already leaked into transcripts and should be rotated.

- `QBS_HUBSPOT_TOKEN` — HubSpot private-app token, portal `20682069`, 144
  scopes, **verified working**
- `UNIPILE_API_KEY` — Unipile **v1** key
- Unipile **v2** key is separate and IS in the environment, stored as
  **`UNIPILE_V2_KEY`**. `transport.v2_key_from_env()` accepts that or
  `UNIPILE_V2_API_KEY`; a name mismatch here is silent and expensive, because
  the client just reports "no v2 key configured" and degrades every call to
  the v1 fallback while looking migrated

## THE JOB: migrate to Unipile v2

Shawn migrated to Unipile v2 on 2026-08-30. This is the main outstanding task.
**Everything about API access got better; the response shapes changed.**

### Why v2 is worth it

The v1 tenant DSN is `api30.unipile.com:16072`. Cloud containers here reach
**port 443 only**, so that DSN is unreachable — a direct socket to :16072 times
out while :443 on the same IP is open. That forced every call through the
Unipile MCP connector, and **routine-fired sessions have no MCP connectors at
all** (measured: a broad `ToolSearch` for `mcp__` in a fired session returns
nothing). So no schedule could ever touch LinkedIn.

v1 has a documented escape hatch — move the port to a query parameter:

```
https://api30.unipile.com/api/v1/accounts?port=16072    ->  200
```

**v2 needs no workaround at all.** Plain host, standard 443, and Sales
Navigator works where it 401'd on v1.

### v2 contract, established by probing (not from docs)

```
base            https://api.unipile.com/v2
auth            X-API-KEY header
account_id      IN THE PATH, not a query param:
                  https://api.unipile.com/v2/{acc_id}/users/{identifier}
                the error tells you: params/account_id must match ^acc_(.*)$
```

Shawn's only account (he deleted the duplicate — there is now exactly one):

```
acc_01m19mb99wfzvsb68etkn5n87x     maps to v1 id 7lBoyXuETqKdiJYLj5HBGA
member id  ACoAAAGv8WABzhfWcURPIaBDzbgiEWX5e781Etw   (immutable — assert on this)
slug       shawnpetersonquantum                       (changeable — do not)
products_connection_status: classic=running, company=running, sales_navigator=running
```

**Verified 200 on v2:** `/accounts`, `/accounts/{id}`, `/users/{id}` with
`linkedin_sections=experience`, `/users/{id}/comments`, `/users/{id}/posts`.

### Response-shape changes the code must absorb

| v1 | v2 |
|---|---|
| `items` | `data` |
| `date` | `created_at` |
| `social_id` (`urn:li:activity:123`) | **gone** |
| `id` = plain number | base64 composite |

The post id now decodes to both URNs at once:

```
WyJhY3Rpdml0eTo3NDk2MjgwMjc2OTQ0MjY5MzEzIiwi...
  -> ["activity:7496280276944269313","ugcPost:7496280276105441280"]
```

That appears to **fix** a v1 bug: there, `Comment.post_id` matched the numeric
tail of `social_id` and not the post's own `id`, so joining on `id` silently
failed for every ugcPost. Re-derive `posts.post_join_key` against v2 and
re-test the dedupe end to end before trusting it.

Sales Navigator search params also changed — `/linkedin/search/parameters` now
requires `keywords`.

### Open decision

v2 is **BETA** and Unipile warns of breaking changes. v1 still works via
`?port=`. v1 and v2 are separate account stores with separate keys — a v2 key
returns `401 missing_credentials` against v1. Confirm with Shawn which is
canonical before building further.

## Traps — every one of these was found the hard way

**Never treat an instrument failure as a finding.** `GET /users/{id}` without
`linkedin_sections=experience` returns **HTTP 200 with no `work_experience`
key**. A parser mapping that to "no current role" writes *"No Longer with
Company"* across the CRM. `verify.read_roles` raises `InstrumentError` instead.

**`hs_lead_status` needs the internal value, not the label.** `"CAS Prospect"`
matches 0 contacts; `"ConnectandSell Prospect"` matches 126,145. HubSpot
returns 0 for a bad enum *value* but errors on a bad property *name*, so this
fails completely silently.

**`ai__sources_confirming` is a NUMBER.** The outreach runbook instructs
writing a string label into it. That write fails or coerces to garbage.

**Upsert on `linkedin_profile_url__unique_value`, never on
`hublead_linkedin_member_id`.** Both are unique, but coverage is 80.5% vs
0.02% — keying on the member id creates a duplicate for ~99.98% of contacts.
The lookup is **byte-exact**: a `www.` variant, a trailing slash or a
capitalised slug all 404, and on upsert each 404 becomes a CREATE. Always
`normalize.canonical_url()` first.

**1.3% of contacts have two LinkedIn URLs pointing at different people** —
usually a relative matched on surname (Jim Becker → `margie-becker`). Neither
property is reliably authoritative. `normalize.choose_profile_url` resolves by
name where it can and returns a skip reason where it cannot. Never guess.

**HubSpot has two timestamp kinds needing opposite handling.** `date`
properties store UTC midnight of a calendar date — read them as UTC or every
"re-attempt after N days" guard fires a day early. `datetime` properties are
real instants and must bucket on Chicago-local midnight. See `ledger.py`.

**The comment feed paginates to ~2,775 comments over 26+ pages.** A partial
dedupe set silently re-comments on older posts while looking authoritative.
`commented_post_ids` raises unless fully paged.

**One API key spans several people's LinkedIn accounts.** Assert identity on
the immutable member id before any write. `config.assert_send_account` is an
allowlist — never turn it back into a blocklist.

**The cap must fail closed.** All three logging paths died 2026-06-01 and
nobody noticed for twelve weeks. A dead ledger reads "0 sent today" which reads
as full capacity — the over-send direction, which gets accounts restricted.
`ledger.decide_allowance` halts instead. `LEDGER_EPOCH` exists because the
Jun 1 gap is deliberately not back-filled (Shawn's decision) and counting
history from all time would deadlock every run forever.

## State of play

**Working and tested:** all HubSpot plumbing, preflight (green), the roster
builder, URL canonicalization, the Reading Rule, comment dedupe, post
eligibility, the error taxonomy, cap accounting and date arithmetic.

**Not built:** the engagement and outreach orchestration — the loop that ties
these together and actually comments or sends. Nothing has ever sent a
LinkedIn message from this code, and `dry_run` defaults to true.

**Blocked on nobody now.** The connector problem is solved by v2 (or by v1's
`?port=`). No support tickets pending.

**Also worth knowing:** the `contact-verification` routine has been reporting
SUCCEEDED while writing nothing since June — same root cause. Its
`scripts/unipile.py` needs the same fix. `ai__li_last_attempt_date` and
`ai__verification_issue` are still 0 across the portal.
