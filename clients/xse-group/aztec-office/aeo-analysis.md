# Aztec Office — AEO (Answer Engine Optimization) Analysis

| | |
|---|---|
| **Client** | XSE Group (shared ownership) |
| **Brand** | Aztec Office |
| **Domain** | https://www.aztecoffice.com/ |
| **Prepared for** | Friday XSE Client Success call |
| **Analyst** | Shawn Peterson |
| **Data source** | Semrush — US database |
| **Date** | 2026-07-21 |

---

## 1. Executive summary

Aztec Office is an **office-technology dealer** (printers, copiers, document scanners, toner/ink for Canon, Sharp, Brother, HP, plus displays, PTZ cameras and breakroom supplies). Its organic footprint today is very small — **316 organic keywords and ~69 organic visits/month** — which means the AEO upside is large and mostly untapped.

The good news: the site already has **one proven answer-style asset** (the `/doc-scanners` "best document scanners" page) that ranks page-1 for a cluster of "best…" queries. That page is the template to replicate.

Four takeaways:

1. **Concentration risk** — two pages (homepage + `/doc-scanners`) produce ~90% of all organic traffic. There is no answer-content depth behind them.
2. **The scanner "best-of" page works** — it ranks positions 4–12 for a dozen commercial-intent "best scanner" queries. This is exactly the content format AI answer engines and featured snippets pull from. Prove it once, scale it across categories.
3. **Entity confusion is the #1 AEO blocker** — "Aztec" collides with the Aztec civilization, Aztec adult-learning software (their own `learning.aztecoffice.com` subdomain), and Aztec schools. Answer engines cannot cleanly identify "Aztec Office" as an office-technology dealer, which suppresses citation.
4. **Toner & scanner how-to questions are the fastest AEO win** — high search volume, low difficulty, and directly tied to products they sell (consumables). These map straight to People-Also-Ask and AI Overviews.

---

## 2. What "AEO" means for this engagement

Answer Engine Optimization = earning **citations and direct answers** in:

- Google **AI Overviews** and **People-Also-Ask (PAA)**
- **Featured snippets** (position-zero)
- Conversational engines — **ChatGPT / Copilot, Perplexity, Gemini**

AEO is won with (a) **question-answering content** structured so a machine can lift a clean answer, (b) **clear entity/authority signals** so the engine trusts the source, and (c) **structured data** (FAQPage, Product, Organization schema).

**Methodology this pass:** Semrush US database — domain overview (`domain_rank`), organic keywords (`domain_organic`, 75 rows), organic competitors, top pages, and question-keyword universe (`phrase_questions` for "document scanner" and "printer toner") plus a head-term batch.

**SERP-feature pull (completed):** the per-keyword SERP-feature data has now been captured — see §3.5. Recommended remaining step: manual **AI-Overview spot-checks** on the priority keywords (Semrush's feature flags don't yet cleanly isolate AI Overviews for every query) before content is written.

---

## 3. Current state

### Domain snapshot (Semrush, US)

| Metric | Value |
|---|---|
| Organic keywords | 316 |
| Organic traffic | ~69 / month |
| Paid keywords | 0 |
| Semrush rank | ~4,379,198 (very low authority) |

### Traffic is dangerously concentrated

| Page | Keywords | Share of organic traffic |
|---|---|---|
| Homepage (`/`) | 47 | **59%** (mostly branded — "aztec office supplies") |
| `/doc-scanners` | 78 | **30%** |
| Everything else | ~190 pages | ~11% |

Homepage traffic is almost entirely **branded** — people already looking for Aztec. Only the scanner page earns meaningful **non-branded** demand.

### The one page that works — `/doc-scanners`

Ranks page-1 for a whole cluster of commercial "best" queries:

| Keyword | Position | Volume |
|---|---|---|
| best document scanner 2026 | 4 | 40 |
| best adf document scanner | 6 | 70 |
| best document scanners | 7 | 320 |
| best scanner for documents | 8 | 480 |
| best scanners for documents | 8 | 70 |
| best desktop scanners | 9 | 90 |
| best desktop scanner | 10 | 210 |
| best scanner with feeder | 10 | 70 |

This is the **model**: a category "best-of" guide that answers a buyer's comparison question. It is inherently AEO-friendly. Replicate it for every product line.

