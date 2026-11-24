# QA report: GoodSuite HubSpot drafts (portal 20921734), 2026-11-18

Nothing was enabled, published, enrolled or sent. HubSpot's own renderer was not seen (preview needs a HubSpot login); all visual checks are local Playwright renders of the template plus the live widget content.

## Result

Copy verdicts across the 58 unique emails: **33 PASS, 6 FIXED, 19 FLAG**.
Design: the new hero (2 to 4 word phrase at 38px, explicit `#004B87` wrapper background) is **applied to 6 of 58** emails only. The other 52 still have the one-word 56px hero and no wrapper background. Their full 7-widget PATCH bodies are written and tested (one was applied and read back): `/tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa/payloads/<emailId>.json`. I stopped because each PATCH must carry the full widget set inline (about 7 KB out and 7 KB echoed back), and 52 more calls were not feasible in this run.

## A. Assets (read only)

- Workflows: all 10 in plan_data.json read back with `isEnabled:false`, `LIST_BASED` enrolment on the expected list, content_ids and cumulative delays match plan_data steps (checked for every workflow, including L3's branch order and L2's date-based delays). Ids: 5422456551, 5422159566, 5422602950, 5422610154, 5422587600, 5422587613, 5422593747, 5422608106, 5422593724, 5422156522.
- Lists: 8513, 8551, 8552, 8553, 8550, 8543, 8521, 8531, 8519, 8520 are `MANUAL` (static), `size 0`. A search for "DRAFT" returns exactly these 10 lists. No contact can be enrolled (workflows off, lists empty).
- Emails: 58 created today (no archived ones), all `AUTOMATED_EMAIL` / `AUTOMATED_DRAFT`, `isPublished:false`, templatePath `templates/GoodSuite_DnD_Email_v1.html`, six modules plus `preview_text`, none deleted. All 58 ids are in plan_data.json. Nothing orphaned or leftover (no test/probe emails, lists or DRAFT workflows). Workflows created today but not ours: "2026 [GS Active Clients] Holiday Closure Notice: Thanksgiving", "[Newsletter] Quarterly Newsletter - Q4 - November 2026 - Active Clients", "2026 [GS Employees] Holiday Closure Notice: Thanksgiving" (all disabled, other lanes).
- Note: `publishDate` is populated on every draft (equals last save time) while `isPublished` is false and state is AUTOMATED_DRAFT. That is HubSpot behaviour for drafts, not a publish.
- Subscription type: L1, L2, L3, L5, L6 emails use subscription 2169812752 "GoodSuite Insider: Education & Events"; NNC and L4 use 29902898 "Cybersecurity Tips & Alerts". Sales prospecting under an education/events subscription is worth a compliance look (flag).

## B. Copy QA, findings that apply to every lane

