# Hard-won facts, for any agent working on QBS automation

Everything here was **measured on 2026-08-30**, not inferred from documentation. Several items
contradict what the docs say, and two contradict what other agents (including me) asserted earlier
in the day. Where a claim was wrong, the correction is kept alongside it rather than quietly
replaced — the wrong version is usually the intuitive one, and someone will re-derive it otherwise.

---

## 1. Scheduled Routines are not like interactive sessions

A session fired by a Routine differs from the one you are reading this in, in two ways that make
naively-written automation fail **silently in about three minutes**:

**It has no git checkout.** An interactive session carries `session_context.sources`; a
routine-fired session's context has no `sources` key at all. Any step referencing a repo path dies
on the first command.

> Fix: clone it yourself:
> `git clone --depth 1 --branch main https://github.com/Quantum-Business-Solutions/qbs-contact-verification`
>
> Note what changed here on 2026-09-03: this repository is **private**, and an earlier version of
> this note asserted "the repo is public, so this needs no credentials." A clone from an
> interactive session still succeeds with no token in the environment - git read access is served
> by the session's git proxy, not by a credential you can see - so a local test proves nothing
> about a fired session's access. Do not assume; the clone step must halt loudly on failure.

**It has no MCP connector tools.** Not a bug, not an outage — a property of how the Routine was
created. `create_trigger` says so outright:

> this trigger stores no MCP connectors, so the sessions it fires will run without connector
> (`mcp__<server>__*`) tools

And its `connectors` parameter is **rejected for this organization**. The Routines UI on claude.ai
only lists first-party connectors (Gmail, Calendar, …), not custom MCP servers. **There is no way
to give a Routine a custom connector.** Anything depending on one cannot be scheduled — build it on
plain HTTPS instead.

*I sent Shawn to look for a Unipile connector in the Routines UI before checking this. It isn't
there and never was.*

## 2. Cloud egress reaches port 443 only

Measured: `api30.unipile.com:16072` → connection reset / TCP timeout. Same host on `:443` → open.
The agent proxy will establish a CONNECT tunnel and *then* reset TLS, so a partial success here
means nothing.

The MCP connector appeared to work around this only because it tunnels through Anthropic's own
proxy — which is exactly why it isn't available where you need it most.

Two ways out, in order of preference: use an API that is already on 443 (see §3), or put a relay
there. A Supabase Edge Function works well — source in `relay/index.ts`, deployed and verified.
Keep such a relay **GET-only, host-locked, and account-allowlisted**, and have callers pass their
own credential so the relay stores none.

## 3. Unipile v1 vs v2

| | v1 | v2 |
|---|---|---|
| host/port | tenant DSN on **:16072** (unreachable) | `api.unipile.com` on **443** |
| account id | in the query — `S6ua4Sf…` | in the **path** — must match `^acc_` |
| profile | `/api/v1/users/{slug}?linkedin_sections=experience` | `/v2/{acc}/users/{slug}?with_sections=linkedin_experience` |
| envelope | `items` | `data` |
| experience at | `work_experience` | **`specifics.experience`** |
| row shape | `{company, position, start, end}` | `{company:{id,name}, job_title, started_on, ended_on}` |
| current role | `end: null` | `ended_on` **absent** |
| company id | no | **yes** — use it to disambiguate same-name companies |
| search | `POST /api/v1/linkedin/search` with `api:"sales_navigator"` | `POST /v2/{acc}/linkedin/search` takes a **search URL**; Sales Navigator URLs are rejected by its parser |

**The trap:** a v2 profile request without `with_sections` returns **HTTP 200 with no experience at
all**. Not an error, not an empty array — the keys simply aren't there. v1 behaves the same way
without `linkedin_sections`. Any code that treats "no rows" as "no history" will fabricate results.
Assert the section is present before judging anything.

**Rate limits are published — read them, don't guess.** Every response carries
`x-ratelimit-limit`, `x-ratelimit-remaining` and `retry-after`, and a 429 body states it in words:
*"We only allow 100 requests. Retry in 16 minutes."*

