# Term set

QA'd against ~3.9M records at UBEO. Counts are that portal — treat as relative
weight, not absolute expectation.

**Before adding any term, sample 8 records and read them.** Volume is not
evidence; see rejected terms below.

---

## Design principle: anchors make most timing words redundant

If `lease` is harvested exhaustively, *"2 years left on their lease"* is
**already in the pool**. Adding `to go` (31,438) or `left in` (9,894) as separate
terms costs enormous crawl time and adds only records that mention timing with
no lease context — which are ambiguous anyway. *Two years left* on what?

So: harvest the **anchors** exhaustively, then add only terms that appear
*without* an anchor nearby.

---

## Anchors — harvest exhaustively, always windowed

`lease` `leases` `leasing` `leased` `contract` `contracts` `contracted`
`agreement` `agreements` `deal` `deals`

`lease` alone exceeds the 10K cap in both task bodies and subjects. Never query
these flat.

---

## Timing — high-precision, can appear without an anchor

`years left` `yrs left` `year left` `months left` `mos left` `expires` `expire`
`expiring` `expiration` `comes due` `coming due` `up for renewal` `renews`
`evergreen` `auto renew` `buyout` `buy out` `runs out` `rollover` `locked in`
`locked into` `mid contract` `end date`

---

## Fuzzy quantifiers — 12,030 records, no numeric regex catches them

`a couple` `couple years` `couple of years` `couple more` `a few years`
`few more years` `several years` `a year or two` `year and a half` `18 mos`
`long term` `multi year`

Mapping: couple = 2 · few = 3 · several = 4 · year-and-a-half = 1.5

**These need a lease word within 100 characters** or they match equipment age.

---

## Just-signed — the highest-value class

`just signed` `just renewed` `recently signed` `recently renewed` `signed a new`
`renewed their` `renewed our` `re-signed` `resigned` `signed with` `went with`
`yr deal` `year deal` `recently got`

Someone who just signed volunteers **who they signed with**. Signing date, term
length, and incumbent from one sentence.

---

## Vocabulary found only by reading real records

None of these were in the original term list. All were discovered by sampling
actual subjects — *"Call, 4yr deal began Dec 2024/Jan 2025"*, *"call, With Kelly
until 2028"*.

`until` `til` `thru` `through` `not until` `out until` `good til` `w/until`
`start` `started` `starts` `began` `sold` `placed` `upgrade` `installed`
`delivery`

**Lesson: sample the corpus before finalizing any term list.** The client's own
vocabulary will not match yours.

---

## Elapsed term — the mirror image, and the one everyone forgets

Every term above reads *remaining* time. These read *elapsed* time and are just as
datable — but they invert if you feed them to a remaining-term rule. Found only
after a run that had already passed two QA passes.

| Term | calls | note |
|---|---|---|
| `into the contract` | 205 | |
| `just renewed` | 210 | start-date form |
| `recently renewed` | 209 | start-date form |
| `year into` | 151 | |
| `years into` | 138 | |
| `into their contract` | 136 | |
| `years ago we` | 122 | |
| `signed last year` | 58 | |
| `into a 5 year` / `into a five year` | 41 each | total term stated → CALCULATED |
| `into their lease` | 39 | |
| `renewed last` | 40 | |
| `started our lease` | 7 | |
| `signed two years ago` | 5 | |

Gross ~1,400 on calls before dedupe; the harvested pool came to **3,189 calls and
5,000+ tasks**. Also harvest the ordinal forms — `first year of`, `second year of`,
`third year of`, `year of their`, `year of the`.

**Do not harvest bare `into`.** It is one of the most common words in English and
the pool becomes unusable. Always pair it with a duration or a lease noun.

## Term lengths — a length plus a start date yields an end date

`36 month` `39 month` `48 month` `60 month` `63 month` `66 month` `12 month`
`24 month` `36 mo` `60 mo`

---

## Incumbent OEMs — dealers routinely omit these from their own filters

`Ricoh` `Xerox` `Canon` `Konica` `Minolta` `Sharp` `Toshiba` `Kyocera` `Lanier`
`Savin` `Lexmark` `Brother` `Epson` `Oce` `Panasonic`

Many carry no timing, but they **fill the provider gap** via cross-object merge
on company — the largest quality gap in the output.

`Xerox` and `Konica` exceed the 10K cap in task subjects.

---

## Leasing companies — imply a lease exists and give a paper trail

`Wells Fargo` `US Bank` `Marlin` `Great America` `DLL` `LEAF` `TIAA`
`First Citizens` `CIT`*

*`CIT` returns 13,425 at UBEO and is mostly false positive. Verify before use.

---

## Ownership — tag and EXCLUDE, do not chase

`own their` `we own` `they own` `owns` `outright` `purchased` `bought`

These accounts bought rather than leased. No lease date will ever exist. Tag
them so they stop re-entering the pool on every run.

---

## Rejected — measured and dropped

### Tokenizer traps (never add these)

| Term | Volume | Actually matches |
|---|---|---|
| `'26` `'27` `'28` `'29` `26'` `27'` `28'` `29'` | 326,871 combined | `3/27`, `Oct.27th`, "270 employers" — **0 of 8 sampled were real** |
| `IM C` | 23,599 | "hi**m c**an", "Ki**m c**all" |
| `Kelly` | 4,313 | people named Kelly |
| `co-op` | 2,449 | "**Co-op**erative Adjustment Bureau" |
| `Advance` | 1,902 | "**Advance**Online Solutions" |

### High volume, no added signal (redundant given anchors)

`up in` 96,957 · `is up` 37,653 · `to go` 31,438 · `ending` 13,892 ·
`proposal` 12,229 · `out from` 10,970 · `left in` 9,894 · `5 year` 5,230 ·
`looking at` 5,178 · `evaluating` 4,464 · `3 year` 5,176 · `4 year` 3,376 ·
`they own` 3,191 · `owns` 3,725 · `in contract` 2,754 · `30 day` 2,287

**~283,600 combined hits dropped as pure crawl cost.**

### Dealer names that do not exist in this data

`Loffler` `Gordon Flesch` `Applied Imaging` `Impact Networking` — all **zero**.
Competing-dealer names were a reasonable hypothesis and did not survive
measurement. Test them per client rather than assuming.

---

## Worth adding, not yet run

Measured as real but not included in the UBEO run:

- **Model families** — `bizhub` 965 · `e-STUDIO` 597 · `TASKalfa` · `C258` ·
  `C558` · `C360`. A rep naming a model knows the fleet.
- **Finance vocabulary** — `$1 buyout` 524 · `overage` 163
- **Procurement anchors** — `RFP` 370 · `E-rate` 1,250 · `board meeting` 512 ·
  `school year` 399

---

## Expected yield

**~1–3% of pool.** Above that, suspect false positives. Below it, suspect a
missing field or a pattern gap — not a missing keyword.

Adding keywords stops helping well before the data is exhausted: the final UBEO
calls harvest grew the pool **60%** and added **2%** signal.
