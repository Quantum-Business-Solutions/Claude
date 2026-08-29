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

UNIPILE_BASE = "https://api30.unipile.com:16072/api/v1"

#: The only account either routine may send or comment from.
SHAWN_ACCOUNT_ID = "S6ua4SfUT4SMRFZFOmyUzQ"
#: Member IDs are immutable; slugs are user-changeable. Assert on both.
SHAWN_PROVIDER_ID = "ACoAAAGv8WABzhfWcURPIaBDzbgiEWX5e781Etw"
SHAWN_PUBLIC_IDENTIFIER = "shawnpetersonquantum"

#: Shawn's second connection to the same LinkedIn login. NOT interchangeable
#: with the primary:
#:   - Sends (invite / DM / InMail): forbidden. v3 sent InMails here and the
#:     path was never proven; the outreach runbook stops rather than falling back.
#:   - Sales Navigator search (the watch-list sync): required, per the
#:     2026-08-29 watch-sync audit, which found the classic account lacks the
#:     Sales Nav entitlement.
#: Note the two source documents contradict each other on that entitlement, so
#: unipile.resolve_search_account() reads premiumFeatures live instead of
#: trusting either. See docs/known-issues.md#sales-nav-entitlement.
SHAWN_SEARCH_ACCOUNT_ID = "7lBoyXuETqKdiJYLj5HBGA"

#: Colleagues' accounts in the same Unipile workspace. Sending from one of
#: these puts QBS outreach out under someone else's name.
COLLEAGUE_ACCOUNT_IDS = frozenset({
    "4fi7iaAuRRmRpzl4G8Dqjg",
    "9eK50zZlT2qVr0oCo0NJVg",
    "F5Y_Hhe_TCO94_hkWXmCKg",
    "oCJmihYGQJ-wsaA0bgW_aQ",
    "xgfVW4VBRri7sQ9tDmSGAw",
})

#: Accounts no send may ever originate from.
FORBIDDEN_SEND_ACCOUNT_IDS = COLLEAGUE_ACCOUNT_IDS | {SHAWN_SEARCH_ACCOUNT_ID}

TIMEZONE = ZoneInfo("America/Chicago")

# --- HubSpot task types ---------------------------------------------------

TASK_TYPE_INVITE = "LINKED_IN_CONNECT"
TASK_TYPE_INMAIL = "LINKED_IN_MESSAGE"
TASK_TYPE_DM = "LINKED_IN"

#: Every task type either routine writes. Tally queries must cover all three:
#: the engagement routine logs LINKED_IN, and so does the outreach routine for
#: DMs, so neither can count on type alone to isolate its own work.
ALL_LINKEDIN_TASK_TYPES = (TASK_TYPE_INVITE, TASK_TYPE_INMAIL, TASK_TYPE_DM)

# --- Verification (the Reading Rule) --------------------------------------

VERDICT_YES = "yes"
VERDICT_NO = "no"
VERDICT_UNREADABLE = "unreadable"

#: Written to the ai__ namespace, which the overwriting portal workflows
#: (274857276, 274857511) and Data Enrichment do not touch.
AI_STILL_AT_COMPANY = "ai__li_still_at_company"
AI_CONTACT_EVIDENCE = "ai__contact_evidence"
AI_VERIFIED_DATE = "ai__contact_verified_date"
AI_SOURCES_CONFIRMING = "ai__sources_confirming"
AI_SOURCE_LABEL = "LinkedIn (Unipile work_experience)"

#: Stripped from both sides before comparing employers.
COMPANY_SUFFIXES = (
    "incorporated", "inc", "llc", "l.l.c.", "corporation", "corp",
    "limited", "ltd", "company", "co", "holdings", "holding", "group",
    "plc", "gmbh", "sa", "nv", "bv", "ag", "pty",
)

# --- Screening ------------------------------------------------------------

#: Shortened forms accepted when matching a LinkedIn slug to a first name.
NICKNAMES = {
    "chuck": "charles", "mike": "michael", "bob": "robert",
    "danny": "daniel", "zach": "zachary", "ken": "kenneth",
    "bill": "william", "jim": "james", "dave": "david",
    "rick": "richard", "steve": "steven", "tom": "thomas",
}

SENIORITY_ALLOWED = frozenset({"executive", "owner", "vp", "director"})

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

REQUIRED_LEAD_STATUS_LABEL = "CAS Prospect"
LEAD_STATUS_MOVED = "No Longer with Company"

VERIFICATION_UNIVERSE_LIST_ID = "5243"
VERIFIED_CALLABLE_LIST_ID = "8260"

LAST_MESSAGE_PROPERTY = "hublead_last_linkedin_message_sent_date"
LAST_INVITE_PROPERTY = "hublead_last_linkedin_invitation_sent_date"

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
    combined_ceiling: int = 100
    daily_stop: int = 70
    target_low: int = 15
    target_high: int = 20

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
    #: A high `no` rate is the established ~49% baseline, NOT a stop condition.
    #: A high `unreadable` rate means the API or permissions changed.
    max_unreadable_rate: float = 0.40
    max_single_channel_rate: float = 0.50
    max_unipile_errors: int = 2
    min_candidates: int = 5
    min_connections_count: int = 30
    #: Skip anyone with a meeting booked inside this window.
    recent_meeting_days: int = 180
    #: Rolling scan: extra pages of 100 companies when the pool runs thin.
    max_extra_pages: int = 5
    page_size: int = 100
    runway_warning_margin: int = 500


# --- Engagement routine ---------------------------------------------------

WATCH_LIST_NAME = "LinkedIn Watch — Sales Nav"

#: Load-bearing: tally.count_engagement_posts_today() matches on this prefix.
#: Changing it silently resets the daily count to zero.
TASK_SUBJECT_PREFIX = "LinkedIn Engagement —"

#: Contact property caching the Unipile provider_id, so a prospect who changes
#: their LinkedIn vanity URL does not silently drop off the watch list.
PROVIDER_ID_PROPERTY = "qbs_linkedin_provider_id"

#: Candidate properties holding a contact's LinkedIn URL, most-preferred
#: first. Resolved against the portal at runtime rather than assumed.
LINKEDIN_URL_PROPERTIES = ("hs_linkedin_url", "linkedin_url", "linkedinbio")


@dataclass(frozen=True)
class EngagementPacing:
    """Comment limits.

    The Cowork skill burst-posted its whole daily allowance in ~16 minutes and
    then went silent for 24h. `per_hour` exists so an hourly routine can spread
    the same volume across a workday, which is both safer and more human.
    """

    per_day: int = 12
    per_run: int = 2
    per_hour: int = 2
    #: Local hours during which commenting is allowed (start inclusive, end exclusive).
    active_hours: tuple[int, int] = (7, 18)
    throttle_after: int = 16
    throttled_per_day: int = 6
    min_gap_seconds: int = 90
    max_gap_seconds: int = 180


@dataclass(frozen=True)
class EngagementScreening:
    min_score: int = 4
    min_words: int = 15
    max_words: int = 50
    freshness_hours: int = 12


# --- Settings -------------------------------------------------------------

@dataclass(frozen=True)
class Settings:
    hubspot_token: str
    unipile_api_key: str
    dry_run: bool = False
    caps: OutreachCaps = field(default_factory=OutreachCaps)
    thresholds: OutreachThresholds = field(default_factory=OutreachThresholds)
    pacing: EngagementPacing = field(default_factory=EngagementPacing)
    screening: EngagementScreening = field(default_factory=EngagementScreening)


class ConfigError(RuntimeError):
    """Raised when required credentials are absent or malformed."""


def load_settings(dry_run: bool = False) -> Settings:
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
