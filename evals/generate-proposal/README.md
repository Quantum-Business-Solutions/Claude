# generate-proposal eval

Compares two Claude models as drafters for QBS's `generate_proposal` capability
(ClientCommand MCP tool: "Generate a full AI-drafted proposal from a discovery
session, transcripts, and HubSpot context.") on 25 real client inputs, judged
blind, pairwise, by a third model.

## Design

- **Inputs**: 25 real ClientCommand portals (`inputs.json` — IDs only, no
  client names/contacts/content in git). Selected from the 49 active portals
  by filtering to ones with recent, substantive meeting history
  (`list_meetings(has_summary=true)`, most recent ~100 records as of
  2026-09-17), which gives each input enough real context (account history,
  stated priorities, deal signals) to draft a proposal from — most QBS
  proposals in this DB are expansion/upsell proposals for existing accounts,
  not cold discovery calls, so this mirrors real usage.
- **Task**: for each portal, assemble a `generate_proposal`-shaped input
  (`clientCompany`, `clientName`/`clientEmail` from the portal record,
  `transcriptSnippets` from recent meetings, `hubspotContext` from the
  client's HubSpot deals/company record) fetched live from ClientCommand —
  never persisted to git.
- **Candidates**: the same assembled input is drafted twice, once by
  `claude-opus-4-7`, once by `claude-sonnet-5`, with an identical system
  prompt (see `prompt.md`).
- **Judge**: `claude-opus-5`, blind pairwise. Each trial presents both drafts
  labeled A/B in randomized order (label→model mapping kept out of the judge
  prompt and only decoded after scoring) and asks for a winner + rationale
  against the rubric in `rubric.md`.
- **Output**: per-trial verdicts + rationale, aggregate win rate, written to
  `results/` (gitignored — may quote real client content via the judge's
  rationale).

## Status

Scaffold + input manifest only. Generation and judging have **not been run**.

Blocker: this sandbox has no `ANTHROPIC_API_KEY` / `ant` profile, so
`run_eval.py` cannot call `claude-opus-4-7` / `claude-sonnet-5` /
`claude-opus-5` directly yet. See `run_eval.py` header for what it needs to
proceed.

## Files

- `inputs.json` — the 25 portal IDs (IDs only).
- `prompt.md` — the shared generation system prompt given to both candidate
  models.
- `rubric.md` — the judge's scoring rubric.
- `fetch_inputs.py` — run inside a Claude Code session with the
  `Client_Command_-_NEW` MCP tools available; resolves each portal ID to a
  real `generate_proposal` input and writes it to `.cache/` (gitignored).
- `run_eval.py` — standalone script; reads `.cache/`, calls the Anthropic API
  for both candidates plus the judge, writes `results/`.
