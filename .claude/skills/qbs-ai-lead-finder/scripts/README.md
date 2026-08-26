# Pipeline scripts

Reference implementations from the UBEO run (portal 516382). Each expects
`PAT` in the environment and writes intermediate JSON to the working directory.

| Script | Purpose |
|---|---|
| `harvest_pool.py` | Union the keyword set across text properties, dedupe by record ID |
| `extract_signals.py` | Apply the three date sources, classify flags, dedupe statements |
| `company_rollup.py` | Resolve associations, gate on lifecycle, rank, build company values |

Run order: harvest → extract → rollup. Adjust `TERMS`, the object list, and the
`EXCLUDE` lifecycle set per client. Treat these as a starting point, not a
turnkey job — the classification patterns need a read-through against each
dealer's own note-writing conventions before a portal-wide write.
