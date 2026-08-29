---
name: qbs-decision-maker-finder
description: Find who actually makes the buying decision at an account by reading CRM conversation history, then check whether that person exists as a contact and whether their buying role is set. Surfaces the common failure where reps log calls against whoever answered the phone while the real decision maker, named in the note, has no contact record at all. Use for any B2B client with call notes, meeting notes, or logged conversations — vertical-agnostic. Trigger on "who is the decision maker", "find decision makers", "are we talking to the right person", "missing contacts", "gatekeeper vs decision maker", "buying role", "who actually decides", "contact gaps", or any request to identify buying authority from CRM activity. Requires a client HubSpot PAT (see qbs-hubspot-private-app).
---

# Decision Maker Finder

Reps log a call against whoever picked up. The note frequently names someone
else entirely as the person who decides — and that person often has no contact
record. This finds them.

Three questions per conversation:

1. **Is the contact this call is logged against actually the decision maker?**
2. **If not, who is?**
3. **Is that person already in the CRM, and is their buying role set?**

Vertical-agnostic. Nothing here is specific to any industry.

---

## The one thing that makes this work

> **"Spoke with X" does not mean X decides.** It usually means X answered the phone.

This is the whole discipline. A first attempt built on "spoke with" patterns
produced 238 of 252 extractions from that phrasing alone — and on inspection
they were receptionists, operators, and people who transferred the call
onward. The regex had built a *gatekeeper detector* wearing a decision-maker
label.

Only **explicit authority language** identifies a decision maker:

| Trust | Language |
|---|---|
| **CONFIRMED** | "X is the decision maker", "X is the owner/president/CFO", "X signs off", "X handles [the category]" |
| **CONFIRMED** | "I am not the decision maker, you need X" — a disclaimer plus a name is the strongest signal of all |
| **STATED** | "need to speak with X", "referred me to X", "transferred me to X", "X is in charge of" |
| **NOT A SIGNAL** | "spoke with X", "talked to X", "X said", "POC X" |

That last row is a gatekeeper signal. Capture it separately if useful — knowing
who screens the call has value — but never write it as the decision maker.

---

## Preflight

Load `qbs-hubspot-private-app` for the token. Verify the portal
(`GET /account-info/v3/details`) before touching anything.

### Check how the client tracks this today — before claiming a gap

Run these before telling anyone their decision-maker data is missing:

```
contacts.hs_buying_role                  HAS_PROPERTY     ← the native field
contacts.* matching /decision|buying|role|authority|persona/
contact↔company association labels       (custom labels are common)
```

At UBEO: `hs_buying_role` was set on **2 contacts out of 1,089,825**. But six
legacy `scrole1`–`scrole6` Yes/No flags existed on 30,987 contacts with ~5,200
Yes values and unhelpful labels ("SCRole3"). Nobody could say what they meant.

**Ask the client what the legacy fields mapped to before declaring a greenfield.**
A migrated system often has the answer in a field nobody labelled.

---

## Properties

Same architecture as any QBS AI field set: one human-readable overview, several
structured handles.

| Property | Type | Purpose |
|---|---|---|
| `ai__decision_maker` | textarea | **The overview.** Name, confidence, role, in-CRM status, evidence, provenance. What a rep reads. |
| `ai__decision_maker_name` | text | Just the name — for matching and filtering |
| `ai__associated_contact_is_dm` | select | Yes / No — different person named / No contact associated / Unclear |
| `ai__decision_maker_in_hubspot` | select | Yes / No / Unsure |
| `ai__decision_maker_contact_id` | text | The matched contact (store the full record URL) |
| `ai__decision_maker_buying_role` | select | AlreadySet / NotSet / OtherRole / NoContact |

Create on every engagement object carrying conversation text — calls, meetings,
notes, tasks, emails.

### Overview format

```
<Name> [<CONFIDENCE>] - <role if stated> - <IN HUBSPOT | NOT IN HUBSPOT>
  - <evidence, quoted>
  [source: call id <N>, logged MM/DD/YYYY, logged against: <associated contact>]
  ** <why this determination was made>
```

