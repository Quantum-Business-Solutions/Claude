# QBS Website — Recovery & Working State (2026-07-17)

Working files from the website recovery session (after the original session was
deleted). HubSpot portal **20682069**, site **thequantumleap.business**, theme
**Quantum Void** (one of 9 wholly-owned themes, ~48 shared modules each).

## Offering map (positioning agreed with Shawn)

| Page | Offering | Notes |
|---|---|---|
| `/en/services/hubspot-onboarding` | **Standard HubSpot Onboarding** — HubSpot's guided scope at 25% off published rates | Quick-sell page for HubSpot reps. Landing page id `216087137824`. Intentionally light/HubSpot-look styling. |
| `/services/onboarding` | **Guided onboarding** — client team does the work, Quantum guides. Blocks of hours + $295 CRM launch. | Site page id `191573866652`. **Shawn manually restored an old version — do not modify without his go-ahead.** Original pricing content also lives in archived draft `216088091298` ("HubSpot Onboarding - Comparison Chart DRAFT") and in the page's 79 revisions. |
| `/hubspot-build` | **HubSpot Implementation & Build** — "we do the work", Growth-Ready implementation content merged in | Site page id `208130422201`. |
| `/q2-revenue-machine` | **Q2** — integrated revenue platform for office technology dealers | Site page id `207650758165`, fully restored from Atlas original (id `207626223693`, archived). |

## What changed today

- **Q2 page**: restored all 24-module Atlas content into Void (hero, stats 24%/83%/$2.1M/100%, Hidden Costs, 4 Command feature sections + dashboards, video 139933937452, 4 real testimonials, 90-day gantt, AI/HubSpot cards, GTM Playbook offer w/ Qwilr link). Published.
- **Nav menu `184144186499` ("2025 Quantum Menu")**: Q2 added to top of Solutions; new Tech dropdown (Technology Overview, Standard HubSpot Onboarding, Onboarding Services, Migrations, HubSpot Build, Integrations, Command Apps, ZoomInfo Help, ConnectAndSell Services, Q2).
- **Header partial** (`Quantum Void/templates/partials/header.html`): removed the hardcoded Tech dropdown (old permissions workaround) that duplicated the menu-driven one.
- **Standard HubSpot Onboarding LP**: unarchived + published at `/en/services/hubspot-onboarding`.
- **Build page**: merged implementation-page content (challenges checklist, testimonials, guided-onboarding cross-link). Published.
- **Contact Us** (`179475768950`): added `quantum-contact` module (form `1ff65e03-7449-4e39-9ebb-2fb67dcec18f` "Contact form" + meeting link + email) so visitors can write instead of booking. Published.

## Void module catalog (numeric IDs required in layoutSections params)

| Module | ID |
|---|---|
| quantum-hero | 217248524134 |
| quantum-rich-text / FAQ | 217248524682 |
| quantum-feature-split | 217248524197 |
| quantum-cta-band | 217248524161 |
| quantum-stats-band | 217248524205 |
| quantum-testimonial-slider | 217248524117 |
| quantum-logo-strip | 217248524194 |
| quantum-process-flow | 217287090745 |
| quantum-roadmap (gantt) | 217324784732 |
| Feature graphic (quantum-image) | 217248524692 |
| quantum-services-list | 217248524168 |
| quantum-comparison | 217248524114 |
| quantum-contact | 217248524640 |
| HubSpot native video | 35056501883 |

Numeric IDs per theme discoverable via `GET /content/api/v4/custom_widgets?name__icontains=<name>`.

## API patterns

- Edit: `PATCH /cms/v3/pages/{site-pages|landing-pages}/{id}/draft` with `{"layoutSections": ...}`
- Publish: `POST .../{id}/draft/push-live` (204)
- Unarchive: `PATCH .../{id}?archived=true` body `{"archived": false}`
- Menu: `GET/PUT /cms/v3/menus/184144186499` (full `body.pages_tree` round-trip)
- Theme source: `GET/PUT /cms/v3/source-code/published/content/<path>` (PUT is multipart `-F file=@...`)
- Module fields: `GET .../content/<theme>/modules/<mod>.module/fields.json`

## Files

- `q2_atlas.json` — original Atlas Q2 page (source of truth for Q2 content)
- `q2_void.json` / `q2_patch2.json` — Q2 before restore / final published layout
- `onboarding_backup.json` — /services/onboarding Void version before today's edits
- `std_onboarding.json` — archived Standard HubSpot Onboarding LP (25%-off charts)
- `comparison_draft.json` — archived draft holding the $295 CRM launch / tier pricing
- `build_backup.json`, `contact_backup.json` — pre-edit backups
- `menu_patch2.json` — nav menu with Tech dropdown
- `header_new.html` — header partial with hardcoded Tech removed (as deployed)

## Outstanding

- `/services/onboarding` rework (original content in Void styling) — waiting on Shawn.
- Blog listing page entity `66867919382` — HubSpot UI only (Content → Blog → Blog Listing Pages).
- Optional: full audit of remaining HubSpot-services pages vs Atlas originals.
- Shawn to rotate the HubSpot private app token shared during this session.

## 2026-07-18 — New solution landing pages (drafts) + AEO visual

- Five new Void landing pages built as **drafts** (publish pending approval/classifier):
  hubspot-portal-audit `217438044208`, hubspot-training `217438044210`,
  revops-services `217438141499`, fractional-leadership `217438044214`,
  tech-stack `217438044216` (partner/affiliate links page — swap in PartnerStack URLs).
  Generator: `build_solution_pages.py`. All pricing from Client Command service catalog.
- SEO/AEO page `217437850443`: added "How AEO works" question-map section
  (`aeo-question-map.svg`, uploaded to /quantum-theme/art) and pushed live.
  Pre-edit draft backup: `aeo_page_pre_qmap.json`.
- SalesChain migration guide published (by Shawn via UI):
  /blog/migrating-from-saleschain-to-hubspot-dealer-guide
- Menu tie-in for the five new pages: pending page publish.
