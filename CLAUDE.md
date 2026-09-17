# Working rules

Keep this file short. It is re-sent on every turn.

## Big documents (ClientCommand pages, proposals, HTML)

`set_web_proposal_custom_html` and `create_web_proposal` replace the **whole**
document. A one-word change costs a full retype (~50k tokens for a real page).
So:

1. **The repo is canonical.** Page source lives in `pages/<slug>.html`. Edit it
   there with `sed`/`python`, not by retyping.
2. **Prefer `customHtmlUrl` / `html_url`.** Both tools accept a URL and fetch
   server-side. Commit the file, push, pass the raw URL. ~100 tokens instead of
   50,000. Only inline the document when no fetchable URL exists.
3. **One push per review round.** Batch every pending edit. Never push just to
   look at something — check locally first.
4. **Say the cost before a full inline push** ("this is a ~50k-token rewrite")
   and let me decide if it is worth it.
5. **Never read a document back to verify.** `get_web_proposal` returns the
   entire HTML. Use `list_web_proposals` for state, or trust the write result.

## General

- Don't ask for data twice. If I pasted it, it is in context; if it is in a
  file, grep the file.
- Read parts of files (`sed -n`, `grep -n`), not whole files, unless the whole
  file is genuinely needed.
- Don't echo large content back to me to show it worked. Say what changed.
- Long jobs: work locally, report once at the end, not step by step.

## Context

- QBS HubSpot portal: `20682069`
- Client portals always use a PAT (see `qbs-hubspot-private-app`), never the
  OAuth MCP — that connector is bound to 20682069.
- Develop on the branch named in the session prompt. Commit; never push to
  another branch without being asked.
