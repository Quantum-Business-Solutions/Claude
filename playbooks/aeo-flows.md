# QBS AEO Flows — Reusable Playbook

**What this is:** a set of repeatable Answer Engine Optimization (AEO) "flows" — parameterized playbooks QBS can run for any client. They were built during the **Aztec Office** engagement (office-technology dealer), and because most QBS clients are office-equipment dealers (Eakes, Kelly Office, Fisher's, Pulse, Image 2000, Brandon Business Machines, Hilyard's, Revolution Office, Swenson, Tascosa, Power Business Technology…), each flow transfers with only the parameters swapped.

**How to use:** every flow lists **Inputs** (the parameters you swap per client), **Steps**, **Output**, and where relevant a **Schema snippet** and an **Automation note** (how it would run in n8n). Aztec examples are shown inline in `> quote blocks`.

> **Automation status:** the n8n connector is not yet authorized in this workspace, so these run **semi-manually today** (Claude + Semrush + Firecrawl + HubSpot). Each flow is written to be automation-ready — once n8n is connected, the "Automation note" describes the trigger/nodes. Nothing here depends on n8n to deliver value now.

**The one principle behind every flow:** AI answer engines and SERP features cite *editorial, question-answering, schema-marked* content — never bare product-listing pages. Every flow below turns dealer inventory into answer-grade content and machine-readable signals.

---

## Flow 1 — Question Harvest → Answer Block (PAA capture)

**Purpose:** capture People-Also-Ask / AI-Overview answers by publishing snippet-ready Q&A + FAQ schema.
**When to run:** for every priority category page.
**Inputs:** `{client, domain, category_seeds[]}` (e.g. seeds = "document scanner", "printer toner").
**Tools:** Semrush `phrase_questions` → Claude drafting → CMS + FAQPage schema.

**Steps**
1. Pull question keywords for each seed (`phrase_questions`, sort by volume). Keep those tied to what the client sells.
2. Cluster by page (scanner Qs → scanner page, toner Qs → toner page).
3. Draft each answer as a **40–60 word, direct, liftable** paragraph — answer first, detail second.
4. Publish as an on-page FAQ block **and** emit FAQPage schema.
5. Log target questions; re-check capture in Flow 5.

**Output:** FAQ block + FAQPage schema on each category page; a tracked question list.

**Schema snippet**
```json
{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
 {"@type":"Question","name":"What is a document scanner?","acceptedAnswer":{"@type":"Answer","text":"A document scanner converts paper into digital files…"}}
]}
```
> **Aztec:** scanner + toner/ink pages currently have `has_faq: false` and zero schema. Seed with toner Qs ("how to change toner in a Brother printer" – 1,600) and scanner Qs ("what is a document scanner", "how to choose a document scanner").

**Reusability:** universal. Swap `category_seeds` per client's catalog.
**Automation note (n8n):** cron → Semrush node (phrase_questions) → LLM node (draft answers) → CMS API node (publish) → store question list for monitoring.

---

## Flow 2 — Thin Category Page → "Best-of" Buyer Guide

**Purpose:** convert a product-listing page into a reviewed, AI-citable buyer's guide.
**When to run:** any category page that ranks but is thin (title promises a guide, body is a grid).
**Inputs:** `{client, category_url, product_set, buyer_criteria[]}`.
**Tools:** Firecrawl (audit current page) → Claude (guide) → CMS + ItemList/Product + FAQ schema.

**Steps**
1. Audit the page: content style, word count, schema, FAQ (Firecrawl JSON scrape).
2. Rewrite as a real guide: intro answering the head question → ranked picks with *why* (use-case, ADF capacity, speed, cost) → comparison table → FAQ.
3. Add `ItemList`/`Product` schema for the picks + FAQPage for the questions.
4. Keep the buying CTA (dealer advantage: they actually sell these).

**Output:** editorial guide page with comparison table + schema; a repeatable guide template.

> **Aztec:** `/doc-scanners` is titled "Best Document Scanners 2026" but is a **~150-word product grid, no FAQ, no schema** — yet still ranks pos 4–12. Making it a genuine guide is the single highest-ROI page fix on the site, and the template then clones to copiers, MFPs, and toner.

**Reusability:** the guide template is the workhorse — one structure, N categories, M clients.
**Automation note (n8n):** manual authoring stays human; automate the *audit + brief* (Firecrawl scrape → LLM brief → task in HubSpot).

---

## Flow 3 — Consumables How-To Engine

**Purpose:** win the huge how-to demand around toner/ink/parts, each ending in a purchase path.
**When to run:** any client selling consumables.
**Inputs:** `{client, consumable_lines[] (Brother, HP, Canon…)}`.
**Tools:** Semrush `phrase_questions` ("how to … toner/ink") → Claude → CMS + HowTo schema + product CTA.

**Steps**
1. Harvest how-to questions per brand line (change / replace / reset / recycle / dispose).
2. Write step-by-step guides (short intro answer → numbered steps → "buy the cartridge" CTA).
3. Add `HowTo` schema; link to the exact SKU.
4. Bundle recycle/dispose questions with a **take-back program** offer (answer that converts).

**Schema snippet**
```json
{"@context":"https://schema.org","@type":"HowTo","name":"How to change toner in a Brother printer",
 "step":[{"@type":"HowToStep","text":"Open the front cover…"}]}
```
> **Aztec:** "how to change/replace toner in Brother printer" = 1,600 each; answer sources today are Brother + YouTube + **tonerbuzz.com** (a toner retailer). Aztec sells the toner and can own this.