Measured 2026-08-31: **100 requests per ~16-minute rolling window** — about 375/hour, ~9,000/day.
That is far more headroom than a fixed sleep implies, and a fixed sleep gets it wrong in *both*
directions: 3.5s spends the entire budget in six minutes and then stalls for ten, while a
defensive 10s throttles a run that had room to move. `unipile.py` now spreads the remaining
budget across the remaining window (`pace()`), and on a 429 sleeps the server's own
`retry-after` rather than an invented backoff.

Sizing that follows from it: **815 unverified contacts ≈ 2.2 hours of wall clock**, not weeks.

Never record a 429 as a finding about the record you were reading — and never let one demote your
transport either; see §3.

**v2 account IDs are unrelated to v1 account IDs.** Re-derive the allowlist; don't translate it.

## 4. `experience_preview` truncates — this one cost real money

Rows returned per profile, same key, same moment:

| profile | `experience_preview` | `experience` (v1) | `linkedin_experience` (v2) |
|---|---|---|---|
| williamhgates | 3 | 3 | 3 |
| satyanadella | 5 | 5 | 5 |
| sherylsandberg | **5** | **15** | **15** |
| jeffweiner08 | **7** | **24** | **24** |

The preview returns roughly the most recent handful. If someone carries several concurrent board or
advisory roles, their actual day job can fall outside it. Any logic that asks "is the CRM company
in this list?" then reads **absent** as **departed**.

In the QBS verification pipeline that meant real, callable contacts stamped *No Longer with
Company*. A sample of banked `no` verdicts found people still in the job we had ejected them from —
one of them the **Founder-CEO**, with 25 roles in his full history and his live one nowhere near
the first five.

**Correction worth keeping:** I first reported this as "v1 truncates history" and used it to argue
for v2. That was wrong. v1 returns the complete record when asked correctly. It was **our parameter
choice**, and it was equally wrong on both versions.

Full history costs nothing extra — same single request, one different parameter value.

## 5. Guard against it in code, not in prose

The pipeline already had a written rule to re-pull full history when the CRM company was missing
and the total count exceeded rows returned. It was still wrong in production, because the rule
lived in a skill file and depended on a model remembering it on **every single contact**.

Two lessons that generalise:

- **A rule a model must remember is not a guarantee.** Unattended and at volume, it will be skipped.
  Prefer making the failure impossible: always request the full section, and there is nothing left
  to remember.
- **Positive marker checks can't catch a superset token.** `linkedin_sections=experience` is a
  substring of `linkedin_sections=experience_preview`, so a "does the fix token exist?" guard passes
  on buggy code. You need a **forbidden**-token check for bugs of this shape.

And test the guard in both directions. Mine initially fired on clean code — it was matching the
comparison table in its own docstring. A guard that has only ever been seen passing is untested.

## 6. HubSpot specifics (portal 20682069)

- The evidence property is **`ai__contact_evidence`**. There is no `ai__li_evidence`.
- **Querying a property that doesn't exist returns an empty result, not an error.** I read that as
  "this contact has no evidence recorded" and nearly reported a data-integrity problem that did not
  exist. Verify the property name against `/crm/v3/properties/contacts` before drawing conclusions
  from an absence.
- **A workflow blanks `jobtitle` about 20 seconds after `hs_lead_status` is set to `Retired -
  Remove from All Lists` or `No Longer with Company`.** Observed on contact 136222503544: written
  18:22:04 by the integration, cleared 18:22:24 by AUTOMATION_PLATFORM. An immediate read-back
  therefore reports success and is still wrong — re-read ≥30s later on ejected contacts.
- `previous__company_domain_name` is `type=string fieldType=text`, **not** URL-typed. An earlier
  note claimed otherwise and two QA passes repeated it, one escalating it to a suspected hard bug.
- Check `sourceType` in `propertiesWithHistory` to see who wrote a value: `INTEGRATION` (our
  scripts), `AUTOMATION_PLATFORM` (a workflow), `CRM_UI_*` (a human).
- A workflow being absent from a **sample** is not evidence it is inactive. I concluded a workflow
  was dormant because the most recent `AUTOMATION_PLATFORM` write across 40 contacts was 2026-06-01;
  a single record then showed one on 2026-08-17. Query the property history directly.

## 7. Environment variables

