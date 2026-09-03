"""Configuration, constants and doctrine shared by both LinkedIn routines.

Everything that used to be prose in the Cowork skills lives here as data, so a
run cannot reinterpret it. Credentials come from the environment only and are
never written to disk, HubSpot, or a report.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo

# --- Identity -------------------------------------------------------------

HUBSPOT_PORTAL_ID = "20682069"
SHAWN_OWNER_ID = "103243559"

# NOTE: there is deliberately no UNIPILE_BASE constant here. The tenant DSN
# carries a non-standard port (16072) that this environment cannot reach, and
# a constant in that form is what kept both routines dark for twelve weeks.
# The base URL is built by `unipile.base_url()`, which puts the host on 443
# and moves the port into a `?port=` query parameter.

#: The only account either routine may send or comment from.
#:
#: Aligned to v2 on 2026-08-30. v2 is the primary transport and lists exactly
#: ONE Shawn account, whose metadata.v1_account_id is this value — so pinning
#: it here makes the v1 fallback drive the same LinkedIn session v2 drives.
#: It previously pinned S6ua4SfUT4SMRFZFOmyUzQ, which meant the two transports
#: acted as two different sessions of the same person: the shape that produces
#: errors/multiple_sessions, which `errors.FATAL` classifies as page-a-human.
SHAWN_ACCOUNT_ID = "7lBoyXuETqKdiJYLj5HBGA"
#: Member IDs are immutable; slugs are user-changeable. Assert on both.
SHAWN_PROVIDER_ID = "ACoAAAGv8WABzhfWcURPIaBDzbgiEWX5e781Etw"
SHAWN_PUBLIC_IDENTIFIER = "shawnpetersonquantum"

#: Shawn's LinkedIn is connected to Unipile TWICE and both sessions are live
#: on one login — a restriction risk in itself, since the API's 401 enum
#: includes errors/multiple_sessions (which `errors.FATAL` treats as
#: page-a-human).
#:
#: Verified live 2026-08-30: both ids resolve, both return his seven dated
#: roles, and both report the same immutable member id — so `assert_identity`
#: cannot tell them apart. Only the id itself distinguishes them:
#:
#:     7lBoyXuETqKdiJYLj5HBGA   created 2026-05-10   <- v2 maps here; we send here
#:     S6ua4SfUT4SMRFZFOmyUzQ   created 2026-03-09   <- STALE, safe to disconnect
#:
#: An earlier constant here recommended disconnecting 7lBoy… That is now
#: WRONG and must not be acted on: v2 maps to that account, so disconnecting
#: it breaks the primary transport.
#:
#: v2 settles which one the code uses; disconnecting the other is Shawn's
#: action and does not block anything. Preflight reconciles the two versions
#: on every run so a future divergence is loud rather than silent.
SHAWN_V1_ACCOUNT_IDS = ("S6ua4SfUT4SMRFZFOmyUzQ", "7lBoyXuETqKdiJYLj5HBGA")

#: Colleagues' accounts in the same Unipile workspace. Sending from one of
#: these puts QBS outreach out under someone else's name.
COLLEAGUE_ACCOUNT_IDS = frozenset({
    "4fi7iaAuRRmRpzl4G8Dqjg",
    "9eK50zZlT2qVr0oCo0NJVg",
    "F5Y_Hhe_TCO94_hkWXmCKg",
    "oCJmihYGQJ-wsaA0bgW_aQ",
    "xgfVW4VBRri7sQ9tDmSGAw",
})

def assert_send_account(account_id: str) -> str:
    """Allowlist gate for every send/comment path.

    A denylist fails OPEN: one API key spans seven accounts and five people,
    so the moment a sixth person connects, their id is absent from any
    hardcoded blocklist and the guard silently passes. Only one account is
    ever correct, so assert equality.
    """
    if account_id != SHAWN_ACCOUNT_ID:
        raise PermissionError(
            f"Refusing to act as account {account_id!r}. The only permitted "
            f"send/comment account is {SHAWN_ACCOUNT_ID} (Shawn Peterson). "
            "This key also spans colleague and client identities."
        )
    return account_id

TIMEZONE = ZoneInfo("America/Chicago")

# --- Unipile API facts (verified live 2026-08-29) -------------------------

#: Dedupe endpoint. Per-post comment reads return TOP-LEVEL COMMENTS ONLY —
#: replies need a separate &comment_id call. Proved: on activity
#: 7495818623802916864 the post reports comment_counter 11, the comments list
#: returns total_items 8 with cursor null ("complete"), and Shawn's own
#: comment is one of the 3 missing replies. A per-post dedupe therefore says
#: "Shawn has not commented" about a post he commented on. This endpoint
#: returns his comments across ALL posts including replies, in one call.
SELF_COMMENTS_PATH = "/users/{provider_id}/comments"

#: /users/{id}/posts REJECTS the vanity slug with 422 invalid_recipient — it
#: requires the provider id (ACo…/ADo…), or a numeric id with is_company=true.
#: Note the asymmetry: GET /users/{slug} (profile) DOES accept a slug.
#: This is why the roster must carry the member ID, not just a URL.
POSTS_REQUIRE_PROVIDER_ID = True

#: Omitting this returns HTTP 200 with NO work_experience key at all. The
#: Reading Rule then has no input, and a parser that maps "no current role
#: matches" to `no` would write LEAD_STATUS_MOVED across the CRM. A missing
#: key is an INFRASTRUCTURE FAULT, never a verdict. Do not use "*" — it
#: returns ~20KB of skills/education/recommendations for no benefit.
PROFILE_SECTIONS_PARAM = "experience"

#: Post timestamps: there is no `created_at`. `date` is a relative string
#: ("3d", "1w"). Use `parsed_datetime` (absolute ISO). On a reshare,
#: parsed_datetime is the RESHARE time, so a freshness window happily admits
#: someone resharing months-old content, and the draft would be scored
#: against the resharer's one-line commentary rather than the substance.
#: `article.published_at` is garbage (a 2028 date observed).
POST_TIMESTAMP_FIELD = "parsed_datetime"
SKIP_REPOSTS = True

#: Group posts appear in the feed with author.id == None, and private groups
#: make a comment invisible to the prospect's network — worthless for warming
#: and a None-comparison crash waiting to happen.
SKIP_POST_URN_PREFIXES = ("urn:li:groupPost:",)

# NOTE: `post_join_key` lives in `posts.py`. The copy here lacked that one's
# None guard and raised AttributeError where the live version returns None.

# NOTE: the comment self-match field lives in `posts.SELF_MATCH_FIELD`.

#: Free, provider-side idempotency check that does not depend on the HubSpot
#: logging path being alive — which matters, since that path has been dead
#: since 2026-06-01. Profile carries invitation: {type, status}. A live case
#: exists right now: Jared Nimblett was invited 2026-08-28, is still PENDING,
#: and routes to FREE_INMAIL today because the CRM guard property is empty.
SKIP_ON_PENDING_INVITATION = True

# NOTE: the Unipile error taxonomy lives in `errors.py` and ONLY there. A
# second copy sat here and disagreed with it — 2 retryable slugs against 6,
# 4 fatal against 25 — i.e. two sources of truth for the most safety-critical
# classification in the system, with the dead copy being the wrong one.
# `errors.py` is checked against the published enum by tests/test_errors.py.

# --- HubSpot task types ---------------------------------------------------

TASK_TYPE_INVITE = "LINKED_IN_CONNECT"
TASK_TYPE_INMAIL = "LINKED_IN_MESSAGE"
TASK_TYPE_DM = "LINKED_IN"

#: Every task type either routine writes. Tally queries must cover all three:
#: the engagement routine logs LINKED_IN, and so does the outreach routine for
#: DMs, so neither can count on type alone to isolate its own work.
ALL_LINKEDIN_TASK_TYPES = (TASK_TYPE_INVITE, TASK_TYPE_INMAIL, TASK_TYPE_DM)

# --- Verification (the Reading Rule) --------------------------------------

#: The live option set on ai__li_still_at_company, read from the portal
#: schema on 2026-08-29. NOTE: the qbs-linkedin-daily runbook documents only
#: yes/no/unreadable — that vocabulary is stale. Writing only three values
#: makes outreach data incomparable with the contact-verification routine,
#: which is the opposite of what the runbook says it wants.
VERDICT_YES = "yes"
VERDICT_NO = "no"
VERDICT_MOVED = "moved"
VERDICT_NO_PROFILE = "no_profile"
VERDICT_UNREADABLE = "unreadable"

VERDICTS = (VERDICT_YES, VERDICT_NO, VERDICT_MOVED, VERDICT_NO_PROFILE, VERDICT_UNREADABLE)

#: Written to the ai__ namespace, which the overwriting portal workflows
#: (274857276, 274857511) and Data Enrichment do not touch.
AI_STILL_AT_COMPANY = "ai__li_still_at_company"       # select, 5 options above
AI_CONTACT_EVIDENCE = "ai__contact_evidence"           # textarea
AI_VERIFIED_DATE = "ai__contact_verified_date"         # date
AI_LAST_ATTEMPT_DATE = "ai__li_last_attempt_date"      # date
AI_TENURE_YEARS = "ai__li_tenure_years"                # number
AI_ROLE_CHANGED = "ai__li_recent_role_change"          # select: yes/no
AI_JOB_TITLE = "ai__job_title"                         # text — LinkedIn-verified title
AI_REASSOCIATED_ON = "ai__reassociated_on"             # date

#: BUG IN THE RUNBOOK: qbs-linkedin-daily Step 4c says to set this to the
#: string "LinkedIn (Unipile work_experience)". The property is type NUMBER
#: ("Sources Confirming This Contact"). That write fails or coerces badly.
#: It is a COUNT of corroborating sources, not a source label.
AI_SOURCES_CONFIRMING = "ai__sources_confirming"       # number

#: Review-queue properties, shared with the contact-verification routine.
AI_ISSUE = "ai__verification_issue"                    # select
AI_ISSUE_NOTE = "ai__verification_issue_note"          # textarea
AI_ISSUE_ON = "ai__verification_issue_on"              # date

#: Stripped from both sides before comparing employers.
COMPANY_SUFFIXES = (
    "incorporated", "inc", "llc", "l.l.c.", "corporation", "corp",
    "limited", "ltd", "company", "co", "holdings", "holding", "group",
    "plc", "gmbh", "sa", "nv", "bv", "ag", "pty",
)

# --- Screening ------------------------------------------------------------

# NOTE: NICKNAMES lives in `normalize.py`, which holds 45 entries against the
# 12 duplicated here. normalize's is the one slug matching actually uses.

#: 'partner' was previously excluded here but accepted by SENIOR_TITLE_TOKENS
#: — 557 CAS Prospect contacts sit in that gap. Included, since the title
#: re-check downstream is the stricter gate.
SENIORITY_ALLOWED = frozenset({"executive", "owner", "vp", "director", "partner"})

#: Verified titles at or above this line qualify. Checked against the title
#: read off LinkedIn, because hs_seniority can be years stale.
SENIOR_TITLE_TOKENS = (
    "chief", "head of", "president", "founder", "owner", "partner",
    "vp", "vice president", "svp", "evp", "cro", "ceo", "coo", "cfo",
    "cto", "cmo", "cio", "director",
)

#: Junior signals that disqualify even when hs_seniority says otherwise.
JUNIOR_TITLE_TOKENS = (
    "specialist", "coordinator", "analyst", "assistant", "intern",
)

#: Functions that still count as buying roles after a promotion or lateral.
BUYING_FUNCTIONS = ("sales", "revenue", "marketing", "operations", "growth", "demand")

#: Dedupe preference when several contacts share a company.
SENIORITY_RANK = ("executive", "owner", "vp", "director")
FUNCTION_RANK = ("sales", "revenue", "marketing", "operations")

COMPETITOR_HEADLINE_TOKENS = (
    "hubspot consultant", "revops consulting", "sales training", "marketing agency",
)

EXCLUDED_COMPANY_IDS = frozenset({
    "7311932261",     # Quantum Business Solutions
    "53557064041",    # HubSpot
    "53539920425",    # ConnectAndSell
})

EXCLUDED_COMPANY_NAME_TOKENS = (
    "marketing", "advertising", "agency", "consulting", "cardone",
)

EXCLUDED_INDUSTRIES = ("MARKETING_AND_ADVERTISING", "PUBLIC_RELATIONS_AND_COMMUNICATIONS")

#: Freeform industry substrings that also disqualify.
EXCLUDED_INDUSTRY_TOKENS = ("advertising", "marketing")

# --- Outreach routine -----------------------------------------------------

#: INTERNAL VALUE, not the label. The label is "CAS Prospect"; the internal
#: value is "ConnectandSell Prospect". Verified live 2026-08-29:
#:   hs_lead_status EQ "CAS Prospect"            -> 0 contacts
#:   hs_lead_status EQ "ConnectandSell Prospect" -> 126,145 contacts
#: HubSpot returns 0 for an invalid enum VALUE but errors on an invalid
#: property NAME, so this class of bug fails completely silently. Never
#: hardcode a label. resolve_lead_status() re-checks against the live option
#: set on every run and halts if it is absent.
REQUIRED_LEAD_STATUS = "ConnectandSell Prospect"

#: Internal value (label is "No Longer with Company - Needs Updated").
LEAD_STATUS_MOVED = "No Longer with Company"

VERIFICATION_UNIVERSE_LIST_ID = "5243"
VERIFIED_CALLABLE_LIST_ID = "8260"


CHANNEL_DM = "DM"
CHANNEL_FREE_INMAIL = "FREE_INMAIL"
CHANNEL_PAID_INMAIL = "PAID_INMAIL"
CHANNEL_INVITE = "INVITE"
CHANNEL_SKIP = "SKIP"

CHANNEL_TASK_TYPE = {
    CHANNEL_INVITE: TASK_TYPE_INVITE,
    CHANNEL_FREE_INMAIL: TASK_TYPE_INMAIL,
    CHANNEL_PAID_INMAIL: TASK_TYPE_INMAIL,
    CHANNEL_DM: TASK_TYPE_DM,
}

FREE_OP_MARKER = "[FREE-OP]"
UNVERIFIED_MARKER = "[UNVERIFIED-EMPLOYMENT]"

# Templates are sent verbatim. Editing them changes what prospects receive.
TEMPLATE_DM = (
    "Hey — figured I'd reach out since we're connected. Quick context: we do "
    "HubSpot RevOps consulting for growth teams, lots of automation and "
    "attribution work. Curious what's been top of mind for you lately — happy "
    "to swap ideas if anything overlaps. No agenda."
)

TEMPLATE_INVITE = (
    "We work with growth leaders just like yourself to maximize HubSpot and "
    "drive automation. Would love to connect and swap notes on what you're "
    "working on. Open to a quick chat?"
)

TEMPLATE_INMAIL = (
    "We are working with growth leaders, just like yourself to maximize HubSpot "
    "and its capabilities to help drive decisions, growth and automation. Last "
    "we showed, you had HubSpot, but I know things can change quickly in today's "
    "environment. When would work best to hop on a quick call and discuss HubSpot "
    "or other key initiatives you are working on to drive growth? If easier, here "
    "is my meeting link: meetings.hubspot.com/shawn-peterson"
)

INMAIL_SUBJECT = "HubSpot"


@dataclass(frozen=True)
class OutreachCaps:
    """Daily and rolling send limits.

    NOTE: the source runbook is internally inconsistent on the daily stop
    threshold — Step 0d stops at a total of 70, while the caps table and stop
    conditions cite a combined ceiling of 100. Both are encoded; `daily_stop`
    is the one that actually halts a run. Raise with Shawn before changing.
    """

    invites_per_day: int = 20
    invite_channel_cutoff: int = 15
    paid_inmails_per_day: int = 25
    free_inmails_per_day: int = 15
    #: The per-channel caps sum to 60, so the runbook's daily_stop of 70 and
    #: combined ceiling of 100 could NEVER fire — both were dead code, and the
    #: "70 vs 100 contradiction" was a decoy. The real binding constraint has
    #: always been target_high. A cap that cannot be reached is not a safety
    #: net; it is a false one. __post_init__ now asserts reachability.
    daily_stop: int = 60
    target_low: int = 15
    target_high: int = 20

    def __post_init__(self) -> None:
        channel_sum = (
            self.invites_per_day + self.paid_inmails_per_day + self.free_inmails_per_day
        )
        if self.daily_stop > channel_sum:
            raise ValueError(
                f"daily_stop={self.daily_stop} is unreachable: the per-channel "
                f"caps sum to {channel_sum}, so the stop condition can never "
                "fire. Lower daily_stop or raise a channel cap."
            )
        if self.invite_channel_cutoff > self.invites_per_day:
            raise ValueError("invite_channel_cutoff must not exceed invites_per_day")

    weekly_invites_zero: int = 100
    weekly_invites_reduced: int = 80
    weekly_invites_reduced_to: int = 5
    weekly_invites_note: int = 60

    monthly_free_op_zero: int = 50
    monthly_free_op_reduced: int = 40
    monthly_free_op_reduced_to: int = 2
    monthly_free_op_note: int = 30


@dataclass(frozen=True)
class OutreachThresholds:
    """Stop conditions expressed as ratios of the candidates examined."""

    max_invalid_recipient_rate: float = 0.30
    #: A high `no` rate is expected and is NOT a stop condition. But the "49%
    #: baseline" in the runbook does not match the portal. Live cumulative
    #: distribution over 2,842 verified contacts (2026-08-29):
    #:   yes 1,962 (69%) | no 431 (15%) | unreadable 435 (15%)
    #:   moved 7 | no_profile 7        -> all non-yes = 31%
    #: The real `no` rate is ~15%, not 49% — that figure looks like one run
    #: generalized into doctrine. Consequence: a 40% unreadable ceiling was
    #: calibrated against the wrong baseline. Against a 15% norm, 40% is far
    #: too loose to catch an instrument failure. Tightened to 0.25; revisit
    #: once the routine produces its own run-level history.
    max_unreadable_rate: float = 0.25
    max_single_channel_rate: float = 0.50
    max_unipile_errors: int = 2
    min_candidates: int = 5
    min_connections_count: int = 30
    #: Skip anyone with a meeting booked inside this window.
    recent_meeting_days: int = 180
    #: Rolling scan: extra pages when the pool runs thin.
    max_extra_pages: int = 5
    #: HubSpot search caps `limit` at 200 and the `after` offset at 10,000.
    #: Always read the response's exact `total`; never len(results) — with
    #: page_size == a cap value, a count silently saturates at the ceiling.
    page_size: int = 200
    max_search_offset: int = 10_000
    #: Hard HubSpot limit: 6 filters per filterGroup. The qualification set
    #: uses 5, so there is exactly one slot of headroom.
    max_filters_per_group: int = 6
    runway_warning_margin: int = 500


# --- Engagement routine ---------------------------------------------------

WATCH_LIST_NAME = "LinkedIn Watch — Sales Nav"

#: Human-readable subject only. DO NOT COUNT ON IT.
#: HubSpot's CONTAINS_TOKEN is a case-insensitive, order-independent,
#: unanchored AND-of-whole-tokens — not a prefix match. Verified live:
#:   "LinkedIn Free OP InMail —" -> 30 ... and so does "InMail OP Free LinkedIn"
#: The em dash is stripped by the tokenizer (harmless but inert). So this
#: prefix really means "linkedin AND engagement anywhere in the subject", and
#: is contaminated by hand-typed tasks: 6 unrelated CALL/TODO subjects already
#: match "Engagement", e.g. "Call re: marketing engagement. See email".
#: Historical subjects also use five inconsistent variants, so no subject rule
#: can reconstruct history either.
TASK_SUBJECT_PREFIX = "LinkedIn Engagement —"

#: Count on THIS instead — a structural marker written into the task body that
#: no human types by hand. Cheap, needs no new property, and is exact.
TASK_LEDGER_MARKER = "qbs-ledger:engage-v1"

#: Comment caps. Separate from the outreach caps: a comment is far lower risk
#: than an invite or InMail, but it is still a public action under Shawn's
#: name, and LinkedIn throttles comment volume independently.
COMMENTS_PER_DAY = 8
COMMENTS_PER_RUN = 4

#: Local posting window, checked PER ACTION rather than once per run — a run
#: starting at 17:55 must not place its next comment at 18:02 after a pause.
ACTIVE_HOURS = (7, 18)

#: Posts we must NEVER comment on, and why this exists.
#:
#: The first live run of engage.py surfaced, as an eligible candidate, a VP of
#: Marketing's post reading "After 12 years, today is my last day at Thomson
#: Reuters." Every mechanical guard passed: fresh, original, not yet
#: commented, comments enabled. A HubSpot-RevOps comment under that post
#: would have been tone-deaf in public, under Shawn's name, on a prospect.
#:
#: Freshness and dedupe are necessary and not sufficient. A post can be
#: perfectly eligible and completely wrong to engage with, so content is
#: screened too. These patterns are phrase-level rather than keyword-level:
#: "last day" alone also matches "last day of the quarter".
#:
#: A departure post is ALSO the most valuable enrichment signal LinkedIn
#: gives us -- the person is a mover before any CRM knows it -- so these are
#: FLAGGED for the record rather than merely skipped.
SENSITIVE_POST_PATTERNS = (
    (r"\b(?:my )?last day (?:at|with|working)\b", "departure"),
    (r"\bI(?:'m| am) leaving\b", "departure"),
    (r"\bafter \d+ (?:great |wonderful |incredible |amazing )?years? (?:at|with)\b",
     "departure"),
    (r"\b(?:accepted|starting|joining|joined) (?:a |my )?new (?:role|chapter|"
     r"journey|position|adventure)\b", "job change"),
    (r"\bnext chapter\b", "job change"),
    (r"\b(?:laid off|impacted by (?:the )?(?:recent )?layoffs?|"
     r"part of the layoffs?|role was eliminated)\b", "layoff"),
    (r"\b(?:open to work|seeking new opportunities|looking for my next)\b",
     "job seeking"),
    (r"\b(?:passed away|passing of|in loving memory|rest in peace)\b",
     "bereavement"),
    (r"\b(?:my|his|her|their) (?:cancer|diagnosis|chemo|surgery)\b", "health"),
    (r"\b(?:we are|we're|I am|I'm) (?:heartbroken|devastated|grieving)\b",
     "bereavement"),
)
OUTREACH_LEDGER_MARKER = "qbs-ledger:outreach-v1"

#: HubSpot sets hs_createdate and it cannot be wrong. hs_timestamp is the DUE
#: DATE and is writer-controlled — the Jun 1 batch wrote an identical
#: hs_timestamp to all 19 rows. Bucket the daily cap on hs_createdate.
CAP_DATE_PROPERTY = "hs_createdate"

#: Stable LinkedIn member ID (== Unipile provider_id). Already exists in the
#: portal and is UNIQUE, so no custom property is needed: keying on this means
#: a prospect who changes their vanity URL never drops off the watch list.
PROVIDER_ID_PROPERTY = "hublead_linkedin_member_id"

#: Unique identity properties, verified against the portal schema. Any of
#: these is safe to upsert on; hs_linkedin_url is NOT unique and must not be
#: used as an upsert key. This resolves watch-sync audit blocker #2.
UNIQUE_IDENTITY_PROPERTIES = (
    "hublead_linkedin_member_id",          # stable member ID — preferred key
    "hublead_linkedin_public_identifier",  # slug — changeable, still unique
    "hublead_linkedin_urn",
    "linkedin_profile_url__unique_value",  # the unique profile-URL property
)

#: Upsert key. Uniqueness is necessary but NOT sufficient — coverage decides
#: whether an upsert matches or mass-creates duplicates. Live coverage over
#: 153,330 contacts, measured 2026-08-29:
#:   linkedin_profile_url__unique_value   123,471  (80.5%)  <- key
#:   hublead_linkedin_public_identifier       295  ( 0.19%)
#:   hublead_linkedin_urn                     294  ( 0.19%)
#:   hublead_linkedin_member_id                29  ( 0.02%)  <- do NOT key on
#: Keying on the member ID would miss ~99.98% of contacts and create a
#: duplicate for each — exactly what watch-sync blocker #2 exists to prevent.
UPSERT_KEY_PROPERTY = "linkedin_profile_url__unique_value"

#: Tried first as a precise match, and WRITTEN on every touch so its coverage
#: grows over time. Never create a contact on a member-ID miss alone.
SECONDARY_MATCH_PROPERTY = "hublead_linkedin_member_id"

#: Non-unique URL properties, read-only for us. Preferred order for reading an
#: existing LinkedIn URL off a contact.
LINKEDIN_URL_PROPERTIES = (
    "linkedin_profile_url__unique_value",
    "hs_linkedin_url",
    "pb_linkedin_profile_url",
    "zoominfo_person_linkedin_url_",
    "linkedinbio",
)

SALESNAV_URL_PROPERTY = "hublead_salesnav_profile_url"

# --- Outreach date properties ---------------------------------------------
# Send side — written by the outreach routine today.
LAST_MESSAGE_SENT = "hublead_last_linkedin_message_sent_date"
LAST_INVITE_SENT = "hublead_last_linkedin_invitation_sent_date"

#: Response side — these EXIST in the portal but nothing writes them. This is
#: why the weekly digest has to hand-assemble a reply rate from Unipile and
#: reports "0/4, essentially no signal". Populating them makes acceptance and
#: reply rate native CRM metrics.
LAST_INVITE_ACCEPTED = "hublead_last_linkedin_invitation_accepted_date"
LAST_MESSAGE_RECEIVED = "hublead_last_linkedin_message_received_date"

#: Status enums that already exist for outreach state.
OUTREACH_STATUS = "linkedin__outreach"          # select
CONTACTED_STATUS = "linkedin__contacts"         # select — read by the runbook
CONNECTED_STATUS = "linkedin__connected"        # select
REQUESTED_BY_SHAWN = "linkedin__requested_by_shawn"  # select


@dataclass(frozen=True)
class EngagementPacing:
    """Comment limits for an HOURLY routine.

    The previous numbers did not cohere. per_hour == per_run made the
    per-hour cap a no-op; per_day=12 was unreachable under the deployed
    twice-daily schedule (2 runs x 2 = 4/day ceiling); and throttle_after=16
    could never fire against a 12/day cap. These assume the hourly routine
    this rebuild actually deploys.
    """

    per_run: int = 1
    per_day: int = 10
    #: Local hours, start inclusive / end EXCLUSIVE. Checked PER POST, not
    #: once at run start: a run beginning at 17:55 must not post its second
    #: comment at 18:02 after a 90-180s gap.
    active_hours: tuple[int, int] = (7, 18)
    min_gap_seconds: int = 90
    max_gap_seconds: int = 180

    def __post_init__(self) -> None:
        slots = self.active_hours[1] - self.active_hours[0]
        if self.per_run * slots < self.per_day:
            raise ValueError(
                f"per_day={self.per_day} unreachable: {slots} hourly slots x "
                f"per_run={self.per_run} = {self.per_run * slots}"
            )


@dataclass(frozen=True)
class EngagementScreening:
    min_score: int = 4
    min_words: int = 15
    max_words: int = 50
    #: Must exceed the longest gap between runs or posts fall in a blind spot.
    #: At the old twice-daily cadence a 12h window left 14:08->20:05 invisible
    #: every day (~6h) and Friday 14:08 -> Monday 08:05 (66h) every weekend —
    #: prospects posting Friday afternoon were never engaged. Hourly runs make
    #: 24h ample, and the dedupe (not the window) prevents re-commenting.
    freshness_hours: int = 24


# --- Settings -------------------------------------------------------------

@dataclass(frozen=True)
class Settings:
    hubspot_token: str
    unipile_api_key: str
    #: Defaults TRUE. Given that a task reported success for months while
    #: doing nothing, a misconfigured runner must not send for real.
    dry_run: bool = True
    caps: OutreachCaps = field(default_factory=OutreachCaps)
    thresholds: OutreachThresholds = field(default_factory=OutreachThresholds)
    pacing: EngagementPacing = field(default_factory=EngagementPacing)
    screening: EngagementScreening = field(default_factory=EngagementScreening)


class ConfigError(RuntimeError):
    """Raised when required credentials are absent or malformed."""


def load_settings(dry_run: bool = True) -> Settings:
    """Read credentials from the environment.

    Fails with an actionable message rather than deep inside an API call, so an
    unattended routine reports the real cause.
    """
    hubspot_token = os.environ.get("QBS_HUBSPOT_TOKEN", "").strip()
    unipile_api_key = os.environ.get("UNIPILE_API_KEY", "").strip()

    missing = []
    if not hubspot_token:
        missing.append("QBS_HUBSPOT_TOKEN (HubSpot private-app token, pat-na1-...)")
    if not unipile_api_key:
        missing.append("UNIPILE_API_KEY (Unipile API key)")
    if missing:
        raise ConfigError(
            "Missing required environment variables:\n  - "
            + "\n  - ".join(missing)
            + "\n\nSet these on the Claude Code environment so scheduled "
            "routines inherit them."
        )

    if len(unipile_api_key) < 30 or "." not in unipile_api_key:
        raise ConfigError(
            "UNIPILE_API_KEY looks truncated or malformed. Failing now rather "
            "than deep in a run, where an auth error can be mistaken for a "
            "transient fault and retried."
        )

    if not hubspot_token.startswith("pat-"):
        raise ConfigError(
            "QBS_HUBSPOT_TOKEN does not look like a HubSpot private-app token "
            "(expected a 'pat-' prefix)."
        )

    return Settings(
        hubspot_token=hubspot_token,
        unipile_api_key=unipile_api_key,
        dry_run=dry_run,
    )
