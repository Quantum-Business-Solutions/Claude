# QBS Technology Stack Reference

## Table of Contents
1. CRM & Sales
2. Outbound & Engagement
3. Enrichment
4. Communication
5. Development & Infrastructure
6. Automation & Integration
7. AI & Agents
8. Scraping & Research
9. Marketing & Content
10. Finance
11. QBS Products

---

## 1. CRM & Sales

### HubSpot
- **Type**: CRM platform (Sales Hub Enterprise, Marketing Hub Pro, Content Starter, Sales Pro)
- **Capabilities**: Pipeline management, email sequences, deal tracking, marketing automation, reporting, custom objects, workflows, forms, landing pages, API access
- **APIs**: REST API, webhooks, custom coded actions, MCP server
- **Integrates with**: All QBS products, ZoomInfo, Orum, Instantly, Unipile, Microsoft 365, Zapier, n8n
- **Good for**: Contact/deal management, email automation, sales pipeline, marketing campaigns, reporting dashboards, workflow triggers

### LinkedIn Sales Navigator
- **Type**: Prospecting tool
- **Capabilities**: Advanced search, lead lists, account monitoring, InMail, saved searches, alerts
- **Integrates with**: HubSpot (lead sync), Unipile (messaging), ZoomInfo (enrichment)
- **Good for**: Finding decision-makers, building target account lists, monitoring prospect activity

---

## 2. Outbound & Engagement

### Orum
- **Type**: Parallel dialer
- **Capabilities**: AI-powered multi-line dialing, live connect, voicemail drop, call recording, analytics, CRM sync
- **Integrates with**: HubSpot (contact lists, activity logging)
- **Good for**: High-volume outbound calling, increasing live conversation rate

### ConnectAndSell
- **Type**: Outbound calling with agent navigation
- **Capabilities**: Live agent gatekeeping, phone tree navigation, CRM logging, call analytics
- **Integrates with**: HubSpot
- **Good for**: Getting past gatekeepers, executive-level outreach

### Drop Cowboy
- **Type**: Ringless voicemail
- **Capabilities**: Voicemail drops without ringing, campaign management, delivery tracking
- **Integrates with**: HubSpot, n8n, Zapier
- **Good for**: Top-of-funnel awareness, follow-up campaigns, non-intrusive outreach

### Instantly
- **Type**: Cold email platform
- **Capabilities**: Inbox rotation, email warmup, deliverability monitoring, A/B testing, campaign analytics, multi-account management, API access
- **Integrates with**: HubSpot, ZoomInfo, Supabase (via API/webhooks)
- **Good for**: Scaled cold email outreach, multi-domain sending, deliverability optimization

### Unipile
- **Type**: LinkedIn API platform
- **Capabilities**: LinkedIn messaging, connection requests, profile data access, content publishing, InMail API
- **APIs**: REST API for LinkedIn actions
- **Integrates with**: BrandCommand, HubSpot, Supabase Edge Functions, Sales Navigator
- **Good for**: Automated LinkedIn outreach, content publishing, messaging at scale without scraping

### VAPI
- **Type**: Voice AI platform
- **Capabilities**: AI-powered outbound calls, natural conversation, lead qualification, appointment booking, call recording, custom voice personas
- **APIs**: REST API, webhooks
- **Integrates with**: HubSpot, Claude API, Microsoft 365
- **Good for**: AI SDR ("Alex"), autonomous outbound calling, after-hours lead qualification

---

## 3. Enrichment

### ZoomInfo
- **Type**: B2B intelligence platform
- **Capabilities**: Contact data, company firmographics, org charts, technographics, intent signals, direct dials, email addresses
- **APIs**: REST API, webhooks, bulk enrichment
- **Integrates with**: HubSpot, Orum, Instantly, Sales Navigator
- **Good for**: Prospect research, data enrichment, ICP identification, technographic targeting

### FullEnrich
- **Type**: Contact enrichment (mobile numbers)
- **Capabilities**: Verified mobile phone numbers, waterfall enrichment across multiple data providers
- **APIs**: REST API
- **Key advantage**: Reseller-friendly TOS — safe to embed in client-facing platforms (unlike Apollo/ZoomInfo)
- **Integrates with**: HubSpot, BrandCommand, Supabase Edge Functions
- **Good for**: Mobile number enrichment for BrandCommand clients, compliant data embedding

---

## 4. Communication

### Microsoft 365 / Outlook
- **Type**: Business communication suite
- **Capabilities**: Email, calendar, contacts, Teams, OneDrive, SharePoint
- **APIs**: Microsoft Graph API (email, calendar, contacts, files, Teams data)
- **Integrates with**: HubSpot, ClientCommand, BrandCommand, Zoom
- **Good for**: Email integration, calendar sync, meeting data, file access across QBS products

