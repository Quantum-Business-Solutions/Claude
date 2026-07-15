# Evidence Standards

What counts as proof that a ticket's work is done. Every mode uses these
rules; if a mode file and this file ever disagree, this file wins.

## The verb in the subject picks the evidence source

Parse the leading verb/intent of the ticket subject, then check that source.

| Ticket language | What "done" means | Check | `source_to_check` |
|---|---|---|---|
| build, create, configure, set up, automate, import, backfill, clean up, update [in HubSpot], add property/report/dashboard/workflow/object | Artifact exists in the client's portal | Live client portal | `Client HubSpot Portal` |
| send, notify, nudge, email, deliver, share, reach out, follow up, provide [to a person] | The message actually went out | Outlook / logged email engagements | `Email` (+ `Meeting` if verbal commit) |
| test, review, validate, walk through, demo, present | It happened on a call / in the portal | Meeting transcript + portal | `Meeting`, often `Client HubSpot Portal` |
| investigate, scope, explore, research, evaluate, recommend, propose | A finding was delivered | Meeting or email deliverable trail | `Meeting` or `Email` |
| discuss, sync, meet, call, kickoff | The meeting occurred | Meeting transcript | `Meeting` |
| schedule, update invite, reschedule | Calendar/admin action | Calendar/email | `Email` or `Manually` |
| monitor, watch, keep an eye on, continue to track | Open-ended; rarely closeable | — | `Manually` → usually `No` or `Needs Review` |

Multiple verbs ("Build the object **and** notify Haley") → check every
component; `Yes` only if all are satisfied, otherwise `Needs Review` naming
the missing piece.

## The three-check rule (for portal artifacts)

Every artifact match must pass all three; a match that fails timestamp or
attribution gets flagged, never counted:

1. **Existence** — the property/workflow/list exists and matches the ticket's
   subject keywords. Existence alone isn't done: zero population, zero fires,
   or zero members is a data-less shell → `PARTIAL`, surface it.
2. **Timestamp** — `createdAt` falls inside the engagement window. Pre-dates
   engagement start → pre-existing client work. Long after the ticket with no
   explanation → verify harder.
3. **Attribution** — `createdById` resolves to a QBS seat
   (`references/qbs_seats.md`). Client-built artifacts during the engagement
   are useful context but not billable QBS delivery, and never close evidence.

## Meeting-completion detection

A meeting summary lists **promises**, not completions. Client Command
summaries (`get_meeting_intelligence`) have sections that mean different
things:

1. **"✅ Items Completed on Call"** → finished/agreed live. For a matching
   ticket: `completed_on_client_call = Yes`. Caveat: "agreed in principle" is
   a *decision*, not a build — mark the discussion ticket complete, not the
   build ticket.
2. **"🎯 Action Items / Potential Tickets"** → forward promises. Never mark
   complete from this section alone.
3. **"📅 Expected Agenda for Next Meeting"** → still open → `No`.
4. **`commitments[].evidence_found`** is known-unreliable — `false` means
   Client Command hasn't confirmed it; always verify another source yourself.

**The reliable completion test:** a promise in meeting N acknowledged as done
in meeting N+1, OR listed under "Items Completed on Call", OR verifiable in
the live portal → `Yes`. Reappears in the next agenda → `No`. Marked
completed-on-call but no portal artifact (for build work) → `Needs Review`.

Prefer the most recent meeting's view. For built artifacts the portal is
ground truth; for scope/decisions/commitments the meeting record is. See
`references/same_call_completion.md` for the transcript phrase library and
the time-window rules (canonical artifact window: meeting start to meeting
end + 24h; widen to ±7 days only when explicitly retrying an ambiguous case,
and say so in the reason).

## Duplicate detection

Real duplicates match on the FULL subject (prefix + description + date) AND
the same associated company. The classic true-dupe source is Client Command's
commitment extractor running twice on the same meeting within ~24h. Flag the
later one as duplicate-of-[earlier ID]; never delete, and never dedup on a
prefix-stripped subject.

## The double-bill check

Before any `Yes`, search the client's CLOSED tickets for the same work under
different wording (auto-created action items often duplicate work already
executed and billed under a differently-worded ticket). If found: still
`Yes`, but the reason must read "delivered under closed ticket [ID] — do not
re-bill." This has caught real double-billing (8 reporting tickets on
Fisher's).

## When you can't reach the evidence

No stored credential, missing PAT scope, no meeting record → `Needs Review`
with `source_to_check` set to what SHOULD be checked and the reason saying
what's missing. Never `Yes` on inference, never silently skip.
