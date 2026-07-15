---
name: qbs-automation-scout
description: "Proactively identify automation opportunities in any task, project, or workflow the QBS team discusses. Use this skill whenever anyone on the team describes a manual process, repetitive task, multi-step workflow, client deliverable, data entry, reporting routine, content creation process, follow-up sequence, or operational procedure. Also trigger when someone says things like 'I have to do this every week', 'I manually check...', 'I copy this from X to Y', 'every time a deal closes I...', 'I wish I didn't have to...', 'this takes too long', 'we do this for every client', or describes any task that sounds repetitive, time-consuming, or error-prone. Even if the user isn't asking about automation — if they describe a workflow that COULD be automated, flag it. The goal is to eliminate manual work across QBS operations by finding automation opportunities the team might not even realize exist."
---

# QBS Automation Scout

## Purpose

This skill watches for automation opportunities in every conversation. When someone describes how they do something, this skill evaluates whether part or all of it could be automated using QBS's existing technology stack. It surfaces opportunities the team might not think to ask about.

## When to Use

**Explicit triggers** — someone asks about automation directly:
- "Can we automate this?"
- "How do I automate..."
- "Is there a way to not do this manually?"

**Implicit triggers** — someone describes a process that COULD be automated:
- Any repetitive task ("every week I...", "for each client I...", "whenever a deal closes I...")
- Manual data movement ("I copy from X to Y", "I export the CSV then...")
- Time-consuming processes ("this takes me 2 hours every Monday")
- Error-prone tasks ("sometimes I forget to...", "I missed updating...")
- Client-by-client work ("I do this for every client", "each onboarding I have to...")
- Reporting routines ("I pull this report every month")
- Follow-up sequences ("after the meeting I always send...")
- Content creation patterns ("every week I write a blog post about...")

## Process

### Step 1: Map the Current Workflow

Break down what the person described into discrete steps:

1. What triggers the work? (time-based, event-based, manual)
2. What data is involved and where does it come from?
3. What transformations or decisions happen?
4. Where does the output go?
5. How often does this happen?
6. How long does it take manually?
7. What could go wrong if forgotten or done incorrectly?

### Step 2: Score the Automation Opportunity

Rate each workflow on these dimensions:

| Factor | High Value (automate this) | Low Value (probably skip) |
|--------|---------------------------|--------------------------|
| **Frequency** | Daily/weekly | Once a quarter |
| **Time cost** | 30+ minutes each time | 2 minutes |
| **Error risk** | Mistakes have consequences | Low stakes |
| **Complexity** | Multi-step, multi-system | Single action |
| **Repeatability** | Same steps every time | Highly variable each time |
| **Data availability** | All data in accessible systems | Requires human judgment |

If 3+ factors score "High Value," recommend automation. Present the score to the team so they can prioritize.

### Step 3: Design the Automation

For each opportunity, map it to the QBS stack. Read `references/automation-patterns.md` for the full pattern library.

**Identify the automation tier:**

**Tier 1 — Zero-code (Zapier/HubSpot workflows):**
- Simple trigger → action flows
- Data syncing between two tools
- Notification/alert rules
- Implementation: minutes to hours
- Example: "When deal closes in HubSpot, send Slack notification"

**Tier 2 — Low-code (n8n workflows):**
- Multi-step flows with branching logic
- Data transformation between systems
- Scheduled batch operations
- Webhook processing with conditional routing
- Implementation: hours to a day
- Example: "Every Monday, pull weekly metrics from HubSpot, format report, email to team"

**Tier 3 — Custom code (Supabase Edge Functions):**
- Complex business logic
- Real-time event processing
- API orchestration with error handling
- Integration with AI (Claude API)
- Implementation: days
- Example: "When new lead enters HubSpot, enrich with ZoomInfo + FullEnrich, score with Claude, route to right rep"

**Tier 4 — AI-powered automation (Claude API + agents):**
- Content generation workflows
- Intelligent decision-making
- Natural language processing
- Document analysis and summarization
- Implementation: days to a week
- Example: "When client uploads contract, Claude extracts key terms, creates summary, flags risks, stores in ClientCommand"

