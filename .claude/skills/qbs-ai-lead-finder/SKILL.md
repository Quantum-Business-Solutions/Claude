---
name: qbs-ai-lead-finder
description: Mine a copier/office-equipment dealer's HubSpot engagement history for competitive lease intelligence — when a prospect's current lease ends, who their incumbent provider is, and the evidence behind both — then write structured findings onto engagement and company records. Use whenever a copier dealer, MPS provider, or office-technology client wants their CRM history turned into a prioritized outreach list. Trigger on "AI lead finder", "lease end dates", "competitive lease intel", "who are they with", "mine our call notes for leases", "lease expiration mining", "find prospects whose lease is ending", or any request to extract contract/lease timing from unstructured CRM activity. Requires a client HubSpot PAT (see qbs-hubspot-private-app).
---

# QBS AI Lead Finder

Turns a dealer's unstructured CRM history into a dated, evidence-backed list of
prospects whose competitive lease is ending.

The premise: reps capture lease intelligence for years but write it into free
text rather than a structured field — TCO-tab adoption at these dealers runs
5–15%. The intel exists and is unreachable by any filter or report. This
process makes it reachable.

**Read `references/failure-modes.md` before writing any harvest code.** Nine
distinct bugs produced wrong output during the first production run. Every one
is silent — no error, no exception, just quietly wrong numbers. They are the
reason this skill is long.

---

## Non-negotiables

**A keyword match is not a finding.** True yield off a keyword pool runs ~1–3%.
Nothing is written until it survives extraction, classification, dedup, and the
gates.

**No computed date goes into a structured date property until the client vets
it.** Text evidence fields are inert — nothing automates off them. Date fields
drive views, workflows, and rep queues. Write text first, always. Dates only
after explicit sign-off.

**Every written value carries provenance**: source object, record ID, date
logged, derivation method, and the phrase the date came from. A rep who cannot
trace a claim will not act on it, and you cannot debug what you cannot trace.

**Gate the dealer's own customers at BOTH levels** — company rollup *and*
engagement record. See Stage 6. This was the most damaging bug in the first run.

**Scope creeps across a session.** "Run the process" is not standing approval to
populate every field you can reach. Confirm each new property before writing it.

---

## Preflight

### 1. Verify the portal

```
GET /account-info/v3/details   →  portalId
```

Confirm it matches the intended client **before touching anything**. The QBS
OAuth MCP is bound to portal 20682069 and will silently corrupt analysis if used
against a client. For any client portal, PAT only — load
`qbs-hubspot-private-app`.

### 2. Probe effective permissions

The reported scope list under-reports. Probe with a bogus property name — zero
mutation, definitive answer:

```
PATCH /crm/v3/objects/calls/<id>  {"properties":{"zzz_probe":"x"}}
  400  →  write allowed (property just doesn't exist)
  403  →  no write scope
```

Commonly blocked on dealer PATs: `automation`, `crm.lists.*`,
`crm.objects.deals.read`, `crm.objects.owners.read`. Engagement objects usually
work even when unlisted.

**If the engagement promises a segmented view or an auto-task workflow, confirm
`crm.lists.write` and `automation` now.** Without them those deliverables cannot
be built, and the client needs to know before the work starts, not after.

### 3. Inventory every object and text field

```
POST /crm/v3/objects/{calls,tasks,emails,meetings,notes}/search
  {"limit":1,"filterGroups":[{"filters":[{"propertyName":"<prop>","operator":"HAS_PROPERTY"}]}]}
```

| Object | Text fields to check |
|---|---|
| calls | `hs_call_body`, `hs_call_summary`, `hs_call_title` |
| tasks | `hs_task_body` ("Task Notes"), `hs_task_subject` ("Task Title") |
| meetings | `hs_meeting_body`, `hs_meeting_title`, `hs_internal_meeting_notes`, `hs_meeting_summary` |
| notes | `hs_note_body` |
| emails | `hs_email_text`, `hs_email_subject`, `hs_email_direction` |

**Then sample 100 records per object and read them.** Counts do not tell you
where the content is. At UBEO the median task body was empty — the substance sat
in the subject line, which no amount of counting would have revealed.

