# AI & Automation Utilization Audit

A comprehensive audit of how the portal uses AI and automation tooling — both HubSpot-native (Breeze) and third-party (Claude, ChatGPT, conversation intelligence, meeting AI).

This is a focused expansion of the Feature Matrix specifically covering AI-era tooling. It answers the question: *"Is this team using the modern AI stack in a way that compounds their efficiency, or are they paying for tools that aren't making a difference?"*

## Scope

Three distinct categories:

1. **HubSpot Native AI (Breeze)** — features available in HubSpot portals, tier-dependent
2. **Third-party AI integrations** — Claude, OpenAI/ChatGPT, other AI connectors  
3. **Conversation & meeting intelligence** — Gong, Chorus, Fireflies, Zoom AI, Read AI, Otter, Grain

Each feature gets: tier availability (if applicable), configured status, actively used status, used-well status.

## Scoring contributions

AI adoption is treated as a Scored feature contributing to **Adoption** and **Integrations** dimensions. The underlying rationale: modern revenue teams using AI well execute significantly more effectively than teams who aren't. Non-use of AI at current tier is a measurable efficiency gap.

| Feature class | Dimension | Weight |
|---|---|---|
| Breeze Copilot, Prospecting, Content, Customer agents | Adoption | Scored |
| AI scoring (Fit, Engagement, Predictive) | Reporting | Scored |
| Conversation intelligence (any) | Integrations | Scored — Critical if calling is active but no CI |
| Claude / ChatGPT connectors | Integrations | Visibility (Scored only if team says it's in workflow) |
| AI workflow actions | Automation | Scored |
| AI-generated content | Adoption | Visibility |

---

## Category 1 — HubSpot Native AI (Breeze)

### BR-01 — Breeze Copilot

**What it is.** HubSpot's in-portal AI assistant. Available across all tiers but with tier-limited depth.

**Detection.**
- Look for Chat Assistant properties (`chat_assistant_*`) on Contact / Company objects
- Check portal settings API (if accessible) for Copilot enablement flag
- Heuristic: Breeze Copilot traces leave property footprints when enabled

**Usage evidence.**
- Impossible to measure per-user usage via public API
- Proxy signal: the team's stated usage in interviews

**Used-well threshold.** Team-wide regular use (self-reported in interview).

**Scoring.** In-tier but not configured: −3 Adoption.

---

### BR-02 — Breeze Prospecting Agent

**What it is.** AI agent that identifies and queues prospects based on ICP criteria + intent signals.

**Detection.**
- Property scan on Company for `prospecting_agent_*` fields
- Workflow scan for "Prospecting" in workflow names
- Lists scan for agent-managed prospect lists

**Usage evidence.**
- Prospects created with `Source: Prospecting Agent`
- Prospects that moved from "Queued" to "Working" state

**Used-well threshold.** Agent configured + prospects generated + >30% of queued prospects actively worked.

**Scoring.** In-tier (Sales Pro+) but not configured: −5 Adoption. Configured but unused: −3.

---

### BR-03 — Breeze Content Agent

**What it is.** AI-generated content for marketing emails, landing pages, blog posts, social posts.

**Detection.**
- Check marketing emails for `ai_generated` or `breeze_*` metadata
- Blog post metadata similar check
- Content remix events in activity logs

**Used-well threshold.** At least one content asset per month generated/remixed via Breeze.

**Scoring.** In-tier (Marketing Pro+) but unused: −2 Adoption (low-weight; content agents are helpful but not critical).

---

### BR-04 — Breeze Customer Agent

**What it is.** AI agent that handles customer service interactions in chat / email.

**Detection.**
- Conversations inbox configured with Breeze routing
- Service Hub properties for customer agent handoff

**Used-well threshold.** Service Pro+ and actively handling >20% of inbound service volume.

**Scoring.** In-tier (Service Pro+) but unused: −3 Adoption.

---

### BR-05 — AI Fit Score

**What it is.** AI-generated 0-100 score predicting how well a contact matches historical customer profiles.

**Detection.**
- Property `ai_fit_score` or similar on Contact
- Workflows that key off Fit Score thresholds

**Used-well threshold.** Score populated on >50% of contacts + at least one workflow keyed off the score.

**Scoring.** In-tier (Marketing Pro+) but unused: −5 Reporting. Auto-critical (−12) if Enterprise tier without predictive scoring.

---

### BR-06 — AI Engagement Score

**What it is.** AI-generated score predicting engagement likelihood.

**Detection.** Same pattern as Fit Score — property scan, workflow keying.

**Scoring.** Pairs with BR-05; similar weight.

---

### BR-07 — Predictive Lead Scoring (Enterprise)

**What it is.** Enterprise-tier AI predictive scoring distinct from standard Fit/Engagement.

**Scoring.** In-tier (Enterprise) but unused: −5 Reporting.

---

### BR-08 — AI Workflow Actions

**What it is.** "Breeze AI" actions within HubSpot workflows — AI-generated text, summarization, enrichment.

**Detection.**
- Inspect workflow action types for "AI" / "Breeze" actions (requires workflow detail API)
- Count of workflows using AI actions

**Used-well threshold.** ≥3 workflows using AI actions in production use.

**Scoring.** Pro+ tier unused: −3 Automation.

---

## Category 2 — Third-party AI connectors

### AI-01 — Claude connector (HubSpot MCP)

**What it is.** Anthropic's Claude accessing HubSpot data via Model Context Protocol. Emerging but increasingly common among forward-leaning revenue teams.

**Detection.**
- Installed app registry scan for "Claude" or "Anthropic"
- Private app scan for Anthropic-originating OAuth grants
- API call pattern analysis: calls from Claude MCP user-agent

**Usage evidence.**
- Recent API calls via Claude app
- Team reports using Claude for HubSpot tasks

**Used-well threshold.** Regular team use (weekly minimum) with at least one documented workflow (research, SOW drafting, meeting prep, reporting).

**Scoring.** Visibility feature. Does not deduct if absent, but presence is a differentiator that appears in the Feature Matrix as a strength signal.

---

### AI-02 — OpenAI / ChatGPT integration

**What it is.** GPT-based integrations, whether via official HubSpot ChatGPT app or custom integrations.

**Detection.**
- Installed apps scan for "ChatGPT", "OpenAI", or known GPT wrapper apps
- Workflows with OpenAI API calls (via custom code actions)

**Used-well threshold.** Active integration with measurable usage.

**Scoring.** Visibility. Either/or with Claude (teams typically pick one).

---

### AI-03 — Perplexity / Research AI

**What it is.** AI research tools (Perplexity, You.com, Exa) used for account research workflows.

**Detection.** App registry + workflow pattern scan.

**Scoring.** Visibility.

---

### AI-04 — Sales enablement AI (Outreach Kaia, Salesloft Drift, Gong Engage)

**What it is.** AI-native sales engagement platforms.

**Detection.** Installed app scan.

**Scoring.** Either/or with sequences (these platforms replace HubSpot sequences for many teams).

---

## Category 3 — Conversation & Meeting Intelligence

This is the most important AI category for revenue teams. Call and meeting recording + AI transcription + AI-extracted insights are the single highest-ROI AI investment most teams make.

### CI-01 — Gong

**What it is.** Leading conversation intelligence platform. Records calls + meetings, transcribes, extracts insights.

**Detection.**
- Installed app registry scan for "Gong"
- Engagement source attribution on calls/meetings showing "Gong"
- Workflow integration patterns

**Used-well threshold.**
- >70% of customer-facing calls captured
- Call review activity (calls viewed, commented)
- Gong insights flowing into HubSpot via integration

**Scoring.** Integrations dimension. Missing CI when calling is active: −12 Integrations auto-critical. CI present but <70% coverage: −8.

---

### CI-02 — Chorus (ZoomInfo)

**What it is.** Conversation intelligence, acquired by ZoomInfo.

**Detection.** Similar pattern to Gong.

**Scoring.** Alternative to Gong; team typically has one or the other.

---

### CI-03 — Fireflies.ai

**What it is.** Meeting transcription + AI notes. Popular with SMB/mid-market.

**Detection.**
- App scan
- Meeting objects with Fireflies source attribution
- Note body contains Fireflies-specific boilerplate

**Scoring.** Lower weight than Gong/Chorus (lighter feature set) but still Scored in Integrations.

---

### CI-04 — Zoom AI Companion

**What it is.** Built into Zoom, provides meeting summaries and action items.

**Detection.**
- Check meetings have AI-generated summaries in notes
- Zoom integration configured

**Usage evidence.**
- Meeting summaries present on >50% of meeting engagements
- Action items extracted and acted on

**Used-well threshold.** Active summaries flowing + AI-extracted action items visible.

**Scoring.** If no other CI tool present, Zoom AI Companion is the baseline. Scored as Integrations +5 for presence.

---

### CI-05 — Read.ai / Otter.ai / Grain / Fathom

**What it is.** Meeting-only AI tools (no call recording, but extensive meeting capture).

**Detection.** App scan + meeting engagement source.

**Critical check — dual-engagement logging.** If Zoom AI Companion AND Read.ai are both configured, meetings are likely being logged twice. This is an **auto-critical Integrations finding** per the anti-patterns catalog (AP-15 Dual Engagement).

**Scoring.** Present with single-source logging: Integrations +3. Dual-engagement: −15 auto-critical.

---

### CI-06 — Salesloft Drift / HubSpot Calling with AI

**What it is.** Native calling tools with AI transcription.

**Detection.**
- HubSpot Calling with AI transcription flag in settings
- Salesloft integration + calling features

**Scoring.** Covered in SH-01/SH-02 feature matrix entries — the AI layer is an add-on signal.

---

### CI-07 — Abstrakt (dealer channel specific)

**What it is.** Compliance-focused call intelligence used in some dealer-channel businesses.

**Detection.** App registry.

**Scoring.** Vertical-specific. For office equipment dealers, Abstrakt presence is a noteworthy strength.

---

## Cross-AI patterns

### AP — AI Theater

Portal shows AI tools installed but:
- Fit Score populated on <10% of contacts
- No workflow keyed off any AI score
- CI tool installed but no call reviews happening
- Breeze Copilot enabled but no team mention of usage

Treatment: **High finding in Adoption** — team has invested in AI tooling without operationalizing it. Recommendation is usually training + workflow design, not more tools.

### AP — AI Shelfware

Portal has multiple overlapping AI tools (Breeze + Claude + ChatGPT + Gong + Fireflies) but uses none consistently. Indicates purchasing without strategy.

Treatment: **Medium finding in Integrations** with recommendation to consolidate.

### AP — AI Under-Investment

Portal on Pro+ tiers with zero AI adoption:
- No Fit Score, no Engagement Score, no Breeze Prospecting
- No CI tool despite active calling
- No AI workflow actions

Treatment: **High finding across Adoption + Integrations + Reporting**. Portal is paying Pro+ prices without Pro+ execution.

---

## Presentation in the deliverable

A dedicated **AI & Automation Utilization** section appears in the Feature Utilization Matrix area, with these subsections:

1. **HubSpot Native AI (Breeze)** — matrix table of BR-01 through BR-08
2. **Third-party AI** — matrix of AI-01 through AI-04 (visibility-weighted, shows presence/absence)
3. **Conversation & Meeting Intelligence** — matrix of CI-01 through CI-07
4. **AI strength narrative** — one-paragraph summary of where AI is strong, where it's weak
5. **AI opportunity overlay** — 1-3 targeted recommendations: the single highest-leverage AI move for this portal

The AI section follows the existing matrix formatting conventions: colored status cells (green/amber/red/gray), Notes column with specific evidence, headline summary after each hub/category table.

---

## Detection method additions required

The existing `hs_feature_detect.py` needs new methods:

1. `list_installed_apps()` — scan the app marketplace integrations for the portal. Returns a list of installed apps with metadata.
2. `detect_ai_features(profile, installed_apps)` — runs the full AI audit pass
3. `check_dual_engagement_logging(apps, engagements)` — the Dual Engagement auto-critical check
4. `detect_conversation_intelligence(apps, engagements)` — CI-specific detection

These methods should be additive to the existing detection module and produce feature-matrix entries that slot into the existing deliverable structure.