**Reusability:** universal for dealers; brand lines are the only swap.
**Automation note (n8n):** cron → Semrush → LLM draft → human review queue → CMS publish.

---

## Flow 4 — Entity & Schema Hygiene

**Purpose:** make the brand machine-readable and unambiguous — the foundation every other flow relies on.
**When to run:** once per client site (then audit quarterly).
**Inputs:** `{client, legal_name, NAP, socials[], service_area}`.
**Tools:** Firecrawl (schema/meta audit) → CMS templates → Google Business Profile.

**Steps**
1. Audit: title/meta present? Organization/LocalBusiness schema? NAP consistent? (Firecrawl.)
2. Add site-wide **Organization + LocalBusiness** schema with `sameAs` to socials/GBP.
3. Fix empty `<title>`/meta and vague H1s at the **template** level (most dealer sites are on shared platforms — one template fix propagates).
4. Claim/complete GBP; align NAP everywhere.
5. Disambiguate same-name entities (distinct branding, explicit service area, `sameAs`).

**Schema snippet**
```json
{"@context":"https://schema.org","@type":"LocalBusiness","name":"<Legal Name>",
 "telephone":"<phone>","address":{"@type":"PostalAddress","streetAddress":"…"},
 "sameAs":["<GBP>","<LinkedIn>","<X>"]}
```
> **Aztec:** homepage `<title>` and meta are **empty**, H1 is "A to Z in Technology," **zero schema** sitewide, and there's entity collision with a separate **Aztec Office of Florida**. This flow is the prerequisite for everything else. (Site runs on ECI EvolutionX → fixes are template-level and propagate.)

**Reusability:** universal; the schema is boilerplate with per-client fields.
**Automation note (n8n):** scheduled Firecrawl audit → diff vs. expected schema → alert + HubSpot ticket when a client site drifts.

---

## Flow 5 — AI-Citation & SERP-Feature Monitoring

**Purpose:** measure the thing that matters — are we cited in answers? — and track progress.
**When to run:** monthly per client (baseline first).
**Inputs:** `{client, domain, tracked_questions[], competitors[]}`.
**Tools:** Firecrawl `search` (answer sources) + Semrush position/SERP-feature tracking.

**Steps**
1. For each tracked buyer question, capture the top answer sources (Firecrawl search).
2. Record: is the client present? who is cited? which feature (PAA/AI Overview/video)?
3. Track Semrush positions + SERP-feature capture for the target set.
4. Report deltas month-over-month; feed misses back into Flows 1–3.

**Output:** an AEO scorecard (citations won, PAA captured, share vs. competitors).

> **Aztec baseline (today):** cited in **0** answer sets across scanner, printer, and toner queries; owns **0** SERP features on non-branded terms. That is the number we move.

**Reusability:** universal; this is the measurement loop for the whole program.
**Automation note (n8n):** cron → Firecrawl search per question → parse citations → append to a Google Sheet/HubSpot → notify on change.

---

## Flow 6 — Keyword-Gap → Content Backlog

**Purpose:** turn a leading competitor's footprint into a prioritized, low-difficulty content backlog.
**When to run:** at engagement start, then quarterly.
**Inputs:** `{client_domain, top_content_competitor}`.
**Tools:** Semrush `domain_domains` (missing keywords) + `phrase_questions`.

**Steps**
1. Pull "missing" keywords (competitor ranks, client doesn't), volume ≥100.
2. Filter to low KD + commercial relevance; cluster into pages.
3. Route each cluster to Flow 2 (guides) or Flow 3 (how-tos).
4. Size the backlog; sequence by volume × margin.

> **Aztec (vs. scanstore.com):** missing high-value, low-KD terms include "document scanner" (9,900), "canon scanners" (1,300, KD 30), "duplex scanner" (1,300, KD 27), "document scanning service" (1,600, KD 23), "flatbed scanners" (2,900). Instant backlog.

**Reusability:** universal; pick the client's strongest content competitor.
**Automation note (n8n):** cron → Semrush domain_domains → filter node → create HubSpot tasks per cluster.

---

## Flow 7 — Local AEO ("near me" + Local pack)

**Purpose:** capture local-intent answers and the Local pack for regional dealers.
**When to run:** any client with a physical service area.
**Inputs:** `{client, locations[], service_area}`.
**Tools:** GBP + LocalBusiness schema + localized landing pages.

**Steps**
1. Complete/optimize GBP (categories, services, Q&A, posts).
2. Build localized service pages ("office copier service in <city>").
3. Add LocalBusiness schema with geo + area served; seed GBP Q&A from Flow 1.
4. Target "near me" / "in <city>" queries.

> **Aztec:** "where can I scan documents near me" (1,600) triggers a **Local pack**; "where to get printer ink" also shows local intent. Regional presence is unclaimed answer territory.

**Reusability:** universal for any multi-location or regional client.
**Automation note (n8n):** GBP post scheduling + review-response drafting.

---

## Suggested rollout order (any client)

1. **Flow 4** (entity/schema hygiene) — foundation.
2. **Flow 6** (keyword gap) — defines the backlog.
3. **Flow 1 + Flow 3** (FAQ capture + how-tos) — fastest wins.
4. **Flow 2** (best-of guides) — highest ROI per page.
5. **Flow 7** (local) — where applicable.
6. **Flow 5** (monitoring) — runs continuously from day one to prove ROI.

*Built from the Aztec Office AEO engagement (XSE Group). Reuse across QBS office-equipment-dealer clients by swapping the Inputs in each flow.*