Real example:

```
Renee Evans [CONFIRMED] - Office Administrator / CFO - IN HUBSPOT - Spoke with
Eric Curtis, one of the owners. Eric is not the key decision maker; he will
refer me to Renee Evans, the office administrator or CFO. [source: call id
115791424548, logged 08/27/2026, logged against: Eric Curtis] ** owner
explicitly names someone else as the decision maker
```

When no decision maker is established, say so — never invent one:

```
No decision maker established [UNRESOLVED] - Transferred to the wrong number;
connected to Brian at the IT support centre. Call cut short as a misdial.
```

---

## Stage 0 — Mine what the client already recorded, before reading anything

**Do this first. It is minutes of work and it beat days of reading.**

Reps with no field for "this person decides" type it into the only editable text
box in front of them: the contact's name.

```
firstname "Tomiko (DM)"          lastname "Leitner (DM)"
firstname "(Retired) Nancy"      lastname "Lasky (DM) (GONE)"
firstname "DO NOT EMAIL Katherine"
lastname  "Mansu (DM) (Replaced Tami F)"     <- succession, recorded in a name
```

At UBEO this yielded **2,088 contacts in two minutes** — 183 decision makers and
1,900 status findings — against 224 records read by hand over hours.

Search `firstname` and `lastname` for `(DM)`, `(GONE)`, `(RETIRED)`, `no longer`,
`DO NOT CALL`, `DO NOT EMAIL`, `(POC)`, `(left)`, `(replaced`. Then:

- **Verify literally.** A CONTAINS_TOKEN search for `DO NOT CALL` matches a
  contact genuinely named **Do Nguyen**. Re-check every hit with a real regex
  before you count it — at UBEO that removed 515 of 2,628 hits.
- **Never modify the name.** Write the AI fields only. The names feed
  personalization, dedupe and integrations; editing them is a separate decision
  for the client, and the migration must be safe to re-run.
- **Never overwrite a verdict that came from reading an engagement.** That is
  better evidence than a marker of unknown age.

Report the side effects too. Markers in `firstname` render in email greetings —
*"Hi DO NOT EMAIL Katherine,"* — and any enrichment tool that writes the name
field silently destroys the intelligence.

Also sweep for legacy free-text fields carried over in migrated bodies
(`SalesStrategy:`, `SalesChainID:`). **Measure before mining them:** UBEO's
`SalesStrategy` appears on 178,240 tasks and a 60-record sample contained *zero*
decision-maker statements — it is mostly revenue boilerplate. The one real hit
was already caught by the ordinary language sweep.

## Stage 1 — Find conversations, not dial attempts

**Most logged calls never reached a person.** At UBEO roughly 90% of the recent
window was voicemail, IVR, or a failed connection. Filtering only on "has a
body" produced a sample that was 93% non-conversations, and the first run's 7%
yield was a sampling artefact, not a data problem.

**Hard-exclude** — the dial never reached a human:

```
no live person · speaker 1 · automated greeting · welcome message
left a message · left a voicemail · leave a message · standard greeting
not in service · mailbox is full · office was closed · unable to answer
attempted to reach · attempted to contact · could not be completed
unsuccessful · insufficient information · no further details · press 1
did not answer · no answer · call failure · directing callers
```

**Hard-require** — evidence a person actually spoke:

```
spoke with · spoke to · s/w · talked to · tt · said · advised
mentioned · informed me · told me · POC · connected with
```

Plus a minimum length (~120 chars). At UBEO this took 1,000 raw calls down to
**650 genuine conversations** — and the yield rose from 7% to a real number.

## Stage 2 — Funnel to authority language

Of those conversations, only a fraction contain a statement about who decides.
Search the conversation set for:

```
decision maker · decides · signs off · approves · authority
is the owner · is the president · is the CFO · is the director
in charge of · handles the · responsible for
need to speak (with|to) · need to talk to · have to go through
referred me to · refer you to · transferred me to · put me through to
not the (right person|decision maker) · not in charge · not my area
```

