# Mode: Close

Executes closes the human has ALREADY approved — from a reviewed flag pass
(`ai__ticket_should_be_closed = Yes`), an approved queue-cleanup bucket, or an
approved reconciliation report. If there's no prior reviewed proposal, stop
and run a flag pass first.

## Preconditions

1. The user has seen per-ticket (or per-bucket) evidence and said yes to this
   specific set. "Close whatever you think is done" is not approval — produce
   the proposal first.
2. Confirm each ticket's owner is the reconciled owner; skip anything else.
3. Re-read the flags/proposal fresh from HubSpot at execution time — don't
   trust in-memory state from an earlier pass.

## Stage lookup (do this first, every time)

`GET /crm/v3/pipelines/tickets` once; build a map of pipeline → closed-stage
ID **by label** ("Closed", "Completed Tickets", ...). Close each ticket to its
own pipeline's closed stage. Never reuse a stage ID across pipelines and never
assume `"4"`.

## The close payload

PATCH each ticket (or batch ≤100 via `POST /crm/v3/objects/tickets/batch/update`)
on the QBS portal `20682069`:

- `hs_pipeline_stage`: the looked-up closed-stage ID for THIS ticket's pipeline
- `closed_date`: intended close date at **12:00 UTC** (doctrine #12)
- `hs_resolution`: `"Work Completed"` (or `"Duplicate"` when closing as
  duplicate — the note must name the keeper ticket ID)
- `content` addendum — the audit trail, structured:
  - what was verified (artifact IDs/names, counts, `createdAt`, `createdById`)
  - meeting reference for done-on-call closes: date, participants, and the
    transcript snippet showing completion (required, not optional)
  - "duplicate of [ID]" for duplicate closes
  - "delivered under closed ticket [ID] — not re-billed" for double-bill catches

## Hours rules

- Same-call completions: use the actual build time referenced in the meeting
  (often 5–15 min = 0.25 hr).
- Verify-only closes (work pre-dated this session): leave `fulfillment_hours_`
  as-is — don't inflate.
- Shells (queue buckets A/B): no hours; they're time-log artifacts, not work.
- If existing `fulfillment_hours_` disagrees with the evidence (hours billed
  for unverifiable work), flag it and skip the close — don't quietly close.

## What never closes

- **BLOCKED tickets** — update `content` with the blocker + last-ping date
  instead; they need follow-up, not resolution.
- Other owners' tickets, internal-pipeline tickets, future-dated meeting
  shells, anything whose flag is `No`/`Needs Review`, and any
  duplicate-with-engagements until a human has reassociated the engagements
  to the keeper.
- Nothing is ever DELETED. Not in any bucket, not for "obvious" dupes.

## Burn-notice check (engagement closes)

If this close batch pushes the engagement's consumed hours past 75% of the
SOW commitment, pause and surface it BEFORE executing so the user can decide
about the Scope Burn Notice (see mode-full-reconciliation, hour burn phase).

## Execute and verify

- Stop on first error and report — don't continue blind.
- Log every action (ticket ID, action, response code, timestamp) to a CSV in
  the working directory and link it in your summary.
- Afterward, re-pull the owner's open count and report the delta. If it
  doesn't match expectations (approved 44, closed 41), say exactly which
  tickets didn't close and why.
- Clear or downgrade the `ai__*` flags on closed tickets is NOT needed —
  closed tickets drop out of the open-queue filters naturally.
