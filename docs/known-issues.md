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
