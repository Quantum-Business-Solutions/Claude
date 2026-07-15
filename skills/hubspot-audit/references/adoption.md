# Dimension 3: Adoption

Assesses whether humans are actually using the portal as intended. A perfectly architected portal with 20% rep adoption is a failure.

## Checks to run

### 3.1 Active user rate

**Query:** Fetch users, check last login timestamp.

**Metrics:**
- % of seats with login in last 30 days
- % with login in last 7 days
- Deactivated seats still being paid for

**Thresholds:**
- Healthy: >85% active-30d, >70% active-7d
- Flag: 70–85% active-30d
- Critical: <70% active-30d

**Impact:** Every inactive paid seat is direct waste. Quantify.

### 3.2 Activity volume per active user

**Query:** Count engagements (calls, emails, meetings, tasks, notes) logged per active user in last 30 days.

**Thresholds (sales reps):**
- Healthy: >40 logged activities/week/rep
- Flag: 15–40/week
- Critical: <15/week (CRM is being bypassed)

**Note:** Adjust for role — CSMs and account managers may log fewer but denser interactions.

### 3.3 Email tool usage

**Query:** Sent emails via HubSpot email tool vs. inferred external email (BCC to HubSpot, Gmail/Outlook extension).

**Finding:** Large gap between sent emails and logged emails from sales reps indicates the email integration isn't being used, which kills email reporting and sequence deliverability.

### 3.4 Meeting tool usage

**Query:**
- Meeting link usage: how many unique users have an active meeting link with bookings in last 90 days?
- Calendar integration status per user

**Threshold:** <50% of sales seats with active meeting link is a flag.

### 3.5 Sequence adoption (Sales Pro+)

**Query:**
- Total sequences created, active sequences
- Sequences with 0 enrollments in last 90 days (ghost sequences)
- % of active reps who have enrolled ≥1 contact in last 30 days
- Average enrollment count per active sequence

**Thresholds:**
- Healthy: <20% ghost sequences, >70% of reps using sequences weekly
- Flag: 20–40% ghost sequences OR 40–70% rep usage
- Critical: >40% ghost sequences OR <40% rep usage

### 3.6 Playbook adoption (Sales Pro+)

**Query:**
- Playbooks created, playbooks with opens in last 30 days
- Rep engagement with playbooks during deal activities

### 3.7 Snippet and template usage

**Query:** Templates created, templates used in last 30 days, % shared vs. private.

**Finding:** Lots of private templates means reps are reinventing; few shared templates means no managerial oversight of outbound messaging.

### 3.8 Mobile app usage

**Query:** Users with mobile app activity in last 30 days.

**Thresholds (for field-based sales like dealer reps):** <50% mobile adoption is a flag — field reps should be using mobile.

### 3.9 Task completion rate

**Query:**
- Tasks created, tasks completed, tasks overdue
- Task type distribution (call, email, to-do, other)

**Thresholds:**
- Healthy: >80% completion rate, <15% overdue
- Flag: 60–80% OR 15–30% overdue
- Critical: <60% completion OR >30% overdue

**Impact:** Low task completion means the follow-up queue is broken. Leads fall through. Deals rot.

### 3.10 Inbox/help desk usage (Service Hub)

If Service Hub is active:
- Unassigned ticket queue age
- Avg response time per ticket
- Conversations inbox usage vs. email forwarding

### 3.11 Knowledge base usage (Service Pro+)

- Articles published, articles with views in last 30 days
- Articles with thumbs-down or report submissions
- Staleness — articles not updated in 180+ days

### 3.12 Report/Dashboard consumption

**Query:**
- Dashboards with views in last 30 days
- % of reps who have viewed any dashboard in last 30 days
- Executive users accessing reports at reasonable cadence

**Finding:** Beautifully built dashboards with zero views = investment waste. Also see Dimension 6.

### 3.13 Marketing tool adoption

If Marketing Hub:
- Email campaigns sent per month trend
- Landing pages published, with conversions
- Forms on site, with submissions in last 30d
- Social tool usage
- Workflow creator distribution (one admin vs. distributed)

### 3.14 Training and documentation signals

**Query:** Check for:
- Internal HubSpot training documents uploaded
- Notes on user records from training sessions
- Team structure (suggests thought given to org design)

**Finding:** Portals with no training artifacts and no team structure often have lowest adoption — correlates, not causes, but worth noting.

### 3.15 Calls logged in HubSpot

**Query:** Count call engagements per active sales user over the last 30 days. Break out by role if roles are defined (BDR/SDR vs. AE vs. Account Manager). Also capture:

- Portal-wide: % of active sales reps with any call logged in last 30 days
- Per-rep ratio of calls to emails (a BDR with 0 calls and 500 emails is not actually outbounding)
- Avg call duration (sub-60-second calls are mostly voicemails)
- Whether HubSpot Calling is configured (provisioned phone numbers) OR a dialer integration is active (Aircall, RingCentral, Kixie, Orum, Drop Cowboy, ConnectAndSell, Five9)
- Calls marked disposition = "Connected" vs. other outcomes

