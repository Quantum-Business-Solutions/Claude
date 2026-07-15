# Same-Call Completion Detection

Many QBS tickets get resolved during the meeting where they were raised, but never get marked closed because the implementer (usually Marko) is still live on the call. Finding these is the single highest-yield part of reconciliation — they're hours that should already be banked but are silently sitting in "open."

Load this file during the same-call hunt (Flag step 5, Full Reconciliation
Phase 3.5). The promotion test (three signals) and the canonical artifact
time window are defined in `references/evidence-standards.md` — this file is
the phrase library and the false-positive guards.

## Why this happens

- Marko shares screen, builds the property/list/workflow live during the call
- Meeting ends, ticket is still technically open
- No one closes it because the moment passes and attention shifts to the next thing
- Weeks later, the ticket looks stale in the open count

This pattern is most common on:

- Simple property adds ("can you create a field for X?")
- Quick list rebuilds or filter fixes
- Small workflow tweaks
- Field renames
- Tasks bundled into a single action item but split across multiple tickets

## Detection approach

A same-call completion requires three signals aligned (full rules and the
window definition: `references/evidence-standards.md`):

1. **Transcript language** suggesting in-call completion (phrase library below)
2. **Portal artifact** matching the ticket subject, created within the canonical same-call window
3. **QBS-seat attribution** on that artifact (resolved in the client portal's own user list)

If any one is missing, don't promote to `🟢 DONE-ON-CALL` — flag as ambiguous instead.

## Phrase library

Group A: "I'm doing it now" (in-meeting active build)

- "Let me do that right now"
- "I'll do that real quick"
- "Give me a second, I'll set that up"
- "Let me add that now"
- "I'm going to create that"
- "Let me just go ahead and build that"
- "One moment, I'll get that going"
- "Alright, creating that now"
- "I'll just fix that"

Group B: "Already done before the call" (pre-built)

- "I already did that"
- "That's already built"
- "Already in place"
- "Already set up"
- "Already live"
- "I got that built yesterday"
- "Already pushed that"
- "That's handled"
- "Already taken care of"

Group C: Completion confirmation within the call

- "Done"
- "That's done"
- "Set"
- "All set"
- "There we go"
- "Okay, that's built"
- "Perfect, that's in"
- "Okay, created"
- "Just saved it"
- "That's saved"

Group D: Ambiguous / needs portal check

- "I'll get that going"
- "I'll do that after the call"
- "Will do"
- "I'll handle it"
- "Noted"
- "Good to go on my end"

Group D phrases mean the work was promised but not necessarily done — always require a portal artifact with matching timestamp before promoting.

## Matching phrases to tickets

The transcript snippet won't mention the ticket ID. You're matching on subject keywords.

Ticket subject: "Create dropdown call outcome properties"
Transcript keywords to search: "call outcome", "dropdown", "call outcome property", "outcome field"

Be generous with near-matches — Marko often paraphrases ticket subjects when speaking.

When a match hits:

1. Extract the full exchange (usually 3–6 lines around the match, enough to get the context)
2. Note the timestamp or time offset within the meeting
3. Check the portal for an artifact created within the canonical same-call window (`references/evidence-standards.md`)
4. Compare artifact subject/name against ticket subject for similarity
5. If all three signals align → `🟢 DONE-ON-CALL`

## False-positive guardrails

Watch for these patterns that LOOK like completion but aren't:

- **Forward-looking "done"** — "That'll be done by Friday" is not same-call completion
- **Completion of a different task** — Marko might say "I just finished X" referring to a different ticket entirely. Always cross-check the subject.
- **Client saying "done"** — if the client (not Marko) says "done," the work may be on the client's side (e.g., they sent the file, uploaded the CSV). That's not a QBS deliverable being completed.
- **Hypothetical** — "So once I build that, it'll be done" is aspirational, not a completion signal.

When in doubt, don't promote. Flag as ambiguous and let the user decide.

## The ambiguous bucket

If a transcript shows completion language but no portal artifact matches, flag for review with the specific quote. Don't guess. Possible explanations:

- **Marko said he'd build it but didn't** — this is real. Surface to Shawn for follow-up.
- **Marko built it but outside the expected time window** — maybe he got distracted, built it days later. Apply the one-time widened-window retry defined in `references/evidence-standards.md` (and note it in the reason).
- **Marko built it in a system this skill isn't checking** — e.g., the work is in n8n or Zapier, not HubSpot. Evidence must come from a system you can actually read (integration logs, an API you have access to); if you can't verify it yourself, note as "check other systems" → `Needs Review`.
- **Completion phrase was about something else entirely** — false positive, move on.

## Output example

Good same-call detection output for the report:

```
Ticket 44462734161 — Create dropdown call outcome properties
Meeting: 4/15/2026 SMP Weekly (Zoom meeting ID ec47913d...)
Transcript snippet (min 23–25):
  Marko: "Let me add the call outcome dropdown right now while we're here."
  Jesse: "Great."
  Marko: "Done, that's saved."

Portal evidence: property `call_outcome` (enumeration, 6 options) exists in
client portal 243570690, createdAt 2026-04-15 14:47 — inside the canonical
same-call window for the 2:00–2:30 PM meeting.
Attribution: createdById 12048713 in the client portal → resolved via that
portal's /crm/v3/owners to marko@thequantumleap.business — QBS seat ✓
(client-portal user IDs are resolved per engagement; never quote a QBS-portal
owner ID as client-portal attribution — see qbs-facts.md)

Status: 🟢 DONE-ON-CALL — recommend close with 0.25 hr fulfillment
```

Bad output (don't close on this kind of match):

```
Ticket 43258932571 — Build re-engagement sequences by product type
Meeting: 3/11/2026 SMP Weekly
Transcript snippet:
  Marko: "Yeah, we'll get that built after the campaigns are ready"

Portal evidence: 0 marketing emails exist in portal
Status: 🔴 OPEN — forward-looking, no completion, no artifact
```
