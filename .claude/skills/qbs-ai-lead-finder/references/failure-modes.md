# Failure modes

Every entry here produced wrong output during the UBEO production run before it
was caught. **All of them are silent** — no error, no exception, just quietly
wrong numbers. Several survived multiple passes because aggregate statistics
looked reasonable.

Each carries a detection test. Run them.

---

## 1. Search result cap — the expensive one

**Symptom.** Pool is a fraction of its true size. No error at any point.

**Cause.** HubSpot's search API hard-stops at 10,000 results per query and
returns a 400 at result 10,001. It binds hardest on the highest-value terms —
`lease` (17,124 task bodies at UBEO), `copier` (20,623 subjects), `Xerox`
(9,198), `Konica` (10,494).

**Impact measured.** Identical term set: **3,997 records flat vs 142,909
windowed**. 36×.

**Fix.** Recursively halve the `hs_timestamp` range until each slice is under
~9,000, then page each slice.

**Detection.**
```python
# any term returning exactly 9,800-10,000 was almost certainly truncated
suspicious = [t for t,n in per_term.items() if 9800 <= n <= 10000]
assert not suspicious, f"cap truncation likely: {suspicious}"
```

---

## 2. Harvest/extract field mismatch

**Symptom.** Yield far below expectation despite a large pool.

**Cause.** Harvesting on one field and extracting from another. At UBEO the
harvester searched `hs_task_subject` but the extractor only read
`hs_task_body` — and ~335,000 tasks have a subject with no body.

**Impact measured.** 203 → 659 signals from fixing this alone. 3×.

**Fix.** Extract from every field harvested. Merge them, avoiding double-count
when subject duplicates the body opening.

**Detection.**
```python
assert set(EXTRACT_FIELDS) >= set(HARVEST_FIELDS), "harvested a field you never read"
```

---

## 3. Tokenizer false positives

**Symptom.** A term returns a huge count and contributes nothing. Pool balloons,
yield does not move.

**Cause.** HubSpot's tokenizer strips punctuation and matches substrings across
word boundaries in ways that are not obvious from the term.

| Term | Expected | Actually matches | Count |
|---|---|---|---|
| `'27` | apostrophe-year | `3/27`, `Oct.27th`, "270 employers" | 38,169 |
| `IM C` | Ricoh IM C series | "hi**m c**an", "Ki**m c**all" | 23,599 |
| `Kelly` | dealer name | people named Kelly | 4,313 |
| `co-op` | cooperative purchasing | "**Co-op**erative Adjustment Bureau" | 2,449 |
| `Advance` | dealer name | "**Advance**Online Solutions" | 1,902 |

At UBEO, **0 of 8 sampled `'27` matches were real.**

**Fix.** Sample any term before trusting its count. Never add a term to the set
on volume alone.

**Detection.**
```python
# for any candidate term, pull 8 records and eyeball them
d = search(obj, prop, term, limit=8, properties=[prop])
# if fewer than half are genuine matches, drop the term
```

---

## 4. January-1 defaulting

**Symptom.** Live leases sort as already-expired. Year-only dates cluster on
Jan 1.

**Cause.** Parsing "lease is up in 2028" yields a year with no month; defaulting
the month to 1 produces `2028-01-01`, which is both wrong and sorts badly.

**Fix.** Pin year-only dates to **10/31** of the stated year. Label them
`CONFIRMED (year only - month assumed)` so the assumption is visible.

**Detection.**
```python
jan1 = [x for x in rows if x['end'].endswith('-01-01')]
# a large Jan-1 cluster means year-only dates are not being pinned
assert len(jan1) < 0.05 * len(rows), "year-only pinning is not firing"
```

---

## 5. Evidence excerpt sliced from the wrong place

**Symptom.** The field asserts a date with nothing visible to support it. Only
findable by reading the output.

**Cause.** Taking `body[:300]` instead of centring on the phrase the date came
from. The justifying phrase often sits past the cut.