At UBEO: **17 of 650 conversations** (2.6%). That is the real working set —
small, and worth reading properly.

## Stage 2.5 — Deduplicate before you read

**A migrated CRM stamps an account-level header onto every engagement for that
account.** The same sentence appears on ten records:

```
x64  "USE THE 202 298 4268 NUMBER TO CALL DM"
x52  "Mike Seay/DM - FLAVO Rx IS THE NAME OF THE COMPANY"
x36  "***HQ FOR 4 or 5 LOCATIONS AND GARY YANKANICH IS POC AND DM FOR ALL LOCATIONS***"
x11  "Linda POC and Trish the final decision maker"
```

Group by the normalised header text, read once, write the determination to every
record in the group. At UBEO 3,710 records collapsed to 1,702 determinations, and
the first 18 groups read covered **245 records — a 13.6x multiplier**.

### Strip call scripts first

The single largest "group" at UBEO was **1,761 records of one SDR call script**:

> *"Hi, this is _____ with UBEO Business Services… I was curious who typically
> oversees those areas for your organization." **Prospect Identifies Decision
> Maker** "Perfect. The reason for my call is…"*

It matched every decision-maker filter because the *script* discusses decision
makers. Nothing in it is about any real account. Detect templates by their
placeholders (`____`, `Hi, this is _`) and by any single text repeated across
hundreds of records, and drop them before ranking.

## Stage 3 — Read them

Patterns cannot finish this job. Three things defeat them, all common:

**Negation.** *"Eric is **not** the key decision maker"* — a pattern grabs Eric.
The sentence says the opposite.

**Transfer direction.** *"Spoke with Heather, who transferred me to Tamara"* —
Tamara is the target, Heather is the gate. A pattern takes whichever name comes
first.

**Name boundaries.** Pattern output from a real run included `wrong department`,
`has`, `speak directly`, `Paul after`, `Melissa from` — none of which are people.

Read each candidate and record: the name, their stated role, the confidence
tier, and one line on *why* you reached that determination. That last part is
what makes the field auditable.

### Can you infer authority from how the contact talks? Tested: no.

It is a reasonable idea — a person with authority says *"we went with Ricoh"*,
*"I handle the copiers"*, *"send me a proposal"* — so it was built and validated
against 220 hand-read calls where the answer was already known.

**It found 0 of 16.** The cause is structural:

```
hand-read calls containing FIRST-person authority ("I handle")  :   0 of 220
hand-read calls containing THIRD-person authority ("X handles") :  91 of 220
```

The notes are **AI-generated summaries, not transcripts**. First-person speech is
paraphrased into the third person before it is ever stored. Rebuilt as
coreference — *does the authority verb attach to the person who answered?* — it
reached **26% agreement**, failing the usual way by extracting `who`,
`person who`, `she`, `staff members`, `that Greg` as names.

Verbatim rep-written tasks were tested too, on the theory they escape the
summariser: **1 relevant hit in 96 sampled records.**

**Use inference to rank the reading queue, never to fill a field.** And be
careful quoting portal-wide counts for these phrases — summing `CONTAINS_TOKEN`
across four objects and several properties inflates them wildly ("I handle"
looked like 6,562; on tasks it is 56).

## Stage 4 — Resolve against the CRM

For each named decision maker, pull the **directly associated contacts first, then
every contact at the associated company**, and match. Searching only the company
roster reports `NoContact` for a call that has a contact but no company — a
fabricated gap.

Use `scripts/resolve_contact.py`. Do not hand-roll this; the matching rules below
were each paid for with a wrong answer.

### Why exact matching fails, and why loose matching is worse

Real misses from an exact matcher, all sitting in the CRM the whole time:

| Note says | CRM holds | Why exact fails |
|---|---|---|
| Amy Greenlee | Amy Greenlee **Holland** | married/second surname |
| Britney Hurlbert | **Brittany Hurlburt** | two spelling drifts |
| Eric Porter | **Erik** Porter | c/k variant |
| Krista Gallio | **Christa Galleo** | phonetic variant |
| Grace Cusimano | Grace **Cucumano** | transcription error |

