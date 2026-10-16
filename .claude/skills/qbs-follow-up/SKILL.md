---
name: qbs-follow-up
description: Turn a HubSpot contact list (Deal Follow-Up, past clients, agreed-to-meet-but-unbooked, etc.) into reviewed, personalised follow-up emails created as Outlook DRAFTS, with the HubSpot BCC so sends log themselves. Use whenever Shawn says "follow up with <list/group>", "draft emails for the Deal Follow-Up list", "who should we email", "stay on top of leads", or "start a follow-up batch". Builds the emailable pool, ranks by company Most Recent Active Engagement, reads each contact's real history, writes a specific email per contact, and stops at the approval gate. NEVER sends. NOT for cold outreach (Instantly) or list cleaning (qbs-list-verification).
---

# QBS Follow-Up

The goal: pick a group, draft emails from what actually happened with each person, send safely,
and never lose track of a follow-up. Shawn reviews and sends; this skill drafts.

## Hard rules
1. **Never send.** Drafts only (`follow_up/drafts.py`). Sending or scheduling happens only when Shawn names the
   exact emails ("send Tom and Michelle"), and only via `send_my_email` after reading the current draft back
   (he may have edited it). No bulk sends, no "the batch looked fine earlier".
2. **BCC `20682069@bcc.hubspot.com` on every draft.** That is how a send gets logged to the contact. Do not add a
   separate logging step for the email itself.
3. **Plain text, no attachments, few or no links, every email different.** Deliverability depends on it.
4. **Daily cap: start at 10-15 drafts per batch and recommend 4-5 sends a day** until Shawn says otherwise.
5. **Read the history before writing.** A draft that could have gone to anyone is a failed draft.

## Run it
1. **Pool** - `python3 -m follow_up.pool <listId> --out pool.json` (read-only). Drops: no email, global unsubscribe,
   Instantly bounce/unsub, invalid email, do-not-market, disqualified, LinkedIn "moved". Moved/bounced contacts are
   *held for re-check, not dropped*: a "moved" flag has been wrong before (two current roles, newest listed first -
   Jack Stigman). Re-check against the full dated experience via `contact-verification/scripts/unipile.py`
   (read-only; Shawn's account only). **One to One opt-out is included** by default (Shawn: these are real
   personal emails); the global `hs_email_optout` is always excluded unless Shawn says otherwise.
2. **Rank** - open deals first, then company `most_recent_active_engagement_date_v2` (company object, NOT contact;
   contact-level date is empty). Skip anyone engaged in the last 14 days (a live conversation) and check Shawn's
   calendar (`list_my_calendar`) for any meeting with the person or company.
3. **Context** - `python3 -m follow_up.context pool.json <ids> --out ctx.json`. Read: meetings and outcomes, human
   replies, what we already sent (do not repeat an ask), conversation calls, deal stage/amount, Call Intel company
   signals (`ai__signal_*`: contract timing, CRM, budget). CAS call-attempt logs are noise.
4. **Write** - one email per person (one email for two people at the same company). Then `python3 -m follow_up.drafts emails.json`.
5. **Hand off** - list who, why they were chosen, what each email refers to, anything unverified, and who was held.

## Tone rules
- Age since last real touch decides the opener. Under ~3 weeks: normal. Over ~3 weeks: acknowledge the gap
  ("it has been a while"). Never "as you asked" / "the email you asked for" about an old request.
- Refer to a specific thing that happened (their reply, the proposal, the missed call, the contract window).
  Only claim what the record supports; flag shaky details to Shawn instead of stating them.
- One low-pressure question, an easy way to say no, no pitch dump. Short.
- Keep it calm and warm. Do not lead with "I have sent several emails" or anything that sounds like a complaint or pressure; for a contact who has had several unanswered emails, write a friendly catch-up and ask when a short call to talk through next year's initiatives would suit them.
- Someone who asked to be left alone, or whose notes say we call too much: email only, brief, no mention of
  calls, follow their lead; or hold. Ask Shawn.
- Former clients: warm, refer to the relationship, no re-pitch.
- Sign `Shawn` / `Quantum Business Solutions`. Subject lines differ per email.

## Follow-up tracking
Sends log via the BCC. The missing piece is "who needs a nudge": on each run, list contacts whose last logged
email from Shawn is 5-7+ business days old with no reply, but check replies first - a reply only reaches HubSpot
if the mailbox is connected to HubSpot, so verify on recent contacts before treating silence as no-reply.

## Known gaps
- Scheduled send is not available through the Outlook tools; Shawn uses Outlook "Schedule send" or tells us when to send.
- Drafts may take a while to appear in desktop Outlook (they show immediately in Outlook on the web).
- LinkedIn messaging step (for contacts connected on LinkedIn or with a One to One opt-out) is not built yet.
- Sending-rate guidance is a rule of thumb; SPF, DKIM and DMARC for thequantumleap.business were verified present
  (2026-10-16) but DKIM signing being enabled in the Microsoft admin center was not.
