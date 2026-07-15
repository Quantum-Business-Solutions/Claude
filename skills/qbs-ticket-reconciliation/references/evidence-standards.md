# Evidence Standards — Tiers, Sources, and What Counts as Proof

Every mode uses these rules to decide whether a ticket's work is "done"; if a
mode file and this file ever disagree, this file wins. The core idea: every
verdict is graded by the strength of the evidence behind it, and the grade is
written into the reason so any human reading the flag knows exactly how much
to trust it. Shawn's history with automated cleanup is false "done" claims —
the tier system exists so that a wrong flag is at least an *honestly labeled*
wrong flag.

## The four tiers

| Tier | Name | Definition | Examples |
|---|---|---|---|
| **T1** | Direct artifact | An artifact observed by a query made **this pass**, passing all three checks (existence, timestamp, attribution) | Property returned 200 with createdAt in-window and QBS createdById; list with size 214; sent-email engagement to the named recipient; a closed ticket record covering the same work |
| **T2** | Documented record | A structured record created near the event by a system or human, but not the artifact itself | "Items Completed on Call" section of a meeting summary; work acknowledged as done in the *following* meeting; a dated deliverable note/file on the company record |
| **T3** | Uncorroborated claim | Someone said it happened | Transcript completion phrases with no portal match; Client Command `commitments[].status=completed` or `evidence_found=true` (both known unreliable); the ticket's own `content` notes |
| **T4** | Inference | Pattern reasoning with no record at all | "Tickets like this are usually done"; subject similarity; silence/absence of activity |

## Verdict rules (non-negotiable)

- **`Yes` requires T1** for anything with a buildable/sendable deliverable
  (portal artifact, email, document).
- **`Yes` on T2 is allowed only when the deliverable IS the record** —
  meetings held, decisions made, reviews walked through on a call. There is
  nothing else to check.
- **T3 alone ⇒ `Needs Review`, never `Yes`.** A claim is a lead, not a
  conclusion.
- **T4 alone ⇒ `No` or `Needs Review`.** Inference never closes a ticket.
- Multi-part subjects ("Build the object **and** notify Haley"): every
  component needs its own qualifying evidence; any component short ⇒
  `Needs Review` naming the missing piece.
- The tier is written as the first token of the reason: `[T1-portal]`,
  `[T2-meeting]`, `[T3-claim-only]`, `[T4-inference]`. Reason style:
  `references/mode-flag.md`.

## Verb → evidence source map

Parse the leading verb/intent of the subject; it tells you where "done" would
leave a trace, and it populates `ai__ticket_clean_up_source_to_check`.

| Subject verb | "Done" means | Check | `source_to_check` |
|---|---|---|---|
| build, create, configure, set up, automate, import, backfill, add property/report/workflow/object | Artifact exists in client portal | Live portal (three-check) | `Client HubSpot Portal` |
| send, notify, email, deliver, share, follow up (to a person) | Message actually went out | Logged email engagements, Outlook trail | `Email` (+`Meeting` if it was a verbal commit) |
| test, review, validate, demo, walk through, present | Happened on a call and/or shows in portal | Meeting record + portal | `Meeting`;`Client HubSpot Portal` |
| investigate, scope, research, evaluate, recommend | A finding was delivered | Meeting or email deliverable trail | `Meeting` or `Email` |
| discuss, sync, meet, call, kickoff | Meeting occurred | Meeting record | `Meeting` |
| schedule, reschedule, update invite | Calendar action happened | Calendar/email | `Email` or `Manually` |
| monitor, watch, keep tracking | Open-ended — no completion state exists | — | `Manually`, verdict `No` ("no completion criteria") |

## The three-check rule (what makes portal evidence T1)

Every artifact match must pass all three before it counts as T1; a match that
fails any check is a *finding* (report it) but not close evidence:

1. **Existence** — the artifact is returned by a query made this pass. Record
   its ID. Existence alone isn't done: zero population, zero fires, or zero
   members is a data-less shell → `PARTIAL`, surface it.