- Hooks: every email has a real first line except three that were generic or about GoodSuite (fixed, see changes).
- Subjects: all between 30 and 49 characters; none outside 25 to 55; no all caps, no spam words after the L6 E4 fix; no duplicate subjects across the 58 (L1a, L1b, L1c intentionally reuse the same email ids).
- No em or en dashes anywhere in widgets, names or subjects. Every personalization token has a fallback ("there", "your business").
- Preheaders add to the subject. One that overlaps: `431227630325` ("What should a printed page cost you?" / "...cost per page easy to compare"), mild. `431261791960` preheader contains "free".
- One CTA per email (single button to /contact/). L2e buttons say "Reply or book your account review", which is two actions.
- Length: five emails are 160 to 167 words by my count (NNC E1 161, E2 167, E4 163, E7 162, L4 E1 160). Not changed.
- Repeated wording: sign-offs "This is the last note in this series. You are always welcome to reply with a question." (NNC E8, L1 E10, L3 E8, L4 E8, L5 E10); "Not the right person for this? ..." P.S. in 6 emails across lanes; "As a GoodSuite customer, you can ask us to ..." in 6 of 8 L4 emails; "What actually happens in a (free) ...?" hook used 3 times (NNC E6, L1 E9, L3 E6); NNC E6 and L1 E9 share "You have heard us mention it, so here is the plain answer. It is a short conversation and a review of ...". Topic overlap NNC E2/E3 with L4 E2/E3 (printers, insurance) with near-identical insurer disclaimer; L6 E6 overlaps NNC. Recommend the owner decides which lane keeps which topic. Not changed.
- Unconfirmed claims: offers confirmed by Shawn are free price check, account review, security check-up, IT review, fleet review. L5 and L6 emails describe service delivery (one predictable cost per page, supplies sent early, monitoring, response times, flat monthly fee, security basics included) that is not on that list. Flagged per email below, not changed. Also "Most ..." generalisations (NNC E1, NNC E2, L1 E1) are unsupported but not statistics.
- Lease windows: L1a sends 7 of the 10 in order (E1 to E7 at day 0, 7, 21, 45, 75, 105, 150), L1b all 10, L1c all 10, confirmed in the flows. Timing risk: the paths run from enrolment day, not from the lease end date. A lease ending in 2 months entering L1a still receives "before you sign" emails up to day 150, and a lease ending in 6 months entering L1b receives E7 to E10 (day 210 to 360) after it has ended. Needs a decision before enabling (branch on lease end date, or shorten).
- L2: workflow delays are -365/-274/-183/-91 days from the lease end date, so an account whose lease ends in under 12 months will have step 1 in the past (the flow description already says add a branch before each step).
- L2e copy is first person singular ("I look after the account") while the From name is "GoodSuite".
- L4 call tasks are `task_type TODO` named "Call: security check-up"; L1, L3, L5 are `CALL`. Minor inconsistency.

## Per-email tables (copy)

Hook line = the h1 after "Hi {first name}". Verdict is on copy. A "Hero ... pending" note means the design fix is not yet applied.

### Net new cyber (NNC)

| Email | Id | Subject | Len | Hook line (first line after greeting) | Verdict | Note |
|---|---|---|---|---|---|---|
| E1 | `431227629299` | Why smaller businesses get targeted | 35 | Most attacks are not aimed at you. They are aimed at everyone. | FLAG | Unsupported generalisation in the hook ("Most attacks are not aimed at you"); 161 words. Confirm or soften. Hero "Basics" (56px) pending, payload ready for "Small is not invisible". |
| E2 | `431261790949` | Your copier is a computer on your network | 41 | The copier in your hallway has its own network address. | FLAG | 167 words (over ~160). "the part most businesses forget" is an unsupported claim. Hero "Print" (56px) pending, payload ready for "Your copier is online". |
| E3 | `431227629302` | What cyber insurance asks about now | 35 | Cyber insurance forms now ask very specific questions. | FLAG | Closing sentence "We cannot speak for any insurer, but we can help you gather honest answers" is repeated almost verbatim in L4 E3. Hero "Insurance" (56px) pending, payload ready for "What insurers ask". |
| E4 | `431227629305` | Passwords and MFA, without the jargon | 37 | If someone stole your password today, what would stop them? | PASS | Hero "MFA" (56px) pending, payload ready for "MFA in plain English". 163 words. |
| E5 | `431278272203` | Could you restore from backup on Monday? | 40 | When did you last restore a file from your backup? | PASS | Hero "Monday" (56px) pending, payload ready for "Ready by Monday?". |
| E6 | `431278232257` | What a security check-up actually covers | 40 | What actually happens in a security check-up? | PASS | Hero "Checklist" (56px) pending, payload ready for "Inside the check-up". |
| E7 | `431261790953` | How to spot a phishing email in 3 steps | 39 | An email says to act right now. What do you do first? | PASS | Hero "Pause" (56px) pending, payload ready for "Pause before you click". 162 words. |
| E8 | `431227630277` | One small security step before year-end | 39 | What is one security step you could finish this year? | PASS | Hero "Next step" (56px) pending, payload ready for "Pick one step". |

