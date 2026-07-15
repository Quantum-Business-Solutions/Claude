---
name: qbs-ticket-reconciliation
description: THE single skill for evaluating, flagging, and closing QBS HubSpot tickets against evidence. Replaces qbs-client-reconciliation, qbs-ticket-reconciliation-flagging, and qbs-marko-ticket-cleanup — if a request matches any of their old triggers, it comes here. Use whenever anyone wants to reconcile a client, clean up tickets, audit an owner's queue (e.g. "clean up Marko's tickets", "what's open on Marko", "audit Marko's queue"), find close-candidate or duplicate or stale tickets, flag tickets for closure review, verify what's actually been built vs. what tickets claim, bank hours, surface unbilled scope creep, or run a weekly/quarterly delivery reality check. Also trigger on "reconcile [client]", "which tickets can we close", "close out [client]'s open tickets", "where are we with [client]", "what's actually done for [client]", "is [client]'s work actually done", "catch up on [client] before QBR", "go through the open queue", or any request to evaluate open tickets against evidence. NOT for creating/logging tickets (qbs-hubspot-ticketing) or full portal health audits with scoring (hubspot-audit). Default posture is flag-for-review; closes only happen after explicit human approval, and this skill never deletes anything.
---

# QBS Ticket Reconciliation

One skill for the whole ticket-hygiene job: evaluate open tickets against
evidence, flag what should close, and — only after human review — execute the
closes. It merges three earlier skills (client-reconciliation, flagging,
Marko-cleanup) whose overlapping triggers and contradictory rules made results
untrustworthy. The rules below are the single, resolved doctrine; when in
doubt, this file wins.

## Pick the mode

Read the user's intent, confirm the mode in one sentence, then read that
mode's reference file. Don't load mode files you aren't using.

