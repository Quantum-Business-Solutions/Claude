# Copier Dealer Census — pipeline, recipes, and research record

Proprietary vertical market intelligence on the US copier dealer channel, built in
HubSpot portal **20682069**.

The goal, in Shawn's words: *"the perfect database of copier companies in the United
States... the right two to three contacts per company, but have it validated."* And the
cadence goal: *"a streamlined way where you're doing this once every thirty or sixty days
... I don't have to feel like every quarter I'm putting another ten hours into this."*

Everything here exists so the next cycle does not restart from zero. The container this
was built in is ephemeral; this directory is the part that survives.

---

## State at end of wave 2 (2026-08-18)

**Legitimate dealer target universe: 717** — after excluding 94 retired brands (they belong
to their acquirer, not the census), 78 non-US, 51 client accounts on hold, 15 not-dealers
and 7 defunct.

| | dealers | |
|---|---|---|
| 1+ reachable decision-maker | 607 | 84.7% |
| Meeting the 2+ goal | 358 | 49.9% |
| Nothing at all on file | 16 | 2.2% |

**Verification is the weak half.** 1,164 dealer contacts carry `validated = Yes`, but only
**376** were set by this project with written evidence in `ai__contact_evidence`. **651 are
inherited flags with no evidence recorded at all** — they look verified, so nobody
re-checks them, which makes them the most dangerous records in the census. Re-verifying
that block is the highest-value verification work outstanding.

## Why dealers lack a reachable decision-maker

244 dealers show none. Only **36** are a genuine sourcing failure:

| Cause | Count |
|---|---|
| Brand retired — the DM works at the acquirer; fixed by consolidation, not sourcing | 62 |
| Not a real target (25 non-US, 15 not-a-dealer, 6 defunct) | 46 |
| Unverified / domain-suspect — classify before sourcing | 38 |
| Trading under an acquirer | 37 |
| **Already covered, hidden by duplicate company records** | 18 |
| Client hold | 6 |
| **Genuinely unreachable** | **36** |

Of the 54 independent dealers in that set, 50 share one problem: we know exactly who the
decision-maker is and have no working email. Not obscure shops — Prosource ($20–50M, 4 DMs),
Cannon IV, JD Young (13 contacts), So Cal (6 DMs). **We have the humans; we're missing
addresses.** That is why email verification beats another sourcing wave.

---

## Layout

    scripts/       the pipeline, in run order
    recipes/       the reusable research methods (start here)
    analysis/      decision-bearing outputs and worklists
    agent-output/  the raw research record from the 9 wave-2 agents

### Run order

```bash
export TOKEN='<hubspot private app token>'     # never hardcode; all scripts read $TOKEN

python3 scripts/pull_for_xlsx.py               # live pull -> xlsx_data.json
python3 scripts/build_xlsx.py                  # -> COPIER_DEALER_CONTACTS.xlsx (7 tabs)
python3 scripts/consolidate.py                 # DRY RUN by default; --write to apply
python3 scripts/promote.py                      # status promotion, with the opt-out guard
```

`consolidate.py` is the one to read first — it carries the dedup guards and the
`validated = Yes` gate, and it prints a full dry-run triage before writing anything.

### Key scripts

| Script | What it does |
|---|---|
| `pull_for_xlsx.py` | Live pull of dealers + contacts. Nothing downstream reads a stale snapshot — an on-disk index went stale mid-session once and nearly caused duplicate creations. |
| `build_xlsx.py` | Builds the 7-tab workbook. Writes **both** a live formula (col B) and a value-at-build (col C). |
| `consolidate.py` | Folds agent output into HubSpot: 3 dedup guards, the validated gate, email routing, per-record fallback. |
| `promote.py` | Promotes reachable DMs to `ConnectandSell Prospect`, with the Do-Not-Call history guard. |
| `mx_sweep.py` / MX logic | Deliverability. Distinguishes forwards-to-acquirer from dead domains. |
| `phone_dupes.py` | Duplicate detection on shared phone across different clusters. |
| `merge_lossless.py` / `merge_approved.py` | Company merges. Re-resolves the survivor ID before each merge because **IDs shift on every merge**. |

---

## Hard-won rules — read before touching the portal

**Batch writes are all-or-nothing.** One unique-value conflict rejects the whole batch (we
lost 83 of 83 creates that way once, and 100 of 149 updates another time). Pre-check both
unique properties live, then write per-record with a fallback.

**`associatedcompanyid` in a CREATE payload is accepted and silently ignored.** The
association must be a separate `PUT /crm/v4/objects/contacts/{id}/associations/companies/{coid}`,
verified through the v4 endpoint — the derived property lags by seconds and reading it back
looks like data loss.