2. **Timestamp** — `createdAt` falls inside the engagement window (first QBS
   ticket `createdate` or SOW start → today). Pre-dating the window ⇒
   pre-existing client work being mistaken for QBS delivery. Post-dating with
   no explanation ⇒ verify harder.
3. **Attribution** — `createdById` resolves to a QBS seat **in that portal's
   own user list** (see `references/qbs-facts.md` — owner IDs and client-portal
   user IDs are different systems). Client-built artifacts during the
   engagement are context, not billable QBS delivery, and never close evidence.

Query patterns per artifact type: `references/portal_queries.md`.

## Source-of-truth doctrine

- **Portal wins for BUILT.** If a transcript says "already built" and the
  portal has no matching artifact, the portal is right until proven otherwise:
  `Needs Review`, reason "[T3-claim-only] completion claimed on [date] call
  ('...quote...') but no matching artifact found in portal [ID] — claim may be
  aspirational, or built in a system not checked (n8n/Zapier)."
- **Meeting record wins for AGREED.** Scope, decisions, priorities, and "the
  client said skip it" live in the meeting record, and a portal artifact can't
  overrule an agreement (an artifact built against a descoped item is a gap
  finding, not a close).
- **Conflicts are findings.** Never average them away. State both sources and
  both dates in the reason and the report.
- "Agreed in principle" / "proposed and accepted" on a call completes the
  **decision** ticket, not the **build** ticket. Do not let one meeting line
  close both.

## Meeting evidence — Zoom transcripts + Client Command intelligence

Meeting evidence comes from two complementary sources: Zoom transcripts are
the actual call recall; Client Command meeting intelligence is the structured
commitment layer on top.

### Zoom transcript flow (Zoom for Claude connector)