### Lease windows L1a/L1b/L1c (shared emails; L1a sends E1 to E7, L1b E1 to E10, L1c E1 to E10)

| Email | Id | Subject | Len | Hook line (first line after greeting) | Verdict | Note |
|---|---|---|---|---|---|---|
| E1 | `431261791960` | Before you renew your copier lease | 34 | Most copier lease renewals are decided on autopilot. | FIXED | FIXED: closing no longer promises a countdown note the short path never sends. Open: hook says "Most copier lease renewals are decided on autopilot", an unsupported claim; preheader contains "free". FIXED: closing no longer promises a countdown note the short path never sends. Open: hook says "Most copier lease renewals are decided on autopilot", an unsupported claim; preheader contains "free". |
| E2 | `431240830674` | Renew, return or upgrade your copier? | 37 | Renew, return, or upgrade: which one are you really choosing? | PASS | Hero "Three paths" (56px) pending, payload ready for "Renew, return, upgrade". |
| E3 | `431240830680` | The copier lease date that matters most | 39 | Does your copier agreement have a notice window? | PASS | Hero "Notice" (56px) pending, payload ready for "Earlier than you think". |
| E4 | `431278232265` | Read your copier lease in 5 minutes | 35 | You can read a copier lease in five minutes if you know where to look. | PASS | Hero "5 minutes" (56px) pending, payload ready for "Five-minute lease read". |
| E5 | `431227630325` | What should a printed page cost you? | 36 | Do you know what one printed page costs your office? | PASS | Hero "Per page" (56px) pending, payload ready for "What a page costs". |
| E6 | `431227630328` | Do you have the right number of copiers? | 40 | Does your copier setup still match the team you have today? | PASS | Hero "Right size" (56px) pending, payload ready for "Right machines, right places". |
| E7 | `431227631291` | How fast should copier service be? | 34 | When the copier goes down, how long until someone shows up? | PASS | Hero "Service" (56px) pending, payload ready for "Fast service, in writing". |
| E8 | `431240830688` | A 12, 9, 6, 3 month lease countdown | 35 | The best copier renewals start a year early. | FLAG | Sent at day 240 on the 6-12 month path and day 210 on the 12-24 path. On the 6-12 path the 12 and 9 month checkpoints have passed. Copy copes ("start where you are"). Hero "12-9-6-3" (56px) pending, payload ready for "Four simple checkpoints". |
| E9 | `431301215968` | What a copier price check covers | 32 | What actually happens in a free copier price check? | PASS | Hero "No pressure" (56px) pending, payload ready for "What you get back". |
| E10 | `431240830692` | Want us to price it out before you sign? | 40 | Want us to price out your copier renewal before you sign? | PASS | Hero "Before you sign" (56px) pending, payload ready for "Before you sign". |

### Customer lease-end emails (L2e)

| Email | Id | Subject | Len | Hook line (first line after greeting) | Verdict | Note |
|---|---|---|---|---|---|---|
| E1 | `431261791945` | Your lease ends in about a year | 31 | Your lease is about a year from its end date. | FLAG | Written in first person singular ("I look after the account") but From name is "GoodSuite"; CTA "Reply or book your account review" is two actions. Hero "12 months" (56px) pending, payload ready for "A year to plan". |
| E2 | `431227630306` | Nine months left: is your setup still right? | 44 | Nine months out, you still have every option open. | FLAG | First person singular vs From "GoodSuite"; CTA is two actions ("Reply or book"). Hero "9 months" (56px) pending, payload ready for "Still the right fit?". |
| E3 | `431261791955` | Six months to go: what will it cost next? | 41 | What will your next lease cost compared with this one? | FLAG | First person singular vs From "GoodSuite"; CTA is two actions ("Reply or book"). Hero "6 months" (56px) pending, payload ready for "Numbers side by side". |
| E4 | `431227630316` | Three months left on your lease | 31 | Your lease ends in about three months, so let us agree the next step. | FLAG | First person singular vs From "GoodSuite"; CTA is two actions ("Reply or book"). Hero "3 months" (56px) pending, payload ready for "Time for a plan". |