---

## Stage 1 — Harvest

Union the term set across every text property of every object, deduplicating by
record ID. Search per-term and merge; HubSpot caps `filterGroups` at 5, so one
OR query cannot hold the set.

Term set and rationale: **`references/term-set.md`**.

### The 10,000-result cap — read this before writing the harvester

HubSpot's search API **hard-stops at 10,000 results per query** and returns a
400 at result 10,001. No warning, no partial flag. Any term above that threshold
is silently truncated — and it binds hardest on exactly the terms that matter
most (`lease`, `copier`, and major OEM names all exceed it).

**Every harvest must be date-windowed.** Recursively halve the `hs_timestamp`
range until each slice is under ~9,000, then page each slice:

```python
def windows(prop, term, lo, hi, depth=0):
    c = count(prop, term, lo, hi)
    if c == 0: return 0
    if c < 9000 or depth >= 8: return page(prop, term, lo, hi)
    m = lo + (hi - lo)/2
    m = date(m.year, m.month, 1)
    if m <= lo or m >= hi: return page(prop, term, lo, hi)
    return windows(prop,term,lo,m,depth+1) + windows(prop,term,m,hi,depth+1)
```

Measured impact at UBEO: identical term set, **3,997 records flat vs 142,909
windowed**. A 36× difference, invisible without this check.

### Small objects: skip keywords entirely

Under ~35,000 records, pull the whole object with date windows and no term
filter. Cleaner, faster, and immune to term-list gaps. Applies to meetings,
notes, and inbound email at typical dealer scale.

### Emails are a special case

`hs_email_text` and `hs_email_html` **reject search filters entirely** — only
`hs_email_subject` is searchable. Filter on `hs_email_direction` and read bodies
back from the result payload.

**Inbound only.** Outbound scores *higher* on keywords and is worthless: the
hits are the dealer's own templates repeating verbatim. At UBEO, outbound was
17.8% keyword-positive and intel-free; inbound was 9.8% and carried the real
signal.

### Harvester requirements

Non-negotiable, all learned the hard way:

- **Resumable.** Persist the pool and a completed-term ledger after every term.
  A multi-hour harvest will be interrupted.
- **Catches every exception, not just HTTPError.** The first run died on an
  uncaught `RemoteDisconnected` after 25 minutes.
- **Prints per-term progress.** A harvester that only prints at the end gives
  no way to spot a problem for hours.
- **Never `nohup` inside a backgrounded call** — the child dies with its parent.

### ✅ GATE 1 — before extracting

- [ ] Every term × field combination appears in the completed ledger
- [ ] **No term returned exactly 9,800–10,000** — that signals cap truncation;
      re-run it windowed
- [ ] Pool size is plausible against the raw counts from Preflight
- [ ] If terms were added mid-run, the ledger confirms they actually ran

---

## Stage 2 — Extract

For each record, try each source in order and **take the first that resolves**.
Ordering is the whole design: inference rules only ever see records the
trustworthy rules could not resolve, so a weak method can never overwrite a
strong one.

| # | Source | Example | Confidence |
|---|---|---|---|
| 1 | Stated date | "lease expires 1/2026" | CONFIRMED |
| 2 | Stated year only | "lease is up in 2028" → **pin 10/31** | CONFIRMED |
| 3 | Remaining term + engagement date | "2 years left" | CALCULATED |
| 4 | Renewal term | "renewed with Lucas for 3 years" | CALCULATED |
| 5 | Term + start year | "NEW 4 YEAR RICOH LEASE 2014" | CALCULATED |
| 6 | Just-signed + term | "just signed 5 yr with Xerox" | CALCULATED |
| 7 | Month-to-month | no lease at all → date = today | WINNABLE NOW |
| 8 | Projected next cycle | lapsed lease + own term, **one roll only** | VERIFY |

### The four classes people get wrong

**Just-signed is the best material in the corpus, not a rejection.** Someone who
has just signed volunteers *who they signed with* — signing date, term length,
and incumbent from one sentence. A 2021 rejection is a 2026 lead. At UBEO, 886
just-signed records yielded 223 computable future dates against a
142-of-266 unknown-provider rate everywhere else.

