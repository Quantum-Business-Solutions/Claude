# System Overview

## What this program is

A LinkedIn-driven pipeline for QBS: find ICP prospects, confirm they still work where the CRM
thinks they do, warm them by engaging with their content, reach them by invite/DM/InMail, and
log every touch to HubSpot so the CRM stays the system of record.

Two motions run in parallel against the same audience:

- **Engagement** (warm) — comment on watch-list prospects' posts in Shawn's voice.
- **Outreach** (cold) — send invites, DMs and InMails to senior contacts at ICP companies.

Reporting sits on top of both.

## The pipeline as designed

```
qbs-linkedin-watch-sync  (07:33 M-F)
   Sales Nav saved leads ──> watch list roster
          │
          ├──> qbs-linkedin-engage-am  (08:05 M-F)   comment on fresh posts
          └──> qbs-linkedin-engage     (14:08 M-F)   comment on fresh posts

qbs-linkedin-daily       (12:00 UTC daily)
   ICP companies ─> senior CAS Prospect contacts ─> employment verification
                 ─> route to channel ─> send ─> log to HubSpot

qbs-linkedin-weekly-digest
   Unipile + HubSpot ──> weekly report
```

`watch-sync` is a **blocking upstream dependency**: both engage tasks hard-stop when the roster
is absent.

## The outreach motion in detail

**Targeting.** Companies where `currently_use_zoominfo_ = Yes` AND `currently_using_hubspot_ = Yes`
— that pair *is* the ICP thesis, because the InMail template asserts "Last we showed, you had
HubSpot." Two OR'd filter groups: engaged >90 days ago, and never engaged. The second group exists
because HubSpot date comparisons don't match NULL, so a bare `LT` silently drops the never-engaged
companies, which are the warmest prospects.

**Qualification.** Senior contacts (`executive / owner / vp / director`) with `hs_lead_status =
CAS Prospect`, a LinkedIn URL, no prior LinkedIn message, and `ai__li_still_at_company != no`.

**Verification — the Reading Rule.** Dated work experience is the source of truth; headlines are
unreliable. Build the set of roles with a null end date, normalize company names on both sides
(strip punctuation and legal suffixes), and accept if either contains the other. Verdicts are
`yes` / `no` / `unreadable`, banked to the `ai__` namespace on every candidate examined — sent or
not — because those 15–20 daily profile reads are free employment verifications. Roughly **49% of
candidates come back `no`**; that is the established baseline, not a malfunction.

**Routing.** `FIRST_DEGREE` → DM · open profile + premium → free InMail · premium → paid InMail ·
2nd/3rd degree → invite · else skip.

**Sending.** One at a time: send → write contact property → write task → next candidate. Never
batched. The May 2026 incident — 11 invites sent and unlogged after a crash — is why.

## The engagement motion in detail

Fetch each watch-list prospect's recent posts, keep those inside a freshness window, skip any post
Shawn has already commented on, screen out anything sensitive (layoffs, grief, illness, politics,
religion, hardship), draft 15–50 words in QBS voice, score it, and post only high-confidence
drafts — with pacing between posts and a hard daily ceiling.

## Why the CRM is the state store

Every failure this program has had is a **state** failure, not a judgment failure:

- a CSV that never existed
- a memory-derived counter that stopped being written for 12 weeks while sends continued
- a database mirror that drifted ~4x from the truth
- local file paths referenced from a cloud runtime

None of them were "the model wrote a bad comment." That is what the rebuild is organized around.
