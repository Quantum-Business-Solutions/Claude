# Praxera — "manufacturer" language rewrite (Tier 1 + Tier 2)

**Date:** 13 September 2026 · **Portal:** 4087538 · **Brand:** Praxera only (no DaVinci, VetriScience or Pet Tech asset was opened or changed).

## The rule applied

Sarah Miller (sign-off sheet): *"Replace all instances of 'manufacturing' / 'manufacturer' with Provider
language. Caveat: 'turnkey production' and 'US manufacturing' are OK."*
Melinda Elmadjian: *"Praxera is never marketed as manufacturing. 'Manufactured in the U.S.' and 'cGMP
facility' are approved; never 'we produce', 'our facilities', 'manufacturers'."*

## Scope

Shawn approved **Tier 1 (first-person) and Tier 2 (Praxera named) only**. Tier 0 (allowed phrases) and
**Tier 3 (465 generic industry sentences across 87 assets) were not touched** — that is the client's decision
and the blog's SEO surface.

| | In scope | Rewritten | Left for a human (see below) |
|---|---|---|---|
| Tier 1 — first person | 17 | 12 | 5 |
| Tier 2 — Praxera named | 23 | 22 | 1 |
| **Total** | **40** | **34** | **6** |

Assets touched: **25** (9 emails, 5 pages, 11 blog posts). Three further assets were in the tier list but
needed no change (see "Left for a human decision").

## Publishing state

- **Emails — all 9 remain DRAFT.** Nothing was published, scheduled or sent.
- **Pages — 4 live pages patched and pushed live** (`/about`, `/alp/ads-mfg-usa`, `/alp/ads-contract-mfg`,
  `/alp/ads-pl-mfg`). Each was checked first: no unrelated pending draft existed on any of them, so the
  push-live carried only this change.
- **`/pl-module-library` (218939556889) patched and left DRAFT** — it was not live, so it was not pushed.
- **Blog posts — 11 live posts patched and pushed live.**
- Before-state JSON for all 28 candidate assets: `backups/manufacturer-language/`.
  The exact edit list is `tools/manufacturer_language_plan.json`; the script is
  `tools/apply_manufacturer_language.py` (every match was verified unique before writing, and each write
  was re-read and verified afterwards).
- No URL or slug was changed. No product name, trademark mark, or factual claim was added or removed.

## Sentences changed

### Emails (9 sentences)

| ID | Label | BEFORE | AFTER |
|---|---|---|---|
| `220684191815` | Praxera - TEST - Pulse layout draft | backed by fifty years of manufacturing standards. | backed by fifty years of production standards. |
| `220685976500` | Praxera - Client_Onboarding_BoF_Danielle_#3 | placement</span> and manufacturing process is designed to ensure | placement</span> and production process is designed to ensure |
| `220685976504` | Praxera - Client_Onboarding_BoF_Danielle_#4 | Praxera has lower minimum order quantities than most private label supplement manufacturers. | Praxera has lower minimum order quantities than most private label supplement providers. |
| `220685976580` | Praxera - Client_Onboarding_BoF_Paul_From_MoF_#1 | we will teach you all about our private label supplement manufacturing services. | we will teach you all about our private label supplement program. |
| `220688283275` | Praxera - Private Label: High Priority - 6 Benefits | You're outsourcing manufacturing to a partner like Praxera | You're outsourcing production to a partner like Praxera |
| `220688283418` | Praxera - White_Label_World_Expo Email Did_Not_Click_Resource | without the need for extensive R&amp;D and manufacturing investments. | without the need for extensive R&amp;D and production investments. |
| `220688836176` | Praxera - Client_Onboarding_BoF_Danielle_#1 | offer turn-key manufacturing solutions. | offer turn-key production solutions. |
| `220688836180` | Praxera - Client_Onboarding_BoF_Danielle_From_MoF_#1 | we will teach you all about our private label supplement manufacturing services. | we will teach you all about our private label supplement program. |
| `220688836183` | Praxera - Client_Onboarding_BoF_Paul_#3 | placement</span> and manufacturing process is designed to be as effortless | placement</span> and production process is designed to be as effortless |

### Pages (9 sentences)

