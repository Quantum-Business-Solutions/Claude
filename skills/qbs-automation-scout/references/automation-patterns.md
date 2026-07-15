# QBS Automation Patterns Reference

## Table of Contents
1. Event-Driven Patterns
2. Scheduled Patterns
3. AI-Powered Patterns
4. Semi-Automation Patterns
5. Cross-Product Patterns

---

## 1. Event-Driven Patterns

These fire when something happens in a system.

### Deal Closed → Multi-System Update
**Trigger**: HubSpot deal moves to "Closed Won"
**Flow**: HubSpot webhook → Supabase Edge Function → parallel calls to:
- Commission Command (calculate commission)
- ClientCommand (create client portal)
- Microsoft 365 (send welcome email)
- Slack/Teams (notify team)
**Tools**: HubSpot, Supabase, Commission Command, ClientCommand, Microsoft 365

### New Lead → Enrich & Score
**Trigger**: New contact created in HubSpot (form fill, import, API)
**Flow**: HubSpot webhook → Edge Function → ZoomInfo API (firmographics) → FullEnrich API (mobile) → Claude API (score lead based on ICP criteria) → HubSpot update (score, owner assignment)
**Tools**: HubSpot, Supabase, ZoomInfo, FullEnrich, Claude API

### Meeting Completed → Intelligence Extraction
**Trigger**: Zoom meeting ends
**Flow**: Zoom webhook → Edge Function → fetch recording/transcript → Claude API (summarize, extract action items, identify next steps) → HubSpot note → ClientCommand meeting record → Microsoft 365 (schedule follow-ups)
**Tools**: Zoom, Supabase, Claude API, HubSpot, ClientCommand, Microsoft 365

### Email Reply Received → Route & Respond
**Trigger**: Instantly detects reply to cold email campaign
**Flow**: Instantly webhook → Edge Function → Claude API (classify: interested, objection, not interested, OOO) → route:
- Interested → HubSpot deal creation, alert rep
- Objection → draft response for rep review
- Not interested → update status, remove from sequence
- OOO → reschedule follow-up
**Tools**: Instantly, Supabase, Claude API, HubSpot

### Content Published → Multi-Channel Distribution
**Trigger**: Blog post published on client website
**Flow**: Webhook → Edge Function → Claude API (adapt content for each platform) → Unipile (LinkedIn post) → Instantly (email newsletter) → BrandCommand (track performance)
**Tools**: Supabase, Claude API, Unipile, Instantly, BrandCommand

---

## 2. Scheduled Patterns

These run on a timer.

### Weekly Pipeline Report
**Schedule**: Every Monday 7am
**Flow**: n8n cron → HubSpot API (deals by stage, new this week, velocity metrics) → Claude API (generate narrative summary with insights) → Microsoft 365 Graph API (email formatted report to leadership)
**Tools**: n8n, HubSpot, Claude API, Microsoft 365

### Daily Competitor Check
**Schedule**: Every morning 6am
**Flow**: n8n cron → Firecrawl (scrape competitor homepages and product pages) → Claude API (compare to previous version, identify changes) → store diff in Supabase → alert if significant changes found
**Tools**: n8n, Firecrawl, Claude API, Supabase

### Weekly SEO Pulse
**Schedule**: Every Friday
**Flow**: n8n cron → Semrush API (position changes, new keyword opportunities, competitor moves) → Claude API (summarize trends, recommend actions) → BrandCommand (store for content planning)
**Tools**: n8n, Semrush, Claude API, BrandCommand

### Monthly Client Health Check
**Schedule**: 1st of each month
**Flow**: n8n cron → for each active client: HubSpot API (activity, deals, tickets) + product usage data from Supabase → Claude API (health score, risk flags, upsell signals) → ClientCommand (update health dashboard) → alert if any client at risk
**Tools**: n8n, HubSpot, Supabase, Claude API, ClientCommand

### Daily Lead Enrichment Sweep
**Schedule**: Every night 11pm
**Flow**: n8n cron → HubSpot API (contacts missing mobile or company data) → batch ZoomInfo + FullEnrich calls → HubSpot bulk update
**Tools**: n8n, HubSpot, ZoomInfo, FullEnrich

---

## 3. AI-Powered Patterns

These use Claude or other AI as the core processing engine.

