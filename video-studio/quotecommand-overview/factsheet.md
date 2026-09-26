# QuoteCommand: verified fact sheet for the product film

Verified 2026-09-24 against `origin/main` @ `de91310` ("Internal reference is reachable from the user menu and ⌘K (#88)") and the live Supabase project `msgxechfpyxnvlcrmoqh` (read-only SELECTs). The demo dealer is Quantum Business Solutions (`8c3dfd49-…4bc0`), shortened below to **Q**.

Paths are relative to the repo root. "SQL" means a live read-only query; each query is summarised where it is used. Where the docs and the code or database disagree, the code or database wins and the entry says so.

**Five things to know before scripting**

1. **Reps can see every deal in their dealership today.** The live `deal_drafts` policy is `Dealer members manage deal drafts … has_dealer_access(auth.uid(), dealer_id)` (SQL on `pg_policies`), and `proposals` works the same way. The territory policies are applied live, but they are RESTRICTIVE and inert: 0 territories and 0 `territory_settings` rows (SQL), and nothing on `main` uses them. The old line "A rep sees their own deals" is therefore false. What a rep does *not* see is **cost**.
2. **The production MCP server does not match `main`.** The deployed `mcp` edge function (v18, deployed 2026-09-24 18:06 UTC, `verify_jwt: true`) contains **19 tools**: the 16 read tools plus `create_proposal_from_deal`, `update_proposal_section` and `set_proposal_published`. Those three come from **unmerged PR #81**, found by grepping the deployed bundle from `get_edge_function`. The same bundle has **no** OAuth resource-metadata code, so the sign-in flow from #85 is not live. `main` has 16 read-only tools (`src/lib/mcp/tools/index.ts`).
3. **Reps can see GP on the Commissions ▸ Statement tab.** The GP column and the "GP comm." column render for every role (`src/components/commissions/StatementTab.tsx:703,711`). This is logged in `docs/open-items.md` §"2026-09-24 — found while building price-book health". Do **not** film the Statement tab as a rep, and do not say "reps never see GP anywhere". What is true: the configurator, My earnings and the approvals card hide GP from reps.
4. **No email is sent.** `RESEND_API_KEY` and `SIGN_MAIL_FROM` are unset, so notices are in-app only: the bell and the banners (`docs/open-items.md` §"customer picks the option"; features.md line 515 says "Notices are in the app, not email").
5. **`docs/features.md` is stale in places.** It says 7,163 rules, 1,332 products, 6 customer + 7 internal documents, "(Quantum first)" on quick start, and "none are pre-filled" for stage tasks. Each is corrected below.

---

## 1. Home and branding

**What it does**
- `/` opens on the dealership's own logo, primary and accent colours, tagline and contact details, which are the same identity their proposals print (`docs/features.md` §Opening the app, lines 72-75).
- The workflow is drawn as four numbered steps (Deals → Configurator → Proposals → Documents). None of them is gated (features.md lines 77-80).
- The counts are the dealership's own: open deals, configured deals, proposals sent or in progress, quoted contract value, and the five most recently touched deals (lines 82-84).
- A step with nothing to report shows the next action instead of a zero ("Start your first deal") (lines 86-88).
- Deals below the margin floor are named above the workflow. **A rep does not see the dealer margin on that banner** (features.md line 1176; CHANGELOG "The rep should only see rep margin").
- The nav order is Account Reviews, Fleet, Deals, Configurator, Proposals, Documents, Orders, Leasing, Commissions, Analytics, Settings (`src/components/GlobalNav.tsx:38-56`). Links the dealership has not bought are dropped rather than greyed out (GlobalNav.tsx:84-89).
- Branding on file (SQL on `dealers`): **Q** has a logo, navy `#0B1F3A`, gold `#C9A24B` and the tagline "Office technology, managed properly." Pollock has its own logo and blues. Tascosa and Eakes have no logo or colours yet.

**Routes:** `/`. Branding is edited at `/admin` (the dealership profile) and in the Setup wizard's Branding step.

**Roles:** everyone. Reps get no dealer margin on this page.

**Changed since the old film:** nothing material. "It opens wearing your brand" is still true.

---

## 2. Account reviews

**What it does**
- This is a list of customers **whose fleet came from e-automate** (filtered on `ea_customer_number`), sorted by print volume (`src/pages/Accounts.tsx:1-11`). It carries a **Beta** badge (Accounts.tsx, `<BetaBadge/>`).
- Each account shows the fleet three ways (by device, by contract and by lease) on one page (`src/pages/AccountOverview.tsx:1-17`).
- The device table sorts by "attention" by default: over duty cycle first, then no contract, then expiring, then age and service calls. The badges that drive the sort are shown on each row (AccountOverview.tsx:30-45).
- **Print / PDF** stacks all three sections for a leave-behind (AccountOverview.tsx:448-454).
- **Start a deal** from the fleet, or from selected devices: it creates the deal with the customer on it, downloads the fleet as the configurator's import CSV, and opens `/configurator?deal=` (AccountOverview.tsx:359-407).
- The data comes from the `account-overview` edge function: HubSpot equipment, e-automate / CEO Juice meters, PrintReleaf, and demo records (CHANGELOG "In the field").

**Routes:** `/accounts`, `/accounts/:id`

**Roles:** every member. There are no cost figures on these pages.

**Not live / caveats:** this is Beta. It only shows accounts that have e-automate data. A dealer without CEO Juice or e-automate sees little here.

**Changed since the old film:** new. The old film did not show it.

---

## 3. Fleet and fleet assessments

**What it does**
- **`/fleet`** is every machine this dealership has placed: customer, site, model, serial, status, lease end and lease payment. It filters by lease end within N months, service plan and status. A drawer holds the meter history chart, "add a reading" and Mark removed (`docs/fleet.md` §1).
- Assets create themselves when an order line or order reaches **Installed**, once per line (fleet.md §1 "How an asset comes into existence").
- **Import meter reads (CSV)** matches by serial. An unknown serial is refused by line number, never silently dropped (fleet.md §1).
- Reps may add a meter read and nothing else. A reading can never be edited, because a correction is a new read (fleet.md "Grants and policies").
- **`/assessments`** imports a prospect's incumbent fleet (CSV/XLSX). Per device it computes CPP and utilisation against the rated duty. Across the fleet it computes consolidation candidates and annual TCO. It then proposes a **replacement fleet priced from the dealer's own catalogue** (fleet.md §2).
- From an assessment, **Open in Configurator** creates a deal, and **Create proposal** adds an "Assessment" section with current-vs-proposed tables and a savings chart. The section is frozen from the same computation (fleet.md §2).
- The seeded demo is "Summit Regional Credit Union": 14 devices, 8 brands, 5 branches, 2 consolidation candidates and **$6,090/yr projected savings** (fleet.md §2 Seed data).