### Zoom
- **Type**: Video conferencing
- **Capabilities**: Video meetings, recording, transcription, breakout rooms, webinars
- **APIs**: REST API, MCP server for meeting data access
- **Integrates with**: ClientCommand, HubSpot, Microsoft 365
- **Good for**: Client meetings, demos, internal calls, meeting intelligence

### Loom
- **Type**: Video messaging
- **Capabilities**: Screen recording, camera recording, viewer analytics, comments, sharing
- **Integrates with**: HubSpot (notes), ClientCommand (portals)
- **Good for**: Async client updates, feature walkthroughs, bug reports, internal communication

---

## 5. Development & Infrastructure

### Lovable
- **Type**: AI frontend app builder
- **Capabilities**: Natural language to React UI, component generation, GitHub sync, preview environments, knowledge base
- **Integrates with**: GitHub (auto-sync), all QBS products
- **Good for**: Rapid UI prototyping, new pages, visual changes, frontend iteration

### Supabase
- **Type**: Backend-as-a-service
- **Capabilities**: PostgreSQL database, authentication, Edge Functions (Deno runtime), real-time subscriptions, file storage, row-level security, connection pooling
- **APIs**: REST API, client libraries, real-time WebSocket
- **Integrates with**: All QBS products, all external APIs (via Edge Functions)
- **Good for**: Database, auth, serverless functions, storage, real-time features. ALL external API calls route through Edge Functions for security.

### React / TypeScript
- **Type**: Frontend framework
- **Capabilities**: Component-based UI, type safety, hooks, state management
- **Good for**: All frontend code across QBS products

### GitHub
- **Type**: Version control
- **Capabilities**: Git repos, pull requests, CI/CD, Actions, code review
- **Integrates with**: Lovable (auto-sync), Claude Code (local clone), Supabase (deployment)
- **Repos at**: C:\Users\ShawnPeterson\Projects (BrandCommand, clientcommand, commissioncommand, doccommand, qbswebsite, quantumcommand)
- **Good for**: Code management, collaboration, deployment pipeline

### VS Code + Claude Code
- **Type**: AI-powered coding environment
- **Capabilities**: File browsing, code editing, AI-assisted coding across all repos simultaneously, terminal access, Git integration, multi-file refactoring, debugging
- **Integrates with**: GitHub, all QBS repos
- **Good for**: Complex logic, Edge Functions, API integrations, debugging, multi-file changes that Lovable can't handle

### GoDaddy
- **Type**: Domain & DNS management
- **Good for**: Domain registration, DNS records for all QBS properties

### Proofpoint
- **Type**: Email security
- **Capabilities**: SPF, DKIM, DMARC configuration, email authentication
- **Integrates with**: Instantly, Microsoft 365, HubSpot
- **Good for**: Email deliverability, anti-spoofing protection

### Postman
- **Type**: API testing
- **Capabilities**: Request building, testing, documentation, environment variables, collections
- **Good for**: Validating API integrations, debugging, documenting endpoints

---

## 6. Automation & Integration

### n8n
- **Type**: Workflow automation (self-hosted)
- **Capabilities**: Visual workflow builder, webhook processing, multi-step API orchestration, code nodes, error handling. Runs on a real server (not serverless).
- **Key advantage**: Can run Playwright and other heavy operations that Edge Functions cannot
- **Integrates with**: HubSpot, Supabase, Zapier, any API
- **Good for**: Complex multi-step workflows, heavy operations, webhook processing

### Zapier
- **Type**: Cloud automation
- **Capabilities**: Trigger/action workflows, 6000+ app integrations, MCP connector for Claude
- **Integrates with**: HubSpot, n8n, Claude API
- **Good for**: Simple integrations, Claude-triggered workflows, connecting tools without code

---

## 7. AI & Agents

### Anthropic / Claude API
- **Type**: Primary AI engine
- **Capabilities**: Text generation, analysis, coding, reasoning, tool use, vision, long context
- **APIs**: Messages API, tool use, streaming
- **Integrates with**: All QBS products (via Supabase Edge Functions), Open Claw, Hindsight
- **Good for**: Content generation, proposals, analysis, agent personas, code generation

### OpenAI API
- **Type**: Secondary AI engine
- **Capabilities**: Text generation, embeddings, image generation, audio, tool use
- **Integrates with**: BrandCommand, Supabase, Hindsight
- **Good for**: Model comparison, fallback, specific tasks, embeddings

### Google Gemini
- **Type**: Additional AI engine
- **Capabilities**: Text generation, multimodal, long context, code generation
- **Integrates with**: Supabase Edge Functions
- **Good for**: Multi-model workflows, tasks requiring different capabilities

