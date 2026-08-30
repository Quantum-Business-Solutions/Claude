# Known Issues, Contradictions and Blockers

## Broken: `qbs-linkedin-watch-sync`

**Has never completed a successful run since inception.** Three independent lines of evidence agree:
the output CSV has never existed anywhere on disk; no `sync_retain` memory has ever been written;
and every sampled run transcript terminates identically at `navigate → navigate (retry) → stop`.

Two structural causes, not one:

- **The browser is unreachable.** The task drives Claude in Chrome — a *local* browser. Cowork
  scheduled tasks execute remotely. The navigate call cannot succeed under any configuration,
  which is why the failure is 100% consistent.
- **The output path is unwritable.** The destination is a local session-scoped folder, and that
  session no longer exists.

Moving Cowork to web does not fix this. It removes the desktop-must-be-awake constraint but leaves
both causes intact and makes the second worse.

**Downstream:** both engage tasks have been hard-stopping on a missing roster every day.
→ *Outstanding: audit what they actually did on each run and confirm no comments were posted
against an improvised roster.*

**The fix:** Unipile exposes `POST /api/v1/linkedin/search`, which accepts a Sales Navigator list
URL and returns `public_identifier`, `public_profile_url`, `name`, and `current_positions[]` per
lead. That is every CSV column except the HubSpot ID, from one authenticated call, with no browser
in the chain.

## Broken: the tally logging

No Hindsight `daily_tally` memory has been written since **2026-06-01** — a ~12-week blackout —
while sends continued (Unipile confirms invites on Aug 26 and Aug 28). The send path works; the
logging path is dead. **The outreach program has been running blind, not stopped.**

This is the single strongest argument for deriving counts from HubSpot tasks rather than from
memory: a memory write that silently fails produces an under-count, and an under-count means
*over-sending*, which is the failure direction that gets an account restricted.

## Degraded: outreach volume

4 touches in the week of Aug 24, against a 13–19/day cadence in late May — roughly a 90% collapse.
All three invites fired at 21:30 UTC, two in the same minute: an automated batch still firing on
schedule against a nearly empty queue. Likely a pool-exhaustion or filter problem, not a send
problem.

## Do not trust: the `linkedin_chats` DB mirror

BrandCommand's `list_linkedin_chats` is materially wrong. It showed 7 in-window threads where
Unipile shows 28; dated one thread Aug 14 where Unipile says Aug 22; reports `is_inmail: false` /
`inbox_tab: "other"` on every row, losing InMail and sponsored classification entirely; carries no
unread state; and ignores the account filter, surfacing Keven Ellison's inbox. Any reporting built
on it **understated inbound volume by roughly 4x**.

Use Unipile directly: `GET /chats?account_id=S6ua4SfUT4SMRFZFOmyUzQ&limit=50`, filter client-side
on `content_type`.

## Counting caveat: `/users/invite/sent`

Returns only **pending** invitations. Anything accepted or withdrawn has already dropped off, so
any count derived from it is a floor, not a total. Another reason HubSpot tasks are the
authoritative send ledger.

## Resolved contradictions

Where the source documents disagreed, these were settled against live data.

### Sales Nav entitlement

- **watch-sync audit §7 claimed:** "The classic account lacks the Sales Nav entitlement" and a
  `sales_navigator` search must run on `7lBoyXuETqKdiJYLj5HBGA`.
- **The outreach runbook claimed:** both accounts are `sales_navigator`; use
  `S6ua4SfUT4SMRFZFOmyUzQ` for everything.
- **Live `GET /accounts` says:** both Shawn accounts carry `premiumFeatures: ["sales_navigator"]`,
  the same `premiumId`, and the same `premiumContractId` `2014060643`.

**The runbook is right; the audit is wrong.** Use `S6ua4SfUT4SMRFZFOmyUzQ` for everything including
Sales Nav search. `7lBoyXuETqKdiJYLj5HBGA` is redundant and should be disconnected — two live
sessions on one LinkedIn login is a restriction risk in itself.

### HubSpot access

- **The outreach skill listed as open item #1:** "HubSpot connector access — **Unverified**. Never
  successfully called in the build session. Everything depends on it."
