# QBS LinkedIn Program — Documentation

Rebuilding the QBS LinkedIn GTM automation as Claude Code Routines.

| Doc | What's in it |
|---|---|
| [system-overview.md](system-overview.md) | What the program does, the five tasks, how they chain |
| [environment.md](environment.md) | Verified accounts, portal facts, credentials, the network constraint |
| [known-issues.md](known-issues.md) | What's broken, contradictions between source docs, open blockers |
| [architecture.md](architecture.md) | Target design on Claude Code Routines |

## Status at a glance — 2026-08-29

| Component | State |
|---|---|
| `qbs-linkedin-watch-sync` | 🔨 Rebuilt as `scripts/watch_sync.py` + routine; blocked on connector grant |
| `qbs-linkedin-engage-am` | 🛑 Blocked daily on a watch list that has never existed |
| `qbs-linkedin-engage` (pm) | 🛑 Same |
| `qbs-linkedin-daily` (outreach) | ⚠️ Sending, but ~90% below baseline and unlogged since 2026-06-01 |
| `qbs-linkedin-weekly-digest` | ✅ Works; was reading a bad data source, now repointed at Unipile |

## Verified this session

- **HubSpot PAT works.** Portal `20682069`, 144 scopes, all CRM scopes present. Resolves the
  longest-standing open item ("HubSpot connector access — unverified, everything depends on it").
- **Unipile works via MCP, not via curl.** See [environment.md](environment.md#network-constraint).
- **Both Shawn accounts have Sales Navigator.** Settles a direct contradiction between two
  source documents. See [known-issues.md](known-issues.md#resolved-contradictions).

## Source documents this consolidates

1. `qbs-linkedin-engage-am` skill (fileless rewrite, 2026-08-29)
2. `qbs-linkedin-daily` skill v2026-08-29 (outreach runbook v3 + crash-safety fixes)
3. QBS LinkedIn Weekly Digest, week of 2026-08-24
4. `qbs-linkedin-watch-sync` task audit, 2026-08-29

Where they disagree, [known-issues.md](known-issues.md) records which one live data supports.