**Numbers (SQL):** Q has **400 fleet assets** and **8 fleet assessments**. The doc's "30 assets" is out of date.

**Routes:** `/fleet`, `/assessments`, `/assessments/:id`. Both are now routed and in the nav (`src/App.tsx:220-222`, GlobalNav.tsx:40). fleet.md's "Gaps: no nav entry or route" is **stale**.

**Roles:** every member reads. Owners, admins and managers write assets. Any member creates an assessment.

**Changed since the old film:** new.

---

## 4. Configurator

### 4a. Catalogue: HubSpot → Postgres
- The catalogue and rules are **synced into QuoteCommand's own tables** (`catalog_products`, `catalog_associations`) and read from there in under a second. HubSpot stays the system of record (features.md lines 869-882; `src/App.tsx:97-107`).
- **The sync is on demand, not scheduled.** It runs when someone presses "Sync catalogue now" on Settings → HubSpot Setup, or automatically when the cache is empty. No sweep runs on a timer (`docs/open-items.md` §"Nothing runs the sync on a schedule").
- **Q's last sync was 2026-09-10 19:04 UTC:** it wrote 1,370 products and 10,844 associations (SQL on `catalog_sync_runs`).
- **A dealer does not need HubSpot at all.** Settings → Price Book → Import takes a manufacturer's XLSX/CSV/PDF and applies it to the dealership's own catalogue. This is Pollock's path (features.md lines 150-162; CHANGELOG 2026-09-15).
- **Numbers (SQL):** Q has **1,418 products** (1,370 from HubSpot and 48 local; 1,413 active). Pollock 114, Power Business Technology 352, Tascosa 74. features.md's "1,332 products" is **stale**.

### 4b. Compatibility rules and their wording
- Rule types are required accessories, choose-one groups, mutually exclusive options, default-included items and optional accessories (features.md lines 106-108; `catalog_associations.rule_type`).
- **Q rule counts (SQL on `catalog_associations` for Q, grouped by `rule_type`):**

  | Rule type | Count |
  |---|---|
  | optional | 8,013 |
  | requires | 1,737 |
  | one_of | 844 |
  | excludes | 217 |
  | default_included | 33 |
  | **Total** | **10,844** |

  That is 2,831 rows that constrain a build; the 8,013 optional rows are "may attach". Pollock has 533, Tascosa 617, PBT 0.