### Managed IT cross-sell (L3)

| Email | Id | Subject | Len | Hook line (first line after greeting) | Verdict | Note |
|---|---|---|---|---|---|---|
| E1 | `431240830653` | One team for your printers and IT | 33 | You already know who to call when the copier acts up. | FLAG | States GoodSuite also looks after IT for businesses like the reader; fine for customers, confirm it is true for all list members. Hero "One team" (56px) pending, payload ready for "One team for both". |
| E2 | `431240830656` | A predictable monthly cost for IT | 33 | How much did IT cost last quarter, down to the dollar? | PASS | Hero "Budget" (56px) pending, payload ready for "Know your IT cost". |
| E3 | `431227630297` | One number to call for print and IT | 35 | A printer jam is an easy call. What about Wi-Fi, email or a locked account? | PASS | Hero "One call" (56px) pending, payload ready for "One number to call". |
| E4 | `431240830659` | How many vendors does your office juggle? | 41 | Count the vendors your office pays for technology. | PASS | Hero "Vendors" (56px) pending, payload ready for "Count your vendors". |
| E5 | `431240830662` | Three questions about your IT spend | 35 | When an IT bill arrives, do you know exactly what it covers? | PASS | Hero "Spend" (56px) pending, payload ready for "Read your IT bill". |
| E6 | `431240830665` | What a first IT review looks like | 33 | What actually happens in an IT review call? | PASS | Hero "Review" (56px) pending, payload ready for "A short IT conversation". |
| E7 | `431240830668` | Fewer vendors, fewer calls: a simple test | 41 | Next time something breaks, count how many calls it takes. | PASS | Hero "The test" (56px) pending, payload ready for "Count the calls". |
| E8 | `431280829127` | A simple next step for print and IT | 35 | The next step can be as small as a reply. | FIXED | FIXED: first line duplicated the hero sub-line (a slogan). Now a reader-facing line. Hero + wrapper bg applied. |

### Cyber cross-sell (L4)

| Email | Id | Subject | Len | Hook line (first line after greeting) | Verdict | Note |
|---|---|---|---|---|---|---|
| E1 | `431227630300` | A security check-up for GoodSuite customers | 43 | When did anyone last review your office security? | FIXED | FIXED: first line was about GoodSuite ("We already know your setup..."); now a reader question. Accent line rewritten to follow it. Hero + wrapper bg applied. |
| E2 | `431280829124` | Who can use the printers on your network? | 41 | Who can print, scan, and reach the admin screen on your copiers? | PASS | Hero "Access" (56px) pending, payload ready for "Who can reach it?". |
| E3 | `431261791942` | Who answers the cyber insurance questionnaire? | 46 | Who at your company fills in the cyber insurance questionnaire? | FLAG | Same insurer disclaimer as NNC E3. Topic overlaps NNC E3 (insurance questionnaire). Hero "Renewal" (56px) pending, payload ready for "Ready before renewal". |
| E4 | `431227630303` | A client sent a security questionnaire. Now what? | 49 | A client just sent a security questionnaire. Where do your answers live? | FIXED | FIXED (design): hero phrase + wrapper bg. Restored after my merge test blanked modules 1 to 5; read back intact. |
| E5 | `431280829130` | If something broke tonight, who would you call? | 47 | If your systems stopped tonight, who would you call first? | PASS | Hero "Call list" (56px) pending, payload ready for "Know your first call". |
| E6 | `431261791963` | Plan security spending by priority, not panic | 45 | What would you fund first if you had a ranked list of security needs? | PASS | Hero "Priorities" (56px) pending, payload ready for "A ranked list". |
| E7 | `431227630319` | When someone leaves, how fast does access end? | 46 | When someone leaves your company, how long until their access ends? | PASS | Hero "Leavers" (56px) pending, payload ready for "Start and stop access". |
| E8 | `431240830677` | Your security check-up is still open | 36 | It has been a while since we first offered you a security check-up. | PASS | Hero "Your call" (56px) pending, payload ready for "Your move, no rush". |