**`associatedcompanyid` is single-valued.** A contact linked to several companies is
invisible to `associatedcompanyid EQ <cid>` for every company but its primary. Dedup by
that filter created three duplicate humans (Bill Northam's primary is Fyxit LLC, Kevin
Morris's is MPS Oklahoma). **Always resolve membership through the v4 associations endpoint.**

**A unique-property conflict is a duplicate-record detector.** Five verified emails failed
to write; chasing who held them exposed 18 dealers whose decision-maker was already
reachable on a second company record — three of them in Meeting Set status. Never just drop
the conflicting field.

**HubSpot search caps at 10,000 records** and fails silently. Paging "all contacts" returned
449 of 3,769 dealer contacts and looked plausible. Batch the company ids and use
`associatedcompanyid IN [40 ids]`.

**Three portal automations actively destroy data:**
1. A workflow **blanks `jobtitle` ~20 seconds** after `hs_lead_status` is set to
   `Retired - Remove from All Lists` or `No Longer with Company`. **8,067 contacts already
   affected.** Workaround: write `TITLE AT DEPARTURE:` into `ai__contact_evidence` *first*.
   `Incorrect Contact` and `Disqualified` are confirmed safe.
2. HubSpot Data Enrichment overwrites verified fields, including the LinkedIn identity key.
3. A workflow copies company phone → contact phone. **This one is deliberate** — HubSpot's
   auto-dialer can only call that line. Do not "fix" it.

**The Do Not Call one-way door.** Workflow `51045413` sets `hs_lead_status = 'Do Not Call - Opt Out'`
on everyone entering list `2627` (v3 listId `4127`), a dynamic list of **47,907** contacts
whose only criterion is `hs_lead_status HAS_EVER_BEEN_ANY_OF ['Do Not Call - Opt Out']`.
Because it matches on *has ever been*, membership is permanent and the workflow reinstates
the status — it cannot be cleared through the UI. 109 dealer decision-makers with working
emails are locked behind it; 131 of those flags were applied by automation in two same-day
batches (68 on 2024-01-23, 63 on 2024-08-07). The bounce workflows were checked and are
**not** the cause.

**`Not Interested` is labelled `Not Interested - Follow-up`** — a follow-up state, not a
do-not-contact. Read the option *label*, not just the value, before treating a status as
terminal. Guarding on both it and Do Not Call rejected 100% of promotion candidates, which
is how the difference surfaced.

**Property notes.** `copier_company` is a booleancheckbox storing `'true'` — filtering on
`"Yes"` returns zero silently. Date filters need epoch milliseconds, not `"2026-08-17"`.
`linkedin_profile_url__unique_value` matches by exact string; canonical form is
`https://linkedin.com/in/<slug>`, and a wrong identity in it **blocks the real executive
from ever being created**. Merging auto-populates `hs_additional_domains` with the loser's
domain — which is what makes the retired-brand design work with no manual step.

---

## Research method

`recipes/RECIPE.md` — the `dealer-people` recipe (LinkedIn company→people via Unipile).
`recipes/HARD_RECIPE.md` — the 9-source escalation for dealers that defeat LinkedIn.
`recipes/WAVE2_BRIEF.md` — the briefing given to all 9 wave-2 agents; reuse it verbatim.

**Source ranking, measured.** State and cooperative **contract vendor schedules** are the
single highest-yield source — Ricoh/Kyocera authorized-dealer lists attached to Iowa
cooperative, Washington DES, Ohio 800817, Indiana IDOA, Texas DIR, NY OGS contracts. They
publish owner name, title *and* direct email. One shard went from 0 to 40 reachable people
out of 52 largely on this source. **Put it ahead of LinkedIn for email discovery.** LinkedIn
remains first for *currency* — `work_experience` with `end: null` proves a current role.

**LinkedIn caveats.** Emails are exposed only for `DISTANCE_1` connections. The company
filter **leaks** — over 1,000 leaks were rejected across wave 1, consistently outnumbering
real finds; verify every hit against the profile's current employer. **Throttling returns an
empty item list with no error**, indistinguishable from "no employees" — use a canary query
and a 75s backoff. Use **no keyword filter** on people search: a keyword filter cost an
earlier wave at least 15 decision-makers, including a President whose headline contained
"President". `api: "sales_navigator"` returns 401 on this key; use `classic`.

**Firecrawl fabricates from 404 pages.** Its JSON extraction invented a plausible SumnerOne
leadership trio and literal "John Doe / Jane Smith" for another dealer. **Check `statusCode`
on every scrape.** Also: `web.archive.org` is egress-blocked from this container, so Wayback
(source #8) must not be counted as "checked".

**Never match a person on surname alone.** An earlier wave matched "Annabelle Young" to the
dealer "RJ Young" and surfaced what appears to be a minor.

**Always canary a DNS/MX sweep.** A portal-wide sweep first flagged 80 domains as unable to
receive mail — but `comcast.net` was among them, which is impossible. Re-probing serially
across three resolver sets showed **58 of 80 were false positives**; the truth was 22
domains / 29 addresses. A dead mail server says nothing about the phone, so nobody was
disqualified over it.

---

## The `validated = Yes` bar

Shawn's standard, verbatim: *"if we validate them, they better have the up to date
information and be with that company."* Both halves, evidenced.

The gate in `consolidate.py` does **not** re-derive every verdict — a first version did and
downgraded 81 of 156, including people named as President on their own dealer's live team
page, which is exactly the first-party proof the standard wants. It instead catches rows
whose *own evidence* betrays uncertainty: explicit hedges (`unverified`, `post-close status`,
`stale`, `likely`, `appears to`), historical markers (`at time of`, `former`, `retired`,
`role ended`), and titles that are really **procurement-document roles** ("Primary Contact")
rather than job titles. That version downgraded 21 of 156, each justified by its own text.

Sources that earn a `Yes`: LinkedIn current role (`end: null`), the dealer's own live
team/leadership page, a state SoS officer filing, a state/cooperative contract schedule
naming them with title, or press/trade coverage naming them in role.
Sources that do **not**: a pattern-guessed email, BBB, a ZoomInfo record with accuracy near
0, a chamber directory, a dealer-locator page.

**A pattern-inferred email is never `validated = Yes`** and never enters the `email` field.
It goes to `linkedin__email` with the anchor it was derived from, and into
`analysis/INFERRED_EMAILS_TO_VERIFY.csv` for a verification pass. In one shard this was the
difference between 40 "reachable" and 22 actually reachable.

**Email routing rule.** Business + no existing email → `email`. Business + existing → 
`email_other`. Personal (free-mail) → `linkedin__email` **only**, never the business field.
Unknown corporate domain → `linkedin__email` + review. Never overwrite a populated business
email.

---

## Standing constraints

- **Client accounts are never modified without explicit sign-off.** Shawn: *"I don't trust
  you enough if the company is a customer of ours."* 51 companies on hard hold.
- **Only Shawn's LinkedIn account** (`S6ua4SfUT4SMRFZFOmyUzQ`). Never the five belonging to
  other staff.
- **TruePeopleSearch and residential people-search sites are declined** — personal data,
  TCPA exposure, and the source class that produced false "deceased" verdicts.
- **Do not disable live portal workflows.** Identify them precisely; switching off automation
  in a live CRM affects everyone.
- Agents write **JSON only** — never directly to HubSpot. One consolidator does the dedup and
  the writes.

---

## Open decisions (blocking)

1. **Three acquirer duplicates** — Kelley Imaging `8293034857` (14 contacts; holds
   `copier_company` and `company_type` the survivor lacks, so the merge direction may need
   inverting), Konica Minolta Business Solutions U.S.A. `35396243578`, Flex Technology Group
   `35410839431` (domain stored as `www.flextg.com`). These block the retired-brand
   consolidation of 97 dealers, 24 of which collapse into one Xerox parent.
2. **Canada / non-US** — 86 records (64 Canadian). Verdict stamped `non_us`;
   `copier_company` deliberately untouched. Segment or remove? 92 Canadian contacts are
   currently dialable.
3. **The 109 Do-Not-Call-locked decision-makers** — were the two 2024 batch events a
   legitimate compliance scrub, or over-broad automation?
4. **18 duplicate company records** hiding coverage (`analysis/split_confirmed.json`), plus
   15 phone-duplicate pairs with 111 contacts split.
5. **13 acquirer corporate executives** — create them on the *acquirer's* record?
6. **Four manufacturer-owned Kyocera branches** (Mid Atlantic, New England, N. California,
   Southeast, Northwest) — direct operations, not independent dealers. Scope call; no
   classification was invented for them.
7. **Email verification key** (NeverBounce fits — `neverbouncevalidationresult` already
   exists on the contact object) to clear the 98 staged inferred addresses.
8. **Rotate all four credentials** pasted in chat during these sessions.

## Next wave

`analysis/wave3_targets.json` — 54 independent dealers with a named decision-maker and no
email, each carrying the sources already tried so wave 3 does not repeat work. 51 of the 54
were touched in wave 2 with `company_site` / `linkedin` / `firecrawl_search`; **state
contract vendor schedules are largely untried on them**, and that is the proven source.