- **Live test says:** the PAT authenticates against portal `20682069` with 144 scopes covering
  every CRM operation both routines need.

Resolved. The blocker was the *OAuth connector*, not HubSpot itself. Direct REST with a PAT works.

## Unresolved contradictions

### Daily stop threshold — 70 or 100?

The outreach runbook says both, in different places:

- Step 0d: "Total ≥70 → `STOPPED: daily cap reached`"
- Caps table: "combined ceiling 100"; Stop conditions: "today's total >100"

Both are encoded in `OutreachCaps`; `daily_stop = 70` is the one that halts a run. **Needs a
decision from Shawn** — a run that stops at 70 when the intended ceiling is 100 leaves a third of
the day's capacity unused.

## Open blockers

| # | Blocker | Needed to unblock |
|---|---|---|
| 1 | **Sales Navigator list URL** unknown | Copy from the address bar with the list open in Sales Nav. Unipile has no endpoint that enumerates saved lead lists — verified against the full API index. Begins `https://www.linkedin.com/sales/lists/people/…` |
| 2 | **Unique LinkedIn URL property** internal name unknown | Both existing tasks filter on `hs_linkedin_url`, but that is a HubSpot standard property and is **not unique by default**. Upserting against the wrong property creates exactly the duplicates the design prevents. Now resolvable — the PAT can read the property schema. |
| 3 | **Watch list does not exist in HubSpot** | The active list `LinkedIn Watch — Sales Nav` has to be created (or the marker-property design built) before any engagement run can work |
| 4 | **Both credentials exposed in transcripts** | Rotate, then set as environment variables |
| 5 | **`qbs-linkedin-expand-pool` is broken** | Its Step 4 rewrites "the Step 1 filter section in the daily task prompt," which now lives in the skill. Needs a one-line fix; check `qbs-linkedin-weekly-digest` for the same assumption |

Blockers 2 and 3 are now solvable directly — the working PAT removes the reason the earlier audit
couldn't resolve them.

## Environment hazards to design around

- **Overwriting workflows.** Portal automations `274857276` and `274857511`, plus Data Enrichment,
  overwrite verified data on standard fields. This is why verification output goes to the `ai__`
  namespace and why job titles are stored in `ai__contact_evidence` rather than the standard title
  field.
- **Silent-failure class.** `watch-sync` reported `lastRunAt` normally for months while
  accomplishing nothing. **Any rewrite must make a zero-result run loud**, not merely absent.

## Cap accounting and date arithmetic — `qbs_linkedin/ledger.py`

Built and tested 2026-08-29. This is the module whose failure costs the most:
an undercount reads as spare capacity, spare capacity authorises more sends,
and over-sending is what gets a LinkedIn account restricted. Every path fails
**closed** — when the ledger cannot be trusted the allowance is zero, not the cap.

### The off-by-one that was hiding in plain sight

HubSpot has two kinds of timestamp and they need opposite handling. Mixing them
is only ever wrong by a few hours, which is exactly why it survives review.

**`date` properties** — `ai__contact_verified_date`, `ai__li_last_attempt_date`,
`ai__reassociated_on`, `ai__verification_issue_on` — store **UTC midnight of the
intended calendar date**. They are a date, not an instant. Converting one to
America/Chicago yields 18:00 or 19:00 the *previous* day:

```
date_to_hubspot_date(2026-01-16)          -> UTC midnight Jan 16
  read as UTC   -> 2026-01-16   correct
  read as local -> 2026-01-15   the bug
```

Every "don't re-attempt within N days" guard would fire a day early, always in
the direction of re-attempting too soon. A 14-day retry window opens on day 13.

**`datetime` properties** — `hs_createdate`, `hs_timestamp`,
`hublead_last_linkedin_message_sent_date` — are real instants, and bucketing
them by day is a genuine timezone question requiring Chicago-local midnight.
A comment posted at 23:30 Chicago is 04:30 UTC the next day; bucketing by UTC
files it under the wrong day and splits one run's tally across two.

Both rules are now separate named functions so they cannot be confused, with
tests asserting the wrong answer is *not* produced.