**Impact measured.** 7 of 266 records in the first pass.

**Fix.** Locate the basis phrase and take ~150 characters either side.

**Detection.**
```python
bad = [x for x in rows if x['basis'] and x['basis'].lower() not in x['value'].lower()]
assert not bad, f"{len(bad)} values do not contain their own basis phrase"
```

---

## 6. Loose quantity rules without lease context

**Symptom.** Equipment age read as lease term.

**Cause.** Fuzzy quantifier patterns ("year and a half", "a couple years") firing
anywhere in the text. Real example:

> *"his plotter is 2 years old and his other equipment is **a year and a half**"*

**Fix.** Require a lease/contract/agreement word within 100 characters of the
match for the loose rules. The tight rules (`left`, `remaining`, `to go`) are
lease-specific enough to stand alone.

**Impact measured.** 54 → 17 records in that class; 36 bad values removed.

---

## 7. Email thread bleed

**Symptom.** Dates from unrelated content in quoted reply chains. Emails only.

**Cause.** Email bodies carry quoted chains and signatures. A "lease" word in
one message pairs with a date 40 lines away in another. Real example:

> *"I am currently on an extended vacation from 9/1/2025 **through 10/24/2025**"*
> — scored as a lease end date

Also seen: City-of-Las-Vegas RFP boilerplate, and the dealer's own rental quote
("for another 63 months") quoted back by the prospect.

**Fix.** Two steps, both required:
1. Strip quoted chains (`On ... wrote:`, `From: ... Sent:`, `>`, `___`) and
   signature blocks — keep only the newest message.
2. Scope extraction to a **single sentence**: the lease word and the date must
   appear in the same sentence.

**Impact measured.** 174 raw → 124 after scoping → 53 after boilerplate
exclusions. **~70% of the raw email extraction was wrong.**

---

## 8. Negation blindness

**Symptom.** Records matching a pattern that the text explicitly negates.

**Real examples.**
> *"Customer **not** on month to month. Still have 1 year on lease."*
> *"they are **not** with Centric"* → scored as provider = Centric

**Fix.** Explicit negation guard within ~25 characters preceding the match:
`not | isn't | aren't | no longer | never`.

---

## 9. Customer leak — the most damaging

**Symptom.** Reps pitch against their own installed base. Looks like a working
list; destroys credibility on first contact.

**Cause.** Gating lifecycle at the company rollup only. The engagement records
still carry the value, and a rep browsing activity finds it.

**Real example.**
> *"We have (2) KONICA leases coming up 2-6-26 that needs to be scheduled for
> **return** — We need the Return Authorization"*

That is the dealer's own equipment coming back, and it reads exactly like a
competitive lease signal.

**Impact measured.** 1,173 engagement records — 976 tasks, 178 calls, 10 emails,
9 notes, 23 meetings.

**Fix.** Resolve associations for every signal, look up lifecycle, and clear the
property on **engagement records** whose company is a customer — not just skip
them at rollup.

**Detection.**
```python
cust = [eid for eid,cid in assoc.items() if lifecycle(cid) == "customer"]
assert not any(has_value(e) for e in cust), f"{len(cust)} customer engagements still carry a value"
```

---

## 10. Direction inversion — elapsed term read as remaining term

**The one that survived two QA passes.** Found only when a human opened a record
and asked why a note mentioning a contract had no lease field.

Every term set is built around *remaining* term — "3 yrs left", "2 years to go".
A comparable volume of notes state *elapsed* term instead, and the two look almost
identical:

```
"a year and a half left on the lease"        ->  ends ~2028-02   (remaining)
"a year and half into their contract"        ->  ends ~2030-02   (elapsed)
```

One word, `into`, flips the answer by three years. A fuzzy-quantifier rule written
for the first form will happily fire on the second and produce a confidently wrong
date — worse than no date, because it looks trustworthy.

### Why aggregate statistics cannot catch it