### Net new managed print (L5)

| Email | Id | Subject | Len | Hook line (first line after greeting) | Verdict | Note |
|---|---|---|---|---|---|---|
| E1 | `431227630284` | Who handles your printers when they stall? | 42 | When a printer stalls, who do people come looking for? | FLAG | Service claims not on the confirmed offer list: one predictable cost per page, response times you can count on. Confirm with GoodSuite. Hero "Print" (56px) pending, payload ready for "Print, handled for you". |
| E2 | `431240829668` | A predictable cost per page for 10+ devices | 43 | How many print invoices land on your desk each month? | FLAG | Claims a fleet of 10+ devices moves to a predictable cost per page and that service, supplies and monitoring sit with one team. Confirm. Hero "One rate" (56px) pending, payload ready for "One cost per page". |
| E3 | `431261790969` | Print should not be a leadership topic | 38 | If printers come up in a leadership meeting, something is off. | FLAG | Claims GoodSuite "takes the whole fleet off your team's plate". Confirm scope. Hero "Off your plate" (56px) pending, payload ready for "Off your plate". |
| E4 | `431227630290` | Running out of toner is a solved problem | 40 | Toner runs out on the day you need a 200-page packet. | FLAG | Claims device levels are monitored and supplies are sent before the fleet runs dry. Confirm. Hero "Toner" (56px) pending, payload ready for "Toner, handled early". |
| E5 | `431278232260` | What a print fleet review actually covers | 41 | Can you name every printer and copier and what each costs to run? | PASS | Hero "Review" (56px) pending, payload ready for "Know your fleet". |
| E6 | `431240829674` | What good print service looks like | 34 | When a copier goes down, how long will you wait? | FLAG | Claims agreed service levels up front and proactive monitoring that catches many issues early. Confirm. Hero "Service" (56px) pending, payload ready for "A fast, clear response". |
| E7 | `431227630293` | Fewer vendors, fewer headaches | 30 | How many vendors does it take to keep your paper moving? | FLAG | Claims one agreement, one point of contact, one accountable team. Confirm. Hero "Simpler" (56px) pending, payload ready for "One partner for print". |
| E8 | `431240829683` | When does your print contract end? | 34 | Do you know the end date of your print and copier agreements? | PASS | Hero "Dates" (56px) pending, payload ready for "Know your end date". |
| E9 | `431240830650` | Three questions about your print fleet | 38 | Three questions show how well your printers work for you. | PASS | Hero "Three" (56px) pending, payload ready for "Three quick questions". |
| E10 | `431261791939` | A yearly check on your print fleet | 34 | It has been a year since we first wrote, so here is the short version. | FLAG | States GoodSuite manages fleets of 10+ devices for a predictable cost per page. Confirm. Hero "Still here" (56px) pending, payload ready for "Still here for you". |

### Net new managed IT (L6)