The obvious fix — "allow one edit" — is worse than the problem. One edit apart sit
both **Eric/Erik Porter** (same person) and **Mark Jones/Mary Jones**,
**Kim/Tim Colbert**, **Alan Wright/Alan Bright** (different people). A false match
writes a real, wrong human being into a field a rep will act on. That is a more
expensive error than a missed match, which merely produces an enrichment task.

So the matcher scores rather than decides:

| Score | Meaning | Action |
|---|---|---|
| **3** | exact, containment, or phonetic equivalence | write it |
| **2** | near-spelling within tight guards | write it |
| **1** | plausible but genuinely ambiguous | **print it, write nothing** |
| **0** | no match | `NoContact` — a real gap |

The rules that produce those scores:

- **Containment either way** on the normalised full name — Amy Greenlee / Greenlee Holland.
- **Phonetic equivalence** on the first name (ph→f, ch→k, c→k, z→s, y→i, doubles
  collapsed) — Eric/Erik, Cathy/Kathy, Krista/Christa.
- **First-name containment** ≥3 chars — Jon/Jonathan.
- **Surname initial must match.** A surname whose *first letter* differs is a
  different family, not a typo: Wright/Bright, Green/Breen. Cusimano/Cucumano and
  Gallio/Galleo differ *inside* the word, which is how a real transcription slip
  behaves.
- **Length guard on first names.** Two-edit tolerance applies only when both first
  names are ≥6 characters. It lets through Sabina/Sabrina and Steven/Stephen; it
  keeps out Mark/Mary and Kim/Tim, which are too short to distinguish a typo from
  a different name.
- **Strip honorifics before matching.** A title routinely stands where a first
  name should be — `Pastor Halley` is Anthony Halley, `Dr. Amaker` is Corey
  Amaker, `Mrs. Cantwell` has no first name recorded at all. Church, school and
  medical accounts make this constant. Strip `Pastor|Rev|Father|Sister|Dr|Mr|
  Mrs|Ms|Prof|Deacon|Bishop|Rabbi|Coach|Principal`, then allow a bare surname to
  match on its own — but only when the surname is longer than four characters,
  or `Pastor Lee` starts matching every Leek and Leach at the account.
- **Single-token names never use containment.** Notes name a lone first name
  constantly — *"ask for Kim, she oversees print"*. Containment would match `Kim`
  to `Kim O`, `Kimberly Anderson` and `Kimura` alike, and `Dan` to `Danielle
  Smith`. A one-word name matches on **exact first name only**, and if several
  people at the account share it, it identifies nobody and drops to a flag.
- **Shared-prefix pairs score 1, never 2.** Britney/Brittany (same person) and
  Michael/Michelle (different people) are *identical* under every mechanical test:
  four-character shared prefix, three edits apart, same surname. Nothing separates
  them but human judgement, so the matcher refuses to guess and prints them.

`scripts/test_resolver.py` locks this in: 12 same-person pairs from live data must
match or flag, 18 different-people pairs must never match. **Run it before every
batch write.** It exits non-zero on any error.

```
PAT=<token> python3 scripts/test_resolver.py
```

### Then read the buying role

| Result | Meaning |
|---|---|
| `AlreadySet` | contains DECISION_MAKER — nothing to do |
| `NotSet` | **the fix list** — person is known, CRM doesn't say they decide |
| `OtherRole` | set to something else — review |
| `NoContact` | **the gap list** — enrichment target |

`hs_buying_role` is a **checkbox** (multi-select), so a contact can hold several
roles. Read before writing; do not clobber.

### Record the name variance

When the note's spelling and the CRM's differ, keep both in the overview —
`Eric Porter (CRM: Erik Porter)` — and set `ai__decision_maker_name` to the CRM
spelling so it filters against the contact record. The evidence keeps the note's
wording; the structured field keeps the CRM's.

---

## What the output is for

