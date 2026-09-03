# Quantum Business Solutions — Claude working rules

This repo is QBS's Claude Code workspace. Each top-level folder is one client engagement or
internal project (for example `davinci-private-label/`, `contact-verification/`). Work in the
folder for the project at hand; a folder's own `CLAUDE.md` adds the project-specific rules and
overrides nothing here. Team voices: Shawn (CEO), Patrick, Marko, Barb — all @thequantumleap.business.

## Non-negotiables
- **Never commit a secret.** No PATs, API keys, or tokens in code, docs, commit messages, or
  this file. Take them from the chat or environment, and remind the user to rotate a token
  that was pasted in chat when the work wraps.
- **Nothing client-facing goes live without the client's sign-off.** Drafts, staging, and
  unpublished content are fine. Publishing, sending, or DNS/domain changes need an explicit
  go from the user, each time.
- **Confirm the target before you write.** Check portal ID, domain, list, or project first.
  For HubSpot, never use ClientCommand's `call_hubspot_as_client` unless the client has a
  stored credential — it silently falls back to QBS's own portal (20682069).
- **Re-read immediately before writing a prepared change.** Someone may have edited by hand
  since your last read. Back up the before-state of anything you modify in a `backups/` folder.
- **Scope is the user's call.** Do exactly what was asked; list anything else you noticed as a
  finding, don't act on it.

## Memory
- **Hindsight (MCP, bank `QBS`) is the shared long-term memory.** At the start of client work,
  `recall` the client and project. When a session produces decisions, gotchas, or client
  facts, `retain` them with client and project tags. If retain fails on credits, save the text
  in the project's `deliverables/` folder so it can be pushed later.
- This file holds standing rules only. Facts about what happened belong in Hindsight and in
  the project folder's deliverables.

## How to work here
- Keep a running human-readable record in the project folder: `deliverables/` for anything
  the client or team reads, `tools/` for scripts, `backups/` for before-states.
- Verify claims against the live system before stating them; when an earlier statement turns
  out wrong, say so plainly and correct the record.
- Reports to the user: lead with the outcome, plain language, tables for numbers, no jargon
  the client couldn't follow.
- Commit as you go with descriptive messages; push to the session's designated branch.
  Never push to `main` or another branch without being asked.
