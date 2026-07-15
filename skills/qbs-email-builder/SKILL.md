---
name: qbs-email-builder
description: Build branded marketing email campaigns and push them into HubSpot as ready-to-schedule drafts. Use this skill any time the user wants to create marketing emails, build a nurture sequence, plan an email campaign, write emails for a client, draft a multi-email program, or generate emails for HubSpot — even if they don't mention HubSpot explicitly. Trigger on phrases like "create emails", "build a campaign", "nurture sequence", "email program", "draft marketing emails", "email series for [company]", or "push emails to HubSpot". The skill researches the target company, identifies their audience and voice, generates a strategic topic arc, writes opinionated POV-style emails, and pushes them as designed drafts into HubSpot. Works for both QBS internal marketing and client engagements.
---

# QBS Email Builder

Build marketing email campaigns the QBS way: research-driven, voice-matched to the company's best historical performers, designed to brand, and pushed into HubSpot as ready-to-schedule drafts.

This skill encodes the methodology Quantum Business Solutions uses to build email programs that actually convert — for ourselves and for clients. The pattern came from analyzing what worked across hundreds of B2B sends and isolating the signals that drive opens, clicks, and meeting bookings.

## When to use this skill

Use this skill any time someone wants marketing emails created. Common phrasings:

- "Build a nurture sequence for [company]"
- "Create 5 emails for our [topic] campaign"
- "Draft an email series for our HubSpot"
- "I need emails for [client name] — they sell [thing] to [audience]"
- "Plan a multi-email program around [topic]"

The skill defaults to producing **5–10 emails** (expandable on request) and pushing them to HubSpot as drafts with branded design.

## The workflow

Follow this sequence every time. Each step has a reference file with deeper guidance — read those when you reach the step.

### Step 1 — Capture the brief

Get these answers before researching anything. Ask in one batch using `ask_user_input_v0` if the user hasn't provided them:

1. **Target company** — URL of their website, OR a brief description (company name + what they sell + to whom)
2. **Campaign goal** — what specific action should this drive (book a call, request a demo, download something, reply with interest)
3. **Audience** — who the emails go to (existing customers, cold ICP, lapsed leads, partner network)
4. **Number of emails** — default 5; user can ask for more
5. **HubSpot or file?** — push to HubSpot as drafts (default) or save as files for review first
6. **Cadence (if multi-email)** — weekly Wednesdays 9am CT is the QBS default

If pushing to HubSpot: confirm the user has HubSpot MCP connected OR is willing to provide a Private App Token (PAT). If neither, switch to file-only mode.

### Step 2 — Research the company

Read `references/research.md` for the full research playbook. The condensed version:

- If a URL was provided: fetch the homepage and 2–3 key pages (about, services, blog) using `web_fetch`
- If only a brief was provided: web_search for the company to confirm positioning
- For HubSpot-connected runs: pull the company's **top-performing historical emails** via the Marketing Email API (this becomes the voice template — critical step)
- Identify: their tagline / value prop, ICP language, tone (formal vs. casual), and what they're clearly trying to sell right now

Don't skip the historical email pull when HubSpot is available. **Voice-matching to proven winners is the #1 lift in this skill** — it's why the emails sound like the company instead of like a generic AI draft.

### Step 3 — Build the topic arc

Read `references/topic-arcs.md` for proven arc patterns and topic-generation guidance.

Strong topic arcs share these traits:
- Each topic is a **specific pain point** the audience has *this week* — not "10 tips for X"
- Topics are framed as **opinionated POVs**, not neutral overviews ("Your CRM is lying to you about pipeline" beats "How to improve your CRM")
- The arc has a story: foundation → tactical fixes → harder topics → planning/finale
- Topics map to the campaign goal (every topic should plausibly motivate the desired action)

Generate the topic list. Show it to the user before writing any email body. Confirm before proceeding.

### Step 4 — Write the emails

Read `references/email-formula.md` for the voice and structure template.