Set on the **environment** (Quantum, `env_01TxD1DB6PTzpB6nQpEiFy88`) via the cloud icon above the
message box at claude.ai/code — there is no settings page.

**They are injected at container start.** A variable saved while a session is running is invisible
to that session forever, no matter how long you wait. Check `/proc/uptime` against when it was
saved before concluding it wasn't set. A newly-fired routine gets a fresh container and sees it.

Anthropic's docs advise against putting credentials here — there is no secrets store — but for an
unattended routine there is no alternative, so rotate on a schedule and keep keys out of chat
transcripts. Anything pasted into a conversation is burned.

## 8. Working method

- **Verify the part you depend on.** Another agent's summary of Unipile v2 was accurate on access
  and wrong for my use case; the field I actually needed (`ended_on`) had to be checked directly.
- **Don't let one clean story cover two bugs.** Three false ejections looked like one root cause
  until the row counts showed one of them had only 2 rows total — truncation couldn't explain it,
  and it turned out to be something else entirely.
- **Distinguish "I ran it" from "I read it."** Most of the expensive errors in this project came
  from confident claims that were never executed.

## 9. A verdict can be perfectly reasoned about the wrong person

Measured 2026-09-03, on the first attempt to validate live output against reality. Of 66 contacts
the routine had just verified, **63 carried a LinkedIn slug containing their own first or last
name; one did not**: CRM *Matt Eberhart* (`matt@query.ai`, Query.AI) carried slug `manthony`, which
resolves to **Matt Anthony** — a real Query advisor with dated, current rows at Query. So every
check the pipeline makes passed: the employer matched, the row was current, no competing role. It
banked a confident `yes` and wrote a native job title, all of it about a different human.

Nothing about the *verification* logic was wrong. The identity was wrong, upstream, in the CRM.

Two things worth carrying to any enrichment work:

- **Confidence in a match is not confidence in the subject.** Any pipeline keyed on a stored
  external identifier inherits every bad identifier in the source, and inherits it *silently* —
  bad-link errors do not look like errors, they look like your best results.
- **The failure mode was already documented and still shipped.** The skill file named this exact
  case and named an issue value for it. Prose does not run. It is now a function
  (`identity_doubt()` in `writeverdicts.py`) that preflight refuses to run without.

The check is deliberately advisory: vanity slugs, maiden names, initials and post-marriage handles
are all legitimate, so a mismatch raises `wrong_link_suspected` for a person and blocks the native
title write, rather than deciding. It also cannot catch a wrong link whose slug happens to carry
the right name — a `John Smith` URL pointing at the wrong John Smith passes. Sampling against
reality is still the only way to find those.

## 10. The ejection workflow does more than blank a title — it detaches the company

Measured 2026-09-03 on contacts 12002674829 and 1316559, from property history:

| when | property | new value | who |
|---|---|---|---|
| 14:41:32 | `hs_lead_status` | `No Longer with Company` | `INTEGRATION` (us) |
| 14:41:52 | `associatedcompanyid` | `''` | `CALCULATED` |
| 14:41:52 | `jobtitle` | `''` | `AUTOMATION_PLATFORM` |

So a portal workflow enrolls on that lead status and, twenty seconds later, **removes the company
association**. §6 recorded the title-blanking half of this; the association half is worse, because
it destroys the only pointer to the employer the person just left — and the mover pipeline reads
*live* associations to decide what to preserve. A mover processed even a minute after the verdict
therefore had nothing to detach, and `previous employer record unknown` was written as if the
contact had never had one.

Portal-wide effect, measured the same day: **450 contacts carry verdict `no`; 446 have neither
`ai__reassociated_on` nor `ai__pending_mover_to`, and 274 have no company association at all.**
Real people, read on LinkedIn, seen to have left, left pointing nowhere.

Two fixes, both in code:

- `movepipe.py` falls back to `propertiesWithHistory=associatedcompanyid` and takes the most recent
  non-empty value, so the previous employer is recovered after the workflow has detached it.
- `writeverdicts.py` **refuses** a `no` verdict that carries neither a destination (`newco`) nor an
  explicit `no_destination` reason. A refused record stays in the queue; a banked one never
  surfaces again, which is exactly how 446 people went quiet.

