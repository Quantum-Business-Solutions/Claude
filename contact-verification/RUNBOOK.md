# QBS list verification — operator runbook

Run the LinkedIn-dated-history verification loop against **any** HubSpot contact list so reps never
dial a stale employer. Nothing here is specific to list 3675; substitute `<LIST>` throughout.

The authority on judgment calls is `skill/qbs-list-verification/SKILL.md`. This file is the mechanics.

---

## 0. Setup (once per session)

```bash
export TOKEN=<hubspot-private-app-token>      # never commit; rotate if it ever appears in chat
export DATE=$(date -u +%Y-%m-%d)              # stamped into every evidence string
export RUN=/tmp/.../scratchpad/run<LIST>      # scratch dir — NEVER git-committed (contact PII)
mkdir -p "$RUN" && cd "$RUN"
```

Unipile LinkedIn reads use **only Shawn's two accounts** (`S6ua4SfUT4SMRFZFOmyUzQ`,
`7lBoyXuETqKdiJYLj5HBGA`). The other identities on the Unipile tenant are **client** accounts —
using one would read LinkedIn as a client. Never.

**Run data stays in `$RUN`.** Verdict logs and mover files contain names, titles and employers of
real people; only code and docs go to git.

---

## 1. Phase 0 — preflight (no writes)

```bash
# a. self-test: prove your query types return known-good answers before trusting any null
# b. map the FULL gate chain (this is the step that prevents a false "we broke the list" panic)
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.hubapi.com/crm/v3/lists/<LIST>?includeFilters=true" > list_<LIST>.json
```

Walk `filterBranch` **recursively** and record all four filter kinds — a parser that only reads
`property` misses the ones that decide membership:

| kind | meaning |
|---|---|
| `filterType: PROPERTY` | contact field (`hs_lead_status`, `phone IS_KNOWN`, …) |
| `filterType: IN_LIST` + `listId` | **upstream list the contact must ALSO be in — recurse into it** |
| `filterBranchType: ASSOCIATION` (`0-2`, assocType `279`) | condition on the associated **company** |
| nested OR-of-AND | contact needs only ONE branch to pass |

Save to `list_anatomy_<LIST>.json`. Then snapshot intake membership to `mem_<LIST>.txt` and treat it
as immutable — measure **progress** against live membership, **coverage** against the snapshot.

Abort if: the list is static or not a contact list (`objectTypeId 0-1`); or any list you write into
filters on a prose property you write.

---

## 2. The batch loop (write after every batch — reps dial while it runs)

```bash
python3 scripts/queue.py <LIST> 12        # next 12 unverified + LinkedIn identifier
```

For each: read the profile via Unipile (`linkedin_sections=experience_preview`), then judge from the
**dated history**, never the HubSpot title string.

Escalation ladder when the stored slug fails:

1. **422 / locked** → LinkedIn people-search on `name + company`.
2. **Wrong-linked** (linked profile's company ≠ HubSpot company — closer to 1 in 4 on recent
   batches) → people-search, and accept a hit **only with an independent corroborator**: location =
   company HQ region, industry, or role. Corroborated → judge on that profile *and* write the
   corrected slug back via `li_url`. Free pre-filter: if the stored slug's surname differs from the
   contact's, it is mis-linked on its face — don't spend the read.
2b. **Before judging `no`, check the org chart.** A move into the parent/holding company, or into a
   sibling brand of the CRM company, is `yes` with a corrected title — not a mover. Same for a
   spinoff or rebrand: same operating business, stale company name.
2c. **A "Retired" headline beats an un-ended role row.** Four such contacts on the last pass would
   have stayed dialable on dated history alone.
3. **No URL at all** → people-search; still nothing → `unreadable`, naming every source tried.
4. ZoomInfo `enrich_contacts` as a corroborator only (see SKILL.md guardrails: FULL_MATCH +
   accuracy ≥ 85; `COMPANY_ONLY_MATCH` writes nothing; DNC-flagged numbers are never written).

```bash
python3 scripts/writeverdicts.py <LIST> b<LIST>_runN.json
```