| ID | Label | BEFORE | AFTER |
|---|---|---|---|
| `216189433476` | about | a 190-plus product catalog manufactured in our FDA-registered, GMP-certified Vermont facility. | a 190-plus product catalog manufactured in the FDA-registered, GMP-certified Vermont facility operated by FoodScience LLC. |
| `216189433476` | about | to extend that same manufacturing standard to a broader audience | to extend that same production standard to a broader audience |
| `216189433476` | about | The scale of FoodScience LLC gives our Praxera private label clients access to manufacturing infrastructure | The scale of FoodScience LLC gives Praxera private label clients access to manufacturing infrastructure |
| `216192983652` | alp/ads-mfg-usa | access to the same doctor-formulated manufacturing that integrative healthcare professionals trust. | access to the same doctor-formulated products that integrative healthcare professionals trust. |
| `216192983654` | alp/ads-contract-mfg | access to the same doctor-formulated manufacturing that integrative healthcare professionals trust. | access to the same doctor-formulated products that integrative healthcare professionals trust. |
| `216194811734` | alp/ads-pl-mfg | access to the same doctor-formulated manufacturing that integrative healthcare professionals trust. | access to the same doctor-formulated products that integrative healthcare professionals trust. |
| `218939556889` | pl-module-library | We own the formulation, manufacturing, quality, compliance, and fulfillment. | We own the formulation, production, quality, compliance, and fulfillment. |
| `218939556889` | pl-module-library | <h2>Manufacturing</h2><p>Production runs in our FDA-registered, GMP-certified Vermont facility. | <h2>Production</h2><p>Production runs in the FDA-registered, GMP-certified Vermont facility operated by FoodScience LLC. |
| `218939556889` | pl-module-library | how to build your brand with our manufacturing team, download our free Definitive Guide. | how to build your brand with our private label team, download our free Definitive Guide. |

### Posts (16 sentences)

| ID | Label | BEFORE | AFTER |
|---|---|---|---|
| `220637272677` | blog/white-label-supplements-vs.-private-label-what-is-the-difference | refer to the same service, where a product is produced by a manufacturer that can be branded and sold by another company. | refer to the same service, where a ready-made product is supplied for another company to brand and sell. |
| `220637272688` | blog/must-have-private-label-probiotics-to-expand-your-product-line | By partnering with a trusted and experienced supplement manufacturer like PraxeraⓇ, which guarantees | By partnering with a trusted and experienced supplement provider like PraxeraⓇ, which guarantees |
| `220637272707` | blog/how-much-to-start-a-private-label-supplement-business | using a low-MOQ manufacturer like Praxera (36 units per SKU, no setup fees). | using a low-MOQ private label provider like Praxera (36 units per SKU, no setup fees). |
| `220637272707` | blog/how-much-to-start-a-private-label-supplement-business | use a low-MOQ manufacturer like Praxera (36-unit minimum, no setup fees), use template label designs from the manufacturer, | use a low-MOQ private label provider like Praxera (36-unit minimum, no setup fees), use template label designs from that provider, |
| `220637272707` | blog/how-much-to-start-a-private-label-supplement-business | The under-$500 launch path uses a low-MOQ manufacturer (Praxera advertises launches for under $500), pre-formulated stock products, a template label design provided by the manufacturer, | The under-$500 launch path uses a low-MOQ private label provider (Praxera advertises launches for under $500), pre-formulated stock products, a template label design provided by that provider, |
| `220637272707` | blog/how-much-to-start-a-private-label-supplement-business | Reputable manufacturers like Praxera have eliminated setup fees entirely. | Reputable private label providers like Praxera have eliminated setup fees entirely. |
| `220637279576` | blog/why-branded-ingredients-are-important-to-private-label-supplements | has been given a name by its manufacturer—for example, Praxera' | has been given a name by the company that developed it—for example, Praxera' |
| `220637279586` | blog/custom-supplements-vs.-private-label-supplements | delivery systems and are manufactured at Praxera to be GMP Certified. | delivery systems and are produced for Praxera to be GMP Certified. |
| `220637279599` | blog/how-private-label-supplements-can-increase-revenue-fast | With a manufacturing supplier like Praxera, you can get all the help you need | With a private label provider like Praxera, you can get all the help you need |
| `220637279628` | blog/top-private-label-protein-powders-for-your-brand | lending manufacturing, formulating, and branding powder to your product | lending production, formulating, and branding powder to your product |
| `220637279650` | blog/contract-manufacturing-vs-private-labeling-supplements | Some manufacturers (like Praxera) specialize in private labeling | Some providers (like Praxera) specialize in private labeling |
| `220637279650` | blog/contract-manufacturing-vs-private-labeling-supplements | Established private label manufacturers like Praxera offer 250+ doctor-formulated products | Established private label providers like Praxera offer 250+ doctor-formulated products |
| `220637279650` | blog/contract-manufacturing-vs-private-labeling-supplements | With a manufacturer like Praxera, you can launch your first private-label supplement line | With a provider like Praxera, you can launch your first private-label supplement line |
| `220638601792` | blog/supplement-dropshipping-5-best-tips-for-success | <p>Our industry-leading manufacturing facilities produce <a href="https://www.praxerasupplements.com/shop-supplements.html" style="color: #6bbfec;">over 250 doctor-formulated vitamins and supplements</a>. | <p>We supply <a href="https://www.praxerasupplements.com/shop-supplements.html" style="color: #6bbfec;">over 250 doctor-formulated vitamins and supplements</a>, produced in industry-leading U.S. facilities. |
| `220640208488` | blog/top-10-mistakes-to-avoid-with-supplement-manufacturing | Praxera upholds stringent sanitation protocols across every production facility, ensuring that private-label products are manufactured in the cleanest environments possible. | Praxera holds every production facility to stringent sanitation protocols, ensuring that private-label products are made in the cleanest environments possible. |
| `220640208499` | blog/healthcare-practitioner-supplement-line-guide | Low-MOQ private label programs from manufacturers like Praxera now offer | Low-MOQ private label programs from providers like Praxera now offer |
## Left for a human decision — 6 sentences, deliberately not rewritten

