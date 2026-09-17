# Fetch step (Phase 1)

`run_eval.py` needs one real `generate_proposal`-shaped input per portal ID
in `inputs.json`, cached at `.cache/<portal_id>.json`. This can only be done
from inside a Claude Code session that has the `Client_Command_-_NEW` MCP
tools loaded — there is no standalone REST credential for ClientCommand in
this repo, by design (that's what keeps client data out of git).

For each `portal_id` in `inputs.json`:

1. `get_portal(portal_id)` → company name, contact, recent tickets/KPIs.
2. `list_meetings(portal_id=portal_id, since="2020-01-01", has_summary=true, limit=10)`
   → pull the 3-5 most recent entries' `content` excerpts as
   `transcriptSnippets`.
3. `hubspot_search(portal_id=portal_id, object_type="deals", filters=[], reason="generate-proposal eval input assembly")`
   (and/or `list_hubspot_deals(search=<company name>)`) → deal stage/amount
   as `hubspotContext`, if any exist for this client.
4. Assemble and write to `.cache/<portal_id>.json`:

```json
{
  "clientCompany": "<from get_portal>",
  "clientName": "<from get_portal, if present>",
  "clientEmail": "<from get_portal, if present>",
  "transcriptSnippets": ["<excerpt 1>", "<excerpt 2>", "..."],
  "hubspotContext": { "...": "..." }
}
```

5. Skip (log, don't fabricate) any portal whose meetings/HubSpot data turn
   out too thin to ground a real proposal — note it in `SELECTION-NOTES.md`
   and treat the eval as N<25 for that run rather than padding the input.

`.cache/` and `results/` are gitignored — this step and `run_eval.py` both
write real client content locally only.