### Intelligent Document Processing
**Input**: PDF, Word doc, or email attachment
**Flow**: Vectorize.io (extract text, tables, structure) → Claude API (classify document type, extract key fields, summarize) → route to appropriate system:
- Contract → ClientCommand + extract terms
- Invoice → QuickBooks
- RFP → BrandCommand + generate proposal outline
**Tools**: Vectorize.io, Claude API, ClientCommand, QuickBooks, BrandCommand

### AI-Powered Content Generation
**Input**: Content brief or trending topic
**Flow**: Semrush (keyword data) → Claude API (generate article) → Firecrawl (research supporting sources) → Claude API (refine with sources) → Screenshot One (capture relevant visuals) → BrandCommand (format and schedule)
**Tools**: Semrush, Claude API, Firecrawl, Screenshot One, BrandCommand

### AI Video Production
**Input**: Topic or script
**Flow**: Claude API (write script, break into scenes, generate scene prompts) → Runway Gen 4.5 (generate video clips, chain scenes using image-to-video for continuity) → CapCut or Edge Function (stitch clips, add audio) → BrandCommand (publish)
**Tools**: Claude API, Runway Gen 4.5, CapCut, BrandCommand

### Intelligent Meeting Prep
**Input**: Upcoming meeting (from calendar)
**Flow**: Microsoft Graph (get meeting attendees, context) → HubSpot (pull contact/deal history) → Firecrawl (scrape attendee company website for recent news) → Claude API (generate briefing doc with talking points, risks, opportunities) → ClientCommand (store prep doc)
**Tools**: Microsoft 365, HubSpot, Firecrawl, Claude API, ClientCommand

### Proposal Generation
**Input**: Discovery call completed
**Flow**: Zoom transcript → Claude API (extract requirements, pain points, budget signals) → ClientCommand (populate discovery findings) → Claude API (generate proposal sections, pricing, timeline) → format as ClientCommand Discovery Deck
**Tools**: Zoom, Claude API, ClientCommand

---

## 4. Semi-Automation Patterns

Human stays in the loop for approval/review.

### Draft → Review → Send
**Pattern**: AI generates draft, human reviews, system sends
**Example**: Claude API drafts follow-up email → displayed in ClientCommand for review → human edits and approves → Microsoft Graph sends → HubSpot logs activity
**When to use**: Any external communication, proposals, contracts

### Prepare → Approve → Execute
**Pattern**: System gathers data and prepares action, human approves, system executes
**Example**: Commission Command calculates payroll amounts → displays for manager review → manager approves → system generates reports / triggers payroll sync
**When to use**: Financial actions, permission changes, data deletions

### Generate → Curate → Publish
**Pattern**: AI creates content, human curates/edits, system publishes
**Example**: BrandCommand generates 5 LinkedIn post options → human picks best and edits → Unipile publishes → BrandCommand tracks performance
**When to use**: Public-facing content, social media, blog posts

---

## 5. Cross-Product Patterns

These span multiple QBS products.

### Full Client Lifecycle
**Flow**: 
1. Lead enters HubSpot (enriched by ZoomInfo + FullEnrich)
2. Outreach via Instantly (email) + Unipile (LinkedIn) + Orum (calls)
3. Meeting booked → Zoom → transcript → ClientCommand discovery
4. Proposal generated in ClientCommand
5. Deal closes in HubSpot
6. ClientCommand portal created automatically
7. Commission Command calculates rep commission
8. BrandCommand starts marketing services
9. DocCommand manages ongoing documents
10. ClientCommand monitors health ongoing

### Content Engine
**Flow**:
1. Semrush identifies keyword opportunities
2. Claude API generates content brief
3. BrandCommand agent writes article
4. Screenshot One / Firecrawl gather visuals and data
5. Claude API generates social adaptations
6. Unipile publishes to LinkedIn
7. Instantly distributes via email
8. Semrush tracks ranking impact
9. Hindsight remembers what performed well → improves future content

### AI Agent Learning Loop
**Flow**:
1. Agent (Open Claw) handles task using Claude API
2. Hindsight retains the interaction
3. Outcome tracked (success/failure/feedback)
4. Hindsight reflects on patterns
5. Next similar task → agent recalls past experiences
6. Agent adjusts approach based on learned patterns
7. Quality improves over time without code changes