**Thresholds:**
- BDR/SDR: Healthy >150 calls/week/rep, Flag 50–150, Critical <50
- AE: Healthy >25 calls/week/rep, Flag 10–25, Critical <10
- Account Manager/CSM: Healthy >10 calls/week/rep, Flag 3–10, Critical <3
- Portal-level: Critical if <40% of sales reps have any call logged in 30d (calling is happening off-platform, or not at all)

**Finding: The Call Black Hole.** If call volume is very low but deal volume is normal, calls are happening on personal cell phones, the rep's desk phone with no integration, or a dialer that isn't writing back to HubSpot. Coaching is impossible. Pipeline attribution to specific activities is impossible. Sequence A/B testing is meaningless.

**Impact:** Without calls in HubSpot: managers can't coach (no call recordings, no dispositions). Marketing can't close-loop outbound campaigns (no call metrics). Revenue operations can't compute activity-to-pipeline ratios. Forecasting loses a key signal. Quantify: at 8 calls/day × 240 working days × rep count, that's the annual call volume that should exist but doesn't, which is a large visibility gap to put a dollar figure on.

**Recommendation:** Three options depending on portal:
1. Enable HubSpot Calling with provisioned numbers (fastest)
2. Deploy a dialer integration (Aircall, RingCentral, Kixie) with auto-log to HubSpot
3. Enforce manual call logging via manager coaching + activity requirements in sequences

### 3.16 Target Accounts usage by reps

**Query:** For each rep with assigned target accounts (if Target Accounts enabled per Architecture 2.15):

- Activities logged against target account companies in last 30 days
- % of target accounts with any activity in last 30 days
- % of target accounts with a meeting scheduled in last 90 days
- Reps who own 0 target account activities (target accounts in name only)

**Thresholds:**
- Healthy: >60% of target accounts have activity in 30d, all reps with target accounts logging against them
- Flag: 30–60% activity rate, a few reps with 0 target account work
- Critical: <30% activity rate (target accounts are a list, not a motion), OR target accounts exist but no rep is working them

**Impact:** Target Accounts is an ABM commitment. Flagging accounts as targets and then ignoring them tells marketing "don't differentiate," then criticizes marketing for undifferentiated leads. Costs deal velocity on the accounts that would move fastest if worked.

### 3.17 ICP tier usage in rep workflow

**Query:** If an ICP property exists (Architecture 2.16), check whether it actually drives rep behavior:

- Are reps filtering their views by ICP tier?
- Are leads routed differently by ICP tier (faster SLA for Tier 1)?
- Are sequences tailored by ICP tier?
- Is ICP tier visible in the deal record sidebar default layout?
- Are dashboards segmented by ICP tier?

**Finding:** If ICP is defined but not surfaced in any rep-facing workflow, it's a property with no behavioral impact. Reps treat every lead the same; the ICP is a shelfware concept. Flag as critical adoption gap.

### 3.18 Lead follow-up discipline (rep behavior view)

The companion to Data Health 1.17. Here we look at *rep behavior* rather than system state.

**Queries:**

- Per-rep median time-to-first-touch on assigned MQLs (last 30 days)
- Per-rep count of assigned MQLs with zero follow-up at 7 days
- Rep ranking: best-to-worst on follow-up speed (identifies coaching targets)
- Per-rep follow-up persistence: avg number of touches before disposition
- Reps who close out leads as "not interested" on first touch vs. after multi-touch engagement (the former is ducking the work)

**Thresholds:**
- Any rep with median TTFT >4 hours on MQLs: Flag for coaching
- Any rep with >20% of assigned MQLs untouched at 7 days: Critical coaching target
- Reps disposing of leads without any follow-up touch: always flag

**Impact:** One or two reps with bad follow-up discipline can drag the whole team's performance. If a rep closes 30% of assigned MQLs as "not interested" with zero touches logged, that's not lead quality — that's rep behavior. The finding empowers managers to coach rather than blame marketing.

**Recommendation:** (1) Share per-rep TTFT and leakage data with managers monthly. (2) Require disposition reasons with minimum activity thresholds (no closing a lead without at least one attempted touch). (3) Surface rep-level follow-up metrics in the lead ops dashboard. (4) Use data in 1:1s, not for blame but for coaching.

### 3.19 Sales methodology adoption (rep behavior view)

Companion to Architecture 2.18. If methodology fields exist structurally, are reps actually using them?

**Query:**

- % of open deals past the qualification stage with methodology fields filled (Economic Buyer, Decision Criteria, Metrics, etc. for MEDDIC; or equivalent for other frameworks)
- Per-rep fill rate on methodology fields — which reps are disciplined, which aren't?
- Correlation between methodology-field completeness and win rate (powerful finding when positive)
- Methodology field updates over time (reps updating as they learn) vs. set-once-and-forget