### DST is not cosmetic

A hardcoded 24-hour window is wrong twice a year. Tested:

| Local day | Real length |
|---|---|
| 2026-03-08 (spring forward) | **23 hours** |
| 2026-08-29 (ordinary CDT) | 24 hours |
| 2026-11-01 (fall back) | **25 hours** |

On the spring-forward day a fixed 24h window overruns into the next day and
double-counts its first hour — inflating the tally, which fails safe — but on
fall-back it *undercounts* by an hour, which does not.

### Fail-closed rules, all tested

| Condition | Allowance | Why |
|---|---|---|
| Ledger has history but no write in 3 days | **0, halt** | The live condition: 153 historic tasks, none since 2026-06-01. A naive read is "0 sent today, full capacity" |
| No history and no recent writes | normal | A first run, not a failure |
| Independent count exceeds ledger by >2 | **0, halt** | The ledger is missing sends; its low number must not authorise more |
| Independent count exceeds by ≤2 | normal | Unipile's own counts are approximate — `/users/invite/sent` is pending-only with synthesised timestamps |
| `posted_today >= per_day` | 0 | Ordinary cap |

Staleness is checked **before** the cap: a dead ledger with a plausible-looking
count is still a halt, because the count itself cannot be trusted.

Preflight now delegates to the same function, so preflight and the routines
cannot drift apart on what "safe to send" means. Live output:

```
[FAIL] ledger: 0 today / 0 in 3d / 153 ever -> ledger has no write in 3d but
       holds 153 historic records — it is not recording. A zero count here
       means 'unknown', not 'nothing sent'.
```

### Active hours are checked per action

`within_active_hours` is called before each post, not once per run. A run
starting at 17:55 must not place its next comment at 18:02 after a 90–180s
pause. Tested at both ends of the window and against a UTC instant that looks
like the middle of the night but is 18:00 locally.

## Decision: the Jun 1 → Aug 29 ledger gap is written off, not back-filled

Shawn's call, 2026-08-29. Those sends are unrecoverable anyway —
`/users/invite/sent` returns pending invitations only, with synthesised
timestamps (every entry shares one fabricated time-of-day), so there is nothing
accurate to reconstruct from. Inventing records would be worse than having none.

**But writing it off had a consequence that needed handling in code.** The
staleness rule halts when history exists and nothing recent does, and 153
historic tasks with no recent ones is exactly that shape. Left alone it would
have halted **every run forever**: the routine cannot write its first ledger
entry without sending, and cannot send while the ledger looks dead.

`LEDGER_EPOCH = 2026-08-29` breaks the deadlock honestly. Before it, silence is
written off; after it, silence is a fault. The first run finds no post-epoch
history, treats itself as a fresh ledger, and proceeds. Every run after that is
held to the full standard — one send creates one record, and a day of silence
after that halts.

Preflight now passes:

```
[PASS] ledger: 0 today / 0 in 3d / 0 since epoch 2026-08-29
       -> 20 allowed (0/60 used today)

PREFLIGHT OK
```

Three tests pin the behaviour, including one asserting the old all-time count
*would* have deadlocked, so nobody reintroduces it.

## Playwright cannot reach LinkedIn from this environment

Tested 2026-08-29. Chromium launches (use the pre-installed
`/opt/pw-browsers/chromium-1194/chrome-linux/chrome` via `executable_path` —
`pip install playwright` pulls a build expecting 1234 and `playwright install`
must not be run). Navigation to a LinkedIn post fails with
`net::ERR_CONNECTION_RESET` both with and without an explicit proxy, while
`curl https://www.linkedin.com/` returns HTTP 200 from the same container —
so it is LinkedIn's bot detection on headless Chromium, not egress policy.

Not worth pursuing: the Unipile API returns comment and post content directly,
which is authoritative rather than a rendering of it.

## No REST path to Unipile exists — measured, not assumed

Asked on 2026-08-30 whether the LinkedIn work could simply be configured the
way `contact-verification` is, so that it works. It cannot, and
`contact-verification/scripts/unipile.py` is what proves it. Running its own
`probe` against the live key:

```
unreachable  https://api30.unipile.com:16072   tcp 51.159.14.128:16072 TimeoutError
REACHABLE    https://api30.unipile.com         GET /accounts -> HTTP 502
REACHABLE    https://api.unipile.com           GET /accounts -> HTTP 404
REACHABLE    https://api1.unipile.com          GET /accounts -> HTTP 502
```

Port 443 is reachable at the network level; **no host serves the tenant API
there.** The tenant port `16072` times out. So the environment secret
`UNIPILE_API_KEY` is sufficient credentials and insufficient access — the key
was never the problem.

This matches what `contact-verification/ROUTINE.md` already states, and means
both programs share one dependency: **the `mcp__Unipile__*` connector must be
present in the fired session.** That is a claude.ai connector grant, not an
environment variable, and the two are not interchangeable.

### Consequence for the verification routine

`trig_01B3hA6TUzMWE7tYR7d25mkD` fired 2026-08-30 14:13 UTC and reported
`SUCCEEDED`. Its prompt states that `ai__li_last_attempt_date`,
`ai__verification_issue` and `ai__li_tenure_years` were set on **zero** records
and that exercising them was the point of the capped run. Measured afterwards:

| Property | Populated |
|---|---|
| `ai__li_last_attempt_date` | 0 |
| `ai__verification_issue` | 0 |

Consistent with the run halting cleanly at its Unipile self-test — correct
behaviour under the contract ("a halted run is a successful routine"), but the
effect is a routine reporting success while writing nothing. Exactly the
failure class both programs exist to eliminate.

### The durable fix

Ask Unipile whether the account can be served on **port 443**. If it can,
`unipile.py`'s existing candidate list finds it with no code change, the REST
path starts working, the environment secret becomes sufficient, the MCP
connector stops being a dependency for either program, and response **headers**
become readable — which the MCP HAR passthrough does not return, so
`Retry-After` and `X-RateLimit-*` are currently invisible.

One support ticket, versus a per-routine configuration constraint forever.

## MEASURED: routine-fired sessions have no MCP connectors at all

Settled 2026-08-30 by firing a diagnostic routine that reported its findings
into a HubSpot task (the only channel a fired session was known to have).

```
VERDICT: UNIPILE MCP IS NOT AVAILABLE
Visible mcp__ tools: none
  (a broad ToolSearch for "mcp__" also returned no matches)
UNIPILE_API_KEY env var: present
```

**Not a Unipile-specific gap — fired sessions get zero connectors of any kind.**
The environment secret is correctly configured and sitting there unusable,
because the session has no tool that can reach a non-443 port.

This explains, without inference:

| Run | Outcome |
|---|---|
| `qbs-linkedin-watch-sync` test fire | 0 provider IDs resolved |
| Verification routine, 2026-08-30 14:13 | `SUCCEEDED`, 0 writes to its target fields |
| Connector probe v1 | ran, produced nothing |
| Connector probe v2 | reported the verdict above |

All four are the same cause. Both programs halt correctly at their Unipile
self-test — which is the contract working — but the visible result is a routine
reporting SUCCEEDED while accomplishing nothing.

### What this rules in and out

- **Not** the API key. Present and valid; it works from an interactive session
  and from a laptop.
- **Not** the curl command or the DSN. Both correct.
- **Not** environment secrets. Correctly set; secrets and connectors are
  different mechanisms and one cannot substitute for the other.
- **It is** that scheduled sessions carry no connectors in this organization.
  `create_trigger` refuses the `connectors` parameter outright:
  *"not available for this organization."*

### The two ways out

1. **Port 443 from Unipile.** If the tenant can be served on 443, REST works
   directly from any container, the environment secret becomes sufficient, and
   connectors stop mattering for either program. `unipile.py` already probes
   for it, so no code changes. This is the durable fix — it removes the
   dependency rather than provisioning around it.
2. **Enable connectors for scheduled sessions**, if that is grantable at the
   organization level. The API path is closed, so this is a claude.ai-side
   change.

Until one of them lands, anything needing LinkedIn runs from an interactive
session, and no schedule should be trusted to do it.