Sequencing that follows: set the lead status **away from** the ejected value before re-associating,
or the workflow may act on the write you are in the middle of making.

## 11. `previous__company_domain_name` validates as a URL while reporting `fieldType: text`

`GET /crm/v3/properties/contacts/previous__company_domain_name` returns `type=string`,
`fieldType=text`. Writing `fictiv.com` to it returns **HTTP 400**:

```
INVALID_URL  No protocol found. URL must start with 'http://' or 'https://'.
```

`https://fictiv.com` is accepted. So property metadata does not tell you the whole validation
story, and a bare-domain write is fatal — it took down a mover pass on its first contact.

**Correction to §6**, which said this property is "not URL-typed". The metadata says text; the API
validates a URL. Shawn was right that the portal has URL-ish fields and I was reading the schema
instead of testing the write. Test the write.

## 12. A mover's new employer may already be someone you know

A confirmed mover is a fresh prospect at their new employer — **unless the new employer is already
a current client, a former client, or has a meeting or open deal in flight**, in which case
stamping `ConnectandSell Prospect` mislabels an existing relationship and drops the contact into
cold-calling lists. `movepipe.dest_status()` reads the destination company's `lifecyclestage`,
`type`, associated deals and upcoming meetings, and returns one of the portal's own existing
statuses (`Current Client`, `Former Client`, `Open Opportunity`, `ConnectandSell Meeting Set`),
raising `destination_is_account` so a person confirms it. Verified firing in both directions: a
customer with six deals, a `type=Current Client` record and two companies with open deals all
diverted; today's eighteen mover destinations all came back clean prospects.

An open deal outranks `lifecyclestage`, which is hand-edited and goes stale. An upcoming meeting
outranks both.

## 13. The pacing that was documented was never running

`unipile.py` has a `pace()` function that reads `x-ratelimit-remaining` / `retry-after` and spreads
the remaining budget across the remaining window. `ROUTINE.md` described that behaviour as the
reason a run stays inside Unipile's limit. Both were wrong about what actually happened, for a dull
reason: **callers invoke the script once per contact**, so `RATE` was re-initialised to `None` on
every read and `pace()` was never called at all. Nothing paced anything. Throttling was handled
only *reactively*, by `rows()` honouring a 429 after the wall had already been hit.

That is why v2 exhausted itself partway through the 2026-09-03 run. Fixed by persisting the budget
to a small state file (`/tmp/.unipile_rate.json`, overridable with `UNIPILE_RATE_STATE`) so the
next invocation paces against the last one.

**Two bugs sat behind it, both of the same shape — an unbounded wait.**

`pace()` did `time.sleep(reset+2)` with no cap. Measured live: v2's reset came back as **79,751
seconds — 22.2 hours.** So the "correct" behaviour was to sleep 22 hours inside a scheduled job
with a three-hour budget. Not a pause: a silent stall, which is the precise failure this process
exists to prevent. `rows()` had the milder version of it, capping each retry at 1200s and so
waiting up to 80 minutes across four attempts.

The fix is not a smaller sleep, it is a different decision. **A reset longer than
`RUNG_SPENT_AFTER` (300s) means the rung is spent, not that you should wait** — so the ladder
demotes to the next rung immediately, which is the entire reason a ladder exists. Any single
pacing sleep is additionally capped at `PACE_CAP` (90s).

And a bug the fix itself introduced, caught by running it: `RATE` is module-level while the ladder
walks several rungs in one process, so v1 inherited v2's spent budget and the whole ladder went
down over a limit that did not apply to it. `_load_rate()` now resets the dict before loading.

**Operational consequence worth knowing:** v2 carries a ~22-hour lockout once spent. A run that
exhausts it has no v2 for the next day, and the relay is the only remaining rung. There is no
third. Report the rung split every run.

## 14. A version guard that ships inside the artifact cannot detect that the artifact is stale

`preflight.py` has a code-version guard: a table of markers every script must contain, and it
exits 3 if any is missing. It was built after a routine ran three-day-old code and reported a clean
list, and it has been described — by me, repeatedly, including in a routine prompt written this
afternoon — as the backstop that makes a fallback to an older repo safe.

