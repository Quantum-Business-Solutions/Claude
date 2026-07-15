---
name: qbs-stack-solver
description: "Solve problems, address needs, and plan builds using QBS's existing technology stack BEFORE recommending any new tools. Use this skill whenever anyone on the QBS team describes a challenge, need, feature request, workflow problem, integration question, or asks 'how would we do X' or 'can we build Y' or 'what tool should we use for Z.' Also trigger on phrases like 'I need a way to...', 'how do I automate...', 'what's the best approach for...', 'can we connect X to Y', 'is there a way to...', or when someone is evaluating a new tool purchase. This skill should trigger BEFORE suggesting any external tool, SaaS product, or new technology. Even if the user names a specific new tool ('should we get Apify?'), run the stack check first to see if existing tools already cover the need. The goal is maximum productivity from what QBS already owns."
---

# QBS Stack Solver

## Purpose

This skill helps the QBS team solve problems and build features using their existing 37-tool technology stack before recommending anything new. It prevents tool sprawl, reduces costs, and ensures the team gets full value from what they already own.

## When to Use

- Someone describes a problem, need, or challenge
- Someone asks "how would we build X" or "can we do Y"
- Someone is evaluating a new tool purchase
- Someone asks which tool to use for a task
- Someone needs to connect systems or automate a workflow
- Someone is planning a new feature for any QBS product
- Any time a solution is being discussed

## Process

### Step 1: Understand the Need

Clarify what the person is trying to accomplish. Ask:
- What's the specific outcome they want?
- Is this a one-time task or ongoing automation?
- Which QBS product(s) does this relate to?
- What data needs to flow and between which systems?
- What's the trigger (manual, scheduled, event-driven)?

### Step 2: Search the Stack

Read `references/tech-stack.md` for the complete tool inventory with capabilities, APIs, and integration points.

For every tool in the stack, evaluate:
1. Does this tool have a capability that addresses the need?
2. Does this tool have an API or integration that enables the workflow?
3. Can multiple existing tools be chained together to solve this?

### Step 3: Propose Solutions (Stack-First)

Present solutions in this priority order:

**Priority 1 — Single existing tool solves it:**
"You already have [Tool] which does exactly this. Here's how to use it for this need: [specific steps]."

**Priority 2 — Multiple existing tools chained together:**
"You can combine [Tool A] + [Tool B] + [Tool C] to accomplish this. Here's the data flow: [A triggers B via webhook, B processes and sends to C via API]."

**Priority 3 — Existing tool with minor configuration:**
"[Tool] can do this but needs [specific setup/configuration]. Here's what to configure: [steps]."

**Priority 4 — Build it with your development stack:**
"This isn't covered by an existing tool, but you can build it using [Supabase Edge Functions / Lovable / Claude Code]. Here's the approach: [architecture]."

**Priority 5 — New tool genuinely needed:**
Only after exhausting priorities 1-4: "Your current stack doesn't cover [specific capability]. Here's what you'd need and why existing tools can't do it: [gap analysis]. Recommended addition: [tool] because [reason]."

### Step 4: Deliver a Clear Recommendation

Always end with a structured recommendation. Don't just list options — tell the team exactly what to do and why. Use this format:

**RECOMMENDATION:**

1. **Best approach**: State the recommended solution in one sentence. Be opinionated — pick the best path, don't hedge.

2. **Why this over alternatives**: Briefly explain why this approach beats other options. Reference the specific advantages (speed, cost, reliability, existing familiarity).

3. **Tools involved**: List every tool from the stack that participates, and what role each plays:
   - [Tool A] — [specific role: trigger, data source, processing, output, etc.]
   - [Tool B] — [specific role]

4. **Data flow**: Describe the complete chain:
   - **Trigger**: What starts it (event, schedule, manual action)
   - **Input**: Where data comes from
   - **Processing**: What transforms, enriches, or acts on the data
   - **Output**: Where results land and who sees them

5. **Build plan** — Tell the team exactly where to build it and in what order:
   - **Step 1**: [specific action] — build in [Lovable / Claude Code / n8n / Zapier]
   - **Step 2**: [specific action] — build in [tool]
   - **Step 3**: [specific action] — build in [tool]
   - **Estimated effort**: [quick win = hours / medium = 1-3 days / larger build = 1-2 weeks]

