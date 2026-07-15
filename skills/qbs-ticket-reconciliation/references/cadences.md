# Cadences — the rhythm that keeps the queue trustworthy

Load when the run is a standing cadence (weekly / monthly / quarterly), a
catch-up after time away, or when the user asks for reconciliation without
naming a mode. Every prior attempt at ticket cleanup decayed because it was
event-driven: someone noticed the queue was bad, ran a heroic one-off, and six
weeks later it was bad again. This skill fixes that the way a good admin
employee does — with standing cadences, a snapshot after every run so the next
run has memory, and a catch-up protocol so a gap in the rhythm degrades
gracefully instead of resetting to zero.

Every run, regardless of mode, ends with the same three artifacts:
1. **State of the Queue report** (with deltas vs. the last snapshot) — `references/memory.md`
2. **Snapshot note** written to HubSpot — `references/memory.md`
3. **Decision log entries** for any new human rulings — `references/memory.md`

If the user asks for reconciliation without naming a mode, pick the mode that matches
scope (one client → monthly sweep; the whole queue → weekly pass; "before QBR" →
quarterly), say which mode you're running, and note when the last run of that mode was
(from snapshot notes). If a cadence was missed, say so plainly — "last weekly pass was
19 days ago" — and widen the window to cover the gap. Never silently skip the gap.

---

## Weekly queue pass (Mondays — after Client Command's Sunday-night sync)

Purpose: catch problems while they're one week old, not one quarter old. Scope: the
whole Marko-owned open queue, but only *shallow* checks — no client-portal verification.
Budget: the output should take Shawn ~15 minutes to review. Mechanics:
`references/mode-queue-cleanup.md`.

Checklist (in order, never skip — if a step can't run, report it as skipped-with-reason):

1. Load last weekly snapshot; compute the window (last snapshot date → today).
2. Pull open tickets created in the window (owner-scoped, internal pipelines excluded,
   stage labels mapped live).
3. **Fresh duplicate scan** across the window + existing open queue: full subject + same
   associated company. Client Command's commitment extractor sometimes double-fires
   within ~24h of a meeting — pairs created within 24h of each other on the same company
   are the classic signature. Check engagements on every pair before proposing anything.
4. **Aging alerts**: action-item tickets >14 days past due (by `createdate`-anchored due
   dates, not lastmodified); anything crossing 30/60/90-day age lines this week.
5. **Pattern flags only**: obvious shells with a closed counterpart, dupes, tickets whose
   subject matches a "completed" pattern from the recent meeting summaries. Flag them
   (all four properties); leave evidence-heavy calls for the monthly sweep.
6. **Other-owner report**: list (never touch) new tickets owned by others that look like
   cleanup candidates.
7. Produce State of the Queue with week-over-week deltas; write snapshot; ask per-bucket
   approval questions for anything flagged Yes.

## Monthly per-client sweep

Purpose: one client done properly. Rotate so every active client gets swept roughly
monthly — the snapshot notes tell you which client is most overdue; propose that one if
the user doesn't name a client. Mechanics: `references/mode-flag.md`.

Checklist:

1. Resolve the client by associated company (live discovery —
   `references/client-discovery.md`). Load the client's snapshot + decision log.
2. Confirm portal credential (`check_client_credential`); state up front whether portal
   verification is available this run.
3. Pull ALL open tickets associated to the company; classify (work / shells / action
   items / other-owner); pull the client's CLOSED tickets for the double-bill check.
4. Pull recent meeting intelligence and Zoom transcripts for the engagement window.
5. Evaluate every open work ticket with the full evidence procedure
   (`references/evidence-standards.md`), including the same-call completion hunt on
   everything still unexplained.
6. **Inverse gap check**: portal artifacts created in the engagement window with no
   matching ticket (scope creep or off-ticket work → Shawn); meeting action items that
   never became tickets; concerns raised in 3+ meetings with no deliverable (→ client
   chase or Shawn).
7. Flags, report, escalations, per-bucket approvals, snapshot, decision-log updates.

## Quarterly full reconciliation (before QBRs)

Purpose: the numbers Shawn walks into a QBR with must be defensible. Everything in the
monthly sweep, for the named client (or each QBR-bound client), plus
(`references/mode-full-reconciliation.md`):

1. **Meeting trace on every close candidate**: the originating discussion — 2–3
   transcript sentences, date, attendees — goes into the reason/report. A close Shawn
   can't explain to the client isn't ready.
2. **Hour-burn vs. SOW**: sum `fulfillment_hours_` across all engagement tickets (open +
   closed) against the current SOW's prepaid commitment (fetch the SOW terms live from
   Client Command / the deal record — never assume last quarter's tiers). Flag the burn
   band and whether the SOW's burn-notice threshold is crossed — or *would be crossed by
   the proposed closes*. That call is Shawn's, made before execution, never after.
3. **Decision-log review**: rulings older than two quarters get re-listed for
   reaffirm/expire — decisions should be durable, not immortal.
4. Offer (don't assume) a client-facing status version of the report with internal items
   (gaps, blockers on QBS side, billing flags) stripped.

## Catch-up mode ("I'm back after 6 weeks — where are things?")

The rhythm broke; the job is re-orientation, not a guilt trip and not a giant blind run.

1. Find the latest snapshot notes (all scopes). Report: when each cadence last ran, what
   was pending approval then, what rulings were logged.
2. Pull current queue counts and compute deltas vs. those snapshots — "open Marko tickets
   went 84 → 117; 41 created in the gap; 3 clients had meetings with completed-on-call
   items nobody flagged."
3. Report any approved-but-unexecuted closes from the last run (they'll show as flagged
   Yes but still open) — approvals expire between runs, so re-confirm before executing;
   evidence may be six weeks stale.
4. Propose a recovery order: weekly pass first (cheap, catches dupes), then monthly
   sweeps for the most-overdue clients. Let the human pick; run what's picked.

## Proactivity rules (be the employee who notices)

- Whenever another QBS conversation reveals evidence relevant to open tickets (a meeting
  recap says something shipped, an email confirms delivery), suggest — once, briefly —
  running a targeted flag pass on that client. Don't nag; note it and move on.
- If a weekly pass finds zero issues, say so and show the deltas anyway. "Nothing to do"
  is a finding that builds trust; an empty silence is not.
- If the same escalation to Marko or the client repeats three runs in a row, raise it to
  Shawn with the history attached instead of repeating it a fourth time.

## Escalation routing (who gets what — decide, don't dump)

| Goes to | What | Why |
|---|---|---|
| **Marko** | Stale onboarding templates (done vs. won't-do), ambiguous build evidence, partial builds (artifact exists, no data flowing), mystery-seat attribution on builds | Implementation judgment |
| **Shawn** | Double-bill catches, hours logged with no verifiable artifact, burn crossing the SOW notice threshold, untracked portal work (change-order candidates), any `fulfillment_hours_` question | Billing and money decisions |
| **Client chase** | Tickets blocked on client action >14 days, concerns raised in 3+ meetings with no deliverable | Needs comms, not closes |

Escalations carry a one-line ask each ("Marko: ticket 4312… — property exists, 0/1,268
populated — finish or descope?"). Repeat escalations reference the prior ask and its date.