### Big commercial terms they barely rank for (AEO headroom)

| Keyword | Volume | Current position |
|---|---|---|
| printer toner | 2,900 | 32 |
| multifunction printer | 2,900 | — (weak) |
| desktop scanner | 1,900 | 21 |
| office copier | 1,300 | — (weak) |
| canon copier | 720 | — (weak) |
| office scanner | 590 | — (weak) |

### Entity / brand-confusion problem

The domain ranks for a jumble of unrelated "Aztec" meanings that dilute the brand's machine-readable identity:

- **Aztec civilization** — "what tools did the aztecs use" (pos 62)
- **Aztec adult-learning software** — "aztec tech", "azteclearning", "aztec training" all point to `learning.aztecoffice.com/aztec` (a different product living on a subdomain)
- Misc — "aztec schools", "aztec appliance", "offtech of maine", "copy tec"

For AEO this matters more than for classic SEO: answer engines resolve a query to an **entity** before choosing a source. Aztec Office's entity is muddy, so it rarely gets picked as "the office-equipment dealer."

### 3.5 SERP-feature capture — what's *available* vs. what they *own*

Semrush reports two things per keyword: which rich features appear on that SERP, and which of them the domain actually occupies. The gap between the two **is** the AEO opportunity.

**Finding: on non-branded queries, Aztec Office occupies essentially zero SERP features.** The only keyword where they hold a feature is the branded "aztec office supplies" (sitelinks). Every commercial and informational query below shows a feature-rich SERP that Aztec is absent from.

**People Also Ask (feature 21) is present on nearly every target SERP** — best document scanners, best scanner for documents, desktop scanner, printer toner, where to get printer ink, best desktop scanners, and more. PAA boxes are the single most winnable AEO surface here, and Aztec captures none of them.

| Target keyword | Features available on the SERP | Aztec owns |
|---|---|---|
| best document scanners | Sitelinks, Video, **PAA**, + reviews/related | none |
| best scanner for documents | Image pack, Video, **PAA**, + more | none |
| desktop scanner | Image pack, Video, Video carousel, **PAA** | none |
| printer toner | Video, Video carousel, **PAA**, + more | none |
| where to get printer ink | Local pack, Video, **PAA** | none |
| best desktop scanners | Sitelinks, Video, Image, Video carousel, **PAA** | none |

*Feature codes confidently identified: 3 = Local pack, 5 = Image pack, 6 = Sitelinks, 7 = Reviews, 9 = Video, 13 = Image, 14/15 = Ads, 20 = Video carousel, 21 = People Also Ask. Several newer high-numbered codes (34, 36, 45, 52) recur on these commercial SERPs and likely include Related searches / Popular products / AI Overview — to be confirmed in the manual AI-Overview spot-check.*

**Two AEO implications:**
- **PAA is the beachhead.** Structured FAQ answers on the scanner, toner and ink pages target boxes that already exist on these SERPs.
- **Video keeps appearing** (Video + Video carousel on most SERPs). Short product/how-to video is a second, under-used answer surface for this catalog.

---

## 4. The opportunity — question/answer universe (AEO content roadmap)

These are real queries with volume, phrased as questions, in categories Aztec Office already sells. They are the raw material for PAA / AI-Overview capture.

### Cluster A — Toner (STRONGEST: high volume, low difficulty, sells consumables)

| Question keyword | Volume |
|---|---|
| how to change toner in brother printer | 1,600 |
| how to replace toner in brother printer | 1,600 |
| what is printer toner | 720 |
| how to change toner on a brother printer | 480 |
| what is toner for printer | 480 |
| how to install toner in brother printer | 390 |
| how to reset brother printer toner | 210 |
| how to dispose of printer toner | 210 |
| how to recycle printer toner cartridges | 170 |
| what does toner do in a printer | 210 |

> "How to dispose of / recycle toner" pairs perfectly with a **toner take-back / recycling program** — an answer that doubles as a conversion path.

### Cluster B — Document scanners (extends the page that already wins)

| Question keyword | Volume |
|---|---|
| how to scan a document from scanner | 6,600 |
| what is a document scanner | 170 |
| what is automatic document feeder in scanner | 90 |
| how does a document scanner work | 30 |
| how to choose a document scanner | 20 |