Key constraints:
- **140–180 words per email body** (not counting eyebrow/headline). This range matched QBS's best-performing send. Longer emails consistently underperform unless the topic genuinely requires depth.
- **Opinionated, first-person Shawn-voice** (or matched to the target company's voice if doing client work)
- **One framework per email** (numbered list, contrast pair, before/after) — not paragraphs of explanation
- **CTA in the closing line as a soft question**, then the button below
- **No spam-trigger words** ("FREE!!!", "ACT NOW", "LIMITED TIME", "GUARANTEE")

For each email, produce: subject, preview text, eyebrow label, headline, body HTML, CTA button text.

### Step 5 — Apply the design system

Read `references/design-system.md` for the full design spec.

The QBS default design (used unless overridden for client work):
- **Navy header** (`#181844`) with the cropped Quantum logo
- **Off-white page background** (`#fafaf7`), white email body
- **Instrument Serif** headlines (38px), **DM Sans** body (17px)
- **Gold** (`#c4a44a`) for CTAs, links, dividers
- **Branded signature block** + partner credentials card + navy footer

For client work, identify the client's brand colors and fonts from their website and substitute. Keep the structural design (navy header bar style, eyebrow → serif headline → body → CTA → branded footer) — only swap the visual tokens.

### Step 6 — Push to HubSpot

Read `references/hubspot-push.md` for the API mechanics.

The push process:
1. Find the user's best-performing recent email via the Marketing Email API — this becomes the structural template
2. Create each email by cloning the template structure and replacing content + design
3. Set send dates (default: weekly Wednesdays 9am CT starting next available Wednesday)
4. Attach recipient lists (default: same lists used by the historical winner email)
5. Create or attach to a campaign for clean reporting
6. Verify each email exists in HubSpot before reporting success
7. Provide direct edit links for each draft

If running in file-only mode, output `.html` files to `/mnt/user-data/outputs/` instead.

### Step 7 — Verify and report

Always verify before declaring success:
- Re-fetch each email by ID from HubSpot to confirm it exists and is in DRAFT state
- Check that all key fields persisted (subject, body, lists, send date)
- Run a quick deliverability scan (HTML size, link domains, spam trigger words, image/text ratio)

Then deliver a clean summary with:
- Table of all emails (number, send date, subject, edit link)
- Any issues found during verification
- A reminder about PAT rotation if a PAT was used

## What NOT to do

These are real mistakes from past iterations of this work — avoid them:

- **Don't write 20+ emails before the user reviews the topic arc.** A bad arc means rewriting all 20. Always confirm topics first.
- **Don't use HubSpot's default style settings.** They produce generic teal-and-gray emails that look templated.
- **Don't put content into the wrong widget type.** The header is an `image_email` widget; bodies and signatures are `rich_text`. Mixing these breaks the editor.
- **Don't skip the deliverability scan.** Spam-trigger words in subject lines kill open rates before anything else matters.
- **Don't write emails longer than 200 words by default.** The data is consistent — short wins.
- **Don't proactively claim a Claude/AI angle replaces the company.** For QBS especially: AI emails should position expertise as essential, not the firm as replaceable.
- **Don't fabricate customer references or specific metrics.** Use directional language ("a regional dealer," "a mid-sized MSP") unless the user provides real names with permission.

## Reference files

- `references/research.md` — How to research a target company and pull voice-matching historical emails
- `references/topic-arcs.md` — Proven topic arc patterns and topic-generation guidance
- `references/email-formula.md` — The 6-element email structure with examples
- `references/design-system.md` — QBS brand spec + adaptation guide for client work
- `references/hubspot-push.md` — HubSpot API mechanics for creating drafts, campaigns, and recipient lists

## Scripts

- `scripts/push_email.py` — Reusable function for creating a single branded email draft in HubSpot. Takes a config dict, returns email ID.
- `scripts/scan_deliverability.py` — Runs a spam-risk analysis on a finished email (HTML size, links, trigger words, image ratio). Use before pushing.
- `scripts/render_preview.py` — Renders an email as a standalone HTML file you can screenshot or share with the user before pushing.