| Email | Id | Subject | Len | Hook line (first line after greeting) | Verdict | Note |
|---|---|---|---|---|---|---|
| E1 | `431227630281` | Who do you call when the network goes down? | 43 | It is 9:05 and nobody can log in. Who do you call? | FLAG | Claims "Real people", "Security basics covered", predictable monthly fee. Confirm exact managed IT scope (offer text still pending client confirmation). Hero "Call" (56px) pending, payload ready for "One call away". |
| E2 | `431261790957` | Fewer surprises on the IT invoice | 33 | The most expensive IT bill is usually the one nobody planned for. | FLAG | Flat monthly fee claim; confirm plans are flat-fee. Hero "Flat" (56px) pending, payload ready for "A flat monthly fee". |
| E3 | `431261790960` | What does a monthly IT plan include? | 36 | Ask five people what IT support means and you get five answers. | PASS | Hero "Included" (56px) pending, payload ready for "What is included". |
| E4 | `431261790963` | Inside an IT review: what to expect | 35 | You do not need a project to find out where your IT stands. | FIXED | FIXED: subject contained "free". Hero + wrapper bg applied. |
| E5 | `431261790966` | Is the new hire's laptop ready for Monday? | 42 | A new hire starts Monday. Is the laptop set up and the email ready? | PASS | Hero "Day 1" (56px) pending, payload ready for "Ready for day one". |
| E6 | `431240829671` | Security basics, built into your IT support | 43 | Who checks that every laptop in your office is up to date? | FIXED | FIXED: first line was a generic statement. Now a concrete question. Hero + wrapper bg applied. |
| E7 | `431227630287` | What if the one person who knows IT leaves? | 43 | Does only one person know the router password? | PASS | Hero "Key person" (56px) pending, payload ready for "Beyond one person". |
| E8 | `431261791932` | A simple IT plan for the year ahead | 35 | Most IT budgets are a guess plus a few emergencies. | PASS | Hero "Roadmap" (56px) pending, payload ready for "A one-page IT plan". |
| E9 | `431240829677` | Pay-per-fix IT or a flat monthly plan? | 38 | Paying per fix feels cheaper, until the month three things break. | PASS | Hero "Fix or plan" (56px) pending, payload ready for "Fix or plan?". |
| E10 | `431240829680` | A second opinion on your IT, any time | 37 | A year of notes from us. Is your IT in better shape? | PASS | Hero "Open door" (56px) pending, payload ready for "An open door". |

## C. Design QA

Rendered 15 emails across every lane (NNC E1/E5, L1 E1/E8, L2e E1, L3 E1/E8, L4 E1/E4, L5 E1/E3, L6 E1/E4/E5/E6) at 375px, 700px and dark mode. Before and after PNGs are listed below. Looked at: hero, contrast, button, three-point card, spacing, footer.

Findings:
1. Hero: one-word 56px headlines ("Call", "Proof", "Day 1", "Print", "Monday") read as labels; two-word ones wrap ("Off your plate" on two lines at 375px). The headline often repeated the hero sub-line or the pill. Replacement: 2 to 4 word phrases at 38px / 1.15 line height, chosen so the phrase does not repeat the pill or sub-line. All 58 phrases are in `/tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa/build_fix.py` (HERO map).
2. Hero background: the dark blue comes only from the template's `dnd_section background_color='#004B87'`. I rendered the same email with the section background removed (`/tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/nobg_hero_crop.png`): the white headline vanishes and only the pale sub-line remains. Fix: `hs_wrapper_css.background-color: #004B87` on module-0-0-0, the same value as the template section. HubSpot accepted and returned it on all 6 patched emails.
3. Footer icons: all five load from hubspotusercontent (Website, LinkedIn, `gs-social-facebook-f.png`, Instagram, YouTube, all 120x120 PNG, HTTP 200). The Facebook "f" is correct (white f on the same blue circle); its edge is slightly softer than the others (anti-aliased vs paletted). See `/tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/assets/icons_strip.png`.
4. Dark mode: header logo swaps to the white logo (`gs-logo-white.png`, loads), footer and chips turn dark, body sections stay light with dark text, so text contrast is fine. The blue circle social icons are lower contrast on the dark footer but visible.
5. Button: #003A69 on #94C83D (about 6:1), pill, full width of content at 375px; long CTAs ("Book your free security check-up") wrap to two lines. My local button simulation left-aligns wrapped text; HubSpot's button module centres it, unverified.
6. Three-point card: numbered circles and indented detail line align at 375, 700 and dark mode; no overlap.
7. **Template bug (not changed, template is not mine to edit): at 375px the page scrolls horizontally by 11px (386px wide) and by 26px at 360px.** Cause confirmed by hiding rows one by one: the footer social row (5 icons with `min-width:44px` plus padding is about 330px wide inside a 355px card with 26px side padding). Fix in `GoodSuite_DnD_Email_v1.html`: at max-width 400px set `.soc-td` padding to `0 3px` and the cell padding to `22px 12px 6px`, or drop `min-width` on the social anchors.
8. Left over default text: none found in any of the 58 (no "Big idea", "Your headline goes here", "Point one title").
9. Not verified: HubSpot's renderer, Outlook desktop (Word engine), Gmail dark-mode inversion, real client behaviour of `hs_wrapper_css.background-color` in the sent email (it renders correctly in the API echo; the editor view was not seen).