### Cluster C — Copiers / MFPs (highest commercial value)

Head terms ("office copier" 1,300, "multifunction printer" 2,900, "canon copier" 720) have no supporting answer content. Build buyer-question pages: *"How much does an office copier cost?", "Lease vs. buy a copier?", "What is a multifunction printer?", "Canon vs. Sharp copiers?"*

---

## 5. Competitive landscape

| Competitor | Organic keywords | Organic traffic | Note |
|---|---|---|---|
| **scanstore.com** | 3,383 | 3,562 | Content leader — proves the scanner-guide model scales ~50× |
| visioneer.com | 676 | 1,096 | Scanner manufacturer content |
| aztectechnologies.com | 218 | 469 | Name-adjacent (adds to entity confusion) |
| columbia-business.com | 288 | 94 | Regional office-equipment dealer |
| accessofficeproducts.com | 130 | 41 | Direct-type competitor |

scanstore.com is the proof point: a focused office-scanner site can hold thousands of keywords. Aztec Office has the product range to do the same across scanners **and** toner **and** copiers.

---

## 6. Recommendations (prioritized)

### Tier 1 — Quick wins (0–30 days)
1. **Add FAQPage schema + an FAQ block** to `/doc-scanners` and the toner/ink category page, answering the Cluster A & B questions in 40–60 word snippet-ready blocks.
2. **Publish 3 toner how-to guides** ("how to change/replace/reset toner in a Brother printer") — highest volume-to-difficulty ratio on the whole site, and each ends in a "buy the toner" CTA.
3. **Fix entity signals** — add complete Organization schema (name, logo, sameAs to social/GMB), a clear "Aztec Office is an office-technology dealer" positioning line above the fold, and a consistent NAP.

### Tier 2 — Structural (30–90 days)
4. **Clone the "best-of" template** into 3 new category guides: *best office copiers*, *best multifunction printers*, *best office toner deals*.
5. **Disambiguate the learning subdomain** — clarify or separate `learning.aztecoffice.com` so it stops competing for the "Aztec" entity with the commercial site.
6. **Build copier buyer-question hub** (cost, lease-vs-buy, brand comparisons) to attack the 1,000–2,900-volume commercial head terms with supporting answers.

### Tier 3 — Authority & technical (ongoing)
7. **Earn citations** — get Aztec Office listed/reviewed on office-equipment directories and local B2B listings to build the authority AI engines weigh before citing.
8. **Product schema** on equipment-guide pages (hundreds exist, ranking 20–90) so they become eligible for rich results.
9. **Measure AEO directly** — track AI-Overview / featured-snippet presence and monitor whether ChatGPT/Perplexity cite the site for category queries.

---

## 7. Suggested first content sprint (8 assets)

1. How to change toner in a Brother printer (1,600) — guide + video + CTA
2. How to replace toner in a Brother printer (1,600)
3. How to reset toner on a Brother printer (210)
4. What is printer toner? / What does toner do? (720 + 210) — explainer
5. How to recycle/dispose of printer toner (380 combined) — + recycling program
6. Best office copiers 2026 — "best-of" clone
7. Best multifunction printers 2026 — "best-of" clone
8. How to choose a document scanner — extends the winning scanner page

Each built as: **direct answer up top (snippet-ready) → detail → FAQPage schema → product CTA.**

---

## 8. Next steps

- [x] Semrush SERP-feature pull complete (§3.5)
- [x] Engagement logged in HubSpot — ticket **47081286763**, owner Shawn Peterson, associated to XSE Group + Aztec Office, category Client – Marketing, due 2026-07-24
- [ ] Manual **AI-Overview spot-checks** on priority keywords (remaining phase-2 step)
- [ ] Confirm content owner and cadence with Shawn Peterson
- [ ] Review priorities on the **Friday XSE call**

---

## 9. Deep-dive addendum (v2)

This round added a site crawl, live answer-engine testing, authority data, and a competitor keyword-gap pull — moving the analysis from Semrush estimates to verified ground truth.

### 9.1 On-page / technical crawl (Firecrawl)