| User intent sounds like | Mode | Read |
|---|---|---|
| "flag [client]'s tickets", "which can we close", weekly cleanup pass, "anything new to clean up" | **Flag** (default) | `references/mode-flag.md` |
| "clean up [owner]'s queue", "Marko has too many open tickets", duplicates, stale shells | **Queue cleanup** (a flag pass scoped to an owner's whole queue) | `references/mode-queue-cleanup.md` |
| "where are we with [client]", "what's actually done", QBR prep, hour burn, scope creep | **Full reconciliation** (engagement-level audit) | `references/mode-full-reconciliation.md` |
| "execute the closes", "close the approved ones", user has reviewed flags/proposal | **Close** | `references/mode-close.md` |

All modes share the evidence rules in `references/evidence-standards.md` —
read it whenever you're deciding whether something is "done."

When the request is ambiguous ("clean up Fisher's"), default to **Flag** and
say so — it's safe, and its output feeds every other mode. Never jump straight
to Close: closing requires a prior flag pass or proposal the human has
actually reviewed.

## Doctrine (resolved — these override anything you remember)

These rules exist because each one was learned from a real incident. They are
not style preferences.

1. **Flag first, close second, delete never.** Every evaluation writes
   recommendations (the four `ai__*` flag properties or a proposal report) for
   a human to review. Closes execute only in Close mode after per-bucket or
   per-ticket approval. This skill NEVER deletes a ticket — suspected
   duplicates are closed-as-duplicate with a pointer to the keeper, and any
   true deletion is a human action in the HubSpot UI. (A prefix-normalized
   dedup once mass-deleted 341 distinct tickets. That class of mistake must be
   structurally impossible, which is why deletion isn't in this skill at all.)
2. **Stage IDs are pipeline-specific.** Never assume `"4"` = Closed — that's
   only true in the Support pipeline. Before classifying or closing anything,
   pull `GET /crm/v3/pipelines/tickets` once and map each pipeline's stages by
   LABEL. (The Onboarding pipeline's "Completed Tickets" is `103557754`; an
   ID-only read shows it as open.)
3. **Duplicates match on the FULL subject** — prefix + description + date —
   plus the same associated company. Never a normalized/prefix-stripped
   version: stripping client codes collapses every client's "Weekly Client
   Success Meeting" into one false cluster.
4. **Identify clients by ASSOCIATED COMPANY, not subject prefix.** Subjects
   get mis-prefixed or unprefixed (Spectrum's WBS block had no `SPT -` prefix).
   Pull the ticket→company association to know the true client.
   The client roster itself is DERIVED live each run — never from a
   hand-maintained table (see `references/client-discovery.md`). New clients
   are picked up automatically; unknown or ambiguous codes are surfaced, not
   guessed.
5. **Credentials: never ask the user to paste a raw PAT into chat.** Verify
   client portals through Client Command's audited tools
   (`check_client_credential`, then `call_hubspot_as_client` with a mandatory,
   truthful `reason` on every call). If no stored credential exists, fall back
   to a PAT in the `CLIENT_HUBSPOT_TOKEN` env var; if neither is available,
   flag affected tickets `Needs Review` — don't silently skip and don't guess.
6. **Client portals are read-only during reconciliation.** GET only. All
   writes (flags, closes) happen on the QBS portal `20682069`. If a token
   turns out to be bound to an unexpected portal, stop.
7. **Source of truth depends on the question.** For whether something was
   BUILT, the live portal wins — it's ground truth for artifacts. For what was
   AGREED or intended (scope, decisions, who committed to what), the meeting
   record wins. A "completed on call" claim with no portal artifact is `Needs
   Review`, not done.
8. **Owner scoping.** Reconcile one owner's tickets at a time (default:
   Marko Ajder, owner ID `466155664`). Other owners' tickets are listed for
   the human, never flagged or modified. Confirm `hubspot_owner_id` per ticket.
9. **Staleness = `createdate`, never `hs_lastmodifieddate`** — workflows touch
   every ticket regularly, so last-modified is noise.
10. **Exclude internal pipelines** (label contains "internal", e.g. Quantum
    Internal `11057532`) from cleanup candidates — those hold time-tracking
    shells that are working as designed.
11. **The double-bill trap.** Before recommending any close as "done," search
    the client's CLOSED tickets for the same work under different wording. If
    it was already delivered and billed elsewhere, flag `Yes` but the reason
    must say "delivered under closed ticket [ID] — do not re-bill."
12. **Date fields get noon UTC.** When setting `closed_date` (or any date
    property), use 12:00 UTC on the intended day so the date reads the same in
    Chicago and Belgrade year-round. Never hand-compute timezone offsets —
    they change with DST.
13. **Engagements before merges.** Any ticket with calls/notes/emails/tasks
    attached must never lose them; if a duplicate-with-engagements needs
    consolidating, the human reassociates engagements first (Close mode
    explains how to propose this).
14. **Evidence is cited, not asserted.** Every flag reason and every close
    note names the specific artifact (ID, count, timestamp, creator), the
    meeting (date + quote), or the closed ticket it relies on. If you can't
    cite it, it's `Needs Review`.

## The four flag properties (QBS portal 20682069, TICKET object)

Every evaluation writes all four — they are the interface between AI
recommendation and human decision:

| Property | Type | Values |
|---|---|---|
| `ai__ticket_should_be_closed` | single-select | `Yes` / `No` / `Needs Review` |
| `ai__ticket_should_be_closed_reason` | text | evidence-citing explanation |
| `ai__ticket_clean_up_source_to_check` | multi-select (semicolon-joined) | `Email` / `Meeting` / `Client HubSpot Portal` / `Manually` / `Other` |
| `completed_on_client_call` | single-select | `Yes` / `No` |

The human filters on `ai__ticket_should_be_closed = Yes` in HubSpot, reviews
the reasons, and approves. Only then does Close mode touch
`hs_pipeline_stage`, `closed_date`, `hs_resolution`, `billable_`, or
`fulfillment_hours_` — flag writes never include those fields.

## Reference files

- `references/evidence-standards.md` — what counts as proof: the verb→source
  table, the three-check rule (existence / timestamp / attribution),
  meeting-completion detection, dedup and double-bill checks. Read for every
  mode.
- `references/mode-flag.md` — the flag pass: procedure, API writes, worked
  examples.
- `references/mode-queue-cleanup.md` — the five queue buckets (shells, meeting
  shells, extractor dupes, stale onboarding, other dupes) and weekly cadence.
- `references/mode-full-reconciliation.md` — the six-phase engagement audit:
  ticket inventory, portal verification, same-call hunt, meeting trace, gap
  analysis, hour burn.
- `references/mode-close.md` — executing approved closes safely: stage lookup,
  close payload, content notes, hours rules, post-close verification.
- `references/output_template.md` — the reconciliation report structure.
- `references/same_call_completion.md` — phrase library + rules for detecting
  work finished live on a call (highest-yield close category).
- `references/ticket_classification.md` — bucketing tickets found on a client
  company record.
- `references/portal_queries.md` — per-ticket-type verification queries
  against a client portal.
- `references/qbs_seats.md` — QBS staff seat/owner IDs and how to refresh them.
- `references/client-discovery.md` — deriving the active client list and
  3-letter codes live from ticket associations (no roster file). Read at the
  start of any pass that spans clients or names a client you haven't resolved.

## Related skills (route away, don't absorb)

- Creating or logging tickets, import spreadsheets, time tracking →
  `qbs-hubspot-ticketing`
- Full portal health audit with six-dimension scoring (prospects, QBRs) →
  `hubspot-audit`
- Client-portal API access mechanics and scopes → `qbs-hubspot-private-app`