**Month-to-month means no lease to wait for — callable today.** These have no
future date, so any pipeline requiring one silently discards them. Date them to
today so they sort to the top. Guard the negation: *"customer **not** on month
to month"* is not a hit.

**Projection is capped at one cycle.** Rolling a lapsed lease forward by its own
term is defensible once. Measured degradation at UBEO: 1 cycle 2,588
(defensible) / 2 cycles 4,411 (assumes same vendor and term twice) / 3+ cycles
3,143 (fiction). Never exceed one, and always label it VERIFY.

**Elapsed term is a second, invisible half of the corpus — and it inverts.**
Every term set starts by looking for *remaining* term ("3 yrs left"). Roughly the
same volume of notes state *elapsed* term instead:

> *"not the decision maker will try again monday before 9. A year and half into
> their contract"*

That is a dated lease signal. Read naively it is also **backwards**: a
"year and a half" rule built for remaining term dates this to early 2028 when the
answer is early 2030. The direction flips on one word — `into`.

Rules:

- If a duration is followed by `into`, it is elapsed. Remaining-term rules must
  not fire on that sentence.
- **Total term stated** → `CALCULATED`. *"2 years into a 5 year lease"* → 3 years out.
- **No total stated** → `PROJECTED`, assuming the 60-month copier convention, and
  the assumption goes **in the evidence string** so nobody mistakes it for a fact:
  `(assumes the 60-month copier term)`.
- Ordinals count too: *"in the second year of a 5 year lease"* → 1.5 elapsed.
- *"just renewed" / "recently renewed" / "signed in 2023"* are the same class
  viewed from the start date. Guard the negation — *"they did **not** just renew"*.
- Reject the impossible: *"6 years into a 5 year lease"* yields nothing.

Beware the tokenizer here. `into` is an extremely common English word — *"we
walked into the lobby"*, *"moved into their new office"*. The pattern must require
a duration before it and a lease noun after it, or the pool fills with noise.

Measured at UBEO, this class was worth **~3,200 calls and ~5,000 tasks** that the
original term set never touched, on a run that had already been QA'd twice.

### Parsing details that cost real yield

- **Fuzzy quantifiers** — "a couple years left", "a few years", "several years",
  "a year or two", "year and a half". Affect **12,030 records**. No numeric
  regex catches them. Map: couple=2, few=3, several=4, year-and-a-half=1.5.
- **Month abbreviations** — the lookup needs `sept`, not just `sep`. Normalize
  by first three characters after stripping periods.
- **Year-only dates pin to 10/31**, never Jan 1. Defaulting to January is both
  wrong and makes live leases sort as already-expired.
- **Loose quantity rules need a lease word within 100 characters**, or
  *"his plotter is 2 years old"* becomes a lease term.
- **Emails need thread-stripping and single-sentence scoping.** Without both,
  *"vacation from 9/1/2025 through 10/24/2025"* is read as a lease end date. A
  40-line thread pairs "lease" from one message with a date from another.

### Date window

Keep anything from **12 months in the past forward**. Computed dates carry ±3
months of precision, so a recently-lapsed date is inside the error bar and often
the hottest lead in the set. Flag those `IN_PLAY_VERIFY`.

Long-expired dates are not waste — they are a **win-back list** (that account
went to market without you). Bucket them separately rather than discarding.

### ✅ GATE 2 — before writing anything

- [ ] **Read 10–15 extracted records yourself.** Not counts — the actual text.
      Every precision bug in the first run was caught this way and none by
      aggregate statistics.
- [ ] Every value's basis phrase appears in its own evidence excerpt
- [ ] Yield is plausible: ~1–3% of pool. Far above suggests false positives;
      far below suggests a field or pattern gap
- [ ] Source distribution is sane — projection should not dominate confirmed
      by more than ~3:1
- [ ] Spot-check the highest-volume single pattern for a systematic error

---

## Stage 3 — Classify and exclude

Exclusions matter more than extraction. Each of these carries clean, accurate
lease dates that would otherwise land on a call list.

