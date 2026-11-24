# HubSpot user-level credential and sequences-as-packages (ClientCommand)

Written 2026-11-24. A handoff for another agent picking this up. Nothing described here is merged or has run against a real HubSpot.

**Goal:** make sequences deployable as packages. HubSpot's sales email templates and sequences APIs refuse a portal (private-app) token. They accept only an OAuth token from a developer-platform app with user-level access (`isUserLevel: true`). That token belongs to one person in one HubSpot account and lasts 30 minutes. Every other HubSpot call in ClientCommand uses portal tokens, so this is a separate path.

Repo: `Quantum-Business-Solutions/clientcommand` (Supabase project `zjtgesaiemlveuoymubo`, edge function `client-command-mcp`).

## What exists: two open PRs, nothing merged

### #637: the credential (branch `claude/hubspot-user-credential`)

- One shared app registration, `hubspot_user_app`, sits in `qbs_internal_services`. The Client ID and secret are entered in Settings → Internal Services, like Canva. It uses OAuth with no PKCE and sends the client secret in the request body.
- Requested scopes:
  - `automation.email_templates.read` and `.write`
  - `automation.sequences.read`, `.create`, `.edit` and `.delete`
  - There is no enrollments scope.
- Each client portal gets one `client_credentials` row (service `hubspot_user`). It holds the person's encrypted access and refresh tokens, plus the HubSpot account ID and who approved it. One person can connect many portals, one row each.
- Connect flow: the `start_hubspot_user_connect` tool (or the `oauth_start_portal` action in `manage-credentials`) returns a link. It lands on the existing `/settings/oauth/callback` page. The callback asks HubSpot which account the token is for and **stores nothing if it isn't the portal the connection was started for**.
- Tools:
  - `start_hubspot_user_connect`
  - `hubspot_user_connections` (lists connected portals, never shows a token)
  - `call_hubspot_as_user`, which can reach only `/automation/email-templates/` and `/automation/sequences/` and never falls back to the QBS token
- Review fixes:
  - Percent-encoded dots such as `%2e%2e` are refused, because `fetch` turns them into real `..` and could leave the allowed paths.
  - The "enabled" switch on the app and on its credential is now checked on every connect and call.
- Migration `20261130294500_hubspot_user_app.sql` adds a nullable `portal_id` column to `qbs_oauth_states` and the registry row.
- Key files: `supabase/functions/_shared/hubspot-user-token.ts`, `supabase/functions/_shared/hubspot-user-tools.ts`, `supabase/functions/manage-credentials/index.ts`, `src/test/hubspot-user-credential.test.ts`.

### #638: packages (branch `claude/package-user-assets`, stacked on #637)

Retarget it to `main` after #637 merges.

- The library's 60 `email_template` and 23 `sequence` assets are only names from an inventory spreadsheet ("Not API-verifiable"). They have no bodies and no steps, so nothing could be deployed from them.
- Three tools in `supabase/functions/_shared/package-user-assets.ts`. `deploy_package` is **untouched**.
  - `capture_package_user_assets` reads real templates and sequences by name from a connected source portal into the package. It does a dry run first.
  - `deploy_package_user_assets` creates the templates, then the sequences, repointing each step at the template just created in the target.
    - It is a dry run unless confirmed.
    - It uses the same readiness gate as `deploy_package`.
    - It skips anything already there by name, so it is idempotent, and it reads every item back.
    - It records the run in the new `qbs_user_asset_runs` table.
  - `rollback_package_user_assets` deletes only the sequences that run created. HubSpot has no delete API for templates, so those are listed for a person to remove.
- Nothing is ever enrolled, so nothing sends.
- Review fixes:
  - A network error mid-deploy no longer loses the run record.
  - The create request always sends the top-level `dynamic` boolean.
  - A sequence answered as `{sequence: {...}}` is read either way.
- Migration `20261130295500_user_asset_runs.sql` adds one table.
- Tests: `src/test/package-user-assets.test.ts` (30 tests, against an in-memory fake HubSpot).

## Status at last look

- All 30 package tests pass, and so do the credential tests.
- CI was green on the earlier heads, and all review threads are resolved. The CI and Vercel review for the newest #638 head (`a33633b3`) were still running at last look.
- **Merging is the user's call.** Merging #637 triggers the Deploy Supabase backend Action. The migrations must ship only through that Action, never applied directly to the database.
- A follow-up check-in was scheduled for about 14:28 UTC on 2026-11-24.

## Not verified

- **No live run yet.** Nothing has run against a real HubSpot, because the app wasn't set up when this was written.
- Whether user-level access lets us **read** sequence definitions (capture needs that). HubSpot says "manage sequence definitions" is supported but some read endpoints aren't.
- Whether the sequences list endpoint returns the same paged `results` shape as the templates list.
- The exact create-sequence response shape (`id` versus `sequence.id`). The code handles both.
- Whether a user can edit templates owned by another user.

## What the user needs to do

1. Create a **user-level, private + OAuth** developer-platform app. It needs:
   - the redirect URL `https://clientcommand.thequantumleap.business/settings/oauth/callback`
   - the six scopes above, including the template scopes, since sequence steps point at templates
   - Q Squared and each client account on its allowlist
   - The user says they built an app "just for sequences", so its scopes must be checked.
2. After the PRs merge and deploy, save the app's Client ID and secret in Settings → Internal Services → "HubSpot (user-level app)". The secret should never go in chat.
3. Connect Q Squared and run the first read and edit there. The person approving needs a paid Sales Hub or Service Hub seat.

## Constraints that still apply

- Prove everything only on **Q Squared Demo (HubSpot 47404459)**.
- Never touch the live Quantum portal, 20682069.
- Always pass `allow_global_fallback:false` on `call_hubspot_as_client`, because it silently falls back to the live QBS token otherwise.

## For the Outbound Email master list

The earlier change-log entry for that panel says HubSpot's Templates API could show email wording as the next step. `call_hubspot_as_user` would serve that once a portal is connected.

## Reference

- HubSpot docs: email templates `https://developers.hubspot.com/docs/api-reference/latest/automation/email-templates/guide`, sequences `https://developers.hubspot.com/docs/api-reference/latest/automation/sequences/guide`, user-level apps `https://developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/user-level-apps`.
- HubSpot says a private-distribution OAuth app can be installed in multiple accounts via an allowlist set in the project settings. An earlier statement in the session that private apps are single-account was wrong.
- Paths are versioned `2026-09`: `/automation/email-templates/2026-09/` and `/automation/sequences/2026-09/serviceaccounts/sequences`.