### Open Claw
- **Type**: AI agent framework
- **Capabilities**: Autonomous agents, tool use, decision-making, multi-step workflows, plugin system
- **Integrates with**: Claude API, Hindsight (memory plugin), BrandCommand
- **Good for**: Building AI agents that can use tools and make decisions autonomously

### Vectorize.io
- **Type**: Context engineering platform
- **Capabilities**: Document processing (PDF, Word, presentations, images), data extraction, chunking, embedding, indexing, semantic search, metadata filtering
- **Integrates with**: Hindsight, BrandCommand, Claude API
- **Good for**: RAG pipelines, document ingestion, delivering optimized context to agents

### Vectorize Hindsight
- **Type**: Agent memory system
- **Capabilities**: retain() stores memories, recall() searches them, reflect() reasons over them. Separates facts, experiences, observations, and mental models. Time-aware retrieval. Per-user memory banks.
- **Integrates with**: Open Claw (plugin), Claude API, OpenAI, BrandCommand
- **Good for**: Persistent agent memory, agents that learn over time, personalized AI interactions, multi-session continuity

### Runway Gen 4.5
- **Type**: AI video generation
- **Capabilities**: Text-to-video, image-to-video, 1280x720, 5-second clips per scene, API access
- **APIs**: api.dev.runwayml.com
- **Integrates with**: BrandCommand, Supabase Edge Functions, Claude API (for script generation)
- **Good for**: Automated marketing video creation, scene generation, visual content production

---

## 8. Scraping & Research

### Firecrawl
- **Type**: Web content extraction
- **Capabilities**: Website crawling, JS rendering, markdown conversion, structured data extraction, MCP server
- **APIs**: REST API, MCP server
- **Integrates with**: BrandCommand, Claude API, Supabase
- **Good for**: Scraping websites into LLM-ready content, competitor research, content ingestion

### Screenshot One
- **Type**: Website screenshot API
- **Capabilities**: Full-page screenshots, element screenshots, PDF generation, custom viewport sizes
- **APIs**: REST API (already configured in BrandCommand)
- **Integrates with**: BrandCommand, Supabase Edge Functions
- **Good for**: Automated guide generation, website audits, visual documentation, competitor monitoring

### Perplexity
- **Type**: AI research assistant
- **Capabilities**: Sourced real-time web answers, multi-step research, citation tracking
- **Integrates with**: BrandCommand, ClientCommand
- **Good for**: Quick market research, competitor intelligence, fact-checking

---

## 9. Marketing & Content

### Semrush
- **Type**: Enterprise SEO platform
- **Capabilities**: Keyword research, competitor analysis, SERP tracking, backlink monitoring, content gap analysis, site audit, position tracking
- **APIs**: REST API
- **Integrates with**: BrandCommand (deep integration), Claude API
- **Good for**: SEO strategy, keyword targeting, content planning, competitive intelligence

### CapCut
- **Type**: Video editing
- **Capabilities**: Video editing, AI video generation, templates, effects, social format export
- **Integrates with**: BrandCommand, Runway
- **Good for**: Social content editing, short-form video, AI-assisted video creation

---

## 10. Finance

### QuickBooks
- **Type**: Accounting
- **Capabilities**: Invoicing, expense tracking, revenue reporting, payroll, client billing
- **APIs**: REST API, MCP connector
- **Integrates with**: Commission Command (future payroll sync via Finch API)
- **Good for**: Financial management, invoicing, expense tracking, future commission payroll integration

---

## 11. QBS Products

### Commission Command
- **Focus**: Dealer commission tracking SaaS
- **Stack**: React/TypeScript + Supabase + HubSpot
- **Key integrations**: HubSpot (deals, line items), QuickBooks (future payroll), e-automate/CEO Juice (dealer systems)

### BrandCommand
- **Focus**: AI Marketing Team platform
- **Stack**: React/TypeScript + Supabase + Claude API + Runway Gen 4.5
- **Key integrations**: Semrush (SEO), Unipile (LinkedIn), Hindsight (memory), Firecrawl (web data), Screenshot One (guides), HubSpot, FullEnrich

### ClientCommand
- **Focus**: Client management portal
- **Stack**: React/TypeScript + Supabase + Claude API
- **Key integrations**: HubSpot (deals, contacts), Microsoft 365 (email, calendar), Zoom (meetings)

### DocCommand
- **Focus**: HubSpot-embedded document management
- **Stack**: React/TypeScript + Supabase
- **Key integrations**: HubSpot (deal context, embedding)

### Firmd
- **Focus**: Luxury skincare e-commerce
- **Stack**: React/TypeScript + Supabase
- **Key integrations**: Claude API (recommendations, content)
