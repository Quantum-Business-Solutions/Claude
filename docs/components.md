# Component reference and live verification

Every rule in these modules comes from an API behaviour that contradicts the
obvious implementation. Each was verified against live data on 2026-08-29, not
just against fixtures. **177 tests.**

| Module | Job | Verified against |
|---|---|---|
| `normalize.py` | LinkedIn URL canonicalization, identity guards | 2,000 live contacts + full 1,136-contact list |
| `ledger.py` | Cap accounting, HubSpot date arithmetic | Live task ledger; DST dates |
| `verify.py` | The Reading Rule | Live Unipile profile (Micheline Nijmeh) |
| `posts.py` | Post selection and comment dedupe | Shawn's live comment feed |
| `errors.py` | Unipile response classification | Real error shapes seen this session |

## `posts.py` — comment dedupe

Three live behaviours, each of which breaks the obvious implementation.

**Per-post reads miss replies.** `GET /posts/{id}/comments` returns top-level
comments only. On activity `7495818623802916864` the post reports
`comment_counter: 11`, the comments list returns `total_items: 8` with
`cursor: null` — "complete" — and Shawn's own comment is one of the three
missing replies (comment `7498144322144481280`, `thread_id`
`7495910984549683200`). A per-post check reports "Shawn has not commented"
about a post he commented on four days earlier.

Fixed by reading `GET /users/{provider_id}/comments`: one call, includes
replies, cheaper. Confirmed live — that reply appears in the feed.

**The join key is not the post's `id`.** `Comment.post_id` matches the numeric
tail of `social_id`. Real pair: `urn:li:ugcPost:7495561989247856640` has
`id: 7495561990287826944`. Joining on `id` silently returns False for every
ugcPost and groupPost.

**The feed paginates.** Shawn's is **26 pages** at `limit=25`. Reading page one
builds a set covering his newest 25 comments and silently re-comments on
everything older — a partial dedupe set is worse than none, because it looks
authoritative. `commented_post_ids` now raises `IncompleteDedupeError` when
`pages_fetched < page_count`.

Also excluded: reshares (`parsed_datetime` is the *reshare* time, and the text
we would score is the resharer's one-liner), private group posts
(`author.id` is None and the comment is invisible to the prospect's network),
posts with no parsable timestamp, and future timestamps — `article.published_at`
carried a 2028 date on a same-day post.

## `verify.py` — the Reading Rule

Live results against the Nijmeh profile:

| CRM company | Verdict | Tenure |
|---|---|---|
| ThoughtSpot | `yes` | 1.5y |
| Thoughtspot Inc. | `yes` | 1.5y |
| JFrog | `moved` | — |
| Zscaler | `moved` | — |
| Acme Widgets | `moved` | — |

**A missing `work_experience` key raises `InstrumentError` and is never a
verdict.** Omitting `linkedin_sections=experience` returns HTTP 200 with the
key absent; a parser mapping that to `no` would write "No Longer with Company"
across the CRM from one missing query parameter.

Only `company`, `position`, `start` and `end` are dependable —
`company_id`, `status` and `location` are absent on many live entries. Dates
are US-format strings, not ISO. Entries are **not** chronological, so anything
taking `work_experience[0]` is right by accident. Current roles are a **set**:
senior people hold an operating role plus board seats.

Tenure runs from the earliest start at the matched employer so an internal
promotion does not reset the clock, and is flagged low-confidence when roles
overlap — one real profile carries three overlapping roles at one company.

## `errors.py` — response classification

| Response | Action |
|---|---|
| `401 invalid_credentials` (the live Sales Nav failure) | **halt** |
| `400 invalid_parameters` | **halt** — our request is wrong; repeating it won't help |
| `422 invalid_recipient` (slug passed to `/posts`) | skip this candidate |
| `422 already_invited_recently` | skip, **but still write the CRM record** |
| `429 too_many_requests` | stop for the day |
| `200` with `usage: 90` | **stop for the day** |
| unrecognised error | **halt** |

Two things make this harder than reading a status code. The only authoritative
quota signal is `usage` in the **success** body, firing at 50/75/90/95 — a path
checking status codes alone discards it. And the MCP passthrough returns the
body only, **no headers**, so `Retry-After` and `X-RateLimit-*` are unreadable
on the one transport that works from a container.

`already_invited_recently` sets `log_anyway`: it is not a failure, and skipping
the CRM write burns that prospect again on every future run.

Unrecognised errors halt rather than retry. Guessing through an unknown failure
mode on a live LinkedIn account is how accounts get restricted.
