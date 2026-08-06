# HubSpot Solutions Partner Directory — Master List

Automated export of **every partner profile** in the public
[HubSpot Solutions Partner Directory](https://ecosystem.hubspot.com/marketplace/solutions).

This replaces the manual copy-paste process. One command rebuilds the whole list.

```bash
pip install openpyxl              # optional, only needed for the .xlsx output
python3 scripts/fetch_hubspot_partners.py
```

## Outputs

| File | Description |
| --- | --- |
| `data/hubspot_partners.csv` | Master list, UTF-8 BOM (opens cleanly in Excel) |
| `data/hubspot_partners.xlsx` | Same data, formatted with frozen header + autofilter |
| `data/listing_details.cache.jsonl` | Raw per-profile API responses (cache) |

Rows are sorted **Elite → Diamond → Platinum → Gold → untiered**, and by review
count within each tier, so the most credentialed partners are at the top.

## Columns

| Column | Notes |
| --- | --- |
| `company_name` | Company name from the profile |
| `directory_url` | Public directory profile link |
| `website` | Partner's own site (usually their HubSpot-partner landing page) |
| `tier` | `elite` / `diamond` / `platinum` / `gold`, blank if untiered |
| `partner_type` | `partner` or `provider` |
| `review_count`, `rating` | Directory review stats (rating out of 5) |
| `country`, `city`, `state` | Primary office — physical office if listed, else first remote location |
| `all_countries` | Every country the partner lists an office in |
| `regions` | North America / EMEA / APAC / South America labels |
| `office_model` | Physical office, works remotely, or both |
| `languages` | Languages served (ISO codes) |
| `services` | Service catalogue entries (43 possible) |
| `industries` | Industry specialisms (37 possible) |
| `accreditations` | HubSpot accreditations — the hard-to-earn ones (CRM Implementation, Custom Integration, Onboarding, Data Migration, Platform Enablement, Solutions Architecture Design) |
| `certifications` | HubSpot Academy certifications held |
| `client_size_focus` | Client employee-count ranges the partner targets |
| `budget` | Minimum engagement budget band |
| `works_with_breeze` | Breeze (HubSpot AI) capability flag |
| `integrations_supported` | Count of marketplace apps the partner supports |
| `first_published`, `last_published` | Profile publish dates (UTC) |
| `listing_name`, `slug`, `listing_id` | Directory identifiers |
| `partner_id`, `profile_id`, `partner_portal_id` | HubSpot-internal partner identifiers |
| `description` | Profile pitch copy, newlines flattened |

## How it works

The directory is a client-rendered React app, so there is no HTML to scrape.
It talks to HubSpot's "chirp" RPC gateway, and two of those RPCs are public and
unauthenticated:

```
POST https://api.hubspot.com/chirp-frontend-external/v1/gateway/<service>/<rpc>
```

1. **`PersonalizationPublicRpc/search`** — the paginated listing index.
   Filtered to `PRODUCT_TYPE = SOLUTIONS_PARTNER_PROFILE`, 250 per page.
   Sorted by `LISTING_NAME ASC`: the default relevance ranking reshuffles
   between requests, which silently drops and duplicates rows during deep
   pagination. Alphabetical sort is stable.

2. **`MarketplaceListingDetailsRpc/getListingDetailsV3`** — the full profile
   for one `listingId`. This is where location, website, services, industries,
   accreditations and certifications come from; the search index alone does not
   include them.

Gotchas worth knowing if you extend this:

- Filter values need a `__typename` discriminant or the gateway rejects them
  with `Missing __typename or discriminant for union member`. String filters use
  `com.hubspot.marketplace.search.models.filters.StringFilterQuery`.
- Detail responses wrap every field as `{"value": x, "__typename": ...}`.
  The `unwrap()` helper flattens these.
- Offices arrive under **either** `physicalOfficeLocations` or
  `remoteLocations` depending on how the partner works — read both, or you lose
  location on roughly three quarters of profiles.
- Untiered profiles report `tier` as the string `"none"`, normalised to blank.
- `getListingDetailsV3` keys off `listingId` only. There is no slug lookup.

## Re-running

- Stage 2 is **cached and resumable**. Interrupt it and re-run; it picks up
  where it left off. Delete `data/listing_details.cache.jsonl` to force a full
  refresh — the cache never expires on its own, so do this whenever you want
  current data rather than a rebuild of the same snapshot.
- Detail fetching runs 8 concurrent workers with exponential backoff on
  429/5xx. That is deliberately modest; raising it risks throttling.
- `robots.txt` on `ecosystem.hubspot.com` allows `/marketplace/*`.
- Flags: `--no-details` for a fast index-only pass, `--limit N` for a smoke test.

## Filterable dimensions

`MarketplaceStorefrontPublicRpc/getSearchFilterConfig` reports the facets the
directory itself supports, if you ever need to slice server-side instead of in
the spreadsheet:

`PROFILE_SOLUTIONS_PARTNER_TIER` (4) · `PROFILE_BUDGET` (4) ·
`PROFILE_INDUSTRIES` (37) · `PROFILE_CATALOG_SERVICES` (43) ·
`PROFILE_LANGUAGES` · `PROFILE_SUPPORTED_LISTINGS` ·
`PROFILE_CERTIFICATIONS` · `PROFILE_LOCATION_COUNTRY` (247) ·
`PROFILE_OFFICE_LOCATION` (3) · `PROFILE_ACCREDITATIONS` (9)