It is not, and the test is trivial. The Claude repo's `main` at `f4169ed` predates the identity
check, the no-destination rule, the destination-account check, the `previous__company_domain_name`
protocol fix and the rate-limit fixes. Running **its own** preflight against the live portal:

```
ok   code version: all QA fixes present
...
PREFLIGHT PASSED for list 5243 - safe to run.
```

Of course it passes. The guard and the code are the same artifact, so an old checkout arrives with
an old list of requirements and satisfies it perfectly. The only visible difference was one line —
"issue vocabulary: all **15** code values" against 16 — which is a pass either way.

**The check has to live outside the thing it checks.** For a Routine that means the prompt, which
is versioned separately from the repository: grep the checkout for markers of the fixes that must
be present, and halt if any is missing. Markers currently required: `RUNG_SPENT_AFTER`,
`def identity_doubt(`, `def dest_status(`, `no_destination`,
`propertiesWithHistory=associatedcompanyid`.

This one nearly shipped as a footgun. An hour before finding it I had rewritten the routine to
permit a "loud fallback" to the older repo *specifically because* preflight would catch stale code.
It would not have caught it — and stale code plus a spent v2 budget is the 22-hour sleep from §13.

## 15. Mining a destination out of prose read negations as destinations

A QA pass re-read fifteen of one day's verdicts against LinkedIn: nine correct, four wrong, two
unverifiable. Every error traced to one place, and none of them to the employment judgement — on
the twelve records where dated rows could be compared against the reasoning, the reading of end
dates was right every time, including hard fractional-CMO cases.

`recoverdest.py` mines a departed contact's destination out of the prose in
`ai__contact_evidence`. Its pattern crossed sentence boundaries, so:

```
"...experience_preview: NOT at Digital Hands"   -> ('Digital Hands', None)
"No longer CEO at Laborie."                     -> ('Laborie',       None)
"LEFT NRI North America 06/2026. Do not call at NRI."  -> ('NRI',    None)
```

**It read a negation as a destination.** `moverqueue` and `movepipe` then attached three real
people to the employer they had just left, flipped the verdict from `no` to `yes`, stamped
`validated__linkedin_or_manually = Yes`, set lead status `ConnectandSell Prospect` and carried the
phone. One of them had "Do not call at NRI" in the same field. That is worse than doing nothing: it
hands an SDR a dial at the company the person left and marks it verified on the way out, so nobody
re-checks. Three of eighty-six in one day; indistinguishable in the CRM from a correct
re-association.

**Two failed fixes before the working one**, both worth keeping because the shapes recur:

- Judging the whole evidence string flags nearly every genuine mover — "LEFT `<old>`, then `<x>`,
  now `<new>`" contains a negation by construction.
- "A positive marker anywhere in the left window beats a negation" let a distant *"Now board chair
  roles only"* excuse an adjacent *"No longer CEO at Laborie"*.

What works is **nearest marker wins**: scan back 90 characters and take whichever of negation or
positive sits closest to the capture — plus a separate rule that a capture *containing* a negation
is never an employer name, since a positive marker can precede it ("Current row: NOT at ...").

One more trap, found the same way: **a trailing `\b` in an alternation silently kills any branch
ending in a non-word character.** `\b(?:now|...|mover\s*->)\b` never matches `Mover ->`, so a real
destination was rejected as negated. Spell the boundaries per-branch.

## 16. An advisory guard binds inconsistently, which is the same as not binding

The identity check (§9) raised `wrong_link_suspected` and refused the native title, but left the
verdict to the judge. In one run that produced both outcomes: Matt Eberhart (`manthony`) came out
`unreadable` and stayed callable, while **Michael Stella was EJECTED on a stranger's profile** —
slug `michaeldaecher`, whose Thought Industries CMO row matched Stella's company *and* title. The
guard fired identically in both cases; only the judge differed.

It now forces the verdict to `unreadable` — never `yes`, never `no` — because if you cannot say
whose profile you read, you know nothing about that person's employment. `identity_ok: true` plus
an `identity_note` is the escape hatch for the ~5% of slugs that are legitimately unrecognisable,
and it requires a positive check (headline, location, employer history matching the record), not
an assumption.