| Flag | Detects | Why it matters |
|---|---|---|
| `DEALER_INCUMBENT` | "lease with us", "through us", "from us", "current customer", "we sold", "off lease" | The dealer already holds this lease. Pitching them looks incompetent. |
| `DNC` | "XDNC", "DO NOT CALL", "stop calling" | Accurate data, wrong list. |
| `OWNS_EQUIPMENT` | ownership terms with no lease mention | No lease exists, so no expiration ever will. |
| `MONTH_TO_MONTH` | month-to-month, m2m (negation-guarded) | Not an exclusion — an escalation. Callable now. |
| `AUTO_RENEW` | auto renew, evergreen, rolled over | Escalation. Missing the notice window costs the cycle. |
| `IN_PLAY_VERIFY` | date within 12 months past | Inside the error bar; verify on the call. |

Incumbent phrasing varies more than any regex covers. **Read the residue by hand
before a portal-wide run** — at UBEO this recovered 16 providers regex missed
and corrected *"they are **not** with Centric"*, which regex had scored as
provider = Centric.

---

## Stage 4 — Deduplicate

**Legacy CRM boilerplate.** Migrated dealers stamp a `SalesStrategy` /
`SalesChainID` blob onto every task for an account — one string appeared on
**178 separate records** at UBEO. Strip `SalesChainID:`, `Federal ID Number:`,
`SICCode:`, `Annual Revenue:`, `Toll Free:` before hashing, then dedupe on the
first ~150 characters of normalized text.

Raw 4,718 matches collapsed to 626 unique statements. Skipping this inflates
every downstream number by roughly 7×.

---

## Stage 5 — Write engagement evidence

Create `ai__lease_information` (string / textarea) on each engagement object.

**Check the schema per object — naming is not consistent.** At UBEO the
engagement objects used `ai__lease_information` (double underscore) while the
company object used `ai_lease_information` (single). Read the existing property
list; never assume.

### Format

```
YYYY/MM [CONFIDENCE] - Provider - <evidence centred on the basis phrase>
  [source: <type> id <N>, logged MM/DD/YYYY, <derivation>: "<basis phrase>"]
  ** FLAGS
```

**`YYYY/MM`, never `MM/YYYY`.** These are text fields, so they sort as strings —
year-first makes a plain A→Z sort chronological. `MM/YYYY` puts `01/2029` above
`09/2026`, exactly backwards for a list whose purpose is soonest-first.

**Centre the evidence excerpt on the basis phrase** (~150 chars either side).
Never slice from the start of the body: the phrase justifying the date sits past
the cut often enough that the field ends up asserting a date with nothing
visible to support it.

Write via `POST /crm/v3/objects/{obj}/batch/update`, 100 per batch.

### ✅ GATE 3 — after writing

- [ ] **Verify with a direct GET, not search.** The search index lags writes by
      up to a minute — it will under-report and look like a failure.
- [ ] Re-check counts after ~45s once the index settles
- [ ] Spot-read 3 written records in the portal UI as a rep would see them

---

## Stage 6 — Roll up to companies

Resolve associations, then batch-read companies for lifecycle and any existing
value.

### Rank when an account has several signals

1. Evidence strength (stated > calculated > projected)
2. Provider known
3. Recency

### Two gates, both mandatory

**Gate 1 — lifecycle.** Skip `customer`, plus any dealer-specific stage (UBEO
had a custom "Team UBEO"). **Ask which stages are in scope; do not assume.**

**Gate 2 — never downgrade.** A value with no `[source:` tag was written by a
human — skip it entirely. Machine values are only replaced by a *higher-ranked*
signal. This makes re-running safe: at UBEO's final run, 1,887 companies
correctly kept their existing value.

### The customer gate applies at BOTH levels

Gating only at the rollup keeps customer leases off the company record but
**leaves them written on the engagement records**, where a rep browsing activity
still finds them. At UBEO this left 1,173 records live, including:

> *"We have (2) KONICA leases coming up 2-6-26 that needs to be scheduled for
> **return** — We need the Return Authorization"*

That is the dealer's own equipment coming back, and it reads exactly like a
competitive signal. Clear them from the engagement records too.

### Cross-object merge closes the provider gap

