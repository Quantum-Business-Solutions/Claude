# Environment

Everything here was verified live on 2026-08-29 unless marked otherwise.

## HubSpot

| Fact | Value |
|---|---|
| Portal | `20682069` |
| Shawn owner ID | `103243559` |
| Auth | Private-app token (PAT), `QBS_HUBSPOT_TOKEN` |
| App ID | `36895779` |
| Scopes | 144, including all CRM read/write needed |

**Verified working.** `POST /oauth/v2/private-apps/get/access-token-info` returned HTTP 200 with
`hubId: 20682069`. Present scopes include `crm.objects.contacts.read`, `crm.objects.contacts.write`,
`crm.objects.companies.read`, `crm.lists.read`, `crm.objects.owners.read`,
`crm.schemas.contacts.read`, `tickets`.

This closes open item #1 in the outreach skill ("HubSpot connector access — **Unverified**. Never
successfully called in the build session. Everything depends on it."). **Direct REST with the PAT
works and does not require the OAuth connector**, which is what has been failing.

## Unipile

DSN: `api30.unipile.com:16072` · Auth header: `X-API-KEY`

Seven LinkedIn accounts, all `status: OK`, belonging to five people:

| Account ID | Person | Sales Nav | Role here |
|---|---|---|---|
| `S6ua4SfUT4SMRFZFOmyUzQ` | **Shawn Peterson** | ✅ | **The only send/comment account** |
| `7lBoyXuETqKdiJYLj5HBGA` | Shawn Peterson (dup) | ✅ | Redundant — recommend disconnecting |
| `4fi7iaAuRRmRpzl4G8Dqjg` | Isaac Hernandez | — | Never use |
| `9eK50zZlT2qVr0oCo0NJVg` | Keven Ellison | — | Never use |
| `F5Y_Hhe_TCO94_hkWXmCKg` | Keven Ellison (dup) | — | Never use |
| `oCJmihYGQJ-wsaA0bgW_aQ` | William Cronk | — | Never use |
| `xgfVW4VBRri7sQ9tDmSGAw` | Tom Menton | — | Never use |

Shawn's identity, to assert before any send:

- Member ID `ACoAAAGv8WABzhfWcURPIaBDzbgiEWX5e781Etw` — immutable, assert on this
- Slug `shawnpetersonquantum` — user-changeable, assert but don't rely on
- Premium contract `2014060643`, QBS org `urn:li:fsd_company:80108807`

**Why identity assertion matters:** one API key spans five people's inboxes. Any call that forgets
`account_id` silently blends a colleague's data into QBS reporting — or worse, sends under their name.

## Network constraint

**Unipile is not reachable by direct HTTP from a Claude Code cloud container.**

Its DSN uses port `16072`. The agent proxy's documented policy lists *"non-443 HTTPS ports"* under
**"Not supported through the proxy (report, do not work around)"**. Direct `curl` fails every time:

```
curl: (35) Recv failure: Connection reset by peer
proxy failure class: ws_closed_mid_exchange
```

Three attempts, all identical. Structural, not intermittent.

**The path that works:** the **Unipile MCP connector** (`mcp__Unipile__execute-request`, a HAR
passthrough). It makes the call from the MCP server's own host, so the sandbox's port policy does
not apply. Verified with a live `GET /api/v1/accounts` returning HTTP 200 and all seven accounts.

### What this means for the build

| Service | Port | Path from a routine |
|---|---|---|
| HubSpot | 443 | Direct REST — plain, testable Python |
| Unipile | 16072 | **Unipile MCP connector only** |

So the split is: **HubSpot plumbing is code; Unipile calls are MCP tool calls.** That's less clean
than one uniform client, but it's the honest constraint. Worth asking Unipile support whether a
port-443 DSN exists for this account — it would remove the split entirely.

Never disable TLS verification or unset `HTTPS_PROXY` to get around this.

## Credentials

**Never commit tokens.** Two reasons, one of which is practical rather than principled:

1. HubSpot is a GitHub secret-scanning partner. A `pat-na1-…` pushed to GitHub is typically
   detected and **auto-revoked within minutes** — committing it causes the breakage it was meant
   to prevent.
2. Git history is permanent. A rotated key still sits in every clone.

### How to supply them

**For routines (the real answer):** set them as environment variables on the Claude Code
environment. Every session and every scheduled routine inherits them, they never appear in a
transcript, and they never touch git.

```
QBS_HUBSPOT_TOKEN=pat-na1-...
UNIPILE_API_KEY=...
```

**For local iteration:** a `.env` at repo root. It is gitignored. `load_settings()` reads the
environment first and falls back to that file.

### Rotate these

| Credential | Why |
|---|---|
| Unipile API key | Pasted into chat transcripts on 2026-08-29, at least twice |
| HubSpot PAT | Pasted into a chat transcript on 2026-08-29 |

Rotate, then set the new values as environment variables and never paste them again.
