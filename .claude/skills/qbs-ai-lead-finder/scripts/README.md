# Pipeline scripts

Reference implementations from the UBEO production run. Each expects `PAT` in
the environment and writes intermediate JSON to the working directory.

## Run order

```
harvest_pool.py    →  qa_gates.py harvest
extract_signals.py →  qa_gates.py extract     ← READ THE OUTPUT HERE
<write>            →  qa_gates.py write
company_rollup.py  →  qa_gates.py rollup
```

## The gates are not optional

`qa_gates.py` exits non-zero on failure so a gate cannot be skipped by accident.
Every check corresponds to a bug that shipped wrong data — see
`../references/failure-modes.md`.

On its first run against real output, the extract gate immediately caught a live
defect: 23% of signals landing on Jan 1 because two derivation paths defaulted
the month instead of pinning it. That is what these are for.

**Gate 2 prints records and tells you to read them.** Do that. Every precision
bug in the first production run was caught by reading output; none by aggregate
statistics.

## Usage

```bash
python3 qa_gates.py harvest --pool pool.json --ledger done.json \
        --terms terms.json --fields hs_task_body,hs_task_subject \
        --per-term per_term_counts.json

python3 qa_gates.py extract --signals signals.json --pool pool.json

PAT=... python3 qa_gates.py write --signals signals.json \
        --obj tasks --prop ai__lease_information

python3 qa_gates.py rollup --signals signals.json --assoc assoc.json \
        --companies companies.json --kept-existing 1906
```

## Per-client adaptation

`TERMS`, the object list, and the `EXCLUDE` lifecycle set change per client.
Treat these as a starting point, not a turnkey job — the classification patterns
need a read-through against each dealer's own note-writing conventions before a
portal-wide write.