Each of these landed in Tier 1 or Tier 2 because the tiering script saw a pronoun or the word "Praxera"
near "manufactur*". In every case the manufacturing word itself is either **already client-approved
language** or **the neutral industry category word** that Tier 3 protects. Rewriting them would either
undo approved wording or leave the page contradicting itself.

| Asset | Sentence as it stands | Why it was left |
|---|---|---|
| page `216192983597` `/certifications` (Tier 2) | "All Praxera private label products are manufactured in FDA-registered, GMP-certified U.S. facilities." | This is exactly the phrasing Sarah and Melinda approved ("Manufactured in the U.S.", "cGMP facility"). It is passive and claims no Praxera-owned facility. It was tiered only because the allow-list matched the literal string "manufactured in the U.S." and not this variant. **Confirm with Mindy that it stays.** |
| post `220637272691` sleep post (Tier 1) | "Our innovative product line guarantees thoroughly researched ingredients … and promises Good Manufacturing Practices (GMP) certifications." | "Good Manufacturing Practices (GMP)" is the name of the certification standard, not a manufacturing claim. Changing it would break the proper noun. |
| post `220637272688` probiotics post (Tier 1) | "…certain strains have been shown to offer targeted benefits for different health challenges.* **Partner with a manufacturer that offers probiotic strains supported by clinical studies…**" | The pronoun ("We now know…") and the word "manufacturer" are in two different sentences that the splitter merged across the `*` footnote marker. The manufacturer here is a generic third party, identical to the Tier-3 uses in the same article ("choosing a manufacturer who offers aligned products", H3 "Partner With A Reliable Manufacturer"). |
| post `220637272693` gummy post (Tier 1) | "In this blog post, we'll explore the challenges with manufacturing gummies…" | Generic industry topic, matching ~15 Tier-3 uses in the same article and the H2s "Pick a Trustworthy Manufacturer" / "Select a Manufacturer Who is Experienced…". |
| post `220637272693` gummy post (Tier 1) | "We will explore: … **Choosing a manufacturer experienced with bioactive nutritional ingredients** …" | This is a table-of-contents bullet mirroring the Tier-3 H2 "Tip #4. Select a Manufacturer Who is Experienced with Bioactive Nutritional Ingredients". Changing the bullet without the heading would make the article contradict itself, and the heading is Tier 3. |
| post `220640208488` top-10-mistakes post (Tier 1) | "We are committed to helping businesses navigate the complexities of supplement manufacturing and avoiding costly pitfalls." | Praxera is the guide here, not the manufacturer. "Supplement manufacturing" echoes the post's own title and slug, which are Tier 3 and must not change. |

**Recommendation:** all six are safe to leave as they are. If Mindy wants any of them changed anyway, the
gummy post and the probiotics post should be changed together with their Tier-3 headings, which needs
Shawn to reopen the Tier-3 decision for those two posts.

## Where a rewrite touched a factual point

Three sentences asserted that Praxera owns the facility. They were rewritten to attribute the facility to
**FoodScience LLC**, which is supported by copy already live on `/about`: *"Praxera of Vermont is part of the
FoodScience family of companies… FoodScience LLC operates multiple manufacturing facilities and product
brands."* No new fact was introduced.

- `/about`: "manufactured in **our** … Vermont facility" → "manufactured in **the** … Vermont facility **operated by FoodScience LLC**".
- `/pl-module-library`: "Production runs in **our** … Vermont facility" → "…**operated by FoodScience LLC**", and the step heading "Manufacturing" → "Production".
- `blog/supplement-dropshipping-5-best-tips-for-success`: "**Our industry-leading manufacturing facilities produce** over 250 …" → "**We supply** over 250 … **produced in industry-leading U.S. facilities**".