The extractor's output looked healthy: dates in range, tiers assigned, evidence
attached. Nothing in a count, a distribution, or a null-rate check distinguishes a
lease ending in 2028 from one ending in 2030. **Only reading a record next to its
source text exposes it.**

### Detection

```python
# every record whose evidence contains "into" must have come from an elapsed rule
suspect = [r for r in rows
           if re.search(r'\binto\b', r['basis'], re.I)
           and 'elapsed' not in r['src']]
assert not suspect, "remaining-term rule fired on elapsed-term language"
```

And the inverse — records the harvest never even saw:

```python
# sample records containing elapsed language but carrying no signal at all
"into their contract", "years into", "just renewed", "recently renewed"
```

At UBEO this second query returned ~1,400 calls gross, harvesting to **3,189 calls
and 5,000+ tasks** with no lease field, on a run already declared complete.

### Fixes

1. Harvest the elapsed class explicitly (`references/elapsed-terms.json`).
2. Require a duration before `into` and a lease noun after it — bare `into` is one
   of the commonest words in English and floods the pool with *"walked into the
   lobby"*.
3. Where no total term is stated, project on the 60-month copier convention, tier
   it `PROJECTED`, and **put the assumption in the evidence string**:
   `(assumes the 60-month copier term)`. A projection that hides its assumption is
   indistinguishable from a measurement.
4. Reject impossibilities — *"6 years into a 5 year lease"* yields nothing.

### The general lesson

Ask of every extraction rule: *does this phrasing have a mirror image that means
the opposite?* Remaining/elapsed. Signed/expiring. Renewed/lapsed. The mirror is
usually in the data at similar volume, and it usually reads as a near-synonym.

## 11. The anchor field missing from the harvest — failure mode 2, second helping

The elapsed-term harvester was told which body fields to search and dutifully
stored exactly those. It was never told to store `hs_timestamp`. Every downstream
computation measures from the engagement date, so every record hit
`if not ts: continue` and the extractor reported **0 signals from 14,300
harvested records** while its unit tests passed 14/14.

Zero is a suspiciously clean number. Treat any extractor that returns *nothing*
from a large pool as broken until proven otherwise — a genuine yield of zero
essentially never happens on a pool built from matched keywords.

**Fix:** the harvester appends the anchor fields itself rather than trusting the
caller:

```python
for _t in ("hs_timestamp", "hs_createdate"):
    if _t not in PROPS: PROPS.append(_t)   # anchor fields, never optional
```

Backfilling an existing pool is cheap — batch/read 100 ids at a time — so a
mis-harvested pool never needs re-harvesting.

## 12. Regex windows that leap across clauses

```
"renewed for 5years, call back in 2026"   ->  dated 2031-07-01
```

The start-year rule allowed up to 40 characters between the verb and the year, so
it skipped over the real term and read the **callback date** as the lease start,
then added 60 months. The output looked entirely normal: plausible tier, plausible
date, evidence quoted.

**Fixes:**

1. Shrink the gap to what the grammar actually needs — a few optional articles,
   not 40 free characters.
2. Add an explicit veto for the competing meaning:

```python
CALLBACK = re.compile(r"\b(?:call|try|follow[- ]?up|reach out|check|touch base)\s+"
                      r"(?:me |them |him |her )?(?:back )?(?:again )?(?:in|around|by)\b", re.I)
```

Any date-bearing rule needs the same question asked of it: **what else could this
number be?** Callback dates, invoice dates, fiscal years and delivery dates all
look exactly like lease dates to a regex.

## 13. Rolling a lapsed lease forward on the wrong term

The one-cycle roll-forward used a flat 60 months even when the note stated the
term. *"Signed a new lease in 2018 for 3 yrs"* ended 2021; rolled by 60 months it
became 2026 and looked current. Rolled by its own 36-month term it lands in 2024 —
still lapsed, and correctly dropped.

