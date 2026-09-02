# Mindy's two review notes - every instance

Measured from the live page drafts and the Private Label theme modules, 2 September 2026.
Nothing published, nothing changed. 62 Praxera pages scanned.

## 1. "Under Capabilities, we need Custom Formulation removed"

**This is one edit, not 27.** The Capabilities column lives in a module default,
so every page renders the same copy:

- `Private Label/Modules/Global Footer.module/fields.json`
  - link label **Custom Formulation**, `linkUrl` is `#` - it already goes nowhere
  - the edit lands on all 127 pages using this footer: 62 Praxera + 65 `pl-demo-*-v3`
  - none of those 127 are published, so no live page moves

### Separately: 99 prose mentions across 26 pages - NOT what she asked about

These are sentences explaining the concept ("custom formulation means our R&D team
develops new formulations"), mostly inside FAQ answers. Removing them would gut the
copy. Worth confirming she means the footer link only.

| page | mentions |
|---|---|
| `custom-formulation` | 11 |
| `alp/ads-custom` | 7 |
| `faq` | 5 |
| `aging` | 4 |
| `cognitive` | 4 |
| `detox` | 4 |
| `energy` | 4 |
| `fitness` | 4 |
| `heart-health` | 4 |
| `herbal` | 4 |
| `immune-support` | 4 |
| `joint-support` | 4 |
| `mens-health` | 4 |
| `multivitamin` | 4 |
| `pediatric` | 4 |
| `prenatal` | 4 |
| `probiotics` | 4 |
| `sleep` | 4 |
| `weight-management` | 4 |
| `womens-health` | 4 |
| `alp/ads-contract-mfg` | 3 |
| `design-services` | 1 |
| `ingredient-sourcing` | 1 |
| `learning/definitive-guide` | 1 |
| `learning/onboarding-guide` | 1 |
| `testing` | 1 |

## 2. "Manufacturing / Manufacturers -> Providing / Providers, not in all areas"

### CHANGE  first-person claim - 10 instances

Praxera claiming to be the manufacturer. These must change.

**`(home)`**

- Whether you are launching your first supplement brand or expanding an existing product line, we handle the manufacturing complexity so you focus on your customers and your brand.  
  <sub>/Private Label - Page - Home - Private Label Supplements/main_content/column_1/module_1 / content</sub>
- We handle the manufacturing-side compliance.  
  <sub>/Private Label - Page - Home - Private Label Supplements/main_content/column_19/module_19 / answer</sub>

**`about`**

- Five decades later, we have grown into a 190-plus product catalog manufactured in our FDA-registered, GMP-certified Vermont facility.  
  <sub>/Private Label - Page - About Us/main_content/column_1/module_1 / content</sub>
- We launched our private label program to extend that same manufacturing standard to a broader audience: entrepreneurs and established brand-builders who want to launch their own supplement lines without compromising on quality.  
  <sub>/Private Label - Page - About Us/main_content/column_4/module_4 / content</sub>
- The scale of FoodScience LLC gives our Praxera private label clients access to manufacturing infrastructure, ingredient sourcing networks, and quality systems that would be impossible at a smaller scale.  
  <sub>/Private Label - Page - About Us/main_content/column_9/module_9 / content</sub>

**`certifications`**

- FDA-registered means we are on the FDA's list of facilities that manufacture dietary supplements, which requires meeting facility and process standards.  
  <sub>/Private Label - Page - Certifications/main_content/column_7/module_7 / answer</sub>
- We have certified manufacturing lines available for kosher and halal products.  
  <sub>/Private Label - Page - Certifications/main_content/column_7/module_7 / answer</sub>

**`chewables`**

- We can manufacture chewables free of common allergens (dairy, soy, wheat, nuts) through ingredient selection and segregated production.  
  <sub>/Private Label - Page - Chewables/main_content/column_10/module_10 / answer</sub>

**`quality-standards`**

- Here is how we make sure every private label product we manufacture earns that trust on day one.  
  <sub>/Private Label - Page - Quality Standards/main_content/column_1/module_1 / content</sub>

**`ty-consultation`**

- With over 50 years in the health supplement industry, we are one of the most trusted dietary supplement manufacturers.  
  <sub>/Private Label - Page - TY - Consultation Booked/main_content/column_3/module_3 / content</sub>

### REVIEW  neutral noun - 109 instances

'manufacturing' as a plain noun. Judgement call per sentence - many read fine.

**`(home)`**

- Get to market faster with 50 years of supplement manufacturing expertise.  
  <sub>/Private Label - Page - Home - Private Label Supplements/main_content/column_0/module_0 / headline</sub>
- Every product is manufactured in the United States.  
  <sub>/Private Label - Page - Home - Private Label Supplements/main_content/column_14/module_14 / content</sub>
- manufacturing, FDA-registered  
  <sub>/Private Label - Page - Home - Private Label Supplements/main_content/column_14/module_14 / title</sub>
- Our expert team is with you every step of the way: product selection, design, manufacturing, and ongoing brand support.  
  <sub>/Private Label - Page - Home - Private Label Supplements/main_content/column_14/module_14 / content</sub>
- A private label supplement is a pre-formulated dietary supplement produced by a manufacturer (us) and sold under your brand name.  
  <sub>/Private Label - Page - Home - Private Label Supplements/main_content/column_19/module_19 / answer</sub>
- You don't formulate it, you don't manufacture it, and you don't run quality testing.  
  <sub>/Private Label - Page - Home - Private Label Supplements/main_content/column_19/module_19 / answer</sub>
- , you don't need a license to sell dietary supplements, but you must comply with FDA labeling rules (DSHEA), follow good manufacturing practices on your distribution side, and register with FDA if you import or manufacture certain products.  
  <sub>/Private Label - Page - Home - Private Label Supplements/main_content/column_19/module_19 / answer</sub>
- vitamin-manufacturer-prexera  
  <sub>/Private Label - Page - Home - Private Label Supplements/main_content/column_4/module_4 / alt</sub>
- manufacturing, ready in weeks.  
  <sub>/Private Label - Page - Home - Private Label Supplements/main_content/column_9/module_9 / content</sub>

**`Global Footer`**

- png", "alt" : "Praxera Logo White", "loading" : "lazy", "width" : 612, "height" : 208, "max_width" : 612, "max_height" : 208 } }, { "id" : "bc01c9a2-f729-ab93-7730-87f28563dd33", "name" : "caption", "label" : "Caption", "required" : false, "locked" : true, "type" : "richtext", "d  
  <sub>Private Label/Modules/Global Footer.module/fields.json / default</sub>

**`about`**

- DaVinci Vermont manufacturing facility  
  <sub>/Private Label - Page - About Us/main_content/column_7/module_7 / alt</sub>
- owned manufacturer of nutritional supplements for humans and pets.  
  <sub>/Private Label - Page - About Us/main_content/column_9/module_9 / content</sub>
- FoodScience operates multiple manufacturing facilities and product brands serving the integrative medicine, retail, veterinary, and private label channels.  
  <sub>/Private Label - Page - About Us/main_content/column_9/module_9 / content</sub>

**`alp/ads-contract-mfg`**

- Praxera's private label program gives serious brand-builders access to the same doctor-formulated manufacturing that integrative healthcare professionals trust.  
  <sub>/Private Label - Ads LP - Supplement Contract Manufacturer/main_content/column_2/module_2 / content</sub>
- manufacturing, FDA-registered  
  <sub>/Private Label - Ads LP - Supplement Contract Manufacturer/main_content/column_3/module_3 / title</sub>
- We document it in a way that you own and could (in theory) take to another manufacturer.  
  <sub>/Private Label - Ads LP - Supplement Contract Manufacturer/main_content/column_7/module_7 / answer</sub>
- The timeline includes formulation development, ingredient sourcing, stability testing, manufacturing scale-up, and first batch production.  
  <sub>/Private Label - Ads LP - Supplement Contract Manufacturer/main_content/column_7/module_7 / answer</sub>

**`alp/ads-custom`**

- Praxera's private label program gives serious brand-builders access to the same doctor-formulated manufacturing that integrative healthcare professionals trust.  
  <sub>/Private Label - Ads LP - Custom Formulation Supplements/main_content/column_2/module_2 / content</sub>
- manufacturing, FDA-registered  
  <sub>/Private Label - Ads LP - Custom Formulation Supplements/main_content/column_3/module_3 / title</sub>
- You own the formula, the manufacturing process is yours, and you have a real moat against competitors.  
  <sub>/Private Label - Ads LP - Custom Formulation Supplements/main_content/column_7/module_7 / answer</sub>

**`alp/ads-mfg-usa`**

- Praxera's private label program gives serious brand-builders access to the same doctor-formulated manufacturing that integrative healthcare professionals trust.  
  <sub>/Private Label - Ads LP - Supplement Manufacturer USA/main_content/column_2/module_2 / content</sub>
- manufacturing, FDA-registered  
  <sub>/Private Label - Ads LP - Supplement Manufacturer USA/main_content/column_3/module_3 / title</sub>
- manufacturers operate under FDA oversight with consistent enforcement.  
  <sub>/Private Label - Ads LP - Supplement Manufacturer USA/main_content/column_7/module_7 / answer</sub>
- manufacturing matter for supplement brands?  
  <sub>/Private Label - Ads LP - Supplement Manufacturer USA/main_content/column_7/module_7 / question</sub>
- manufacturing cost-competitive or better.  
  <sub>/Private Label - Ads LP - Supplement Manufacturer USA/main_content/column_7/module_7 / answer</sub>
- manufacturing for reasons beyond just unit cost.  
  <sub>/Private Label - Ads LP - Supplement Manufacturer USA/main_content/column_7/module_7 / answer</sub>
- manufacturing more expensive than overseas?  
  <sub>/Private Label - Ads LP - Supplement Manufacturer USA/main_content/column_7/module_7 / question</sub>

**`alp/ads-pl-mfg`**

- Praxera's private label program gives serious brand-builders access to the same doctor-formulated manufacturing that integrative healthcare professionals trust.  
  <sub>/Private Label - Ads LP - Private Label Supplement Provider/main_content/column_2/module_2 / content</sub>
- manufacturing, FDA-registered  
  <sub>/Private Label - Ads LP - Private Label Supplement Provider/main_content/column_3/module_3 / title</sub>
- Manufacturing, quality testing, certificates of analysis, label design (template or custom), basic packaging selection, fulfillment-ready bottling.  
  <sub>/Private Label - Ads LP - Private Label Supplement Provider/main_content/column_7/module_7 / answer</sub>
- 50 years of supplement-specific manufacturing experience.  
  <sub>/Private Label - Ads LP - Private Label Supplement Provider/main_content/column_7/module_7 / answer</sub>
- Why work with Praxera over other private label manufacturers?  
  <sub>/Private Label - Ads LP - Private Label Supplement Provider/main_content/column_7/module_7 / question</sub>

**`book-consultation`**

- You'll be on a call with a private label specialist who can speak to manufacturing, quality, design, and business considerations.  
  <sub>/Private Label - Page - Book a Consultation/main_content/column_8/module_8 / answer</sub>

**`capsules`**

- Below is what to know about manufacturing capsules for private label: the formulations we offer, the specs available, how they are made, and which health categories benefit most.  
  <sub>/Private Label - Page - Capsules/main_content/column_1/module_1 / content</sub>
- Manufacturing specs available for private label capsules.  
  <sub>/Private Label - Page - Capsules/main_content/column_4/module_4 / headline</sub>
- Capsules manufacturing  
  <sub>/Private Label - Page - Capsules/main_content/column_6/module_6 / alt</sub>
- Both formats can be manufactured allergen-free for the top common allergens (soy, dairy, wheat, etc.  
  <sub>/Private Label - Page - Capsules/main_content/column_9/module_9 / answer</sub>
- Most capsule formulations have a 24-month shelf life from manufacture date when stored under standard conditions.  
  <sub>/Private Label - Page - Capsules/main_content/column_9/module_9 / answer</sub>

**`case-studies`**

- Many private label brands prefer not to publicly disclose their manufacturing partner.  
  <sub>/Private Label - Page - Case Studies/main_content/column_6/module_6 / answer</sub>
- Brands that want to outsource ALL strategy (private label handles manufacturing, not market positioning).  
  <sub>/Private Label - Page - Case Studies/main_content/column_6/module_6 / answer</sub>

**`certifications`**

- Manufacturing certifications you can stand behind.  
  <sub>/Private Label - Page - Certifications/main_content/column_0/module_0 / headline</sub>
- When a retailer evaluates your supplement brand, certifications signal that your manufacturer has been audited by independent third parties against published quality standards.  
  <sub>/Private Label - Page - Certifications/main_content/column_1/module_1 / content</sub>
- All Praxera&nbsp;private label products are manufactured in our FDA-registered, GMP-certified U.  
  <sub>/Private Label - Page - Certifications/main_content/column_1/module_1 / content</sub>
- Required for legal manufacture of dietary supplements in the United States.  
  <sub>/Private Label - Page - Certifications/main_content/column_2/module_2 / content</sub>
- Independent third-party audit of Good Manufacturing Practices specifically for the supplement category.  
  <sub>/Private Label - Page - Certifications/main_content/column_2/module_2 / content</sub>
- No supplement manufacturer can legally claim FDA approval.  
  <sub>/Private Label - Page - Certifications/main_content/column_7/module_7 / answer</sub>
- GMP (Good Manufacturing Practice) certification means an independent third-party auditor has confirmed we follow defined quality protocols for facility, equipment, personnel, raw materials, processes, packaging, and record-keeping.  
  <sub>/Private Label - Page - Certifications/main_content/column_7/module_7 / answer</sub>

**`chewables`**

- Manufacturing specs available for private label chewables.  
  <sub>/Private Label - Page - Chewables/main_content/column_5/module_5 / headline</sub>
- Chewable tablets are manufactured on lower-pressure rotary presses tuned for softer hardness profiles that customers can comfortably bite.  
  <sub>/Private Label - Page - Chewables/main_content/column_7/module_7 / content</sub>
- Chewables manufacturing  
  <sub>/Private Label - Page - Chewables/main_content/column_7/module_7 / alt</sub>

**`contact`**

- Drop-in visits are not supported because manufacturing facilities have access protocols, but scheduled visits are encouraged.  
  <sub>/Private Label - Page - Contact/main_content/column_7/module_7 / answer</sub>

**`custom-formulation`**

- The phases: formulation development, ingredient sourcing, stability testing, final formulation lock, manufacturing scale-up, and first production run.  
  <sub>/Private Label - Page - Custom Formulation/main_content/column_8/module_8 / answer</sub>
- We document the formula in a way that you could (in theory) take to another manufacturer, though we hope you won't.  
  <sub>/Private Label - Page - Custom Formulation/main_content/column_8/module_8 / answer</sub>

**`customer-art`**

- Product name, statement of identity, net quantity, supplement facts panel, ingredients statement, manufacturer name and address, structure-function claim disclaimer, lot code area, and barcode area.  
  <sub>/Private Label - Page - Customer-Supplied Art Guidelines/main_content/column_14/module_14 / answer</sub>

**`dropshipping`**

- Current Good Manufacturing Practices are non-negotiable.  
  <sub>/main_content/column_5/module_5 / content</sub>

**`facility`**

- Where your private label products are manufactured.  
  <sub>/Private Label - Page - Our Facility/main_content/column_0/module_0 / headline</sub>
- We have operated from Vermont since 1976 and have been steadily expanding the facility over the past five decades to add manufacturing lines, quality lab, and warehousing capacity.  
  <sub>/Private Label - Page - Our Facility/main_content/column_6/module_6 / answer</sub>
- Where is your manufacturing facility?  
  <sub>/Private Label - Page - Our Facility/main_content/column_6/module_6 / question</sub>
- What formats do you manufacture on-site?  
  <sub>/Private Label - Page - Our Facility/main_content/column_6/module_6 / question</sub>
- Tours typically include the manufacturing floor, quality lab, and warehouse.  
  <sub>/Private Label - Page - Our Facility/main_content/column_6/module_6 / answer</sub>

**`gummies`**

- Below is what to know about manufacturing gummies for private label: the formulations we offer, the specs available, how they are made, and which health categories benefit most.  
  <sub>/Private Label - Page - Gummies/main_content/column_1/module_1 / content</sub>
- Manufacturing specs available for private label gummies.  
  <sub>/Private Label - Page - Gummies/main_content/column_4/module_4 / headline</sub>
- Gummy manufacturing has higher minimums than other formats due to depositing line setup and drying time.  
  <sub>/Private Label - Page - Gummies/main_content/column_5/module_5 / description</sub>
- Gummies are manufactured on starch-molding and pectin-deposit lines.  
  <sub>/Private Label - Page - Gummies/main_content/column_6/module_6 / content</sub>

**`how-to-sell-supplements`**

- Ask any prospective partner for certificates of analysis, third-party testing, and documentation of good manufacturing practices, and confirm the facility is FDA-registered.  
  <sub>/main_content/column_10/module_10 / content</sub>

**`ingredient-sourcing`**

- Three layers: supplier qualification (audits, documentation, history), incoming raw material testing (identity, potency, contaminants on every lot), and process verification during manufacturing.  
  <sub>/Private Label - Page - Ingredient Sourcing/main_content/column_6/module_6 / answer</sub>

**`learning/definitive-guide`**

- However, like any other food product, supplements must be compliant with the FDA’s regulations regarding labeling and manufacturing.  
  <sub>/Private Label - Page - Definitive Guide/main_content/column_3/module_3 / content</sub>
- Current Good Manufacturing Practices (CGMPs) required under CFR-21-111 ensure testing is done on every raw material in a supplement.  
  <sub>/Private Label - Page - Definitive Guide/main_content/column_3/module_3 / content</sub>
- A FEW THINGS TO LOOK FOR DURING THE VETTING PROCESS: • Is the supplement provider FDA registered? • Does the provider have an up-to-date Current Good Manufacturing Practices (CGMP) certification? • Do they have on-site regulatory and quality control departments? • Are they free o  
  <sub>/Private Label - Page - Definitive Guide/main_content/column_3/module_3 / content</sub>
- For business and compliance purposes, products should also align with applicable labeling and manufacturing regulations.  
  <sub>/Private Label - Page - Definitive Guide/main_content/column_6/module_6 / content</sub>
- However, supplement products still need to comply with FDA regulations related to labeling, manufacturing, and current good manufacturing practices.  
  <sub>/Private Label - Page - Definitive Guide/main_content/column_6/module_6 / content</sub>
- How can I evaluate supplement quality before choosing a provider? A strong vetting process includes reviewing whether the provider is FDA registered, follows current good manufacturing practices, maintains regulatory and quality control systems, uses third-party testing, and prov  
  <sub>/Private Label - Page - Definitive Guide/main_content/column_6/module_6 / content</sub>

**`learning/ingredients-testing`**

- ' This guide explains what that actually means in manufacturing terms: how raw materials are sourced and vetted, what third-party tests confirm, which GMP certifications mean what, and which marketing claims should make you skeptical.  
  <sub>/Private Label - Page - Ingredients & Testing Guide/main_content/column_1/module_1 / content</sub>
- Whether you are picking a manufacturer or trying to understand what's actually in your own products, this guide gives you the technical literacy to ask better questions.  
  <sub>/Private Label - Page - Ingredients & Testing Guide/main_content/column_1/module_1 / content</sub>
- Brand builders who want to understand what 'quality' actually means in supplement manufacturing, so they can evaluate manufacturing partners (us or anyone else) intelligently.  
  <sub>/Private Label - Page - Ingredients & Testing Guide/main_content/column_6/module_6 / answer</sub>
- It's specifically designed to be useful for non-manufacturing audiences.  
  <sub>/Private Label - Page - Ingredients & Testing Guide/main_content/column_6/module_6 / answer</sub>
- Many of our clients share it with their retail accounts as a way to demonstrate manufacturing rigor.  
  <sub>/Private Label - Page - Ingredients & Testing Guide/main_content/column_6/module_6 / answer</sub>

**`learning/onboarding-guide`**

- Manufacturing runs in FDA-registered facility with full QA.  
  <sub>/Private Label - Page - Onboarding Guide/main_content/column_2/module_2 / content</sub>

**`liquids`**

- Below is what to know about manufacturing liquids for private label: the formulations we offer, the specs available, how they are made, and which health categories benefit most.  
  <sub>/Private Label - Page - Liquids/main_content/column_1/module_1 / content</sub>
- Manufacturing specs available for private label liquids.  
  <sub>/Private Label - Page - Liquids/main_content/column_4/module_4 / headline</sub>
- Liquid manufacturing has slightly higher MOQ than tablets due to bottling and filling minimums.  
  <sub>/Private Label - Page - Liquids/main_content/column_5/module_5 / description</sub>
- Liquid manufacturing happens in sanitized stainless-steel mixing tanks under controlled temperature and pH conditions.  
  <sub>/Private Label - Page - Liquids/main_content/column_6/module_6 / content</sub>
- Liquids manufacturing  
  <sub>/Private Label - Page - Liquids/main_content/column_6/module_6 / alt</sub>

**`multivitamin`**

- vitamin-manufacturer-prexera  
  <sub>/Private Label - Page - Multivitamin Supplements/main_content/column_6/module_6 / alt</sub>

**`our-process`**

- Manufacturing  
  <sub>/Private Label - Page - Our Process/main_content/column_2/module_2 / title</sub>
- In dietary supplement manufacturing  
  <sub>/Private Label - Page - Our Process/main_content/column_3/module_3 / description</sub>
- Brand and manufacturing ownership  
  <sub>/Private Label - Page - Our Process/main_content/column_4/module_4 / alt</sub>

**`powders`**

- Below is what to know about manufacturing powders for private label: the formulations we offer, the specs available, how they are made, and which health categories benefit most.  
  <sub>/Private Label - Page - Powders/main_content/column_1/module_1 / content</sub>
- Manufacturing specs available for private label powders.  
  <sub>/Private Label - Page - Powders/main_content/column_4/module_4 / headline</sub>
- Powders manufacturing  
  <sub>/Private Label - Page - Powders/main_content/column_6/module_6 / alt</sub>

**`quality-standards`**

- Ready to private label with a quality-first manufacturer?  
  <sub>/Private Label - Page - Quality Standards/main_content/column_10/module_10 / headline</sub>
- Current Good Manufacturing Practices govern every step from raw material receipt through finished product shipping.  
  <sub>/Private Label - Page - Quality Standards/main_content/column_5/module_5 / description</sub>
- Current Good Manufacturing Practices, in plain language.  
  <sub>/Private Label - Page - Quality Standards/main_content/column_6/module_6 / headline</sub>
- GMP is the FDA's framework for supplement manufacturing.  
  <sub>/Private Label - Page - Quality Standards/main_content/column_7/module_7 / content</sub>
- For private label brands, this means you can confidently tell your customers that every product you sell was manufactured under the same standards as the brands they already trust.  
  <sub>/Private Label - Page - Quality Standards/main_content/column_7/module_7 / content</sub>

**`request-quote`**

- We don't need to know your customer acquisition strategy or financial plan to price a manufacturing engagement.  
  <sub>/Private Label - Page - Request a Quote/main_content/column_7/module_7 / answer</sub>
- Manufacturing quotes include production, quality testing, certificates of analysis, label printing, and bottling.  
  <sub>/Private Label - Page - Request a Quote/main_content/column_7/module_7 / answer</sub>

**`resources`**

- The Essential Guide to Choosing a Manufacturer &rsaquo; How to Choose the Best Private Label Manufacturer &rsaquo; How to Choose a Private Label Supplement Provider &rsaquo;  
  <sub>/Private Label - Page - Resources Hub/main_content/column_5/module_5 / content</sub>

**`soft-gels`**

- Below is what to know about manufacturing soft gels for private label: the formulations we offer, the specs available, how they are made, and which health categories benefit most.  
  <sub>/Private Label - Page - Soft Gels/main_content/column_1/module_1 / content</sub>
- Manufacturing specs available for private label soft gels.  
  <sub>/Private Label - Page - Soft Gels/main_content/column_4/module_4 / headline</sub>
- Soft Gels manufacturing  
  <sub>/Private Label - Page - Soft Gels/main_content/column_6/module_6 / alt</sub>
- Soft gels can be manufactured in a wide range of colors using both natural and FD&amp;C-approved colorants.  
  <sub>/Private Label - Page - Soft Gels/main_content/column_9/module_9 / answer</sub>

**`tablets`**

- Below is what to know about manufacturing tablets for private label: the formulations we offer, the specs available, how they are made, and which health categories benefit most.  
  <sub>/Private Label - Page - Tablets/main_content/column_1/module_1 / content</sub>
- Tablets are the most cost-efficient supplement format to manufacture.  
  <sub>/Private Label - Page - Tablets/main_content/column_3/module_3 / content</sub>
- Manufacturing specs available for private label tablets.  
  <sub>/Private Label - Page - Tablets/main_content/column_4/module_4 / headline</sub>
- Tablets manufacturing  
  <sub>/Private Label - Page - Tablets/main_content/column_6/module_6 / alt</sub>
- Tablets can be manufactured with a score line so customers can split a dose in half.  
  <sub>/Private Label - Page - Tablets/main_content/column_9/module_9 / answer</sub>

**`terms`**

- This website is provided for informational purposes to support businesses evaluating Praxera as a private label supplement manufacturing partner.  
  <sub>/Private Label - Page - Terms of Service/main_content/column_3/module_3 / content</sub>

**`testing`**

- Stability testing is required to support shelf life claims (usually 2-3 years from manufacture date for supplements).  
  <sub>/Private Label - Page - Testing Protocols/main_content/column_6/module_6 / answer</sub>

### KEEP  Vermont provenance - 5 instances

'Manufactured in Vermont, U.S.A.' - approved provenance, leave alone.

**`alp/ads-contract-mfg`**

- Manufactured in Vermont, U.  
  <sub>/Private Label - Ads LP - Supplement Contract Manufacturer/main_content/column_3/module_3 / content</sub>

**`alp/ads-custom`**

- Manufactured in Vermont, U.  
  <sub>/Private Label - Ads LP - Custom Formulation Supplements/main_content/column_3/module_3 / content</sub>

**`alp/ads-mfg-usa`**

- Manufactured in Vermont, U.  
  <sub>/Private Label - Ads LP - Supplement Manufacturer USA/main_content/column_3/module_3 / content</sub>

**`alp/ads-pl-mfg`**

- Manufactured in Vermont, U.  
  <sub>/Private Label - Ads LP - Private Label Supplement Provider/main_content/column_3/module_3 / content</sub>

**`quality-standards`**

- Manufactured in Vermont  
  <sub>/Private Label - Page - Quality Standards/main_content/column_2/module_2 / description</sub>

### KEEP  industry term - 8 instances

'contract manufacturing' - the industry's own term; two ad pages are named for it.

**`alp/ads-contract-mfg`**

- Our contract manufacturing.  
  <sub>/Private Label - Ads LP - Supplement Contract Manufacturer/main_content/column_0/module_0 / headline</sub>
- Contract manufacturing typically refers to producing to your specifications (your formulation, your packaging, your everything).  
  <sub>/Private Label - Ads LP - Supplement Contract Manufacturer/main_content/column_7/module_7 / answer</sub>
- Most clients start with private label and add contract manufacturing as they grow.  
  <sub>/Private Label - Ads LP - Supplement Contract Manufacturer/main_content/column_7/module_7 / answer</sub>
- What's the difference between private label and contract manufacturing?  
  <sub>/Private Label - Ads LP - Supplement Contract Manufacturer/main_content/column_7/module_7 / question</sub>
- What's the minimum production run for contract manufacturing?  
  <sub>/Private Label - Ads LP - Supplement Contract Manufacturer/main_content/column_7/module_7 / question</sub>
- How long do contract manufacturing projects typically take?  
  <sub>/Private Label - Ads LP - Supplement Contract Manufacturer/main_content/column_7/module_7 / question</sub>

**`case-studies`**

- previous contract manufacturer.  
  <sub>/Private Label - Page - Case Studies/main_content/column_2/module_2 / content</sub>

**`learning/definitive-guide`**

- ” – Mindy Elmajian, Human Contract Manufacturing Business Leader at FoodScience LLC HOW TO LAUNCH YOUR PRIVATE LABEL BRAND Private labeling is a lucrative business.  
  <sub>/Private Label - Page - Definitive Guide/main_content/column_3/module_3 / content</sub>

