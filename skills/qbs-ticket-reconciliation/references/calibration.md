# Calibration — Scoring the Last Pass, Tightening This One

Load at the start of every pass that will write flags (the readback), and
again when producing the report. The skill measures its own track record
every pass and adjusts. This is the difference between "an assistant that
claims things" and "an employee whose judgment you've watched be right" —
trust is earned from a visible accept/overturn record, not asserted.

## Scoring the last pass

Calibration is computed from **live portal state**, so it needs no fragile
side-store:

1. From the most recent pass note on the company record (see
   `references/mode-close.md`, audit trail) or snapshot note (see
   `references/memory.md`), get the list of ticket IDs flagged `Yes` and
   `Needs Review` last pass. If no pass note exists (first run, or notes
   purged), fall back to querying tickets where `ai__ticket_should_be_closed`
   has any value and treat results as "prior flags, pass date unknown" — say
   so in the report rather than presenting them as a scored history.
2. For each prior `Yes`, classify its fate:
   - **Accepted** — ticket has since moved to a closed-by-label stage.
   - **Overturned** — human flipped the flag to `No`/`Needs Review`, or edited
     the reason to disagree, or the ticket is open with evidence the human
     explicitly rejected.
   - **Pending** — still open, flags untouched (the human hasn't reviewed yet —
     this is backlog, not disagreement; never count pending as accepted).
3. Score: `overturn rate = overturned / (accepted + overturned)`. Also note
   how many `Needs Review` flags the human resolved and in which direction —
   if humans keep resolving a category of Needs Review to Yes, the rules may
   be too conservative there (report it; do not silently loosen).

## Tightening rules

| Last-pass overturn rate | This pass's posture |
|---|---|
| 0–10% | Normal rules. |
| >10–25% | Tighten: T2-based `Yes` verdicts demote to `Needs Review`; state in the report which tickets were demoted by calibration. |
| >25% | Tighten hard: only T1 with all three checks produces `Yes`; open the report with the overturn list and ask the human what pattern they were rejecting — encode the answer into the next pass's notes. |

Loosening never happens automatically. If calibration suggests the rules are
too strict, that is a recommendation in the report for Shawn to approve,
because the cost asymmetry is absolute: a too-cautious flag wastes a minute
of review; a too-eager close double-bills a client or erases a record of work.

## Reporting calibration

The report opens with the calibration snapshot (see
`references/output_template.md`):

```
Last pass (2026-07-01): 14 Yes flags → 11 accepted, 1 overturned, 2 pending.
Overturn rate 8% → normal rules this pass.
Overturned: 4519... ("build" claimed done; human found workflow disabled) — this pass,
enabled-state is checked before any workflow Yes (already covered by portal_queries).
```

Report the hit rate **per verdict×tier cell**, not just overall — e.g.
"12/12 Yes/T1 closed by human; 3/7 Yes/T3 closed" — because the cells earn
trust at different speeds, and the per-cell record is what tells Shawn which
cells he can review quickly and which still need scrutiny.

Every overturned flag gets a one-line root cause and, where the miss reveals
a rule gap, the adjustment made. Overturns are the most valuable data the
skill receives — surface them prominently, never bury them.