**And the check itself was nearly useless, for a reason worth internalising: it accepted a FIRST
name match.** `michael` is a substring of `michaeldaecher`, so the guard cleared the very record it
existed to catch. First names are shared by millions of people. The surname is the test.

Two mechanical notes from making it bind:

- **Blank a property, never omit it.** Omitting `ai__contact_verified_date` leaves whatever is
  already there, so a record forced to `unreadable` kept a verified date from the earlier wrong run
  and read as freshly confirmed while its verdict said otherwise. Same for `ai__job_title`, which
  held a different person's job.
- When a guard spots a wrong URL, **writing the finding into prose and leaving the wrong URL on the
  record means the same wrong human is read again tomorrow.** Contact 3247359 carried
  `anna-koblish-89a169134`, a freelance photographer, with the evidence noting "URL corrected to
  antony-koblish-28515643" — a correction that was never written to a field.

## 17. Yes — you can click through to the company and read its website

Asked directly: when a dated row tells you where somebody works, can you follow the company and
find its site? **Yes, and it is the better source.**

```
GET /api/v1/linkedin/company/{public_identifier}?account_id=...     (v1, via the relay)
GET /v2/{acc}/linkedin/company/{public_identifier}                   (v2)
```

Returns `website`, `industry`, `employee_count`, `locations`, `organization_type` and — usefully —
`acquired_by`. Verified live through the relay:

| destination | LinkedIn says | ZoomInfo said |
|---|---|---|
| Pivot180 | **pivot180.ai** | pivot180.com |
| Havoc | **havoc.co** | NO_MATCH |
| PADT, Inc | padtinc.com | padtinc.com |
| What Chefs Want! | whatchefswant.com | whatchefswant.com |

It beats a third-party lookup for the obvious reason: it is the company's own declared site, read
from the same source as the employment row, so it cannot disagree with the row that produced the
verdict. It also caught a case ZoomInfo got wrong (`.ai` not `.com`) and one it could not resolve
at all.

**The catch is the identifier.** The endpoint wants a LinkedIn public identifier or ID, not a
display name. On **v2 every experience row carries `company.id`**, so a mover's destination resolves
deterministically — capture it during the profile read and the lookup is exact. On v1 the rows carry
no id (`company_id: null`), so a slugified name is a GUESS: `moverqueue.li_website()` therefore
checks the returned `name` against the destination before accepting the website, because a wrong
company record is worse than none. Measured hit rate from names alone: 5 of 8 hard cases.

Two further fields worth wiring in and not yet used:
- `employee_count` — a two-person company is somebody's own consultancy, not an ICP account. That
  is currently inferred from stop-words in prose ("his own firm"), which is exactly the kind of
  guess this replaces with a number.
- `acquired_by` — how a rename like Market Resource Partners → pharosIQ stops reading as a
  departure, without a human recognising the brand.

## 18. The native job title is not written because nobody passes the flag

The mechanism has been correct for a while: `title_conf >= 0.95` plus verdict `yes` writes native
`jobtitle`, and it holds on read-back. Measured across one day's 169 `yes` verdicts:

| | |
|---|---|
| native `jobtitle` already matches `ai__job_title` | 88 |
| `ai__job_title` set, native **differs** — a rep reads the stale one | 37 |
| `ai__job_title` set, native blank | 4 |
| **no `ai__job_title` captured at all** | **40** |

Of the 37 differences, most are not stale data — they are **abbreviation noise the wrong way
round**: `ai__job_title` said "CMO" where the native field already said "Chief Marketing Officer",
or "Vice President Marketing" against "Vice President, Marketing". One appended the employer to the
title ("CMO, Finovifi"). Only about ten are genuine changes a rep would want (a VP who is now an
SVP, and one who is now a Digital Product Manager — a step DOWN, which matters just as much).

So the fix is not in the gate. **On a `yes` verdict where the title was read off the end-null row,
`title_conf` 0.95 is the DEFAULT, not an exception** — that is precisely what the 0.95 definition
already says, and the judge simply wasn't passing the flag. Two rules go with it, because the native
field is what appears in the sidebar, the screen-pop and every export:

- Write the **full form**, never the abbreviation. "Chief Marketing Officer", not "CMO".
- Never append the employer to the title. The company has its own field.