**Tier 5 — Full agent automation (Open Claw + Hindsight):**
- Autonomous multi-step workflows
- Learning from outcomes over time
- Complex tool orchestration
- Personalized per-client behavior
- Implementation: weeks
- Example: "BrandCommand content agent monitors trending topics, generates articles, creates social posts, schedules publishing, learns what performs best"

### Step 4: Present the Recommendation

Format every automation recommendation like this:

**What you're doing manually:**
[Describe the current manual process]

**What it would look like automated:**
[Describe the automated version]

**Tools involved (all already in your stack):**
[List the specific tools and how they connect]

**Automation tier:** [1-5]

**Implementation effort:** [time estimate]

**Time saved:** [per week/month estimate]

**Data flow:**
[Trigger] → [Step 1 tool] → [Step 2 tool] → [Output destination]

**Risk/gotchas:**
[What to watch out for — rate limits, edge cases, approval steps that should stay manual]

### Step 5: Flag What Should Stay Manual

Not everything should be automated. Flag these as "keep manual":

- **High-stakes client communication** — AI can draft, human should review and send
- **Financial approvals** — automate the prep, keep the approval human
- **Strategic decisions** — automate the data gathering, keep the decision human
- **First-time processes** — automate after you've done it manually enough times to know the pattern
- **Creative direction** — automate execution, keep direction human

The recommended pattern for these is **semi-automation**: automate everything up to the decision point, present it to a human for approval, then automate everything after approval.

## Common Automation Opportunities at QBS

These are patterns the team should watch for:

### Client Onboarding
- **Manual**: Create portal, set up HubSpot properties, send welcome email, schedule kickoff, create project plan
- **Automated**: HubSpot deal stage change → Edge Function creates ClientCommand portal → auto-populates from deal data → sends templated welcome via Microsoft 365 → creates calendar invite via Graph API → generates project plan from template

### Weekly Reporting
- **Manual**: Pull HubSpot reports, format in spreadsheet, email to stakeholders
- **Automated**: n8n scheduled workflow → HubSpot API pull → data formatting → Claude API for narrative summary → email via Microsoft 365 Graph API

### Content Pipeline
- **Manual**: Research topics, write articles, create social posts, schedule publishing
- **Automated**: Semrush API identifies keyword gaps → Claude API generates content brief → BrandCommand agent writes article → Screenshot One captures visuals → Unipile schedules LinkedIn post

### Lead Enrichment & Routing
- **Manual**: New lead comes in, research on ZoomInfo, find mobile on FullEnrich, update HubSpot, assign to rep
- **Automated**: HubSpot workflow trigger → Edge Function calls ZoomInfo API → FullEnrich API → updates contact → lead scoring → round-robin assignment

### Post-Meeting Follow-up
- **Manual**: After call, write notes, update HubSpot, send follow-up email, create tasks
- **Automated**: Zoom recording → transcript → Claude API summarizes and extracts action items → HubSpot note created → follow-up email drafted in Outlook → tasks created in ClientCommand

### Commission Calculation
- **Manual**: Export deals, look up rates, calculate commissions, create reports
- **Automated**: HubSpot deal close → webhook to Commission Command → auto-calculation → report generation → notification to rep

### Competitor Monitoring
- **Manual**: Check competitor websites, note changes, report to team
- **Automated**: Scheduled Firecrawl scrape → Claude API compares to previous version → alerts on changes → stores in BrandCommand knowledge base

## Integration Quick Reference

When designing automations, use this to pick the right connector:

| From → To | Method |
|-----------|--------|
| HubSpot → Supabase | HubSpot webhook → Edge Function |
| Supabase → HubSpot | Edge Function → HubSpot API |
| Any tool → Any tool | n8n webhook workflow or Zapier |
| Scheduled task | n8n cron trigger or Supabase pg_cron |
| AI processing | Supabase Edge Function → Claude API |
| LinkedIn action | Supabase Edge Function → Unipile API |
| Email sending | Edge Function → Microsoft Graph API |
| File processing | Edge Function → Vectorize.io pipeline |
| Video generation | Edge Function → Runway Gen 4.5 API |
| Web scraping | Edge Function → Firecrawl API |
| Screenshots | Edge Function → Screenshot One API |