Roll by the term the record states, and only fall back to the convention when
none is stated. Then re-check the cap: a record still lapsed after one cycle is
dropped, not rolled again. Applying this at UBEO cut the elapsed-term set from
1,616 to 1,283 — the 333 removed were all fiction.

**A rolled record is a projection, whatever it was before.** Demote the tier on
roll-forward; a CALCULATED date that has been moved by an assumed renewal is no
longer calculated. This alone moved 275 UBEO records out of CALCULATED.

## 14. Anchoring a relative term to the engagement timestamp

The single most dangerous bug in the extractor, because the output looks
completely reasonable.

Rules like *"just signed"*, *"renewed for N"* and *"N years left"* compute a
date by adding the term to the engagement's `hs_timestamp`. That is correct only
when the statement was made **about the moment the record was logged**. It very
often is not:

| what the record says | logged | extractor said | truth |
|---|---|---|---|
| `New lease just signed 5/2018` | 2022-2024 | 2027-2029 | 2023 |
| `Signed a new lease in 2018 for 3 yrs` | 2024 | 2027 | 2021 |
| `renewed for 60 mos beginning JAN 2024` | 2027 | 2031 | 2029 |
| `Just signed leases with Cannon Direct in January` | 04/2022 | 04/2027 | 01/2027 |
| `Briefly chatted back in 2023 and at the time you had 2-3 years left` | 2025 | 2028 | 2025-2026 |

Every one of these states its own anchor, in the same sentence, and the
extractor stepped over it.

**Rule: if the sentence carries an explicit start month or year, that is the
anchor. The engagement timestamp is the fallback, never the default.** Only
genuinely present-tense phrasing ("just signed", "we renewed last month") may
anchor to the record date, and "last month" means the record date minus one
month, not the record date.

Measured at UBEO: of 1,687 signals whose date was anchored to the timestamp,
**71 (4.2%) state an earlier anchor the extractor ignored** — 67 of them on
tasks, where the legacy CRM's stamped account headers repeat old strategy notes
for years. Each is wrong by 2 to 8 years.

## 15. Stamped account headers inflate a "new findings" count

The legacy CRM stamps one account-strategy header onto every task for that
account. A single 2018 note — *"Part of Northrop Realty. New lease just signed
5/2018"* — reappeared on **17 separate tasks** spanning 2022 to 2024 and was
counted as 17 findings.

Deduplicate on `(company, normalised body)` **before** reporting any count, and
treat a header that repeats across years as one determination dated to the
header, not to each task.

At UBEO this was the difference between reporting 30 new lease determinations
and the true figure of 10: 17 were one account's header, 1 was a duplicate
phrasing, and 2 were mis-anchored past-dated leases that read as future.

## 16. "New" findings on accounts that already have the field

A gap analysis that scans engagements at accounts *selected because they already
have a lease date* finds engagement-level gaps, not new accounts. All 10 UBEO
determinations landed on companies that already carried a company-level date:
3 corroborated it, 7 contradicted it.

That is still worth writing — the engagement now carries its own citation, and a
contradiction is a lead to resolve — but it is **not** net-new pipeline. Say
which it is before anyone builds a forecast on the number.

**Never roll a single engagement up over an existing company date to resolve a
contradiction.** Surface the conflict; let a human pick.

## Infrastructure failures

Not data bugs, but they cost hours.

**Harvester dies on a dropped connection.** Catching only `HTTPError` misses
`RemoteDisconnected`, socket timeouts, and DNS blips. The first run died after
25 minutes with nothing saved. Catch broad, back off, and persist after every
term.

**Backgrounded `nohup` child killed with its parent.** Run the work as the
background command directly; do not `nohup` inside it.

**No progress output.** A harvester that prints only on completion gives no way
to spot a problem for hours. Print per term.

**Snapshotting a file mid-write.** Copying the pool while the harvester is
writing yields truncated JSON. Retry until it parses.

**Search index lag.** Verification via search immediately after a write
under-reports and looks like failure. Verify with direct GET; re-check search
after ~45 seconds.
