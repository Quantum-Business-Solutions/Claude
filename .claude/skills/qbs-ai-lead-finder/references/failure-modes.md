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