### Screenshots (saved)
Files named `before_<id>_{m,d,md}.png` render the live content before changes (m = 375px, d = 700px, md = 375px dark). `after_<id>_*.png` render the new payloads; only 431227630300, 431227630303, 431261790963, 431261791960, 431280829127, 431240829671 are live in HubSpot, the other after-renders are previews of pending payloads.

- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431227629299_d.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431227629299_m.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431227629299_md.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431227630281_d.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431227630281_m.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431227630281_md.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431227630284_d.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431227630284_m.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431227630284_md.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431227630300_d.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431227630300_m.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431227630300_md.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431227630303_d.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431227630303_m.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431227630303_md.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431240829671_d.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431240829671_m.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431240829671_md.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431240830653_d.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431240830653_m.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431240830653_md.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431240830688_d.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431240830688_m.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431240830688_md.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431261790963_d.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431261790963_m.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431261790963_md.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431261790966_d.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431261790966_m.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431261790966_md.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431261790969_d.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431261790969_m.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431261790969_md.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431261791945_d.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431261791945_m.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431261791945_md.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431261791960_d.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431261791960_m.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431261791960_md.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431278272203_d.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431278272203_m.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431278272203_md.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431280829127_d.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431280829127_m.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/after_431280829127_md.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431227629299_d.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431227629299_m.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431227629299_md.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431227630281_d.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431227630281_m.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431227630281_md.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431227630284_d.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431227630284_m.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431227630284_md.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431227630300_d.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431227630300_m.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431227630300_md.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431227630303_d.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431227630303_m.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431227630303_md.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431240830653_d.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431240830653_m.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431240830653_md.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431240830688_d.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431240830688_m.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431240830688_md.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431261790966_d.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431261790966_m.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431261790966_md.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431261790969_d.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431261790969_m.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431261790969_md.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431261791945_d.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431261791945_m.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431261791945_md.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431261791960_d.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431261791960_m.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431261791960_md.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431278272203_d.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431278272203_m.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431278272203_md.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431280829127_d.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431280829127_m.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/before_431280829127_md.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/nobg_431261791960_d.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/nobg_431261791960_m.png
- /tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa_email_shots/nobg_431261791960_md.png

## D. Changes made in HubSpot (6 draft emails, full 7-widget PATCH each, read back)