6. **What to watch out for**: Flag any gotchas, limitations, or things that could go wrong. Examples:
   - Edge Function timeout limits for long operations
   - API rate limits on specific tools
   - Data format mismatches between systems
   - Auth/permission requirements

7. **Future enhancement** (optional): If there's a natural next step or upgrade path, mention it. Example: "Once this is working, you could extend it to also trigger [X] which would enable [Y]."

### Step 5: Implementation Routing

Always recommend the right build environment for each piece:

| What you're building | Build it in | Why |
|---------------------|-------------|-----|
| New UI page or component | Lovable | Fastest for visual work |
| Supabase Edge Function | Claude Code (VS Code) | Needs full repo context |
| Complex API logic | Claude Code (VS Code) | Multi-file awareness |
| Database schema changes | Claude Code (VS Code) | Migration files needed |
| Simple trigger → action | Zapier | No code, fastest setup |
| Multi-step webhook processing | n8n | Real server, handles heavy ops |
| Heavy browser automation | n8n or hosted service | Edge Functions can't run Playwright |
| Quick prototype / proof of concept | Lovable | See it working in minutes |
| Bug fix or debugging | Claude Code (VS Code) | Can trace across files |
| Strategy or architecture planning | Claude.ai | Big picture thinking |

### Step 6: Offer to Start Building

After presenting the recommendation, always ask: "Want me to start building this?" or "Should I write the prompt for [Lovable/Claude Code] to get this started?" This keeps momentum — the team shouldn't have to figure out the next action themselves.

## Common Patterns

These are frequently-needed patterns that the existing stack already handles:

| Need | Existing Solution |
|------|------------------|
| Send automated LinkedIn messages | Unipile API → Supabase Edge Function → HubSpot trigger |
| Enrich contact with mobile number | FullEnrich API → Supabase Edge Function → HubSpot update |
| Generate content for client | Claude API → BrandCommand agent → review → publish |
| Scrape competitor website | Firecrawl API → Claude API for analysis → store in Supabase |
| Take website screenshots | Screenshot One API → Supabase storage → display in app |
| Automate email outreach | Instantly API → HubSpot contact sync → deliverability monitoring |
| AI video for marketing | Claude API (script) → Runway Gen 4.5 (video) → BrandCommand |
| Give AI agents memory | Hindsight retain/recall/reflect → Open Claw plugin |
| Process documents for AI | Vectorize.io pipeline → chunking/embedding → agent context |
| Voice AI outbound calls | VAPI ("Alex") → HubSpot (logging) → Claude API (conversation) |
| Research a company | Firecrawl + Perplexity + ZoomInfo → Claude API synthesis |
| Build a knowledge base guide | Screenshot One + Claude API → formatted article → publish |
| Track commissions from deals | HubSpot deals/line items → Supabase calculations → Commission Command |
| Client health monitoring | HubSpot activity + Zoom meetings + email data → ClientCommand dashboard |

## Key Architectural Principles

These principles guide solution design at QBS:

1. **All external API calls go through Supabase Edge Functions** — never call third-party APIs directly from the frontend
2. **Event-driven over polling** — only delta changes move across the wire after initial load
3. **HubSpot is the system of record** for contacts, deals, and companies
4. **Supabase is the backend** for all QBS products — database, auth, storage, real-time
5. **Lovable for UI, Claude Code for logic** — use each tool where it's strongest
6. **Edge Functions have limitations** — no headless browsers (use n8n or hosted services for Playwright), timeout limits for long operations
7. **FullEnrich (not Apollo/ZoomInfo) for client-facing data** — reseller-friendly TOS
8. **Modular architecture** — components should be swappable (e.g., Runway → Sora when available)

## Red Flags: When Someone Probably Doesn't Need a New Tool

- "We need a LinkedIn automation tool" → You have Unipile
- "We need a cold email tool" → You have Instantly
- "We need a web scraper" → You have Firecrawl
- "We need a screenshot tool" → You have Screenshot One
- "We need AI for content" → You have Claude API + BrandCommand
- "We need a dialer" → You have Orum + ConnectAndSell
- "We need to enrich contacts" → You have ZoomInfo + FullEnrich
- "We need video generation" → You have Runway Gen 4.5
- "We need agent memory/RAG" → You have Hindsight + Vectorize.io
- "We need a research tool" → You have Perplexity + Firecrawl
- "We need a voice AI" → You have VAPI
- "We need SEO tools" → You have Semrush
- "We need workflow automation" → You have n8n + Zapier