Batch item: `{id, verdict, ev}` + optional `ls`, `newco`, `sources`, `title` → `ai__job_title`,
`li_url` → both URL fields, `changed` → explicit "what changed in HubSpot".

The script enforces the rules you must not bypass: no `hs_lead_status` on a `yes`; only the four
lead-status literals; never native `jobtitle`; evidence stamped
`Verified - <date> - <evidence> - Changed: <what changed>`; read-back confirmation; movers queued.

---

## 3. Mover pipeline (after ~10 movers accumulate)

```bash
# a. verify each destination domain — FULL_MATCH + a corroborator, via ZoomInfo enrich_companies
#    The company name match needs its OWN corroborator (HQ city/state, or industry vs the person's
#    career). A bare-name FULL_MATCH has returned an entirely unrelated business in another country
#    more than once. Watch near-homograph destinations — one transposed letter
#    attaches the contact to the wrong employer and the evidence still reads plausibly.
# b. build movers.json: {id, newco, domain?, dm, title, ev}
python3 scripts/movepipe.py <LIST> movers.json
```

`dm` (is this person a decision-maker at the NEW company?) drives lead status:
`true` → `ConnectandSell Prospect`, `false` → `Not Decision Maker`. Ambiguous → `false` + flag.

**Then close the ICP loop.** New companies have none of the ICP fields the calling list gates on, so
pull `employeeCountByDepartment` and write the band to `icp_queue_<LIST>.json`. Do **not** auto-write
ICP fields — they redefine list membership. Most movers legitimately leave the ICP (on 3675 only 1 of
7 new companies was in the 50-99 sales band); route them from the Moved-Companies list, don't loosen
the ICP.

---

## 4. Outputs + honest reporting

Two dynamic lists via `scripts/twolists.py` / `listb.py`: **Moved Companies** (evidence CONTAINS
`RE-ASSOCIATED`) and **No Primary Associated Company** (`number_of_associated_companies = 0`).

Report, every run:

- members (taken **twice, minutes apart** — dynamic lists recalculate asynchronously and a
  mid-recalculation count is meaningless)
- verified-yes / no / unreadable
- **intended removals** (lead status set) vs **unintended** — never one number
- unreadable still dialable, no-LinkedIn-URL, wrong-linked-slug counts
- **succession conflicts**: scan the run's `yes` set for two contacts claiming the same top seat at
  the same company. Keep both verdicts, annotate the older profile's evidence, name it in the report.
- read-back shortfall: contacts stamped earlier in the run can be deleted/merged before the report —
  say so rather than quoting the verdict-log length as if it were live membership.

### When the owner asks "why did my list drop?"

Run the attribution, in this order. Never answer by assertion.

1. Pull current membership.
2. Intersect with the verdict log → verified-`yes` contacts that fell off.
3. Read their `hs_lead_status`, phone fields, `number_of_associated_companies` → rules the process in or out.
4. Test them against **each** upstream `IN_LIST` gate separately.
5. Only then the ASSOCIATION (company) filters.

On 3675 this showed 389 intended removals, plus 487 good CEOs lost to an upstream gate — of which
**zero** had been touched by the pipeline (they fail `hs_persona = persona_1`, a field this process
is forbidden to write). Watch for that persona gate: it is usually the biggest recoverable pool.

---

## 5. Cadence

A dynamic calling list is never "done" — it keeps admitting members from its own criteria (263 new on
3675 within hours of a full pass). Re-run weekly on an active list, scoping to members with **no**
`ai__li_still_at_company` **or** `ai__contact_verified_date` older than 90 days.

## Guardrails that halt the run

Any 401/403 (an auth failure reads as "no data" and would stamp live records) · `no` share >60% or
<5% over the first 50 verdicts (baseline ~36%) · unreadable >20% (baseline ~8%) · 5 consecutive
identity failures · live membership drift >10% mid-run · any per-run ceiling exceeded (companies
created, associations deleted, emails/phones cleared, personas changed — default 0, enrichment credits).