Two lists, and they are worth different things:

**`NoContact` — the enrichment gap.** A person your reps have spoken to, named
in a note, with no record. Name plus company is enough for ZoomInfo to append
email and direct dial. Without this, when the opportunity matures there is
nobody to sequence.

**`NotSet` — the segmentation fix.** The person exists and HubSpot doesn't know
they decide. Populating `hs_buying_role` turns a dead field into a filter the
whole team can use.

Two more things fall out for free, and clients tend to want them more than the
lists above.

**Opt-outs and do-not-call requests buried in note text.** *"Gina requested to be
taken off the call list."* *"He asked to be removed from the call list and not
contacted again."* These are compliance obligations sitting in free text where no
suppression process can see them. Three appeared in the first 64 records. Surface
them loudly.

**Buying structure.** Notes routinely reveal *how* the account buys, which decides
whether there is a decision maker to find at all: *"all contracts are handled
through the state"*, *"their corporate office in San Antonio manages those
services"*, *"individuals manage their own printer needs"*. A site that cannot
decide should not be worked as if it can.

A third thing falls out for free: **dead contacts.** *"Pedro informed me that
Judy Gilmore is retired"* — Judy is the contact the call was logged against.
Capture those; they are CRM hygiene nobody is paying for and everybody wants.

---

## Gates

**Before writing anything:**

- [ ] Read 10–15 extractions yourself. Every failure in the first run was found
      this way and none by aggregate statistics.
- [ ] No extracted "name" is a fragment — scan for trailing prepositions
      (`X from`, `X after`) and non-names (`has`, `wrong department`)
- [ ] `scripts/test_resolver.py` exits 0 — 12 same-person pairs match, 18
      different-people pairs do not
- [ ] Every `NOT IN HUBSPOT` verdict survived the scored match, not just an exact one
- [ ] Every score-1 near miss the writer printed was decided by hand before the
      batch was called done
- [ ] Negation and transfer direction were read, not assumed
- [ ] Records with no determinable decision maker say so explicitly

**Never write `hs_buying_role` on contacts without explicit client approval.**
Writing the AI fields on engagements is reversible and inert. Writing buying
roles onto contact records changes data the client's team and workflows depend
on. Report the `NotSet` list; let them approve the write.

---

## Reference: UBEO run

| Stage | Count |
|---|---|
| Calls sampled | 1,000 |
| ...that were genuine conversations | 650 |
| ...containing authority language | 17 (2.6%) |
| Contacts with `hs_buying_role` set, portal-wide | 2 of 1,089,825 |

Scaled to the full portal, the same funnel over every call in HubSpot produced an
**authority-language pool of 22,030** and, after the conversation filter, a
**reading queue of 3,779**. That is the honest size of the job: ~3,800 records a
human (or a careful model) has to read. There is no shortcut that preserves the
accuracy.

### The headline number

Across the first 64 records read at UBEO:

| | |
|---|---|
| Note names someone **other than** the logged contact | **42** |
| Logged contact **is** the decision maker | 12 |
| Unclear from the note | 8 |
| No contact associated at all | 2 |

**Roughly four in five conversations were logged against the wrong person.** Not
through carelessness — the rep logs the call against whoever the dialer dialled,
and the note faithfully records that someone else decides. The information was
always there; nothing read it.

Of the 38 decision makers actually named: **29 exist as contacts with the buying
role unset**, and **9 do not exist in the CRM at all**.

### What the first read batches actually contained

Of the first 10 read, **8 named a decision maker and 2 exposed dead contacts** —
people the CRM still lists at companies where they no longer work, or never did:

- *"Anna answered and confirmed Charlie does not work there"* — Charlie Arrington
  is the contact the call is logged against.
- *"Called for Deanna Lund, CFO, and was told she is not known at the company."*

Half of the 8 named someone who **was not in HubSpot at all**. Those are the
enrichment targets, and they are the reason the exercise pays for itself.

Pattern-only extraction on the same 650 got roughly **1 in 14** right at its
highest confidence tier. Budget for reading.