| Check | Homepage | /doc-scanners |
|---|---|---|
| Structured data (schema.org) | **None** | **None** |
| `<title>` | **Empty** | "Document Scanners – Aztec Office" |
| Meta description | **Empty** | Present (promises a guide) |
| H1 | "A to Z in Technology" (no keyword/entity value) | "Document Scanners" |
| FAQ / Q&A content | No | No |
| Content style | — | **Product grid, ~150 words** |

Two critical findings:
- **Zero structured data anywhere.** No Organization, LocalBusiness, Product or FAQ schema on the pages checked. This is the biggest technical AEO blocker — there is no machine-readable entity or answer markup for engines to lift.
- **The /doc-scanners page is a mirage.** Its `og:title` is "Best Document Scanners 2026 – Fast, Reliable, Affordable" and the meta promises a buyer's guide, but the body is a **~150-word product grid with no FAQ and no reviews.** It ranks page-one *despite* being thin — so turning it into a genuine reviewed guide (Flow 2) is the single highest-ROI page fix on the site.
- *Platform note:* the site runs on ECI **EvolutionX** (`evocdn.io`, `evo_*` meta). Schema/title fixes are template-level — one fix propagates site-wide, which is good for scale but may be constrained by the platform.

### 9.2 Answer-engine / citation testing — the AEO ground truth

Tested the real buyer questions and recorded which sources the engines surface:

| Query | Top answer sources | Aztec cited? |
|---|---|---|
| best document scanner with ADF | PCMag, NYT Wirecutter, TechGearLab, PopularMechanics, Reddit, YouTube | **No** |
| best multifunction printer (small business) | RTINGS, PCMag, CNET, TechRadar, + dealer blogs *uptownprinters*, *geeksonsite* | **No** |
| how to change toner in a Brother printer | Brother support, YouTube, *tonerbuzz.com* (toner retailer blog) | **No** |

**Aztec Office is cited in zero answer sets.** The decisive pattern: engines cite **editorial review guides and how-to content** — and, tellingly, *other dealers'* blogs (uptownprinters, tonerbuzz) get cited. Aztec's equivalent pages are product listings, so they're invisible to answer engines. This is the whole thesis, now evidenced: **product-listing pages don't get cited; answer content does.**

### 9.3 Authority / backlinks (Semrush)

| Metric | Aztec Office | scanstore.com (content leader) |
|---|---|---|
| Authority Score | 15 | 27 |
| Referring domains | 190 | 1,318 |
| Backlinks | 1,695 | 15,142 |

scanstore has ~7× the referring domains and nearly double the authority — which is *why* it's answer-citable and Aztec isn't. Authority is a long game (Flow 4 + digital PR); near-term, content quality + schema is the faster lever.

### 9.4 Entity collision (expanded)

Beyond the civilization / learning-software / schools confusion, there is a same-name competitor — **Aztec Office of Florida** (aztecofficefl.com, Jacksonville, its own showroom and phone). Aztec Office (founded in Connecticut) and Aztec Office of Florida collide in results. Flow 4 (distinct branding, explicit service area, `sameAs`, GBP) is required to separate the entities for answer engines.

### 9.5 Keyword-gap backlog (vs. scanstore.com)

High-value terms the content leader ranks for and Aztec is missing (volume ≥100, sorted by opportunity):

| Missing keyword | Volume | KD |
|---|---|---|
| document scanner | 9,900 | 52 |
| flatbed scanners | 2,900 | 46 |
| document scanning service | 1,600 | **23** |
| canon scanners | 1,300 | **30** |
| duplex scanner | 1,300 | **27** |
| document scanners | 1,600 | 50 |

The low-KD terms (23–30) are realistic near-term wins and feed straight into Flows 2, 3 and 6.

### 9.6 Reusable output

These findings were generalized into **`playbooks/aeo-flows.md`** — seven parameterized AEO flows (question harvest, best-of guide, consumables how-to, entity/schema hygiene, citation monitoring, keyword-gap backlog, local AEO) that transfer to QBS's other office-equipment-dealer clients by swapping inputs.

---

*Data pulled via Semrush (US database) and Firecrawl on 2026-07-21. Semrush traffic/position figures are estimates and will differ from Google Search Console actuals; answer-source results reflect live web results at time of testing.*
