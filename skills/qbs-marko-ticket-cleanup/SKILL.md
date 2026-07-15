---
name: qbs-marko-ticket-cleanup
description: Audit and clean up Marko Ajder's open ticket queue in the QBS HubSpot portal (20682069). Triggers when the user asks about Marko's tickets, his open queue, his backlog, what should be closed for Marko, duplicate tickets owned by Marko, or stale Marko tickets. Also triggers on phrases like "clean up Marko's tickets", "what's open on Marko", "audit Marko's queue", "help Marko clean up", "Marko has too many open tickets", or any HubSpot ticket-cleanup request that names Marko. Supports both one-off audits ("show me what to close") and weekly cadence audits ("anything new this week to clean up"). Always produces a reviewable report before any close or delete action — write operations require explicit confirmation per ticket bucket.
---

# Marko Ticket Cleanup

## What this skill does

Pulls Marko Ajder's open tickets from QBS portal `20682069`, classifies them into cleanup buckets, produces an Excel report, and (after explicit user confirmation) executes the safe closes. Written for Marko specifically — owner ID `466155664`, with detection patterns tuned to QBS's actual ticket conventions (BackOffice shells, recurring meeting tickets, action-commitment dupes from Client Command, stale onboarding templates).

## When to use vs. when not to use

**USE this skill when:**
- User asks anything about Marko's open tickets, his queue, his backlog, or his ticket cleanup
- User says "what should Marko close," "clean up Marko's tickets," "Marko has too many tickets"
- Weekly check-in: "anything new in Marko's queue this week"
- After a known batch event (Client Command sync ran, suspect dupes were created)

**DO NOT use this skill when:**
- The user wants to audit a different owner's queue — this skill is Marko-specific by design. For other owners, build a generalized version or run the search manually.
- The user is working in a client portal — this skill targets QBS portal `20682069` only. Use `qbs-hubspot-private-app` for client portals.
- The user wants to create new tickets — use `qbs-hubspot-ticketing` instead.

## Critical rules

**Propose-then-execute, always.** This skill never closes or deletes tickets without an explicit "yes, execute" from the user, *per bucket*. Closing the wrong ticket is worse than leaving the wrong ticket open. The skill's job is to produce a clear proposal; the human's job is to authorize.

**Stage IDs are pipeline-specific — never assume `'4' = closed`.** The QBS portal has multiple ticket pipelines (Support, On-Boarding for HubSpot, Quantum Internal, Sales as a Service), each with its own stage IDs. Always look up the actual stage label via `/crm/v3/pipelines/tickets` before classifying. The first pass on this audit got it wrong by assuming stage `'4'` was always closed; in the Onboarding pipeline, stage `103557754` is "Completed Tickets" but reads as "open" by ID alone.

**Never use last-modified date as a staleness signal.** Workflows tick everything regularly, so `hs_lastmodifieddate` is useless for "has this ticket been forgotten." Use `createdate` instead.

**Engagements (calls/notes/emails/tasks/meetings) must be checked before delete.** The Sierra Structures cleanup found 7 of 49 dupe tickets had call records attached — losing those would be unacceptable. If a ticket has engagements, it gets the merge-then-delete path, not the bare-delete path.

**Internal-pipeline tickets are excluded from the audit entirely.** The "Quantum - Internal Pipeline" (and any future pipeline whose label contains "internal") holds time-tracking and meeting tickets that Marko logs hours against. These are working-as-designed; they should never be flagged as cleanup candidates. The exclusion is enforced in `_common.fetch_pipelines()` via the `EXCLUDED_PIPELINE_LABEL_FRAGMENTS` constant — add new fragments there if other internal pipelines appear.

**Token comes from `CLIENT_HUBSPOT_TOKEN` env var or is pasted by the user.** Never hardcode. The token is a Private App access token for portal `20682069`. If running this skill discovers the token is bound to a different portal, stop — that's a wrong-portal scenario.

## The five buckets

After many sessions of cleanup, Marko's open tickets fall into five recognizable patterns. Each bucket has a different cleanup recommendation:

| Bucket | Pattern | Recommendation |
|--------|---------|----------------|
| **A. Recurring time-tracking shells** | "QBS - Daily Client Email Support", "QBS - BackOffice (...)" — created daily as time logs | Close in bulk, no engagement check needed (these are shells) |
| **B. Recurring internal meeting shells** | "QBS - Weekly Internal Client Success Meeting", "Ticket Status/Review meeting" — batch-created for a year of recurring meetings | Close in bulk *if* no engagements; merge-then-close if engagements present |
| **C. Action-commitment duplicates** | Created by Client Command's commitment extractor running twice on the same meeting (often within a 24-hour window). E.g. yesterday's "SPT - Chase KeyPoint..." appearing on both Apr 27 and Apr 28 | Delete the dupe; keep the earlier one |
| **D. Stale onboarding template tickets** | "HubSpot On-Boarding [Client] - Sales - Confirm Client has Connected..." sitting open >180 days | Hand to Marko for review — close-as-Done vs close-as-Won't-Do is judgment-only |
| **E. Other duplicates** | Any other exact-match-after-prefix-stripping duplicates | Inspect individually before action |

Buckets A, B, and C can be cleaned in bulk after confirmation. Bucket D requires human judgment per ticket. Bucket E gets surfaced for review.

## Workflow

### Step 1 — Verify and pull data

Run `scripts/audit.py` (no args for full audit, or `--since YYYY-MM-DD` for weekly mode):

```bash
python3 scripts/audit.py                    # Full audit — all of Marko's open tickets
python3 scripts/audit.py --since 2026-04-21 # Weekly mode — only tickets created since
```

The script:
1. Verifies token works against portal `20682069` (errors if wrong portal)
2. Pulls all tickets owned by Marko (paginated, up to 5000)
3. Looks up actual stage labels from the pipeline definitions
4. Filters to truly open tickets (excludes "Closed", "Completed Tickets", and similar by label)
5. Classifies each open ticket into one of the five buckets
6. For Buckets A, B, C: checks engagements (calls/notes/emails/tasks/meetings) on each candidate
7. Writes the proposal to `/mnt/user-data/outputs/Marko_Cleanup_Proposal_YYYY-MM-DD.xlsx`

### Step 2 — Present the proposal

Read the Excel summary aloud to the user. For each bucket, state:
- How many tickets the bucket contains
- The recommended action (bulk close, merge+close, delete, or hand-off)
- How many in the bucket have engagements (i.e. require merge instead of bare close)
- A few example subjects so the user can sanity-check the bucket

**Then ask, per bucket, whether to proceed.** Don't ask "execute everything?" — ask one question per actionable bucket. Bucket D never goes through this skill's executor; tell the user to handle in HubSpot UI.

### Step 3 — Execute (only after confirmation)

Run `scripts/execute.py` with the bucket name and the proposal file:

```bash
python3 scripts/execute.py --proposal /mnt/user-data/outputs/Marko_Cleanup_Proposal_2026-04-28.xlsx --bucket A
python3 scripts/execute.py --proposal ... --bucket B
python3 scripts/execute.py --proposal ... --bucket C
```

The executor:
1. Re-reads the proposal Excel (no in-memory state from the audit)
2. For Bucket A and B (close): PATCHes each ticket to its pipeline's "Closed" stage
3. For Bucket B with engagements: reassociates engagements to the keeper, then deletes others
4. For Bucket C (delete): hard-deletes via DELETE
5. Logs every action to `/home/claude/marko_cleanup_log_YYYYMMDD_HHMM.csv` — ticket ID, action taken, response code, timestamp
6. Stops on first error and reports — does not continue blind

### Step 4 — Verify

After execute, the script re-pulls Marko's open count and reports the delta. If the delta doesn't match expectations (e.g., expected to close 44, only 41 closed), the user gets the discrepancy plus the log file path.

## Weekly cadence mode

When run with `--since`, the audit only flags:
- New duplicates introduced in that window (most often Bucket C — Client Command extraction artifacts)
- New time-tracking/meeting shells that already have a closed counterpart from prior weeks
- Tickets created in the window that already match a "looks completed" pattern

This is the right weekly check after Client Command sync runs. Aim for Monday-morning cadence, since most batch syncs run Sunday night.

## What this skill never does

- Closes tickets owned by anyone other than Marko (owner ID 466155664)
- Operates on closed tickets (read-only there is fine, but no skill-driven changes)
- Bulk-closes Bucket D (old onboarding templates) — these always need human judgment
- Modifies ticket associations to companies, deals, or contacts (engagement reassociation is the only association change made, and only in Bucket B's merge path)
- Touches custom properties or pipeline configurations

## See also

- `references/buckets.md` — full pattern definitions for each bucket, including the regexes used for classification
- `references/api-endpoints.md` — the specific HubSpot endpoints used and why
- `scripts/audit.py` — read-only audit that produces the proposal
- `scripts/execute.py` — write-side executor, runs only after explicit confirmation
- `scripts/_common.py` — shared HTTP client, owner/stage lookups, normalizers