1. **`search_meetings`** — find the client's call by company name + date
   window (align to the ticket's creation/meeting date). Returns meeting IDs
   and metadata.
2. **`get_meeting_assets`** / **`get_recording_resource`** — pull the
   transcript for the matched meeting.
3. **Search the transcript** for the commitment in the ticket subject — was it
   discussed, and was it stated as *done* (past tense, "we already set that
   up") or *promised* (future tense, "I'll get that built")? A future-tense
   promise on the call is NOT completion — it's the open ticket.

A located Zoom transcript confirming completion strengthens the tier: it is
T2 evidence on its own, and it corroborates a portal artifact into a solid
same-call T1. If no Zoom transcript can be located for the relevant call,
fall back to Client Command meeting intelligence, note in the reason that no
transcript was found, and degrade confidence accordingly — a meeting-verb
ticket with no transcript is `Needs Review`, not `Yes`.

### Client Command meeting intelligence (structured layer)

A meeting summary lists **promises**, not completions. Client Command
summaries (`get_meeting_intelligence`) have sections that mean different
things:

1. **"✅ Items Completed on Call"** → finished/agreed live (T2). For a
   matching ticket: `completed_on_client_call = Yes`. Caveat: "agreed in
   principle" is a *decision*, not a build — see source-of-truth above.
2. **"🎯 Action Items / Potential Tickets"** → forward promises. Never mark
   complete from this section alone.
3. **"📅 Expected Agenda for Next Meeting"** → still open → `No`.
4. **`commitments[].evidence_found`** is known-unreliable — treat it as T3;
   always verify another source yourself.

**The reliable completion test:** a promise in meeting N acknowledged as done
in meeting N+1, OR listed under "Items Completed on Call", OR confirmed in a
Zoom transcript (all T2), OR verifiable in the live portal (T1) → `Yes` per
the verdict rules. Reappears in the next agenda → `No`. Claimed done but no
portal artifact for build work → `Needs Review`. Prefer the most recent
meeting's view.

## Same-call completion detection (highest-yield, highest-risk)

Marko often builds the thing live on the call and the ticket never gets
closed. These are the fastest hours to bank — and the easiest place to
manufacture a false `Yes`. Promotion to `Yes` with
`completed_on_client_call = Yes` requires **all three**:

1. **Transcript/summary signal** — "Items Completed on Call" names it, or the
   transcript contains completion language matched to the ticket's subject
   keywords. Phrase library and false-positive guards:
   `references/same_call_completion.md`.
2. **Portal artifact** matching the subject, created inside the canonical
   same-call window (below).
3. **QBS-seat attribution** on the artifact (three-check rule).

Signal 1 without 2 ⇒ T3 ⇒ `Needs Review` with the quote — either a false
claim (real, and Shawn wants to know) or work done in an unchecked system.

### The canonical same-call artifact window (defined here and ONLY here)

- **Primary window:** meeting start **−24h** to meeting end **+24h**. An
  artifact `createdAt` inside this window, with signals 1 and 3, supports
  `completed_on_client_call = Yes` (the −24h side covers "I already did that
  yesterday" pre-builds acknowledged live).
- **Widened window:** if nothing lands in the primary window, widen ONCE to
  **±7 days** and say so explicitly in the reason ("artifact found in widened
  ±7d window"). For widened-window matches, `completed_on_client_call` is
  `Yes` only if the transcript confirms live completion on the call itself;
  otherwise the verdict can still be `Yes` on the portal evidence, but
  `completed_on_client_call = No` — done, just not provably on the call.

Every other file that needs the window points here. Do not restate the
numbers elsewhere — divergent copies of this rule are how the legacy skills
contradicted each other.

Fulfillment hours on approved same-call closes: the actual build time
referenced on the call (typically 0.25 hr). Never inflate; never set hours
during flagging at all.

## The double-bill check (mandatory before any `Yes`)

Search the same company's **closed** tickets for work matching this open
ticket (keyword search on subject terms + human-readable comparison).
Auto-created meeting action items frequently sit open while the identical
work was executed and billed under a differently-worded closed ticket — on
Fisher's, 8 open reporting tickets were already billed under closed tickets.
If a match is found, the verdict is `Yes` but the reason MUST contain the
literal phrase **"delivered under closed ticket [ID] — do not re-bill."** so
the human closing it cannot miss the billing implication. Double-bill catches
are excluded from bulk approval and always route to Shawn's billing review.
This check is why `Yes` flags can be trusted to be *safe to close*, not just
*probably done*.

## Duplicate detection

Real duplicates match on the FULL subject (prefix + description + date) AND
the same associated company — doctrine #3 in SKILL.md; never a
prefix-stripped or normalized subject. The classic true-dupe source is Client
Command's commitment extractor running twice on the same meeting within ~24h.
Flag the later one as duplicate-of-[earlier ID]; never delete. Engagement
checks and bucket handling: `references/mode-queue-cleanup.md`.

## Uncertainty language

Reasons state what was and wasn't checked, in plain words:

- Good: "[T1-portal] Custom object form_leads (2-230043398) exists, 430
  records, created 2026-03-02 by QBS seat 12048713; no closed ticket covers
  this work (searched 41 closed)."
- Good: "[T2-meeting] Acknowledged as delivered in 6/12 call ('the report
  Haley asked for is in her inbox'); NO sent-email engagement found to confirm
  — if closing, confirm with Haley."
- Bad: "Work appears complete." (No tier, no evidence, no query, indefensible.)

If a source could not be reached (no credential, no transcript), the reason
names the gap and `source_to_check` names what a human should check. See
`references/failure-modes.md`.

## Optional future schema (do NOT create now)

A dedicated `ai__ticket_close_confidence` select property and a
`Zoom Transcript` option on the source multi-select would make the tier
filterable in HubSpot. Both are schema migrations; the tier-in-reason prefix
covers the need without touching the schema. If Shawn ever wants them, that
is a deliberate one-time property change — never something a reconciliation
pass creates on the fly.