- **"Needs one of" rules (new, #71):** a finisher adds its relay or bridge unit with a note, e.g. "RU-519 Relay Unit added — required by FS-539 Staple Finisher". The last part a selected accessory depends on cannot be removed alone ("Remove both") (features.md lines 110-116). **Q has 111** (SQL on `accessory_prerequisites`): Sharp 72, KM 14, Kyocera 9, Ricoh 6, Toshiba 4, HP 3, Canon 2, Xerox 1 (CHANGELOG #71).
- Owners and admins edit rules in CPQ Settings ▸ Rules.

### 4c. Quick start from customer needs
- The rep answers plain questions: B&W and colour pages, colour needed, paper size, head-count or speed, finishing, scanning, fax, and budget. Two or three **already-valid builds** come back from the live catalogue, each with a one-line reason. **Build all as options** saves them as good / better / best (features.md lines 118-136; `src/lib/quickStart.ts`).
- It uses only real products and rules. It waits for the rules to load ("Loading your rules…"). It shows **no cost or margin**.
- **On for every dealer.** It mounts under `flexPricing` (`src/pages/Configurator.tsx:9043-9045`), and flex pricing is on for all dealers because `FLEX_PRICING_OPT_OUT` is empty (`src/lib/featureFlags.ts:31-34`). features.md's "(Quantum first)" label is **stale**.
- Verified live example (CHANGELOG, earlier 2026-09-24): 8,000 mono + 2,000 colour, 11x17, 20 people, stapling, under $450/mo. The screen answers "Nothing fits $450/mo — closest options:" with the Kyocera TASKalfa 3554ci at about $496/mo. With a $500 budget it becomes BEST FIT.
- **"Ready to send?"** is a checklist before sending: fully configured, service or "hardware only", customer linked, approval sorted, trade-up payoff, a lease rate, ship-to per machine, and nothing under rep cost (features.md lines 138-148).

### 4d. Saved builds and bundles; good / better / best
- **Saved builds** ("My builds") follow the rep to any device. An owner or admin can publish a **dealer bundle**, optionally at a **fixed bundle price**. Every saved build is **re-checked against today's price book and rules** when it is added, and any change is named (features.md lines 220-235; `src/lib/savedBuilds.ts`). No cost is ever saved.
- **Good / better / best** takes the built machine plus one step down and one step up. Each alternative is fully built (same colour, same paper size, a scanner if needed) with equipment and monthly deltas. **Save all three as quote options**; a quote holds three (features.md lines 237-250; `src/lib/goodBetterBest.ts`).
- Caveat: the "+$x/mo" deltas in the dialog are per machine, so they are approximate on a multi-machine quote. The saved options are exact (`docs/open-items.md` §saved builds).
- Live (SQL): 0 saved builds exist yet. The test rows were deleted.

### 4e. Volume and duty-cycle checks
- A warning appears when the entered pages/month exceed the **recommended ceiling for the machine's class**: "…pages/mo is over this device's recommended N. Expect service pain…" (`src/pages/Configurator.tsx:266-267, 8028-8040`).
- The ceilings are A3 colour 20,000, A4 colour 8,000, A4 mono 7,500 and A3 mono 80,000.
- **Nuance:** this is a class ceiling, not the manufacturer's rated duty cycle for the model. Say "recommended volume for that class of machine".

### 4f. Flex pricing: the "new configurator"
- It is on for **every dealership**. It brings the editable per-machine price table with locks, undo and reset, **Hit a number**, the sticky summary, the accordion build sheet, the compact product list, side-by-side options and first-week hints (CHANGELOG "The new configurator is on for every dealership").
- **Hit a number** takes a target of all-in monthly payment, deal total or margin % and solves the price (`src/components/configurator/HitANumberBox.tsx:125`).

### 4g. Rep margin and "Raise the price by $X"
- Without `see_cost` (i.e. a rep), every margin on the configurator is **rep margin** = (equipment sell − rep cost) ÷ sell, labelled "Rep margin" (features.md lines 1166-1179; `src/lib/pricing/repMargin.ts`).
- A rep sees the guardrail in words only: "Within guardrails — no approval needed", "Needs manager approval", "Blocked". No floor, approval or target percentage is shown.
- Every approval banner, for every role, says **"Raise the price by $X to skip approval"** (repMargin.ts; FlexSummaryBar.tsx; features.md line 1174).
- `see_cost` = owner, admin, manager (`src/lib/roles.ts:59`). `see_rep_cost` includes rep (roles.ts:67). `see_finance_reserve` = owner, admin, manager (roles.ts:75).
- A rep never sees dealer cost, dealer margin, finance reserve or GP in the configurator. Dealer cost is withheld at the database: reps read the `product_prices_rep` view, which has no `dealer_price` column, and `product_prices` SELECT is owner/admin/manager only (SQL on `pg_policies`: "dealer admins read product prices").

### 4h. Cost change requests
- When it is allowed, a rep's line menu reads **Request a cost change…**: a new rep cost or % off, a reason from a list, and a **required note**. The line shows "Awaiting approval". A manager approves or denies on the line or in the Approvals inbox, and the history reads as one sentence (features.md lines 272-287).
- **Effectively off everywhere.** The per-dealer mode defaults to "Follow each comp plan", and all 5 plans have `allow_rep_cost_edit = false` (SQL). No `configurator_dealer_settings` row exists (SQL). To demo it, switch it on in CPQ Settings ▸ Discount authority.

**Routes:** `/configurator`, `/configurator?deal=<id>`, `/configurator?quick=1`, `/quote/mobile`. Rules and authority settings are at `/admin/cpq` (`?tab=pricing|authority`).

**Changed since the old film:** the rule count grew, "needs one of" is new, quick start is new, "Ready to send?" is new, saved builds and bundles are new, GBB generation is new, rep margin is new, "Raise the price by $X" is new, cost requests are new, and the catalogue moved to a Postgres copy.

---

## 5. Pricing and leasing

**What it does**
- **Funder rate cards** are held per leasing partner, program (FMV or $1 buyout), term and amount band. Off-book terms are interpolated and labelled as interpolated (features.md lines 292-294).
- **Q (SQL on `lease_rate_factors`):** **13 funders, 1,638 rate factors**, programs `fmv` and `dollar`.
  - Caveat: every funder on Q's demo sheet prices identically (CHANGELOG 2026-09-22 QA pass). Do not film two funders side by side and imply they differ.
- **Payment-first / solve backwards:** enter the monthly the customer will accept and the engine solves the price (features.md lines 289-290; Hit a number "Target monthly payment, all-in").
- **Takeovers / buyouts:** remaining payments, ETF and return freight roll into the payment and are itemised on the customer's document (features.md lines 341-345).
- **New: "Read their statement".** A text PDF of the incumbent funder's statement is read **on the device** (no AI or OCR). It extracts payment, payments remaining, payoff, ETF, lessor and agreement number, each with a confidence label. It recognises 25 funders (features.md lines 347-362; LESSORS list in `src/lib/buyout/statementParse.ts:59`, 25 names counted). A photo or a scan reads nothing and is shown beside the form.
- **Margin floor and approvals (Q, SQL on `cpq_pricing_settings`):** target 40%, **approval line 32%**, **hard floor 25%**, lift 10%. Pricing under 32% needs a manager. **Under 25% is blocked and cannot be approved at all** (`src/lib/approvalsInbox.ts:24-25, 186-189`).
- Margin is equipment-only ("Hardware gross margin"). Service GP is kept separate (features.md lines 296-298).
- Pricing programs follow the customer, with rules like "customer type Government → GSA Schedule". Q's programs (SQL): Standard, US Communities, Non Profit, GSA Schedule (features.md lines 304-326).
- **"Prices changed — update the proposal?"** When the build no longer matches a proposal or quote, a banner shows the delta. A draft proposal refreshes in one click; a sent proposal gets "Create revised version"; a signed deal is locked and gets "Start a new version" (features.md lines 482-489; `src/components/configurator/PriceChangeBanner.tsx`, `src/hooks/usePriceChangePrompt.ts`).

**Routes:** `/leasing` with tabs Applications, Payment calculator, Rate cards, Partners and Portfolio (`src/pages/Leasing.tsx:65-69`). `/settings/leasing`. `/admin/leasing` redirects to `/leasing?tab=partners`.

**Roles:** a rep sees the funder panel read-only. Rate grid edits are owner/admin; `lease_rate_factors` is locked to owners, as the 2026-09-16 "instruments" change proved.

**Old transcript lines now wrong**
- [1:36] "…below the floor the quote cannot be sent until a manager clears it." There are **two lines**. Under the *approval line* a manager must approve. Under the *floor* nobody can approve; the rep must reprice.
- [1:44] "Rep cost is never exposed." **Wrong.** Reps do see *rep* cost and rep margin (`roles.ts:67`). What a rep never sees is **dealer cost**, dealer margin, finance reserve and GP.

---

## 6. Service

**What it does**
- Metered service: included pages from the machine's rate group, overage beyond them, and colour and B&W metered separately (features.md lines 368-369).
- Rates are per machine, not one global rate (lines 371-373).
- Pooled or per-device, with escalators. **Cost-per-copy rental** is an acquisition type alongside lease and cash (lines 375-376).
- The base rate covers the allotment and nothing else. This is regression-tested so that base plus overage at the customer's volume equals the quoted monthly (lines 378-383).
- **New: service from the customer's real fleet.** Expected and included volumes come from the account review, the dealer's own meter reads, or a saved assessment, and the panel names the source and period (lines 385-402). Live example (CHANGELOG "In the field"): Pollock's "Richmond County School System" shows 75,600 pages/mo, "Last 12 months · 8 devices".
- Service terms appear only when service is sold (lines 404-406).
- **Service rates per dealer (SQL on `service_rates`):** only Q has its own card, with 20 rows. The other four dealers quote from the built-in default card (confirmed by price-book health in the CHANGELOG).

**Roles:** reps do not see the service margin % (CHANGELOG #69).

**Old transcript:** [2:21] "…the margin on the service agreement shown live beside it" is true for owners, admins and managers only. It is hidden from reps.

---

## 7. Approvals inbox (new)

**What it does**
- One screen of every deal waiting on a decision. Each card shows the customer, the rep, what is asked (pricing below the approval line, or a rep cost change), the reason in words and **"Raise the price by $X to skip approval"** (features.md lines 331-339).
- **Approve** / **Deny** with a note is one tap. A denial needs 12+ characters (CHANGELOG #84). A quote under the hard floor cannot be approved.
- The rep hears about the decision in the bell wherever it was made: inbox, deal or settings card. Decisions from the last 14 days are listed below.
- The **Approvals** nav link carries a count (`ApprovalsNavLink`, GlobalNav.tsx:19, 204, 296). It works on a phone.

**Route:** `/approvals`

**Roles:** owner, admin, manager (`decide_approvals`, roles.ts:103). **Reps see neither the page nor the link.** Only `see_cost` viewers see dealer margin against the floor on the cards.

**Changed since the old film:** new.

---

## 8. Proposals

**What it does**
- A proposal is an ordered list of sections with three owners: company copy, **from the build** (which is never editable prose), and the rep's own words (features.md lines 412-418).
- There are **23 section types** (`src/lib/proposal-modules.ts:244-378`): Cover, Cover letter, Executive summary, Who we are, **A short introduction (video)**, Solutions we deliver, Credentials, Brands we represent, Our proven process, Where you are today, Fleet assessment, Recommended solution, What changes for you, Investment, Optional add-ons, Service & support, Working with us, Options compared, Proof, What customers say, Next steps, Let's talk, Terms.
- There are **4 templates**: Standard proposal, Competitive takeover, Fleet refresh, Single device (`src/lib/proposalSections.ts:206-255`).
- **One renderer.** `ProposalDocument` draws the rep's Preview, the customer link and the print/PDF (CHANGELOG 2026-09-22 proposal pass; package-pricing entry: "the rep's Preview and the Proposal modules sample … render the same component").
- **Video section:** off by default. Paste a YouTube, Vimeo or Loom link, or a direct .mp4/.webm/.mov (`src/components/proposal/ProposalDocument.tsx:2756-2797`; proposal-modules.ts:268).
- **Share link:** `/p/:token`. The customer needs no login; access is by the RLS policy for `status='sent'` (`src/App.tsx:169-175`).
- **Options compared** shows good / better / best side by side. **The customer picks:** "Choose this option", confirm, name. It is recorded on the server by option id; the page never sends a price (features.md lines 426-440).
- **Engagement tracking:** opens, time reading, devices, prints and downloads, and which sections and options held the reader ("Read the Investment section for 3m 12s"). The lists mark a proposal **Hot** when it is opened twice or more in 72 hours or read for 3+ minutes. The rep's own visits are not counted. No IP is stored (features.md lines 491-502).
- **Customer questions:** a floating "Ask a question" about the whole proposal, a section or an option. It lands in the panel and the bell, the rep answers inline, and the customer can reply. There is a follow-up nudge "Opened 3 times, no reply — follow up?" (lines 504-515).
- **Package pricing** (display only): accessories are listed by name and quantity with no price, and each machine shows one figure (lines 459-480).
- **Pick, then sign:** after choosing, the customer signs an **order form for that option** on the normal signing page (lines 442-457).
- Designed for mono photocopies: states are marked with words rather than tints (ProposalDocument.tsx:608, 1824, 2207).

**Numbers (SQL):** Q has 65 proposals: 40 sent and 25 draft.

**Routes:** `/proposals`, `/p/:token` (public), `/deals/:id` (engagement panel).

**Roles:** every member builds proposals. The output is margin-free.

**Not live / behind a switch**
- **Customer self-sign** is **OFF** by default. Q's dealer-wide switch is `customer_self_sign = false`. It is on only for the pilot deal `f1a95000-0000-4000-8000-0000000000d1` "Northwind Orthopedics — Pick & sign demo" (SQL on `dealer_flow_settings`).
- **Package pricing** defaults to Itemized. Every dealer reads `itemized` (SQL). Pollock asked for Package on 2026-09-24 but it has not been switched.
- A self-signed order form opens an order whose lines come from the deal's **saved** configuration. The rep must "Load Option X into the deal" (open-items).
- The rep's email notice of a choice is queued, not sent (no mail configured).
- The rep's proposal-builder toolbar overflows at 390px (open-items, `src/pages/Proposals.tsx:429`). The customer's page is fine at that width.

**Demo deals:** "Northwind Orthopedics — Options demo (customer chooses)" `…00c1` / proposal `…00c2`, and the pick & sign demo `…00d1`.

**Changed since the old film:** the customer picks an option, engagement tracking, questions, the video section, package pricing, pick-then-sign, and "Prices changed". "One renderer" is still true.

---

## 9. Documents and the Document Hub

**What it does**
- There are **15 document types**, taken from the code registry (`src/components/documents/registry.tsx:64-261`; mirrored in `src/lib/workbook/documentAudience.ts:49-63`):
  - **Customer-facing (7):** Quote; Service Agreement; FMV Lease; Letter of Intent; Credit Application (code `new_customer`); Managed Services Agreement; **Schedule A — Equipment by Location**.
  - **Internal (8):** Installation; Lease Funding; Lease Return; Interterritorial; Relocation; Removal (equipment removal); Commission (worksheet); **Delivery Tickets**.
  - **Docs disagree:** features.md lines 531-539 say "six customer-facing … seven internal" and omit Schedule A and Delivery Tickets. The code wins: **15 = 7 + 8**.
- Every document is pre-filled from the deal. Pre-fill fills gaps and never overwrites a typed field (features.md lines 621-627).
- **Deal types (6):** lease, purchase, CPP rental, state contract, managed print, services only. The type is inferred from pricing, can be overridden in one pick, and is mirrored to HubSpot as `cpq_deal_type`. Each type has its own starting packet and its own fulfilment path (features.md line 529; `docs/deal-types.md`).
- **Packet templates (SQL on `packet_templates`, 6 per dealer, 24 total):**

  | Deal type | Packet |
  |---|---|
  | Lease | quote, lease agreement, service agreement, credit application, delivery acceptance (optional) |
  | Purchase | quote, purchase agreement (LOI), service agreement, delivery acceptance |
  | CPP rental | quote, CPP rental agreement, CPP service agreement, delivery acceptance |
  | State contract | quote with acknowledgement, Schedule A, service agreement |
  | Managed print | quote, Managed Print agreement, Schedule A |
  | Services only | Managed Services Agreement |

- **Schedule A** has one initials line per location and is added automatically on a multi-site deal (registry.tsx:230-244).
- **Delivery Tickets** print one page per ship-to site for the truck (registry.tsx:245-259).
- **Preview full packet** shows the exact PDF bytes that will be sent, with signature boxes drawn, and offers Download, Place fields and Send (features.md lines 638-646).
- Signed packets are split into **per-document PDFs** on completion (features.md lines 697-713).
- Paper-signed packets are covered in section 10.

**Routes:** `/documents` (`?deal=`). Terms and custom types are under `/settings`.

**Roles:** everyone. The commission worksheet prints rep cost and margin, which makes it an internal document.

**Caveat:** the Document Hub is desktop-only by design (features.md lines 1096-1100).

**Old transcript lines now wrong**
- [2:42] "12 document types" → **15**.
- [2:47] "…new customer…" → now called **Credit Application**.
- [3:00] "Five customer facing, seven internal" → **seven customer-facing, eight internal**.

---

## 10. Signature / e-sign

**What it does**
- Envelopes support multiple signers, sequential order and field placement (features.md lines 750).
- The audit trail stores the consent language verbatim, whether consent was given, the signer's IP and user agent, and a **content hash** (lines 752-754).
- **Immutability is enforced by the database.** `authenticated` has **SELECT only** on `sign_events` and `sign_fields`, and there is no update or delete policy (SQL on `role_table_grants` and `pg_policies`).
  - Accurate wording: "the database refuses edits to the signing history". It is done through grants, not triggers.
  - `sign_envelopes.execution_mode` has an immutability trigger (SQL on triggers).
- **Paper signatures:** Preview full packet → **Sign on paper** → print → upload the ink-signed scan. The upload lands as a completed envelope, so the order, tasks, archive and filing all happen the same way (`docs/paper-signatures.md`). Q has 0 paper envelopes live (SQL). The edge function `sign-envelope-paper` v6 is deployed.
- **Signed Orders archive:** a flat cross-deal list with search, the executed PDF, signers, audit trail and hash as sent and as executed. "Out for signature" is one click away. Downloads are signed URLs that expire in 10 minutes. The screen cannot write (features.md lines 761-777).
- **Numbers (SQL):** Q has 23 envelopes: 18 completed, 4 sent, 1 declined.

**Routes:** `/signed-orders`, the Signatures entry in the Document Hub, `/sign/:token` (public signing page).

**Changed since the old film:** paper signatures are new, per-document split is new, and self-sign order forms are new. The rest holds.

---

## 11. Orders and fulfilment

**What it does**
- **A signature starts the order.** A completed envelope creates an order at Contract Signed with a per-dealer number `ORD-00001…` (features.md lines 783-788; trigger `sign_envelopes_create_order`).
- **9 stages (SQL on `order_stages` for Q, matching `src/lib/orders/stages.ts:41-49`), with SLA / warning hours:**

  | # | Stage | SLA / warning |
  |---|---|---|
  | 1 | Contract Signed | 24h / 18 |
  | 2 | Order Submitted | 48h / 36 |
  | 3 | Credit Approved | 48h / 36 |
  | 4 | Funding Authorized | 24h / 18 |
  | 5 | Equipment Ordered | 120h / 96 |
  | 6 | Received at Warehouse | 48h / 36 |
  | 7 | Delivery Scheduled | 72h / 48 |
  | 8 | Installed | 48h / 36 |
  | 9 | Closed Won | no clock |

  The stages sit under **6 phases**: Signature & Capture, Credit & Lease, Equipment Ordering, Pre-Config & Scheduling, Delivery & Install, Activation & Billing (features.md lines 801-808).
- The clock is amber at the warning hour and red when the SLA runs out. A stage with no SLA gets no clock (features.md line 805).
- Every move is recorded. `order_status_history` allows INSERT and SELECT only, so a move cannot be edited (SQL on grants).
- **Tasks:** a **standard checklist ships.** Q has 36 task rules and the other four dealers 32 each (SQL on `task_automation_rules`), seeded by `supabase/migrations/20260910160000_standard_stage_tasks.sql` with a "Restore defaults" button. Q has **901 order tasks** (SQL). features.md line 792 ("none are pre-filled") is **stale**.
- Serials are entered per unit on the order (`src/components/orders/OrderEquipmentSerials.tsx`). Pulling serials from e-automate inventory is "look later" (open-items line 359).
- **Order push to e-automate via CEO Juice** is ID634 `AddOrder`. It stages order lines, and CEO Juice builds the sales order. The screen says "accepted for import", never "order created" (`supabase/functions/ceojuice-push-order/index.ts:19-60`).
  - A successful push advances the order to **Order Submitted** by itself (`supabase/migrations/20260909120000_orders_pipeline.sql:54, 882-888`; `advance_order_to_stage` rpc at ceojuice-push-order:1615).
  - Live (SQL): Q has 1 CEO Juice connection and 11 pushes (4 succeeded, 6 pending, 1 released).
- **DocuWare filing:** the signed packet and workbook are filed into a DocuWare cabinet with index fields (`docs/docuware.md`). The edge functions are deployed. **No dealer has connected DocuWare** (SQL: 0 connections, 0 filings), so it is built but unused.
- **Delivery ticket** is an internal document; delivery acceptance is optional in packets (section 9).
- There are two views: the fulfilment board (the default) and **ERP push** (the four-bucket e-automate board). There is also a table view, My Tasks, and **New order** (a 4-step wizard or a quick form) (features.md lines 801-820; `docs/orders-next.md`).
- **Numbers (SQL):** Q has 55 orders. By stage: Contract Signed 18, Order Submitted 5, Credit Approved 1, Funding Authorized 3, Equipment Ordered 7, Received at Warehouse 5, Delivery Scheduled 7, Installed 4, Closed Won 5.
- Deal types change the path: a purchase passes through the credit and funding stages, and services-only passes through the equipment stages (features.md line 529).

**Routes:** `/orders`, `/orders/:orderNumber`, `/orders?view=…`, `/settings/orders`.

**Roles:** everyone sees the board. Owners, admins and managers run it. A rep can move an order or task assigned to them (features.md lines 795-799).

**Not live / in progress**
- **Next-step owners** (the "order_next_step_and_stage_owners" migration) are applied live but have no UI on `main`. `order_stage_task_owners` has 1 row.
- The installer delivery & acceptance app is **not built**.

**Old transcript lines**
- [5:14] lists 7 stage names. The full nine are above.
- [5:42] duplicates the CEO Juice sentence.
- [5:55] "task templates per stage spawn the work automatically once you define them" is outdated: **a standard checklist is pre-loaded**.

---

## 12. HubSpot integration

**What it does**
- **In from HubSpot:** deals, companies, contacts, the product catalogue and compatibility rules (synced into Postgres), and e-automate equipment for account reviews (features.md lines 847-852, 869-882).
- **Out to HubSpot:** deal amount, buyout fields, win/loss reasons, line items grouped by machine (in batches of 100), `cpq_deal_type`, and the Managed IT lines as their own line items (lines 851-852, 529, 208-209).
- **QuoteCommand quote records:** each quote is its own custom object associated to the Deal and Company, carrying totals, margin, GP, buyout and the full configuration JSON, so good, better and best sit side by side in the CRM (lines 884-895). The type id is resolved by name per portal.
- An **"Open in QuoteCommand ➡️"** calculated property appears on every deal (lines 854-861).
- Quote PDFs attach to the deal as a note with **no expiry** (lines 863-867).
- A push reports partial failures by name and is never shown as success (lines 897-901).
- **HubSpot card:** a React UI extension on deal, company and project records. It shows the quote value, the margin *as a word* (never a number), signature status, order number and stage, SLA, open tasks, next delivery or install, and buttons (`docs/hubspot-card.md`). The backend is deployed (`hubspot-card-data` v8, `hubspot-card-action` v5). **The card itself needs a manual `hs project upload`**. hubspot-card.md §Limits says "until it runs portal 47404459 does not show the card". Confirm it is uploaded before filming it.
- **HubSpot is optional.** A dealer can run on a price-book import (Pollock). Q and PBT have HubSpot catalogue syncs (SQL on `catalog_sync_runs`).

**Routes:** `/settings/integrations`, `/settings/integrations/hubspot/mapping`.

**Caveats:** HubSpot line items carry per-line prices even in Package mode (open-items). `cpq_blended_margin` on the deal is dealer-basis (CHANGELOG #74 "Not done").

**Old transcript:** [4:35] "Nothing here asks a dealership to move CRM" is true, and QuoteCommand now also works **with no CRM**.

---

## 13. Commissions and My earnings

**What it does**
- There is one engine (`supabase/functions/_shared/commissions/calculateCommission.ts`) behind the pay run, the Statement, the Calculator and the quoting preview (`docs/commissions.md`).
- Commissions tabs: **Statement, Calculator, Payouts, Quotas, My plan**, plus **Team** and **Pay run** for leadership (`src/pages/Commissions.tsx:448-476`).
- Features: basis per rule (contract value vs gross equipment sale), month approvals that go "out of date" when a late deal lands, **Mark ‹month› paid** with a reference, and gov/edu handling (commissions.md).
- Kickers: the plan's "GP comm." share, shown as `kicker_amount` on the Statement. The `commission_kickers` table itself has **0 rows** (SQL), so do not describe a "kickers library".
- **"What I'll earn on this deal"** on the configurator rail updates live as the price moves (features.md lines 1023-1027).
- **My earnings** (`/earnings`) shows month to date by status, a pipeline estimate over the rep's own open deals, and 12 months of statements.
- **GP visibility for reps:** in the rail and on My earnings, a rep on a GP-based plan sees a **±10% range** with no percentage, so GP cannot be read back (features.md lines 1029-1040). Owners, admins and managers see exact figures. Paid statements are exact for the rep, with no rate or basis shown.
- **Numbers (SQL):** 5 active plans (Q 1 "QBS Standard Sales Plan (2026)", PBT 2, Pollock 1, Tascosa 1).

**Routes:** `/commissions`, `/earnings`, `/settings/commissions`.

**Roles:** `see_team_commissions` and `manage_comp_plans` are owner/admin/manager. `edit_comp_plan_rules` is owner/admin. The Pay run writes are owner/admin on the server.

**Rep must never see:** GP. **But the Statement tab shows reps a GP column and "GP comm." today** (`StatementTab.tsx:703,711`; open-items). Don't film the Statement as a rep.

**Old transcript:** [6:00] "The commission worksheet prints rep cost and margin from the same record" is true; it is internal.

---

## 14. Reporting and Analytics

**What it does**
- `/analytics` has two tabs: **Dashboard** and **Audit log** (`src/pages/Analytics.tsx:216-226`).
- Dashboard: KPI row, margin histogram, win/loss card, owner table (leadership only) and **Renewals radar** (Analytics.tsx:229-240).
- **Reps see averages of rep margin, never dealer margin** (`marginBasis={canSeeCost ? "dealer" : "rep"}`, Analytics.tsx:229-231).
- The audit feed records edits, not keystrokes: one event per save (features.md lines 1049-1051).
- The renewal pipeline is seeded from lease-end dates six months out (features.md lines 1057-1058; `hubspot-renewal-seed` v33 deployed). It depends on HubSpot.

**Caveat:** "By owner" can show "Unassigned" for every deal because of a build-pipeline defect (CHANGELOG 2026-09-22 QA). Check it before filming the owner table.

---

## 15. Roles, permissions, tenancy; View as rep

**Facts**
- There are four roles: owner, admin, manager, rep (`src/lib/roles.ts:23`). Platform staff (Quantum) sit above them.
- **Every dealership is a separate tenant.** Policies key on `has_dealer_access(auth.uid(), dealer_id)` (SQL `pg_policies`). There are 5 dealers live: Quantum, Pollock, Power Business Technology, Tascosa, Eakes (SQL).
- **Cost is withheld at the database.** `product_prices` is readable only by owner/admin/manager, and reps read `product_prices_rep`, which has no `dealer_price` column (features.md lines 1159-1162; SQL policy "dealer admins read product prices").
- **Reps currently see every deal and proposal in their dealership.** RLS is `has_dealer_access` for all members (SQL). The territory restriction is built in the database (RESTRICTIVE policies, `territory_access` migration applied live 2026-09-24) but it is **inert**: no territories, no settings, no UI on `main`.
- **View as rep:** Account menu → View as rep, or the card on Settings. Every role gate follows it: dealer cost, rep floor, GP and finance reserve disappear, and a gold banner stays until you exit (features.md lines 1141-1164).
  - It is a screen preview; the session and RLS are unchanged, as the banner says.
  - On Commissions, leadership can use **View as ‹name›** to preview a specific rep (lines 1181-1187).

**Routes:** Settings, the Account menu, `/admin` (users).

**Old transcript lines now wrong**
- [6:25] "A rep sees their own deals." **False today.** Say "A rep works inside their own dealership and never sees its cost book."
- [6:27] "A manager approves below floor pricing" → a manager approves pricing below the **approval line**; below the **floor** nothing can be approved.

---

## 16. Setup wizard (new)

- It has **13 steps** (`src/lib/onboarding/steps.ts:101-218`): Dealership profile, Branding, Users, Modules, Price book import, Lease rate cards, Service rate card, Commission plan, Approval limits, HubSpot (optional), Document terms, Orders, Go live.
- The step estimates add up to 315 minutes (steps.ts `minutes`: 10+10+15+5+60+20+15+30+15+30+45+30+30).
- A step turns green by itself when the data shows it is done. It can be marked done or skipped with a reason, and undone. `?step=` links straight to a step, and `?view=list` gives the checklist. The wizard changes no settings itself (features.md lines 955-977).
- **Route:** `/admin/onboarding`, owner/admin. The nav shows a Setup badge with the count.
- Live: only Pollock has a `dealer_onboarding` progress row (SQL).

---

## 17. Price-book health (new)

- It reads the catalogue exactly as the configurator prices it and lists problems with counts, examples and severity: implausible costs, $0 sellables, a colour flag contradicting the name, machines with no speed, required groups that exclude their own finisher, punches with no finisher rule, accessories no rule offers, the default service card, and so on (features.md lines 979-1003).
- Fixes are explicit and previewed (before → after). Only **Apply to price book** writes (lines 1005-1011).
- Speeds are read from model numbers for Konica, Xerox and Canon, with named refusals (lines 1013-1019; `src/lib/modelSpeed.ts`).
- **Q findings (2026-09-24, CHANGELOG):** 9 colour flags that disagree with the name, 41 required groups excluding their own finisher, 18 machines with no speed, 19 punch units with no finisher rule, 112 accessories no rule offers. Pollock: 14 implausible costs (BH 451i at 74.9% rep margin).
- **Route:** `/settings/price-book-health`. **Owner/admin only**; a rep is refused and never sees the tile (`src/App.tsx:242`, RequireDealerAdmin). It reads dealer cost.

---

## 18. Integrations page

- `/settings/integrations` holds four integrations: **HubSpot**, **CEO Juice · e-automate**, **DocuWare**, **Connect Claude (MCP)** (`src/pages/Integrations.tsx:321-557`; features.md lines 948-953).
- Every role sees the page. Connecting or disconnecting is owner/admin. A rep can read status and connect their own Claude.
- Live state: HubSpot is connected for Q and PBT. CEO Juice is connected for Q only. DocuWare is connected for no one (SQL).

---

## 19. Asking Claude (MCP)

**Facts on `main`**
- There are **16 tools, all read-only** (`src/lib/mcp/tools/index.ts:43-65`; `readOnlyHint: true`, `src/lib/mcp/runtime/tool.ts:105`):
  - Orientation: whoami.
  - Pipeline: list_renewals (default 90 days, max 730), pipeline_summary, get_deal, margin_analysis.
  - Price book: search_catalog, machine_accessories, lease_terms.
  - Customer: search_accounts, get_account.
  - Paperwork: list_quotes, get_quote, list_documents, envelope_status.
  - Money: commission_summary.
  - Fulfilment: order_status.
- Every tool runs as the signed-in user under RLS. No tool accepts a dealer id. A scope layer refuses honestly instead of returning a quieter answer. Deal and pipeline tools withhold blended margin without `margins:read`, which is owner/admin/manager (`src/lib/mcp/runtime/scopes.ts`; features.md line 1178).

**What is live in production**
- The deployed `mcp` v18 bundle has **19 tools**: the 16 above plus 3 **write** tools from unmerged **PR #81** (`create_proposal_from_deal`, `update_proposal_section`, `set_proposal_published`, which is confirm-gated). They are deployed but not on `main`.

**OAuth sign-in (#85)**
- The code is merged and the audience-hook migration is applied. It is **not switched on**. Three things are needed:
  - Supabase dashboard → Auth → OAuth Server (enable, path `/oauth/consent`, dynamic registration);
  - the Custom Access Token hook `mcp_oauth_audience_hook`;
  - redeploying `mcp` with `--no-verify-jwt` (`docs/mcp-connect.md` §"Switching it on").
- The live function is `verify_jwt: true` and its bundle has no OAuth metadata. **Today the only working way in is pasting a one-hour token into Claude Code.**

**Route:** Settings → Integrations → Connect Claude (MCP). The consent screen is `/oauth/consent`.

**Old transcript**
- [6:51] "ships a read-only MCP server" is true of `main`. For production, say "sixteen tools that read your business" and leave writes unmentioned until #81 merges, or disclose them.
- The [6:54] example "which leases expire in the next 90 days" matches `list_renewals`.
- **Do not show Claude.ai web or mobile connecting by sign-in.** It does not work yet.

---

## 20. On a phone

- **Quick quote** is at `/quote/mobile`, the **Quick** button, or `/configurator?quick=1`. It is laid out one-handed at 390px.
  - Start from quick start, a search, a saved bundle or a recent deal.
  - One machine card at a time, with swipe and a 48px stepper.
  - Lease/Cash, term chips and service on/off.
  - The fleet-volume panel and the statement reader.
  - Monthly, equipment total and a margin chip are **pinned** above **Save to deal** and **Send proposal** (features.md lines 1064-1079; `src/components/configurator/QuickQuoteView.tsx`).
- Send follows the desktop flow (approval when gated, otherwise "Ready to send?"), and a blocked quote cannot be sent. **A rep sees rep margin in words, never a cost.**
- Also mobile: the Deals list as cards, the nav drawer, number pads (features.md lines 1081-1094), the **Approvals inbox**, and the customer's proposal and signing pages.
- **Desktop-only on purpose:** the Document Hub, the price book, the leasing rate grid, Analytics, Settings and admin (features.md lines 1096-1100).
- Verified at 390×844 as a rep on all five dealers, with no horizontal scroll (CHANGELOG "In the field").

**Old transcript:** [7:13-7:26] is still true; Quick quote is the upgrade.

---

## 21. Notifications and the bell

- `EngagementBell` in the top bar reads `rep_notifications` (`src/components/GlobalNav.tsx:15, 376`).
- The kinds are `engagement_followup`, `proposal_comment`, `option_sign_started`, `option_signed`, `option_sign_declined`, `approval_decided`, `cost_adjustment_decided` and `general` (migration `20260924…` CHECK lists; `supabase/migrations/20260924200000_proposal_engagement_and_comments.sql:185`).
- The bell tells the **rep**: a customer asked a question, the proposal was opened 3 times with no reply, the customer started or finished signing, or an approval or cost request was decided.
- **A manager is not belled when a request arrives.** The Approvals nav badge count is the manager's signal.
- It is in-app only; no email is sent.

---

## Top 12 true things to show, ranked by what a dealer principal cares about

1. **"What can my reps see of my cost book?"** Use View as rep: dealer cost, dealer margin, GP and finance reserve vanish, and the database withholds dealer cost from real reps (the `product_prices_rep` view). Do *not* open the Commissions Statement in this segment.
2. **The margin guardrails have teeth.** At 32% a quote needs a manager and at 25% it is blocked (Q). The banner says "Raise the price by $X to skip approval", and the manager clears it in one tap in the Approvals inbox on a phone.
3. **Every quote is buildable.** 10,844 compatibility rules on Q's own catalogue, plus 111 "needs one of" rules: tick the FS-539 finisher and the RU-519 relay unit is added with a sentence explaining why.
4. **Quick start from the customer's needs.** Pages, people, 11x17, stapling and a $500 budget return three already-built machines from the dealer's own catalogue, and "Build all as options" turns them into good / better / best.
5. **The customer's proposal link.** Branded, no login, options side by side, "Choose this option", and a question box. Then the rep's engagement panel: "Read the Investment section for 3m 12s", the Hot badge, and the bell.
6. **The takeover.** The rep uploads the incumbent's statement PDF, it is read on the device, and the payoff is itemised on the customer's document ("we are paying off $X").
7. **Signature → order with a clock.** 18 completed envelopes on Q. The order appears at Contract Signed and moves through 9 stages with SLAs; stage 5 (Equipment Ordered) has 120h. The standard task checklist is pre-loaded, and Q has 901 tasks.
8. **The CEO Juice push moves the order to Order Submitted by itself.** It is honest about the result ("accepted for import", never "order created").
9. **Fifteen document types from one deal.** The packet follows the deal type: lease, purchase, CPP rental, state contract with Schedule A by location, managed print, services only. Paper signatures land in the same place.
10. **Quick quote on a phone at 390px.** A quote in about two minutes, with monthly and margin pinned under the thumb, and send gated exactly like desktop.
11. **Price-book health and the setup wizard.** The catalogue is audited ("9 colour flags that disagree with the name") with previewed fixes, and the 13-step wizard turns green from the dealership's own data.
12. **HubSpot round-trip without lock-in.** Good, better and best land as three QuoteCommand records on the deal, the "Open in QuoteCommand" link is on every deal, and a dealer with no HubSpot can still import a manufacturer price book and quote on day one.

Honourable mentions: fleet assessment → priced replacement ("$6,090/yr savings" on the Summit demo), service priced from the customer's real meter reads, "Prices changed — update the proposal?", and saved dealer bundles at a fixed price.

---

## Claims to avoid

| Don't say | Why | Say instead |
|---|---|---|
| "A rep sees only their own deals." | RLS lets every member read every deal and proposal in their dealership. Territory access is built in the database but inert, with no UI. | "A rep works in their own dealership and never sees your cost." |
| "Rep cost is never exposed." | Reps see *rep* cost and rep margin by design (`roles.ts:67`). | "Dealer cost never reaches a rep." |
| "Reps never see GP." (unqualified) | The Commissions Statement shows reps GP and "GP comm." (`StatementTab.tsx:703,711`). | "The configurator and My earnings never show a rep GP." |
| "7,000 compatibility rules." | Stale. | "Over ten thousand rules on Quantum's catalogue" (10,844). |
| "Twelve document types; five customer-facing, seven internal." | Stale. | "Fifteen: seven for the customer, eight internal." |
| "A manager can approve anything below the floor." | Below the hard floor nothing is approvable. | "Below the approval line a manager decides; below the floor it's blocked." |
| "Connect Claude with a normal sign-in on web or mobile." | OAuth is not switched on in production. | "Connect Claude Code today; sign-in connector coming." |
| "Claude can build and publish proposals for you." | Those write tools are in unmerged PR #81, though deployed. | Leave it out, or label it as coming soon. |
| "The MCP server is read-only." (about production) | Production has 3 write tools deployed. | "Sixteen tools that read your business." |
| "Customers sign their chosen option directly." | Off by default; it is on for one Quantum pilot deal only. | Show it as an option a dealer can switch on. |
| "Package pricing on your proposals." | Built, but every dealer is on Itemized. | "You choose itemized or package." |
| "Reps can request cost changes." | Every plan has `allow_rep_cost_edit = false`, so it is effectively off everywhere. | Switch it on for the demo, or say "when you allow it". |
| "The catalogue is live from HubSpot" / "syncs automatically". | It is a synced copy, refreshed on demand. Q last synced 2026-09-10. | "Your HubSpot catalogue, synced into QuoteCommand." |
| "Emails the rep / emails the customer." | No mail is configured; the outbox is queued only. | "Tells the rep in the app." |
| "Duty cycle of that model." | The check is a class-level recommended volume. | "Flags volume over what that class of machine is built for." |
| "Files everything into DocuWare." | Built and deployed, but no dealer is connected. | "Can file into DocuWare." |
| "Serials come from e-automate." | Serials are typed on the order; the inventory pull is "look later". | Don't claim it. |
| "Installers sign delivery on a phone app." | The installer D&A app is not built. | Don't claim it. |
| "Assign next-step owners / territories." | The migrations are applied live; no UI on `main`. | Don't show it. |
| "Kicker library." | `commission_kickers` has 0 rows; the GP share is the "kicker". | "GP share." |
| "Different funders, different rates" (on Q's demo). | Q's 13 demo funders price identically. | Show one funder. |
| "The HubSpot card on every deal." | The card needs a manual `hs project upload`; confirm first. The "Open in QuoteCommand" property is safe to show. | Show the property. |
| "Account reviews for every customer." | Beta, and only accounts with e-automate data. | Qualify it. |
| "Service card per dealer." | Only Quantum has its own; four dealers are on the built-in default. | Show Quantum's card only. |
| "Analytics by owner." | May show "Unassigned" (build defect). | Check it before filming. |
