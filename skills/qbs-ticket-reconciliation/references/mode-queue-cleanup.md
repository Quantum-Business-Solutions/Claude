# Mode: Queue Cleanup

A flag pass scoped to one owner's ENTIRE open queue (all clients), tuned to
the recurring patterns that clog it. Default owner: Marko Ajder
(`466155664`); works for any owner by swapping the ID. Output is a proposal
report + flags — execution goes through Close mode per bucket.

## Setup

1. Pull all open tickets for the owner (paginate; queues run 500+).
2. Look up every pipeline's stages by LABEL via `GET /crm/v3/pipelines/tickets`
   and filter to truly open (exclude "Closed", "Completed Tickets", and
   similar by label — never by ID).
3. Exclude pipelines whose label contains "internal" — time-tracking and
   meeting-hour shells there are working as designed.
4. Staleness comes from `createdate` (workflows churn `hs_lastmodifieddate`).

## The five buckets

| Bucket | Pattern | Recommendation |
|---|---|---|
| **A. Recurring time-tracking shells** | "QBS - Daily Client Email Support", "QBS - BackOffice (...)" — created daily as time logs | Flag for bulk close (no engagement check needed — they're shells) |
| **B. Recurring internal meeting shells** | "QBS - Weekly Internal Client Success Meeting" batch-created for a year ahead | Flag for bulk close if no engagements; if engagements exist, propose merge-then-close (human reassociates engagements first) |
| **C. Extractor duplicates** | Client Command's commitment extractor ran twice on one meeting (~24h apart), same full subject + company | Flag the LATER one "duplicate of [earlier ID]" — close as duplicate, never delete |
| **D. Stale onboarding templates** | "HubSpot On-Boarding [Client] - ..." open >180 days | Hand to the owner for judgment — never bulk-anything |
| **E. Other duplicates** | Full-subject + same-company matches not explained by C | Inspect individually; flag with the specific keeper named |

Bucket checks that matter:
- **Engagement check before any merge/close proposal for B, C, E:** pull
  calls/notes/emails/tasks/meetings associations. A "duplicate" with call
  records attached is not safely closable until a human moves those
  engagements to the keeper (7 of 49 Sierra dupes had calls attached).
- **Future-dated meeting shells are not cleanup candidates** — they close
  naturally as meetings occur.
- Dedup rule is doctrine #3: FULL subject + same associated company. Never
  prefix-stripped.

## Present the proposal

For each bucket: count, recommended action, how many have engagements, and a
few example subjects so the human can sanity-check. Then ask **per bucket**
whether to proceed — never "execute everything?". Bucket D is never executed
by this skill; it goes to the owner as a review list.

Write the four flag properties on every evaluated ticket as you go, so the
proposal is also filterable in HubSpot.

## Weekly cadence mode

When asked for "anything new this week," limit to tickets created since the
last pass and flag only: new extractor duplicates (bucket C — most common
after Sunday-night Client Command syncs), new shells that already have a
closed counterpart, and new tickets matching a looks-completed pattern.
Monday morning is the right cadence. Keep a dated summary so week-over-week
deltas are visible.

## Executing

After per-bucket approval, follow `references/mode-close.md`. Reminders that
have burned us: close to each ticket's OWN pipeline's closed stage (by
label); closed-as-duplicate notes must name the keeper ticket ID; nothing is
ever deleted by this skill.