One more was softened rather than reattributed, because naming a partner in a blog post is a client call:
`blog/top-10-mistakes-to-avoid-with-supplement-manufacturing` now reads "Praxera **holds every production
facility to** stringent sanitation protocols" instead of "Praxera upholds stringent sanitation protocols
**across every production facility**". If Mindy would rather name FoodScience here too, it is a one-line change.

`/pl-module-library` also carries "We own the formulation, manufacturing, quality…", which is now "We own the
formulation, **production**, quality…". That still says Praxera owns production. Rewriting it to hand
production to a partner would contradict the FAQ two modules above it on the same page ("We do not contract
production out to other manufacturers"), so it was left as a wording fix only. **This one needs Mindy.**

## Findings — out of scope, not acted on

The 525-sentence inventory only scanned rich-text and body fields. Inside the 28 assets opened for this job
there are further first-person / Praxera-named manufacturing claims in fields the inventory never saw:
**FAQ modules, `htmlTitle`, `metaDescription`, `headHtml` JSON-LD schema, headlines, stat labels and image
alt text.** None were changed. The same gap almost certainly applies to the other 68 Praxera assets.

| Asset | Field | Text |
|---|---|---|
| `/certifications` | htmlTitle | "Manufacturing Certifications \| Praxera Private Label" |
| `/certifications` | FAQ answer | "FDA-registered means **we are on the FDA's list of facilities that manufacture** dietary supplements…" |
| `/certifications` | FAQ answer | "…an independent third-party auditor has confirmed **we follow** defined quality protocols for facility, equipment…" |
| `/certifications` | FAQ answer | "**We have certified manufacturing lines** available for kosher and halal products." |
| `/alp/ads-mfg-usa` | htmlTitle | "Supplement Manufacturer USA \| Praxera Private Label" |
| `/alp/ads-contract-mfg` | htmlTitle / metaDescription | "Supplement Contract Manufacturer \| Praxera…" / "Our contract manufacturing." |
| `/alp/ads-contract-mfg` | headHtml schema + FAQ | "Contract manufacturing typically refers to producing to your specifications… **We do both.**" |
| `/alp/ads-pl-mfg` | htmlTitle / FAQ | "Private Label Supplement Manufacturer \| Praxera…" / "Why work with Praxera over other private label **manufacturers**?" / "**Manufacturing**, quality testing, certificates of analysis…" / "50 years of supplement-specific **manufacturing** experience." |
| `/pl-module-library` | FAQ answer | "**We do not contract production out to other manufacturers.**" |
| `/pl-module-library` | headline | "Inside **our** Williston, Vermont **manufacturing facility**" |
| `/pl-module-library` | image alt | "**DaVinci** Vermont manufacturing facility" — also breaks the "DaVinci is never mentioned on the Praxera site" rule |
| blog `220637272688` | FAQ question | "How can Praxera support brands in private-label probiotic **manufacturing**?" |
| blog `220637272691` | FAQ answer | "Praxera offers … **GMP-certified manufacturing**, brand and art design assistance…" |
| blog `220637272707` | FAQ answer | "…using a low-MOQ **manufacturer like Praxera**, with a template label design provided by the **manufacturer**…" (the article body version of this sentence *was* fixed) |
| blog `220637279628` | FAQ answer | "Praxera offers expert formulation, high-quality ingredients, **manufacturing capabilities**…" |
| blog `220637279650` | FAQ answer | "Private label specialists like Praxera focus on…" (context: "contract **manufacturers**") |
| blog `220638601792` | FAQ answer | "Praxera offers … a trusted **manufacturing partner** to help launch and grow your dropshipping business." |

Two further observations, neither acted on:

1. **`/about` has manufacturing claims outside the inventory** — the stat label "FDA registered
   manufacturing facility", the meta description "50 years of supplement manufacturing expertise", and the
   sentence "The same facility, the same formulations, the same testing protocols, just under your brand."
   The last one implies a Praxera-owned facility without using the word "manufactur*", so no tier caught it.
2. **`blog/custom-supplements-vs.-private-label-supplements` (220637279586) sells custom formulation as a
   Praxera service**, which conflicts with the standing rule that Praxera does not offer Custom Formulation.
   That is a content decision for Tammy/Mindy, not a wording fix.

This mirrors `faq-manufacturing-wording-for-approval.md`, where the same FAQ-module gap was found on 17 live
category pages and is still awaiting Mindy's approval.