One call names the OEM, a task carries the date, a meeting names the decision
maker. Merging on company recovers providers for records that would otherwise
read "Provider unknown" — the single largest quality gap in the output.

### ✅ GATE 4 — after rollup

- [ ] Companies with no association are reported, not silently dropped
- [ ] **Sanity-check associations.** At UBEO a call about "Lowcountry Leadership
      Charter School" was associated to "Emirates Investment & Development
      Center". Bad associations put lease intel on the wrong company.
- [ ] Kept-existing count is non-zero on a re-run (proves Gate 2 works)
- [ ] Zero companies with lifecycle = customer carry a value

---

## Source priority

Run in this order — descending signal density, measured:

| Rank | Object | Why |
|---|---|---|
| 1 | **Tasks** | ~70% of all signal. Content is often in the *subject*, not the body. |
| 2 | **Meetings** | Highest quality per record — 49% name the incumbent OEM vs 28% calls, 15% tasks. Structured appointment briefs. |
| 3 | **Calls** | Body **and** `hs_call_summary` — the summary is not a duplicate; it carries content where the body is an empty dialer stub. |
| 4 | **Notes** | Small, quick. |
| 5 | **Inbound emails** | Weakest yield, highest noise, needs the most special handling. |

### Dialer noise

Auto-dialers (Orum and similar) stamp stub bodies like
`[Orum] MF 8/26 @ 1:54 PM (power)` onto every attempt — 789,471 of 1,019,360
call bodies at UBEO, 77% pure noise.

**Filter stubs by length** (`startswith("[Orum]") and len(body) < 60`), **never
by the dialer prefix**: the same dialer's `----- AI Generated Notes -----`
blocks are among the richest content in the portal. Filtering on the prefix
throws away the best material with the worst.

---

## Where the method runs out

Keywords are exhausted as a lever. The final calls harvest at UBEO grew the pool
**60% and added 2% more signal** — broad terms pull volume and almost no datable
statements.

Roughly **24,000 records** discuss a lease in terms no rule can parse:
*"they're locked in for a while"*, *"not until after the new year"*,
*"when the current one is up in the spring"*, *"budget cycle is July"*.

That is a reading problem, not a matching problem, and it is the largest
remaining increment in any portal this runs against. Do not respond to a
plateau by adding more keywords — measure first, and expect the answer to be
that the residue needs reading.

---

## Reference: UBEO run (portal 516382, Aug 2026)

Use these to sanity-check a new portal's numbers.

| Stage | Count |
|---|---|
| Engagement records total | ~3,915,000 |
| Candidate pool | 355,395 |
| Dated signals | 18,508 |
| In-window (12mo back → forward) | 5,327 |
| After customer/DNC/owner gates | 4,154 |
| **Company records written** | **1,938** |

Written: tasks 3,022 · calls 924 · meetings 159 · notes 96 · emails 43.
Confidence split: CALCULATED 1,820 · PROJECTED 1,563 · CONFIRMED 605 ·
MONTH-TO-MONTH 166. Expiring within 12 months: 2,215. Incumbent named: 769.

**Expect ~1–3% true yield from a keyword pool. Set that expectation with the
client before the engagement starts, not after.**

---

## Deliverables

Two documents, two audiences, and they must not be confused:

- **Client-facing brief** — results only. No term lists, no patterns, no
  pagination technique. The SOW is genericized to protect the methodology; the
  brief must match. Confidence tiering *is* safe to include — a rep who cannot
  tell a confirmed date from a projected one will misuse the field.
- **Internal process flow** — the actual mechanics. Never send to a client.

### If rendering a PDF

- Chromium: `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`. Pass
  `executable_path` — pip's Playwright expects a newer build than is installed.
  Do not run `playwright install`.
- **Two-column grid layouts do not paginate.** Chromium breaks after every grid
  item; collapse to block flow for print or every section lands on its own page.
  A 14-page render became 4 with this one change.
- **Declare `<meta charset="utf-8">`** or every em-dash becomes `â€"`.
- **Google Fonts do not load headless.** Download and inline as base64 data
  URIs, or the PDF silently falls back to Liberation Serif.
- Check the rendered pages, not the page count.
