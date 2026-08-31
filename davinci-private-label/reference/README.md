# reference/

Machine-read state of the Praxera migration. Every file here is written by a
`tools/verify_*.py` script from the live HubSpot portal, and every number in the
ledger is generated from these files rather than typed. Regenerate in order:

    python3 tools/verify_state.py      -> current_state.json
    python3 tools/verify_embeds.py     -> form_embeds.json
    python3 tools/verify_workflows.py  -> workflow_clones.json
    python3 tools/verify_emails.py     -> email_clones.json
    python3 tools/verify_content.py    -> page_health.json, blog_health.json
    python3 tools/build_pairs.py       -> pairs.json
    python3 tools/build_ledger.py      -> deliverables/*.html

The verify scripts read `/tmp/hs.py` for the portal token, which is not in the
repo. Two things they all do that are easy to get wrong:

  * They read the **draft**, not the base record. Every change in this migration
    was made to a draft, so the list endpoints and the base records still show
    the site as it was before any of it.
  * They separate copy, links and hosting. A brand name in an image filename is
    not a page that says DaVinci, and conflating the two is what produced the
    "105 broken emails" figure that turned out to be 0.