| Email id | Field | Old | New |
|---|---|---|---|
| `431227630300` | hero headline (module-0-0-0) | Check-up (56px) | A head start (38px) |
| `431227630300` | hero wrapper hs_wrapper_css.background-color | (none) | #004B87 |
| `431227630300` | hook line (h1, module-1-0-0) | We already know your setup, so a security check-up starts well ahead. | When did anyone last review your office security? |
| `431227630300` | italic accent line (module-1-0-0) | no new vendor to explain everything to | a check-up is an easy way to find out |
| `431227630303` | hero headline (module-0-0-0) | Proof (56px) | Answers on file (38px) |
| `431227630303` | hero wrapper hs_wrapper_css.background-color | (none) | #004B87 |
| `431240829671` | hero headline (module-0-0-0) | Built in (56px) | Security, built in (38px) |
| `431240829671` | hero wrapper hs_wrapper_css.background-color | (none) | #004B87 |
| `431240829671` | hook line (h1, module-1-0-0) | Security is easier when it is part of everyday IT. | Who checks that every laptop in your office is up to date? |
| `431240829671` | italic accent line (module-1-0-0) | not a separate project to remember | security is easier when it is part of everyday IT |
| `431261790963` | hero headline (module-0-0-0) | Review (56px) | Inside an IT review (38px) |
| `431261790963` | hero wrapper hs_wrapper_css.background-color | (none) | #004B87 |
| `431261790963` | subject | Inside a free IT review: what to expect | Inside an IT review: what to expect |
| `431261791960` | hero headline (module-0-0-0) | Renew? (56px) | Pause before you renew (38px) |
| `431261791960` | hero wrapper hs_wrapper_css.background-color | (none) | #004B87 |
| `431261791960` | closing paragraph (module-3-0-0) | Over the next few months we will send short notes on reading a lease, cost per page, and a simple renewal countdown. | Over the next few months we will send short notes on reading a lease, cost per page, and what to ask about service. |
| `431280829127` | hero headline (module-0-0-0) | Next step (56px) | Three easy ways in (38px) |
| `431280829127` | hero wrapper hs_wrapper_css.background-color | (none) | #004B87 |
| `431280829127` | hook line (h1, module-1-0-0) | One team, one monthly plan, one number to call. | The next step can be as small as a reply. |
| `431280829127` | italic accent line (module-1-0-0) | here is where that leaves us | whenever the timing suits you |

Also, on `431227630303` I ran a test PATCH that sent module-1..5 widgets without bodies. HubSpot replaced them (blank bodies) and I restored the full original content in the next call; the final read back matches the original except for the intended hero change. Lesson: a PATCH widget replaces that widget completely, not just the widget set.

Final read-back of all 58 emails (one list call): all still AUTOMATED_DRAFT, unpublished, six modules with non-empty bodies plus preview_text, `56px` hero remains in 52.

### Not applied yet (ready)
Payload files for the 52 emails still on the one-word hero (full 7 widgets, tested method): `/tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa/payloads/<id>.json`. Hero phrases: `/tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa/build_fix.py` (HERO). Regenerate with `python3 -I qa/build_fix.py`. Each file is the exact JSON body for `PATCH /marketing/v3/emails/<id>`.

### plan_data.json
Updated (subject/body) for the 5 emails whose copy changed: L6 E4 subject, L1 E1 closing (3 lanes), L3 E8 hook and accent, L4 E1 hook and accent, L6 E6 hook and accent. Hero headlines are not in plan_data bodies, so nothing to update there. Backup of the previous file: `/tmp/claude-0/-home-user-Claude/d363302e-6199-53ff-909a-b855e523360f/scratchpad/lease/qa/plan_data.before_qa.json`.

## Open flags (need a human)
1. Apply the remaining 52 hero fixes (payloads ready).
2. Lease path timing vs lease end date (L1a, L1b).
3. L5 and L6 service claims, L3 E1 "we also look after IT" and L4 "we already know your equipment" need GoodSuite confirmation.
4. L2e first person voice vs From "GoodSuite"; "Reply or book" CTA.
5. Subscription types for sales emails (Education & Events).
6. Template social row overflow at 375px (template edit needed).
7. Repeated sign-offs, hooks and cross-lane topics (NNC vs L4, L6 E6).
8. Word counts 160 to 167 on NNC E1/E2/E4/E7 and L4 E1.
9. Unsupported "Most ..." generalisations in NNC E1/E2 and L1 E1.
10. US spelling nit: "afterwards" in NNC E6 and L6 E4 vs "afterward" elsewhere.