**Thresholds:**
- Healthy: >75% of post-qualification open deals have methodology fields filled; variation across reps <20%
- Flag: 40–75% fill rate, or high rep variance (>20 percentage points)
- Critical: <40% fill rate — methodology structurally present but behaviorally absent

**Impact:** Methodology fields without rep discipline are worse than no fields — they create false confidence. Leadership assumes deal quality is captured; in reality it's theater. The fix is coaching + enforcement via stage gating, not more fields.

### 3.20 HubSpot AI / Breeze feature adoption

HubSpot has shipped significant AI capability over the last 18 months. Check which AI features are enabled and adopted.

**Query:** Enumerate the portal's AI-feature adoption:

- **Breeze Copilot** — enabled for the account? Users actively using it?
- **AI content assistant** — emails drafted with AI assistance, landing pages generated, blog post drafts?
- **Breeze prospecting agent** (Sales Pro+) — configured? generating prospect lists? results being worked?
- **AI-powered lead scoring** — configured? aligned with ICP?
- **Predictive lead scoring** — enabled? fit score present? correlating with outcomes?
- **AI dedupe** — enabled? recurring review cadence?
- **ChatSpot / Breeze chat** — used by admins to query the portal?
- **Meeting summarization** (Zoom AI Companion, Breeze intelligence) — configured and logging to HubSpot?
- **Content remix / repurposing** — used by marketing team?
- **AI assistant for workflows** — used when building new workflows?

**Thresholds:**
- Ahead of the curve: 6+ AI features adopted with evidence of usage
- Healthy: 3–5 AI features adopted
- Flag: 1–2 AI features adopted, most ignored
- Critical: Zero AI features adopted — portal is using HubSpot circa 2022, leaving paid capability on the table

**Impact:** AI features paid for but not used = direct waste. AI features used incorrectly (AI content assistant generating off-brand content, predictive lead scoring without reviewing score correlation) = active harm. The opportunity: QBS positions itself as the partner that operationalizes these features, which differentiates from agencies still doing 2022 HubSpot work.

**Recommendation:** (1) Prioritize 2–3 AI features with clearest ROI for the client's context. (2) Train the team on each: when to use, when not to use, how to evaluate output. (3) Build governance (AI-generated content reviewed before send; predictive scores cross-checked quarterly). (4) Revisit quarterly as HubSpot ships new AI — this is now a regular cadence, not a one-time setup.

### 3.21 Mobile experience completeness

Builds on 3.8 with specific configuration checks for field-based roles.

**Query:**

- Mobile app adoption rate (users with mobile activity in last 30 days, from 3.8)
- Record card mobile layout customized vs. default? (Critical properties visible without scrolling on phone?)
- Mobile-specific notifications configured (deal updates, task assignments, meeting reminders)?
- Mobile workflow enabled (reps can log calls/notes/meetings from phone easily)?
- Offline mode usage (for reps in dead-zone territories — e.g., dealer-channel reps in warehouses, basements, rural accounts)?
- Mobile-friendly forms for field reps (quick-add forms vs. desktop-only forms)?
- Calling from mobile integrated (HubSpot mobile calling, Twilio integration) so calls log even when rep is mobile?

**Thresholds:**
- Healthy for field-based clients: >70% of field reps actively using mobile, record layouts mobile-optimized, mobile calling integrated
- Flag: 40–70% mobile usage among field reps, layouts not customized, no mobile calling
- Critical: <40% mobile usage among field reps — field activity is invisible to the CRM

**Impact:** For dealer-channel and other field-heavy sales motions, the mobile experience IS the CRM experience 40% of the time. A bad mobile experience means reps log activities retroactively (if at all) in the parking lot after the call, or never. Pipeline visibility, coaching, and forecasting all erode. Worth its own audit sub-section for clients where field reps are >30% of the team.

**Recommendation:** (1) Customize mobile record card layouts for each major role. (2) Enable mobile-specific notifications for the events that matter. (3) Integrate mobile calling. (4) Create quick-add forms optimized for thumb-typing. (5) For rural/warehouse-heavy territories, test offline mode and train reps.

## Dealer-channel-specific checks

- **Service contract activity logging:** are service managers logging renewals, calls, escalations on SC records?
- **Equipment record updates:** are techs updating equipment status or is equipment data static since import?
- **Field rep mobile usage:** territory reps not on mobile = adoption failure specifically for this industry

## Output format

```yaml
- id: adoption_01_inactive_seats
  dimension: adoption
  severity: high
  title: "28% of paid seats inactive in last 30 days"
  evidence: "25 Sales Enterprise seats purchased; 18 with login in last 30 days; 7 inactive. Annual cost of inactive seats: ~$13,440"
  impact: "Direct waste; also degrades rep-by-rep reporting baselines"
  recommendation: "Deactivate 7 unused seats at next renewal OR reassign to waitlisted users. Audit who approved the seats to prevent repeat."
  effort: hours
  tier_requirement: none
```
