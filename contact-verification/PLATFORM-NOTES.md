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

> Fix: clone it yourself. The repo is public, so this needs no credentials and is verified working:
> `git clone --depth 1 --branch main https://github.com/Quantum-Business-Solutions/Claude`

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
